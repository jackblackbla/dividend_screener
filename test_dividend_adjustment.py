import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dataclasses import dataclass
from datetime import date

logging.basicConfig(level=logging.DEBUG)

@dataclass
class DividendInfo:
    year: int
    dividend_per_share: float
    adjusted_dividend_per_share: float = None

class MockDividendInfoRepository:
    def get_dividend_info(self, stock_code, years_to_consider):
        return [DividendInfo(year=2023, dividend_per_share=1000)]

    def save_stock_issuance_reduction(self, stock_code, issuance_reductions):
        pass

class MockStockIssuanceReduction:
    def __init__(self, event_type, date, factor):
        self.isu_dcrs_stle = event_type
        self.isu_dcrs_de = date
        self.adjust_ratio = factor

class MockStock:
    def __init__(self, code):
        self.code = code
        self.issuance_reductions = []

class MockStockRepository:
    def get_stock(self, stock_code):
        stock = MockStock(stock_code)
        # 다양한 이벤트 추가
        stock.issuance_reductions.extend([
            MockStockIssuanceReduction('무상증자', date(2023, 1, 1), 1.2),  # 20% 무상증자
            MockStockIssuanceReduction('유상증자', date(2023, 3, 1), 1.1),  # 10% 유상증자
            MockStockIssuanceReduction('액면분할', date(2023, 5, 1), 5.0),  # 1:5 액면분할
            MockStockIssuanceReduction('주식배당', date(2023, 7, 1), 1.05), # 5% 주식배당
            MockStockIssuanceReduction('합병', date(2023, 9, 1), 1.3),     # 1:0.3 합병
            MockStockIssuanceReduction('분할합병', date(2023, 11, 1), 1.2) # 1:0.2 분할합병
        ])
        return stock

def test_adjusted_dividend_calculation():
    # 예상 누적 배수 계산
    expected_factor = 1.2 * 1.1 * 5.0 * 1.05 * 1.3 * 1.2
    
    # 테스트 실행
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()

    from usecases.dividend_screening import StockIssuanceReductionUseCase
    use_case = StockIssuanceReductionUseCase(
        MockDividendInfoRepository(),
        session
    )

    # 테스트 결과 검증
    try:
        result = use_case.adjust_dividend_by_factor('005930', 2023, 2023)
        assert result is not None, "Result should not be None"
        assert len(result) > 0, "Result list should not be empty"
        
        adjusted_dividend = result[0].adjusted_dividend_per_share
        expected_value = 1000 / expected_factor
        
        assert abs(adjusted_dividend - expected_value) < 0.01, \
            f"Expected adjusted dividend: {expected_value}, but got {adjusted_dividend}"
            
        print("Test passed successfully!")
        
    except AssertionError as e:
        print(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_adjusted_dividend_calculation()