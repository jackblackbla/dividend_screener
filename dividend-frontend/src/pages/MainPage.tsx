import React, { useState } from 'react';
import axios from 'axios';

interface Stock {
  stock_code: string;
  stock_name: string;
  dividend_per_share: number;
  dividend_count: number;
  consecutive_years: number;
  dividend_growth: number;
  meets_criteria: boolean;
}

const MainPage: React.FC = () => {
  const [minYield, setMinYield] = useState(3.0);
  const [limit, setLimit] = useState(10);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.get("http://localhost:8000/api/v1/screen", {
        params: { min_yield: minYield, min_count: limit }
      });
      setStocks(response.data.data);
    } catch (err) {
      setError('배당률 필터에 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">배당주 스크리너</h1>
      
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="mb-4">
          <label className="block mb-2">
            최소 배당률 (%):
            <input
              type="number"
              step="0.1"
              value={minYield}
              onChange={(e) => setMinYield(parseFloat(e.target.value))}
              className="ml-2 p-2 border rounded"
            />
          </label>
        </div>
        
        <div className="mb-4">
          <label className="block mb-2">
            표시할 종목 수:
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="ml-2 p-2 border rounded"
            />
          </label>
        </div>
        
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          {loading ? '검색 중...' : '스크리닝 실행'}
        </button>
      </form>

      {error && <div className="text-red-500 mb-4">{error}</div>}

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white">
          <thead>
            <tr>
              <th className="px-4 py-2">종목코드</th>
              <th className="px-4 py-2">종목명</th>
              <th className="px-4 py-2">주당 배당금</th>
              <th className="px-4 py-2">배당 횟수</th>
              <th className="px-4 py-2">연속 배당 연도</th>
              <th className="px-4 py-2">배당 성장률 (%)</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <tr
                key={stock.stock_code}
                className={stock.meets_criteria ? 'bg-yellow-100' : ''}
              >
                <td className="border px-4 py-2">{stock.stock_code}</td>
                <td className="border px-4 py-2">{stock.stock_name}</td>
                <td className="border px-4 py-2">{stock.dividend_per_share.toLocaleString()}</td>
                <td className="border px-4 py-2">{stock.dividend_count}</td>
                <td className="border px-4 py-2">{stock.consecutive_years}</td>
                <td className="border px-4 py-2">{stock.dividend_growth.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MainPage;