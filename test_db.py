from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock, FinancialStatement, DividendInfo

# 데이터베이스 연결 설정
engine = create_engine('mysql+pymysql://root:@localhost:3306/dividend')
Session = sessionmaker(bind=engine)
session = Session()

# 테스트 데이터 삽입
try:
    # 주식 데이터 추가
    stock = Stock(code="005930", name="삼성전자", market="KOSPI", industry="전자제품")
    session.add(stock)
    session.commit()

    # 재무제표 데이터 추가
    fs = FinancialStatement(
        stock_id=stock.id,
        year=2023,
        quarter=4,
        sales=300000,
        operating_profit=40000,
        net_income=35000,
        assets=500000,
        liabilities=200000,
        equity=300000
    )
    session.add(fs)
    session.commit()

    # 배당 정보 데이터 추가
    div = DividendInfo(
        stock_id=stock.id,
        year=2023,
        dividend_per_share=1416,
        dividend_yield=2.5,
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