import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from krx_ticker_fetcher import generate_otp, download_csv, get_kospi_kosdaq_tickers, save_tickers_to_db
from schema import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock
import os

@pytest.fixture
def test_db():
    # 테스트용 in-memory SQLite DB 설정
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    # 테스트 데이터베이스 URL 설정
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_generate_otp():
    payload = {
        "locale": "ko_KR",
        "mktId": "STK",
        "share": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901"
    }
    otp = generate_otp(payload)
    assert isinstance(otp, str)
    assert len(otp) > 0

def test_download_csv():
    payload = {
        "locale": "ko_KR",
        "mktId": "STK",
        "share": "1",
        "csvxls_isNo": "false",
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT01901"
    }
    otp = generate_otp(payload)
    csv_data = download_csv(otp)
    assert isinstance(csv_data, bytes)
    assert len(csv_data) > 0

def test_get_kospi_kosdaq_tickers():
    df = get_kospi_kosdaq_tickers()
    assert not df.empty
    assert set(['단축코드', '한글 종목약명', '시장구분']).issubset(df.columns)

def test_save_tickers_to_db(test_db):
    # 데이터 저장 테스트
    save_tickers_to_db(session=test_db)

    # 저장된 데이터 확인
    stocks = test_db.query(Stock).all()
    assert len(stocks) > 0
    assert all(hasattr(stock, 'code') for stock in stocks)
    assert all(hasattr(stock, 'name') for stock in stocks)
    assert all(hasattr(stock, 'market') for stock in stocks)
    assert all(hasattr(stock, 'code') for stock in stocks)
    assert all(hasattr(stock, 'name') for stock in stocks)
    assert all(hasattr(stock, 'market') for stock in stocks)