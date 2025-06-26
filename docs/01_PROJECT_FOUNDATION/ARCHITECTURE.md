# System Architecture Overview

**Purpose**: High-level system design and component relationships  
**Audience**: Developers, architects, and AI assistants  
**Scope**: Complete system architecture from frontend to AI integration  

---

## Architecture Philosophy

The FRC GPT Scouting App follows a **service-oriented architecture** that prioritizes:

### Core Principles
- **Clear Separation of Concerns**: Each service has a single, well-defined responsibility
- **Independent Service Development**: Services can be developed, tested, and deployed independently  
- **AI-Assisted Development Workflows**: Architecture designed for Claude Code and AI assistant integration
- **Maintainable, Testable Code**: Clean interfaces and comprehensive testing at all levels
- **Scalable Performance**: Efficient caching, batch processing, and optimization
- **Strategic AI Integration**: GPT-4 analysis woven throughout the decision-making process

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   Web Browser   │    │  Mobile Device  │    │   API Client    │ │
│  │   (React/TS)    │    │   (Future)      │    │  (External)     │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API GATEWAY                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              FastAPI Backend (Python 3.11)                 │ │
│  │  • Authentication & Authorization                          │ │
│  │  • Request Validation & Rate Limiting                      │ │
│  │  • Response Formatting & Error Handling                    │ │
│  │  • API Documentation (OpenAPI/Swagger)                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR SERVICE                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           PicklistGeneratorService (Main)                  │ │
│  │  • Coordinates all specialized services                    │ │
│  │  • Manages workflow orchestration                          │ │
│  │  • Handles caching and performance optimization            │ │
│  │  • Provides unified interface to API layer                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  DATA LAYER     │    │ ANALYSIS LAYER  │    │   AI LAYER      │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │    Data     │ │    │ │    Team     │ │    │ │  Picklist   │ │
│ │ Aggregation │ │    │ │  Analysis   │ │    │ │    GPT      │ │
│ │   Service   │ │    │ │   Service   │ │    │ │   Service   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Performance │ │    │ │   Priority  │ │    │ │    Batch    │ │
│ │Optimization │ │    │ │ Calculation │ │    │ │ Processing  │ │
│ │   Service   │ │    │ │   Service   │ │    │ │   Service   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA STORAGE                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   SQLite    │  │    JSON     │  │    Cache    │  │   Logs      │ │
│  │  Database   │  │    Files    │  │  (Memory)   │  │   Files     │ │
│  │             │  │             │  │             │  │             │ │
│  │ • Teams     │  │ • Scouting  │  │ • Results   │  │ • Debug     │ │
│  │ • Matches   │  │ • Config    │  │ • Sessions  │  │ • Audit     │ │
│  │ • Events    │  │ • Context   │  │ • Metrics   │  │ • Error     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Architecture Detail

### Service Orchestration Pattern

The application uses a **lightweight orchestrator pattern** where the main `PicklistGeneratorService` coordinates specialized services without tight coupling.

#### Design Benefits
- **Independent Testing**: Each service can be tested in isolation
- **Clear Responsibilities**: No confusion about which service handles what
- **Flexible Scaling**: Services can be optimized or replaced independently
- **AI Development Friendly**: Clear boundaries for AI assistants to understand and modify

### Service Inventory

#### 1. DataAggregationService
**Purpose**: Unified data loading and preparation  
**Layer**: Data Layer  

**Responsibilities**:
- Load and validate datasets from multiple formats (JSON, CSV)
- Aggregate metrics from multiple sources (manual scouting, Statbotics, TBA)
- Filter and prepare data for analysis based on criteria
- Handle data format variations and inconsistencies
- Provide clean, consistent data structure to other services

**Key Interfaces**:
```python
def get_teams_for_analysis(exclude_teams: List[int] = None) -> List[Dict]
def load_game_context() -> Optional[str]
def validate_dataset() -> Dict[str, Any]
def aggregate_team_metrics(team_data: Dict) -> Dict
```

**Dependencies**: File system, JSON processing, logging  
**Data Sources**: JSON files, CSV imports, external APIs  

