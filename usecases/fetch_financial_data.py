from typing import List
from adapters.opendart_adapter import OpenDartApiAdapter
from repositories.financial_statement_repository import FinancialStatementRepository
from repositories.dividend_info_repository import DividendInfoRepository

class FetchFinancialDataUseCase:
    def __init__(self, 
                 api_adapter: OpenDartApiAdapter,
                 fs_repository: FinancialStatementRepository,
                 div_repository: DividendInfoRepository):
        self.api_adapter = api_adapter
        self.fs_repository = fs_repository
        self.div_repository = div_repository

    def execute(self, stock_code: str, start_year: int, end_year: int) -> dict:
        results = {
            'financial_statements': [],
            'dividend_info': []
        }

        # 재무제표 데이터 가져오기 및 저장
        for year in range(start_year, end_year + 1):
            for quarter in range(1, 5):
                try:
                    financials = self.api_adapter.get_financial_statements(stock_code, year, quarter)
                    self.fs_repository.save_financial_statements(stock_code, financials)
                    results['financial_statements'].extend(financials)
                except Exception as e:
                    print(f"Error fetching financial statements for {year} Q{quarter}: {str(e)}")

        # 배당 정보 가져오기 및 저장
        for year in range(start_year, end_year + 1):
            try:
                dividends = self.api_adapter.get_dividend_info(stock_code, year)
                self.div_repository.save_dividend_info(stock_code, dividends)
                results['dividend_info'].extend(dividends)
            except Exception as e:
                print(f"Error fetching dividend info for {year}: {str(e)}")

        return results