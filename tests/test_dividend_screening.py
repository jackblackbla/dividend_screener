import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_mock
from adapters.opendart_adapter import OpenDartApiAdapter
from exceptions import OpenDartApiError, CorpCodeFetchError

@pytest.fixture
def open_dart_adapter():
    return OpenDartApiAdapter(api_key="test_key")

def test_get_dividend_detail_info(open_dart_adapter, mocker):
    mock_response = {
        "status": "000",
        "rcept_dt": "2023-12-31",
        "cash_dividend": "1500",
        "dividend_yield": "3.5"
    }
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_response, raise_for_status=lambda: None))

    result = open_dart_adapter.get_dividend_detail_info("20231231000123")
    assert result["year"] == 2023
    assert result["dividend_per_share"] == 1500.0
    assert result["dividend_yield"] == 3.5

def test_get_dividend_detail_info_api_error(open_dart_adapter, mocker):
    mock_response = {
        "status": "013",
        "message": "No data found"
    }
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_response, raise_for_status=lambda: None))

    with pytest.raises(OpenDartApiError):
        open_dart_adapter.get_dividend_detail_info("20231231000123")

def test_get_corp_code(open_dart_adapter, mocker):
    mock_response = {
        "status": "success",
        "data": {
            "corp_code": "00126380"
        }
    }
    mocker.patch('requests.get', return_value=mocker.Mock(json=lambda: mock_response, raise_for_status=lambda: None))

    result = open_dart_adapter.get_corp_code("005930")
    assert result == "00126380"

def test_get_corp_code_api_error(open_dart_adapter, mocker):
    mocker.patch('requests.get', side_effect=Exception("API error"))

    with pytest.raises(CorpCodeFetchError):
        open_dart_adapter.get_corp_code("005930")

class TestDividendScreeningUseCase:
    @pytest.fixture
    def use_case(self, mocker):
        from repositories.dividend_info_repository import DividendInfoRepository
        from repositories.financial_statement_repository import FinancialStatementRepository
        from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
        
        dividend_repo = DividendInfoRepository(mocker.Mock())
        financial_repo = FinancialStatementRepository(mocker.Mock())
        return DividendScreeningUseCase(dividend_repo, financial_repo)

    def test_screen_stocks_no_price_data(self, use_case, mocker):
        from exceptions import NoPriceDataError
        from usecases.dividend_screening import ScreeningCriteria
        
        # Mock dividend info
        mock_dividend_info = [
            mocker.Mock(stock_code="005930", dividend_per_share=1500.0, dividend_yield=3.5)
        ]
        use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
        
        # Mock price data to raise NoPriceDataError
        use_case._get_current_price = mocker.Mock(side_effect=NoPriceDataError("No price data"))
        
        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=1,
            years_to_consider=1
        )
        
        results = use_case.screen_stocks(["005930"], criteria)
        
        assert len(results["included"]) == 0
        assert len(results["excluded"]) == 1
        assert results["excluded"][0] == "005930"

    def test_screen_stocks_performance(self, use_case, mocker):
        """대량 데이터에 대한 성능 테스트"""
        from usecases.dividend_screening import ScreeningCriteria
        
        # Mock 데이터 준비
        stock_codes = [f"000{str(i).zfill(3)}" for i in range(200)]  # 200개 종목
        mock_dividend_info = [
            mocker.Mock(stock_code=code, dividend_per_share=1500.0, dividend_yield=3.5)
            for code in stock_codes
        ]
        use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
        use_case._get_current_price = mocker.Mock(return_value=50000.0)  # 고정 주가
        
        criteria = ScreeningCriteria(
            min_dividend_yield=3.0,
            min_dividend_count=1,
            years_to_consider=1
        )
        
        # 성능 측정
        import time
        start_time = time.time()
        results = use_case.screen_stocks(stock_codes, criteria)
        elapsed_time = time.time() - start_time
        
        # 결과 검증
        assert len(results["included"]) == 200
        assert len(results["excluded"]) == 0
        assert all(result.meets_criteria for result in results["included"])
        
        # 성능 로그 출력
        print(f"\nPerformance Test: {len(stock_codes)} stocks screened in {elapsed_time:.2f} seconds")