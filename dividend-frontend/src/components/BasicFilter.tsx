import React, { ChangeEvent } from 'react';

interface BasicFilters {
  min_yield: number;
  min_count: number;
  years: number;
}

export interface AdvancedFilters {
  yield_ranges: string[];
  consecutive_years: number;
}

interface BasicFilterProps {
  basicFilters: BasicFilters;
  advancedFilters: AdvancedFilters;
  onBasicChange: (filters: BasicFilters) => void;
  onAdvancedChange: (filters: AdvancedFilters) => void;
  onSearch: () => void;
}

const BasicFilter = ({ 
  basicFilters, 
  advancedFilters,
  onBasicChange,
  onAdvancedChange,
  onSearch
}: BasicFilterProps): JSX.Element => {
  const handleBasicChange = (e: ChangeEvent<HTMLInputElement> | ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    onBasicChange({
      ...basicFilters,
      [name]: Number(value),
    });
  };

  const handleCheckboxChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { value, checked } = e.target;
    let newRanges = [...advancedFilters.yield_ranges];
    
    if (checked) {
      newRanges.push(value);
    } else {
      newRanges = newRanges.filter(range => range !== value);
    }

    onAdvancedChange({
      ...advancedFilters,
      yield_ranges: newRanges,
    });
  };

  const handleConsecutiveYearsChange = (e: ChangeEvent<HTMLInputElement>) => {
    onAdvancedChange({
      ...advancedFilters,
      consecutive_years: Number(e.target.value),
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-[1600px] mx-auto">
      <h3 className="text-lg font-semibold mb-4">필터 설정</h3>
      <div className="space-y-6">
        <div className="flex items-end gap-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">최소 배당률 (%)</label>
            <select
              name="min_yield"
              value={basicFilters.min_yield}
              onChange={handleBasicChange}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            >
              <option value={3}>3%</option>
              <option value={4}>4%</option>
              <option value={5}>5%</option>
              <option value={6}>6%</option>
              <option value={7}>7%</option>
            </select>
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">최소 배당 횟수</label>
            <input
              type="number"
              name="min_count"
              value={basicFilters.min_count}
              onChange={handleBasicChange}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              min="0"
            />
          </div>
          
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">고려 기간 (년)</label>
            <input
              type="number"
              name="years"
              value={basicFilters.years}
              onChange={handleBasicChange}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              min="1"
            />
          </div>

          <button
            type="button"
            className="h-[42px] ml-4 px-6 bg-blue-500 text-white font-medium rounded-md hover:bg-blue-600 transition-colors"
            onClick={onSearch}
          >
            검색
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">배당률 구간</label>
          <div className="space-y-3">
            {['10% 이상', '8% 이상', '5% 이상'].map((range) => (
              <label key={range} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  value={range}
                  checked={advancedFilters.yield_ranges.includes(range)}
                  onChange={handleCheckboxChange}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-gray-700">{range}</span>
              </label>
            ))}
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">최소 연속배당 연수</label>
          <input
            type="number"
            value={advancedFilters.consecutive_years}
            onChange={handleConsecutiveYearsChange}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            min="0"
          />
        </div>
      </div>
    </div>
  );
};

export default BasicFilter;