// frontend/src/components/CategoryTabs.tsx

import React from 'react';

export interface Category {
  id: string;
  label: string;
  description: string;
  icon?: string;
}

interface CategoryTabsProps {
  categories: Category[];
  activeCategory: string;
  onCategoryChange: (categoryId: string) => void;
  countsPerCategory?: Record<string, number>;
  totalCount?: number;
}

const CategoryTabs: React.FC<CategoryTabsProps> = ({
  categories,
  activeCategory,
  onCategoryChange,
  countsPerCategory,
  totalCount
}) => {
  return (
    <div className="mb-6">
      {/* Category navigation */}
      <div className="flex flex-wrap border-b border-gray-200">
        {categories.map((category) => {
          const isActive = activeCategory === category.id;
          const count = countsPerCategory?.[category.id] || 0;
          
          return (
            <button
              key={category.id}
              onClick={() => onCategoryChange(category.id)}
              className={`py-3 px-4 text-sm font-medium flex items-center gap-2 ${
                isActive
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
              }`}
            >
              {category.icon && <span>{category.icon}</span>}
              <span>{category.label}</span>
              {countsPerCategory && (
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  count > 0 
                    ? isActive
                      ? 'bg-blue-200 text-blue-800' 
                      : 'bg-gray-200 text-gray-700'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      
      {/* Progress bar */}
      {totalCount !== undefined && countsPerCategory && (
        <div className="mt-2">
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
            <div 
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ 
                width: `${totalCount > 0 ? (Object.values(countsPerCategory).reduce((a, b) => a + b, 0) / totalCount) * 100 : 0}%` 
              }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>0%</span>
            <span>
              {totalCount > 0 
                ? `${Math.round((Object.values(countsPerCategory).reduce((a, b) => a + b, 0) / totalCount) * 100)}%`
                : '0%'
              } Complete
            </span>
            <span>100%</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryTabs;