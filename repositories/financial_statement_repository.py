from sqlalchemy.orm import Session
from schema import FinancialStatement, Stock

class FinancialStatementRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_financial_statements(self, stock_code: str, financials: list):
        stock = self.session.query(Stock).filter_by(code=stock_code).first()
        if not stock:
            raise ValueError(f"Stock with code {stock_code} not found")

        for data in financials:
            fs = FinancialStatement(
                stock_id=stock.id,
                year=data['year'],
                quarter=data['quarter'],
                sales=data.get('sales'),
                operating_profit=data.get('operating_profit'),
                net_income=data.get('net_income'),
                assets=data.get('assets'),
                liabilities=data.get('liabilities'),
                equity=data.get('equity')
            )
            self.session.add(fs)
        self.session.commit()