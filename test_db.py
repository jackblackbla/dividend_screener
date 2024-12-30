from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock, FinancialStatement, DividendInfo

# 데이터베이스 연결 설정
engine = create_engine('mysql+pymysql://root:@localhost:3306/dividend')
Session = sessionmaker(bind=engine)
session = Session()

# 테스트 데이터 삽입
try:
    # 대량 테스트 데이터 추가
    stocks = [
        Stock(code="005930", name="삼성전자", market="KOSPI", industry="전자제품"),
        Stock(code="000660", name="SK하이닉스", market="KOSPI", industry="반도체"),
        Stock(code="035420", name="NAVER", market="KOSPI", industry="인터넷"),
        Stock(code="051910", name="LG화학", market="KOSPI", industry="화학"),
        Stock(code="005380", name="현대차", market="KOSPI", industry="자동차"),
        # ... (추가 종목 데이터)
    ]
    
    # 200개 종목 데이터 생성
    for i in range(200):
        code = f"000{str(i).zfill(3)}"
        stock = Stock(
            code=code,
            name=f"테스트종목{i}",
            market="KOSPI",
            industry="테스트산업"
        )
        stocks.append(stock)
    
    session.add_all(stocks)
    session.commit()

    # 재무제표 및 배당 정보 데이터 추가
    for stock in stocks:
        # 재무제표 데이터
        fs = FinancialStatement(
            stock_id=stock.id,
            year=2023,
            quarter=4,
            sales=300000 + (stock.id * 1000),
            operating_profit=40000 + (stock.id * 100),
            net_income=35000 + (stock.id * 100),
            assets=500000 + (stock.id * 1000),
            liabilities=200000 + (stock.id * 500),
            equity=300000 + (stock.id * 500)
        )
        session.add(fs)

        # 배당 정보 데이터
        div = DividendInfo(
            stock_id=stock.id,
            year=2023,
            dividend_per_share=1416 + (stock.id * 10),
            dividend_yield=2.5 + (stock.id * 0.1),
            ex_dividend_date="2023-12-15"
        )
        session.add(div)
    
    session.commit()

    # 데이터 조회
    retrieved_stock = session.query(Stock).filter_by(code="005930").first()
    print(f"Stock: {retrieved_stock.name}")

    retrieved_fs = session.query(FinancialStatement).filter_by(stock_id=stock.id, year=2023, quarter=4).first()
    print(f"Sales: {retrieved_fs.sales}")

    retrieved_div = session.query(DividendInfo).filter_by(stock_id=stock.id, year=2023).first()
    print(f"Dividend: {retrieved_div.dividend_per_share}")

finally:
    session.close()