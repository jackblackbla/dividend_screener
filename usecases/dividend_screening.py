from typing import List, Optional, Dict
from dataclasses import dataclass
import sqlalchemy
from sqlalchemy import func
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.stock_price_repository import StockPriceRepository
from exceptions import DividendScreeningError, NoPriceDataError
import logging
from datetime import datetime
from schema import Stock

logger = logging.getLogger(__name__)

@dataclass
class ScreeningCriteria:
    min_dividend: float  # 최소 배당금
    min_yield: float  # 최소 배당률
    min_dividend_count: int  # 최소 배당 횟수
    years_to_consider: int  # 고려할 연도 수
    min_consecutive_years: Optional[int] = None  # 연속 배당 연도 수
    min_dividend_growth: Optional[float] = None  # 최소 배당 성장률

@dataclass
class ScreeningResult:
    stock_code: str
    stock_name: str
    dividend_per_share: float
    dividend_count: int
    consecutive_years: int
    dividend_growth: float
    dividend_yield: float
    meets_criteria: bool

class DividendScreeningUseCase:
    def __init__(self,
                 dividend_repo: DividendInfoRepository,
                 financial_repo: FinancialStatementRepository,
                 stock_price_repo: StockPriceRepository,
                 session):
        self.dividend_repo = dividend_repo
        self.financial_repo = financial_repo
        self.stock_price_repo = stock_price_repo
        self.session = session

    def screen_stocks(self, stock_codes: List[str], criteria: ScreeningCriteria) -> Dict:
        if not stock_codes:
            raise DividendScreeningError("Stock codes list cannot be empty")

        if criteria.years_to_consider <= 0:
            raise DividendScreeningError("Years to consider must be greater than 0")

        included = []
        excluded = []
        
        for stock_code in stock_codes:
            try:
                # 배당 정보 조회
                dividend_info = self.dividend_repo.get_dividend_info(
                    stock_code, 
                    criteria.years_to_consider
                )
                
                if not dividend_info:
                    excluded.append(stock_code)
                    continue
                    
                # 최근 배당금
                latest_dividend = dividend_info[-1].dividend_per_share
                logger.debug(f"Stock {stock_code}: Latest dividend = {latest_dividend}")
                
                # 주가 및 배당률 계산
                try:
                    close_price = self._get_current_price(stock_code)
                    dividend_yield = self._calculate_dividend_yield(latest_dividend, close_price)
                    logger.debug(f"Stock {stock_code}: Close price = {close_price}, Dividend yield = {dividend_yield}%")
                except NoPriceDataError:
                    dividend_yield = 0.0
                    logger.debug(f"Stock {stock_code}: No price data available")
                
                # 스크리닝 지표 계산
                dividend_count = len(dividend_info)
                consecutive_years = self._calculate_consecutive_years(dividend_info)
                dividend_growth = self._calculate_dividend_growth(dividend_info)
                logger.debug(f"Stock {stock_code}: Dividend count = {dividend_count}, Consecutive years = {consecutive_years}, Dividend growth = {dividend_growth}%")
                
                # 스크리닝 조건 평가
                meets_criteria = (
                    latest_dividend >= criteria.min_dividend and
                    dividend_yield >= criteria.min_yield and
                    dividend_count >= criteria.min_dividend_count and
                    (criteria.min_consecutive_years is None or
                     consecutive_years >= criteria.min_consecutive_years) and
                    (criteria.min_dividend_growth is None or
                     dividend_growth >= criteria.min_dividend_growth)
                )
                logger.debug(f"Stock {stock_code}: Meets criteria = {meets_criteria}")

                # 결과 추가
                included.append(ScreeningResult(
                    stock_code=stock_code,
                    stock_name=self._get_stock_name(stock_code),
                    dividend_per_share=latest_dividend,
                    dividend_count=dividend_count,
                    consecutive_years=consecutive_years,
                    dividend_growth=dividend_growth,
                    dividend_yield=dividend_yield,
                    meets_criteria=meets_criteria
                ))
                
            except Exception as e:
                logger.error(f"Error screening stock {stock_code}: {str(e)}")
                excluded.append(stock_code)
                
        return {
            "included": [{
                "stock_code": result.stock_code,
                "stock_name": result.stock_name,
                "dividend_per_share": result.dividend_per_share,
                "dividend_count": result.dividend_count,
                "consecutive_years": result.consecutive_years,
                "dividend_growth": result.dividend_growth,
                "dividend_yield": result.dividend_yield,
                "meets_criteria": result.meets_criteria,
                "stock_code": result.stock_code  # stock_code 키 추가
            } for result in included],
            "excluded": excluded,
            "criteria": criteria.__dict__,
            "timestamp": datetime.now().isoformat()
        }

    def screen_high_yield_stocks(self, min_yield: float) -> List[Dict]:
        """최소 배당률 이상인 종목들을 스크리닝합니다."""
        from sqlalchemy import text
        query = text("""
            WITH latest AS (
                SELECT MAX(trade_date) AS latest_date
                FROM stock_prices
            )
            SELECT s.code AS stock_code,
                   d.year,
                   d.dividend_per_share,
                   p.close_price,
                   (d.dividend_per_share / p.close_price * 100) AS dividend_yield
              FROM stocks s
              JOIN dividend_info d ON s.id = d.stock_id
              JOIN stock_prices p ON p.stock_id = s.id
              JOIN latest l ON p.trade_date = l.latest_date
             WHERE (d.dividend_per_share / p.close_price * 100) >= :min_yield
        """)
        
        result = self.session.execute(query, {'min_yield': min_yield})
        return [row._asdict() for row in result]

    def _calculate_consecutive_years(self, dividend_info: List) -> int:
        """연속 배당 연도 수 계산"""
        if not dividend_info:
            return 0
            
        sorted_info = sorted(dividend_info, key=lambda x: x.year)
        consecutive = 1
        
        for i in range(1, len(sorted_info)):
            if sorted_info[i].year == sorted_info[i-1].year + 1:
                consecutive += 1
            else:
                break
                
        return consecutive

    def _calculate_dividend_growth(self, dividend_info: List) -> float:
        """배당 성장률 계산"""
        if len(dividend_info) < 2:
            return 0.0
            
        sorted_info = sorted(dividend_info, key=lambda x: x.year)
        first = sorted_info[0].dividend_per_share
        last = sorted_info[-1].dividend_per_share
        
        return ((last - first) / first) * 100 if first != 0 else 0.0

    def _get_stock_name(self, stock_code: str) -> str:
        """종목 이름 조회"""
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if stock:
            return stock.name
        return stock_code

    def _get_current_price(self, stock_code: str) -> float:
        """최근 거래일의 주가를 가져옵니다."""
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise NoPriceDataError(f"Stock with code {stock_code} not found")
            
        latest_date = self.stock_price_repo.get_latest_trade_date()
        if not latest_date:
            raise NoPriceDataError("No trade date available")
            
        prices = self.stock_price_repo.get_prices_by_date(latest_date)
        if stock.id not in prices:
            raise NoPriceDataError(f"No price data available for {stock_code} on {latest_date}")
            
        return prices[stock.id]

    def _calculate_dividend_yield(self, dividend_per_share: float, close_price: float) -> float:
        """배당률을 계산합니다."""
        if close_price == 0:
            return 0.0
        return (dividend_per_share / close_price) * 100