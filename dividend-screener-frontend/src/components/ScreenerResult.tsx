import React from 'react';
import { useNavigate } from 'react-router-dom';

interface Row {
  code: string;
  name: string;
  yield: number;
  consecutive_years: number;
  has_div_cut: boolean;
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
          <th>배당컷여부</th>
          <th>액션</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, idx)=>(
          <tr key={idx}>
            <td>{r.name}</td>
            <td>{r.yield}%</td>
            <td>{r.consecutive_years}년</td>
            <td>{r.has_div_cut ? '있음' : '없음'}</td>
            <td>
              <button className="btn btn-sm btn-outline-primary me-2"
                      onClick={()=>handleDetail(r.code)}>상세</button>
              <button className="btn btn-sm btn-outline-success"
                      onClick={()=>handleDrip(r.code)}>DRIP</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default ScreenerResult;