#### 2. TeamAnalysisService
**Purpose**: Team evaluation and ranking algorithms  
**Layer**: Analysis Layer  

**Responsibilities**:
- Calculate weighted team scores based on multiple criteria
- Perform similarity analysis between teams
- Select reference teams for batch processing strategies
- Rank teams by various strategic criteria
- Generate team comparison matrices

**Key Interfaces**:
```python
def rank_teams_by_score(teams: List[Dict], priorities: List[Dict]) -> List[Dict]
def select_reference_teams(teams: List[Dict], count: int, strategy: str) -> List[Dict]
def calculate_weighted_score(team: Dict, priorities: List[Dict]) -> float
def compare_teams(team1: Dict, team2: Dict, criteria: List[str]) -> Dict
```

**Dependencies**: Mathematical libraries, data aggregation service  
**Algorithms**: Weighted scoring, similarity metrics, ranking algorithms  

#### 3. PriorityCalculationService
**Purpose**: Multi-criteria scoring logic  
**Layer**: Analysis Layer  

**Responsibilities**:
- Normalize priority weights across different metrics
- Validate priority configurations for consistency
- Calculate context-specific priority adjustments
- Handle priority edge cases and error conditions
- Provide flexible priority weighting schemes

**Key Interfaces**:
```python
def normalize_priorities(priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]
def validate_priorities(priorities: List[Dict]) -> Dict[str, Any]
def calculate_context_priorities(context: str, base_priorities: List[Dict]) -> List[Dict]
def apply_strategic_adjustments(priorities: List[Dict], strategy: str) -> List[Dict]
```

**Dependencies**: Mathematical validation, logging  
**Algorithms**: Normalization, validation, weight distribution  

#### 4. BatchProcessingService
**Purpose**: Batch management and progress tracking  
**Layer**: AI Layer  

**Responsibilities**:
- Coordinate batch processing workflows for large datasets
- Track progress across multiple batches with real-time updates
- Combine and reconcile results from multiple batch operations
- Handle batch failure scenarios and retry logic
- Optimize batch sizes for performance and cost

**Key Interfaces**:
```python
def process_in_batches(teams: List[Dict], batch_size: int, callback: Callable) -> Dict
def get_batch_status(batch_id: str) -> Dict[str, Any]
def combine_batch_results(results: List[Dict]) -> Dict
def optimize_batch_strategy(team_count: int, constraints: Dict) -> Dict
```

**Dependencies**: Async processing, progress tracking, orchestrator  
**Patterns**: Producer-consumer, progress callbacks, error recovery  

#### 5. PerformanceOptimizationService
**Purpose**: Caching and performance management  
**Layer**: Data Layer  

**Responsibilities**:
- Generate intelligent cache keys for consistent caching
- Manage cached results with TTL and invalidation strategies
- Monitor cache performance and hit rates
- Handle cache invalidation on data updates
- Optimize memory usage and performance metrics

**Key Interfaces**:
```python
def generate_cache_key(params: Dict) -> str
def get_cached_result(key: str) -> Optional[Dict]
def store_cached_result(key: str, result: Dict, ttl: int = None) -> bool
def invalidate_cache_pattern(pattern: str) -> int
def get_cache_metrics() -> Dict[str, Any]
```

**Dependencies**: Memory management, hashing, performance monitoring  
**Patterns**: Cache-aside, write-through, TTL management  

#### 6. PicklistGPTService
**Purpose**: OpenAI integration and prompt management  
**Layer**: AI Layer  

**Responsibilities**:
- Create sophisticated system and user prompts for analysis
- Execute API calls to OpenAI with proper error handling
- Parse and validate GPT responses for consistency
- Handle API errors, rate limits, and retry logic
- Manage token counting and cost optimization

**Key Interfaces**:
```python
def create_system_prompt(pick_position: str, context: str) -> str
def create_user_prompt(team_data: List[Dict], priorities: List[Dict]) -> str
def execute_analysis(messages: List[Dict]) -> Dict[str, Any]
def parse_response_with_index_mapping(response: str, teams: List[Dict]) -> List[Dict]
def check_token_count(prompt: str) -> Dict[str, int]
```

