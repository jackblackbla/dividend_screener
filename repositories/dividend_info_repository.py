from sqlalchemy.orm import Session
from schema import DividendInfo, Stock

class DividendInfoRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_dividend_info(self, stock_code: str, dividends: list):
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        for data in dividends:
            div = DividendInfo(
                stock_id=stock.id,
                year=data['year'],
                dividend_per_share=data.get('dividend_per_share'),
                dividend_yield=data.get('dividend_yield'),
                ex_dividend_date=data.get('ex_dividend_date')
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