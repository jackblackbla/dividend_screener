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
        "corp_code": "00126380"
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
        
        assert len(results) == 1
        assert results[0].stock_code == "005930"
        assert results[0].dividend_yield == 0.0
        assert results[0].dividend_count == 1
        assert results[0].meets_criteria is False