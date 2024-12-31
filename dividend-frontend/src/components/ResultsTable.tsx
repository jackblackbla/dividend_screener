import React, { useState } from 'react';

export interface Stock {
  [key: string]: any;
  stock_code: string;
  stock_name: string;
  dividend_yield: number;
  dividend_per_share: number;
  dividend_count: number;
  consecutive_years: number;
  long_term_growth: number;
  short_term_growth: number;
  latest_close_price: number;
}

interface ResultsTableProps {
  data: Stock[];
}

const ResultsTable = ({ data }: ResultsTableProps) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  const sortedData = React.useMemo(() => {
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortConfig]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIndicator = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) return null;
    return sortConfig.direction === 'asc' ? ' ▲' : ' ▼';
  };

  if (sortedData.length === 0) {
    return <div className="mt-4 text-gray-500">검색 결과가 없습니다.</div>;
  }

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('stock_code')}
            >
              종목코드{getSortIndicator('stock_code')}
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('stock_name')}
            >
              종목명{getSortIndicator('stock_name')}
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('latest_close_price')}
            >
              현재가(전일종가){getSortIndicator('latest_close_price')}
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('dividend_yield')}
            >
              배당률(%){getSortIndicator('dividend_yield')}
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('dividend_per_share')}
            >
              2023년 주당 배당금(원){getSortIndicator('dividend_per_share')}
            </th>
            <th 
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('dividend_count')}
            >
              배당횟수{getSortIndicator('dividend_count')}
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('consecutive_years')}
            >
              연속배당연수{getSortIndicator('consecutive_years')}
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('long_term_growth')}
            >
              장기 배당 증가율(%){getSortIndicator('long_term_growth')}
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('short_term_growth')}
            >
              단기 배당 증가율(%){getSortIndicator('short_term_growth')}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((stock) => (
            <tr key={stock.stock_code}>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.stock_code}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.stock_name}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.latest_close_price?.toLocaleString() ?? '0'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.dividend_yield?.toFixed(2) ?? '0.00'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.dividend_per_share?.toLocaleString() ?? '0'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.dividend_count}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.consecutive_years}년
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.long_term_growth?.toFixed(2) ?? '0.00'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.short_term_growth?.toFixed(2) ?? '0.00'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;
