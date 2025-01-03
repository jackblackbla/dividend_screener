import React, { useState } from 'react';
import ScreenerForm from '../components/ScreenerForm';
import ScreenerResult from '../components/ScreenerResult';
import { fetchScreener } from '../services/api';

function ScreenerPage() {
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = async (formValues: any) => {
    try {
      const data = await fetchScreener(formValues);
      setResults(data);
    } catch (error) {
      console.error('검색 실패:', error);
      setResults([]);
    }
  };

  return (
    <div className="container mt-4">
      <h2 className="mb-3">[스크리너]</h2>
      <ScreenerForm onSearch={handleSearch} />
      <hr />
      <ScreenerResult rows={results} />
    </div>
  );
}

export default ScreenerPage;