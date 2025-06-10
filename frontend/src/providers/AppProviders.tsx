import React, { ReactNode } from 'react';
import { ErrorProvider } from '../context/ErrorContext';
import { AppProvider } from '../context/AppContext';
import { AllianceProvider } from '../context/AllianceContext';
import { PicklistProvider } from '../context/PicklistContext';
import { ApiProvider } from './ApiProvider';
import { ThemeProvider } from './ThemeProvider';

/**
 * Composition component that provides all global providers
 * in the correct order for the application.
 * 
 * Provider order is important:
 * 1. ErrorProvider - Must be first to catch errors from other providers
 * 2. ThemeProvider - UI theming
 * 3. ApiProvider - API client configuration
 * 4. AppProvider - Global app state
 * 5. PicklistProvider - Picklist-specific state
 * 6. AllianceProvider - Alliance-specific state
 */
export interface AppProvidersProps {
  children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <ErrorProvider>
      <ThemeProvider>
        <ApiProvider>
          <AppProvider>
            <PicklistProvider>
              <AllianceProvider>
                {children}
              </AllianceProvider>
            </PicklistProvider>
          </AppProvider>
        </ApiProvider>
      </ThemeProvider>
    </ErrorProvider>
  );
}

/**
 * Alternative provider for testing that only includes
 * essential providers without external dependencies
 */
export interface TestProvidersProps {
  children: ReactNode;
  mockApiClient?: any;
}

export function TestProviders({ children, mockApiClient }: TestProvidersProps) {
  return (
    <ErrorProvider>
      <ThemeProvider>
        <ApiProvider apiClient={mockApiClient}>
          <AppProvider>
            <PicklistProvider>
              <AllianceProvider>
                {children}
              </AllianceProvider>
            </PicklistProvider>
          </AppProvider>
        </ApiProvider>
      </ThemeProvider>
    </ErrorProvider>
  );
}

/**
 * Minimal provider for components that only need error handling
 * and theming without state management
 */
export interface MinimalProvidersProps {
  children: ReactNode;
}

export function MinimalProviders({ children }: MinimalProvidersProps) {
  return (
    <ErrorProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </ErrorProvider>
  );
}

/**
 * Provider for stories/documentation that includes
 * all providers with mock data
 */
export interface StoryProvidersProps {
  children: ReactNode;
  initialState?: {
    app?: any;
    picklist?: any;
    alliance?: any;
  };
}

export function StoryProviders({ children, initialState }: StoryProvidersProps) {
  // Mock API client for stories
  const mockApiClient = {
    get: async () => ({ data: null }),
    post: async () => ({ data: null }),
    put: async () => ({ data: null }),
    delete: async () => ({ data: null }),
  };
  
  return (
    <ErrorProvider>
      <ThemeProvider defaultTheme="light">
        <ApiProvider apiClient={mockApiClient}>
          <AppProvider initialState={initialState?.app}>
            <PicklistProvider initialState={initialState?.picklist}>
              <AllianceProvider initialState={initialState?.alliance}>
                {children}
              </AllianceProvider>
            </PicklistProvider>
          </AppProvider>
        </ApiProvider>
      </ThemeProvider>
    </ErrorProvider>
  );
}