# API Contracts

**Purpose**: Complete API specifications and interface definitions  
**Audience**: Frontend developers, API consumers, and AI assistants  
**Scope**: All REST endpoints, request/response formats, and integration patterns  

---

## API Overview

The FRC GPT Scouting App provides a **RESTful API** built with FastAPI that offers comprehensive team analysis and picklist generation capabilities. The API is designed for both human developers and AI assistants, with clear contracts and comprehensive documentation.

### API Characteristics
- **REST Architecture**: Resource-based URLs with standard HTTP methods
- **JSON Format**: All requests and responses use JSON
- **Schema Validation**: Automatic request/response validation with Pydantic
- **OpenAPI Documentation**: Live documentation at `/docs`
- **Versioning**: API versioned for backward compatibility
- **Error Handling**: Consistent error response format

### Base Configuration
```
Base URL: http://localhost:8000 (development)
API Version: v1
Content-Type: application/json
Documentation: http://localhost:8000/docs
```

---

## Core API Endpoints

### Health and System Endpoints

#### GET /health
**Purpose**: System health check and status  
**Authentication**: None required  

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-06-25T10:30:00Z",
  "services": {
    "database": "healthy",
    "ai_service": "healthy",
    "cache": "healthy"
  },
  "uptime_seconds": 86400
}
```

#### GET /api/v1/info
**Purpose**: API information and capabilities  

**Response**:
```json
{
  "api_version": "1.0.0",
  "supported_formats": ["json"],
  "rate_limits": {
    "requests_per_minute": 100,
    "ai_requests_per_hour": 50
  },
  "features": {
    "picklist_generation": true,
    "team_comparison": true,
    "batch_processing": true,
    "caching": true
  }
}
```

---

### Picklist Generation Endpoints

#### POST /api/v1/picklist/generate
**Purpose**: Generate AI-powered team picklist  
**Authentication**: API key recommended for production  

**Request Body**:
```json
{
  "your_team_number": 1234,
  "pick_position": "first",
  "priorities": [
    {
      "metric": "autonomous_score",
      "weight": 0.3,
      "description": "Autonomous period performance"
    },
    {
      "metric": "teleop_avg_points", 
      "weight": 0.4,
      "description": "Teleoperated average points"
    },
    {
      "metric": "endgame_points",
      "weight": 0.2,
      "description": "Endgame scoring ability"
    },
    {
      "metric": "defense_rating",
      "weight": 0.1,
      "description": "Defensive capability rating"
    }
  ],
  "exclude_teams": [9999, 8888],
  "team_numbers": null,
  "dataset_path": "app/data/unified_dataset.json",
  "options": {
    "use_batch_processing": "auto",
    "include_reasoning": true,
    "max_teams": 100
  }
}
```

**Request Schema Validation**:
```python
class PicklistGenerationRequest(BaseModel):
    your_team_number: int = Field(..., gt=0, description="Your team number")
    pick_position: str = Field(..., regex="^(first|second|third)$")
    priorities: List[PriorityItem] = Field(..., min_items=1, max_items=10)
    exclude_teams: Optional[List[int]] = Field(default=None, description="Teams to exclude")
    team_numbers: Optional[List[int]] = Field(default=None, description="Specific teams to analyze")
    dataset_path: Optional[str] = Field(default=None, description="Custom dataset path")
    options: Optional[PicklistOptions] = Field(default_factory=PicklistOptions)

class PriorityItem(BaseModel):
    metric: str = Field(..., description="Performance metric name")
    weight: float = Field(..., ge=0, le=1, description="Priority weight (0-1)")
    description: Optional[str] = Field(default=None, description="Human-readable description")

class PicklistOptions(BaseModel):
    use_batch_processing: str = Field(default="auto", regex="^(auto|force|never)$")
    include_reasoning: bool = Field(default=True)
    max_teams: int = Field(default=100, ge=1, le=1000)
