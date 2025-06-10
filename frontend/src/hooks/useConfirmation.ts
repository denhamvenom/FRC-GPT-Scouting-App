import { useState, useCallback } from 'react'
import type { ConfirmationDialogProps } from '../components/common/ConfirmationDialog'

export interface ConfirmationOptions {
  /** Dialog title */
  title: string
  /** Dialog message */
  message: string | React.ReactNode
  /** Confirm button text */
  confirmText?: string
  /** Cancel button text */
  cancelText?: string
  /** Dialog variant */
  variant?: 'danger' | 'warning' | 'success' | 'primary'
  /** Custom icon */
  icon?: React.ReactNode
  /** Additional content */
  children?: React.ReactNode
  /** Whether to close on overlay click */
  closeOnOverlayClick?: boolean
}

export interface ConfirmationState {
  /** Whether the dialog is open */
  isOpen: boolean
  /** Dialog configuration */
  options: ConfirmationOptions | null
  /** Promise resolvers */
  resolvers: {
    resolve: (confirmed: boolean) => void
    reject: (error: Error) => void
  } | null
  /** Loading state */
  isLoading: boolean
}

/**
 * Hook for managing confirmation dialogs
 * 
 * @returns Object with confirmation state and methods
 * 
 * @example
 * ```tsx
 * import { useConfirmation } from '@/hooks/useConfirmation'
 * import ConfirmationDialog from '@/components/common/ConfirmationDialog'
 * 
 * function MyComponent() {
 *   const { confirm, confirmationProps } = useConfirmation()
 * 
 *   const handleDelete = async () => {
 *     const confirmed = await confirm({
 *       title: 'Delete Item',
 *       message: 'Are you sure you want to delete this item?',
 *       variant: 'danger',
 *       confirmText: 'Delete'
 *     })
 * 
 *     if (confirmed) {
 *       // Proceed with deletion
 *       console.log('Item deleted')
 *     }
 *   }
 * 
 *   return (
 *     <div>
 *       <button onClick={handleDelete}>Delete Item</button>
 *       <ConfirmationDialog {...confirmationProps} />
 *     </div>
 *   )
 * }
 * ```
 * 
 * @example
 * ```tsx
 * // With async confirmation action
 * const handleSave = async () => {
 *   const confirmed = await confirm({
 *     title: 'Save Changes',
 *     message: 'Do you want to save your changes?',
 *     confirmText: 'Save',
 *     variant: 'primary'
 *   })
 * 
 *   if (confirmed) {
 *     try {
 *       setConfirmationLoading(true)
 *       await saveData()
 *       console.log('Data saved successfully')
 *     } catch (error) {
 *       console.error('Failed to save:', error)
 *     } finally {
 *       setConfirmationLoading(false)
 *     }
 *   }
 * }
 * ```
 */
export function useConfirmation() {
  const [state, setState] = useState<ConfirmationState>({
    isOpen: false,
    options: null,
    resolvers: null,
    isLoading: false
  })

  const confirm = useCallback((options: ConfirmationOptions): Promise<boolean> => {
    return new Promise((resolve, reject) => {
      setState({
        isOpen: true,
        options,
        resolvers: { resolve, reject },
        isLoading: false
      })
    })
  }, [])

  const handleConfirm = useCallback(async () => {
    if (!state.resolvers) return

    try {
      setState(prev => ({ ...prev, isLoading: true }))
      state.resolvers.resolve(true)
    } catch (error) {
      state.resolvers.reject(error as Error)
    } finally {
      setState({
        isOpen: false,
        options: null,
        resolvers: null,
        isLoading: false
      })
    }
  }, [state.resolvers])

  const handleCancel = useCallback(() => {
    if (state.resolvers) {
      state.resolvers.resolve(false)
    }
    setState({
      isOpen: false,
      options: null,
      resolvers: null,
      isLoading: false
    })
  }, [state.resolvers])

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }))
  }, [])

  const confirmationProps: ConfirmationDialogProps = {
    isOpen: state.isOpen,
    title: state.options?.title || '',
    message: state.options?.message || '',
    confirmText: state.options?.confirmText,
    cancelText: state.options?.cancelText,
    variant: state.options?.variant,
    icon: state.options?.icon,
    children: state.options?.children,
    closeOnOverlayClick: state.options?.closeOnOverlayClick,
    isLoading: state.isLoading,
    onConfirm: handleConfirm,
    onCancel: handleCancel
  }

  return {
    /** Show confirmation dialog */
    confirm,
    /** Props to pass to ConfirmationDialog component */
    confirmationProps,
    /** Set loading state for async confirmations */
    setConfirmationLoading: setLoading,
    /** Current confirmation state */
    isConfirmationOpen: state.isOpen,
    /** Whether confirmation is loading */
    isConfirmationLoading: state.isLoading
  }
}

/**
 * Hook for creating a reusable confirmation with predefined options
 * 
 * @param defaultOptions - Default confirmation options
 * @returns Confirmation function with preset options
 * 
 * @example
 * ```tsx
 * const confirmDelete = useConfirmationWithDefaults({
 *   title: 'Delete Item',
 *   variant: 'danger',
 *   confirmText: 'Delete',
 *   icon: <TrashIcon />
 * })
 * 
 * const handleDelete = async (itemName: string) => {
 *   const confirmed = await confirmDelete({
 *     message: `Are you sure you want to delete "${itemName}"?`
 *   })
 * 
 *   if (confirmed) {
 *     // Delete item
 *   }
 * }
 * ```
 */
