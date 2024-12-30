import React, { ChangeEvent } from 'react';

interface BasicFilterProps {
  filters: {
    min_yield: number;
    min_count: number;
    years: number;
  };
  onChange: (filters: {
    min_yield: number;
    min_count: number;
    years: number;
  }) => void;
}

const BasicFilter = ({ filters, onChange }: BasicFilterProps): JSX.Element => {
  const handleChange = (e: ChangeEvent<HTMLInputElement> | ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    onChange({
      ...filters,
      [name]: Number(value),
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-4">기본 필터</h3>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">최소 배당률 (%)</label>
          <select
            name="min_yield"
            value={filters.min_yield}
            onChange={handleChange}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          >
            <option value={3}>3%</option>
            <option value={4}>4%</option>
            <option value={5}>5%</option>
            <option value={6}>6%</option>
            <option value={7}>7%</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">최소 배당 횟수</label>
          <input
            type="number"
            name="min_count"
            value={filters.min_count}
            onChange={handleChange}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            min="0"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">고려 기간 (년)</label>
          <input
            type="number"
            name="years"
            value={filters.years}
            onChange={handleChange}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            min="1"
          />
        </div>
      </div>
    </div>
  );
};

export default BasicFilter;