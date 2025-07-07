# Team Comparison Service Decomposition Strategy

## Current Architecture Analysis

### Monolithic Service Issues
The current `TeamComparisonService` (415 lines) violates single responsibility principle by handling:
1. **Prompt Generation**: System and user prompt creation
2. **GPT Integration**: OpenAI API communication
3. **Response Parsing**: JSON parsing and validation
4. **Metric Discovery**: Field mapping and extraction
5. **Statistics Processing**: Comparison table generation
6. **Chat Management**: Conversation history handling

### Refactoring Strategy: Service Decomposition

## Target Architecture

### 1. Core TeamComparisonService (Orchestrator)
**Responsibility**: High-level workflow orchestration and public interface
```python
class TeamComparisonService:
    def __init__(self, unified_dataset_path: str) -> None:
        self.data_service = TeamDataService(unified_dataset_path)
        self.prompt_service = ComparisonPromptService()
        self.gpt_service = GPTAnalysisService()
        self.metrics_service = MetricsExtractionService()
    
    async def compare_teams(self, ...) -> Dict[str, Any]:
        # Orchestrate the workflow using composed services
```

### 2. TeamDataService
**Responsibility**: Team data preparation and validation
```python
class TeamDataService:
    def __init__(self, unified_dataset_path: str):
        self.generator = PicklistGeneratorService(unified_dataset_path)
    
    def prepare_teams_data(self, team_numbers: List[int]) -> List[Dict[str, Any]]:
        # Data preparation logic
    
    def validate_team_availability(self, team_numbers: List[int], teams_data: List[Dict]) -> None:
        # Team validation logic
```

### 3. ComparisonPromptService  
**Responsibility**: Prompt generation and message building
```python
class ComparisonPromptService:
    def create_system_prompt(self, pick_position: str, num_teams: int) -> str:
        # System prompt creation
    
    def build_conversation_messages(self, ...) -> List[Dict[str, str]]:
        # Message building for GPT
```

### 4. GPTAnalysisService
**Responsibility**: OpenAI API integration and response handling
```python
class GPTAnalysisService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def get_initial_analysis(self, messages: List[Dict]) -> Dict[str, Any]:
        # Initial JSON analysis
    
    async def get_followup_response(self, messages: List[Dict]) -> str:
        # Follow-up text response
```

### 5. MetricsExtractionService
**Responsibility**: Metric discovery, mapping, and statistics extraction
```python
class MetricsExtractionService:
    def extract_metrics_from_narrative(self, narrative: str, teams_data: List[Dict]) -> List[str]:
        # Narrative analysis
    
    def find_matching_field(self, suggested_metric: str, available_fields: set, teams_data: List[Dict]) -> Optional[str]:
        # Field mapping
    
    def extract_comparison_stats(self, teams_data: List[Dict], suggested_metrics: Optional[List[str]]) -> Dict[str, Any]:
        # Statistics extraction
```

## Implementation Plan

### Phase 1: Create New Service Classes
1. Extract `TeamDataService` first (lowest risk)
2. Extract `ComparisonPromptService` 
3. Extract `GPTAnalysisService`
4. Extract `MetricsExtractionService`

### Phase 2: Refactor Main Service
1. Inject new services into `TeamComparisonService`
2. Replace internal logic with service calls
3. Maintain exact same public interface

### Phase 3: Validation
1. Ensure identical API responses
2. Verify performance unchanged
3. Test error handling preservation

## Detailed Refactoring Steps

### Step 1: TeamDataService Creation
**File**: `backend/app/services/team_data_service.py`
```python
class TeamDataService:
    """Handles team data preparation and validation for comparison."""
    
    def __init__(self, unified_dataset_path: str) -> None:
        self.generator = PicklistGeneratorService(unified_dataset_path)
    
    def prepare_teams_data(self, team_numbers: List[int]) -> Tuple[List[Dict[str, Any]], Dict[int, int]]:
        """Prepare team data and create index mapping."""
        teams_data_all = self.generator._prepare_team_data_for_gpt()
        teams_data = [t for t in teams_data_all if t["team_number"] in team_numbers]
        
        # Validate all teams found
        if len(teams_data) != len(team_numbers):
            found = {t["team_number"] for t in teams_data}
            missing = [n for n in team_numbers if n not in found]
            raise ValueError(f"Teams not found in dataset: {missing}")
        
        # Sort to preserve order and create index mapping
        teams_data.sort(key=lambda t: team_numbers.index(t["team_number"]))
        team_index_map = {i + 1: t["team_number"] for i, t in enumerate(teams_data)}
        
        return teams_data, team_index_map
```

### Step 2: ComparisonPromptService Creation
**File**: `backend/app/services/comparison_prompt_service.py`
```python
class ComparisonPromptService:
    """Handles prompt generation for team comparison analysis."""
    
    def create_system_prompt(self, pick_position: str, num_teams: int) -> str:
        """Create system prompt for team comparison."""
        # Move _create_comparison_system_prompt logic here
    
    def build_conversation_messages(
        self, 
        system_prompt: str,
        teams_data: List[Dict[str, Any]],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        team_numbers: List[int],
        team_index_map: Dict[int, int],
        question: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """Build conversation messages for GPT."""
        # Move message building logic here
```

