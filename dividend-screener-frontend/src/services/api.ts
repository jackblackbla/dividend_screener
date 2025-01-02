export async function fetchScreener(params: any): Promise<any[]> {
  // build querystring
  const qs = new URLSearchParams();
  if(params.minYield) qs.set('min_yield', params.minYield.toString());
  if(params.marketCap) qs.set('market_cap', params.marketCap);
  if(params.consecutiveYears) qs.set('consecutive_years', params.consecutiveYears.toString());
  if(params.avoidDivCut) qs.set('avoid_div_cut', 'true');
  if(params.payoutMax) qs.set('payout_max', params.payoutMax.toString());
  if(params.sector) qs.set('sector', params.sector);

  const res = await fetch(`/api/screener?${qs.toString()}`);
  if(!res.ok) {
    console.error('fetchScreener error', res.statusText);
    return [];
  }
  return res.json();
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