```

**Success Response (200)**:
```json
{
  "status": "success",
  "data": {
    "ranked_teams": [
      {
        "team_number": 254,
        "rank": 1,
        "score": 92.5,
        "nickname": "The Cheesy Poofs",
        "autonomous_score": 18.5,
        "teleop_avg_points": 55.2,
        "endgame_points": 20.0,
        "defense_rating": 4.8,
        "ai_reasoning": "Exceptional autonomous performance with consistent high scoring in teleop. Strong endgame capabilities make them ideal for first pick.",
        "strengths": ["Autonomous", "Consistency", "Endgame"],
        "concerns": ["None significant"],
        "alliance_fit": "Perfect for aggressive scoring strategy"
      },
      {
        "team_number": 1678,
        "rank": 2,
        "score": 89.1,
        "nickname": "Citrus Circuits",
        "autonomous_score": 16.8,
        "teleop_avg_points": 52.1,
        "endgame_points": 18.5,
        "defense_rating": 3.9,
        "ai_reasoning": "Solid all-around performance with reliable scoring. Good complementary pick for balanced alliance.",
        "strengths": ["Reliability", "Teleop scoring"],
        "concerns": ["Defense could be stronger"],
        "alliance_fit": "Excellent secondary scorer"
      }
    ],
    "summary": "Analysis of 45 teams for first pick position. Team 254 emerges as the clear top choice due to exceptional autonomous performance and consistent high scoring. The top 5 teams all demonstrate strong offensive capabilities suitable for an aggressive alliance strategy.",
    "key_insights": [
      "Top teams excel in autonomous with average scores >15 points",
      "Endgame performance varies significantly across the field",
      "Strong offensive teams available, defense is secondary consideration"
    ],
    "recommended_strategy": "Focus on offensive powerhouses for first two picks, consider defensive specialist for third pick if available.",
    "metadata": {
      "analysis_type": "single_processing",
      "team_count_analyzed": 45,
      "processing_time_seconds": 3.2,
      "ai_model_used": "gpt-4",
      "token_usage": 2450,
      "cost_estimate": 0.12,
      "cached": false,
      "cache_key": "1234_first_a1b2c3d4_none"
    }
  },
  "request_id": "req_abc123def456"
}
```

**Error Responses**:

**400 Bad Request - Invalid Parameters**:
```json
{
  "status": "error",
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "priorities",
    "issue": "Priority weights must sum to between 0.8 and 1.2",
    "received_sum": 0.5
  },
  "request_id": "req_abc123def456"
}
```

**429 Too Many Requests**:
```json
{
  "status": "error", 
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60,
  "request_id": "req_abc123def456"
}
```

**500 Internal Server Error**:
```json
{
  "status": "error",
  "error": "analysis_failed",
  "message": "AI analysis service temporarily unavailable",
  "request_id": "req_abc123def456",
  "support_info": {
    "error_code": "AI_SERVICE_TIMEOUT",
    "timestamp": "2024-06-25T10:30:00Z"
  }
}
```

#### GET /api/v1/picklist/status/{request_id}
**Purpose**: Check status of long-running picklist generation  

**Path Parameters**:
- `request_id`: Unique request identifier from initial generation request

**Response for In-Progress Request**:
```json
{
  "status": "processing",
  "progress": {
    "current_step": "ai_analysis",
    "completion_percentage": 65,
    "estimated_time_remaining": 45,
    "steps_completed": ["data_preparation", "priority_normalization", "team_ranking"],
    "current_step_detail": "Processing batch 3 of 4"
  },
  "request_id": "req_abc123def456"
}
```

**Response for Completed Request**:
```json
{
  "status": "completed",
  "result_available": true,
  "result_url": "/api/v1/picklist/result/req_abc123def456",
  "expires_at": "2024-06-25T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

---

### Team Comparison Endpoints

#### POST /api/v1/teams/compare
**Purpose**: Detailed comparison between specific teams  

**Request Body**:
```json
{
  "team_numbers": [254, 1678, 148],
  "your_team_number": 1234,
  "pick_position": "second",
  "priorities": [
    {"metric": "autonomous_score", "weight": 0.3},
    {"metric": "teleop_avg_points", "weight": 0.4},
    {"metric": "defense_rating", "weight": 0.3}
  ],
  "comparison_type": "detailed",
  "include_statistics": true
}
```

**Success Response (200)**:
```json
{
  "status": "success",
  "data": {
    "comparison_matrix": [
      {
        "team_number": 254,
        "nickname": "The Cheesy Poofs",
        "overall_score": 92.5,
        "strengths": ["Autonomous", "Consistency", "Endgame"],
        "weaknesses": ["Limited defense experience"],
        "vs_other_teams": {
          "1678": {"advantage": "autonomous", "concern": "similar_roles"},
          "148": {"advantage": "consistency", "concern": "none"}
        }
      }
    ],
    "head_to_head": {
      "254_vs_1678": {
        "winner": 254,
        "margin": 3.4,
        "key_differentiator": "autonomous_performance",
        "synergy_rating": 8.5
      },
      "254_vs_148": {
        "winner": 254,
        "margin": 8.2,
        "key_differentiator": "overall_consistency",
        "synergy_rating": 9.1
      },
      "1678_vs_148": {
        "winner": 1678,
        "margin": 4.8,
        "key_differentiator": "teleop_scoring",
        "synergy_rating": 7.8
      }
    },
    "alliance_scenarios": [
      {
        "alliance": [1234, 254, 1678],
        "predicted_score": 185.3,
        "strengths": "Dominant offensive alliance with excellent autonomous",
        "concerns": "Defense may be lacking against strong opponents",
        "recommendation": "Ideal for qualification matches, consider defensive third pick for eliminations"
      }
    ],
    "statistical_summary": {
      "autonomous_range": {"min": 14.2, "max": 18.5, "avg": 16.1},
      "teleop_range": {"min": 48.7, "max": 55.2, "avg": 52.0},
      "consistency_scores": [0.92, 0.88, 0.85]
    }
  },
  "request_id": "req_compare_xyz789"
}
```

#### POST /api/v1/teams/compare/chat
**Purpose**: Interactive Q&A about team comparison  

**Request Body**:
```json
{
  "team_numbers": [254, 1678],
  "question": "Which team would be better for defense in elimination matches?",
  "context": {
    "your_team_number": 1234,
    "pick_position": "third",
    "previous_picks": [254, 1678]
  },
  "conversation_id": "conv_abc123"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "answer": "For defensive roles in elimination matches, Team 1678 would be the better choice despite Team 254's higher overall ranking. Here's why:\n\n1. **Defensive Experience**: Team 1678 has demonstrated effective defensive strategies in 73% of their matches this season\n2. **Robot Design**: Their robot's lower center of gravity and robust drivetrain make them more effective at disrupting opponent scoring\n3. **Strategic Flexibility**: They can transition between offense and defense based on match requirements\n\nTeam 254, while exceptional offensively, is better utilized as a primary scorer rather than in a defensive role.",
    "supporting_data": {
      "1678_defense_stats": {"matches_played_defense": 8, "effectiveness_rating": 4.2},
      "254_defense_stats": {"matches_played_defense": 2, "effectiveness_rating": 3.1},
      "relevant_metrics": ["defense_rating", "drivetrain_robustness", "strategic_flexibility"]
    },
    "conversation_id": "conv_abc123",
    "follow_up_suggestions": [
      "How would this alliance perform against the #1 seed?",
      "What are the weaknesses of this defensive strategy?",
      "Which teams might counter this alliance composition?"
    ]
  },
  "request_id": "req_chat_def456"
}
```

---

### Data Management Endpoints

#### GET /api/v1/datasets
**Purpose**: List available datasets  

**Query Parameters**:
- `year`: Filter by competition year (optional)
- `event_type`: Filter by event type (optional)
- `format`: Response format, default 'json'

**Response**:
```json
{
  "status": "success",
  "data": {
    "datasets": [
      {
        "id": "2024_week1_regional",
        "name": "2024 Week 1 Regional Championship",
        "path": "app/data/2024_week1_regional.json",
        "team_count": 48,
        "last_updated": "2024-03-15T14:30:00Z",
        "format_version": "1.2",
        "data_sources": ["manual_scouting", "statbotics", "tba"],
        "metrics_available": [
          "autonomous_score", "teleop_avg_points", "endgame_points", 
          "defense_rating", "reliability_score", "opr", "dpr", "ccwm"
        ]
      }
    ],
    "total_count": 5,
    "default_dataset": "app/data/unified_dataset.json"
  }
}
```

#### POST /api/v1/datasets/validate
**Purpose**: Validate dataset format and completeness  

**Request Body**:
```json
{
  "dataset_path": "app/data/custom_dataset.json",
  "validation_level": "comprehensive"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "validation_result": {
      "is_valid": true,
      "team_count": 42,
      "required_fields_present": true,
      "missing_fields": [],
      "data_quality_score": 0.94,
      "warnings": [
        "3 teams missing 'defense_rating' field",
        "Team 1234 has unusually high teleop_avg_points (potential outlier)"
      ],
      "recommendations": [
        "Consider adding match_count field for better reliability assessment",
        "Include event_type for context-specific analysis"
      ]
    }
  }
}
```

#### GET /api/v1/teams/{team_number}
**Purpose**: Get detailed information about a specific team  

**Path Parameters**:
- `team_number`: FRC team number

**Query Parameters**:
- `include_history`: Include historical performance data
- `dataset`: Specific dataset to query

**Response**:
```json
{
  "status": "success",
  "data": {
    "team_number": 254,
    "nickname": "The Cheesy Poofs",
    "organization": "NASA Ames Research Center",
    "location": "San Jose, CA, USA",
    "rookie_year": 1999,
    "current_performance": {
      "autonomous_score": 18.5,
      "teleop_avg_points": 55.2,
      "endgame_points": 20.0,
      "defense_rating": 4.8,
      "reliability_score": 0.92,
      "matches_played": 12,
      "wins": 10,
      "losses": 2,
      "ties": 0
    },
    "calculated_metrics": {
      "opr": 65.3,
      "dpr": 8.2,
      "ccwm": 57.1,
      "consistency_rating": 0.91,
      "strategic_flexibility": 4.5
    },
    "strengths": ["Autonomous", "Consistency", "Endgame", "Innovation"],
    "areas_for_improvement": ["Defense coordination"],
    "notable_achievements": [
      "2023 World Championship Winner",
      "Innovation in Control Award 2023"
    ]
  }
}
```

---

### Analysis Utilities Endpoints

#### POST /api/v1/analysis/priorities/suggest
**Purpose**: Get AI-suggested priorities based on competition context  

**Request Body**:
```json
{
  "competition_context": "Regional championship with strong defensive meta",
  "your_team_strengths": ["autonomous", "teleop_scoring"],
  "pick_position": "first",
  "available_metrics": [
    "autonomous_score", "teleop_avg_points", "endgame_points",
    "defense_rating", "reliability_score"
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "suggested_priorities": [
      {
        "metric": "teleop_avg_points",
        "weight": 0.35,
        "reasoning": "Primary scoring metric crucial for strong alliances"
      },
      {
        "metric": "autonomous_score", 
        "weight": 0.25,
        "reasoning": "Autonomous advantage provides early match momentum"
      },
      {
        "metric": "reliability_score",
        "weight": 0.25,
        "reasoning": "Consistency critical in elimination rounds"
      },
      {
        "metric": "defense_rating",
        "weight": 0.15,
        "reasoning": "Defensive capability important in current meta"
      }
    ],
    "strategy_explanation": "For first pick in a defensive meta, prioritize consistent high scorers who can overcome defensive pressure. Reliability becomes crucial as matches get more competitive.",
    "alternative_strategies": [
      {
        "name": "Offensive Focused",
        "priorities": [{"metric": "teleop_avg_points", "weight": 0.5}],
        "when_to_use": "When facing weaker defensive opponents"
      }
    ]
  }
}
```

#### GET /api/v1/analysis/metrics/available
**Purpose**: Get list of available performance metrics with descriptions  

**Response**:
```json
{
  "status": "success",
  "data": {
    "metrics": [
      {
        "metric": "autonomous_score",
        "display_name": "Autonomous Score",
        "description": "Average points scored during autonomous period",
        "data_type": "float",
        "typical_range": [0, 25],
        "higher_is_better": true,
        "category": "offense"
      },
      {
        "metric": "teleop_avg_points",
        "display_name": "Teleop Average Points",
        "description": "Average points scored during teleoperated period",
        "data_type": "float", 
        "typical_range": [10, 80],
        "higher_is_better": true,
        "category": "offense"
      },
      {
        "metric": "defense_rating",
        "display_name": "Defense Rating",
        "description": "Defensive capability rating (1-5 scale)",
        "data_type": "float",
        "typical_range": [1, 5],
        "higher_is_better": true,
        "category": "defense"
      }
    ],
    "categories": ["offense", "defense", "consistency", "endgame", "strategy"]
  }
}
```

---

### Batch Processing Endpoints

#### POST /api/v1/batch/process
**Purpose**: Start batch processing for large datasets  

**Request Body**:
```json
{
  "batch_id": "batch_20240625_001",
  "teams_data": "app/data/large_regional_dataset.json",
  "analysis_parameters": {
    "your_team_number": 1234,
    "pick_position": "first",
    "priorities": [
      {"metric": "autonomous_score", "weight": 0.3},
      {"metric": "teleop_avg_points", "weight": 0.7}
    ]
  },
  "batch_options": {
    "batch_size": 20,
    "max_parallel_batches": 3,
    "timeout_per_batch": 120
  }
}
```

**Response**:
```json
{
  "status": "accepted",
  "data": {
    "batch_id": "batch_20240625_001",
    "estimated_completion_time": "2024-06-25T11:15:00Z",
    "total_teams": 150,
    "total_batches": 8,
    "status_url": "/api/v1/batch/status/batch_20240625_001",
    "result_url": "/api/v1/batch/result/batch_20240625_001"
  },
  "request_id": "req_batch_abc123"
}
```

#### GET /api/v1/batch/status/{batch_id}
**Purpose**: Get status of batch processing job  

**Response**:
```json
{
  "status": "success",
  "data": {
    "batch_id": "batch_20240625_001",
    "status": "processing",
    "progress": {
      "completed_batches": 5,
      "total_batches": 8,
      "completion_percentage": 62.5,
      "current_batch": 6,
      "estimated_time_remaining": 180
    },
    "batch_results": [
      {
        "batch_number": 1,
        "status": "completed",
        "teams_processed": 20,
        "processing_time": 45.2,
        "result_summary": "Batch 1: Top team 2471 (score: 89.3)"
      }
    ],
    "performance_metrics": {
      "avg_time_per_batch": 52.3,
      "total_ai_tokens_used": 15420,
      "estimated_total_cost": 0.85
    }
  }
}
```

---

## Error Handling Standards

### Error Response Format

All error responses follow a consistent format:

```json
{
  "status": "error",
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {
    "field": "specific_field_if_applicable",
    "received_value": "what_was_received",
    "expected_format": "what_was_expected"
  },
  "request_id": "req_unique_identifier",
  "timestamp": "2024-06-25T10:30:00Z",
  "documentation_url": "https://docs.app.com/errors/error_code"
}
```

### HTTP Status Codes

| Status Code | Usage | Description |
|-------------|-------|-------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for async processing |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | External service error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

#### Validation Errors (400)
- `validation_error`: Request validation failed
- `invalid_team_number`: Team number format invalid
- `invalid_priorities`: Priority configuration invalid
- `missing_required_field`: Required field missing
- `invalid_pick_position`: Pick position must be first/second/third

#### Processing Errors (500)
- `ai_service_error`: AI analysis failed
- `data_processing_error`: Data processing failed
- `cache_error`: Cache operation failed
- `database_error`: Database operation failed

#### Rate Limiting (429)
- `rate_limit_exceeded`: Too many requests
- `ai_quota_exceeded`: AI service quota exceeded
- `concurrent_limit_exceeded`: Too many concurrent requests

---

## Authentication and Security

### API Key Authentication

**Development Environment**: No authentication required  
**Production Environment**: API key required for all endpoints except `/health`

**Request Header**:
```
Authorization: Bearer your_api_key_here
```

**Error Response for Missing Auth**:
```json
{
  "status": "error",
  "error": "authentication_required",
  "message": "API key required for this endpoint",
  "request_id": "req_auth_fail_123"
}
```

### Rate Limiting

**Standard Limits**:
- General API: 100 requests per minute per API key
- AI Analysis: 50 requests per hour per API key
- Batch Processing: 5 concurrent batches per API key

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1624636800
X-RateLimit-Type: requests_per_minute
```

---

## API Versioning Strategy

### Version Format
- **URL Versioning**: `/api/v1/endpoint`
- **Header Versioning**: `API-Version: 1.0` (alternative)
- **Semantic Versioning**: Major.Minor.Patch format

### Backward Compatibility
- **Minor versions**: Backward compatible (new features, optional fields)
- **Major versions**: May break compatibility (require migration)
- **Deprecation**: 6-month notice for breaking changes

### Version Migration
```json
{
  "deprecated_version": "v1",
  "current_version": "v2", 
  "migration_guide": "https://docs.app.com/migration/v1-to-v2",
  "deprecation_date": "2024-12-31T23:59:59Z",
  "breaking_changes": [
    "Priority weights now require normalization",
    "Team comparison response format changed"
  ]
}
```

---

## Client Integration Examples

### Python Client
```python
import requests
import json

class FRCScoutingClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def generate_picklist(self, your_team_number, pick_position, priorities):
        """Generate picklist using the API."""
        payload = {
            "your_team_number": your_team_number,
            "pick_position": pick_position,
            "priorities": priorities
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/picklist/generate",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Exception(f"API Error: {response.json()}")

# Usage example
client = FRCScoutingClient()
result = client.generate_picklist(
    your_team_number=1234,
    pick_position="first",
    priorities=[
        {"metric": "autonomous_score", "weight": 0.4},
        {"metric": "teleop_avg_points", "weight": 0.6}
    ]
)
```

### JavaScript/TypeScript Client
```typescript
interface PicklistRequest {
  your_team_number: number;
  pick_position: 'first' | 'second' | 'third';
  priorities: Priority[];
  exclude_teams?: number[];
}

interface Priority {
  metric: string;
  weight: number;
  description?: string;
}

class FRCScoutingAPI {
  constructor(private baseUrl: string = 'http://localhost:8000', private apiKey?: string) {}

  async generatePicklist(request: PicklistRequest): Promise<any> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };
    
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/picklist/generate`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API Error: ${error.message}`);
    }

    const result = await response.json();
    return result.data;
  }
}

