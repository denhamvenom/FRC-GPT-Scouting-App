# Service Architecture

**Purpose**: Detailed service design and implementation patterns  
**Audience**: Developers, architects, and AI assistants  
**Scope**: Complete service-oriented architecture documentation  

---

## Service Architecture Overview

The FRC GPT Scouting App implements a **service-oriented architecture** that emphasizes clean separation of concerns, independent development, and AI-friendly patterns. The architecture centers around a lightweight orchestrator that coordinates six specialized services.

### Design Philosophy

**Core Principles**:
- **Single Responsibility**: Each service has one clear, well-defined purpose
- **Loose Coupling**: Services communicate through clean interfaces, not direct dependencies
- **High Cohesion**: Related functionality is grouped within services
- **Testability**: Services can be tested in isolation with mocked dependencies
- **AI Development Ready**: Clear patterns that AI assistants can understand and replicate

### Orchestration Pattern

Unlike traditional monolithic designs or complex microservice meshes, this architecture uses a **lightweight orchestrator pattern**:

```python
# Orchestrator coordinates services without tight coupling
class PicklistGeneratorService:
    def __init__(self, dataset_path: str):
        # Initialize all specialized services
        self.data_service = DataAggregationService(dataset_path)
        self.team_analysis = TeamAnalysisService(self.data_service.get_teams_data())
        self.priority_service = PriorityCalculationService()
        self.performance_service = PerformanceOptimizationService(self._picklist_cache)
        self.batch_service = BatchProcessingService(self._picklist_cache)
        self.gpt_service = PicklistGPTService()
    
    async def generate_picklist(self, ...):
        # Coordinate services to fulfill complex workflows
        teams_data = self.data_service.get_teams_for_analysis(exclude_teams)
        priorities = self.priority_service.normalize_priorities(priorities)
        
        if should_use_batch:
            return await self._orchestrate_batch_processing(...)
        else:
            return await self._orchestrate_single_processing(...)
```

---

## Service Inventory

### 1. DataAggregationService
**Layer**: Data Layer  
**Purpose**: Unified data loading, validation, and preparation  
**File**: `backend/app/services/data_aggregation_service.py`  

#### Responsibilities
- Load and validate datasets from multiple formats (JSON, CSV)
- Aggregate metrics from multiple sources (manual scouting, Statbotics, TBA)
- Filter and prepare data for analysis based on criteria
- Handle data format variations and inconsistencies
- Provide clean, consistent data structure to other services

#### Public Interface
```python
class DataAggregationService:
    def __init__(self, dataset_path: str):
        """Initialize with path to unified dataset file."""
        
    def get_teams_for_analysis(self, exclude_teams: List[int] = None, team_numbers: List[int] = None) -> List[Dict]:
        """Get filtered list of teams ready for analysis."""
        
    def load_game_context(self) -> Optional[str]:
        """Load game-specific context information."""
        
    def validate_dataset(self) -> Dict[str, Any]:
        """Validate dataset completeness and quality."""
        
    def aggregate_team_metrics(self, team_data: Dict) -> Dict:
        """Aggregate and normalize team performance metrics."""
```

#### Key Implementation Details
- **Data Sources**: Supports JSON files, CSV imports, external API data
- **Validation**: Comprehensive data validation with detailed error reporting
- **Normalization**: Consistent field naming across different data sources
- **Filtering**: Flexible team filtering based on various criteria
- **Error Handling**: Graceful handling of missing or malformed data

#### Usage Example
```python
# Initialize service
data_service = DataAggregationService("path/to/unified_dataset.json")

# Get teams for analysis
teams = data_service.get_teams_for_analysis(
    exclude_teams=[1234, 5678],
    team_numbers=None  # All teams
)

# Load competition context
context = data_service.load_game_context()

# Validate data quality
validation_result = data_service.validate_dataset()
if validation_result["status"] == "valid":
    proceed_with_analysis(teams)
```

