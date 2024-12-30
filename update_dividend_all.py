import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import DividendInfo, Stock
import time
import logging
from datetime import datetime
from exceptions import APIError, RateLimitError
import os
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
        "bsns_year": year,
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
                
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {stock.corp_code}: {str(e)}")
        return None

def process_dividend_data(stock, year, data):
    session = Session()
    try:
        for item in data['list']:
            if item['se'] == '주당 현금배당금(원)':
                if 'stock_knd' in item and item['stock_knd'] == '보통주':
                    dividend_data = {
                        'stock_id': stock.id,
                        'year': year,
                        'reprt_code': "11011",
                        'dividend_per_share': float(item.get('thstrm', '0').replace(',', '').replace('-', '0')),
                        'dividend_yield': float(item.get('thstrm_rate', '0').replace('-', '0')),
                        'ex_dividend_date': item.get('stlm_dt', '')
                    }
                    
                    if dividend_data['dividend_per_share'] > 0:
                        dividend = DividendInfo(**dividend_data)
                        session.merge(dividend)
                        logger.info(f"Processed dividend for {stock.code} ({stock.corp_code}, {year}): {dividend_data['dividend_per_share']}원")
                    else:
                        logger.warning(f"No dividend data for {stock.corp_code} ({year})")
        session.commit()
    except Exception as e:
        logger.error(f"Error processing {stock.corp_code}: {str(e)}")
        session.rollback()
    finally:
        session.close()

def process_stock_batch(stocks):
    for stock in stocks:
        for year in range(2018, 2024):
            try:
                data = fetch_dividend_info(stock, year)
                if data:
                    process_dividend_data(stock, year, data)
                time.sleep(0.3)  # Rate Limit 대응
            except RateLimitError:
                time.sleep(1)
                continue
            except APIError as e:
                logger.error(str(e))
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                continue

def main():
    try:
        session = Session()
        stocks = session.query(Stock).filter(Stock.corp_code.isnot(None)).all()
        total_stocks = len(stocks)
        logger.info(f"Starting dividend update for {total_stocks} stocks")
        
        # 종목을 배치로 분할
        batches = [stocks[i:i + BATCH_SIZE] for i in range(0, len(stocks), BATCH_SIZE)]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_stock_batch, batch) for batch in batches]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Batch processing failed: {str(e)}")
        
        logger.info("Dividend update completed successfully")
        
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