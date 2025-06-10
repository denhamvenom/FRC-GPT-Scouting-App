import { useState, useCallback, useRef } from 'react'
import type { ToastProps } from '../components/common/Toast'

export interface ToastOptions {
  /** Toast title */
  title?: string
  /** Toast message */
  message: string
  /** Toast type */
  type?: 'success' | 'error' | 'warning' | 'info'
  /** Duration in milliseconds (0 for persistent) */
  duration?: number
  /** Whether the toast can be dismissed */
  dismissible?: boolean
  /** Position of the toast */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  /** Custom icon */
  icon?: React.ReactNode
  /** Action button */
  action?: {
    label: string
    onClick: () => void
  }
}

/**
 * Hook for managing toast notifications
 * 
 * @param options - Default options for all toasts
 * @returns Object with toast methods and state
 * 
 * @example
 * ```tsx
 * import { useToast } from '@/hooks/useToast'
 * import { ToastContainer } from '@/components/common/Toast'
 * 
 * function MyComponent() {
 *   const { toasts, addToast, success, error, warning, info } = useToast()
 * 
 *   const handleSuccess = () => {
 *     success('Operation completed successfully!')
 *   }
 * 
 *   const handleError = () => {
 *     error('Something went wrong', {
 *       title: 'Error',
 *       action: {
 *         label: 'Retry',
 *         onClick: () => console.log('Retrying...')
 *       }
 *     })
 *   }
 * 
 *   return (
 *     <div>
 *       <button onClick={handleSuccess}>Show Success</button>
 *       <button onClick={handleError}>Show Error</button>
 *       <ToastContainer toasts={toasts} />
 *     </div>
 *   )
 * }
 * ```
 */
export function useToast(defaultOptions: Partial<ToastOptions> = {}) {
  const [toasts, setToasts] = useState<ToastProps[]>([])
  const toastIdRef = useRef(0)

  const addToast = useCallback(
    (options: ToastOptions): string => {
      const id = `toast-${++toastIdRef.current}`
      const mergedOptions = { ...defaultOptions, ...options }
      
      const newToast: ToastProps = {
        id,
        title: mergedOptions.title,
        message: mergedOptions.message,
        type: mergedOptions.type || 'info',
        duration: mergedOptions.duration ?? 5000,
        dismissible: mergedOptions.dismissible ?? true,
        position: mergedOptions.position || 'top-right',
        icon: mergedOptions.icon,
        action: mergedOptions.action,
        onClose: removeToast
      }

      setToasts(prev => [...prev, newToast])
      return id
    },
    [defaultOptions]
  )

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const clearAllToasts = useCallback(() => {
    setToasts([])
  }, [])

  const updateToast = useCallback((id: string, updates: Partial<ToastOptions>) => {
    setToasts(prev =>
      prev.map(toast =>
        toast.id === id
          ? {
              ...toast,
              ...updates,
              onClose: removeToast
            }
          : toast
      )
    )
  }, [removeToast])

  // Convenience methods for different toast types
  const success = useCallback(
    (message: string, options: Omit<ToastOptions, 'message' | 'type'> = {}) =>
      addToast({ ...options, message, type: 'success' }),
    [addToast]
  )

  const error = useCallback(
    (message: string, options: Omit<ToastOptions, 'message' | 'type'> = {}) =>
      addToast({ ...options, message, type: 'error' }),
    [addToast]
  )

  const warning = useCallback(
    (message: string, options: Omit<ToastOptions, 'message' | 'type'> = {}) =>
      addToast({ ...options, message, type: 'warning' }),
    [addToast]
  )

  const info = useCallback(
    (message: string, options: Omit<ToastOptions, 'message' | 'type'> = {}) =>
      addToast({ ...options, message, type: 'info' }),
    [addToast]
  )

  return {
    /** Array of current toasts */
    toasts,
    /** Add a new toast */
    addToast,
    /** Remove a specific toast */
    removeToast,
    /** Clear all toasts */
    clearAllToasts,
    /** Update an existing toast */
    updateToast,
    /** Show success toast */
    success,
    /** Show error toast */
    error,
    /** Show warning toast */
    warning,
    /** Show info toast */
    info
  }
}

/**
 * Hook for toast notifications with async operation support
 * 
 * @returns Object with async toast methods
 * 
 * @example
 * ```tsx
 * const { toastAsync, toasts } = useAsyncToast()
 * 
 * const handleAsyncOperation = async () => {
 *   await toastAsync(
 *     async () => {
 *       // Simulate async operation
 *       await new Promise(resolve => setTimeout(resolve, 2000))
 *       throw new Error('Something went wrong')
 *     },
 *     {
 *       loading: 'Saving data...',
 *       success: 'Data saved successfully!',
 *       error: 'Failed to save data'
 *     }
 *   )
 * }
 * ```
 */