#### Dependencies
- **Internal**: Logging, configuration management
- **External**: JSON processing, file system access
- **Data Sources**: Dataset files, configuration files

---

### 2. TeamAnalysisService
**Layer**: Analysis Layer  
**Purpose**: Team evaluation, ranking, and comparison algorithms  
**File**: `backend/app/services/team_analysis_service.py`  

#### Responsibilities
- Calculate weighted team scores based on multiple criteria
- Perform similarity analysis between teams for strategic insights
- Select reference teams for batch processing strategies
- Rank teams by various strategic criteria (offense, defense, consistency)
- Generate team comparison matrices and statistical analysis

#### Public Interface
```python
class TeamAnalysisService:
    def __init__(self, teams_data: List[Dict]):
        """Initialize with team performance data."""
        
    def rank_teams_by_score(self, teams: List[Dict], priorities: List[Dict]) -> List[Dict]:
        """Rank teams by weighted priority scores."""
        
    def select_reference_teams(self, teams: List[Dict], count: int, strategy: str = "diverse") -> List[Dict]:
        """Select representative teams for batch processing."""
        
    def calculate_weighted_score(self, team: Dict, priorities: List[Dict]) -> float:
        """Calculate single weighted score for a team."""
        
    def compare_teams(self, team1: Dict, team2: Dict, criteria: List[str]) -> Dict:
        """Detailed comparison between two teams."""
        
    def get_team_statistics(self, teams: List[Dict]) -> Dict[str, Any]:
        """Calculate statistical summary of team performance."""
```

#### Key Algorithms

**Weighted Scoring Algorithm**:
```python
def calculate_weighted_score(self, team: Dict, priorities: List[Dict]) -> float:
    """
    Calculate weighted score using normalized priorities.
    
    Score = Σ(metric_value * priority_weight) for all priorities
    """
    total_score = 0.0
    
    for priority in priorities:
        metric = priority["metric"]
        weight = priority["weight"]
        
        if metric in team:
            # Normalize metric value (0-100 scale)
            normalized_value = self._normalize_metric_value(team[metric], metric)
            total_score += normalized_value * weight
    
    return total_score
```

**Team Selection Strategies**:
- **Diverse**: Select teams with varied strengths and weaknesses
- **Representative**: Select teams that represent different performance tiers
- **Strategic**: Select teams based on alliance complementarity

#### Usage Example
```python
# Initialize with team data
analysis_service = TeamAnalysisService(teams_data)

# Rank teams by priorities
ranked_teams = analysis_service.rank_teams_by_score(
    teams=all_teams,
    priorities=[
        {"metric": "autonomous_score", "weight": 0.3},
        {"metric": "teleop_avg_points", "weight": 0.4},
        {"metric": "endgame_points", "weight": 0.2},
        {"metric": "defense_rating", "weight": 0.1}
    ]
)

# Select reference teams for batch processing
reference_teams = analysis_service.select_reference_teams(
    teams=ranked_teams,
    count=5,
    strategy="diverse"
)
```

#### Dependencies
- **Internal**: Data aggregation service, logging
- **External**: Mathematical libraries, statistical functions
- **Algorithms**: Scoring algorithms, ranking algorithms, similarity metrics

---

### 3. PriorityCalculationService
**Layer**: Analysis Layer  
**Purpose**: Multi-criteria scoring logic and priority management  
**File**: `backend/app/services/priority_calculation_service.py`  

#### Responsibilities
- Normalize priority weights across different metrics
- Validate priority configurations for consistency and completeness
- Calculate context-specific priority adjustments
- Handle priority edge cases and error conditions
- Provide flexible priority weighting schemes for different strategies

#### Public Interface
```python
class PriorityCalculationService:
    def normalize_priorities(self, priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize priority weights to sum to 1.0."""
        
    def validate_priorities(self, priorities: List[Dict]) -> Dict[str, Any]:
        """Validate priority configuration."""
        
    def calculate_context_priorities(self, context: str, base_priorities: List[Dict]) -> List[Dict]:
        """Adjust priorities based on game context."""
        
    def apply_strategic_adjustments(self, priorities: List[Dict], strategy: str) -> List[Dict]:
        """Apply strategic adjustments to priorities."""
        
    def get_priority_description(self, metric: str) -> str:
        """Get human-readable description of a priority metric."""
```

