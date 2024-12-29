import requests
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
from exceptions import OpenDartApiError, CorpCodeFetchError

@dataclass
class FinancialStatement:
    year: int
    quarter: int
    sales: float
    operating_profit: float
    net_income: float
    assets: float
    liabilities: float
    equity: float

@dataclass
class DividendInfo:
    year: int
    dividend_per_share: float
    dividend_yield: float
    ex_dividend_date: Optional[datetime]

class OpenDartApiAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
        self.corp_code_map = {
            "005930": "00126380",  # 삼성전자
            # 다른 종목 코드 추가
        }

    def _get_corp_code(self, stock_code: str) -> str:
        return self.corp_code_map.get(stock_code)

    def get_financial_statements(self, stock_code: str, year: int, quarter: int) -> List[FinancialStatement]:
        corp_code = self._get_corp_code(stock_code)
        if not corp_code:
            raise OpenDartApiError(f"Corp code not found for stock code {stock_code}")

        url = f"{self.base_url}/fnlttSinglAcntAll.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011",  # 1분기보고서
            "fs_div": "CFS"  # 연결재무제표
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != '000':
                raise OpenDartApiError(f"API error: {data['message']}")

            results = []
            for item in data['list']:
                if item['fs_nm'] == '연결재무제표' and item['sj_nm'] == '재무상태표':
                    results.append(FinancialStatement(
                        year=year,
                        quarter=quarter,
                        sales=float(item.get('thstrm_amount', 0)),
                        operating_profit=float(item.get('thstrm_amount', 0)),
                        net_income=float(item.get('thstrm_amount', 0)),
                        assets=float(item.get('thstrm_amount', 0)),
                        liabilities=float(item.get('thstrm_amount', 0)),
                        equity=float(item.get('thstrm_amount', 0))
                    ))
            return results

        except requests.exceptions.RequestException as e:
            raise OpenDartApiError(f"API request failed: {str(e)}")

    def get_dividend_info(self, stock_code: str, year: int) -> List[DividendInfo]:
        corp_code = self._get_corp_code(stock_code)
        if not corp_code:
            raise OpenDartApiError(f"Corp code not found for stock code {stock_code}")

        url = f"{self.base_url}/alotMatter.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != '000':
                raise OpenDartApiError(f"API error: {data['message']}")

            results = []
            for item in data['list']:
                ex_dividend_date = None
                if item.get('ex_dividend_date'):
                    ex_dividend_date = datetime.strptime(item['ex_dividend_date'], '%Y-%m-%d')
                
                results.append(DividendInfo(
                    year=year,
                    dividend_per_share=float(item.get('cash_dividend', 0)),
                    dividend_yield=float(item.get('dividend_yield', 0)),
                    ex_dividend_date=ex_dividend_date
                ))
            return results

        except requests.exceptions.RequestException as e:
            raise OpenDartApiError(f"API request failed: {str(e)}")

    def get_dividend_detail_info(self, rcept_no: str) -> dict:
        url = f"{self.base_url}/document.json"
        params = {
            "crtfc_key": self.api_key,
            "rcept_no": rcept_no
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "000":
                raise OpenDartApiError(f"DART API error: {data['message']}")

            ex_dividend_date = None
            if data.get("ex_dividend_date"):
                ex_dividend_date = datetime.strptime(data["ex_dividend_date"], '%Y-%m-%d')

            return {
                "year": int(data["rcept_dt"][:4]),
                "dividend_per_share": float(data["cash_dividend"]),
                "dividend_yield": float(data["dividend_yield"]),
                "ex_dividend_date": ex_dividend_date
            }

        except requests.exceptions.RequestException as e:
            raise OpenDartApiError(f"API request failed: {str(e)}")

    def get_corp_code(self, stock_code: str) -> str:
        """
        종목 코드를 사용하여 B의 API를 호출하고, 고유번호(corp_code)를 반환합니다.

        Args:
            stock_code: 종목 코드

        Returns:
            고유번호(corp_code)

        Raises:
            CorpCodeFetchError: API 호출 실패 시
        """
        try:
            response = requests.get(f"http://localhost:8001/api/v1/stock?code={stock_code}")
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            data = response.json()
            if data["status"] != "success":
                raise ValueError(f"API returned error: {data.get('message')}")
            corp_code = data["data"]["corp_code"]
            if not corp_code:
                raise ValueError("corp_code not found in response")
            return corp_code
        except Exception as e:
            raise CorpCodeFetchError(f"Failed to fetch corp_code for {stock_code}: {e}")