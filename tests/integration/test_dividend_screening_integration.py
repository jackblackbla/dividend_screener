import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
import pytest
from adapters.opendart_adapter import OpenDartApiAdapter
from exceptions import CorpCodeFetchError, DividendScreeningError
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from dotenv import load_dotenv

load_dotenv()

class TestDividendScreeningIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import datetime
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from schema import Base, Stock, DividendInfo
        
        # 테스트용 메모리 데이터베이스 생성
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker(bind=engine)
        cls.session = Session()
        
        # 테스트 데이터베이스 초기화
        Base.metadata.create_all(engine)
        
        # 테스트 데이터 추가
        stock1 = Stock(code='005930', name='삼성전자')
        stock2 = Stock(code='000660', name='SK하이닉스')
        cls.session.add_all([stock1, stock2])
        cls.session.commit()
        
        # 배당 정보 추가
        dividend1 = DividendInfo(
            stock_id=stock1.id,
            year=2023,
            dividend_per_share=1500.0,
            dividend_yield=3.5,
            ex_dividend_date=datetime.date(2023, 12, 31)
        )
        dividend2 = DividendInfo(
            stock_id=stock2.id,
            year=2023,
            dividend_per_share=1000.0,
            dividend_yield=2.8,
            ex_dividend_date=datetime.date(2023, 12, 31)
        )
        cls.session.add_all([dividend1, dividend2])
        cls.session.commit()
        
        cls.dividend_repo = DividendInfoRepository(cls.session)
        cls.financial_repo = FinancialStatementRepository(cls.session)
        cls.use_case = DividendScreeningUseCase(cls.dividend_repo, cls.financial_repo)

    def test_screen_stocks_with_real_data(self):
        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=3,
            years_to_consider=3
        )

        results = self.use_case.screen_stocks(['005930'], criteria)

        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results[0].dividend_yield)
        self.assertIsNotNone(results[0].dividend_count)
        self.assertIsInstance(results[0].meets_criteria, bool)

    def test_screen_stocks_with_multiple_stocks(self):
        criteria = ScreeningCriteria(
            min_dividend_yield=2.0,
            min_dividend_count=2,
            years_to_consider=2
        )

        results = self.use_case.screen_stocks(['005930', '000660'], criteria)

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsNotNone(result.dividend_yield)
            self.assertIsNotNone(result.dividend_count)
            self.assertIsInstance(result.meets_criteria, bool)

@pytest.fixture
def mock_open_dart_adapter(mocker):
    import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from schema import Base, Stock, DividendInfo
    
    # 테스트용 메모리 데이터베이스 생성
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 테스트 데이터베이스 초기화
    Base.metadata.create_all(engine)
    
    # 테스트 데이터 추가
    stock = Stock(code='005930', name='삼성전자')
    session.add(stock)
    session.commit()
    
    # 배당 정보 추가
    dividend = DividendInfo(
        stock_id=stock.id,
        year=2023,
        dividend_per_share=1500.0,
        dividend_yield=3.5,
        ex_dividend_date=datetime.date(2023, 12, 31)
    )
    session.add(dividend)
    session.commit()
    
    return session

def test_screen_stocks_with_mock_data(mock_open_dart_adapter):
    dividend_repo = DividendInfoRepository(mock_open_dart_adapter)
    financial_repo = FinancialStatementRepository(mock_open_dart_adapter)
    use_case = DividendScreeningUseCase(dividend_repo, financial_repo)

    criteria = ScreeningCriteria(
        min_dividend_yield=3.0,
        min_dividend_count=1,
        years_to_consider=1
    )

    results = use_case.screen_stocks(['005930'], criteria)

    assert len(results) == 1
    assert results[0].dividend_yield == 3.5
    assert results[0].dividend_count == 1
    assert results[0].meets_criteria is True

if __name__ == '__main__':
    unittest.main()