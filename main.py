from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from adapters.opendart_adapter import OpenDartApiAdapter
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.dividend_info_repository import DividendInfoRepository
from usecases.fetch_financial_data import FetchFinancialDataUseCase
from schema import Base
import os

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

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