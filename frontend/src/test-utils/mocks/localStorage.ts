/**
 * Mock localStorage implementation for testing
 */

export class MockLocalStorage {
  private store: Record<string, string> = {}

  getItem(key: string): string | null {
    return this.store[key] || null
  }

  setItem(key: string, value: string): void {
    this.store[key] = String(value)
  }

  removeItem(key: string): void {
    delete this.store[key]
  }

  clear(): void {
    this.store = {}
  }

  key(index: number): string | null {
    const keys = Object.keys(this.store)
    return keys[index] || null
  }

  get length(): number {
    return Object.keys(this.store).length
  }

  // Helper methods for testing
  getAllKeys(): string[] {
    return Object.keys(this.store)
  }

  getAllValues(): Record<string, string> {
    return { ...this.store }
  }

  reset(): void {
    this.store = {}
  }
}

// Helper to setup localStorage mock with initial data
export const setupLocalStorageMock = (initialData: Record<string, any> = {}) => {
  const mockStorage = new MockLocalStorage()
  
  // Set initial data
  Object.entries(initialData).forEach(([key, value]) => {
    mockStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value))
  })

  // Mock the localStorage
  Object.defineProperty(global, 'localStorage', {
    value: mockStorage,
    writable: true
  })

  return mockStorage
}

// Common localStorage keys used in the app
export const LOCAL_STORAGE_KEYS = {
  EVENT_CONFIG: 'frc_event_config',
  TEAM_DATA: 'frc_team_data',
  PICKLIST_SETTINGS: 'frc_picklist_settings',
  ALLIANCE_STATE: 'frc_alliance_state',
  USER_PREFERENCES: 'frc_user_preferences',
  SCHEMA_MAPPINGS: 'frc_schema_mappings'
} as const

// Mock data for localStorage
export const mockLocalStorageData = {
  [LOCAL_STORAGE_KEYS.EVENT_CONFIG]: {
    event_key: "2025lake",
    sheet_id: "test-sheet-id",
    last_updated: "2025-06-06T12:00:00Z"
  },
  [LOCAL_STORAGE_KEYS.USER_PREFERENCES]: {
    theme: "light",
    auto_refresh: true,
    polling_interval: 5000
  },
  [LOCAL_STORAGE_KEYS.PICKLIST_SETTINGS]: {
    excluded_teams: [1357, 2468],
    strategy_prompt: "Focus on auto and defense",
    max_teams: 24
  }
}