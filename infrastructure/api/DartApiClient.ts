import axios from 'axios';
import { IDartApiClient, FinancialData, DividendHistory } from '../../application/interfaces/IDartApiClient';

export class DartApiClient implements IDartApiClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;

  constructor() {
    this.baseUrl = 'https://opendart.fss.or.kr';
    this.apiKey = process.env.DART_API_KEY || '';
  }

  public async fetchFinancialData(symbol: string): Promise<FinancialData> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/financial`, {
        params: {
          crtfc_key: this.apiKey,
          corp_code: symbol,
        },
      });
      return this.parseFinancialData(response.data);
    } catch (error) {
      throw new Error(`Failed to fetch financial data: ${error}`);
    }
  }

  public async fetchDividendHistory(symbol: string, startDate: string, endDate: string): Promise<DividendHistory[]> {
    try {
      const response = await axios.get(`${this.baseUrl}/api/dividend`, {
        params: {
          crtfc_key: this.apiKey,
          corp_code: symbol,
          bgn_de: startDate,
          end_de: endDate,
        },
      });
      return this.parseDividendHistory(response.data);
    } catch (error) {
      throw new Error(`Failed to fetch dividend history: ${error}`);
    }
  }

  private parseFinancialData(data: any): FinancialData {
    return {
      revenue: data.revenue,
      netIncome: data.netIncome,
      fiscalYear: data.fiscalYear,
    };
  }

  private parseDividendHistory(data: any): DividendHistory[] {
    return data.map((item: any) => ({
      symbol: item.corp_code,
      dividendAmount: item.dividend,
      recordDate: item.record_date,
    }));
  }
}