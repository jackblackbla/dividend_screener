export interface FinancialData {
  revenue: number;
  netIncome: number;
  fiscalYear: string;
}

export interface DividendHistory {
  symbol: string;
  dividendAmount: number;
  recordDate: string;
}

export interface IDartApiClient {
  /**
   * 주어진 주식 심볼이나 회사 코드에 대한 기본 재무 또는 공시 데이터를 가져옵니다.
   * @param symbol 주식 심볼 또는 DART 회사 코드
   */
  fetchFinancialData(symbol: string): Promise<FinancialData>;
  
  /**
   * 주어진 심볼이나 기간에 대한 배당금 내역을 가져옵니다.
   */
  fetchDividendHistory(symbol: string, startDate: string, endDate: string): Promise<DividendHistory[]>;
}