#### Key Implementation Details

**Priority Normalization**:
```python
def normalize_priorities(self, priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize priority weights to ensure they sum to 1.0.
    
    Input: [{"metric": "auto", "weight": 0.3}, {"metric": "teleop", "weight": 0.7}]
    Output: Normalized weights with additional metadata
    """
    if not priorities:
        return []
    
    # Calculate total weight
    total_weight = sum(p.get("weight", 0) for p in priorities)
    if total_weight <= 0:
        logger.warning("Total priority weight is zero or negative")
        return []
    
    # Normalize and add metadata
    normalized_priorities = []
    for priority in priorities:
        weight = priority.get("weight", 0)
        metric = priority.get("metric", "")
        
        if weight > 0 and metric:
            normalized_weight = weight / total_weight
            normalized_priorities.append({
                "metric": metric,
                "weight": normalized_weight,
                "original_weight": weight,
                "description": self._get_priority_description(metric)
            })
    
    return normalized_priorities
```

**Validation Logic**:
- **Weight Validation**: Ensure all weights are positive numbers
- **Metric Validation**: Verify all metrics exist in available data
- **Completeness**: Check for required strategic priorities
- **Consistency**: Ensure priorities align with competition context

#### Usage Example
```python
# Initialize service
priority_service = PriorityCalculationService()

# Normalize user-provided priorities
raw_priorities = [
    {"metric": "autonomous_score", "weight": 3},
    {"metric": "teleop_avg_points", "weight": 4},
    {"metric": "endgame_points", "weight": 2},
    {"metric": "defense_rating", "weight": 1}
]

normalized = priority_service.normalize_priorities(raw_priorities)
# Result: weights sum to 1.0 (0.3, 0.4, 0.2, 0.1)

# Validate priorities
validation_result = priority_service.validate_priorities(normalized)
if validation_result["valid"]:
    proceed_with_analysis(normalized)
```

#### Dependencies
- **Internal**: Logging, configuration
- **External**: Mathematical validation
- **Data**: Metric definitions, validation rules

---

### 4. BatchProcessingService
**Layer**: AI Layer  
**Purpose**: Batch management and progress tracking for large datasets  
**File**: `backend/app/services/batch_processing_service.py`  

#### Responsibilities
- Coordinate batch processing workflows for large datasets (>50 teams)
- Track progress across multiple batches with real-time updates
- Combine and reconcile results from multiple batch operations
- Handle batch failure scenarios and retry logic
- Optimize batch sizes for performance and cost efficiency

#### Public Interface
```python
class BatchProcessingService:
    def __init__(self, cache_manager):
        """Initialize with cache manager for result storage."""
        
    def process_in_batches(self, teams: List[Dict], batch_size: int, callback: Callable) -> Dict:
        """Process teams in batches with progress tracking."""
        
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get current status of batch processing."""
        
    def combine_batch_results(self, results: List[Dict]) -> Dict:
        """Combine results from multiple batches into unified ranking."""
        
    def optimize_batch_strategy(self, team_count: int, constraints: Dict) -> Dict:
        """Determine optimal batching strategy."""
        
    def handle_batch_failure(self, batch_id: str, error: Exception) -> Dict:
        """Handle and potentially retry failed batch."""
```

#### Batch Processing Algorithm

