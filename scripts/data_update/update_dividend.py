import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import requests
import logging
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Numeric
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from exceptions import APIError, RateLimitError

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(env_path)

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
DATABASE_URL = "mysql+pymysql://root@localhost:3306/dividend?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_size=15,
    max_overflow=30,
    pool_timeout=60,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        'connect_timeout': 15,
        'read_timeout': 45,
        'write_timeout': 45,
        'ssl_disabled': True
    }
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# 모델 정의
class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True)
    corp_code = Column(String(8), nullable=True)
    name = Column(String(100), nullable=True)
    dividend_info = relationship("DividendInfo", back_populates="stock")

class DividendInfo(Base):
    __tablename__ = 'dividend_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    code = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    reprt_code = Column(String(5), nullable=False)
    dividend_per_share = Column(Numeric(20, 2), nullable=True)
    adjusted_ratio = Column(Numeric(10, 4), nullable=True)
    adjusted_dividend_per_share = Column(Numeric(20, 2), nullable=True)
    ex_dividend_date = Column(Date, nullable=True)
    stock = relationship("Stock", back_populates="dividend_info")

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    trade_date = Column(Date, nullable=False)
    close_price = Column(Numeric(12, 2), nullable=False)

class StockIssuanceReduction(Base):
    __tablename__ = 'stock_issuance_reduction'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    corp_code = Column(String(8), nullable=False)
    isu_dcrs_de = Column(Date)
    isu_dcrs_stle = Column(String(100))
    adjust_ratio = Column(Numeric(10, 4))

# API 설정
API_KEY = os.getenv("DART_API_KEY")
if not API_KEY:
    logger.warning("DART_API_KEY is not set in environment")

# 배치 처리 설정
BATCH_SIZE = 50
MAX_WORKERS = 4

# API 호출 함수들
def call_irdsSttus(corp_code: str, bsns_year: str, reprt_code: str):
    """증자(감자) 현황 조회"""
    url = "https://opendart.fss.or.kr/api/irdsSttus.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        # 응답을 dict로 강제 변환
        if not isinstance(data, dict):
            try:
                data = dict(data)
            except (TypeError, ValueError):
                logger.warning(f"Failed to convert response to dict: {type(data)}")
                return {"status": "999", "list": []}
                
        if data.get("status") == "000":
            return data
        else:
            logger.warning(f"irdsSttus: status={data.get('status')} msg={data.get('message')}")
            return {"status": data.get('status', '999'), "list": []}
    except Exception as e:
        logger.error(f"call_irdsSttus error: {str(e)}")
        return {"status": "999", "list": []}

def call_alotMatter(corp_code: str, bsns_year: str, reprt_code: str):
    """배당 정보 조회"""
    url = "https://opendart.fss.or.kr/api/alotMatter.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        response = r.json()
        # 응답을 dict로 강제 변환
        if not isinstance(response, dict):
            try:
                response = dict(response)
            except (TypeError, ValueError):
                logger.warning(f"Failed to convert response to dict: {type(response)}")
                return {"list": []}
            
        if response.get("status") == "000":
            return response
        else:
            status = response.get("status", "unknown")
            message = response.get("message", "no message")
            logger.warning(f"alotMatter: status={status} msg={message}")
            return {"list": []}
    except Exception as e:
        logger.error(f"call_alotMatter error: {str(e)}")
        return {"list": []}

def call_dvRs(corp_code: str, bgn_de: str, end_de: str):
    """분할 정보 조회"""
    url = "https://opendart.fss.or.kr/api/dvRs.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bgn_de": bgn_de,
        "end_de": end_de
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        # 응답을 dict로 강제 변환
        if not isinstance(data, dict):
            try:
                data = dict(data)
            except (TypeError, ValueError):
                logger.warning(f"Failed to convert response to dict: {type(data)}")
                return []
                
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"dvRs: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_dvRs error: {str(e)}")
        return []

