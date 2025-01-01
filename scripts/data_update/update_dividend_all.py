import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.schema import DividendInfo, DividendYield, Stock, StockPrice, StockIssuanceReduction
import time
import logging
from datetime import datetime
from exceptions import APIError, RateLimitError
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_dividend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# OpenDART API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv('DART_API_KEY')

# 배치 처리 설정
BATCH_SIZE = 50  # 한 번에 처리할 종목 수
MAX_WORKERS = 4  # 병렬 처리 스레드 수

def fetch_dividend_info(stock, year):
    url = "https://opendart.fss.or.kr/api/alotMatter.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": stock.corp_code,
        "bsns_year": str(year),  # 연도별 데이터 요청
        "reprt_code": "11011"  # 사업보고서
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] != '000':
            if data['status'] == '013':  # 요청 제한
                raise RateLimitError(data['message'])
            else:
                raise APIError(f"API Error: {data['message']}")
                
        # JSON 응답 로깅
        logger.info(f"API Response for {stock.corp_code}:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
                
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {stock.corp_code}: {str(e)}")
        return None

def process_issuance_reduction(stock, year):
    from adapters.opendart_adapter import OpenDartApiAdapter
    session = Session()
    try:
        adapter = OpenDartApiAdapter(API_KEY)
        events = adapter.calculate_adjustment_factors(stock.code, f'{year}-01-01', f'{year}-12-31')
        
        for event in events:
            existing = session.query(StockIssuanceReduction).filter_by(
                stock_id=stock.id,
                isu_dcrs_de=event['date']
            ).first()
            
            if not existing:
                issuance = StockIssuanceReduction(
                    stock_id=stock.id,
                    corp_code=stock.corp_code,
                    isu_dcrs_de=event['date'],
                    isu_dcrs_stle=event['type'],
                    adjust_ratio=event['cumulative_factor']
                )
                session.add(issuance)
        
        session.commit()
    except Exception as e:
        logger.error(f"Error processing issuance reduction for {stock.code}: {str(e)}")
        session.rollback()
    finally:
        session.close()

def process_dividend_data(stock, data, year):
    session = Session()
    try:
        if 'list' not in data or not isinstance(data['list'], list):
            logger.warning(f"No dividend list found for {stock.corp_code} ({year})")
            return
             
        # 최근 주가 정보 가져오기
        latest_price = session.query(StockPrice).filter(
            StockPrice.stock_id == stock.id
        ).order_by(StockPrice.trade_date.desc()).first()
         
        if not latest_price:
            logger.warning(f"No price data found for {stock.code}")
            return
             
        # 배당 관련 정보 초기화
        dividend_info = {
            'dividend_per_share': 0,
            'cash_dividend_ratio': 0,
            'stock_dividend_ratio': 0
        }
        
        # 배당 정보 초기화
        ex_dividend_date = ''
        
        for item in data['list']:
            # 'se' 필드에 따라 데이터 처리
            if item['se'] == '주당 현금배당금(원)':
                val = float(item.get('thstrm', '0').replace(',', '').replace('-', '0'))
                if val > dividend_info['dividend_per_share']:
                    dividend_info['dividend_per_share'] = val
                    ex_dividend_date = item.get('stlm_dt', '')  # 해당 아이템에서 날짜 가져오기
        
        if dividend_info['dividend_per_share'] > 0 and ex_dividend_date:
            # 저장할 데이터 준비
            # DividendInfo 데이터 준비
            dividend_data = {
                'stock_id': stock.id,
                'code': stock.code,
                'year': year,
                'reprt_code': "11011",
                'dividend_per_share': dividend_info['dividend_per_share'],
                'adjust_ratio': dividend_info.get('adjust_ratio', 1.0),  # 조정계수 설정
                'ex_dividend_date': ex_dividend_date
            }

            # DividendYield 데이터 준비
            if latest_price and latest_price.close_price > 0:
                yield_data = {
                    'stock_id': stock.id,
                    'date': latest_price.trade_date,
                    'yield_value': (dividend_info['dividend_per_share'] / float(latest_price.close_price)) * 100
                }

                # DividendYield 중복 확인
                existing_yield = session.query(DividendYield).filter_by(
                    stock_id=stock.id,
                    date=latest_price.trade_date
                ).first()

                if existing_yield:
                    existing_yield.yield_value = yield_data['yield_value']
                else:
                    yield_record = DividendYield(**yield_data)
                    session.add(yield_record)
            # 추가 배당 정보 로깅
            logger.info(f"Additional dividend info for {stock.code} ({stock.corp_code}):\n"
                       f"Cash Dividend Ratio: {dividend_info['cash_dividend_ratio']}%\n"
                       f"Stock Dividend Ratio: {dividend_info['stock_dividend_ratio']}%")
            
            # 중복 데이터 확인
            existing = session.query(DividendInfo).filter_by(
                stock_id=stock.id,
                year=year,
                reprt_code="11011"
            ).first()
            
            if existing:
                # 기존 데이터 업데이트
                existing.dividend_per_share = dividend_info['dividend_per_share']
                existing.ex_dividend_date = ex_dividend_date
            else:
                # 새로운 데이터 생성
                dividend = DividendInfo(**dividend_data)
                session.add(dividend)
                
            logger.info(f"Processed dividend for {stock.code} ({stock.corp_code}): {dividend_info['dividend_per_share']}원")
        else:
            logger.warning(f"Invalid dividend data for {stock.corp_code}")
                    
        session.commit()
    except Exception as e:
        logger.error(f"Error processing {stock.corp_code}: {str(e)}")
        session.rollback()
    finally:
        session.close()

def process_stock_batch(stocks):
    for stock in stocks:
        for year in range(2019, 2024):  # 2019-2023년도 데이터 처리
            try:
                # 배당 정보 처리
                data = fetch_dividend_info(stock, year)
                if data:
                    process_dividend_data(stock, data, year)
                
                # 무상증자/감자 정보 처리
                process_issuance_reduction(stock, year)
                
                time.sleep(0.3)  # Rate Limit 대응
            except RateLimitError:
                time.sleep(1)
                continue
            except APIError as e:
                logger.error(f"{year} {str(e)}")
                continue
            except Exception as e:
                logger.error(f"{year} Unexpected error: {str(e)}")
                continue

def main():
    try:
        session = Session()
        stocks = session.query(Stock).filter(Stock.corp_code.isnot(None)).all()
        total_stocks = len(stocks)
        logger.info(f"Starting 2019-2023 dividend update for {total_stocks} stocks")
        
        # 종목을 배치로 분할
        batches = [stocks[i:i + BATCH_SIZE] for i in range(0, len(stocks), BATCH_SIZE)]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_stock_batch, batch) for batch in batches]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Batch processing failed: {str(e)}")
        
        logger.info("2023 dividend update completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Script started at {start_time}")
    
    main()
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Script completed in {duration}")