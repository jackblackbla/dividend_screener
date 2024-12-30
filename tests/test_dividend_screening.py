import pytest
from unittest.mock import Mock, patch
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.stock_price_repository import StockPriceRepository
from schema import Stock, DividendInfo
from exceptions import DividendScreeningError, NoPriceDataError

@pytest.fixture
def mock_repos():
    dividend_repo = Mock(spec=DividendInfoRepository)
    financial_repo = Mock(spec=FinancialStatementRepository)
    stock_price_repo = Mock(spec=StockPriceRepository)
    return dividend_repo, financial_repo, stock_price_repo

@pytest.fixture
def mock_session():
    return Mock()

def test_screen_high_yield_stocks(mock_repos, mock_session):
    dividend_repo, financial_repo, stock_price_repo = mock_repos
    
    # 테스트 데이터 설정
    test_stocks = [
        ('000001', 2023, 1000, 3.5),
        ('000002', 2023, 1500, 4.2)
    ]
    dividend_repo.get_high_yield_stocks.return_value = test_stocks
    
    # 주가 데이터 설정
    stock_price_repo.get_latest_trade_date.return_value = '2023-12-29'
    stock_price_repo.get_prices_by_date.return_value = {
        1: 28571.43,  # 000001: 1000 / 0.035
        2: 35714.29   # 000002: 1500 / 0.042
    }
    
    # 종목 데이터 설정
    mock_stocks = {
        '000001': Mock(id=1, code='000001', name='Company A'),
        '000002': Mock(id=2, code='000002', name='Company B')
    }
    mock_session.query.return_value.filter_by.side_effect = lambda code: Mock(
        first=Mock(return_value=mock_stocks[code])
    )
    
    use_case = DividendScreeningUseCase(
        dividend_repo, financial_repo, stock_price_repo, mock_session
    )
    
    # 테스트 실행
    results = use_case.screen_high_yield_stocks(3.0)
    
    # 결과 검증
    assert len(results) == 2
    assert results[0]['stock_code'] == '000001'
    assert results[0]['stock_name'] == 'Company A'
    assert results[0]['dividend_yield'] == 3.5
    assert results[1]['stock_code'] == '000002'
    assert results[1]['stock_name'] == 'Company B'
    assert results[1]['dividend_yield'] == 4.2

def test_screen_high_yield_stocks_no_price_data(mock_repos, mock_session):
    dividend_repo, financial_repo, stock_price_repo = mock_repos
    
    # 테스트 데이터 설정
    test_stocks = [
        ('000001', 2023, 1000, 3.5)
    ]
    dividend_repo.get_high_yield_stocks.return_value = test_stocks
    
    # 주가 데이터 없음 설정
    stock_price_repo.get_latest_trade_date.return_value = '2023-12-29'
    stock_price_repo.get_prices_by_date.return_value = {}
    
    use_case = DividendScreeningUseCase(
        dividend_repo, financial_repo, stock_price_repo, mock_session
    )
    
    # 테스트 실행
    results = use_case.screen_high_yield_stocks(3.0)
    
    # 결과 검증
    assert len(results) == 0