// Usage example
const api = new FRCScoutingAPI();
const result = await api.generatePicklist({
  your_team_number: 1234,
  pick_position: 'first',
  priorities: [
    { metric: 'autonomous_score', weight: 0.4 },
    { metric: 'teleop_avg_points', weight: 0.6 }
  ]
});
```

---

## OpenAPI/Swagger Integration

### Live Documentation
- **Interactive Docs**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

### Schema Export
```bash
# Export OpenAPI schema
curl http://localhost:8000/openapi.json > api-schema.json

# Generate client code
openapi-generator generate -i api-schema.json -g python -o ./python-client
openapi-generator generate -i api-schema.json -g typescript-fetch -o ./ts-client
```

---

## Next Steps

### For Frontend Developers
1. **[Frontend Integration Guide](../04_DEVELOPMENT_GUIDES/FRONTEND_INTEGRATION.md)** - React integration patterns
2. **[Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)** - Local development setup
3. **[Testing Guide](../04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md)** - API testing strategies

### For Backend Developers
1. **[Service Architecture](SERVICE_ARCHITECTURE.md)** - Service implementation details
2. **[Database Schema](DATABASE_SCHEMA.md)** - Data model specifications
3. **[Coding Standards](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)** - Development guidelines

### For AI Assistants
1. **[Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md)** - Machine-readable API contracts
2. **[Development Patterns](../05_AI_FRAMEWORK/PROMPT_TEMPLATES.md)** - API development templates
3. **[AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)** - API development with AI assistance

---

**Last Updated**: June 25, 2025  
**Maintainer**: API Team  
**Related Documents**: [Service Architecture](SERVICE_ARCHITECTURE.md), [Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)