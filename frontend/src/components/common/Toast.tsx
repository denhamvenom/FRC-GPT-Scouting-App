import React, { useEffect, useState } from 'react'

export interface ToastProps {
  /** Unique identifier */
  id: string
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
  /** Close handler */
  onClose?: (id: string) => void
  /** Custom icon */
  icon?: React.ReactNode
  /** Action button */
  action?: {
    label: string
    onClick: () => void
  }
  /** Additional CSS classes */
  className?: string
}

export interface ToastContainerProps {
  /** Array of toasts to display */
  toasts: ToastProps[]
  /** Default position for all toasts */
  defaultPosition?: ToastProps['position']
  /** Maximum number of toasts to show */
  maxToasts?: number
  /** Default duration for toasts */
  defaultDuration?: number
  /** Container className */
  className?: string
}

const typeStyles = {
  success: {
    container: 'bg-green-50 border-green-200',
    icon: 'text-green-400',
    title: 'text-green-800',
    message: 'text-green-700',
    close: 'text-green-500 hover:text-green-600'
  },
  error: {
    container: 'bg-red-50 border-red-200',
    icon: 'text-red-400',
    title: 'text-red-800',
    message: 'text-red-700',
    close: 'text-red-500 hover:text-red-600'
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-200',
    icon: 'text-yellow-400',
    title: 'text-yellow-800',
    message: 'text-yellow-700',
    close: 'text-yellow-500 hover:text-yellow-600'
  },
  info: {
    container: 'bg-blue-50 border-blue-200',
    icon: 'text-blue-400',
    title: 'text-blue-800',
    message: 'text-blue-700',
    close: 'text-blue-500 hover:text-blue-600'
  }
}

const defaultIcons = {
  success: (
    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  ),
  error: (
    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  ),
  info: (
    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  )
}

const positionClasses = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
  'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
  'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
}

/**
 * Individual Toast component
 */
export const Toast: React.FC<ToastProps> = ({
  id,
  title,
  message,
  type = 'info',
  duration = 5000,
  dismissible = true,
  onClose,
  icon,
  action,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(true)
  const [isRemoving, setIsRemoving] = useState(false)
  const styles = typeStyles[type]

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [duration])

  const handleClose = () => {
    setIsRemoving(true)
    setTimeout(() => {
      setIsVisible(false)
      onClose?.(id)
    }, 300) // Animation duration
  }

  if (!isVisible) return null

  return (
    <div
      className={`
        max-w-sm w-full ${styles.container} border rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden
        ${isRemoving ? 'animate-pulse opacity-0' : 'animate-bounce'}
        transform transition-all duration-300 ease-in-out
        ${className}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          {/* Icon */}
          <div className="flex-shrink-0">
            <div className={styles.icon}>
              {icon || defaultIcons[type]}
            </div>
          </div>
          
          {/* Content */}
          <div className="ml-3 w-0 flex-1 pt-0.5">
            {title && (
              <p className={`text-sm font-medium ${styles.title}`}>
                {title}
              </p>
            )}
            <p className={`text-sm ${styles.message} ${title ? 'mt-1' : ''}`}>
              {message}
            </p>
            
            {/* Action button */}
            {action && (
              <div className="mt-2">
                <button
                  type="button"
                  onClick={action.onClick}
                  className={`text-sm font-medium ${styles.title} hover:underline focus:outline-none focus:underline`}
                >
                  {action.label}
                </button>
              </div>
            )}
          </div>
          
          {/* Close button */}
          {dismissible && (
            <div className="ml-4 flex-shrink-0 flex">
              <button
                type="button"
                className={`rounded-md inline-flex ${styles.close} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-green-50 focus:ring-green-600`}
                onClick={handleClose}
              >
                <span className="sr-only">Close</span>
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * ToastContainer component for managing multiple toasts
 * 
 * @example
 * ```tsx
 * // Basic usage
 * const [toasts, setToasts] = useState<ToastProps[]>([])
 * 
 * const addToast = (toast: Omit<ToastProps, 'id'>) => {
 *   const newToast = { ...toast, id: Date.now().toString() }
 *   setToasts(prev => [...prev, newToast])
 * }
 * 
 * const removeToast = (id: string) => {
 *   setToasts(prev => prev.filter(toast => toast.id !== id))
 * }
 * 
 * <ToastContainer
 *   toasts={toasts}
 *   defaultPosition="top-right"
 *   maxToasts={5}
 * />
 * 
 * // Usage with useToast hook (when created)
 * const { toasts, addToast } = useToast()
 * 
 * <button onClick={() => addToast({
 *   type: 'success',
 *   title: 'Success!',
 *   message: 'Your action was completed successfully.'
 * })}>
 *   Show Toast
 * </button>
 * 
 * <ToastContainer toasts={toasts} />
 * ```
 */
export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  defaultPosition = 'top-right',
  maxToasts = 5,
  defaultDuration = 5000,
  className = ''
}) => {
  // Group toasts by position
  const toastsByPosition = toasts.reduce((acc, toast) => {
    const position = toast.position || defaultPosition
    if (!acc[position]) acc[position] = []
    acc[position].push(toast)
    return acc
  }, {} as Record<string, ToastProps[]>)

  const handleClose = (id: string) => {
    // This should be handled by parent component
    // The toast component will call this but the parent needs to update the toasts array
  }

  return (
    <>
      {Object.entries(toastsByPosition).map(([position, positionToasts]) => (
        <div
          key={position}
          className={`fixed z-50 ${positionClasses[position as keyof typeof positionClasses]} ${className}`}
        >
          <div className="flex flex-col space-y-4">
            {positionToasts.slice(0, maxToasts).map((toast) => (
              <Toast
                key={toast.id}
                {...toast}
                duration={toast.duration ?? defaultDuration}
                onClose={handleClose}
              />
            ))}
          </div>
        </div>
      ))}
    </>
  )
}

export default Toast