### Step 3: GPTAnalysisService Creation  
**File**: `backend/app/services/gpt_analysis_service.py`
```python
class GPTAnalysisService:
    """Handles OpenAI GPT integration for team analysis."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def get_initial_analysis(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get initial structured analysis from GPT."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return json.loads(response.choices[0].message.content)
    
    async def get_followup_response(self, messages: List[Dict[str, str]]) -> str:
        """Get follow-up response from GPT."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
```

### Step 4: MetricsExtractionService Creation
**File**: `backend/app/services/metrics_extraction_service.py`
```python
class MetricsExtractionService:
    """Handles metric discovery and statistics extraction."""
    
    def extract_metrics_from_narrative(self, narrative: str, teams_data: List[Dict[str, Any]]) -> List[str]:
        # Move _extract_metrics_from_narrative logic here
    
    def find_matching_field(self, suggested_metric: str, available_fields: set, teams_data: List[Dict[str, Any]]) -> Optional[str]:
        # Move _find_matching_field logic here
    
    def extract_comparison_stats(self, teams_data: List[Dict[str, Any]], suggested_metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        # Move _extract_comparison_stats logic here
```

### Step 5: Refactor Main Service
Update `TeamComparisonService` to use composed services:

```python
class TeamComparisonService:
    """Compare up to three teams and return a ranking and summary."""

    def __init__(self, unified_dataset_path: str) -> None:
        self.data_service = TeamDataService(unified_dataset_path)
        self.prompt_service = ComparisonPromptService()
        self.gpt_service = GPTAnalysisService()
        self.metrics_service = MetricsExtractionService()
        self.generator = PicklistGeneratorService(unified_dataset_path)  # For token checking

    async def compare_teams(
        self,
        team_numbers: List[int],
        your_team_number: int,
        pick_position: str,
        priorities: List[Dict[str, Any]],
        question: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # Input validation
        if not team_numbers or len(team_numbers) < 2:
            raise ValueError("At least two teams must be provided")

        # Prepare team data
        teams_data, team_index_map = self.data_service.prepare_teams_data(team_numbers)

        # Create prompts and messages
        system_prompt = self.prompt_service.create_system_prompt(pick_position, len(teams_data))
        messages = self.prompt_service.build_conversation_messages(
            system_prompt, teams_data, your_team_number, pick_position, 
            priorities, team_numbers, team_index_map, question, chat_history
        )

        # Token count validation (preserve existing behavior)
        total_content = system_prompt + "\n".join([msg["content"] for msg in messages[1:]])
        self.generator._check_token_count(system_prompt, total_content)

        # Get GPT analysis
        if chat_history and question:
            # Follow-up question
            response_text = await self.gpt_service.get_followup_response(messages)
            return {
                "ordered_teams": None,
                "summary": response_text,
                "comparison_data": self.metrics_service.extract_comparison_stats(teams_data),
            }
        else:
            # Initial analysis
            data = await self.gpt_service.get_initial_analysis(messages)
            
            # Process response (preserve existing logic)
            if "ranking" in data:
                # New format processing
                ranking_data = data["ranking"]
                ordered_teams = []
                for rank_item in ranking_data:
                    team_num = rank_item["team_number"]
                    team_data = next((t for t in teams_data if t["team_number"] == team_num), None)
                    if team_data:
                        team_with_ranking = team_data.copy()
                        team_with_ranking["score"] = rank_item.get("score", 0)
                        team_with_ranking["reasoning"] = rank_item.get("brief_reason", "")
                        ordered_teams.append(team_with_ranking)

                # Handle metrics
                suggested_metrics = data.get("key_metrics", [])
                if not suggested_metrics or suggested_metrics == ["rank"]:
                    narrative = data.get("summary", "")
                    suggested_metrics = self.metrics_service.extract_metrics_from_narrative(narrative, teams_data)
                
                return {
                    "ordered_teams": ordered_teams if ordered_teams else teams_data,
                    "summary": data.get("summary", "No detailed analysis provided."),
                    "comparison_data": self.metrics_service.extract_comparison_stats(teams_data, suggested_metrics),
                }
            else:
                # Fallback format
                ordered = self.generator._parse_response_with_index_mapping(data, teams_data, team_index_map)
                return {
                    "ordered_teams": ordered if ordered else teams_data,
                    "summary": data.get("summary", "Analysis completed."),
                    "comparison_data": self.metrics_service.extract_comparison_stats(teams_data),
                }
```

## Risk Mitigation

### Zero-Change Validation
1. **Response Byte Comparison**: Compare API responses before/after
2. **Performance Benchmarking**: Validate <5% degradation
3. **Error Message Preservation**: Same error types and messages
4. **Order Preservation**: Teams ranked in identical order

### Rollback Strategy
1. **Git Branch**: Create feature branch for refactoring
2. **A/B Testing**: Ability to switch between old/new implementations
3. **Emergency Rollback**: Instant revert capability
4. **Progressive Deployment**: Validate each service extraction step

## Success Criteria
- ✅ Identical API responses (byte-perfect)
- ✅ Performance within 5% of baseline
- ✅ All existing tests pass
- ✅ Error handling unchanged
- ✅ Code organization improved
- ✅ Single responsibility principle achieved

This decomposition maintains exact external behavior while improving internal structure and maintainability.