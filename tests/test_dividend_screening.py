import unittest
from unittest.mock import Mock
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria, ScreeningResult
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from exceptions import DividendScreeningError

class TestDividendScreeningUseCase(unittest.TestCase):
    def setUp(self):
        self.mock_dividend_repo = Mock(spec=DividendInfoRepository)
        self.mock_financial_repo = Mock(spec=FinancialStatementRepository)
        self.use_case = DividendScreeningUseCase(
            self.mock_dividend_repo,
            self.mock_financial_repo
        )

    def test_screen_stocks_with_valid_criteria(self):
        # Mock 데이터 설정
        from schema import DividendInfo
        self.mock_dividend_repo.get_dividend_info.return_value = [
            DividendInfo(dividend_yield=3.5),
            DividendInfo(dividend_yield=4.0),
            DividendInfo(dividend_yield=3.8)
        ]

        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=3,
            years_to_consider=3
        )

        results = self.use_case.screen_stocks(['005930'], criteria)

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].meets_criteria)
        self.assertAlmostEqual(results[0].dividend_yield, 3.77, places=2)
        self.assertEqual(results[0].dividend_count, 3)

    def test_screen_stocks_with_invalid_criteria(self):
        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=3,
            years_to_consider=0
        )

        with self.assertRaises(DividendScreeningError):
            self.use_case.screen_stocks(['005930'], criteria)

    def test_screen_stocks_with_empty_stock_codes(self):
        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=3,
            years_to_consider=3
        )

        with self.assertRaises(DividendScreeningError):
            self.use_case.screen_stocks([], criteria)

    def test_calculate_dividend_count(self):
        dividend_info = [
            {'dividend_yield': 3.5},
            {'dividend_yield': 4.0},
            {'dividend_yield': 3.8}
        ]
        count = self.use_case._calculate_dividend_count(dividend_info)
        self.assertEqual(count, 3)

    def test_calculate_average_dividend_yield(self):
        from schema import DividendInfo
        dividend_info = [
            DividendInfo(dividend_yield=3.5),
            DividendInfo(dividend_yield=4.0),
            DividendInfo(dividend_yield=3.8)
        ]
        avg_yield = self.use_case._calculate_average_dividend_yield(dividend_info)
        self.assertAlmostEqual(avg_yield, 3.77, places=2)

    def test_calculate_average_dividend_yield_with_empty_list(self):
        avg_yield = self.use_case._calculate_average_dividend_yield([])
        self.assertEqual(avg_yield, 0.0)

if __name__ == '__main__':
    unittest.main()