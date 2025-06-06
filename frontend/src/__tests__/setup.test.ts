/**
 * Basic setup validation tests for the frontend testing infrastructure
 */

import { describe, it, expect, vi } from 'vitest'
import { 
  mockTeamData, 
  mockPicklistData, 
  createMockApiResponse 
} from '../test-utils/mocks/api-mocks'
import { 
  setupLocalStorageMock, 
  LOCAL_STORAGE_KEYS, 
  mockLocalStorageData 
} from '../test-utils/mocks/localStorage'

describe('Testing Infrastructure Setup', () => {
  it('should have Vitest working correctly', () => {
    expect(true).toBe(true)
    expect(1 + 1).toBe(2)
  })

  it('should have vi (Vitest) mocking available', () => {
    const mockFn = vi.fn()
    mockFn('test')
    expect(mockFn).toHaveBeenCalledWith('test')
    expect(mockFn).toHaveBeenCalledTimes(1)
  })

  it('should have access to mock API data', () => {
    expect(mockTeamData).toBeDefined()
    expect(mockTeamData).toHaveLength(2)
    expect(mockTeamData[0]).toHaveProperty('team_number', 1234)
    expect(mockTeamData[0]).toHaveProperty('nickname', 'Test Team Alpha')

    expect(mockPicklistData).toBeDefined()
    expect(mockPicklistData.rankings).toHaveLength(2)
    expect(mockPicklistData.metadata.total_teams).toBe(2)
  })

  it('should create mock API responses correctly', () => {
    const response = createMockApiResponse(mockTeamData, 200)
    expect(response.status).toBe(200)
    expect(response.ok).toBe(true)
    
    const errorResponse = createMockApiResponse({ error: 'Not found' }, 404)
    expect(errorResponse.status).toBe(404)
    expect(errorResponse.ok).toBe(false)
  })

  it('should have localStorage mocking working', () => {
    const mockStorage = setupLocalStorageMock(mockLocalStorageData)
    
    // Test that initial data was set
    expect(mockStorage.getItem(LOCAL_STORAGE_KEYS.EVENT_CONFIG)).toBeTruthy()
    
    // Test setting and getting items
    mockStorage.setItem('test_key', 'test_value')
    expect(mockStorage.getItem('test_key')).toBe('test_value')
    
    // Test removing items
    mockStorage.removeItem('test_key')
    expect(mockStorage.getItem('test_key')).toBeNull()
    
    // Test clearing storage
    mockStorage.clear()
    expect(mockStorage.length).toBe(0)
  })

  it('should have window.matchMedia mocked', () => {
    expect(window.matchMedia).toBeDefined()
    const mediaQuery = window.matchMedia('(min-width: 768px)')
    expect(mediaQuery.matches).toBe(false)
    expect(typeof mediaQuery.addEventListener).toBe('function')
  })

  it('should have ResizeObserver and IntersectionObserver mocked', () => {
    expect(global.ResizeObserver).toBeDefined()
    expect(global.IntersectionObserver).toBeDefined()
    
    const resizeObserver = new ResizeObserver(() => {})
    expect(typeof resizeObserver.observe).toBe('function')
    
    const intersectionObserver = new IntersectionObserver(() => {})
    expect(typeof intersectionObserver.observe).toBe('function')
  })

  it('should handle JSON operations correctly', () => {
    const testData = { team: 1234, score: 150.5 }
    const jsonString = JSON.stringify(testData)
    const parsed = JSON.parse(jsonString)
    
    expect(parsed.team).toBe(1234)
    expect(parsed.score).toBe(150.5)
  })

  it('should support async/await operations', async () => {
    const asyncOperation = async () => {
      return new Promise(resolve => {
        setTimeout(() => resolve('completed'), 10)
      })
    }
    
    const result = await asyncOperation()
    expect(result).toBe('completed')
  })

  it('should have array and object manipulation working', () => {
    const teams = [1234, 5678, 9012]
    expect(teams).toHaveLength(3)
    expect(teams).toContain(1234)
    expect(Math.max(...teams)).toBe(9012)
    
    const teamData = {
      team_number: 1234,
      nickname: "Test Team",
      performance: {
        auto: 25.0,
        teleop: 100.0
      }
    }
    
    expect(teamData.team_number).toBe(1234)
    expect(teamData.performance.auto).toBe(25.0)
  })
})