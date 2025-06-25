import { useState, useEffect } from "react";
import { BatchProcessing, PicklistResult } from "../types";

interface BatchProcessingState {
  batchProcessingActive: boolean;
  batchProcessingInfo: BatchProcessing | null;
  pollingCacheKey: string | null;
  elapsedTime: number;
  setBatchProcessingActive: (active: boolean) => void;
  setBatchProcessingInfo: (info: BatchProcessing | null) => void;
  setPollingCacheKey: (key: string | null) => void;
  setElapsedTime: (time: number) => void;
}

export function useBatchProcessing(): BatchProcessingState {
  const [batchProcessingActive, setBatchProcessingActive] = useState<boolean>(false);
  const [batchProcessingInfo, setBatchProcessingInfo] = useState<BatchProcessing | null>(null);
  const [pollingCacheKey, setPollingCacheKey] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    if (batchProcessingActive) {
      timer = setInterval(() => {
        setElapsedTime((prev) => prev + 0.1);
      }, 100);
    } else {
      setElapsedTime(0);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [batchProcessingActive]);

  return {
    batchProcessingActive,
    batchProcessingInfo,
    pollingCacheKey,
    elapsedTime,
    setBatchProcessingActive,
    setBatchProcessingInfo,
    setPollingCacheKey,
    setElapsedTime,
  };
}