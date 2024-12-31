from sqlalchemy.orm import Session
import sqlalchemy
from sqlalchemy import func
from config.schema import DividendInfo, Stock, StockIssuanceReduction

class DividendInfoRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_dividend_info(self, stock_code: str, dividends: list):
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        for dividend in dividends:
            div = DividendInfo(
                stock_id=stock.id,
                year=dividend.year,
                dividend_per_share=dividend.dividend_per_share,
                dividend_yield=dividend.dividend_yield,
                ex_dividend_date=dividend.ex_dividend_date
            )
            self.session.add(div)
        self.session.commit()

    def get_dividend_info(self, stock_code: str, years: int, apply_adjustment: bool = False) -> list:
        """
        배당 정보 조회. 조정계수 적용 여부를 선택할 수 있음
        
        Args:
            stock_code: 종목 코드
            years: 조회할 연도 수
            apply_adjustment: 조정계수 적용 여부
            
        Returns:
            배당 정보 리스트
        """
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        dividends = self.session.query(DividendInfo)\
            .filter_by(stock_id=stock.id)\
            .order_by(DividendInfo.year.desc())\
            .limit(years)\
            .all()

        if apply_adjustment:
            # 조정계수 적용
            from adapters.opendart_adapter import OpenDartApiAdapter
            import os
            
            api_key = os.getenv('DART_API_KEY')
            if not api_key:
                raise ValueError("DART_API_KEY environment variable is required")
                
            adapter = OpenDartApiAdapter(api_key)
            events = adapter.calculate_adjustment_factors(stock_code, '1900-01-01', '2100-01-01')
            
            # 이벤트를 연도별로 그룹화
            event_dict = {}
            for event in events:
                year = int(event['date'][:4])
                if year not in event_dict:
                    event_dict[year] = []
                event_dict[year].append(event)
            
            # 각 배당 정보에 조정계수 적용
            for dividend in dividends:
                if dividend.year in event_dict:
                    # 해당 연도의 마지막 이벤트의 누적 배수 사용
                    last_event = event_dict[dividend.year][-1]
                    dividend.apply_adjustment_factor(last_event['cumulative_factor'])

        return dividends

    def update_adjusted_dividends(self, stock_code: str):
        """
        모든 배당 정보에 대해 조정계수를 적용하여 업데이트
        """
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        # 조정계수 계산
        from adapters.opendart_adapter import OpenDartApiAdapter
        import os
        
        api_key = os.getenv('DART_API_KEY')
        if not api_key:
            raise ValueError("DART_API_KEY environment variable is required")
            
        adapter = OpenDartApiAdapter(api_key)
        events = adapter.calculate_adjustment_factors(stock_code, '1900-01-01', '2100-01-01')
        
        # 이벤트를 연도별로 그룹화
        event_dict = {}
        for event in events:
            year = int(event['date'][:4])
            if year not in event_dict:
                event_dict[year] = []
            event_dict[year].append(event)
        
        # 모든 배당 정보에 조정계수 적용
        dividends = self.session.query(DividendInfo)\
            .filter_by(stock_id=stock.id)\
            .all()
            
        for dividend in dividends:
            if dividend.year in event_dict:
                # 해당 연도의 마지막 이벤트의 누적 배수 사용
                last_event = event_dict[dividend.year][-1]
                dividend.apply_adjustment_factor(last_event['cumulative_factor'])
        
        self.session.commit()

    def get_high_yield_stocks(self, min_yield: float) -> list:
        """최소 배당률 이상인 종목들의 배당 정보를 조회합니다."""
        # 가장 최신 연도 조회
        latest_date = self.session.query(func.max(DividendInfo.year)).scalar()

        # 최신 연도 데이터가 없는 경우 빈 리스트 반환
        if not latest_date or not self.session.query(DividendInfo).filter_by(year=latest_date).first():
            return []

        return self.session.query(
            Stock.code,
            DividendInfo.year,
            DividendInfo.dividend_per_share,
            DividendInfo.dividend_yield
        ).join(Stock, Stock.id == DividendInfo.stock_id)\
         .filter(DividendInfo.year == latest_date)\
         .filter(DividendInfo.dividend_yield >= min_yield)\
         .all()

    def save_stock_issuance_reduction(self, stock_code: str, issuance_reductions: list):
        """증자(감자) 현황 데이터를 저장합니다."""
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        for issuance in issuance_reductions:
            existing = self.session.query(StockIssuanceReduction).filter_by(
                corp_code=issuance.corp_code,
                isu_dcrs_de=issuance.isu_dcrs_de,
                isu_dcrs_stle=issuance.isu_dcrs_stle
            ).first()

            if not existing:
                new_issuance = StockIssuanceReduction(
                    stock_id=stock.id,
                    corp_code=issuance.corp_code,
                    rcept_no=issuance.rcept_no,
                    isu_dcrs_de=issuance.isu_dcrs_de,
                    isu_dcrs_stle=issuance.isu_dcrs_stle,
                    isu_dcrs_stock_knd=issuance.isu_dcrs_stock_knd,
                    isu_dcrs_qy=issuance.isu_dcrs_qy,
                    isu_dcrs_mstvdv_fval_amount=issuance.isu_dcrs_mstvdv_fval_amount,
                    isu_dcrs_mstvdv_amount=issuance.isu_dcrs_mstvdv_amount,
                    stlm_dt=issuance.stlm_dt,
                    adjust_ratio=issuance.adjust_ratio
                )
                self.session.add(new_issuance)
        
        self.session.commit()