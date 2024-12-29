from typing import List, Optional
from dataclasses import dataclass
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from exceptions import DividendScreeningError, NoPriceDataError

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
                
                # 주가 정보가 없는 경우 배당률이 0이 되므로 meets_criteria는 False
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

    def _get_current_price(self, stock_code: str) -> float:
        """주식의 현재 가격을 가져옵니다.
        
        Args:
            stock_code: 종목 코드
            
        Returns:
            현재 주가
            
        Raises:
            NoPriceDataError: 주가 정보를 가져올 수 없는 경우
        """
        # TODO: 실제 주가 데이터 소스와 연동 필요
        raise NoPriceDataError(f"No price data available for {stock_code}")

    def _calculate_average_dividend_yield(self, dividend_info: List) -> float:
        if not dividend_info:
            return 0.0
            
        try:
            current_price = self._get_current_price(dividend_info[0].stock_code)
            if current_price <= 0:
                return 0.0
                
            total_dividend = sum(info.dividend_per_share for info in dividend_info)
            average_dividend = total_dividend / len(dividend_info)
            return (average_dividend / current_price) * 100
            
        except NoPriceDataError:
            return 0.0