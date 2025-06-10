// API Hooks (existing)
export { useApi } from './useApi'
export { useApiCall } from './useApiCall'

// Local Storage Hooks
export {
  useLocalStorage,
  useLocalStorageString,
  useLocalStorageBoolean,
  useLocalStorageNumber,
  useLocalStorageArray
} from './useLocalStorage'

// Debouncing Hooks
export {
  useDebounce,
  useDebouncedCallback,
  useAdvancedDebounce,
  useDebouncedState
} from './useDebounce'

// Async Operation Hooks
export {
  useAsync,
  useAsyncCallback,
  useAsyncData,
  useAsyncMultiple
} from './useAsync'
export type { AsyncState, UseAsyncOptions } from './useAsync'

// Confirmation Dialog Hooks
export {
  useConfirmation,
  useConfirmationWithDefaults,
  useAsyncConfirmation,
  useQuickConfirmation
} from './useConfirmation'
export type { ConfirmationOptions, ConfirmationState } from './useConfirmation'

// Toast Notification Hooks
export {
  useToast,
  useAsyncToast,
  usePromiseToast,
  usePersistentToast
} from './useToast'
export type { ToastOptions } from './useToast'

// Keyboard Shortcut Hooks
export {
  useKeyboard,
  useKeyboardShortcut,
  useArrowKeyNavigation,
  useContextualKeyboard,
  usePressedKeys
} from './useKeyboard'
export type { KeyboardShortcut, UseKeyboardOptions } from './useKeyboard'

// Default exports for convenience
export { default as useLocalStorageDefault } from './useLocalStorage'
export { default as useDebounceDefault } from './useDebounce'
export { default as useAsyncDefault } from './useAsync'
export { default as useConfirmationDefault } from './useConfirmation'
export { default as useToastDefault } from './useToast'
export { default as useKeyboardDefault } from './useKeyboard'