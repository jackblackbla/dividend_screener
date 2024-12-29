import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock, Base

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