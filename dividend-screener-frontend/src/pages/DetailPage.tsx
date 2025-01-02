import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

function DetailPage() {
  const { code } = useParams();
  const [stockInfo, setStockInfo] = useState<any>(null);

  useEffect(()=>{
    // TODO: fetch /api/stocks/:code -> get basic info, sector, market_cap
    // setStockInfo(...)
  }, [code]);

  return (
    <div className="container mt-4">
      <h2>종목 상세 페이지</h2>
      {stockInfo ? (
        <div>
          <div className="mb-3">
            <h4>{stockInfo.name} ({stockInfo.code})</h4>
            <p>업종: {stockInfo.sector}</p>
            <p>시가총액: {stockInfo.market_cap}원</p>
            <p>최근 주가: ???</p>
          </div>

          {/* (B) 배당 이력 그래프(조정DPS) => Chart.js or Recharts */}
          <div className="card mb-3">
            <div className="card-header">배당 이력 그래프</div>
            <div className="card-body">
              {/* <MyChartComponent data={stockInfo.dividendHistory} /> */}
              <p>(line chart placeholder)</p>
            </div>
          </div>

          {/* (C) 이벤트 타임라인 */}
          <div className="card mb-3">
            <div className="card-header">이벤트 타임라인</div>
            <div className="card-body">
              {/* stockInfo.events? */}
              {stockInfo.events?.map((ev: any, idx: number)=>(
                <p key={idx}>
                  {ev.event_date} : {ev.event_type} {ev.description}
                </p>
              ))}
            </div>
          </div>

          <button className="btn btn-outline-primary">
            DRIP 시뮬로 이동
          </button>
        </div>
      ) : (
        <p>로딩중...</p>
      )}
    </div>
  );
}

export default DetailPage;