def call_mgRs(corp_code: str, bgn_de: str, end_de: str):
    """합병 정보 조회"""
    url = "https://opendart.fss.or.kr/api/mgRs.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bgn_de": bgn_de,
        "end_de": end_de
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        # 응답을 dict로 강제 변환
        if not isinstance(data, dict):
            try:
                data = dict(data)
            except (TypeError, ValueError):
                logger.warning(f"Failed to convert response to dict: {type(data)}")
                return []
                
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"mgRs: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_mgRs error: {str(e)}")
        return []

# 이벤트 처리 및 조정 계수 계산
def gather_events_and_compute_factor(stock, dividend_year):
    """이벤트 수집 및 조정 계수 계산"""
    corp_code = stock.corp_code
    year_str = str(dividend_year)
    reprt_code = "11011"

    events = []
    
    # 증자/감자 정보
    irds_response = call_irdsSttus(corp_code, year_str, reprt_code)
    irds_list = irds_response.get('list', []) if isinstance(irds_response, dict) else []
    
    if isinstance(irds_list, list):
        for item in irds_list:
            if isinstance(item, dict):  # dict 타입 확인
                event_date = parse_date(item.get('isu_dcrs_de'), dividend_year)
                events.append({
                    'date': event_date,
                    'type': item.get('isu_dcrs_stle', ''),
                    'data': item
                })

    # 배당 정보
    alot_response = call_alotMatter(corp_code, year_str, reprt_code)
    alot_list = alot_response.get('list', []) if isinstance(alot_response, dict) else []
    
    if isinstance(alot_list, list):
        for item in alot_list:
            if isinstance(item, dict) and '주당 주식배당' in item.get('se', ''):
                event_date = parse_date(item.get('stlm_dt'), dividend_year)
                events.append({
                    'date': event_date,
                    'type': '주식배당',
                    'data': item
                })

    # 분할/합병 정보
    start_date_str = f"{year_str}0101"
    end_date_str = f"{year_str}1231"
    dvrs_list = call_dvRs(corp_code, start_date_str, end_date_str)
    mgrs_list = call_mgRs(corp_code, start_date_str, end_date_str)
    
    if isinstance(dvrs_list, list) and isinstance(mgrs_list, list):
        for item in dvrs_list + mgrs_list:
            if isinstance(item, dict):
                event_date = parse_date(item.get('bddd'), dividend_year)
                events.append({
                    'date': event_date,
                    'type': '분할' if item in dvrs_list else '합병',
                    'data': item
                })

    # 날짜 순 정렬 및 누적 계수 계산
    events.sort(key=lambda x: x['date'])
    cumulative_factor = Decimal('1.0')
    
    for ev in events:
        factor = parse_event_factor(ev['type'], ev['data'])
        cumulative_factor *= factor

    return cumulative_factor

# 기타 유틸리티 함수들
def parse_date(date_str, fallback_year):
    """날짜 파싱"""
    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass
    return datetime(fallback_year, 12, 31)

def parse_event_factor(ev_type, data):
    """이벤트 유형에 따른 조정 계수 계산"""
    factor = Decimal('1.0')
    
    if ev_type in ['유상증자', '무상증자']:
        qy_str = data['isu_dcrs_qy'] if isinstance(data, dict) and 'isu_dcrs_qy' in data else '0'
        face_val_str = data['isu_dcrs_mstvdv_fval_amount'] if isinstance(data, dict) and 'isu_dcrs_mstvdv_fval_amount' in data else '0'
        try:
            qy = Decimal(qy_str)
            face_val = Decimal(face_val_str) if face_val_str != '0' else Decimal('1')
            factor = Decimal('1.0') + (qy / face_val)
        except:
            factor = Decimal('1.0')
    
    elif '감자' in ev_type:
        qy_str = data['isu_dcrs_qy'] if isinstance(data, dict) and 'isu_dcrs_qy' in data else '0'
        face_val_str = data['isu_dcrs_mstvdv_fval_amount'] if isinstance(data, dict) and 'isu_dcrs_mstvdv_fval_amount' in data else '0'
        try:
            qy = Decimal(qy_str)
            face_val = Decimal(face_val_str) if face_val_str != '0' else Decimal('1')
            factor = Decimal('1.0') - (qy / face_val)
        except:
            factor = Decimal('1.0')
    
    elif ev_type == '주식배당':
        thstrm_str = data['thstrm'] if isinstance(data, dict) and 'thstrm' in data else '0'
        try:
            ratio = Decimal(thstrm_str)
            factor = Decimal('1.0') + ratio
        except:
            factor = Decimal('1.0')
    
    elif ev_type in ['분할', '합병']:
        rt_vl = data['rt_vl'] if isinstance(data, dict) and 'rt_vl' in data else '0'
        try:
            ratio = Decimal(rt_vl)
            factor = ratio if ratio > 0 else Decimal('1.0')
        except:
            factor = Decimal('1.0')

    return max(factor, Decimal('0.0001'))

