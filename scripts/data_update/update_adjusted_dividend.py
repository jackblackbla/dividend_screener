import os
import requests
import logging
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file with explicit path
env_path = os.path.join(os.path.dirname(__file__), '../../config/.env')
load_dotenv(env_path)

# Debug: Check if DART_API_KEY is loaded correctly
dart_key = os.getenv("DART_API_KEY")
logger = logging.getLogger(__name__)
logger.info(f"DART_API_KEY loaded: {dart_key is not None}, length: {len(dart_key) if dart_key else 0}")

# -------------------------------------------------------------------
# 1. 로깅 설정
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_api_adjusted_dividend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# 2. DB 연결 & 모델
# -------------------------------------------------------------------
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

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True)         # 종목코드
    corp_code = Column(String(8), nullable=True)   # 8자리
    name = Column(String(100), nullable=True)

class DividendInfo(Base):
    __tablename__ = 'dividend_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    year = Column(Integer, nullable=False)
    dividend_per_share = Column(Float, nullable=True)
    adjusted_ratio = Column(Float, nullable=True)
    adjusted_dividend_per_share = Column(Float, nullable=True)

# -------------------------------------------------------------------
# 3. OpenDART API 키
# -------------------------------------------------------------------
API_KEY = os.getenv("DART_API_KEY")
if not API_KEY:
    logger.warning("DART_API_KEY is not set in environment. Please ensure it's loaded.")

# -------------------------------------------------------------------
# 4. API 호출 함수들
# -------------------------------------------------------------------

def call_irdsSttus(corp_code: str, bsns_year: str, reprt_code: str):
    """증자(감자) 현황(irdsSttus.json)"""
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
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"irdsSttus: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_irdsSttus error: {str(e)}")
        return []

def call_alotMatter(corp_code: str, bsns_year: str, reprt_code: str):
    """배당(alotMatter.json)"""
    url = "https://opendart.fss.or.kr/api/alotMatter.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"alotMatter: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_alotMatter error: {str(e)}")
        return []

def call_dvRs(corp_code: str, bgn_de: str, end_de: str):
    """분할(dvRs.json)"""
    url = "https://opendart.fss.or.kr/api/dvRs.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bgn_de": bgn_de,  # YYYYMMDD
        "end_de": end_de
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"dvRs: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_dvRs error: {str(e)}")
        return []

def call_mgRs(corp_code: str, bgn_de: str, end_de: str):
    """합병(mgRs.json)"""
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
        if data.get("status") == "000":
            return data.get("list", [])
        else:
            logger.warning(f"mgRs: status={data.get('status')} msg={data.get('message')}")
            return []
    except Exception as e:
        logger.error(f"call_mgRs error: {str(e)}")
        return []

# -------------------------------------------------------------------
# 5. 이벤트 취합 & factor 계산
# -------------------------------------------------------------------
def gather_events_and_compute_factor(stock, dividend_year):
    """
    irdsSttus(증자감자), alotMatter(배당), dvRs(분할), mgRs(합병) => events
    이벤트별 parse_event_factor()로 배수를 계산 → 누적곱
    """
    corp_code = stock.corp_code
    year_str = str(dividend_year)
    reprt_code = "11011"  # 사업보고서

    # A) 증자(감자): irdsSttus
    irds_list = call_irdsSttus(corp_code, year_str, reprt_code)

    # B) 배당(주식배당): alotMatter
    alot_list = call_alotMatter(corp_code, year_str, reprt_code)

    # C) 분할(dvRs)
    start_date_str = f"{year_str}0101"
    end_date_str   = f"{year_str}1231"
    dvrs_list = call_dvRs(corp_code, start_date_str, end_date_str)

    # D) 합병(mgRs)
    mgrs_list = call_mgRs(corp_code, start_date_str, end_date_str)

    events = []

    # 1) irdsSttus -> isu_dcrs_stle, isu_dcrs_de
    for item in irds_list:
        event_date = parse_date(item.get('isu_dcrs_de'), dividend_year)
        event_type = item.get('isu_dcrs_stle', '')
        events.append({
            'date': event_date,
            'type': event_type,  # 예: '유상증자', '무상증자', '감자', ...
            'data': item
        })

    # 2) alotMatter -> 주식배당?
    for item in alot_list:
        se_val = item.get('se', '')
        if '주당 주식배당' in se_val:
            event_date = parse_date(item.get('stlm_dt'), dividend_year)
            events.append({
                'date': event_date,
                'type': '주식배당',
                'data': item
            })

    # 3) dvRs -> 분할
    for item in dvrs_list:
        bddd = item.get('bddd')  # 이사회결의일
        event_date = parse_date(bddd, dividend_year)
        events.append({
            'date': event_date,
            'type': '분할',
            'data': item
        })

    # 4) mgRs -> 합병
    for item in mgrs_list:
        bddd = item.get('bddd')  # 이사회결의일
        event_date = parse_date(bddd, dividend_year)
        events.append({
            'date': event_date,
            'type': '합병',
            'data': item
        })

    # 날짜 순 정렬
    events.sort(key=lambda x: x['date'])

    # 누적곱
    cumulative_factor = Decimal('1.0')
    for ev in events:
        ev_type = ev['type']
        ev_data = ev['data']
        factor = parse_event_factor(ev_type, ev_data)
        cumulative_factor *= factor

    return cumulative_factor


def parse_date(date_str, fallback_year):
    """날짜 문자열을 datetime으로 변환. 없거나 실패 시 fallback"""
    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass
    return datetime(fallback_year, 12, 31)


