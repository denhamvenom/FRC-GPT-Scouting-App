import React, { useState, useMemo } from 'react'
import LoadingSpinner from './LoadingSpinner'

export interface DataTableColumn<T> {
  /** Unique identifier for the column */
  key: string
  /** Display title for the column header */
  title: string
  /** Function to render cell content */
  render?: (value: any, record: T, index: number) => React.ReactNode
  /** Whether the column is sortable */
  sortable?: boolean
  /** Custom sort function */
  sorter?: (a: T, b: T) => number
  /** Column width */
  width?: string | number
  /** Column alignment */
  align?: 'left' | 'center' | 'right'
  /** Whether the column is fixed */
  fixed?: 'left' | 'right'
  /** Custom header render function */
  headerRender?: () => React.ReactNode
}

export interface DataTableProps<T> {
  /** Array of data to display */
  data: T[]
  /** Column definitions */
  columns: DataTableColumn<T>[]
  /** Loading state */
  loading?: boolean
  /** Empty state message */
  emptyText?: string
  /** Row key function */
  rowKey?: (record: T) => string | number
  /** Row click handler */
  onRowClick?: (record: T, index: number) => void
  /** Row selection configuration */
  rowSelection?: {
    selectedRowKeys?: (string | number)[]
    onChange?: (selectedRowKeys: (string | number)[], selectedRows: T[]) => void
    type?: 'checkbox' | 'radio'
  }
  /** Table size */
  size?: 'small' | 'medium' | 'large'
  /** Whether to show header */
  showHeader?: boolean
  /** Whether to show borders */
  bordered?: boolean
  /** Whether rows are striped */
  striped?: boolean
  /** Custom row class name function */
  rowClassName?: (record: T, index: number) => string
  /** Pagination configuration */
  pagination?: {
    current?: number
    pageSize?: number
    total?: number
    onChange?: (page: number, pageSize?: number) => void
    showSizeChanger?: boolean
    pageSizeOptions?: string[]
  }
  /** Additional table props */
  className?: string
}

const sizeClasses = {
  small: 'text-xs',
  medium: 'text-sm',
  large: 'text-base'
}

const paddingClasses = {
  small: 'px-2 py-1',
  medium: 'px-4 py-2',
  large: 'px-6 py-3'
}

/**
 * DataTable component for displaying tabular data
 * 
 * @example
 * ```tsx
 * // Basic usage
 * const columns = [
 *   { key: 'name', title: 'Name', sortable: true },
 *   { key: 'age', title: 'Age', sortable: true },
 *   { 
 *     key: 'actions', 
 *     title: 'Actions',
 *     render: (_, record) => (
 *       <button onClick={() => edit(record)}>Edit</button>
 *     )
 *   }
 * ]
 * 
 * <DataTable
 *   data={users}
 *   columns={columns}
 *   rowKey={(record) => record.id}
 * />
 * 
 * // With row selection
 * <DataTable
 *   data={users}
 *   columns={columns}
 *   rowKey={(record) => record.id}
 *   rowSelection={{
 *     selectedRowKeys: selectedKeys,
 *     onChange: (keys, rows) => setSelectedKeys(keys),
 *     type: 'checkbox'
 *   }}
 * />
 * 
 * // With pagination
 * <DataTable
 *   data={users}
 *   columns={columns}
 *   rowKey={(record) => record.id}
 *   pagination={{
 *     current: currentPage,
 *     pageSize: 10,
 *     total: totalUsers,
 *     onChange: (page) => setCurrentPage(page)
 *   }}
 * />
 * ```
 */
