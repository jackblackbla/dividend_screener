export interface Stock {
  stock_code: string;
  stock_name: string;
  dividend_yield: number;
  dividend_per_share: number;
  dividend_count: number;
  consecutive_years: number;
  dividend_growth: number;
}

interface ResultsTableProps {
  data: Stock[];
}

const ResultsTable = ({ data }: ResultsTableProps) => {
  if (data.length === 0) {
    return <div className="mt-4 text-gray-500">검색 결과가 없습니다.</div>;
  }

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              종목코드
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              종목명
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              배당률(%)
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              주당 배당금(원)
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              배당횟수
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              연속배당연수
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              배당 증가율(%)
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((stock) => (
            <tr key={stock.stock_code}>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.stock_code}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {stock.stock_name}
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
                {stock.dividend_growth?.toFixed(2) ?? '0.00'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;