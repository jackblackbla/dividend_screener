from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
    dividend_yield: float
    consecutive_years: int

class ScreeningResponse(BaseModel):
    status: str
    data: List[ScreeningResult]
    message: Optional[str] = None

@app.get("/api/v1/screen", response_model=ScreeningResponse)
async def screen_stocks(
    min_yield: float = Query(3.0, description="최소 배당률"),
    years: int = Query(5, description="연속 배당 년수"),
    min_count: int = Query(1, description="최소 배당 횟수")
):
    """
    배당 스크리닝 조건에 맞는 종목들을 조회합니다.
    """
    try:
        db = SessionLocal()
        
        # 임시 하드코딩 데이터
        results = [
            {"stock_code": "005930", "stock_name": "삼성전자", "dividend_yield": 3.2, "consecutive_years": 5},
            {"stock_code": "000660", "stock_name": "SK하이닉스", "dividend_yield": 3.5, "consecutive_years": 6}
        ]
        
        filtered_results = [
            result for result in results
            if result["dividend_yield"] >= min_yield and
            result["consecutive_years"] >= years
        ][:min_count]

        return ScreeningResponse(
            status="success",
            data=[ScreeningResult(**result) for result in filtered_results]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()