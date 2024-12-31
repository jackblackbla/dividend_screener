import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Stock

# 데이터베이스 연결 설정
DATABASE_URL = "mysql+pymysql://root@localhost:3306/dividend"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# OpenDART API 키 설정
API_KEY = "e7ad2f9a5e4818f54e3cbcd721eaff15c1a02010"

# OpenDART에서 corpCode.zip 다운로드
url = "https://opendart.fss.or.kr/api/corpCode.xml"
params = {"crtfc_key": API_KEY}
response = requests.get(url, params=params)

# ZIP 파일 압축 해제
with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
    with zip_file.open('CORPCODE.xml') as xml_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

# corp_code 매핑
for item in root.findall("list"):
    stock_code = item.find("stock_code").text
    corp_code = item.find("corp_code").text
    
    # stocks 테이블 업데이트
    stock = session.query(Stock).filter_by(code=stock_code).first()
    if stock:
        stock.corp_code = corp_code

session.commit()
session.close()