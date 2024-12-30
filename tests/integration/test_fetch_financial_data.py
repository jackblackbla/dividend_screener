import pytest
from unittest.mock import patch
from adapters.opendart_adapter import OpenDartApiAdapter
from usecases.fetch_financial_data import FetchFinancialDataUseCase
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.stock_repository import StockRepository
from exceptions import ApiError, DatabaseError

@pytest.fixture
def setup_use_case():
    adapter = OpenDartApiAdapter()
    financial_repo = FinancialStatementRepository()
    dividend_repo = DividendInfoRepository()
    stock_repo = StockRepository()
    return FetchFinancialDataUseCase(adapter, financial_repo, dividend_repo, stock_repo)

def test_fetch_and_store_financial_data_success(setup_use_case):
    # Test successful data fetching and storage
    corp_code = "00126380"  # Example corp code
    result = setup_use_case.execute(corp_code)
    
    assert result is not None
    # Add assertions to verify data in database

def test_fetch_financial_data_invalid_corp_code(setup_use_case):
    # Test invalid corp code handling
    with pytest.raises(ApiError):
        setup_use_case.execute("invalid_code")

def test_fetch_financial_data_api_rate_limit(setup_use_case):
    # Test API rate limit handling
    with patch.object(OpenDartApiAdapter, 'get_financial_statement', side_effect=ApiError("Rate limit exceeded")):
        with pytest.raises(ApiError):
            setup_use_case.execute("00126380")

def test_fetch_financial_data_database_error(setup_use_case):
    # Test database error handling
    with patch.object(FinancialStatementRepository, 'save', side_effect=DatabaseError("Database error")):
        with pytest.raises(DatabaseError):
            setup_use_case.execute("00126380")

def test_fetch_financial_data_complete_flow(setup_use_case):
    # Test complete flow from API to database
    corp_code = "00126380"
    result = setup_use_case.execute(corp_code)
    
    # Verify data in all repositories
    stock = setup_use_case.stock_repo.find_by_corp_code(corp_code)
    financials = setup_use_case.financial_repo.find_by_stock_id(stock.id)
    dividends = setup_use_case.dividend_repo.find_by_stock_id(stock.id)
    
    assert stock is not None
    assert financials is not None
    assert dividends is not None