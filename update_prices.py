import argparse
from datetime import datetime
from krx_ticker_fetcher import save_prices_to_db

def main():
    parser = argparse.ArgumentParser(description='Update stock prices from KRX')
    parser.add_argument('date', type=str, help='Date in YYYYMMDD format')
    
    args = parser.parse_args()
    
    # 날짜 형식 검증
    try:
        datetime.strptime(args.date, '%Y%m%d')
    except ValueError:
        print("Error: Invalid date format. Please use YYYYMMDD format.")
        return
    
    # 주가 데이터 수집 및 저장
    save_prices_to_db(args.date)
    print(f"Stock prices for {args.date} updated successfully.")

if __name__ == "__main__":
    main()