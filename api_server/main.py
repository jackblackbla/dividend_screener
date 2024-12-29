from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# DB 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class StockResponse(BaseModel):
    stock_code: str
    corp_code: str
    stock_name: str

class ApiResponse(BaseModel):
    status: str
    data: Optional[StockResponse] = None
    message: Optional[str] = None

@app.get("/api/v1/stock", response_model=ApiResponse)
async def get_stock_info(code: str = Query(..., description="종목 코드")):
    """
    종목 코드를 사용하여 stocks 테이블에서 해당 종목의 고유번호(corp_code)를 조회합니다.
    """
    try:
        db = SessionLocal()
        
        # 테스트를 위한 임시 하드코딩
        if code == "005930":
            result = {"stock_code": "005930", "corp_code": "00126380", "stock_name": "삼성전자"}
        elif code == "000660":
            result = {"stock_code": "000660", "corp_code": "00164742", "stock_name": "SK하이닉스"}
        else:
            result = None

        if result:
            return ApiResponse(status="success", data=StockResponse(**result))
        else:
            raise HTTPException(status_code=404, detail=f"Stock not found for code: {code}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()