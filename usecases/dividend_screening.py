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
from config.schema import Stock

logger = logging.getLogger(__name__)

@dataclass
class ScreeningCriteria:
    min_dividend: float  # 최소 배당금
    min_yield: float  # 최소 배당률
    min_dividend_count: int  # 최소 배당 횟수
    years_to_consider: int  # 고려할 연도 수
    min_consecutive_years: Optional[int] = None  # 연속 배당 연도 수
    min_dividend_growth: Optional[float] = None  # 최소 배당 성장률
    avoid_div_cut: Optional[bool] = False  # 배당감소 제외

@dataclass
class ScreeningResult:
    stock_code: str
    stock_name: str
    dividend_per_share: float
    dividend_count: int
    consecutive_years: int
    long_term_growth: float  # 장기 성장률 (기존 dividend_growth)
    short_term_growth: float  # 단기 성장률 (새로 추가)
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
        """주식 스크리닝을 수행합니다."""
        if not stock_codes:
            raise DividendScreeningError("Stock codes list cannot be empty")

        if criteria.years_to_consider <= 0:
            raise DividendScreeningError("Years to consider must be greater than 0")

        # 무상조정계수 적용 부분 제거 (DB에서만 조회하도록)
        # issuanceUseCase = StockIssuanceReductionUseCase(self.dividend_repo, self.session)
        # for code in stock_codes:
        #     issuanceUseCase.adjust_dividend_by_factor(code, start_year=2015, end_year=2023)

        included = []
        excluded = []
        
        for stock_code in stock_codes:
            try:
                # 배당 정보 조회 (이미 DB에 저장된 정보 사용)
                dividend_info = self.dividend_repo.get_dividend_info(
                    stock_code, 
                    criteria.years_to_consider
                )
                
                if not dividend_info:
                    excluded.append(stock_code)
                    continue
                    
                # 2023년 배당금
                dividend_2023 = next((d.dividend_per_share for d in dividend_info if d.year == 2023), None)
                if dividend_2023 is None:
                    excluded.append(stock_code)
                    continue
                logger.debug(f"Stock {stock_code}: 2023 dividend = {dividend_2023}")
                
                # 주가 및 배당률 계산
                try:
                    close_price = self._get_current_price(stock_code)
                    dividend_yield = self._calculate_dividend_yield(dividend_2023, close_price)
                    logger.debug(f"Stock {stock_code}: Close price = {close_price}, Dividend yield = {dividend_yield}%")
                except NoPriceDataError:
                    dividend_yield = 0.0
                    logger.debug(f"Stock {stock_code}: No price data available")
                
                # 스크리닝 지표 계산
                dividend_count = len(dividend_info)
                consecutive_years = self._calculate_consecutive_years(dividend_info)
                long_term_growth = self._calculate_long_term_growth(dividend_info)
                short_term_growth = self._calculate_short_term_growth(dividend_info)
                logger.debug(f"Stock {stock_code}: Dividend count = {dividend_count}, Consecutive years = {consecutive_years}, Long term growth = {long_term_growth}%, Short term growth = {short_term_growth}%")
                
                # 스크리닝 조건 평가
                meets_criteria = (
                    dividend_2023 >= criteria.min_dividend and
                    dividend_yield >= criteria.min_yield and
                    dividend_count >= criteria.min_dividend_count and
                    (criteria.min_consecutive_years is None or
                     consecutive_years >= criteria.min_consecutive_years) and
                    (criteria.min_dividend_growth is None or
                     long_term_growth >= criteria.min_dividend_growth)
                )
                logger.debug(f"Stock {stock_code}: Meets criteria = {meets_criteria}")

                # 결과 추가
                included.append(ScreeningResult(
                    stock_code=stock_code,
                    stock_name=self._get_stock_name(stock_code),
                    dividend_per_share=dividend_2023,
                    dividend_count=dividend_count,
                    consecutive_years=consecutive_years,
                    long_term_growth=long_term_growth,
                    short_term_growth=short_term_growth,
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
                "long_term_growth": result.long_term_growth,
                "short_term_growth": result.short_term_growth,
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
            SELECT s.stock_id, s.code AS stock_code, s.corp_code, s.name,
                   s.sector, s.exchange,
                   d.year,
                   d.dividend_per_share,
                   p.close_price,
                   (d.dividend_per_share / p.close_price * 100) AS dividend_yield
              FROM stocks s
              JOIN dividend_info d ON s.stock_id = d.stock_id
              JOIN stock_prices p ON p.stock_id = s.stock_id
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

    def _calculate_long_term_growth(self, dividend_info: List) -> float:
        """장기 배당 성장률 계산"""
        if len(dividend_info) < 2:
            return 0.0
            
        sorted_info = sorted(dividend_info, key=lambda x: x.year)
        first = sorted_info[0].dividend_per_share
        last = sorted_info[-1].dividend_per_share
        
        return ((last - first) / first) * 100 if first != 0 else 0.0

    def _calculate_short_term_growth(self, dividend_info: List) -> float:
        """단기 배당 성장률 계산 (작년 대비)"""
        if len(dividend_info) < 2:
            return 0.0
            
        sorted_info = sorted(dividend_info, key=lambda x: x.year)
        prev = sorted_info[-2].dividend_per_share
        current = sorted_info[-1].dividend_per_share
        
        return ((current - prev) / prev) * 100 if prev != 0 else 0.0

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
        if stock.stock_id not in prices:
            raise NoPriceDataError(f"No price data available for {stock_code} on {latest_date}")
            
        return prices[stock.stock_id]

    def _calculate_dividend_yield(self, dividend_per_share: float, close_price: float) -> float:
        """배당률을 계산합니다."""
        if close_price == 0:
            return 0.0
        return (dividend_per_share / close_price) * 100

class StockIssuanceReductionUseCase:
    def __init__(self,
                 dividend_repo: DividendInfoRepository,
                 session):
        self.dividend_repo = dividend_repo
        self.session = session

    def process_issuance_reduction(self, stock_code: str, year: int, reprt_code: str):
        """증자(감자) 현황 데이터를 처리합니다."""
        from adapters.opendart_adapter import OpenDartApiAdapter
        from config import DART_API_KEY

        # API 어댑터 초기화
        adapter = OpenDartApiAdapter(DART_API_KEY)

        # 증자(감자) 현황 데이터 조회
        issuance_reductions = adapter.get_stock_issuance_reduction(stock_code, year, reprt_code)

        # 무상조정계수 계산
        for issuance in issuance_reductions:
            if issuance.isu_dcrs_stle in ['무상증자', '무상감자']:
                issuance.adjust_ratio = self._calculate_adjust_ratio(issuance)

        # 데이터 저장
        self.dividend_repo.save_stock_issuance_reduction(stock_code, issuance_reductions)

    def _calculate_adjust_ratio(self, issuance) -> float:
        """무상조정계수를 계산합니다."""
        if issuance.isu_dcrs_stle == '무상증자':
            # 무상증자: 1 + (발행 수량 / 기존 주식 수)
            return 1 + (issuance.isu_dcrs_qy / self._get_previous_shares_count(issuance.corp_code))
        elif issuance.isu_dcrs_stle == '무상감자':
            # 무상감자: (기존 주식 수 - 감자 수량) / 기존 주식 수
            return (self._get_previous_shares_count(issuance.corp_code) - issuance.isu_dcrs_qy) / self._get_previous_shares_count(issuance.corp_code)
        return 1.0

    def _get_previous_shares_count(self, corp_code: str) -> int:
        """이전 발행주식수를 조회합니다."""
        # TODO: 실제 구현 필요 (기존 발행주식수 테이블에서 조회)
        return 1000000  # 임시 값

    def compute_adjustment_factor(self, corp_code: str, start_year: int, end_year: int) -> float:
        """
        start_year ~ end_year 사이 발생한 무상증자/감자 이벤트를 조회 후,
        누적 곱으로 최종 무상조정계수를 계산합니다.
        """
        cumulative_factor = 1.0

        for year in range(start_year, end_year + 1):
            try:
                df = self._dart.report(corp_code, '증자', year)
                if df is None or df.empty:
                    continue

                for idx, row in df.iterrows():
                    isu_type = str(row.get('isu_dcrs_stle', ''))
                    quantity = row.get('isu_dcrs_qy', 0)

                    if '무상증자' in isu_type:
                        factor = 1 + (quantity / self._get_previous_shares_count(corp_code))
                        cumulative_factor *= factor
                    elif '무상감자' in isu_type:
                        prev_shares = self._get_previous_shares_count(corp_code)
                        factor = (prev_shares - quantity) / prev_shares
                        cumulative_factor *= factor

            except Exception as e:
                logger.error(f"Failed to retrieve or parse data for {corp_code}, year={year}, err={str(e)}")
                continue

        return cumulative_factor

    def adjust_dividend_by_factor(self, stock_code: str, start_year: int, end_year: int):
        """
        1) 무상조정계수(cumulative_factor) 계산
        2) DB에서 과거 DPS 불러옴
        3) '조정된 DPS'로 업데이트 or 로깅
        """
        corp_code = stock_code  # 실제론 Dart 고유번호 변환 필요할 수 있음
        factor = self.compute_adjustment_factor(corp_code, start_year, end_year)

        dividend_info = self.dividend_repo.get_dividend_info(stock_code, years_to_consider=10)
        if not dividend_info:
            logger.info(f"No dividend info found for {stock_code}")
            return

        logger.info(f"[{stock_code}] 무상조정계수 (총 누적) = {factor:.4f}")

        for record in dividend_info:
            original_dps = record.dividend_per_share
            adjusted_dps = original_dps / factor
            logger.info(f"  Year={record.year}, Original={original_dps}, Adjusted={adjusted_dps:.2f}")

        # 실제론 self.dividend_repo.update_adjusted_dps(...) 등으로 DB 반영 가능