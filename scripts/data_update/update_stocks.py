import pandas as pd
from sqlalchemy import create_engine
from schema import Base, Stock
from sqlalchemy.orm import sessionmaker

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# CSV 파일 읽기
df = pd.read_csv('temp_krx_utf8.csv')

# 데이터베이스에 데이터 삽입
for _, row in df.iterrows():
    stock = Stock(
        code=row['단축코드'],
        name=row['한글 종목약명'],
        market=row['시장구분'],
        listed_date=pd.to_datetime(row['상장일'])
    )
    session.merge(stock)  # 중복 시 업데이트

session.commit()
session.close()