**Intelligent Batching Strategy**:
```python
def optimize_batch_strategy(self, team_count: int, constraints: Dict) -> Dict:
    """
    Determine optimal batch size and strategy based on:
    - Total team count
    - Available processing time
    - Cost constraints
    - Accuracy requirements
    """
    
    # Default batch size calculation
    if team_count <= 20:
        return {"strategy": "single", "batch_size": team_count}
    elif team_count <= 50:
        return {"strategy": "small_batch", "batch_size": 15}
    else:
        # Large dataset - use reference team strategy
        return {
            "strategy": "reference_batch",
            "batch_size": 20,
            "reference_teams": 5,
            "total_batches": math.ceil(team_count / 20)
        }
```

**Progress Tracking**:
```python
class BatchProgress:
    def __init__(self, total_batches: int):
        self.total_batches = total_batches
        self.completed_batches = 0
        self.failed_batches = 0
        self.start_time = datetime.now()
        self.results = []
    
    def update_progress(self, batch_result: Dict):
        """Update progress with completed batch result."""
        self.completed_batches += 1
        self.results.append(batch_result)
        
        # Calculate ETA
        elapsed = datetime.now() - self.start_time
        if self.completed_batches > 0:
            avg_time_per_batch = elapsed / self.completed_batches
            remaining_batches = self.total_batches - self.completed_batches
            eta = avg_time_per_batch * remaining_batches
        
        return {
            "progress": self.completed_batches / self.total_batches,
            "completed": self.completed_batches,
            "total": self.total_batches,
            "eta_seconds": eta.total_seconds() if 'eta' in locals() else None
        }
```

#### Usage Example
```python
# Initialize batch service
batch_service = BatchProcessingService(cache_manager)

# Process large dataset in batches
teams_data = data_service.get_teams_for_analysis()  # 150 teams

# Optimize batching strategy
strategy = batch_service.optimize_batch_strategy(
    team_count=len(teams_data),
    constraints={"max_cost": 10.0, "max_time": 300}
)

# Process in batches
async def analysis_callback(batch_teams, batch_index):
    return await gpt_service.analyze_team_batch(batch_teams)

result = await batch_service.process_in_batches(
    teams=teams_data,
    batch_size=strategy["batch_size"],
    callback=analysis_callback
)
```

#### Dependencies
- **Internal**: Performance optimization service, logging
- **External**: Async processing, progress tracking
- **AI Services**: GPT service for analysis execution

---

### 5. PerformanceOptimizationService
**Layer**: Data Layer  
**Purpose**: Caching, performance monitoring, and optimization  
**File**: `backend/app/services/performance_optimization_service.py`  

#### Responsibilities
- Generate intelligent cache keys for consistent caching across requests
- Manage cached results with TTL and invalidation strategies
- Monitor cache performance and hit rates
- Handle cache invalidation on data updates
- Optimize memory usage and performance metrics

#### Public Interface
```python
class PerformanceOptimizationService:
    def __init__(self, cache_manager):
        """Initialize with cache management system."""
        
    def generate_cache_key(self, your_team_number: int, pick_position: str, 
                          priorities: List[Dict], exclude_teams: List[int] = None) -> str:
        """Generate consistent cache key for picklist parameters."""
        
    def get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached result if available and valid."""
        
    def store_cached_result(self, cache_key: str, result: Dict, ttl: int = 3600) -> bool:
        """Store result in cache with specified TTL."""
        
    def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize memory usage and clean up stale cache entries."""
```

#### Caching Strategy

**Cache Key Generation**:
```python
def generate_cache_key(self, your_team_number: int, pick_position: str, 
                      priorities: List[Dict], exclude_teams: List[int] = None) -> str:
    """
    Generate deterministic cache key from parameters.
    
    Format: team_number_position_priorities_hash_exclude_hash
    Example: "1234_first_a3b2c1d4_e5f6g7h8"
    """
    import hashlib
    import json
    
    # Sort priorities for consistent ordering
    sorted_priorities = sorted(priorities, key=lambda x: x.get("metric", ""))
    priorities_str = json.dumps(sorted_priorities, sort_keys=True)
    priorities_hash = hashlib.md5(priorities_str.encode()).hexdigest()[:8]
    
    # Handle exclude teams
    exclude_str = ""
    if exclude_teams:
        sorted_exclude = sorted(exclude_teams)
        exclude_str = json.dumps(sorted_exclude)
        exclude_hash = hashlib.md5(exclude_str.encode()).hexdigest()[:8]
    else:
        exclude_hash = "none"
    
    return f"{your_team_number}_{pick_position}_{priorities_hash}_{exclude_hash}"
```

