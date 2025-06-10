import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Hook for debouncing a value
 * 
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds
 * @returns The debounced value
 * 
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('')
 * const debouncedSearchTerm = useDebounce(searchTerm, 300)
 * 
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     performSearch(debouncedSearchTerm)
 *   }
 * }, [debouncedSearchTerm])
 * 
 * return (
 *   <input
 *     value={searchTerm}
 *     onChange={(e) => setSearchTerm(e.target.value)}
 *     placeholder="Search..."
 *   />
 * )
 * ```
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Hook for debouncing a callback function
 * 
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds
 * @param deps - Dependencies array (like useCallback)
 * @returns The debounced function
 * 
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('')
 * 
 * const debouncedSearch = useDebouncedCallback(
 *   (term: string) => {
 *     console.log('Searching for:', term)
 *     // Perform search
 *   },
 *   300,
 *   []
 * )
 * 
 * const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
 *   const value = e.target.value
 *   setSearchTerm(value)
 *   debouncedSearch(value)
 * }
 * 
 * return (
 *   <input
 *     value={searchTerm}
 *     onChange={handleInputChange}
 *     placeholder="Search..."
 *   />
 * )
 * ```
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList
): T {
  const timeoutRef = useRef<NodeJS.Timeout>()

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args)
      }, delay)
    },
    [callback, delay, ...deps]
  ) as T

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

/**
 * Hook for debouncing with additional control methods
 * 
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds
 * @param options - Additional options
 * @returns Object with debounced function and control methods
 * 
 * @example
 * ```tsx
 * const { 
 *   debouncedCallback, 
 *   cancel, 
 *   flush, 
 *   isPending 
 * } = useAdvancedDebounce(
 *   (searchTerm: string) => {
 *     performSearch(searchTerm)
 *   },
 *   300,
 *   {
 *     leading: false,
 *     trailing: true,
 *     maxWait: 1000
 *   }
 * )
 * 
 * const handleSearch = (term: string) => {
 *   debouncedCallback(term)
 * }
 * 
 * const handleCancel = () => {
 *   cancel() // Cancel pending execution
 * }
 * 
 * const handleFlush = () => {
 *   flush() // Execute immediately
 * }
 * ```
 */
export function useAdvancedDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  options: {
    /** Execute on the leading edge instead of trailing */
    leading?: boolean
    /** Execute on the trailing edge */
    trailing?: boolean
    /** Maximum time callback can be delayed */
    maxWait?: number
  } = {}
) {
  const { leading = false, trailing = true, maxWait } = options
  
  const timeoutRef = useRef<NodeJS.Timeout>()
  const maxTimeoutRef = useRef<NodeJS.Timeout>()
  const lastCallTimeRef = useRef<number>()
  const lastInvokeTimeRef = useRef<number>(0)
  const argsRef = useRef<Parameters<T>>()
  const [isPending, setIsPending] = useState(false)

  const invokeCallback = useCallback(() => {
    const args = argsRef.current
    if (args) {
      lastInvokeTimeRef.current = Date.now()
      setIsPending(false)
      callback(...args)
    }
  }, [callback])

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = undefined
    }
    if (maxTimeoutRef.current) {
      clearTimeout(maxTimeoutRef.current)
      maxTimeoutRef.current = undefined
    }
    setIsPending(false)
    lastCallTimeRef.current = undefined
  }, [])

  const flush = useCallback(() => {
    if (timeoutRef.current) {
      cancel()
      invokeCallback()
    }
  }, [cancel, invokeCallback])

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now()
      const isInvoking = leading && !timeoutRef.current
      
      argsRef.current = args
      lastCallTimeRef.current = now
      setIsPending(true)

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      if (isInvoking) {
        invokeCallback()
        if (!trailing) {
          setIsPending(false)
          return
        }
      }

      // Set up max wait timeout
      if (maxWait && !maxTimeoutRef.current) {
        maxTimeoutRef.current = setTimeout(() => {
          cancel()
          invokeCallback()
        }, maxWait)
      }

      // Set up trailing timeout
      timeoutRef.current = setTimeout(() => {
        if (maxTimeoutRef.current) {
          clearTimeout(maxTimeoutRef.current)
          maxTimeoutRef.current = undefined
        }
        
        if (trailing && lastCallTimeRef.current) {
          invokeCallback()
        } else {
          setIsPending(false)
        }
        
        timeoutRef.current = undefined
      }, delay)
    },
    [callback, delay, leading, trailing, maxWait, invokeCallback, cancel]
  ) as T

  // Cleanup on unmount
  useEffect(() => {
    return cancel
  }, [cancel])

  return {
    debouncedCallback,
    cancel,
    flush,
    isPending
  }
}

/**
 * Hook for debouncing state updates
 * 
 * @param initialValue - Initial state value
 * @param delay - Delay in milliseconds
 * @returns [debouncedValue, immediateValue, setValue, cancel]
 * 
 * @example
 * ```tsx
 * const [debouncedValue, immediateValue, setValue, cancel] = useDebouncedState('', 300)
 * 
 * useEffect(() => {
 *   if (debouncedValue) {
 *     performSearch(debouncedValue)
 *   }
 * }, [debouncedValue])
 * 
 * return (
 *   <div>
 *     <input
 *       value={immediateValue}
 *       onChange={(e) => setValue(e.target.value)}
 *       placeholder="Search..."
 *     />
 *     <button onClick={cancel}>Cancel Search</button>
 *     <p>Immediate: {immediateValue}</p>
 *     <p>Debounced: {debouncedValue}</p>
 *   </div>
 * )
 * ```
 */
export function useDebouncedState<T>(
  initialValue: T,
  delay: number
): [T, T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [immediateValue, setImmediateValue] = useState<T>(initialValue)
  const [debouncedValue, setDebouncedValue] = useState<T>(initialValue)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    const newValue = value instanceof Function ? value(immediateValue) : value
    setImmediateValue(newValue)

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(newValue)
    }, delay)
  }, [immediateValue, delay])

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = undefined
    }
  }, [])

  useEffect(() => {
    return cancel
  }, [cancel])

  return [debouncedValue, immediateValue, setValue, cancel]
}

export default useDebounce