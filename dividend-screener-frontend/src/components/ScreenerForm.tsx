import React, { useState } from 'react';

interface Props {
  onSearch: (vals: any) => void;
}

function ScreenerForm({ onSearch }: Props) {
  const [minYield, setMinYield] = useState<number>(3);
  const [marketCap, setMarketCap] = useState<string>('1조 이상');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 고급 필터
  const [consecutiveYears, setConsecutiveYears] = useState<number>(5);
  const [avoidDivCut, setAvoidDivCut] = useState<boolean>(false);
  const [payoutMax, setPayoutMax] = useState<number>(80);
  const [sector, setSector] = useState<string>('');
  const [minGrowthRate, setMinGrowthRate] = useState<number>(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      minYield,
      marketCap,
      consecutiveYears,
      avoidDivCut,
      payoutMax,
      sector,
      minGrowthRate
    });
  };

  return (
    <form onSubmit={handleSubmit} className="mb-3">

      {/* Basic Filter */}
      <div className="row mb-2">
        <div className="col-md-4">
          <label className="form-label">배당수익률(%) &gt;=</label>
          <input type="number"
                 className="form-control"
                 value={minYield}
                 onChange={(e) => setMinYield(Number(e.target.value))}
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">시총</label>
          <select className="form-select"
                  value={marketCap}
                  onChange={(e)=>setMarketCap(e.target.value)}>
            <option>1조 이상</option>
            <option>5천억 이상</option>
            <option>2조 이상</option>
          </select>
        </div>
      </div>

      {/* Toggle advanced */}
      <button type="button"
              className="btn btn-secondary mb-2"
              onClick={()=> setShowAdvanced(!showAdvanced)}>
        {showAdvanced ? '고급 필터 닫기' : '고급 필터 열기 ▼'}
      </button>

      {showAdvanced && (
        <div className="card card-body mb-3">
          {/* 연속배당연도 */}
          <div className="row mb-2">
            <div className="col-md-4">
              <label className="form-label">연속배당연도 &gt;=</label>
              <input type="number"
                     className="form-control"
                     value={consecutiveYears}
                     onChange={(e)=> setConsecutiveYears(Number(e.target.value))}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label">배당성향 max(%)</label>
              <input type="number"
                     className="form-control"
                     value={payoutMax}
                     onChange={(e)=> setPayoutMax(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="form-check form-check-inline mb-2">
            <input className="form-check-input square-checkbox"
                   type="checkbox"
                   checked={avoidDivCut}
                   onChange={(e)=> setAvoidDivCut(e.target.checked)}/>
            <label className="form-check-label">
              최근 배당컷 없는 종목만
            </label>
          </div>

          <div className="mb-2">
            <label className="form-label">업종</label>
            <select className="form-select"
                    value={sector}
                    onChange={(e)=>setSector(e.target.value)}>
              <option value="">--선택안함--</option>
              <option value="제지">제지</option>
              <option value="화학">화학</option>
              <option value="금융">금융</option>
              {/* etc */}
            </select>
          </div>

          {/* 배당성장률 필드 추가 */}
          <div className="mb-3">
            <label className="form-label">배당성장률(%) &gt;=</label>
            <input type="number"
                   className="form-control"
                   value={minGrowthRate}
                   onChange={(e) => setMinGrowthRate(Number(e.target.value))} />
            <small className="text-muted">
              최근 3년 연평균 배당성장률 기준
            </small>
          </div>
        </div>
      )}

      <div className="d-flex">
        <button type="submit" className="btn btn-primary">검색</button>
        <button type="reset" className="btn btn-outline-secondary ms-2"
          onClick={()=>{
            setMinYield(3); setMarketCap('1조 이상');
            setConsecutiveYears(5); setAvoidDivCut(false);
            setPayoutMax(80); setSector('');
          }}>
          초기화
        </button>
      </div>
    </form>
  );
}

export default ScreenerForm;