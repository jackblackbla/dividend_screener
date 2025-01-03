from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from usecases.dividend_screening import StockIssuanceReductionUseCase
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.stock_price_repository import StockPriceRepository
from config.schema import Stock, DividendInfo, StockIssuanceReduction
import logging
from datetime import datetime

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

# CORS 설정 (필요에 맞게 allow_origins 수정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --------------------------------------------
# MODELS FOR API RESPONSES
# --------------------------------------------

class StockResponse(BaseModel):
    stock_code: str
    stock_name: str

class ApiResponse(BaseModel):
    status: str
    data: Optional[StockResponse] = None
    message: Optional[str] = None

class ScreeningResult(BaseModel):
    stock_code: str
    stock_name: str
    dividend_per_share: float
    dividend_yield: float
    dividend_count: int
    consecutive_years: int
    long_term_growth: float  # 장기 배당 성장률
    short_term_growth: float  # 단기 배당 성장률
    meets_criteria: bool
    latest_close_price: Optional[float] = None

class ScreeningResponse(BaseModel):
    status: str
    data: List[ScreeningResult]
    message: Optional[str] = None
    criteria: dict
    timestamp: str

class IssuanceReductionResponse(BaseModel):
    status: str
    data: List[Dict]
    message: Optional[str] = None

# --------------------------------------------
# ENDPOINTS
# --------------------------------------------

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


@app.get("/api/v1/screen", response_model=ScreeningResponse)
async def screen_stocks(
    # 기존 필터들
    min_yield: float = Query(0.0, description="최소 배당수익률 (%)"),
    min_count: int = Query(1, description="최소 배당 횟수"),
    years: int = Query(5, description="조회할 연도 수"),
    consecutive_years: int = Query(0, description="최소 연속 배당 연도"),
    min_dividend: float = Query(0.0, description="최소 배당금"),
    limit: int = Query(100, description="결과 제한 수"),
    market_cap: Optional[float] = Query(None, description="최소 시가총액 (억원)"),
    avoid_div_cut: Optional[bool] = Query(False, description="배당감소 제외"),
    sector: Optional[str] = Query(None, description="업종"),

    # 새로 추가된 필터
    min_growth_rate: float = Query(0.0, description="최소 배당성장률(%) (최근 n년간)")
):
    """
    배당주 스크리닝 API

    고급 필터에 '배당성장률(min_growth_rate)' 파라미터를 새로 추가.
    프론트에서 '?min_growth_rate=5' 형태로 전달하면,
    백엔드에서 DB(사전 계산된 dividend_growth_3y 등)를 활용해
    필터링할 수 있다.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting screening with criteria: {locals()}")
        
        # Repository 초기화
        dividend_repo = DividendInfoRepository(db)
        financial_repo = FinancialStatementRepository(db)
        stock_price_repo = StockPriceRepository(db)
        
        # UseCase 초기화
        use_case = DividendScreeningUseCase(
            dividend_repo=dividend_repo,
            financial_repo=financial_repo,
            stock_price_repo=stock_price_repo,
            session=db
        )
        
        # 스크리닝 기준 설정
        criteria = ScreeningCriteria(
            min_dividend=min_dividend,
            min_yield=min_yield,
            min_dividend_count=min_count,
            years_to_consider=years,
            min_consecutive_years=consecutive_years,
            avoid_div_cut=avoid_div_cut,
            min_dividend_growth=min_growth_rate  # 배당성장률 필드
        )
        
        # 종목 코드 조회 쿼리 (market_cap, sector 등)
        query = text("""
            SELECT DISTINCT s.code
            FROM dividend_v2.stocks s
            LEFT JOIN dividend_v2.market m ON s.stock_id = m.stock_id
            WHERE 1=1
            AND (:market_cap IS NULL OR m.market_cap >= :market_cap)
            AND (:sector IS NULL OR s.sector = :sector)
        """)
        
        # market_cap은 원 단위로 저장되어 있음
        market_cap_raw = market_cap if market_cap else None
        logger.debug(f"market_cap input: {market_cap} -> market_cap_raw: {market_cap_raw}")

        query_result = db.execute(
            query,
            {
                "market_cap": market_cap_raw,
                "sector": sector
            }
        ).fetchall()
        
        logger.debug(f"DB query result: {query_result}")
        
        stock_codes = [row[0] for row in query_result]
        
        if not stock_codes:
            return ScreeningResponse(
                status="success",
                data=[],
                message="No stocks found matching the criteria",
                criteria=criteria.__dict__,
                timestamp=datetime.now().isoformat()
            )
        
        # 스크리닝 실행
        # (screen_stocks() -> dict with included[] / excluded[].)
        # Suppose the 'screen_stocks()' returns a dict with format:
        # {
        #   "included": [ { ... }, { ... } ],
        #   "excluded": [ ... ],
        #   "criteria": { ... },
        #   "timestamp": "...",
        # }
        #
        # We'll reshape it to ScreeningResponse
        result_dict = use_case.screen_stocks(stock_codes[:limit], criteria)
        
        # "included" -> transform to a list of ScreeningResult
        included_list = []
        if "included" in result_dict:
            for item in result_dict["included"]:
                included_list.append(
                    ScreeningResult(
                        stock_code=item.get("stock_code"),
                        stock_name=item.get("stock_name"),
                        dividend_per_share=item.get("dividend_per_share", 0.0),
                        dividend_yield=item.get("dividend_yield", 0.0),
                        dividend_count=item.get("dividend_count", 0),
                        consecutive_years=item.get("consecutive_years", 0),
                        long_term_growth=item.get("long_term_growth", 0.0),
                        short_term_growth=item.get("short_term_growth", 0.0),
                        meets_criteria=item.get("meets_criteria", False),
                        latest_close_price=item.get("latest_close_price")
                    )
                )

        logger.info(f"Screening completed. Found {len(included_list)} matching stocks")
        logger.debug(f"Screening details: {result_dict.get('criteria', {})}")
        
        return ScreeningResponse(
            status="success",
            data=included_list,
            message="Screening completed",
            criteria=result_dict.get("criteria", {}),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error during screening: {str(e)}", exc_info=True)
        logger.error(f"Screening criteria at error: {criteria.__dict__}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/v1/issuance-reduction", response_model=IssuanceReductionResponse)
async def process_issuance_reduction(
    stock_code: str = Query(..., description="종목 코드"),
    year: int = Query(..., description="사업연도"),
    reprt_code: str = Query(..., description="보고서 코드")
):
    """
    증자(감자) 현황 데이터를 처리합니다.
    """
    db = SessionLocal()
    try:
        # Repository 초기화
        dividend_repo = DividendInfoRepository(db)
        
        # UseCase 초기화
        use_case = StockIssuanceReductionUseCase(dividend_repo, db)
        
        # 증자(감자) 현황 데이터 처리
        use_case.process_issuance_reduction(stock_code, year, reprt_code)
        
        return IssuanceReductionResponse(
            status="success",
            data=[],
            message="Issuance reduction data processed successfully"
        )
    except Exception as e:
        logger.error(f"Error processing issuance reduction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

def _get_stock_id(db, stock_code: str) -> int:
    """주식 코드를 사용하여 주식 ID를 조회합니다."""
    stock = db.query(Stock).filter_by(code=stock_code).first()
    if stock:
        return stock.stock_id
    raise ValueError(f"Stock with code {stock_code} not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)