import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.schema import DividendInfo, Stock, StockPrice
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
BATCH_SIZE = 10  # 10개 종목만 처리
MAX_WORKERS = 1  # 단일 스레드로 처리

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
            
        for item in data['list']:
            dividend_per_share = float(item.get('thstrm', '0').replace(',', '').replace('-', '0'))
            ex_dividend_date = item.get('stlm_dt', '')
            
            # 배당수익률 계산: (주당 배당금 / 주가) * 100
            dividend_yield = (dividend_per_share / float(latest_price.close_price)) * 100 if latest_price.close_price > 0 else 0
            
            if dividend_per_share > 0 and ex_dividend_date:
                # 저장할 데이터 준비
                dividend_data = {
                    'stock_id': stock.id,
                    'year': 2023,
                    'reprt_code': "11011",
                    'dividend_per_share': dividend_per_share,
                    'dividend_yield': dividend_yield,
                    'ex_dividend_date': ex_dividend_date
                }
                
                # 저장 전 데이터 로깅
                logger.info(f"Saving dividend data for {stock.code} ({stock.corp_code}):\n{json.dumps(dividend_data, indent=2, ensure_ascii=False)}")
                
                # 중복 데이터 확인
                existing = session.query(DividendInfo).filter_by(
                    stock_id=stock.id,
                    year=2023,
                    reprt_code="11011"
                ).first()
                
                if existing:
                    # 기존 데이터 업데이트
                    existing.dividend_per_share = dividend_per_share
                    existing.dividend_yield = dividend_yield
                    existing.ex_dividend_date = ex_dividend_date
                else:
                    # 새로운 데이터 생성
                    dividend = DividendInfo(**dividend_data)
                    session.add(dividend)
                    
                logger.info(f"Processed dividend for {stock.code} ({stock.corp_code}): {dividend_per_share}원")
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
        try:
            data = fetch_dividend_info(stock, 2023)  # 2023년도 데이터만 처리
            if data:
                process_dividend_data(stock, data, 2023)
            time.sleep(0.3)  # Rate Limit 대응
        except RateLimitError:
            time.sleep(1)
            continue
        except APIError as e:
            logger.error(f"2023 {str(e)}")
            continue
        except Exception as e:
            logger.error(f"2023 Unexpected error: {str(e)}")
            continue

def main():
    try:
        session = Session()
        # 상위 10개 종목만 선택
        stocks = session.query(Stock).filter(Stock.corp_code.isnot(None)).limit(10).all()
        total_stocks = len(stocks)
        logger.info(f"Starting 2023 dividend update for {total_stocks} stocks")
        
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