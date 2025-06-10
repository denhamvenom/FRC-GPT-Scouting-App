import React, { useRef, useEffect } from 'react'

export interface ConfirmationDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean
  /** Dialog title */
  title: string
  /** Dialog message/description */
  message: string | React.ReactNode
  /** Confirm button text */
  confirmText?: string
  /** Cancel button text */
  cancelText?: string
  /** Variant for confirm button styling */
  variant?: 'danger' | 'warning' | 'success' | 'primary'
  /** Whether to show loading state */
  isLoading?: boolean
  /** Callback when confirmed */
  onConfirm: () => void | Promise<void>
  /** Callback when cancelled */
  onCancel: () => void
  /** Additional content to show in the dialog */
  children?: React.ReactNode
  /** Whether to close on overlay click */
  closeOnOverlayClick?: boolean
  /** Icon to display */
  icon?: React.ReactNode
}

const variantStyles = {
  danger: {
    button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
    icon: 'text-red-600',
    iconBg: 'bg-red-100'
  },
  warning: {
    button: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
    icon: 'text-yellow-600',
    iconBg: 'bg-yellow-100'
  },
  success: {
    button: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
    icon: 'text-green-600',
    iconBg: 'bg-green-100'
  },
  primary: {
    button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
    icon: 'text-blue-600',
    iconBg: 'bg-blue-100'
  }
}

const defaultIcons = {
  danger: (
    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  warning: (
    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  success: (
    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  primary: (
    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

/**
 * ConfirmationDialog component for user confirmations
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <ConfirmationDialog
 *   isOpen={isOpen}
 *   title="Delete Item"
 *   message="Are you sure you want to delete this item?"
 *   onConfirm={handleDelete}
 *   onCancel={() => setIsOpen(false)}
 * />
 * 
 * // With custom variant and loading state
 * <ConfirmationDialog
 *   isOpen={isOpen}
 *   title="Delete Account"
 *   message="This action cannot be undone. All your data will be permanently deleted."
 *   variant="danger"
 *   confirmText="Delete Account"
 *   isLoading={isDeleting}
 *   onConfirm={async () => {
 *     setIsDeleting(true)
 *     await deleteAccount()
 *     setIsDeleting(false)
 *   }}
 *   onCancel={() => setIsOpen(false)}
 * />
 * 
 * // With custom content
 * <ConfirmationDialog
 *   isOpen={isOpen}
 *   title="Review Changes"
 *   message="Please review the following changes:"
 *   onConfirm={handleConfirm}
 *   onCancel={handleCancel}
 * >
 *   <ul className="mt-2 text-sm text-gray-600">
 *     <li>• Change 1</li>
 *     <li>• Change 2</li>
 *   </ul>
 * </ConfirmationDialog>
 * ```
 */
export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'primary',
  isLoading = false,
  onConfirm,
  onCancel,
  children,
  closeOnOverlayClick = true,
  icon
}) => {
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const styles = variantStyles[variant]

  useEffect(() => {
    if (isOpen) {
      cancelButtonRef.current?.focus()
    }
  }, [isOpen])

  const handleConfirm = async () => {
    const result = onConfirm()
    if (result instanceof Promise) {
      await result
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onCancel()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed z-50 inset-0 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          aria-hidden="true"
          onClick={handleOverlayClick}
        />

        {/* This element is to trick the browser into centering the modal contents. */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
          &#8203;
        </span>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="sm:flex sm:items-start">
            <div className={`mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full ${styles.iconBg} sm:mx-0 sm:h-10 sm:w-10`}>
              <div className={styles.icon}>
                {icon || defaultIcons[variant]}
              </div>
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                {title}
              </h3>
              <div className="mt-2">
                <div className="text-sm text-gray-500">
                  {message}
                </div>
                {children}
              </div>
            </div>
          </div>
          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white ${styles.button} focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed`}
              onClick={handleConfirm}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </>
              ) : (
                confirmText
              )}
            </button>
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
              onClick={onCancel}
              ref={cancelButtonRef}
              disabled={isLoading}
            >
              {cancelText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfirmationDialog