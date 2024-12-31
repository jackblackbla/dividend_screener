from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    corp_code = Column(String(8), unique=True)  # DART 고유번호
    name = Column(String(255), nullable=False)
    market = Column(String(50))  # 시장 구분 (KOSPI, KOSDAQ 등)
    industry = Column(String(255))  # 업종
    listed_date = Column(Date)  # 상장일
    financial_statements = relationship("FinancialStatement", back_populates="stock")
    dividend_info = relationship("DividendInfo", back_populates="stock")
    dividend_yields = relationship("DividendYield", back_populates="stock")

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

class DividendYield(Base):
    __tablename__ = 'dividend_yields'
    __table_args__ = (
        UniqueConstraint('stock_id', 'date', name='uq_dividend_yield'),
    )

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(Date, nullable=False)  # 배당률 계산일
    yield_value = Column(Numeric(5, 2), nullable=False)  # 배당수익률
    stock = relationship("Stock", back_populates="dividend_yields")

class DividendInfo(Base):
    __tablename__ = 'dividend_info'
    __table_args__ = (
        UniqueConstraint('stock_id', 'year', 'reprt_code', name='uq_dividend_info'),
    )

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    code = Column(String(20), nullable=False)  # 주식 코드
    year = Column(Integer, nullable=False)
    reprt_code = Column(String(5), nullable=False)  # 보고서 코드 (예: 11011)
    dividend_per_share = Column(Numeric(20, 2))  # 주당 배당금
    ex_dividend_date = Column(Date)  # 배당락일
    stock = relationship("Stock", back_populates="dividend_info")

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_stock_price'),
    )

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    trade_date = Column(Date, nullable=False)
    close_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    stock = relationship("Stock")