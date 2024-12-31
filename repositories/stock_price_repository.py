from sqlalchemy.orm import Session
from sqlalchemy import func
from config.schema import StockPrice, Stock
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    def get_latest_trade_date(self) -> str:
        """전체 주가 데이터 중 가장 최근 거래일을 반환합니다."""
        logger.debug("Getting latest trade date using func.max")
        try:
            latest_date = self.session.query(
                func.max(StockPrice.trade_date)
            ).scalar()
            logger.debug(f"Latest trade date: {latest_date}")
            return latest_date.strftime('%Y-%m-%d') if latest_date else None
        except Exception as e:
            logger.error(f"Error in get_latest_trade_date: {str(e)}")
            raise

    def get_prices_by_date(self, trade_date: str) -> dict:
        """특정 거래일의 모든 종목 주가를 {stock_id: close_price} 형태로 반환합니다."""
        prices = self.session.query(
            StockPrice.stock_id,
            StockPrice.close_price
        ).filter_by(trade_date=trade_date).all()
        return {stock_id: close_price for stock_id, close_price in prices}