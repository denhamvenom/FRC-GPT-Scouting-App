import React, { useState, useEffect } from 'react';

interface ProgressData {
  status: 'initializing' | 'active' | 'completed' | 'failed' | 'stalled';
  message: string;
  progress: number;
  current_step: string;
  steps_completed: string[];
  estimated_time_remaining: number | null;
  duration: number;
}

interface ProgressTrackerProps {
  operationId: string;
  onComplete?: (success: boolean) => void;
  pollingInterval?: number; // in ms
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ 
  operationId, 
  onComplete,
  pollingInterval = 2000 // Default to 2 seconds
}) => {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState<boolean>(true);
  const [hasStarted, setHasStarted] = useState<boolean>(false);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchProgress = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/progress/${operationId}`);
        if (!response.ok) {
          if (response.status === 404 && !hasStarted) {
            // Operation not found yet, this is expected at the start
            return;
          }
          throw new Error('Failed to fetch progress');
        }
        
        const data = await response.json();
        setProgress(data);
        setHasStarted(true);
        
        // If operation is completed or failed, stop polling
        if (data.status === 'completed' || data.status === 'failed') {
          setPolling(false);
          if (onComplete) {
            onComplete(data.status === 'completed');
          }
        }
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('An unknown error occurred');
        }
        // Only stop polling if we've started and there's an error
        if (hasStarted) {
          setPolling(false);
        }
      }
    };

    // Fetch immediately on mount
    fetchProgress();
    
    // Set up polling interval if needed
    if (polling) {
      intervalId = setInterval(fetchProgress, pollingInterval);
    }

    // Cleanup function
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [operationId, polling, pollingInterval, onComplete, hasStarted]);

  if (error) {
    return (
      <div className="p-4 bg-red-100 border border-red-400 rounded">
        <p className="text-red-700">Error: {error}</p>
      </div>
    );
  }

  if (!progress) {
    return (
      <div className="p-4 bg-white border rounded shadow-sm mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-medium">Operation Progress</h3>
          <div className="flex items-center">
            <div className="h-3 w-3 rounded-full mr-2 bg-blue-500 animate-pulse"></div>
            <span className="capitalize">initializing</span>
          </div>
        </div>
        
        <div className="mb-4">
          <p className="text-gray-700">Starting picklist generation...</p>
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
          <div 
            className="h-2.5 rounded-full bg-blue-500 animate-pulse" 
            style={{ width: '5%' }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm text-gray-600">
          <div>0% complete</div>
        </div>
      </div>
    );
  }

  // Format time remaining
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds < 60) return `${Math.ceil(seconds)} seconds`;
    return `${Math.ceil(seconds / 60)} minutes`;
  };

  // Status indicator color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'stalled': return 'bg-yellow-500';
      case 'active': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="p-4 bg-white border rounded shadow-sm mb-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-medium">Operation Progress</h3>
        <div className="flex items-center">
          <div className={`h-3 w-3 rounded-full mr-2 ${getStatusColor(progress.status)}`}></div>
          <span className="capitalize">{progress.status}</span>
        </div>
      </div>
      
      <div className="mb-4">
        <p className="text-gray-700">{progress.message}</p>
        
        {progress.current_step && (
          <p className="text-sm text-gray-600 mt-1">
            Current step: {progress.current_step}
          </p>
        )}
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div 
          className={`h-2.5 rounded-full ${getStatusColor(progress.status)}`} 
          style={{ width: `${progress.progress}%` }}
        ></div>
      </div>
      
      <div className="flex justify-between text-sm text-gray-600">
        <div>{progress.progress.toFixed(0)}% complete</div>
        {progress.estimated_time_remaining !== null && progress.status === 'active' && (
          <div>~{formatTimeRemaining(progress.estimated_time_remaining)} remaining</div>
        )}
      </div>
      
      {/* Completed steps */}
      {progress.steps_completed && progress.steps_completed.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium mb-1">Completed Steps:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            {progress.steps_completed.map((step, index) => (
              <li key={index} className="flex items-center">
                <svg className="w-4 h-4 text-green-500 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {step}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Duration */}
      <div className="mt-2 text-xs text-gray-500">
        Duration: {progress.duration.toFixed(1)}s
      </div>
    </div>
  );
};

export default ProgressTracker;