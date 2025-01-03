from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey, UniqueConstraint, BigInteger
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'

    stock_id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    corp_code = Column(String(8), unique=True)  # DART 고유번호
    name = Column(String(100), nullable=False)
    sector = Column(String(50))  # 업종
    exchange = Column(String(10))  # 거래소 (KOSPI, KOSDAQ 등)
    financial_statements = relationship("FinancialStatement", back_populates="stock")
    dividend_info = relationship("DividendInfo", back_populates="stock")
    dividend_yields = relationship("DividendYield", back_populates="stock")
    issuance_reductions = relationship("StockIssuanceReduction", back_populates="stock")

class FinancialStatement(Base):
    __tablename__ = 'financial_statements'

    financial_statement_id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id'), nullable=False)
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

    dividend_yield_id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id'), nullable=False)
    date = Column(Date, nullable=False)  # 배당률 계산일
    yield_value = Column(Numeric(5, 2), nullable=False)  # 배당수익률
    stock = relationship("Stock", back_populates="dividend_yields")

class DividendInfo(Base):
    __tablename__ = 'dividend_info'
    __table_args__ = (
        UniqueConstraint('stock_id', 'year', name='uq_dividend_info'),
    )

    dividend_id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id'), nullable=False)
    year = Column(Integer, nullable=False)
    dividend_per_share = Column(Numeric(20, 2))  # 주당 배당금
    adjusted_dividend_per_share = Column(Numeric(20, 2))  # 조정된 주당 배당금
    adjusted_ratio = Column(Numeric(10, 4))  # 무상조정계수
    ex_dividend_date = Column(Date)  # 배당락일
    stock = relationship("Stock", back_populates="dividend_info")

    def apply_adjustment_factor(self, adjustment_factor: float):
        """
        무상조정계수를 적용하여 조정된 주당 배당금 계산
        
        Args:
            adjustment_factor: 무상조정계수
        """
        if adjustment_factor <= 0:
            raise ValueError("Adjustment factor must be greater than 0")
            
        self.adjusted_dividend_per_share = self.dividend_per_share / adjustment_factor

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_stock_price'),
    )

    stock_price_id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id'), nullable=False)
    trade_date = Column(Date, nullable=False)
    close_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    stock = relationship("Stock")

class StockIssuanceReduction(Base):
    __tablename__ = 'stock_issuance_reduction'
    __table_args__ = (
        UniqueConstraint('corp_code', 'isu_dcrs_de', 'isu_dcrs_stle', name='uq_stock_issuance_reduction'),
    )

    stock_issuance_reduction_id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.stock_id'), nullable=False)
    corp_code = Column(String(8), nullable=False)
    rcept_no = Column(String(14))  # 접수번호
    isu_dcrs_de = Column(Date)  # 발행 감소 일자
    isu_dcrs_stle = Column(String(100))  # 발행 감소 형태
    isu_dcrs_stock_knd = Column(String(50))  # 주식 종류
    isu_dcrs_qy = Column(BigInteger)  # 발행 감소 수량
    isu_dcrs_mstvdv_fval_amount = Column(Numeric(20, 2))  # 주당 액면 가액
    isu_dcrs_mstvdv_amount = Column(Numeric(20, 2))  # 발행 감소 주당 가액
    stlm_dt = Column(Date)  # 결산기준일
    adjusted_ratio = Column(Numeric(10, 4))  # 무상조정계수
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    stock = relationship("Stock", back_populates="issuance_reductions")