export function useAsyncToast(defaultOptions: Partial<ToastOptions> = {}) {
  const toast = useToast(defaultOptions)

  const toastAsync = useCallback(
    async <T>(
      asyncFn: () => Promise<T>,
      messages: {
        loading: string
        success: string | ((data: T) => string)
        error: string | ((error: Error) => string)
      },
      options: {
        loadingOptions?: Partial<ToastOptions>
        successOptions?: Partial<ToastOptions>
        errorOptions?: Partial<ToastOptions>
      } = {}
    ): Promise<T> => {
      const loadingToastId = toast.addToast({
        message: messages.loading,
        type: 'info',
        duration: 0,
        dismissible: false,
        ...options.loadingOptions
      })

      try {
        const result = await asyncFn()
        
        toast.removeToast(loadingToastId)
        
        const successMessage = typeof messages.success === 'function' 
          ? messages.success(result)
          : messages.success
          
        toast.success(successMessage, options.successOptions)
        
        return result
      } catch (error) {
        toast.removeToast(loadingToastId)
        
        const errorMessage = typeof messages.error === 'function'
          ? messages.error(error as Error)
          : messages.error
          
        toast.error(errorMessage, options.errorOptions)
        
        throw error
      }
    },
    [toast]
  )

  return {
    ...toast,
    /** Execute async function with automatic toast notifications */
    toastAsync
  }
}

/**
 * Hook for managing toast notifications with promise-based API
 * 
 * @returns Object with promise-based toast methods
 * 
 * @example
 * ```tsx
 * const { toastPromise, toasts } = usePromiseToast()
 * 
 * const handleSave = () => {
 *   const savePromise = saveData()
 *   
 *   toastPromise(savePromise, {
 *     loading: 'Saving...',
 *     success: 'Saved successfully!',
 *     error: 'Failed to save'
 *   })
 * }
 * ```
 */
export function usePromiseToast(defaultOptions: Partial<ToastOptions> = {}) {
  const toast = useAsyncToast(defaultOptions)

  const toastPromise = useCallback(
    <T>(
      promise: Promise<T>,
      messages: {
        loading: string
        success: string | ((data: T) => string)
        error: string | ((error: Error) => string)
      },
      options?: {
        loadingOptions?: Partial<ToastOptions>
        successOptions?: Partial<ToastOptions>
        errorOptions?: Partial<ToastOptions>
      }
    ): Promise<T> => {
      return toast.toastAsync(() => promise, messages, options)
    },
    [toast]
  )

  return {
    ...toast,
    /** Show toast for a promise */
    toastPromise
  }
}

/**
 * Hook for creating persistent toast notifications
 * 
 * @returns Object with persistent toast methods
 * 
 * @example
 * ```tsx
 * const { showPersistent, hidePersistent, toasts } = usePersistentToast()
 * 
 * const showConnecting = () => {
 *   showPersistent('connecting', {
 *     message: 'Connecting to server...',
 *     type: 'info'
 *   })
 * }
 * 
 * const hideConnecting = () => {
 *   hidePersistent('connecting')
 * }
 * ```
 */
export function usePersistentToast(defaultOptions: Partial<ToastOptions> = {}) {
  const toast = useToast(defaultOptions)
  const persistentToastsRef = useRef<Map<string, string>>(new Map())

  const showPersistent = useCallback(
    (key: string, options: ToastOptions): void => {
      // Remove existing persistent toast with this key
      const existingId = persistentToastsRef.current.get(key)
      if (existingId) {
        toast.removeToast(existingId)
      }

      // Add new persistent toast
      const id = toast.addToast({
        ...options,
        duration: 0,
        dismissible: false
      })

      persistentToastsRef.current.set(key, id)
    },
    [toast]
  )

  const hidePersistent = useCallback(
    (key: string): void => {
      const id = persistentToastsRef.current.get(key)
      if (id) {
        toast.removeToast(id)
        persistentToastsRef.current.delete(key)
      }
    },
    [toast]
  )

  const updatePersistent = useCallback(
    (key: string, updates: Partial<ToastOptions>): void => {
      const id = persistentToastsRef.current.get(key)
      if (id) {
        toast.updateToast(id, updates)
      }
    },
    [toast]
  )

  const hideAllPersistent = useCallback(() => {
    for (const id of persistentToastsRef.current.values()) {
      toast.removeToast(id)
    }
    persistentToastsRef.current.clear()
  }, [toast])

  return {
    ...toast,
    /** Show persistent toast with key */
    showPersistent,
    /** Hide persistent toast by key */
    hidePersistent,
    /** Update persistent toast by key */
    updatePersistent,
    /** Hide all persistent toasts */
    hideAllPersistent
  }
}

export default useToast