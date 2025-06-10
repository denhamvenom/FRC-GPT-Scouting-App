import { useEffect, useRef, useCallback } from 'react'

export interface KeyboardShortcut {
  /** The key combination (e.g., 'cmd+k', 'ctrl+shift+d', 'escape') */
  key: string
  /** Callback function when shortcut is triggered */
  callback: (event: KeyboardEvent) => void
  /** Whether to prevent default behavior */
  preventDefault?: boolean
  /** Whether to stop event propagation */
  stopPropagation?: boolean
  /** Element to attach listener to (defaults to document) */
  target?: HTMLElement | Document | Window
  /** Whether the shortcut is enabled */
  enabled?: boolean
  /** Description for debugging/help */
  description?: string
}

export interface UseKeyboardOptions {
  /** Whether shortcuts are globally enabled */
  enabled?: boolean
  /** Whether to ignore shortcuts when typing in input fields */
  ignoreInputFields?: boolean
  /** Custom target element */
  target?: HTMLElement | Document | Window
}

/**
 * Parse keyboard shortcut string into modifier keys and main key
 */
function parseShortcut(shortcut: string) {
  const parts = shortcut.toLowerCase().split('+')
  const mainKey = parts[parts.length - 1]
  const modifiers = parts.slice(0, -1)

  return {
    mainKey,
    ctrl: modifiers.includes('ctrl'),
    meta: modifiers.includes('cmd') || modifiers.includes('meta'),
    alt: modifiers.includes('alt'),
    shift: modifiers.includes('shift')
  }
}

/**
 * Check if keyboard event matches the parsed shortcut
 */
function matchesShortcut(event: KeyboardEvent, parsed: ReturnType<typeof parseShortcut>) {
  const { mainKey, ctrl, meta, alt, shift } = parsed
  
  // Check main key
  if (event.key.toLowerCase() !== mainKey && event.code.toLowerCase() !== mainKey) {
    return false
  }

  // Check modifiers
  if (event.ctrlKey !== ctrl) return false
  if (event.metaKey !== meta) return false
  if (event.altKey !== alt) return false
  if (event.shiftKey !== shift) return false

  return true
}

/**
 * Check if the active element is an input field
 */
function isInputField(element: Element | null): boolean {
  if (!element) return false
  
  const tagName = element.tagName.toLowerCase()
  const isInput = tagName === 'input' || tagName === 'textarea' || tagName === 'select'
  const isContentEditable = element.getAttribute('contenteditable') === 'true'
  
  return isInput || isContentEditable
}

/**
 * Hook for managing keyboard shortcuts
 * 
 * @param shortcuts - Array of keyboard shortcuts
 * @param options - Configuration options
 * 
 * @example
 * ```tsx
 * import { useKeyboard } from '@/hooks/useKeyboard'
 * 
 * function MyComponent() {
 *   const [isModalOpen, setIsModalOpen] = useState(false)
 *   const [selectedItem, setSelectedItem] = useState(null)
 * 
 *   useKeyboard([
 *     {
 *       key: 'cmd+k',
 *       callback: () => setIsModalOpen(true),
 *       description: 'Open command palette'
 *     },
 *     {
 *       key: 'escape',
 *       callback: () => setIsModalOpen(false),
 *       description: 'Close modal'
 *     },
 *     {
 *       key: 'delete',
 *       callback: () => handleDelete(selectedItem),
 *       enabled: !!selectedItem,
 *       description: 'Delete selected item'
 *     }
 *   ])
 * 
 *   return <div>...</div>
 * }
 * ```
 */
export function useKeyboard(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardOptions = {}
) {
  const {
    enabled = true,
    ignoreInputFields = true,
    target = typeof document !== 'undefined' ? document : null
  } = options

  const shortcutsRef = useRef(shortcuts)
  shortcutsRef.current = shortcuts

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      // Ignore shortcuts when typing in input fields
      if (ignoreInputFields && isInputField(event.target as Element)) {
        return
      }

      // Check each shortcut
      for (const shortcut of shortcutsRef.current) {
        if (shortcut.enabled === false) continue

        const parsed = parseShortcut(shortcut.key)
        if (matchesShortcut(event, parsed)) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault()
          }
          if (shortcut.stopPropagation) {
            event.stopPropagation()
          }
          shortcut.callback(event)
          break // Only trigger first matching shortcut
        }
      }
    },
    [enabled, ignoreInputFields]
  )

  useEffect(() => {
    if (!target) return

    target.addEventListener('keydown', handleKeyDown as EventListener)
    return () => {
      target.removeEventListener('keydown', handleKeyDown as EventListener)
    }
  }, [target, handleKeyDown])
}

