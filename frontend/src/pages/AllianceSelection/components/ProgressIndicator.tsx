/**
 * Progress Indicator Component - Shows loading, error, and success states
 */

import React from 'react';
import { ProgressIndicatorProps } from '../types';

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  loading,
  error,
  successMessage
}) => {
  return (
    <>
      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded mb-6">
          {error}
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}
    </>
  );
};

export default ProgressIndicator;