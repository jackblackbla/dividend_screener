import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from exceptions import OpenDartApiError, CorpCodeFetchError

@dataclass
class StockIssuanceReduction:
    corp_code: str
    rcept_no: str
    isu_dcrs_de: Optional[datetime]
    isu_dcrs_stle: str
    isu_dcrs_stock_knd: str
    isu_dcrs_qy: int
    isu_dcrs_mstvdv_fval_amount: float
    isu_dcrs_mstvdv_amount: float
    stlm_dt: Optional[datetime]
    adjust_ratio: Optional[float]  # 무상증자/감자/분할 등에 따른 주식수 변동 배수

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
    def __init__(self):
        from config import DART_API_KEY
        self.api_key = DART_API_KEY
        print(f"Using DART_API_KEY = '{self.api_key}' (length={len(self.api_key) if self.api_key else 0})")  # API 키 로깅 추가
        self.base_url = "https://opendart.fss.or.kr/api"
        self.corp_code_map = {
            "005930": "00126380",  # 삼성전자
            "000660": "00164742",  # SK하이닉스
            "003920": "00164743",  # 푸드웰
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
            print(f"API Response: {data}")  # API 응답 로깅
            print(f"Request URL: {response.url}")  # 요청 URL 로깅
            print(f"Status Code: {response.status_code}")  # 상태 코드 로깅
            
            if data['status'] != '000':
                raise OpenDartApiError(f"API error: {data['message']}")

            results = []
            for item in data['list']:
                if item.get('fs_nm') == '연결재무제표':
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
                    break  # 첫 번째 유효한 항목만 처리
            return results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise OpenDartApiError("API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise OpenDartApiError("Invalid request parameters. Please check your input.")
            else:
                raise OpenDartApiError(f"API request failed with status code {e.response.status_code}: {str(e)}")
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
            "reprt_code": "11011"  # 사업보고서
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != '000':
                raise OpenDartApiError(f"API error: {data['message']}")

            results = []
            for item in data['list']:
                # 보통주 배당 정보만 추출
                if item.get('stock_knd') == '보통주' and item.get('se') == '주당 현금배당금(원)':
                    dividend_per_share = float(item.get('thstrm', '0').replace(',', ''))  # 당기 배당금
                    dividend_yield = float(item.get('thstrm', '0').replace(',', ''))  # 당기 배당수익률
                    ex_dividend_date = None
                    if item.get('stlm_dt'):  # 결산기준일
                        ex_dividend_date = datetime.strptime(item['stlm_dt'], '%Y-%m-%d')
                    
                    results.append(DividendInfo(
                        year=year,
                        dividend_per_share=dividend_per_share,
                        dividend_yield=dividend_yield,
                        ex_dividend_date=ex_dividend_date
                    ))
                    break  # 보통주 정보만 필요하므로 첫 번째 항목 처리 후 종료
            return results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise OpenDartApiError("API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise OpenDartApiError("Invalid request parameters. Please check your input.")
            else:
                raise OpenDartApiError(f"API request failed with status code {e.response.status_code}: {str(e)}")
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

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise OpenDartApiError("API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise OpenDartApiError("Invalid request parameters. Please check your input.")
            else:
                raise OpenDartApiError(f"API request failed with status code {e.response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise OpenDartApiError(f"API request failed: {str(e)}")

    def get_stock_issuance_reduction(self, stock_code: str, year: int, reprt_code: str) -> List[StockIssuanceReduction]:
        corp_code = self._get_corp_code(stock_code)
        if not corp_code:
            raise OpenDartApiError(f"Corp code not found for stock code {stock_code}")

        url = f"{self.base_url}/irdsSttus.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": reprt_code
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"API Response: {data}")  # API 응답 로깅
            print(f"Request URL: {response.url}")  # 요청 URL 로깅
            print(f"Status Code: {response.status_code}")  # 상태 코드 로깅

            if data['status'] != '000':
                raise OpenDartApiError(f"API error: {data['message']}")

            results = []
            for item in data['list']:
                isu_dcrs_de = datetime.strptime(item['isu_dcrs_de'], '%Y-%m-%d') if item['isu_dcrs_de'] != '-' else None
                stlm_dt = datetime.strptime(item['stlm_dt'], '%Y-%m-%d') if item['stlm_dt'] != '-' else None

                results.append(StockIssuanceReduction(
                    corp_code=corp_code,
                    rcept_no=item['rcept_no'],
                    isu_dcrs_de=isu_dcrs_de,
                    isu_dcrs_stle=item['isu_dcrs_stle'],
                    isu_dcrs_stock_knd=item['isu_dcrs_stock_knd'],
                    isu_dcrs_qy=int(item['isu_dcrs_qy']) if item['isu_dcrs_qy'] != '-' else 0,
                    isu_dcrs_mstvdv_fval_amount=float(item['isu_dcrs_mstvdv_fval_amount']) if item['isu_dcrs_mstvdv_fval_amount'] != '-' else 0.0,
                    isu_dcrs_mstvdv_amount=float(item['isu_dcrs_mstvdv_amount']) if item['isu_dcrs_mstvdv_amount'] != '-' else 0.0,
                    stlm_dt=stlm_dt,
                    adjust_ratio=None  # 추후 계산 필요
                ))

            return results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise OpenDartApiError("API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise OpenDartApiError("Invalid request parameters. Please check your input.")
            else:
                raise OpenDartApiError(f"API request failed with status code {e.response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise OpenDartApiError(f"API request failed: {str(e)}")

    def calculate_adjustment_factors(self, stock_code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        주어진 기간 동안의 자본변동 이벤트를 수집하고 무상조정계수를 계산
        
        Args:
            stock_code: 종목 코드
            start_date: 조회 시작일 (YYYY-MM-DD)
            end_date: 조회 종료일 (YYYY-MM-DD)
            
        Returns:
            이벤트 리스트 (날짜, 이벤트 타입, 배수, 누적 배수 포함)
        """
        corp_code = self._get_corp_code(stock_code)
        if not corp_code:
            raise OpenDartApiError(f"Corp code not found for stock code {stock_code}")

        # 이벤트 타입별로 데이터 수집
        events = []
        # 이벤트 타입별로 데이터 수집
        events = []
        for event_type in ['무상증자', '무상감자', '유상증자', '액면분할', '주식배당', '합병', '분할합병']:
            try:
                df = self.get_stock_issuance_reduction(stock_code, int(start_date[:4]), '11011')
                if df is not None:
                    for item in df:
                        if item.isu_dcrs_de and start_date <= item.isu_dcrs_de.strftime('%Y-%m-%d') <= end_date:
                            # 이벤트 타입에 따라 배수 계산
                            factor = 1.0
                            if event_type == '무상증자':
                                factor = 1 + (item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount)
                            elif event_type == '무상감자':
                                factor = item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount
                            elif event_type == '유상증자':
                                factor = 1 + (item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount)
                            elif event_type == '액면분할':
                                factor = item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount
                            elif event_type == '주식배당':
                                factor = 1 + (item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount)
                            elif event_type == '합병':
                                # 합병비율 계산 (예: 1:0.5 합병 → factor = 1.5)
                                factor = 1 + (item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount)
                            elif event_type == '분할합병':
                                # 분할합병비율 계산 (예: 1:0.3 분할합병 → factor = 1.3)
                                factor = 1 + (item.isu_dcrs_qy / item.isu_dcrs_mstvdv_fval_amount)
                            events.append({
                                'date': item.isu_dcrs_de.strftime('%Y-%m-%d'),
                                'type': event_type,
                                'factor': factor,
                                'cumulative_factor': 1.0  # 초기값, 추후 계산
                            })
            except OpenDartApiError:
                continue

        # 날짜 순으로 정렬
        events.sort(key=lambda x: x['date'])

        # 누적 배수 계산
        cumulative_factor = 1.0
        for event in events:
            cumulative_factor *= event['factor']
            event['cumulative_factor'] = cumulative_factor

        return events

    def process_issuance_reduction(self, stock_code: str, year: int) -> None:
        """
        주식 발행 감소 데이터를 처리하고 데이터베이스에 저장합니다.

        Args:
            stock_code: 종목 코드
            year: 조회 연도

        Raises:
            OpenDartApiError: API 호출 실패 시
        """
        from sqlalchemy.orm import Session
        from repositories.dividend_info_repository import DividendInfoRepository
        from repositories.stock_price_repository import StockPriceRepository
        from repositories.financial_statement_repository import FinancialStatementRepository
        
        session = Session()
        try:
            data = self.get_stock_issuance_reduction(stock_code, year, "11011")
            
            if not data:
                logger.warning(f"No issuance reduction data found for {stock_code} ({year})")
                return

            for item in data:
                event_date = item.isu_dcrs_de
                event_type = item.isu_dcrs_stle
                qty = item.isu_dcrs_qy
                face_value = item.isu_dcrs_mstvdv_fval_amount
                
                # 이벤트 처리 로직 추가
                if event_type and qty != 0:
                    # 데이터베이스 저장 로직
                    pass

            session.commit()
        except Exception as e:
            logger.error(f"Error processing issuance reduction for {stock_code}: {str(e)}")
            session.rollback()
        finally:
            session.close()

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
            response = requests.get(f"http://localhost:8002/api/v1/stock?code={stock_code}")
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
            data = response.json()
            if data["status"] != "success":
                raise ValueError(f"API returned error: {data.get('message')}")
            corp_code = data["data"]["corp_code"]
            if not corp_code:
                raise ValueError("corp_code not found in response")
            return corp_code
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise CorpCodeFetchError("API rate limit exceeded. Please try again later.")
            elif e.response.status_code == 400:
                raise CorpCodeFetchError("Invalid request parameters. Please check your input.")
            else:
                raise CorpCodeFetchError(f"API request failed with status code {e.response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise CorpCodeFetchError(f"API request failed: {str(e)}")