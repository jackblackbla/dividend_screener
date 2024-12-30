from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock, DividendInfo
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_dividend_history_by_code(stock_code):
    session = Session()
    try:
        # 주식 코드로 Stock 정보 조회
        stock = session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            logger.error(f"Stock not found for code: {stock_code}")
            return None

        # 해당 주식의 연도별 배당금 정보 조회
        dividends = session.query(DividendInfo)\
            .filter_by(stock_id=stock.id)\
            .order_by(DividendInfo.year)\
            .all()

        if not dividends:
            logger.info(f"No dividend data found for {stock_code}")
            return None

        # 결과 출력
        logger.info(f"Dividend history for {stock_code} ({stock.name}):")
        for dividend in dividends:
            logger.info(f"Year: {dividend.year}, Dividend: {dividend.dividend_per_share}원, Yield: {dividend.dividend_yield}%")

        return dividends

    except Exception as e:
        logger.error(f"Error fetching dividend history: {str(e)}")
        return None

    finally:
        session.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python get_dividend_by_code.py [stock_code]")
        sys.exit(1)

    stock_code = sys.argv[1]
    get_dividend_history_by_code(stock_code)