**Cache Management**:
- **TTL Strategy**: Different TTL for different types of results
  - Analysis results: 1 hour (data-dependent)
  - Team comparisons: 2 hours (more stable)
  - Statistical summaries: 4 hours (very stable)
- **Invalidation**: Smart invalidation when underlying data changes
- **Memory Management**: LRU eviction with configurable size limits

#### Usage Example
```python
# Initialize performance service
perf_service = PerformanceOptimizationService(cache_manager)

# Generate cache key
cache_key = perf_service.generate_cache_key(
    your_team_number=1234,
    pick_position="first",
    priorities=normalized_priorities,
    exclude_teams=[9999, 8888]
)

# Check for cached result
cached_result = perf_service.get_cached_result(cache_key)
if cached_result:
    return cached_result

# Process and cache result
result = await process_analysis(...)
perf_service.store_cached_result(cache_key, result, ttl=3600)
```

#### Dependencies
- **Internal**: Cache manager, logging, metrics
- **External**: Memory management, TTL tracking
- **Data**: Cache storage, performance metrics

---

### 6. PicklistGPTService
**Layer**: AI Layer  
**Purpose**: OpenAI integration, prompt management, and response parsing  
**File**: `backend/app/services/picklist_gpt_service.py`  

#### Responsibilities
- Create sophisticated system and user prompts for strategic analysis
- Execute API calls to OpenAI with proper error handling and retries
- Parse and validate GPT responses for consistency and accuracy
- Handle API errors, rate limits, and retry logic
- Manage token counting and cost optimization

#### Public Interface
```python
class PicklistGPTService:
    def create_system_prompt(self, pick_position: str, context: str) -> str:
        """Create system prompt for strategic analysis."""
        
    def create_user_prompt(self, your_team_number: int, pick_position: str,
                          priorities: List[Dict], teams_data: List[Dict],
                          team_numbers: List[int], team_index_map: Dict[int, int]) -> str:
        """Create user prompt with team data and analysis requirements."""
        
    def execute_analysis(self, messages: List[Dict]) -> Dict[str, Any]:
        """Execute GPT analysis with error handling and retries."""
        
    def parse_response_with_index_mapping(self, response: str, teams_data: List[Dict],
                                        team_index_map: Dict[int, int]) -> List[Dict]:
        """Parse GPT response and map back to original team data."""
        
    def check_token_count(self, system_prompt: str, user_prompt: str) -> Dict[str, int]:
        """Calculate token count for cost estimation."""
```

#### Prompt Engineering

**System Prompt Strategy**:
```python
def create_system_prompt(self, pick_position: str, context: str) -> str:
    """
    Create system prompt that establishes:
    - Expert FRC strategist persona
    - Analysis requirements and format
    - Strategic considerations for pick position
    - Output format requirements
    """
    return f"""You are an expert FRC (FIRST Robotics Competition) strategist with deep knowledge of team evaluation and alliance selection.

Your task is to analyze teams for {pick_position} pick selection, considering:
- Robot capabilities and consistency
- Strategic alliance fit and synergy
- Match performance and reliability
- Competition context and meta-game

Analysis Context: {context}

Return your analysis in this exact JSON format:
{{
    "ranked_teams": [
        {{"team_number": 1234, "rank": 1, "score": 85.2, "reasoning": "Strong autonomous..."}},
    ],
    "summary": "Comprehensive strategic analysis...",
    "key_insights": ["insight1", "insight2", "insight3"],
    "recommended_strategy": "Detailed recommendation for {pick_position} pick approach"
}}

Focus on actionable strategic insights that help with alliance selection decisions."""
```

