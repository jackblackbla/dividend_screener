import axios from 'axios';
import axiosMockAdapter from 'axios-mock-adapter';
const MockAdapter = axiosMockAdapter;
import { DartApiClient } from '../../infrastructure/api/DartApiClient';

describe('DartApiClient', () => {
  let mockAxios: axiosMockAdapter;
  let dartApiClient: DartApiClient;

  beforeEach(() => {
    mockAxios = new MockAdapter(axios);
    dartApiClient = new DartApiClient();
  });

  afterEach(() => {
    mockAxios.restore();
  });

  it('fetchFinancialData should return financial data', async () => {
    const mockData = {
      revenue: 1000000,
      netIncome: 500000,
      fiscalYear: '2023',
    };

    mockAxios.onGet('https://opendart.fss.or.kr/api/financial').reply(200, mockData);

    const result = await dartApiClient.fetchFinancialData('1234567890');
    
    expect(result).toEqual({
      revenue: 1000000,
      netIncome: 500000,
      fiscalYear: '2023',
    });
  });

  it('fetchDividendHistory should return dividend history', async () => {
    const mockData = [
      {
        corp_code: '1234567890',
        dividend: 100,
        record_date: '2023-01-01',
      },
    ];

    mockAxios.onGet('https://opendart.fss.or.kr/api/dividend').reply(200, mockData);

    const result = await dartApiClient.fetchDividendHistory(
      '1234567890',
      '2020-01-01',
      '2023-12-31'
    );

    expect(result).toEqual([
      {
        symbol: '1234567890',
        dividendAmount: 100,
        recordDate: '2023-01-01',
      },
    ]);
  });

  it('should throw error when API call fails', async () => {
    mockAxios.onGet('https://opendart.fss.or.kr/api/financial').reply(500);

    await expect(dartApiClient.fetchFinancialData('1234567890')).rejects.toThrow(
      'Failed to fetch financial data: Error: Request failed with status code 500'
    );
  });
});