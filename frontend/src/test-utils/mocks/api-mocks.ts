/**
 * Mock implementations for API calls
 */

// Mock team data
export const mockTeamData = [
  {
    team_number: 1234,
    nickname: "Test Team Alpha",
    rookie_year: 2020,
    location: "Test City, ST",
    performance: {
      auto_avg: 25.5,
      teleop_avg: 95.2,
      endgame_avg: 18.3,
      total_avg: 139.0
    }
  },
  {
    team_number: 5678,
    nickname: "Test Team Beta",
    rookie_year: 2018,
    location: "Another City, ST",
    performance: {
      auto_avg: 30.1,
      teleop_avg: 88.7,
      endgame_avg: 22.4,
      total_avg: 141.2
    }
  }
]

// Mock picklist data
export const mockPicklistData = {
  rankings: [
    {
      team: 1234,
      rank: 1,
      strengths: ["Auto", "Defense"],
      notes: 4.8
    },
    {
      team: 5678,
      rank: 2,
      strengths: ["Teleop", "Climbing"],
      notes: 4.5
    }
  ],
  metadata: {
    total_teams: 2,
    strategy: "Balanced approach focusing on versatility",
    excluded_teams: [],
    generated_at: "2025-06-06T12:00:00Z"
  }
}

// Mock alliance selection data
export const mockAllianceData = {
  alliances: [
    {
      captain: 1234,
      first_pick: 5678,
      second_pick: 9012,
      declined: []
    },
    {
      captain: 3456,
      first_pick: 7890,
      second_pick: null,
      declined: [1357]
    }
  ],
  available_teams: [2468, 1357, 1111],
  current_pick: "second",
  current_alliance: 1,
  round: 2
}

// Mock event data
export const mockEventData = {
  event_key: "2025lake",
  name: "Lake Superior Regional",
  year: 2025,
  week: 1,
  start_date: "2025-03-06",
  end_date: "2025-03-09",
  location: "Duluth, MN"
}

// Mock validation results
export const mockValidationResults = {
  total_teams: 45,
  outliers_detected: 3,
  corrections_applied: 2,
  validation_errors: [
    {
      team: 1234,
      field: "auto_points",
      original_value: 150,
      corrected_value: 35,
      reason: "Statistical outlier (Z-score: 4.2)"
    }
  ],
  statistics: {
    auto_points: { mean: 28.5, std: 8.2, min: 0, max: 45 },
    teleop_points: { mean: 95.1, std: 15.3, min: 40, max: 130 }
  }
}

// Mock progress data
export const mockProgressData = {
  operation_id: "test-operation-123",
  progress: 75,
  status: "in_progress",
  message: "Processing teams 30/40...",
  estimated_time_remaining: 45,
  started_at: "2025-06-06T12:00:00Z"
}

// API response wrapper
export const createMockApiResponse = <T>(data: T, status = 200) => ({
  status,
  ok: status >= 200 && status < 300,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data))
})

// Error response helper
export const createMockApiError = (message = "API Error", status = 500) => ({
  status,
  ok: false,
  json: () => Promise.resolve({ error: message }),
  text: () => Promise.resolve(JSON.stringify({ error: message }))
})

// Mock fetch implementation
export const mockFetch = (response: any, delay = 0) => {
  return vi.fn().mockImplementation(() =>
    new Promise(resolve =>
      setTimeout(() => resolve(createMockApiResponse(response)), delay)
    )
  )
}

// Mock fetch with error
export const mockFetchError = (message = "Network Error", delay = 0) => {
  return vi.fn().mockImplementation(() =>
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error(message)), delay)
    )
  )
}