**Response Parsing**:
```python
def parse_response_with_index_mapping(self, response: str, teams_data: List[Dict],
                                    team_index_map: Dict[int, int]) -> List[Dict]:
    """
    Parse GPT response and enrich with original team data.
    
    GPT uses index numbers for efficiency, this maps back to team numbers.
    """
    try:
        parsed_response = json.loads(response)
        ranked_teams = parsed_response.get("ranked_teams", [])
        
        # Map index back to team numbers and enrich with data
        enriched_teams = []
        for team_rank in ranked_teams:
            team_index = team_rank.get("team_index", -1)
            if team_index in team_index_map:
                team_number = team_index_map[team_index]
                
                # Find original team data
                original_team = next(
                    (t for t in teams_data if t["team_number"] == team_number),
                    None
                )
                
                if original_team:
                    enriched_team = {
                        **original_team,  # Include all original data
                        "rank": team_rank.get("rank"),
                        "score": team_rank.get("score"),
                        "ai_reasoning": team_rank.get("reasoning", "")
                    }
                    enriched_teams.append(enriched_team)
        
        return {
            "ranked_teams": enriched_teams,
            "summary": parsed_response.get("summary", ""),
            "key_insights": parsed_response.get("key_insights", []),
            "recommended_strategy": parsed_response.get("recommended_strategy", "")
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse GPT response: {e}")
        raise ValueError("Invalid JSON response from GPT")
```

#### Error Handling and Retries
- **Rate Limiting**: Exponential backoff for rate limit errors
- **API Errors**: Retry logic for transient failures
- **Token Limits**: Automatic prompt truncation if needed
- **Response Validation**: Schema validation for all responses

#### Usage Example
```python
# Initialize GPT service
gpt_service = PicklistGPTService()

# Create prompts
system_prompt = gpt_service.create_system_prompt("first", game_context)
user_prompt = gpt_service.create_user_prompt(
    your_team_number=1234,
    pick_position="first",
    priorities=normalized_priorities,
    teams_data=filtered_teams,
    team_numbers=team_numbers,
    team_index_map=index_map
)

# Execute analysis
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

result = await gpt_service.execute_analysis(messages)
ranked_teams = gpt_service.parse_response_with_index_mapping(
    result["response"], teams_data, team_index_map
)
```

#### Dependencies
- **Internal**: Logging, configuration, error handling
- **External**: OpenAI API, token counting, JSON processing
- **AI**: GPT-4 models, prompt templates, response validation

---

## Service Communication Patterns

### Orchestrator Coordination

The **PicklistGeneratorService** serves as the lightweight orchestrator that coordinates all specialized services without creating tight coupling:

```python
class PicklistGeneratorService:
    """
    Main orchestrator that coordinates all specialized services.
    
    Design Principles:
    - Services are initialized once and reused
    - No direct service-to-service communication
    - All coordination flows through orchestrator
    - Clean error handling and logging throughout
    """
    
    async def generate_picklist(self, your_team_number: int, pick_position: str,
                               priorities: List[Dict], exclude_teams: List[int] = None):
        """
        Main workflow orchestration for picklist generation.
        
        Workflow:
        1. Data Preparation (DataAggregationService)
        2. Priority Normalization (PriorityCalculationService)
        3. Cache Check (PerformanceOptimizationService)
        4. Processing Decision (based on dataset size)
        5. Analysis Execution (TeamAnalysisService + PicklistGPTService)
        6. Result Caching and Return
        """
        
        # 1. Data Preparation
        teams_data = self.data_service.get_teams_for_analysis(exclude_teams)
        game_context = self.data_service.load_game_context()
        
        # 2. Priority Processing
        normalized_priorities = self.priority_service.normalize_priorities(priorities)
        validation_result = self.priority_service.validate_priorities(normalized_priorities)
        
        if not validation_result["valid"]:
            raise ValueError(f"Invalid priorities: {validation_result['errors']}")
        
        # 3. Cache Check
        cache_key = self.performance_service.generate_cache_key(
            your_team_number, pick_position, normalized_priorities, exclude_teams
        )
        
        cached_result = self.performance_service.get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for key: {cache_key}")
            return cached_result
        
        # 4. Processing Decision
        if len(teams_data) > 50:
            result = await self._orchestrate_batch_processing(
                teams_data, your_team_number, pick_position, 
                normalized_priorities, game_context
            )
        else:
            result = await self._orchestrate_single_processing(
                teams_data, your_team_number, pick_position,
                normalized_priorities, game_context
            )
        
        # 5. Cache and Return
        self.performance_service.store_cached_result(cache_key, result)
        return result
```

