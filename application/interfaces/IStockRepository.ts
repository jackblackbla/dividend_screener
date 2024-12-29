import { FinancialDataEntity } from '../../infrastructure/db/entities/FinancialDataEntity';
import { DividendEntity } from '../../infrastructure/db/entities/DividendEntity';
import { StockEntity } from '../../infrastructure/db/entities/StockEntity';

export interface IStockRepository {
  saveFinancialData(symbol: string, financialData: FinancialDataEntity): Promise<void>;
  saveDividendHistory(symbol: string, dividends: DividendEntity[]): Promise<void>;
  findStockByTicker(ticker: string): Promise<StockEntity | null>;
  createOrUpdateStock(stock: StockEntity): Promise<void>;
}