# 메인 처리 로직
def process_dividend_data(stock, data, year):
    """배당 데이터 처리"""
    session = Session()
    try:
        # 데이터 타입 검사 강화
        if not isinstance(data, dict):
            logger.warning(f"Invalid data format for {stock.corp_code} ({year}): expected dict, got {type(data)}")
            return
            
        dividend_list = data.get('list', [])
        if not isinstance(dividend_list, list):
            logger.warning(f"Invalid dividend list format for {stock.corp_code} ({year}): expected list, got {type(dividend_list)}")
            return

        if not dividend_list:
            logger.info(f"Empty dividend list for {stock.corp_code} ({year})")
            return

        latest_price = session.query(StockPrice).filter(
            StockPrice.stock_id == stock.id
        ).order_by(StockPrice.trade_date.desc()).first()

        if not latest_price:
            logger.warning(f"No price data found for {stock.code}")
            return

        dividend_info = {
            'dividend_per_share': Decimal('0'),
            'ex_dividend_date': None
        }

        for item in dividend_list:
            if not isinstance(item, dict):
                continue
                
            se = item.get('se', '')
            thstrm = item.get('thstrm', '0')
            
            if se == '주당 현금배당금(원)':
                try:
                    val = Decimal(thstrm.replace(',', '').replace('-', '0'))
                    if val > dividend_info['dividend_per_share']:
                        dividend_info['dividend_per_share'] = val
                        dividend_info['ex_dividend_date'] = item.get('stlm_dt')
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Error parsing dividend value for {stock.code}: {str(e)}")
                    continue

        if dividend_info['dividend_per_share'] > 0 and dividend_info['ex_dividend_date']:
            factor = gather_events_and_compute_factor(stock, year)
            
            existing = session.query(DividendInfo).filter_by(
                stock_id=stock.id,
                year=year,
                reprt_code="11011"
            ).first()

            if existing:
                existing.dividend_per_share = float(dividend_info['dividend_per_share'])
                existing.adjusted_ratio = float(factor)
                existing.adjusted_dividend_per_share = float(dividend_info['dividend_per_share'] * factor)
                existing.ex_dividend_date = dividend_info['ex_dividend_date']
            else:
                dividend = DividendInfo(
                    stock_id=stock.id,
                    code=stock.code,
                    year=year,
                    reprt_code="11011",
                    dividend_per_share=float(dividend_info['dividend_per_share']),
                    adjusted_ratio=float(factor),
                    adjusted_dividend_per_share=float(dividend_info['dividend_per_share'] * factor),
                    ex_dividend_date=dividend_info['ex_dividend_date']
                )
                session.add(dividend)

            logger.info(f"Processed dividend for {stock.code} ({stock.corp_code}): {dividend_info['dividend_per_share']}원")

        session.commit()
    except Exception as e:
        logger.error(f"Error processing {stock.corp_code}: {str(e)}")
        session.rollback()
    finally:
        session.close()

def process_stock_batch(stocks):
    """종목 배치 처리"""
    for stock in stocks:
        for year in range(2019, 2024):  # 2019-2023년도 데이터 처리
            try:
                data = call_alotMatter(stock.corp_code, str(year), "11011")
                if data:
                    process_dividend_data(stock, data, year)
                
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
    """메인 실행 함수"""
    try:
        session = Session()
        stocks = session.query(Stock).filter(Stock.corp_code.isnot(None)).all()
        total_stocks = len(stocks)
        logger.info(f"Starting 2019-2023 dividend update for {total_stocks} stocks")

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