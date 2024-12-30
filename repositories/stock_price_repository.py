from sqlalchemy.orm import Session
from schema import StockPrice, Stock

class StockPriceRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_stock_prices(self, stock_code: str, prices: list):
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        for price in prices:
            stock_price = StockPrice(
                stock_id=stock.id,
                trade_date=price.trade_date,
                close_price=price.close_price
            )
            self.session.add(stock_price)
        self.session.commit()

    def get_stock_prices(self, stock_code: str, days: int) -> list:
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        return self.session.query(StockPrice)\
            .filter_by(stock_id=stock.id)\
            .order_by(StockPrice.trade_date.desc())\
            .limit(days)\
            .all()