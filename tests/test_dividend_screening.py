import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_mock
from datetime import datetime
from usecases.dividend_screening import DividendScreeningUseCase, ScreeningCriteria
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository
from exceptions import NoPriceDataError

class MockDividendInfo:
    def __init__(self, stock_code, year, dividend_per_share, dividend_yield):
        self.stock_code = stock_code
        self.year = year
        self.dividend_per_share = dividend_per_share
        self.dividend_yield = dividend_yield

@pytest.fixture
def use_case(mocker):
    dividend_repo = DividendInfoRepository(mocker.Mock())
    financial_repo = FinancialStatementRepository(mocker.Mock())
    return DividendScreeningUseCase(dividend_repo, financial_repo)

def test_screen_stocks_basic(use_case, mocker):
    # Mock 데이터 설정
    mock_dividend_info = [
        MockDividendInfo("005930", 2021, 1500.0, 3.5),
        MockDividendInfo("005930", 2022, 1600.0, 3.6),
        MockDividendInfo("005930", 2023, 1700.0, 3.7)
    ]
    use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
    use_case._get_stock_name = mocker.Mock(return_value="삼성전자")

    # 스크리닝 조건 설정
    criteria = ScreeningCriteria(
        min_dividend=1000,
        min_dividend_count=3,
        years_to_consider=3
    )

    # 테스트 실행
    results = use_case.screen_stocks(["005930"], criteria)

    # 결과 검증
    assert len(results["included"]) == 1
    assert results["included"][0].stock_code == "005930"
    assert results["included"][0].dividend_count == 3
    assert results["included"][0].consecutive_years == 3
    assert results["included"][0].dividend_growth > 0

def test_screen_stocks_consecutive_years(use_case, mocker):
    # Mock 데이터 설정 (연속 배당 연도 테스트)
    mock_dividend_info = [
        MockDividendInfo("000660", 2020, 1000.0, 2.5),
        MockDividendInfo("000660", 2021, 1100.0, 2.6),
        MockDividendInfo("000660", 2023, 1200.0, 2.7)  # 2022년 누락
    ]
    use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
    use_case._get_stock_name = mocker.Mock(return_value="SK하이닉스")

    # 스크리닝 조건 설정
    criteria = ScreeningCriteria(
        min_dividend=1000,
        min_dividend_count=3,
        years_to_consider=4,
        min_consecutive_years=3
    )

    # 테스트 실행
    results = use_case.screen_stocks(["000660"], criteria)

    # 결과 검증
    assert len(results["included"]) == 0  # 연속 배당 연도 조건 미달

def test_screen_stocks_dividend_growth(use_case, mocker):
    # Mock 데이터 설정 (배당 성장률 테스트)
    mock_dividend_info = [
        MockDividendInfo("035420", 2021, 500.0, 1.5),
        MockDividendInfo("035420", 2022, 600.0, 1.8),
        MockDividendInfo("035420", 2023, 700.0, 2.0)
    ]
    use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
    use_case._get_stock_name = mocker.Mock(return_value="NAVER")

    # 스크리닝 조건 설정
    criteria = ScreeningCriteria(
        min_dividend=500,
        min_dividend_count=3,
        years_to_consider=3,
        min_dividend_growth=15.0  # 최소 15% 성장률
    )

    # 테스트 실행
    results = use_case.screen_stocks(["035420"], criteria)

    # 결과 검증
    assert len(results["included"]) == 1
    assert results["included"][0].dividend_growth >= 15.0

def test_screen_stocks_no_data(use_case, mocker):
    # Mock 데이터 설정 (데이터 없음)
    use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=[])
    use_case._get_stock_name = mocker.Mock(return_value="없는종목")

    # 스크리닝 조건 설정
    criteria = ScreeningCriteria(
        min_dividend=1000,
        min_dividend_count=1,
        years_to_consider=1
    )

    # 테스트 실행
    results = use_case.screen_stocks(["999999"], criteria)

    # 결과 검증
    assert len(results["included"]) == 0
    assert len(results["excluded"]) == 1

def test_screen_stocks_performance(use_case, mocker):
    # 대량 데이터 성능 테스트
    stock_codes = [f"000{str(i).zfill(3)}" for i in range(200)]  # 200개 종목
    mock_dividend_info = [
        MockDividendInfo(code, 2023, 1500.0, 3.5) for code in stock_codes
    ]
    use_case.dividend_repo.get_dividend_info = mocker.Mock(return_value=mock_dividend_info)
    use_case._get_stock_name = mocker.Mock(return_value="테스트종목")

    criteria = ScreeningCriteria(
        min_dividend=1000,
        min_dividend_count=1,
        years_to_consider=1
    )

    import time
    start_time = time.time()
    results = use_case.screen_stocks(stock_codes, criteria)
    elapsed_time = time.time() - start_time

    assert len(results["included"]) == 200
    print(f"\nPerformance Test: {len(stock_codes)} stocks screened in {elapsed_time:.2f} seconds")