/**
 * Hook for managing a single keyboard shortcut
 * 
 * @param key - Keyboard shortcut string
 * @param callback - Function to call when shortcut is triggered
 * @param options - Configuration options
 * 
 * @example
 * ```tsx
 * const [count, setCount] = useState(0)
 * 
 * useKeyboardShortcut('cmd+k', () => {
 *   console.log('Command palette opened')
 * })
 * 
 * useKeyboardShortcut('space', () => {
 *   setCount(prev => prev + 1)
 * }, {
 *   enabled: true,
 *   preventDefault: true
 * })
 * ```
 */
export function useKeyboardShortcut(
  key: string,
  callback: (event: KeyboardEvent) => void,
  options: Omit<KeyboardShortcut, 'key' | 'callback'> & UseKeyboardOptions = {}
) {
  const {
    preventDefault,
    stopPropagation,
    enabled = true,
    description,
    ignoreInputFields,
    target
  } = options

  useKeyboard(
    [
      {
        key,
        callback,
        preventDefault,
        stopPropagation,
        enabled,
        description
      }
    ],
    { enabled, ignoreInputFields, target }
  )
}

/**
 * Hook for managing arrow key navigation
 * 
 * @param options - Navigation configuration
 * @returns Object with navigation methods
 * 
 * @example
 * ```tsx
 * const items = ['item1', 'item2', 'item3']
 * const { selectedIndex, setSelectedIndex } = useArrowKeyNavigation({
 *   itemCount: items.length,
 *   onSelect: (index) => console.log('Selected:', items[index]),
 *   wrap: true
 * })
 * 
 * return (
 *   <ul>
 *     {items.map((item, index) => (
 *       <li
 *         key={item}
 *         className={selectedIndex === index ? 'selected' : ''}
 *       >
 *         {item}
 *       </li>
 *     ))}
 *   </ul>
 * )
 * ```
 */
export function useArrowKeyNavigation(options: {
  /** Number of items to navigate through */
  itemCount: number
  /** Initial selected index */
  initialIndex?: number
  /** Callback when an item is selected (Enter key) */
  onSelect?: (index: number) => void
  /** Whether to wrap around when reaching boundaries */
  wrap?: boolean
  /** Whether navigation is enabled */
  enabled?: boolean
  /** Custom key bindings */
  keys?: {
    up?: string
    down?: string
    left?: string
    right?: string
    select?: string
    escape?: string
  }
  /** Navigation direction */
  direction?: 'vertical' | 'horizontal' | 'both'
  /** Callback when escape is pressed */
  onEscape?: () => void
}) {
  const {
    itemCount,
    initialIndex = 0,
    onSelect,
    wrap = false,
    enabled = true,
    keys = {},
    direction = 'vertical',
    onEscape
  } = options

  const [selectedIndex, setSelectedIndex] = React.useState(initialIndex)

  const defaultKeys = {
    up: 'arrowup',
    down: 'arrowdown',
    left: 'arrowleft',
    right: 'arrowright',
    select: 'enter',
    escape: 'escape'
  }

  const finalKeys = { ...defaultKeys, ...keys }

  const moveUp = useCallback(() => {
    setSelectedIndex(prev => {
      if (prev <= 0) {
        return wrap ? itemCount - 1 : 0
      }
      return prev - 1
    })
  }, [itemCount, wrap])

  const moveDown = useCallback(() => {
    setSelectedIndex(prev => {
      if (prev >= itemCount - 1) {
        return wrap ? 0 : itemCount - 1
      }
      return prev + 1
    })
  }, [itemCount, wrap])

  const moveLeft = useCallback(() => {
    if (direction === 'horizontal' || direction === 'both') {
      moveUp()
    }
  }, [direction, moveUp])

  const moveRight = useCallback(() => {
    if (direction === 'horizontal' || direction === 'both') {
      moveDown()
    }
  }, [direction, moveDown])

  const handleSelect = useCallback(() => {
    if (selectedIndex >= 0 && selectedIndex < itemCount) {
      onSelect?.(selectedIndex)
    }
  }, [selectedIndex, itemCount, onSelect])

  const shortcuts: KeyboardShortcut[] = [
    {
      key: finalKeys.select,
      callback: handleSelect,
      enabled: enabled && !!onSelect
    },
    {
      key: finalKeys.escape,
      callback: () => onEscape?.(),
      enabled: enabled && !!onEscape
    }
  ]

  if (direction === 'vertical' || direction === 'both') {
    shortcuts.push(
      {
        key: finalKeys.up,
        callback: moveUp,
        enabled: enabled && itemCount > 0
      },
      {
        key: finalKeys.down,
        callback: moveDown,
        enabled: enabled && itemCount > 0
      }
    )
  }

  if (direction === 'horizontal' || direction === 'both') {
    shortcuts.push(
      {
        key: finalKeys.left,
        callback: moveLeft,
        enabled: enabled && itemCount > 0
      },
      {
        key: finalKeys.right,
        callback: moveRight,
        enabled: enabled && itemCount > 0
      }
    )
  }

  useKeyboard(shortcuts, { enabled })

  // Reset selected index when item count changes
  useEffect(() => {
    if (selectedIndex >= itemCount) {
      setSelectedIndex(Math.max(0, itemCount - 1))
    }
  }, [itemCount, selectedIndex])

  return {
    selectedIndex,
    setSelectedIndex,
    moveUp,
    moveDown,
    moveLeft,
    moveRight,
    selectCurrent: handleSelect
  }
}

