import React, { useState, useEffect } from "react";
import { BatchProcessing } from "../types";

interface ProgressIndicatorProps {
  estimatedTime: number;
  teamCount: number;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ 
  estimatedTime, 
  teamCount 
}) => {
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => {
        const newTime = prev + 0.1;
        setProgress(Math.min((newTime / estimatedTime) * 100, 99));
        return newTime;
      });
    }, 100);

    return () => clearInterval(timer);
  }, [estimatedTime]);

  return (
    <div className="flex flex-col items-center w-full max-w-lg mx-auto my-8 px-4">
      <div className="text-center mb-4 space-y-2">
        <h3 className="text-xl font-semibold text-blue-600">
          Generating Picklist for {teamCount} Teams
        </h3>
        <p className="text-gray-600">
          Estimated time: ~{Math.round(estimatedTime)} seconds
        </p>
        <p className="text-gray-600">
          Time elapsed: {elapsedTime.toFixed(1)} seconds
        </p>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
        <div
          className="bg-blue-600 h-4 rounded-full transition-all duration-100 ease-out"
          style={{ width: `${progress}%` }}
        ></div>
      </div>

      <p className="text-sm text-gray-500">
        {progress < 30
          ? "Starting..."
          : progress < 60
            ? "Processing team data..."
            : progress < 90
              ? "Generating rankings..."
              : "Finalizing picklist..."}
      </p>
    </div>
  );
};

interface BatchProgressIndicatorProps {
  batchInfo: BatchProcessing;
  elapsedTime: number;
}

export const BatchProgressIndicator: React.FC<BatchProgressIndicatorProps> = ({ 
  batchInfo, 
  elapsedTime 
}) => {
  return (
    <div className="flex flex-col items-center w-full max-w-lg mx-auto my-8 px-4">
      <div className="text-center mb-4 space-y-2">
        <h3 className="text-xl font-semibold text-blue-600">
          Generating Picklist in Batches
        </h3>
        <p className="text-gray-600">
          Processing teams in batches for higher quality rankings (updates every
          5 seconds)
        </p>
        <p className="text-gray-600">
          Time elapsed: {elapsedTime.toFixed(1)} seconds
        </p>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
        <div
          className="bg-blue-600 h-4 rounded-full transition-all duration-100 ease-out"
          style={{ width: `${batchInfo.progress_percentage}%` }}
        ></div>
      </div>

      <div className="flex justify-between w-full text-sm text-gray-600 mt-1 mb-3">
        <span>
          Processing batch {batchInfo.current_batch} of{" "}
          {batchInfo.total_batches}
        </span>
        <span>{batchInfo.progress_percentage}% complete</span>
      </div>

      <p className="text-sm text-gray-500">
        {batchInfo.progress_percentage === 0
          ? "Starting batch processing..."
          : batchInfo.progress_percentage < 30
            ? "Processing first batches..."
            : batchInfo.progress_percentage < 70
              ? "Ranking teams with reference teams..."
              : batchInfo.progress_percentage < 95
                ? "Processing final batches..."
                : "Combining results..."}
      </p>
    </div>
  );
};

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      <span className="ml-3 text-blue-600">Generating picklist...</span>
    </div>
  );
};