interface ScreeningResult {
  stock_code: string;
  stock_name: string;
  dividend_per_share: number;
  dividend_yield: number;
  dividend_count: number;
  consecutive_years: number;
  long_term_growth: number;
  short_term_growth: number;
  meets_criteria: boolean;
  latest_close_price?: number;
}

interface ScreeningResponse {
  status: string;
  data: ScreeningResult[];
  message?: string;
  criteria: Record<string, any>;
  timestamp: string;
}

export async function fetchScreener(params: any): Promise<ScreeningResult[]> {
  // build querystring
  const qs = new URLSearchParams();
  if(params.minYield) qs.set('min_yield', params.minYield.toString());
  if(params.marketCap) {
    let marketCapValue = params.marketCap;
    if (typeof marketCapValue === 'string') {
      // '조' 단위 처리 (1조 = 1e12)
      if (marketCapValue.includes('조')) {
        marketCapValue = parseFloat(marketCapValue) * 1e12;
      }
      // '억' 단위 처리 (1억 = 1e8)
      else if (marketCapValue.includes('억')) {
        marketCapValue = parseFloat(marketCapValue) * 1e8;
      }
      // 일반 숫자 처리
      else {
        marketCapValue = parseFloat(marketCapValue);
      }
    }
    qs.set('market_cap', marketCapValue.toString());
  }
  if(params.consecutiveYears) qs.set('consecutive_years', params.consecutiveYears.toString());
  if(params.avoidDivCut) qs.set('avoid_div_cut', 'true');
  if(params.payoutMax) qs.set('payout_max', params.payoutMax.toString());
  if(params.sector) qs.set('sector', params.sector);

  try {
    const res = await fetch(`http://localhost:8000/api/v1/screen?${qs.toString()}`);
    if(!res.ok) {
      console.error('fetchScreener error', res.statusText);
      return [];
    }
    const response: ScreeningResponse = await res.json();
    
    // 응답이 예상한 형태가 아닌 경우 빈 배열 반환
    if (!response || !Array.isArray(response.data)) {
      console.error('Invalid response format', response);
      return [];
    }
    
    return response.data;
  } catch (error) {
    console.error('fetchScreener error:', error);
    return [];
  }
}

export async function fetchStockDetail(code: string): Promise<any> {
  const res = await fetch(`/api/stocks/${code}`);
  if(!res.ok) {
    console.error('fetchStockDetail error', res.statusText);
    return null;
  }
  return res.json();
}

export async function runDripSimulation(params: any): Promise<any> {
  const res = await fetch('/api/drip-sim', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params)
  });
  if(!res.ok) {
    console.error('runDripSimulation error', res.statusText);
    return null;
  }
  return res.json();
}