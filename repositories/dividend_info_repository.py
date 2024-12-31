from sqlalchemy.orm import Session
import sqlalchemy
from sqlalchemy import func
from schema import DividendInfo, Stock

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

    def get_dividend_info(self, stock_code: str, years: int) -> list:
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        return self.session.query(DividendInfo)\
            .filter_by(stock_id=stock.id)\
            .order_by(DividendInfo.year.desc())\
            .limit(years)\
            .all()

    def get_high_yield_stocks(self, min_yield: float) -> list:
        """최소 배당률 이상인 종목들의 배당 정보를 조회합니다."""
        latest_date = 2023  # 2023년 배당 정보만 조회

        # 2023년 데이터가 없는 경우 빈 리스트 반환
        if not self.session.query(DividendInfo).filter_by(year=latest_date).first():
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