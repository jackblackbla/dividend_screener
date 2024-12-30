import { ChangeEvent } from 'react';

export interface AdvancedFilters {
  yield_ranges: string[];
  consecutive_years: number;
}

interface AdvancedFilterProps {
  filters: AdvancedFilters;
  onChange: (filters: AdvancedFilters) => void;
}

const AdvancedFilter = ({ filters, onChange }: AdvancedFilterProps) => {
  const handleCheckboxChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { value, checked } = e.target;
    let newRanges = [...filters.yield_ranges];
    
    if (checked) {
      newRanges.push(value);
    } else {
      newRanges = newRanges.filter(range => range !== value);
    }

    onChange({
      ...filters,
      yield_ranges: newRanges,
    });
  };

  const handleConsecutiveYearsChange = (e: ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...filters,
      consecutive_years: Number(e.target.value),
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6">
      <h3 className="text-lg font-semibold mb-4">고급 필터</h3>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">배당률 구간</label>
          <div className="space-y-3">
            {['10% 이상', '8% 이상', '5% 이상'].map((range) => (
              <label key={range} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  value={range}
                  checked={filters.yield_ranges.includes(range)}
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
            value={filters.consecutive_years}
            onChange={handleConsecutiveYearsChange}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            min="0"
          />
        </div>
      </div>
    </div>
  );
};

export default AdvancedFilter;