export function useConfirmationWithDefaults(defaultOptions: Partial<ConfirmationOptions>) {
  const { confirm } = useConfirmation()

  return useCallback(
    (options: Partial<ConfirmationOptions> = {}) => {
      const mergedOptions = { ...defaultOptions, ...options } as ConfirmationOptions
      return confirm(mergedOptions)
    },
    [confirm, defaultOptions]
  )
}

/**
 * Hook for managing confirmation with automatic async handling
 * 
 * @param asyncAction - The async action to perform on confirmation
 * @param options - Confirmation options
 * @returns Object with confirmation method and state
 * 
 * @example
 * ```tsx
 * const { confirmAndExecute, confirmationProps, isLoading } = useAsyncConfirmation(
 *   async (userId: string) => {
 *     await deleteUser(userId)
 *     showSuccessToast('User deleted successfully')
 *   },
 *   {
 *     title: 'Delete User',
 *     variant: 'danger',
 *     confirmText: 'Delete User'
 *   }
 * )
 * 
 * const handleDeleteUser = (userId: string) => {
 *   confirmAndExecute(
 *     { message: `Are you sure you want to delete this user?` },
 *     userId
 *   )
 * }
 * 
 * return (
 *   <div>
 *     <button onClick={() => handleDeleteUser('123')}>
 *       Delete User
 *     </button>
 *     <ConfirmationDialog {...confirmationProps} />
 *   </div>
 * )
 * ```
 */
export function useAsyncConfirmation<T extends any[]>(
  asyncAction: (...args: T) => Promise<void>,
  defaultOptions: Partial<ConfirmationOptions>
) {
  const { confirm, confirmationProps, setConfirmationLoading } = useConfirmation()
  const [isLoading, setIsLoading] = useState(false)

  const confirmAndExecute = useCallback(
    async (
      options: Partial<ConfirmationOptions> = {},
      ...args: T
    ): Promise<boolean> => {
      const mergedOptions = { ...defaultOptions, ...options } as ConfirmationOptions
      
      try {
        const confirmed = await confirm(mergedOptions)
        
        if (confirmed) {
          setIsLoading(true)
          setConfirmationLoading(true)
          
          await asyncAction(...args)
          return true
        }
        
        return false
      } catch (error) {
        console.error('Async confirmation action failed:', error)
        throw error
      } finally {
        setIsLoading(false)
        setConfirmationLoading(false)
      }
    },
    [confirm, setConfirmationLoading, asyncAction, defaultOptions]
  )

  return {
    /** Confirm and execute async action */
    confirmAndExecute,
    /** Props for ConfirmationDialog */
    confirmationProps,
    /** Whether async action is loading */
    isLoading
  }
}

/**
 * Hook for quick confirmation dialogs with common presets
 * 
 * @returns Object with preset confirmation methods
 * 
 * @example
 * ```tsx
 * const { confirmDelete, confirmSave, confirmDiscard, confirmationProps } = useQuickConfirmation()
 * 
 * const handleDelete = async () => {
 *   if (await confirmDelete('this item')) {
 *     // Delete item
 *   }
 * }
 * 
 * const handleSave = async () => {
 *   if (await confirmSave()) {
 *     // Save changes
 *   }
 * }
 * 
 * return (
 *   <div>
 *     <button onClick={handleDelete}>Delete</button>
 *     <button onClick={handleSave}>Save</button>
 *     <ConfirmationDialog {...confirmationProps} />
 *   </div>
 * )
 * ```
 */
export function useQuickConfirmation() {
  const { confirm, confirmationProps } = useConfirmation()

  const confirmDelete = useCallback(
    (itemName: string = 'this item') =>
      confirm({
        title: 'Delete Item',
        message: `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
        variant: 'danger',
        confirmText: 'Delete',
        cancelText: 'Cancel'
      }),
    [confirm]
  )

  const confirmSave = useCallback(
    (message: string = 'Do you want to save your changes?') =>
      confirm({
        title: 'Save Changes',
        message,
        variant: 'primary',
        confirmText: 'Save',
        cancelText: 'Cancel'
      }),
    [confirm]
  )

  const confirmDiscard = useCallback(
    (message: string = 'Are you sure you want to discard your changes?') =>
      confirm({
        title: 'Discard Changes',
        message,
        variant: 'warning',
        confirmText: 'Discard',
        cancelText: 'Keep Editing'
      }),
    [confirm]
  )

  const confirmLogout = useCallback(
    () =>
      confirm({
        title: 'Log Out',
        message: 'Are you sure you want to log out?',
        variant: 'warning',
        confirmText: 'Log Out',
        cancelText: 'Cancel'
      }),
    [confirm]
  )

  return {
    confirmDelete,
    confirmSave,
    confirmDiscard,
    confirmLogout,
    confirmationProps
  }
}

export default useConfirmation