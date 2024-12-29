import { FinancialData } from './IDartApiClient';
import { DividendHistory } from './IDartApiClient';

export interface IStockRepository {
  saveFinancialData(symbol: string, financialData: FinancialData): Promise<void>;
  saveDividendHistory(symbol: string, dividends: DividendHistory[]): Promise<void>;
}