**Dependencies**: OpenAI API, JSON processing, error handling  
**Patterns**: Retry logic, exponential backoff, token management  

---

## Data Flow Architecture

### Standard Picklist Generation Flow

```
1. API Request
   ├── FastAPI endpoint receives request
   ├── Input validation and authentication
   └── Route to PicklistGeneratorService.generate_picklist()

2. Data Preparation
   ├── DataAggregationService.get_teams_for_analysis()
   ├── Load competition context and game rules
   ├── Filter teams based on exclusion criteria
   └── Validate data completeness and quality

3. Analysis Configuration  
   ├── PriorityCalculationService.normalize_priorities()
   ├── Validate strategic priorities and weights
   ├── Calculate context-specific adjustments
   └── Prepare analysis parameters

4. Processing Decision
   ├── Check dataset size and complexity
   ├── Determine if batch processing is needed
   ├── PerformanceOptimizationService.check_cache()
   └── Route to appropriate processing strategy

5A. Single Processing (< 50 teams)
    ├── TeamAnalysisService.rank_teams_by_score()
    ├── PicklistGPTService.execute_analysis()
    ├── Parse and validate AI response
    └── Format results for return

5B. Batch Processing (> 50 teams)
    ├── TeamAnalysisService.select_reference_teams()
    ├── BatchProcessingService.process_in_batches()
    ├── Multiple PicklistGPTService calls
    ├── Combine and reconcile batch results
    └── Generate final unified ranking

6. Result Processing
   ├── PerformanceOptimizationService.store_cached_result()
   ├── Format response for API consumption
   ├── Log performance metrics and usage
   └── Return structured response to client

7. Frontend Integration
   ├── Display ranked team list with reasoning
   ├── Provide interactive analysis tools
   ├── Enable follow-up questions and refinement
   └── Export results for strategic planning
```

### Team Comparison Flow

```
1. Comparison Request
   ├── User selects teams for detailed comparison
   ├── API validates team selection and access
   └── Route to comparison-specific workflow

2. Data Enrichment
   ├── DataAggregationService gathers detailed team data
   ├── Include historical performance and context
   ├── Add competition-specific considerations
   └── Prepare comprehensive team profiles

3. AI Analysis
   ├── PicklistGPTService creates comparison prompts
   ├── Execute detailed comparative analysis
   ├── Generate strategic insights and recommendations
   └── Parse structured comparison results

4. Interactive Enhancement
   ├── Support follow-up questions and refinement
   ├── Enable deep-dive analysis on specific aspects
   ├── Provide visual comparisons and charts
   └── Export detailed comparison reports
```

---

## Technology Stack Architecture

