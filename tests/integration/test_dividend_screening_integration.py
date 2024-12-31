import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

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
        from config.schema import Base, Stock, DividendInfo
        from dotenv import load_dotenv

        # 환경 변수 로드
        load_dotenv()

        # 환경 변수에서 데이터베이스 URL 읽기
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        engine = create_engine(db_url)
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

    def test_performance_with_large_dataset(self):
        import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from config.schema import Base, Stock, DividendInfo
        import datetime

        # 대량 데이터를 위한 별도의 데이터베이스 생성
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker(bind=engine)
        session = Session()
        Base.metadata.create_all(engine)

        # 1000개의 테스트 데이터 생성
        stocks = []
        for i in range(1000):
            stock = Stock(code=f'{i:06d}', name=f'Test Stock {i}')
            stocks.append(stock)
            session.add(stock)
        session.commit()

        # 각 주식에 대해 5년치 배당 정보 추가
        for stock in stocks:
            for year in range(2019, 2024):
                dividend = DividendInfo(
                    stock_id=stock.id,
                    year=year,
                    dividend_per_share=1000.0,
                    dividend_yield=3.5,
                    ex_dividend_date=datetime.date(year, 12, 31)
                )
                session.add(dividend)
        session.commit()

        # 성능 측정 시작
        start_time = time.time()

        # 테스트 실행
        dividend_repo = DividendInfoRepository(session)
        financial_repo = FinancialStatementRepository(session)
        use_case = DividendScreeningUseCase(dividend_repo, financial_repo)

        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=5,
            years_to_consider=5
        )

        stock_codes = [stock.code for stock in stocks]
        results = use_case.screen_stocks(stock_codes, criteria)

        # 성능 측정 종료
        elapsed_time = time.time() - start_time

        # 결과 검증
        self.assertEqual(len(results), 1000)
        for result in results:
            self.assertIsNotNone(result.dividend_yield)
            self.assertIsNotNone(result.dividend_count)
            self.assertIsInstance(result.meets_criteria, bool)

        # 성능 로그 기록
        print(f"\nPerformance Test Result: Processed 1000 stocks in {elapsed_time:.2f} seconds")

@pytest.fixture
def mock_open_dart_adapter(mocker):
    import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.schema import Base, Stock, DividendInfo
    
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

def test_screen_stocks_with_mock_data(mock_open_dart_adapter, mocker):
    dividend_repo = DividendInfoRepository(mock_open_dart_adapter)
    financial_repo = FinancialStatementRepository(mock_open_dart_adapter)
    use_case = DividendScreeningUseCase(dividend_repo, financial_repo)

    # Mock current price to return 100,000
    mocker.patch.object(use_case, '_get_current_price', return_value=100000)

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