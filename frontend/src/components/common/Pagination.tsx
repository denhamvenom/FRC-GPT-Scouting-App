import React from 'react'

export interface PaginationProps {
  /** Current page number (1-based) */
  current: number
  /** Total number of items */
  total: number
  /** Number of items per page */
  pageSize?: number
  /** Page change handler */
  onChange?: (page: number, pageSize?: number) => void
  /** Whether to show page size changer */
  showSizeChanger?: boolean
  /** Available page size options */
  pageSizeOptions?: string[]
  /** Page size change handler */
  onShowSizeChange?: (current: number, size: number) => void
  /** Whether to show quick jumper */
  showQuickJumper?: boolean
  /** Whether to show total count */
  showTotal?: boolean | ((total: number, range: [number, number]) => React.ReactNode)
  /** Size of pagination */
  size?: 'small' | 'default' | 'large'
  /** Number of page buttons to show */
  showLessItems?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Hide on single page */
  hideOnSinglePage?: boolean
  /** Additional CSS classes */
  className?: string
}

const sizeClasses = {
  small: {
    button: 'px-2 py-1 text-xs',
    select: 'text-xs',
    input: 'text-xs px-2 py-1'
  },
  default: {
    button: 'px-3 py-2 text-sm',
    select: 'text-sm',
    input: 'text-sm px-3 py-2'
  },
  large: {
    button: 'px-4 py-2 text-base',
    select: 'text-base',
    input: 'text-base px-4 py-2'
  }
}

/**
 * Pagination component for navigating through pages
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <Pagination
 *   current={currentPage}
 *   total={1000}
 *   pageSize={20}
 *   onChange={(page) => setCurrentPage(page)}
 * />
 * 
 * // With page size changer
 * <Pagination
 *   current={currentPage}
 *   total={1000}
 *   pageSize={pageSize}
 *   showSizeChanger
 *   pageSizeOptions={['10', '20', '50', '100']}
 *   onChange={(page) => setCurrentPage(page)}
 *   onShowSizeChange={(current, size) => {
 *     setCurrentPage(current)
 *     setPageSize(size)
 *   }}
 * />
 * 
 * // With quick jumper and total display
 * <Pagination
 *   current={currentPage}
 *   total={1000}
 *   pageSize={20}
 *   showQuickJumper
 *   showTotal={(total, range) => 
 *     `${range[0]}-${range[1]} of ${total} items`
 *   }
 *   onChange={(page) => setCurrentPage(page)}
 * />
 * ```
 */
export const Pagination: React.FC<PaginationProps> = ({
  current,
  total,
  pageSize = 10,
  onChange,
  showSizeChanger = false,
  pageSizeOptions = ['10', '20', '50', '100'],
  onShowSizeChange,
  showQuickJumper = false,
  showTotal = false,
  size = 'default',
  showLessItems = false,
  disabled = false,
  hideOnSinglePage = false,
  className = ''
}) => {
  const totalPages = Math.ceil(total / pageSize)
  const styles = sizeClasses[size]

  // Hide pagination if only one page
  if (hideOnSinglePage && totalPages <= 1) {
    return null
  }

  // Calculate page range for display
  const getPageRange = () => {
    const delta = showLessItems ? 1 : 2
    const range: number[] = []
    const rangeWithDots: (number | string)[] = []

    for (let i = Math.max(2, current - delta); i <= Math.min(totalPages - 1, current + delta); i++) {
      range.push(i)
    }

    if (current - delta > 2) {
      rangeWithDots.push(1, '...')
    } else {
      rangeWithDots.push(1)
    }

    rangeWithDots.push(...range)

    if (current + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages)
    } else {
      if (totalPages > 1) {
        rangeWithDots.push(totalPages)
      }
    }

    return rangeWithDots
  }

  const handlePageChange = (page: number) => {
    if (page === current || disabled) return
    onChange?.(Math.max(1, Math.min(totalPages, page)), pageSize)
  }

  const handlePageSizeChange = (newPageSize: number) => {
    const newPage = Math.min(current, Math.ceil(total / newPageSize))
    onShowSizeChange?.(newPage, newPageSize)
    onChange?.(newPage, newPageSize)
  }

  const handleQuickJump = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const value = parseInt((e.target as HTMLInputElement).value)
      if (!isNaN(value) && value > 0 && value <= totalPages) {
        handlePageChange(value);
        (e.target as HTMLInputElement).value = ''
      }
    }
  }

  const currentRange: [number, number] = [
    (current - 1) * pageSize + 1,
    Math.min(current * pageSize, total)
  ]

  const baseButtonClasses = `${styles.button} border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 relative inline-flex items-center font-medium focus:z-10 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500`
  const activeButtonClasses = `${styles.button} border border-blue-500 bg-blue-50 text-blue-600 relative inline-flex items-center font-medium z-10 focus:z-20 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500`
  const disabledButtonClasses = `${styles.button} border border-gray-300 bg-gray-50 text-gray-300 relative inline-flex items-center font-medium cursor-not-allowed`

  return (
    <div className={`flex items-center justify-between ${className}`}>
      {/* Total info */}
      {showTotal && (
        <div className="text-sm text-gray-700">
          {typeof showTotal === 'function' 
            ? showTotal(total, currentRange)
            : `Showing ${currentRange[0]} to ${currentRange[1]} of ${total} entries`
          }
        </div>
      )}

      <div className="flex items-center space-x-2">
        {/* Page size changer */}
        {showSizeChanger && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Show</span>
            <select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              disabled={disabled}
              className={`${styles.select} border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500`}
            >
              {pageSizeOptions.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <span className="text-sm text-gray-700">per page</span>
          </div>
        )}

        {/* Pagination controls */}
        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
          {/* Previous button */}
          <button
            onClick={() => handlePageChange(current - 1)}
            disabled={current === 1 || disabled}
            className={`${current === 1 || disabled ? disabledButtonClasses : baseButtonClasses} rounded-l-md`}
          >
            <span className="sr-only">Previous</span>
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>

          {/* Page numbers */}
          {getPageRange().map((page, index) => {
            if (page === '...') {
              return (
                <span
                  key={`ellipsis-${index}`}
                  className={`${styles.button} border border-gray-300 bg-white text-gray-700 relative inline-flex items-center font-medium`}
                >
                  ...
                </span>
              )
            }

            const pageNumber = page as number
            const isActive = pageNumber === current

            return (
              <button
                key={pageNumber}
                onClick={() => handlePageChange(pageNumber)}
                disabled={disabled}
                className={isActive ? activeButtonClasses : (disabled ? disabledButtonClasses : baseButtonClasses)}
                aria-current={isActive ? 'page' : undefined}
              >
                {pageNumber}
              </button>
            )
          })}

          {/* Next button */}
          <button
            onClick={() => handlePageChange(current + 1)}
            disabled={current === totalPages || disabled}
            className={`${current === totalPages || disabled ? disabledButtonClasses : baseButtonClasses} rounded-r-md`}
          >
            <span className="sr-only">Next</span>
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </nav>

        {/* Quick jumper */}
        {showQuickJumper && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Go to</span>
            <input
              type="number"
              min={1}
              max={totalPages}
              placeholder={`1-${totalPages}`}
              onKeyPress={handleQuickJump}
              disabled={disabled}
              className={`${styles.input} w-16 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500`}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default Pagination