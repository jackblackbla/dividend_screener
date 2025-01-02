import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

function DripPage() {
  const [searchParams] = useSearchParams();
  const preSelectedStock = searchParams.get('stock_id') || '';
  
  const [stockId, setStockId] = useState<string>(preSelectedStock);
  const [initialCapital, setInitialCapital] = useState<number>(10000000);
  const [years, setYears] = useState<number>(5);
  const [dripRate, setDripRate] = useState<number>(1.0);

  const [result, setResult] = useState<any>(null);

  const handleSimulate = () => {
    // call /api/drip-sim or similar
    // setResult(...)
  };

  return (
    <div className="container mt-4">
      <h2>DRIP 시뮬레이션</h2>
      <div className="row mb-3">
        <div className="col-md-4">
          <label className="form-label">종목코드</label>
          <input className="form-control"
                 value={stockId}
                 onChange={(e)=>setStockId(e.target.value)} />
        </div>
        <div className="col-md-4">
          <label className="form-label">초기자금(원)</label>
          <input className="form-control"
                 type="number"
                 value={initialCapital}
                 onChange={(e)=>setInitialCapital(Number(e.target.value))} />
        </div>
        <div className="col-md-4">
          <label className="form-label">기간(년)</label>
          <input className="form-control"
                 type="number"
                 value={years}
                 onChange={(e)=>setYears(Number(e.target.value))} />
        </div>
      </div>
      <div className="row mb-3">
        <div className="col-md-4">
          <label className="form-label">재투자비율(0~1)</label>
          <input className="form-control"
                 type="number"
                 step="0.1"
                 min="0"
                 max="1"
                 value={dripRate}
                 onChange={(e)=>setDripRate(Number(e.target.value))} />
        </div>
      </div>

      <button className="btn btn-primary" onClick={handleSimulate}>
        시뮬레이션 실행
      </button>

      {/* 결과 */}
      {result && (
        <div className="mt-4">
          <h5>결과</h5>
          {/* table or chart */}
          <table className="table">
            <thead>
              <tr><th>연도</th><th>배당금</th><th>매수주식</th><th>보유주식수</th><th>자산가치</th></tr>
            </thead>
            <tbody>
              {result.yearlyData.map((row: any, idx: number)=>(
                <tr key={idx}>
                  <td>{row.year}</td>
                  <td>{row.dividend}</td>
                  <td>{row.sharesBought}</td>
                  <td>{row.totalShares}</td>
                  <td>{row.assetValue}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default DripPage;