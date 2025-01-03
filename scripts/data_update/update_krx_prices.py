import requests
from datetime import datetime
import logging
import os
import csv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 로깅 설정
logging.basicConfig(
    filename='logs/update_krx_prices.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# DB 연결 설정 (읽기 전용 사용자)
DB_URL = "mysql+pymysql://root@localhost:3306/dividend_v2"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def insert_csv_to_db(csv_file, trade_date):
    """CSV 파일 데이터를 DB에 저장"""
    session = Session()
    try:
        with open(csv_file, 'r', encoding='euc-kr') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 데이터 파싱
                code = row["종목코드"].strip()
                name = row["종목명"].strip()
                exchange = "KOSPI" if row["시장구분"].strip() == "STK" else "KOSDAQ"
                sector = row["업종명"].strip()
                
                close_price = float(row["종가"].replace(',', '')) if row["종가"] else 0
                market_cap = int(row["시가총액"].replace(',', '')) if row["시가총액"] else 0

                # stocks 테이블 upsert
                stock = session.execute(
                    text("SELECT stock_id FROM stocks WHERE code = :code"),
                    {"code": code}
                ).fetchone()
                
                if not stock:
                    session.execute(
                        text("""
                            INSERT INTO stocks (code, name, exchange, sector)
                            VALUES (:code, :name, :exchange, :sector)
                        """),
                        {"code": code, "name": name, "exchange": exchange, "sector": sector}
                    )
                    stock_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                else:
                    stock_id = stock.stock_id
                    session.execute(
                        text("""
                            UPDATE stocks
                            SET name = :name, exchange = :exchange, sector = :sector
                            WHERE stock_id = :stock_id
                        """),
                        {"name": name, "exchange": exchange, "sector": sector, "stock_id": stock_id}
                    )

                # market 테이블 upsert
                session.execute(
                    text("""
                        INSERT INTO market (stock_id, date, close_price, market_cap)
                        VALUES (:stock_id, :date, :close_price, :market_cap)
                        ON DUPLICATE KEY UPDATE
                            close_price = VALUES(close_price),
                            market_cap = VALUES(market_cap)
                    """),
                    {
                        "stock_id": stock_id,
                        "date": trade_date,
                        "close_price": close_price,
                        "market_cap": market_cap
                    }
                )

                # stock_prices 테이블 upsert
                session.execute(
                    text("""
                        INSERT INTO stock_prices (stock_id, trade_date, close_price)
                        VALUES (:stock_id, :date, :close_price)
                        ON DUPLICATE KEY UPDATE
                            close_price = VALUES(close_price)
                    """),
                    {
                        "stock_id": stock_id,
                        "date": trade_date,
                        "close_price": close_price
                    }
                )
        
        session.commit()
        logging.info(f"데이터베이스에 성공적으로 저장되었습니다: {csv_file}")
        
    except Exception as e:
        session.rollback()
        logging.error(f"데이터베이스 저장 중 오류 발생: {str(e)}")
        raise
    finally:
        session.close()

def download_krx_csv(trd_dd=None, mktId="STK"):
    """
    KRX에서 주가 데이터를 다운로드하고 DB에 저장
    
    Args:
        trd_dd (str, optional): 거래일 (YYYYMMDD). 기본값은 오늘 날짜
        mktId (str, optional): 시장 코드 ('STK'=코스피, 'KSQ'=코스닥). 기본값은 'STK'
    """
    try:
        # 거래일이 지정되지 않은 경우 오늘 날짜 사용
        if trd_dd is None:
            trd_dd = datetime.now().strftime('%Y%m%d')

        # 1) OTP 발급
        generate_otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"

        payload = {
            "locale": "ko_KR",
            "mktId": mktId,
            "trdDd": trd_dd,
            "money": "1",
            "csvxls_isNo": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT03901"
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # OTP 요청
        res_otp = requests.post(generate_otp_url, data=payload, headers=headers)
        res_otp.raise_for_status()
        otp = res_otp.text.strip()
        logging.info(f"OTP 발급 성공: {otp}")

        # 2) CSV 다운로드
        download_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
        params = {"code": otp}

        # CSV 다운로드 요청
        res_csv = requests.post(download_url, params=params, headers=headers)
        res_csv.raise_for_status()

        # 3) 파일 저장
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        filename = f"krx_{mktId}_{trd_dd}.csv"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, "wb") as f:
            f.write(res_csv.content)
        
        logging.info(f"파일 저장 성공: {filepath}")

        # 4) DB에 저장
        insert_csv_to_db(filepath, datetime.strptime(trd_dd, '%Y%m%d').strftime('%Y-%m-%d'))
        return filepath

    except Exception as e:
        logging.error(f"오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # 코스피 데이터 다운로드 및 저장
        download_krx_csv(mktId="STK")
        
        # 코스닥 데이터 다운로드 및 저장
        download_krx_csv(mktId="KSQ")
    except Exception as e:
        print(f"오류 발생: {str(e)}")