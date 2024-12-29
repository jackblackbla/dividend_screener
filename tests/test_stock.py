import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock, Base
from adapters.opendart_adapter import OpenDartApiAdapter
from exceptions import CorpCodeFetchError

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_stock_creation(db_session):
    stock = Stock(code="005930", name="삼성전자")
    db_session.add(stock)
    db_session.commit()
    
    retrieved_stock = db_session.query(Stock).filter_by(code="005930").first()
    assert retrieved_stock.name == "삼성전자"

def test_get_corp_code_success():
    adapter = OpenDartApiAdapter(api_key="test_key")
    corp_code = adapter.get_corp_code("005930")
    assert corp_code == "00126380"

def test_get_corp_code_api_error():
    adapter = OpenDartApiAdapter(api_key="test_key")
    with pytest.raises(CorpCodeFetchError):
        adapter.get_corp_code("invalid_code")

def test_get_corp_code_not_found():
    adapter = OpenDartApiAdapter(api_key="test_key")
    with pytest.raises(CorpCodeFetchError):
        adapter.get_corp_code("999999")