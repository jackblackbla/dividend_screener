import React from 'react';
import { useNavigate } from 'react-router-dom';

interface Row {
  stock_code: string;
  stock_name: string;
  dividend_yield: number;
  consecutive_years: number;
  dividend_per_share: number;
  dividend_count: number;
  long_term_growth: number;
  short_term_growth: number;
  meets_criteria: boolean;
  latest_close_price?: number;
}

interface Props {
  rows: Row[];
}

function ScreenerResult({ rows }: Props) {
  const navigate = useNavigate();

  if(!rows || rows.length===0) {
    return <div>검색 결과가 없습니다.</div>;
  }

  const handleDetail = (code: string) => {
    navigate(`/detail/${code}`);
  };
  const handleDrip = (code: string) => {
    navigate(`/drip?stock_id=${code}`);
  };

  return (
    <table className="table table-striped table-hover">
      <thead>
        <tr>
          <th>종목명</th>
          <th>배당수익률</th>
          <th>연속배당</th>
          <th>배당금</th>
          <th>배당횟수</th>
          <th>최근종가</th>
          <th>장기배당성장률(5년)</th>
          <th>단기배당성장률(3년)</th>
          <th>액션</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, idx)=>(
          <tr key={idx}>
            <td>{r.stock_name}</td>
            <td>{r.dividend_yield.toFixed(2)}%</td>
            <td>{r.consecutive_years}년</td>
            <td>{r.dividend_per_share.toLocaleString()}원</td>
            <td>{r.dividend_count}회</td>
            <td>{r.latest_close_price?.toLocaleString()}원</td>
            <td>{r.long_term_growth.toFixed(1)}%</td>
            <td>{r.short_term_growth.toFixed(1)}%</td>
            <td>
              <button className="btn btn-sm btn-outline-primary me-2"
                      onClick={()=>handleDetail(r.stock_code)}>상세</button>
              <button className="btn btn-sm btn-outline-success"
                      onClick={()=>handleDrip(r.stock_code)}>DRIP</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default ScreenerResult;