/**
 * Hook for managing global keyboard shortcuts with context awareness
 * 
 * @param shortcuts - Object mapping contexts to shortcuts
 * @param currentContext - Current active context
 * 
 * @example
 * ```tsx
 * const { setContext, currentContext } = useContextualKeyboard({
 *   global: [
 *     { key: 'cmd+k', callback: () => openCommandPalette() }
 *   ],
 *   modal: [
 *     { key: 'escape', callback: () => closeModal() },
 *     { key: 'enter', callback: () => confirmAction() }
 *   ],
 *   editing: [
 *     { key: 'cmd+s', callback: () => save() },
 *     { key: 'cmd+z', callback: () => undo() }
 *   ]
 * }, 'global')
 * 
 * // Change context when entering edit mode
 * const startEditing = () => setContext('editing')
 * ```
 */
export function useContextualKeyboard<T extends string>(
  shortcuts: Record<T, KeyboardShortcut[]>,
  initialContext: T
) {
  const [currentContext, setCurrentContext] = React.useState<T>(initialContext)
  
  const activeShortcuts = shortcuts[currentContext] || []
  
  useKeyboard(activeShortcuts)
  
  return {
    currentContext,
    setContext: setCurrentContext,
    activeShortcuts
  }
}

/**
 * Hook that provides information about currently pressed keys
 * 
 * @returns Object with pressed keys information
 * 
 * @example
 * ```tsx
 * const { pressedKeys, isKeyPressed } = usePressedKeys()
 * 
 * return (
 *   <div>
 *     <p>Pressed keys: {Array.from(pressedKeys).join(', ')}</p>
 *     <p>Ctrl pressed: {isKeyPressed('Control')}</p>
 *     <p>Shift pressed: {isKeyPressed('Shift')}</p>
 *   </div>
 * )
 * ```
 */
export function usePressedKeys() {
  const [pressedKeys, setPressedKeys] = React.useState<Set<string>>(new Set())

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    setPressedKeys(prev => new Set(prev).add(event.key))
  }, [])

  const handleKeyUp = useCallback((event: KeyboardEvent) => {
    setPressedKeys(prev => {
      const next = new Set(prev)
      next.delete(event.key)
      return next
    })
  }, [])

  const handleWindowBlur = useCallback(() => {
    setPressedKeys(new Set())
  }, [])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    window.addEventListener('blur', handleWindowBlur)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
      window.removeEventListener('blur', handleWindowBlur)
    }
  }, [handleKeyDown, handleKeyUp, handleWindowBlur])

  const isKeyPressed = useCallback(
    (key: string) => pressedKeys.has(key),
    [pressedKeys]
  )

  return {
    pressedKeys,
    isKeyPressed
  }
}

export default useKeyboard