### Error Propagation Strategy

**Graceful Error Handling**:
```python
async def _orchestrate_single_processing(self, teams_data, your_team_number, 
                                       pick_position, priorities, context):
    """
    Single processing workflow with comprehensive error handling.
    """
    try:
        # Team Analysis
        ranked_teams = self.team_analysis.rank_teams_by_score(teams_data, priorities)
        
        # AI Analysis
        ai_result = await self.gpt_service.execute_analysis(
            self._build_analysis_messages(ranked_teams, your_team_number, 
                                        pick_position, priorities, context)
        )
        
        # Combine results
        final_result = self._combine_analysis_results(ranked_teams, ai_result)
        
        return {
            "status": "success",
            "data": final_result,
            "metadata": {
                "processing_type": "single",
                "team_count": len(teams_data),
                "processing_time": time.time() - start_time,
                "cached": False
            }
        }
        
    except OpenAIError as e:
        logger.error(f"AI analysis failed: {e}")
        # Fallback to statistical analysis only
        return self._fallback_statistical_analysis(ranked_teams)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise AnalysisError(f"Failed to generate picklist: {str(e)}")
```

### Data Flow Patterns

**Unidirectional Data Flow**:
```
User Request → API Layer → Orchestrator → Services → Orchestrator → API Layer → User Response

Key Characteristics:
- No circular dependencies between services
- Clear data transformation at each stage
- Comprehensive logging at service boundaries
- Consistent error handling patterns
```

**Service Isolation**:
- Services don't directly import or call other services
- All inter-service communication goes through orchestrator
- Services can be tested independently with mocked inputs
- Clear interface contracts prevent breaking changes

---

## Testing Architecture

### Service Testing Strategy

**Unit Testing Pattern**:
```python
class TestDataAggregationService(unittest.TestCase):
    """Test DataAggregationService in isolation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dataset_path = "tests/fixtures/test_dataset.json"
        self.service = DataAggregationService(self.test_dataset_path)
    
    def test_get_teams_for_analysis_excludes_teams(self):
        """Test team exclusion functionality."""
        exclude_teams = [254, 1678]
        teams = self.service.get_teams_for_analysis(exclude_teams=exclude_teams)
        
        team_numbers = [team["team_number"] for team in teams]
        for excluded_team in exclude_teams:
            self.assertNotIn(excluded_team, team_numbers)
    
    def test_validate_dataset_with_valid_data(self):
        """Test dataset validation with valid data."""
        result = self.service.validate_dataset()
        
        self.assertEqual(result["status"], "valid")
        self.assertGreater(result["team_count"], 0)
        self.assertTrue(result["has_required_fields"])
```

**Integration Testing Pattern**:
```python
class TestServiceIntegration(unittest.TestCase):
    """Test service integration through orchestrator."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.orchestrator = PicklistGeneratorService("tests/fixtures/integration_dataset.json")
    
    @patch('app.services.picklist_gpt_service.PicklistGPTService.execute_analysis')
    async def test_full_picklist_generation_workflow(self, mock_gpt):
        """Test complete workflow integration."""
        # Mock GPT response
        mock_gpt.return_value = {
            "ranked_teams": [{"team_number": 254, "rank": 1, "score": 95.0}],
            "summary": "Test analysis"
        }
        
        # Execute workflow
        result = await self.orchestrator.generate_picklist(
            your_team_number=1234,
            pick_position="first",
            priorities=[{"metric": "autonomous_score", "weight": 1.0}]
        )
        
        # Verify integration
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        self.assertIn("ranked_teams", result["data"])
```

