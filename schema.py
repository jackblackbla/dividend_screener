from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    market = Column(String(50))  # 시장 구분 (KOSPI, KOSDAQ 등)
    industry = Column(String(255))  # 업종
    listed_date = Column(Date)  # 상장일
    financial_statements = relationship("FinancialStatement", back_populates="stock")
    dividend_info = relationship("DividendInfo", back_populates="stock")

class FinancialStatement(Base):
    __tablename__ = 'financial_statements'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1, 2, 3, 4
    sales = Column(Numeric(20, 2))  # 매출액
    operating_profit = Column(Numeric(20, 2))  # 영업이익
    net_income = Column(Numeric(20, 2))  # 당기순이익
    assets = Column(Numeric(20, 2))  # 자산총계
    liabilities = Column(Numeric(20, 2))  # 부채총계
    equity = Column(Numeric(20, 2))  # 자본총계
    stock = relationship("Stock", back_populates="financial_statements")

class DividendInfo(Base):
    __tablename__ = 'dividend_info'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    year = Column(Integer, nullable=False)
    dividend_per_share = Column(Numeric(20, 2))  # 주당 배당금
    dividend_yield = Column(Numeric(5, 2))  # 배당수익률
    ex_dividend_date = Column(Date)  # 배당락일
    stock = relationship("Stock", back_populates="dividend_info")