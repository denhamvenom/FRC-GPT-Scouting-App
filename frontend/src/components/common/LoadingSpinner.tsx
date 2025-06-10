import React from 'react'

export interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large' | 'xlarge'
  /** Color of the spinner */
  color?: 'primary' | 'secondary' | 'white' | 'gray'
  /** Optional text to display below the spinner */
  text?: string
  /** Whether to show the spinner inline */
  inline?: boolean
  /** Additional CSS classes */
  className?: string
}

const sizeClasses = {
  small: 'h-4 w-4',
  medium: 'h-8 w-8',
  large: 'h-12 w-12',
  xlarge: 'h-16 w-16'
}

const colorClasses = {
  primary: 'text-blue-600',
  secondary: 'text-gray-600',
  white: 'text-white',
  gray: 'text-gray-400'
}

/**
 * LoadingSpinner component for indicating loading states
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <LoadingSpinner />
 * 
 * // With text
 * <LoadingSpinner text="Loading data..." />
 * 
 * // Large size with primary color
 * <LoadingSpinner size="large" color="primary" />
 * 
 * // Inline spinner
 * <LoadingSpinner size="small" inline />
 * ```
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = 'primary',
  text,
  inline = false,
  className = ''
}) => {
  const containerClasses = inline
    ? 'inline-flex items-center'
    : 'flex flex-col items-center justify-center'

  return (
    <div className={`${containerClasses} ${className}`}>
      <svg
        className={`animate-spin ${sizeClasses[size]} ${colorClasses[color]}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        data-testid="loading-spinner"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {text && (
        <p
          className={`mt-2 text-sm ${
            color === 'white' ? 'text-white' : 'text-gray-600'
          }`}
        >
          {text}
        </p>
      )}
    </div>
  )
}

// Default export for convenience
export default LoadingSpinner