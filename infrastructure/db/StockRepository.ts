import { IStockRepository } from '../application/interfaces/IStockRepository';
import { AppDataSource } from '../config/database.config';
import { StockEntity } from './entities/StockEntity';
import { FinancialDataEntity } from './entities/FinancialDataEntity';
import { DividendEntity } from './entities/DividendEntity';

export class StockRepository implements IStockRepository {
  private stockRepository = AppDataSource.getRepository(StockEntity);
  private financialDataRepository = AppDataSource.getRepository(FinancialDataEntity);
  private dividendRepository = AppDataSource.getRepository(DividendEntity);

  public async saveFinancialData(symbol: string, financialData: FinancialDataEntity): Promise<void> {
    let stock = await this.stockRepository.findOneBy({ ticker: symbol });

    if (!stock) {
      stock = new StockEntity();
      stock.ticker = symbol;
      stock = await this.stockRepository.save(stock);
    }

    financialData.stock = stock;
    await this.financialDataRepository.save(financialData);
  }

  public async saveDividendHistory(symbol: string, dividends: DividendEntity[]): Promise<void> {
    let stock = await this.stockRepository.findOneBy({ ticker: symbol });

    if (!stock) {
      stock = new StockEntity();
      stock.ticker = symbol;
      stock = await this.stockRepository.save(stock);
    }

    for (const dividend of dividends) {
      dividend.stock = stock;
      await this.dividendRepository.save(dividend);
    }
  }

  public async findStockByTicker(ticker: string): Promise<StockEntity | null> {
    return this.stockRepository.findOneBy({ ticker });
  }

  public async createOrUpdateStock(stock: StockEntity): Promise<void> {
    await this.stockRepository.save(stock);
  }
}