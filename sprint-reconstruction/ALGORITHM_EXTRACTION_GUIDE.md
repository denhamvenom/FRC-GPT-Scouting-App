# ALGORITHM EXTRACTION GUIDE

## CRITICAL ALGORITHMS TO EXTRACT FROM ORIGINAL

### 1. RATE LIMITING & RETRY LOGIC
**Location**: Original lines 758-799
**Key Components**:
- Exponential backoff formula: `delay = initial_delay * (2**retry_count)`
- Rate limit detection: `"429" in str(e)`
- Max retries: 3
- Initial delay: 1.0 seconds
- Backoff sequence: 2s, 4s, 8s

**Extract To**: `picklist_gpt_service.py::_execute_api_call_with_retry()`

### 2. TOKEN OPTIMIZATION SYSTEM
**Location**: Original lines 295-323
**Key Components**:
- Token encoder: `tiktoken.encoding_for_model("gpt-4-turbo")`
- Token limit: 100,000 input tokens
- Output limit: 4,000 tokens
- Pre-validation before API calls

**Extract To**: `picklist_gpt_service.py::check_token_count()`

### 3. ULTRA-COMPACT JSON FORMAT
**Location**: Original lines 1489-1502
**Key Components**:
- Format: `{"p":[[team,score,"reason"]...],"s":"ok"}`
- Reasoning limit: ≤10 words
- Overflow detection: `{"s":"overflow"}`
- 75% token reduction vs standard format

**Extract To**: `picklist_gpt_service.py::create_system_prompt()`

### 4. INDEX MAPPING SYSTEM
**Location**: Original lines 689-707, 1536-1562
**Key Components**:
- Threshold: ANY team count (not >30)
- Mapping: `{1: team_number, 2: team_number, ...}`
- Critical warnings in prompt
- Prevents duplicate teams completely

**Extract To**: `picklist_gpt_service.py::create_user_prompt()`

### 5. BATCH DECISION LOGIC
**Location**: Original lines 527-535
**Key Components**:
- Threshold: 20 teams (not manual selection)
- Automatic batching when `len(teams_data) > 20`
- Reference teams: 3 per batch
- Final reranking step

**Extract To**: `picklist_generator_service.py::_determine_processing_strategy()`

### 6. TEAM DATA CONDENSATION
**Location**: Original lines 156-239
**Key Components**:
- Essential fields only
- Metrics averages from scouting data
- Statbotics metrics with prefix
- Superscouting notes limited to 1

**Extract To**: `performance_optimization_service.py::condense_team_data()`

### 7. ERROR RECOVERY SYSTEM
**Location**: Original lines 880-1200+
**Key Components**:
- 4-layer parsing system
- Regex extraction patterns
- Ultra-compact format parsing
- Graceful degradation

**Extract To**: `picklist_gpt_service.py::parse_response_with_recovery()`

### 8. MISSING TEAM DETECTION
**Location**: Original lines 2575-2650
**Key Components**:
- Set difference calculation
- Automatic missing team ranking
- Batch size 20 for missing teams
- Integration with main picklist

**Extract To**: `picklist_generator_service.py::handle_missing_teams()`

### 9. PROGRESS TRACKING WITH THREADING
**Location**: Original lines 736-757
**Key Components**:
- Threading for long API calls
- Real-time progress updates
- Event-based completion detection
- Progress percentage calculation

**Extract To**: `batch_processing_service.py::process_with_progress()`

### 10. CONFIGURATION CONSTANTS
**Critical Values**:
- Temperature: 0.2
- Max output tokens: 4000
- Input token limit: 100000
- Batch size: 20
- Reference teams: 3
- Max retries: 3
- Initial delay: 1.0s
- Processing time estimate: 0.9s per team