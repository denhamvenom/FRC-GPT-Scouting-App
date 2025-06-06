/**
 * Custom render utilities for testing React components
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Custom render function with additional context providers
export const renderWithProviders = (
  ui: ReactElement,
  {
    initialEntries = ['/'],
    ...renderOptions
  }: {
    initialEntries?: string[]
  } & Omit<RenderOptions, 'wrapper'> = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <BrowserRouter>
        {children}
      </BrowserRouter>
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Helper to create mock props for components
export const createMockProps = <T extends Record<string, any>>(
  overrides: Partial<T> = {}
): T => {
  const defaultProps = {
    onClick: vi.fn(),
    onChange: vi.fn(),
    onSubmit: vi.fn(),
    onClose: vi.fn(),
    onSave: vi.fn(),
    onDelete: vi.fn(),
    onUpdate: vi.fn(),
    onCancel: vi.fn(),
  }

  return { ...defaultProps, ...overrides } as T
}

// Helper to wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0))

// Mock API response helper
export const mockApiResponse = <T,>(data: T, delay = 0): Promise<T> => {
  return new Promise(resolve => {
    setTimeout(() => resolve(data), delay)
  })
}

// Mock API error helper
export const mockApiError = (message = 'API Error', delay = 0): Promise<never> => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error(message)), delay)
  })
}