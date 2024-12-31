import { useState } from 'react';
import { Stock } from '../components/ResultsTable';
import axios from 'axios';
import BasicFilter from '../components/BasicFilter';
import ResultsTable from '../components/ResultsTable.tsx';

interface BasicFilters {
  min_yield: number;
  min_count: number;
  years: number;
}

interface AdvancedFilters {
  yield_ranges: string[];
  consecutive_years: number;
}

const DividendScreenerPage = () => {
  const [basicFilters, setBasicFilters] = useState<BasicFilters>({
    min_yield: 3.0,
    min_count: 1,
    years: 5,
  });

  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>({
    yield_ranges: [],
    consecutive_years: 0,
  });

  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [results, setResults] = useState<Stock[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const combineParams = () => {
    const params = {
      min_yield: basicFilters.min_yield,
      min_count: basicFilters.min_count,
      years: basicFilters.years,
      yield_ranges: advancedFilters.yield_ranges,
      consecutive_years: advancedFilters.consecutive_years,
      min_dividend: 100.0,
      limit: 5
    };
    return params;
  };

  const fetchAPI = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = combineParams();
      const response = await axios.get('http://localhost:8000/api/v1/screen', { params });
      console.log('API Response:', response.data.data);
      
      if (response.data?.data && Array.isArray(response.data.data)) {
        const filteredResults = response.data.data.filter((item: any) => item.meets_criteria);
        setResults(filteredResults);
      } else {
        setError('유효하지 않은 응답 데이터입니다.');
        setResults([]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-[1600px] mx-auto">
      <h1 className="text-2xl font-bold mb-4">배당주 스크리너 (통합버전)</h1>
      
      <BasicFilter
        basicFilters={basicFilters}
        advancedFilters={advancedFilters}
        onBasicChange={setBasicFilters}
        onAdvancedChange={setAdvancedFilters}
        onSearch={fetchAPI}
      />
      
      {isLoading ? (
        <div className="mt-4 text-center">로딩 중...</div>
      ) : error ? (
        <div className="mt-4 text-red-500 text-center">{error}</div>
      ) : (
        <ResultsTable data={results} />
      )}
    </div>
  );
};

export default DividendScreenerPage;