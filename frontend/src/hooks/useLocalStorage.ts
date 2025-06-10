import { useState, useEffect, useCallback, useMemo, useRef } from 'react'

/**
 * Custom hook for managing localStorage with automatic serialization
 * 
 * @param key - The localStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @param options - Configuration options
 * @returns [value, setValue, removeValue]
 * 
 * @example
 * ```tsx
 * // Basic usage
 * const [name, setName] = useLocalStorage('user-name', '')
 * 
 * // With complex object
 * const [user, setUser] = useLocalStorage('user', { id: '', name: '' })
 * 
 * // With error handling
 * const [settings, setSettings, removeSettings] = useLocalStorage(
 *   'app-settings',
 *   { theme: 'light' },
 *   {
 *     onError: (error) => console.error('localStorage error:', error),
 *     syncAcrossTabs: true
 *   }
 * )
 * 
 * // Remove value
 * const handleLogout = () => {
 *   removeSettings()
 * }
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: {
    /** Called when an error occurs during serialization/deserialization */
    onError?: (error: Error) => void
    /** Whether to sync changes across browser tabs */
    syncAcrossTabs?: boolean
    /** Custom serializer function */
    serializer?: {
      stringify: (value: T) => string
      parse: (value: string) => T
    }
  } = {}
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const { onError, syncAcrossTabs = false, serializer } = options

  // Default serializer
  const defaultSerializer = {
    stringify: (value: T): string => {
      try {
        return JSON.stringify(value)
      } catch (error) {
        onError?.(error as Error)
        return JSON.stringify(initialValue)
      }
    },
    parse: (value: string): T => {
      try {
        return JSON.parse(value)
      } catch (error) {
        onError?.(error as Error)
        return initialValue
      }
    }
  }

  const activeSerializer = useMemo(() => serializer || defaultSerializer, [serializer])

  // Get initial value from localStorage
  const getStoredValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue
    }

    try {
      const item = window.localStorage.getItem(key)
      return item !== null ? activeSerializer.parse(item) : initialValue
    } catch (error) {
      onError?.(error as Error)
      return initialValue
    }
  }, [key, initialValue, activeSerializer, onError])

  const [storedValue, setStoredValue] = useState<T>(getStoredValue)

  // Update localStorage when value changes
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        // Allow value to be a function so we have the same API as useState
        setStoredValue(prevValue => {
          const valueToStore = value instanceof Function ? value(prevValue) : value
          
          // Save to localStorage
          if (typeof window !== 'undefined') {
            window.localStorage.setItem(key, activeSerializer.stringify(valueToStore))
          }
          
          return valueToStore
        })
      } catch (error) {
        onError?.(error as Error)
      }
    },
    [key, activeSerializer, onError]
  )

  // Remove from localStorage
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key)
      }
    } catch (error) {
      onError?.(error as Error)
    }
  }, [key, initialValue, onError])

  // Listen for changes in other tabs/windows
  useEffect(() => {
    if (!syncAcrossTabs || typeof window === 'undefined') {
      return
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(activeSerializer.parse(e.newValue))
        } catch (error) {
          onError?.(error as Error)
        }
      } else if (e.key === key && e.newValue === null) {
        setStoredValue(initialValue)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [key, initialValue, activeSerializer, onError, syncAcrossTabs])

  // Sync with localStorage on mount (in case it changed while component was unmounted)
  const isInitialized = useRef(false)
  useEffect(() => {
    if (!isInitialized.current) {
      const currentValue = getStoredValue()
      setStoredValue(currentValue)
      isInitialized.current = true
    }
  }, [getStoredValue])

  return [storedValue, setValue, removeValue]
}

/**
 * Hook for managing localStorage with type-safe string values
 */
export function useLocalStorageString(
  key: string,
  initialValue: string = '',
  options?: Omit<Parameters<typeof useLocalStorage>[2], 'serializer'>
) {
  return useLocalStorage(key, initialValue, {
    ...options,
    serializer: {
      stringify: (value: string) => value,
      parse: (value: string) => value
    }
  })
}

/**
 * Hook for managing localStorage with boolean values
 */
export function useLocalStorageBoolean(
  key: string,
  initialValue: boolean = false,
  options?: Omit<Parameters<typeof useLocalStorage>[2], 'serializer'>
) {
  return useLocalStorage(key, initialValue, {
    ...options,
    serializer: {
      stringify: (value: boolean) => value.toString(),
      parse: (value: string) => value === 'true'
    }
  })
}

/**
 * Hook for managing localStorage with number values
 */
export function useLocalStorageNumber(
  key: string,
  initialValue: number = 0,
  options?: Omit<Parameters<typeof useLocalStorage>[2], 'serializer'>
) {
  return useLocalStorage(key, initialValue, {
    ...options,
    serializer: {
      stringify: (value: number) => value.toString(),
      parse: (value: string) => {
        const parsed = parseFloat(value)
        return isNaN(parsed) ? initialValue : parsed
      }
    }
  })
}

/**
 * Hook for managing an array in localStorage with helper methods
 */
export function useLocalStorageArray<T>(
  key: string,
  initialValue: T[] = [],
  options?: Omit<Parameters<typeof useLocalStorage>[2], 'serializer'>
) {
  const [array, setArray, removeArray] = useLocalStorage<T[]>(key, initialValue, options)

  const addItem = useCallback((item: T) => {
    setArray(prev => [...prev, item])
  }, [setArray])

  const removeItem = useCallback((index: number) => {
    setArray(prev => prev.filter((_, i) => i !== index))
  }, [setArray])

  const updateItem = useCallback((index: number, item: T) => {
    setArray(prev => prev.map((existing, i) => i === index ? item : existing))
  }, [setArray])

  const clear = useCallback(() => {
    setArray([])
  }, [setArray])

  return {
    array,
    setArray,
    removeArray,
    addItem,
    removeItem,
    updateItem,
    clear
  }
}

export default useLocalStorage