### Frontend Architecture (React + TypeScript)
```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Pages     │  │ Components  │  │   Layouts   │        │
│  │             │  │             │  │             │        │
│  │ • Dashboard │  │ • TeamCard  │  │ • Header    │        │
│  │ • Analysis  │  │ • Charts    │  │ • Sidebar   │        │
│  │ • Compare   │  │ • Tables    │  │ • Footer    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   React     │  │   Context   │  │   Hooks     │        │
│  │   State     │  │    API      │  │   Custom    │        │
│  │             │  │             │  │             │        │
│  │ • Local     │  │ • Global    │  │ • useAPI    │        │
│  │ • Forms     │  │ • Auth      │  │ • useCache  │        │
│  │ • Cache     │  │ • Theme     │  │ • useAsync  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   API       │  │   Utils     │  │   Types     │        │
│  │  Service    │  │             │  │             │        │
│  │             │  │ • Helpers   │  │ • Interfaces│        │
│  │ • REST      │  │ • Format    │  │ • Models    │        │
│  │ • WebSocket │  │ • Validate  │  │ • Enums     │        │
│  │ • Cache     │  │ • Transform │  │ • Constants │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Backend Architecture (Python + FastAPI)
```
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Endpoints  │  │ Middleware  │  │ Validation  │        │
│  │             │  │             │  │             │        │
│  │ • Picklist  │  │ • CORS      │  │ • Pydantic  │        │
│  │ • Compare   │  │ • Auth      │  │ • Schema    │        │
│  │ • Health    │  │ • Logging   │  │ • Types     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Orchestrator│  │  Services   │  │   Utils     │        │
│  │             │  │             │  │             │        │
│  │ • Main      │  │ • 6 Specialized│ • Config    │        │
│  │ • Workflow  │  │   Services  │  │ • Helpers   │        │
│  │ • Coord     │  │ • Clean API │  │ • Constants │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Database   │  │    Files    │  │   Cache     │        │
│  │             │  │             │  │             │        │
│  │ • SQLite    │  │ • JSON      │  │ • Memory    │        │
│  │ • Models    │  │ • CSV       │  │ • Redis     │        │
│  │ • Queries   │  │ • Config    │  │ • TTL       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development Environment
```
┌─────────────────────────────────────────────────────────────┐
│                  DEVELOPER MACHINE                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Frontend   │  │   Backend   │  │  Database   │        │
│  │   (Node)    │  │  (Python)   │  │  (SQLite)   │        │
│  │             │  │             │  │             │        │
│  │ Port: 3000  │  │ Port: 8000  │  │ File: Local │        │
│  │ Hot Reload  │  │ Auto Reload │  │ Development │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Docker Containerized
```
┌─────────────────────────────────────────────────────────────┐
│                   DOCKER COMPOSE                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Frontend   │  │   Backend   │  │   Nginx     │        │
│  │ Container   │  │ Container   │  │ Container   │        │
│  │             │  │             │  │             │        │
│  │ React Build │  │ FastAPI     │  │ Reverse     │        │
│  │ Nginx Serve │  │ Production  │  │ Proxy       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │  Database   │  │   Redis     │                        │
│  │ Container   │  │ Container   │                        │
│  │             │  │             │                        │
│  │ PostgreSQL  │  │ Cache Layer │                        │
│  │ Production  │  │ Sessions    │                        │
│  └─────────────┘  └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication & Authorization
- **API Keys**: OpenAI API key management with environment variables
- **Rate Limiting**: Request throttling to prevent abuse
- **Input Validation**: Comprehensive input sanitization and validation
- **CORS**: Properly configured cross-origin resource sharing

### Data Protection
- **Sensitive Data**: No persistent storage of sensitive scouting data
- **API Security**: HTTPS enforcement in production
- **Database Security**: Parameterized queries to prevent injection
- **Logging**: Audit trails without sensitive information exposure

---

## Performance Architecture

### Caching Strategy
- **Memory Cache**: Fast access to frequently requested data
- **Result Cache**: Expensive AI analysis results cached with TTL
- **Query Cache**: Database query optimization and caching
- **Static Asset Cache**: Frontend assets cached at CDN level

### Optimization Patterns
- **Lazy Loading**: Load data only when needed
- **Batch Processing**: Efficient handling of large datasets
- **Connection Pooling**: Efficient database and API connections
- **Async Processing**: Non-blocking operations where possible

---

## Monitoring & Observability

### Application Metrics
- **Response Times**: API endpoint performance monitoring
- **Error Rates**: Exception tracking and alerting
- **Cache Hit Rates**: Cache performance optimization
- **Resource Usage**: Memory, CPU, and disk utilization

### Business Metrics
- **Analysis Success Rate**: Successful picklist generations
- **User Engagement**: Feature usage and adoption
- **AI Performance**: GPT response quality and consistency
- **Data Quality**: Dataset validation and completeness

---

**Next Steps**: [Service Architecture Details](SERVICE_ARCHITECTURE.md) | [API Contracts](API_CONTRACTS.md) | [Development Setup](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)

---
**Last Updated**: June 25, 2025  
**Maintainer**: Architecture Team  
**Related Documents**: [README.md](../../README.md), [Getting Started](GETTING_STARTED.md), [Technology Stack](TECHNOLOGY_STACK.md)