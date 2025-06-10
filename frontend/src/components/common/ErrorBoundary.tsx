import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  /** Fallback UI to render when an error occurs */
  fallback?: (error: Error, errorInfo: ErrorInfo, resetError: () => void) => ReactNode
  /** Whether to show detailed error information in development */
  showDetails?: boolean
  /** Callback when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  /** Custom error message */
  message?: string
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * ErrorBoundary component for catching and handling React errors
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 * 
 * // With custom fallback
 * <ErrorBoundary
 *   fallback={(error, errorInfo, resetError) => (
 *     <div>
 *       <h2>Something went wrong!</h2>
 *       <button onClick={resetError}>Try again</button>
 *     </div>
 *   )}
 * >
 *   <App />
 * </ErrorBoundary>
 * 
 * // With error logging
 * <ErrorBoundary
 *   onError={(error, errorInfo) => {
 *     console.error('Error caught:', error)
 *     // Send to error tracking service
 *   }}
 * >
 *   <App />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Call the optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  private resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  public render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback && this.state.errorInfo) {
        return this.props.fallback(
          this.state.error,
          this.state.errorInfo,
          this.resetError
        )
      }

      // Default fallback UI
      const isDevelopment = process.env.NODE_ENV === 'development'
      const showDetails = this.props.showDetails ?? isDevelopment

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg
                  className="h-6 w-6 text-red-600"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                {this.props.message || 'Something went wrong'}
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                An unexpected error occurred. Please try refreshing the page.
              </p>
              
              {showDetails && this.state.error && (
                <div className="mt-6 text-left">
                  <details className="bg-gray-100 rounded-lg p-4">
                    <summary className="cursor-pointer font-medium text-gray-700">
                      Error Details
                    </summary>
                    <div className="mt-2 space-y-2">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Error:</p>
                        <p className="text-sm text-red-600 font-mono">
                          {this.state.error.toString()}
                        </p>
                      </div>
                      {this.state.errorInfo && (
                        <div>
                          <p className="text-sm font-medium text-gray-600">
                            Component Stack:
                          </p>
                          <pre className="text-xs text-gray-700 overflow-auto max-h-40 font-mono">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                      {this.state.error.stack && (
                        <div>
                          <p className="text-sm font-medium text-gray-600">
                            Stack Trace:
                          </p>
                          <pre className="text-xs text-gray-700 overflow-auto max-h-40 font-mono">
                            {this.state.error.stack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}
              
              <div className="mt-6 space-y-2">
                <button
                  onClick={this.resetError}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Try Again
                </button>
                <button
                  onClick={() => window.location.href = '/'}
                  className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Go Home
                </button>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Functional component wrapper for easier use
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

export default ErrorBoundary