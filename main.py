from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from adapters.opendart_adapter import OpenDartApiAdapter
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.stock_price_repository import StockPriceRepository
from usecases.fetch_financial_data import FetchFinancialDataUseCase
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from schema import Base, Stock
import os

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 로깅 설정
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/fetch")
async def fetch_financials(stock_code: str, start_year: int, end_year: int):
    db_session = SessionLocal()
    try:
        api_adapter = OpenDartApiAdapter(api_key="e7ad2f9a5e4818f54e3cbcd721eaff15c1a02010")
        fs_repo = FinancialStatementRepository(db_session)
        div_repo = DividendInfoRepository(db_session)
        
        usecase = FetchFinancialDataUseCase(api_adapter, fs_repo, div_repo)
        result = usecase.execute(stock_code, start_year, end_year)
        
        return {"message": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()

@app.get("/api/v1/screen")
async def screen_stocks(
    min_yield: float = 3.0,
    min_count: int = 10,
    min_dividend: float = 100.0,
    limit: int = 5
):
    """배당 스크리닝 API"""
    db_session = SessionLocal()
    try:
        div_repo = DividendInfoRepository(db_session)
        stock_price_repo = StockPriceRepository(db_session)
        
        usecase = DividendScreeningUseCase(
            dividend_repo=div_repo,
            financial_repo=None,
            stock_price_repo=stock_price_repo,
            session=db_session
        )
        
        # 스크리닝 기준 설정
        criteria = ScreeningCriteria(
            min_dividend=min_dividend,
            min_yield=min_yield,
            min_dividend_count=min_count,
            years_to_consider=5
        )
        
        # 모든 종목 코드 가져오기
        stocks = db_session.query(Stock).all()
        stock_codes = [stock.code for stock in stocks]
        
        # 스크리닝 실행
        result = usecase.screen_stocks(stock_codes, criteria)
        return {
            "message": "success",
            "result": result["included"][:limit]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()

@app.get("/screen/high-yield")
async def screen_high_yield_stocks(min_yield: float = 3.0, limit: int = 5):
    db_session = SessionLocal()
    try:
        div_repo = DividendInfoRepository(db_session)
        stock_price_repo = StockPriceRepository(db_session)
        
        usecase = DividendScreeningUseCase(
            dividend_repo=div_repo,
            financial_repo=None,
            stock_price_repo=stock_price_repo,
            session=db_session
        )
        
        result = usecase.screen_high_yield_stocks(min_yield)
        return {"message": "success", "result": result[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()