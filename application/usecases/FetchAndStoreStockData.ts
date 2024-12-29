import { IDartApiClient } from '../interfaces/IDartApiClient';
import { IStockRepository } from '../interfaces/IStockRepository';

export class FetchAndStoreStockData {
  constructor(
    private dartApiClient: IDartApiClient,
    private stockRepository: IStockRepository
  ) {}

  public async execute(symbol: string): Promise<void> {
    const financialData = await this.dartApiClient.fetchFinancialData(symbol);
    await this.stockRepository.saveFinancialData(symbol, financialData);
    
    const dividends = await this.dartApiClient.fetchDividendHistory(
      symbol,
      '2020-01-01',
      '2023-12-31'
    );
    await this.stockRepository.saveDividendHistory(symbol, dividends);
  }
}