def parse_event_factor(ev_type, data):
    """
    실제 API 응답 data를 파싱해서 배수 산정.
    (하드코딩 없이, data 내 수치를 이용)

    예시:
     - 'isu_dcrs_qy' (발행/감자 수량)
     - 'isu_dcrs_mstvdv_fval_amount'(주당 액면가?)
     - 'rt_vl'(분할/합병 비율)
     - 등등
    """
    factor = Decimal('1.0')

    if ev_type in ['유상증자','무상증자']:
        # 예: factor = 1 + (증가주식수 / 기존주식수)
        # 여기서는 isu_dcrs_qy / isu_dcrs_mstvdv_fval_amount 라고 가정
        qy_str = data.get('isu_dcrs_qy','0')
        face_val_str = data.get('isu_dcrs_mstvdv_fval_amount','0')
        try:
            qy = Decimal(qy_str)
            face_val = Decimal(face_val_str) if face_val_str!='0' else Decimal('1')
            factor = Decimal('1.0') + (qy / face_val)
        except:
            factor = Decimal('1.0')

    elif '감자' in ev_type:
        # 예: factor = 1 - (감자주식/기존주식)
        qy_str = data.get('isu_dcrs_qy','0')
        face_val_str = data.get('isu_dcrs_mstvdv_fval_amount','0')
        try:
            qy = Decimal(qy_str)
            face_val = Decimal(face_val_str) if face_val_str!='0' else Decimal('1')
            factor = Decimal('1.0') - (qy / face_val)
        except:
            factor = Decimal('1.0')

    elif ev_type == '주식배당':
        # alotMatter의 item 안에 'thstrm'(이번연도 배당?), 'frmtrm'(전연도), ...
        # 혹은 배당주식수 vs 기존주식수?
        # 여기서는 단순히 1 + (0.1) 가 아닌, data 내에 배당비율이 있다고 가정
        # (예: '주당 주식배당(주)' = 0.05 => 5%?)
        # 실제로는 OpenDART alotMatter 응답에서 'thstrm' 등 parse
        thstrm_str = data.get('thstrm','0')
        try:
            # 가정: 'thstrm'이 '0.1' => 10% 배당
            ratio = Decimal(thstrm_str)
            factor = Decimal('1.0') + ratio
        except:
            factor = Decimal('1.0')

    elif ev_type == '분할':
        # dvRs 응답에서 'rt_vl' 등에 분할비율이 있을 수도
        rt_vl = data.get('rt_vl','0')
        try:
            ratio = Decimal(rt_vl)
            factor = ratio if ratio>0 else Decimal('1.0')
        except:
            factor = Decimal('1.0')

    elif ev_type == '합병':
        # mgRs 응답에서 'rt_vl' 등이 합병비율
        rt_vl = data.get('rt_vl','0')
        try:
            ratio = Decimal(rt_vl)
            factor = ratio if ratio>0 else Decimal('1.0')
        except:
            factor = Decimal('1.0')

    # factor가 0 이하가 될 수도 있으니, 최소값 0.0001 등으로 안전 처리 가능
    if factor <= 0:
        factor = Decimal('1.0')

    return factor


# -------------------------------------------------------------------
# 6. 메인 로직: 배당금 조정
# -------------------------------------------------------------------
def calculate_adjusted_dividend():
    """
    DividendInfo 전체를 대상으로:
    gather_events_and_compute_factor -> cumulative_factor
    adjusted_dividend_per_share 갱신
    """
    try:
        main_session = Session()
        dividends = main_session.query(DividendInfo).all()
        total_dividends = len(dividends)
        logger.info(f"Starting to process {total_dividends} DividendInfo records")

        batch_size = 50
        processed_count = 0

        for i in range(0, total_dividends, batch_size):
            batch = dividends[i:i+batch_size]
            batch_session = Session()

            try:
                for dividend in batch:
                    # Stock 정보 조회
                    stock = batch_session.query(Stock).filter_by(id=dividend.stock_id).first()
                    if not stock or not stock.corp_code:
                        logger.info(f"No corp_code or stock not found for DividendID={dividend.id}")
                        continue

                    logger.info(f"Processing DividendID={dividend.id} (StockCode={stock.code}, Year={dividend.year})")
                    
                    # 무상조정계수 계산
                    factor = gather_events_and_compute_factor(stock, dividend.year)
                    logger.info(f"Calculated factor={factor} for DividendID={dividend.id}")

                    # 기존 데이터 확인
                    existing = batch_session.query(DividendInfo).filter_by(
                        id=dividend.id
                    ).first()

                    if existing:
                        # factor 값이 1.0이 아닌 경우에만 업데이트
                        if factor != Decimal('1.0'):
                            existing.adjusted_ratio = float(factor)
                            if existing.dividend_per_share is not None:
                                new_value = Decimal(str(existing.dividend_per_share)) * factor
                                existing.adjusted_dividend_per_share = float(new_value)
                                logger.info(f"Updated DividendID={dividend.id} with factor={factor}, new DPS => {new_value}")
                        else:
                            logger.info(f"Skipping DividendID={dividend.id} as factor is 1.0")
                    else:
                        logger.warning(f"DividendID={dividend.id} not found in database")

                    processed_count += 1

                batch_session.commit()
                logger.info(f"Committed batch i={i}~{i+batch_size}, processed_count={processed_count}")

            except Exception as e:
                logger.error(f"Error in batch processing: {str(e)}")
                batch_session.rollback()
                raise  # 상위 예외 처리로 전파

        logger.info(f"All dividends adjusted successfully. Total processed: {processed_count}/{total_dividends}")

    except Exception as e:
        logger.error(f"Fatal error in calculate_adjusted_dividend: {str(e)}")
        raise

    finally:
        main_session.close()


# -------------------------------------------------------------------
# 7. 실행부
# -------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    logger.info(f"Script started at {start}")

    calculate_adjusted_dividend()

    end = datetime.now()
    logger.info(f"Script finished at {end}, duration={end - start}")