### Performance Testing

**Load Testing Pattern**:
```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestServicePerformance(unittest.TestCase):
    """Test service performance under load."""
    
    async def test_concurrent_analysis_requests(self):
        """Test handling multiple concurrent requests."""
        orchestrator = PicklistGeneratorService("tests/fixtures/large_dataset.json")
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = orchestrator.generate_picklist(
                your_team_number=1000 + i,
                pick_position="first",
                priorities=[{"metric": "autonomous_score", "weight": 1.0}]
            )
            tasks.append(task)
        
        # Execute concurrently and measure
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify performance
        self.assertLess(total_time, 30.0)  # All requests under 30 seconds
        self.assertEqual(len(results), 10)  # All requests succeeded
        
        for result in results:
            self.assertEqual(result["status"], "success")
```

---

## Deployment and Scaling Considerations

### Horizontal Scaling Strategy

**Service Independence**:
- Each service can be scaled independently based on load
- No shared state between service instances
- Stateless design enables easy horizontal scaling

**Container Deployment**:
```yaml
# docker-compose.yml scaling configuration
services:
  orchestrator:
    image: frc-scouting-app:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    environment:
      - SERVICE_MODE=orchestrator
      
  data-service:
    image: frc-scouting-app:latest
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    environment:
      - SERVICE_MODE=data_service
```

### Performance Optimization

**Caching Strategy**:
- **L1 Cache**: In-memory cache within services
- **L2 Cache**: Shared Redis cache for distributed deployment
- **L3 Cache**: Database query result caching

**Resource Optimization**:
- Lazy loading of large datasets
- Connection pooling for external APIs
- Async processing for non-blocking operations
- Batch processing for large datasets

---

## Future Architecture Evolution

### Microservice Migration Path

**Phase 1**: Current monolithic deployment with service-oriented internal architecture
**Phase 2**: Extract services to separate containers with shared database
**Phase 3**: Full microservices with individual databases and message queues
**Phase 4**: Event-driven architecture with saga patterns

### AI Enhancement Opportunities

**Service-Level AI Integration**:
- **DataAggregationService**: AI-powered data validation and anomaly detection
- **TeamAnalysisService**: Machine learning models for performance prediction
- **PriorityCalculationService**: AI-driven priority recommendations
- **PerformanceOptimizationService**: Intelligent caching and resource allocation

**Advanced AI Features**:
- Real-time model fine-tuning based on competition results
- Predictive analytics for alliance success probability
- Natural language query interface for complex analysis requests

---

## Next Steps

### For Developers
1. **[API Contracts](API_CONTRACTS.md)** - Detailed API specifications
2. **[Database Schema](DATABASE_SCHEMA.md)** - Data model documentation
3. **[Development Guides](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)** - Implementation standards

### For AI Assistants
1. **[Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md)** - Machine-readable specifications
2. **[Development Patterns](../05_AI_FRAMEWORK/PROMPT_TEMPLATES.md)** - Service development templates
3. **[AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)** - AI-assisted development patterns

### For Operations
1. **[Deployment Guide](../06_OPERATIONS/DEPLOYMENT_GUIDE.md)** - Production deployment
2. **[Monitoring](../06_OPERATIONS/MONITORING.md)** - Service monitoring strategies
3. **[Performance Optimization](../06_OPERATIONS/PERFORMANCE_OPTIMIZATION.md)** - Scaling and optimization

---

**Last Updated**: June 25, 2025  
**Maintainer**: Architecture Team  
**Related Documents**: [System Architecture](../01_PROJECT_FOUNDATION/ARCHITECTURE.md), [API Contracts](API_CONTRACTS.md), [Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)