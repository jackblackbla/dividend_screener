import { useState } from 'react';
import { Stock } from '../components/ResultsTable';
import axios from 'axios';
import BasicFilter from '../components/BasicFilter';
import AdvancedFilter from '../components/AdvancedFilter.tsx';
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
      min_dividend: 100.0, // 기본값 설정
      limit: 5 // 기본값 설정
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
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">배당주 스크리너 (통합버전)</h1>
      
      <BasicFilter 
        filters={basicFilters}
        onChange={setBasicFilters}
      />
      
      <button
        className="mt-4 text-blue-500 hover:underline"
        onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
      >
        {isAdvancedOpen ? '고급필터 숨기기' : '고급필터 펼치기'}
      </button>
      
      {isAdvancedOpen && (
        <AdvancedFilter
          filters={advancedFilters}
          onChange={setAdvancedFilters}
        />
      )}
      
      <button
        className="mt-4 bg-blue-500 text-white px-4 py-2 rounded"
        onClick={fetchAPI}
      >
        검색
      </button>
      
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