import unittest
from adapters.opendart_adapter import OpenDartApiAdapter
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
import os
from dotenv import load_dotenv

load_dotenv()

class TestDividendScreeningIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        api_key = os.getenv('OPEN_DART_API_KEY')
        if not api_key:
            raise ValueError("OPEN_DART_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        cls.adapter = OpenDartApiAdapter(api_key)
        cls.dividend_repo = DividendInfoRepository(cls.adapter)
        cls.financial_repo = FinancialStatementRepository(cls.adapter)
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

if __name__ == '__main__':
    unittest.main()