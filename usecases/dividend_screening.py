from typing import List
from dataclasses import dataclass
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from exceptions import DividendScreeningError

@dataclass
class ScreeningCriteria:
    min_dividend_yield: float
    min_dividend_count: int
    years_to_consider: int

@dataclass
class ScreeningResult:
    stock_code: str
    dividend_yield: float
    dividend_count: int
    meets_criteria: bool

class DividendScreeningUseCase:
    def __init__(self, 
                 dividend_repo: DividendInfoRepository,
                 financial_repo: FinancialStatementRepository):
        self.dividend_repo = dividend_repo
        self.financial_repo = financial_repo

    def screen_stocks(self, stock_codes: List[str], criteria: ScreeningCriteria) -> List[ScreeningResult]:
        if not stock_codes:
            raise DividendScreeningError("Stock codes list cannot be empty")

        if criteria.years_to_consider <= 0:
            raise DividendScreeningError("Years to consider must be greater than 0")

        results = []
        for stock_code in stock_codes:
            try:
                dividend_info = self.dividend_repo.get_dividend_info(stock_code, criteria.years_to_consider)
                dividend_count = self._calculate_dividend_count(dividend_info)
                dividend_yield = self._calculate_average_dividend_yield(dividend_info)

                meets_criteria = (
                    dividend_yield >= criteria.min_dividend_yield and
                    dividend_count >= criteria.min_dividend_count
                )

                results.append(ScreeningResult(
                    stock_code=stock_code,
                    dividend_yield=dividend_yield,
                    dividend_count=dividend_count,
                    meets_criteria=meets_criteria
                ))

            except Exception as e:
                raise DividendScreeningError(f"Error screening stock {stock_code}: {str(e)}")

        return results

    def _calculate_dividend_count(self, dividend_info: List) -> int:
        return len(dividend_info)

    def _calculate_average_dividend_yield(self, dividend_info: List) -> float:
        if not dividend_info:
            return 0.0
        total_yield = sum(info.dividend_yield for info in dividend_info)
        return total_yield / len(dividend_info)