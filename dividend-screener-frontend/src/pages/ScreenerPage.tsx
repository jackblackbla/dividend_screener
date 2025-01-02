import React, { useState } from 'react';
import ScreenerForm from '../components/ScreenerForm';
import ScreenerResult from '../components/ScreenerResult';

function ScreenerPage() {
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = (formValues: any) => {
    // TODO: call /api/screener with formValues
    // setResults(responseData);
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