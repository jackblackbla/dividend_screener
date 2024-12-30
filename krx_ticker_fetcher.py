import requests
import pandas as pd
from io import StringIO
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from schema import Base, Stock
from sqlalchemy.orm import sessionmaker

def generate_otp(payload):
    url_otp = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "http://data.krx.co.kr",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "X-Requested-With": "XMLHttpRequest"
    }
    resp = requests.post(url_otp, data=payload, headers=headers)
    resp.raise_for_status()
    return resp.text.strip()

def download_csv(otp_code):
    download_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
    headers = {
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {"code": otp_code}
    r = requests.get(download_url, params=params, headers=headers)
    r.raise_for_status()
    
    # 임시로 파일 저장 (디버깅용, UTF-8로 저장)
    content_utf8 = r.content.decode('cp949').encode('utf-8')
    with open("temp_krx_utf8.csv", "wb") as f:
        f.write(content_utf8)
        
    return r.content

def get_kospi_kosdaq_tickers():
    # 1) KOSPI OTP
    kospi_payload = {
        "locale": "ko_KR",
        "mktId": "STK",
        "share": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901"
    }
    kospi_otp = generate_otp(kospi_payload)
    kospi_csv_bytes = download_csv(kospi_otp)
    
    # CSV -> pandas DataFrame (인코딩 주의)
    kospi_str = kospi_csv_bytes.decode('cp949', errors='replace')
    kospi_df = pd.read_csv(StringIO(kospi_str))
    kospi_df["시장구분"] = "KOSPI"

    # 2) KOSDAQ OTP
    kosdaq_payload = {
        "locale": "ko_KR",
        "mktId": "KSQ",
        "segTpCd": "ALL",
        "share": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901"
    }
    kosdaq_otp = generate_otp(kosdaq_payload)
    kosdaq_csv_bytes = download_csv(kosdaq_otp)
    
    kosdaq_str = kosdaq_csv_bytes.decode('cp949', errors='replace')
    kosdaq_df = pd.read_csv(StringIO(kosdaq_str))
    kosdaq_df["시장구분"] = "KOSDAQ"

    # 병합
    merged_df = pd.concat([kospi_df, kosdaq_df], ignore_index=True)
    # 필요 시 중복 제거
    merged_df.drop_duplicates(subset=["단축코드"], keep="first", inplace=True)
    
    # CSV 파일로 저장
    merged_df.to_csv("merged_krx_tickers.csv", index=False, encoding='utf-8-sig')
    
    return merged_df

def save_tickers_to_db(db_url=None, session=None):
    load_dotenv()
    if session is None:
        db_url = db_url or os.getenv('DATABASE_URL')
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
    
    df_all = get_kospi_kosdaq_tickers()
    df_selected = df_all[['한글 종목약명', '단축코드', '시장구분']]
    df_selected = df_selected.rename(columns={
        '단축코드': 'code',
        '한글 종목약명': 'name',
        '시장구분': 'market'
    })
    
    # ORM을 사용하여 데이터 저장
    for _, row in df_selected.iterrows():
        stock = Stock(
            code=row['code'],
            name=row['name'],
            market=row['market']
        )
        session.add(stock)
    session.commit()
    print(f"Merged KOSPI+KOSDAQ data saved to DB -> {db_url or 'provided session'}")

def get_kospi_kosdaq_prices(trdDd):
    # 1) KOSPI OTP
    kospi_payload = {
        "locale": "ko_KR",
        "mktId": "STK",
        "trdDd": trdDd,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01501"
    }
    kospi_otp = generate_otp(kospi_payload)
    kospi_csv_bytes = download_csv(kospi_otp)
    
    # CSV -> pandas DataFrame (인코딩 주의)
    kospi_str = kospi_csv_bytes.decode('cp949', errors='replace')
    kospi_df = pd.read_csv(StringIO(kospi_str))
    kospi_df["시장구분"] = "KOSPI"

    # 2) KOSDAQ OTP
    kosdaq_payload = {
        "locale": "ko_KR",
        "mktId": "KSQ",
        "segTpCd": "ALL",
        "trdDd": trdDd,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01501"
    }
    kosdaq_otp = generate_otp(kosdaq_payload)
    kosdaq_csv_bytes = download_csv(kosdaq_otp)
    
    kosdaq_str = kosdaq_csv_bytes.decode('cp949', errors='replace')
    kosdaq_df = pd.read_csv(StringIO(kosdaq_str))
    kosdaq_df["시장구분"] = "KOSDAQ"

    # 병합
    merged_df = pd.concat([kospi_df, kosdaq_df], ignore_index=True)
    # 필요 시 중복 제거
    merged_df.drop_duplicates(subset=["종목코드"], keep="first", inplace=True)
    
    # CSV 파일로 저장 (KOSPI와 KOSDAQ 모두 포함)
    merged_df.to_csv("merged_krx_prices.csv", index=False, encoding='utf-8-sig')
    
    # KOSPI와 KOSDAQ 데이터 개수 확인
    kospi_count = len(kospi_df)
    kosdaq_count = len(kosdaq_df)
    print(f"KOSPI records: {kospi_count}, KOSDAQ records: {kosdaq_count}")
    
    return merged_df

def save_prices_to_db(trdDd, db_url=None, session=None):
    from schema import StockPrice
    load_dotenv()
    if session is None:
        db_url = db_url or os.getenv('DATABASE_URL')
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
    
    df_all = get_kospi_kosdaq_prices(trdDd)
    # 필요한 컬럼 선택 및 이름 변경
    # CSV 파일의 실제 컬럼명 확인
    print("Available columns:", df_all.columns)
    
    # 컬럼명 매칭 (KRX API의 실제 컬럼명 사용)
    code_col = '종목코드'
    price_col = '종가'
    # 거래일 정보가 없으므로 입력된 날짜 사용
    trade_date = pd.to_datetime(trdDd, format='%Y%m%d')
    
    df_selected = df_all[[code_col, price_col]].rename(columns={
        code_col: 'stock_code',
        price_col: 'close_price'
    })
    # 거래일 정보 추가
    df_selected['trade_date'] = trade_date
    # ORM을 사용하여 데이터 저장
    total_count = 0
    for _, row in df_selected.iterrows():
        # stock_id 조회
        stock = session.query(Stock).filter_by(code=row['stock_code']).first()
        if stock:
            # 날짜 형식 변환 (YYYYMMDD -> datetime)
            trade_date = pd.to_datetime(row['trade_date'], format='%Y%m%d')
            
            # 중복 체크
            existing = session.query(StockPrice).filter_by(
                stock_id=stock.id,
                trade_date=trade_date
            ).first()
            
            if not existing:
                stock_price = StockPrice(
                    stock_id=stock.id,
                    trade_date=pd.to_datetime(row['trade_date']),
                    close_price=row['close_price']
                )
                session.add(stock_price)
                total_count += 1
        else:
            print(f"Warning: Stock not found for code {row['stock_code']}")
    
    session.commit()
    print(f"Stock prices for {trdDd} saved to DB -> {db_url or 'provided session'}")
    print(f"Total records inserted: {total_count}")

if __name__ == "__main__":
    save_tickers_to_db()
    # 예시: 2024-12-30 주가 데이터 저장
    # save_prices_to_db("20241230")