# DividendScreeningUseCase 모듈 문서

## 개요
이 모듈은 주식의 배당 정보를 기반으로 스크리닝을 수행하는 UseCase를 제공합니다. 주어진 조건에 따라 배당률과 배당 횟수를 평가하여 적합한 종목을 필터링합니다.

## 주요 기능
- 주식 코드 리스트에 대한 배당 스크리닝 수행
- 최소 배당률, 최소 배당 횟수, 고려 기간 등의 조건 설정
- 각 종목의 배당 정보 분석 및 평가 결과 반환

## 사용 방법

### ScreeningCriteria 설정
```python
from usecases.dividend_screening import ScreeningCriteria

criteria = ScreeningCriteria(
    min_dividend_yield=3.0,  # 최소 배당률 (%)
    min_dividend_count=3,    # 최소 배당 횟수
    years_to_consider=3      # 고려 기간 (년)
)
```

### DividendScreeningUseCase 사용 예제
```python
from usecases.dividend_screening import DividendScreeningUseCase
from repositories.dividend_info_repository import DividendInfoRepository
from repositories.financial_statement_repository import FinancialStatementRepository

# Repository 초기화
dividend_repo = DividendInfoRepository()
financial_repo = FinancialStatementRepository()

# UseCase 초기화
use_case = DividendScreeningUseCase(dividend_repo, financial_repo)

# 스크리닝 수행
results = use_case.screen_stocks(
    stock_codes=['005930', '000660'],
    criteria=criteria
)

# 결과 확인
for result in results:
    print(f"Stock: {result.stock_code}")
    print(f"Dividend Yield: {result.dividend_yield:.2f}%")
    print(f"Dividend Count: {result.dividend_count}")
    print(f"Meets Criteria: {result.meets_criteria}")
    print("---")
```

## 응답 구조
- `ScreeningResult` 데이터 클래스:
  - `stock_code`: 주식 코드
  - `dividend_yield`: 평균 배당률
  - `dividend_count`: 배당 횟수
  - `meets_criteria`: 조건 충족 여부

## 예외 처리
- `DividendScreeningError`: 스크리닝 과정에서 발생하는 모든 예외를 캡슐화
  - 잘못된 입력 값
  - 데이터 조회 실패
  - 계산 오류 등

## 테스트 결과
- 단위 테스트 6개 케이스 모두 통과
  - test_calculate_average_dividend_yield
  - test_calculate_average_dividend_yield_with_empty_list
  - test_calculate_dividend_count
  - test_screen_stocks_with_empty_stock_codes
  - test_screen_stocks_with_invalid_criteria
  - test_screen_stocks_with_valid_criteria