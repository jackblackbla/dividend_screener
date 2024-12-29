import { IDartApiClient } from '../interfaces/IDartApiClient';
import { IStockRepository } from '../interfaces/IStockRepository';
import { FinancialDataEntity } from '../../infrastructure/db/entities/FinancialDataEntity';
import { DividendEntity } from '../../infrastructure/db/entities/DividendEntity';

export class FetchAndStoreStockData {
  constructor(
    private dartApiClient: IDartApiClient,
    private stockRepository: IStockRepository
  ) {}

  private mapToFinancialDataEntity(data: any): FinancialDataEntity {
    const entity = new FinancialDataEntity();
    entity.fiscalYear = data.year;
    entity.revenue = data.revenue;
    entity.netIncome = data.netIncome;
    return entity;
  }

  private mapToDividendEntity(data: any): DividendEntity {
    const entity = new DividendEntity();
    entity.exDate = new Date(data.exDate);
    entity.payDate = new Date(data.payDate);
    entity.amount = data.amount;
    return entity;
  }

  public async execute(symbol: string): Promise<void> {
    const financialData = await this.dartApiClient.fetchFinancialData(symbol);
    const financialDataEntity = this.mapToFinancialDataEntity(financialData);
    await this.stockRepository.saveFinancialData(symbol, financialDataEntity);

    const dividends = await this.dartApiClient.fetchDividendHistory(
      symbol,
      '2020-01-01',
      '2023-12-31'
    );
    const dividendEntities = dividends.map(this.mapToDividendEntity);
    await this.stockRepository.saveDividendHistory(symbol, dividendEntities);
  }
}