export function DataTable<T = any>({
  data,
  columns,
  loading = false,
  emptyText = 'No data',
  rowKey = (_, index) => index,
  onRowClick,
  rowSelection,
  size = 'medium',
  showHeader = true,
  bordered = true,
  striped = false,
  rowClassName,
  pagination,
  className = ''
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Handle sorting
  const handleSort = (column: DataTableColumn<T>) => {
    if (!column.sortable) return

    if (sortColumn === column.key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column.key)
      setSortDirection('asc')
    }
  }

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn) return data

    const column = columns.find(col => col.key === sortColumn)
    if (!column) return data

    return [...data].sort((a, b) => {
      if (column.sorter) {
        return sortDirection === 'asc' 
          ? column.sorter(a, b)
          : column.sorter(b, a)
      }

      // Default sorting by key value
      const aValue = (a as any)[column.key]
      const bValue = (b as any)[column.key]

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [data, columns, sortColumn, sortDirection])

  // Handle pagination
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData

    const { current = 1, pageSize = 10 } = pagination
    const start = (current - 1) * pageSize
    return sortedData.slice(start, start + pageSize)
  }, [sortedData, pagination])

  // Get cell value
  const getCellValue = (record: T, column: DataTableColumn<T>, index: number) => {
    if (column.render) {
      return column.render((record as any)[column.key], record, index)
    }
    return (record as any)[column.key]
  }

  // Handle row selection
  const handleRowSelect = (record: T, selected: boolean) => {
    if (!rowSelection) return

    const key = rowKey(record)
    const selectedKeys = rowSelection.selectedRowKeys || []
    
    let newSelectedKeys: (string | number)[]
    if (rowSelection.type === 'radio') {
      newSelectedKeys = selected ? [key] : []
    } else {
      newSelectedKeys = selected
        ? [...selectedKeys, key]
        : selectedKeys.filter(k => k !== key)
    }

    const newSelectedRows = data.filter(item => 
      newSelectedKeys.includes(rowKey(item))
    )

    rowSelection.onChange?.(newSelectedKeys, newSelectedRows)
  }

  // Handle select all
  const handleSelectAll = (selected: boolean) => {
    if (!rowSelection) return

    const newSelectedKeys = selected
      ? paginatedData.map(record => rowKey(record))
      : []

    const newSelectedRows = selected ? [...paginatedData] : []
    rowSelection.onChange?.(newSelectedKeys, newSelectedRows)
  }

  const tableClasses = [
    'min-w-full divide-y divide-gray-200',
    bordered && 'border border-gray-200',
    sizeClasses[size],
    className
  ].filter(Boolean).join(' ')

  const selectedKeys = rowSelection?.selectedRowKeys || []
  const isAllSelected = paginatedData.length > 0 && 
    paginatedData.every(record => selectedKeys.includes(rowKey(record)))
  const isIndeterminate = selectedKeys.length > 0 && !isAllSelected

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner text="Loading data..." />
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 text-lg">{emptyText}</div>
      </div>
    )
  }

  return (
    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
      <div className="overflow-x-auto">
        <table className={tableClasses}>
          {showHeader && (
            <thead className="bg-gray-50">
              <tr>
                {rowSelection && (
                  <th className={`${paddingClasses[size]} text-left`}>
                    {rowSelection.type !== 'radio' && (
                      <input
                        type="checkbox"
                        checked={isAllSelected}
                        ref={input => {
                          if (input) input.indeterminate = isIndeterminate
                        }}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    )}
                  </th>
                )}
                {columns.map((column) => (
                  <th
                    key={column.key}
                    className={`${paddingClasses[size]} text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                    } ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''}`}
                    style={{ width: column.width }}
                    onClick={() => handleSort(column)}
                  >
                    <div className="flex items-center space-x-1">
                      <span>
                        {column.headerRender ? column.headerRender() : column.title}
                      </span>
                      {column.sortable && (
                        <div className="flex flex-col">
                          <svg
                            className={`w-3 h-3 ${
                              sortColumn === column.key && sortDirection === 'asc'
                                ? 'text-blue-600'
                                : 'text-gray-400'
                            }`}
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <svg
                            className={`w-3 h-3 -mt-1 ${
                              sortColumn === column.key && sortDirection === 'desc'
                                ? 'text-blue-600'
                                : 'text-gray-400'
                            }`}
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((record, index) => {
              const key = rowKey(record)
              const isSelected = selectedKeys.includes(key)
              const rowClasses = [
                striped && index % 2 === 1 && 'bg-gray-50',
                onRowClick && 'cursor-pointer hover:bg-gray-50',
                isSelected && 'bg-blue-50',
                rowClassName?.(record, index)
              ].filter(Boolean).join(' ')

              return (
                <tr
                  key={key}
                  className={rowClasses}
                  onClick={() => onRowClick?.(record, index)}
                >
                  {rowSelection && (
                    <td className={paddingClasses[size]}>
                      <input
                        type={rowSelection.type || 'checkbox'}
                        checked={isSelected}
                        onChange={(e) => handleRowSelect(record, e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    </td>
                  )}
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`${paddingClasses[size]} whitespace-nowrap text-gray-900 ${
                        column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''
                      }`}
                      style={{ width: column.width }}
                    >
                      {getCellValue(record, column, index)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      
      {pagination && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => pagination.onChange?.(Math.max(1, (pagination.current || 1) - 1))}
              disabled={(pagination.current || 1) <= 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => pagination.onChange?.((pagination.current || 1) + 1)}
              disabled={(pagination.current || 1) >= Math.ceil((pagination.total || 0) / (pagination.pageSize || 10))}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">
                  {((pagination.current || 1) - 1) * (pagination.pageSize || 10) + 1}
                </span>{' '}
                to{' '}
                <span className="font-medium">
                  {Math.min((pagination.current || 1) * (pagination.pageSize || 10), pagination.total || 0)}
                </span>{' '}
                of{' '}
                <span className="font-medium">{pagination.total || 0}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => pagination.onChange?.(Math.max(1, (pagination.current || 1) - 1))}
                  disabled={(pagination.current || 1) <= 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => pagination.onChange?.((pagination.current || 1) + 1)}
                  disabled={(pagination.current || 1) >= Math.ceil((pagination.total || 0) / (pagination.pageSize || 10))}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataTable