import React, { useState, useEffect, useRef } from 'react'

export interface SearchInputProps {
  /** Current search value */
  value?: string
  /** Placeholder text */
  placeholder?: string
  /** Search handler with debounced input */
  onSearch?: (value: string) => void
  /** Change handler for immediate updates */
  onChange?: (value: string) => void
  /** Debounce delay in milliseconds */
  debounceMs?: number
  /** Whether to show search icon */
  showSearchIcon?: boolean
  /** Whether to show clear button */
  showClearButton?: boolean
  /** Size of the input */
  size?: 'small' | 'medium' | 'large'
  /** Whether the input is disabled */
  disabled?: boolean
  /** Whether the input is loading */
  loading?: boolean
  /** Auto focus on mount */
  autoFocus?: boolean
  /** Additional CSS classes */
  className?: string
  /** Custom search icon */
  searchIcon?: React.ReactNode
  /** Custom clear icon */
  clearIcon?: React.ReactNode
  /** Keyboard shortcuts */
  shortcuts?: {
    /** Focus shortcut (e.g., 'cmd+k') */
    focus?: string
    /** Clear shortcut (e.g., 'escape') */
    clear?: string
  }
  /** Input props to pass through */
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>
}

const sizeClasses = {
  small: {
    input: 'px-8 py-1 text-sm',
    icon: 'h-4 w-4',
    iconPosition: 'left-2'
  },
  medium: {
    input: 'px-10 py-2 text-base',
    icon: 'h-5 w-5',
    iconPosition: 'left-3'
  },
  large: {
    input: 'px-12 py-3 text-lg',
    icon: 'h-6 w-6',
    iconPosition: 'left-4'
  }
}

/**
 * SearchInput component with debouncing and advanced features
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <SearchInput
 *   placeholder="Search..."
 *   onSearch={(value) => handleSearch(value)}
 * />
 * 
 * // With controlled value and custom debounce
 * <SearchInput
 *   value={searchValue}
 *   onChange={setSearchValue}
 *   onSearch={handleSearch}
 *   debounceMs={500}
 *   placeholder="Search teams..."
 * />
 * 
 * // With keyboard shortcuts
 * <SearchInput
 *   placeholder="Search (⌘K)"
 *   onSearch={handleSearch}
 *   shortcuts={{
 *     focus: 'cmd+k',
 *     clear: 'escape'
 *   }}
 *   autoFocus
 * />
 * 
 * // With loading state
 * <SearchInput
 *   value={searchValue}
 *   onSearch={handleSearch}
 *   loading={isSearching}
 *   placeholder="Search..."
 *   size="large"
 * />
 * ```
 */
export const SearchInput: React.FC<SearchInputProps> = ({
  value = '',
  placeholder = 'Search...',
  onSearch,
  onChange,
  debounceMs = 300,
  showSearchIcon = true,
  showClearButton = true,
  size = 'medium',
  disabled = false,
  loading = false,
  autoFocus = false,
  className = '',
  searchIcon,
  clearIcon,
  shortcuts,
  inputProps = {}
}) => {
  const [internalValue, setInternalValue] = useState(value)
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<NodeJS.Timeout>()
  const styles = sizeClasses[size]

  // Sync internal value with prop value
  useEffect(() => {
    setInternalValue(value)
  }, [value])

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      if (onSearch && internalValue !== value) {
        onSearch(internalValue)
      }
    }, debounceMs)

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [internalValue, debounceMs, onSearch, value])

  // Keyboard shortcuts
  useEffect(() => {
    if (!shortcuts) return

    const handleKeydown = (e: KeyboardEvent) => {
      // Focus shortcut
      if (shortcuts.focus) {
        const [modifier, key] = shortcuts.focus.split('+')
        const isModifierPressed = modifier === 'cmd' ? e.metaKey : 
                                 modifier === 'ctrl' ? e.ctrlKey :
                                 modifier === 'alt' ? e.altKey :
                                 modifier === 'shift' ? e.shiftKey : false

        if (isModifierPressed && e.key.toLowerCase() === key.toLowerCase()) {
          e.preventDefault()
          inputRef.current?.focus()
        }
      }

      // Clear shortcut
      if (shortcuts.clear && e.key.toLowerCase() === shortcuts.clear.toLowerCase()) {
        if (document.activeElement === inputRef.current) {
          e.preventDefault()
          handleClear()
        }
      }
    }

    document.addEventListener('keydown', handleKeydown)
    return () => document.removeEventListener('keydown', handleKeydown)
  }, [shortcuts])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInternalValue(newValue)
    onChange?.(newValue)
  }

  const handleClear = () => {
    setInternalValue('')
    onChange?.('')
    onSearch?.('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      handleClear()
    }
    inputProps.onKeyDown?.(e)
  }

  const defaultSearchIcon = (
    <svg
      className={`${styles.icon} text-gray-400`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  )

  const defaultClearIcon = (
    <svg
      className={`${styles.icon} text-gray-400 hover:text-gray-600`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  )

  const loadingIcon = (
    <svg
      className={`${styles.icon} text-gray-400 animate-spin`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
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
  )

  return (
    <div className={`relative ${className}`}>
      {/* Search icon */}
      {showSearchIcon && (
        <div className={`absolute inset-y-0 ${styles.iconPosition} flex items-center pointer-events-none`}>
          {loading ? loadingIcon : (searchIcon || defaultSearchIcon)}
        </div>
      )}

      {/* Input */}
      <input
        {...inputProps}
        ref={inputRef}
        type="text"
        value={internalValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={(e) => {
          setIsFocused(true)
          inputProps.onFocus?.(e)
        }}
        onBlur={(e) => {
          setIsFocused(false)
          inputProps.onBlur?.(e)
        }}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        className={`
          block w-full ${styles.input} border border-gray-300 rounded-md
          focus:ring-blue-500 focus:border-blue-500
          disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
          ${showSearchIcon ? (showClearButton && internalValue ? 'pr-16' : 'pr-4') : (showClearButton && internalValue ? 'pr-12' : 'pr-4')}
          ${isFocused ? 'ring-1 ring-blue-500 border-blue-500' : ''}
          transition-colors duration-200
        `}
      />

      {/* Clear button */}
      {showClearButton && internalValue && !disabled && (
        <button
          type="button"
          onClick={handleClear}
          className={`absolute inset-y-0 right-2 flex items-center px-1 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1`}
          tabIndex={-1}
        >
          {clearIcon || defaultClearIcon}
        </button>
      )}
    </div>
  )
}

export default SearchInput