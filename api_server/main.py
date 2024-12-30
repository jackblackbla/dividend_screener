from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.stock_price_repository import StockPriceRepository
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 콘솔 핸들러 추가
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

app = FastAPI()

# DB 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class StockResponse(BaseModel):
    stock_code: str
    stock_name: str

class ApiResponse(BaseModel):
    status: str
    data: Optional[StockResponse] = None
    message: Optional[str] = None

@app.get("/api/v1/stock", response_model=ApiResponse)
async def get_stock_info(code: str = Query(..., description="종목 코드")):
    """
    종목 코드를 사용하여 stocks 테이블에서 해당 종목 정보를 조회합니다.
    """
    with SessionLocal() as db:
        # stocks 테이블에서 종목 코드로 조회
        result = db.execute(
            text("SELECT code, name FROM stocks WHERE code = :code"),
            {"code": code}
        ).fetchone()

        if result:
            return ApiResponse(
                status="success",
                data=StockResponse(
                    stock_code=result[0],
                    stock_name=result[1]
                )
            )
        else:
            raise HTTPException(status_code=404, detail=f"Stock not found for code: {code}")

class ScreeningResult(BaseModel):
    stock_code: str
    stock_name: str
    dividend_per_share: float
    dividend_count: int
    consecutive_years: int
    dividend_growth: float
    meets_criteria: bool

class ScreeningResponse(BaseModel):
    status: str
    data: List[ScreeningResult]
    message: Optional[str] = None
    criteria: dict
    timestamp: str

@app.get("/api/v1/screen", response_model=ScreeningResponse)
async def screen_stocks(
    min_dividend: float = Query(0, description="최소 배당금"),
    min_yield: float = Query(0.0, description="최소 배당률"),
    min_count: int = Query(3, description="최소 배당 횟수"),
    years: int = Query(5, description="고려할 연도 수"),
    min_consecutive_years: Optional[int] = Query(None, description="최소 연속 배당 연도 수"),
    min_dividend_growth: Optional[float] = Query(None, description="최소 배당 성장률")
):
    """
    배당 스크리닝 조건에 맞는 종목들을 조회합니다.
    """
    try:
        db = SessionLocal()
        
        # Repository 초기화
        dividend_repo = DividendInfoRepository(db)
        financial_repo = FinancialStatementRepository(db)
        
        # Repository 및 UseCase 초기화
        stock_price_repo = StockPriceRepository(db)
        use_case = DividendScreeningUseCase(dividend_repo, financial_repo, stock_price_repo, db)
        
        # 모든 종목 코드 가져오기
        stock_codes = [row[0] for row in db.execute(text("SELECT code FROM stocks")).fetchall()]
        
        # 스크리닝 조건 설정
        criteria = ScreeningCriteria(
            min_dividend=min_dividend,
            min_yield=min_yield,
            min_dividend_count=min_count,
            years_to_consider=years,
            min_consecutive_years=min_consecutive_years,
            min_dividend_growth=min_dividend_growth
        )
        
        # 스크리닝 실행
        result = use_case.screen_stocks(stock_codes, criteria)
        
        return ScreeningResponse(
            status="success",
            data=result["included"],
            criteria={
                "min_dividend": min_dividend,
                "min_yield": min_yield,
                "min_count": min_count,
                "years": years,
                "min_consecutive_years": min_consecutive_years,
                "min_dividend_growth": min_dividend_growth
            },
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error during screening: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)