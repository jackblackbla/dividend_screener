# 주가 데이터 수집 모듈

## 개요
이 모듈은 KRX(Korea Exchange)에서 KOSPI와 KOSDAQ의 주가(종가) 데이터를 수집하여 데이터베이스에 저장하는 기능을 제공합니다.

## 사용 방법

### 스크립트 실행
```bash
python update_prices.py YYYYMMDD
```

예시:
```bash
python update_prices.py 20241230
```

### 주요 기능
1. KRX에서 KOSPI와 KOSDAQ 주가 데이터 다운로드
2. 데이터 병합 및 중복 제거
3. 데이터베이스에 저장 (stock_prices 테이블)

## 데이터베이스 스키마
```sql
CREATE TABLE stock_prices (
  id INT PRIMARY KEY,
  stock_id INT REFERENCES stocks(id),
  trade_date DATE NOT NULL,
  close_price DECIMAL(12,2) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(stock_id, trade_date)
);
```

## 파라미터
- `date`: 주가 데이터를 수집할 날짜 (YYYYMMDD 형식)

## 예제 데이터
| stock_id | trade_date | close_price | created_at          |
|----------|------------|-------------|---------------------|
| 1        | 2024-12-30 | 75000.00    | 2024-12-30 09:00:00 |
| 2        | 2024-12-30 | 150000.00   | 2024-12-30 09:00:00 |

## 주의사항
1. KRX API는 영업일 데이터만 제공
2. 데이터 수집 후 DB에 저장되기 전에 중복 검사 수행
3. 인코딩은 cp949로 처리