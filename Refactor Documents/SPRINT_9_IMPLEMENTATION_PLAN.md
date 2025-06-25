# Sprint 9 Implementation Plan: Main Orchestrator

**Sprint**: 9 - Final Integration  
**Target**: Complete architectural transformation  
**Risk Level**: Medium  
**Complexity**: Focused - Service coordination  

---

## Implementation Overview

Sprint 9 transforms the original `picklist_generator_service.py` from a 3,113-line monolith into a lightweight orchestrator that coordinates the 6 services created in Sprint 8. This completes the most significant architectural transformation in the project's history.

## Pre-Implementation Validation

### ✅ Sprint 8 Foundation Complete
- **6 Services Implemented**: All decomposed services created and tested
- **Integration Patterns Proven**: Comprehensive test suite validates service coordination
- **API Contracts Defined**: Exact preservation requirements documented
- **Baseline Preserved**: Original service behavior fully captured

### ✅ Ready for Implementation
- **Service Dependencies**: All required services available and functional
- **Test Framework**: Integration test patterns established
- **Documentation**: Complete architectural guidance available
- **Validation Tools**: Baseline comparison tools in place

---

## Implementation Strategy

### Service Orchestration Architecture

```python
class PicklistGeneratorService:
    """
    Main orchestrator that coordinates 6 decomposed services while
    maintaining exact API compatibility with the baseline service.
    
    Orchestrates:
    - DataAggregationService: Data loading and preparation
    - TeamAnalysisService: Team evaluation and ranking
    - PriorityCalculationService: Multi-criteria scoring
    - BatchProcessingService: Batch management and progress
    - PerformanceOptimizationService: Caching and optimization
    - PicklistGPTService: OpenAI integration
    """
```

### Core Coordination Patterns

#### 1. **Service Initialization Pattern**
```python
def __init__(self, unified_dataset_path: str):
    # Primary data service - foundation for others
    self.data_service = DataAggregationService(unified_dataset_path)
    
    # Analysis services - depend on data service
    self.team_analysis = TeamAnalysisService(self.data_service.get_teams_data())
    self.priority_service = PriorityCalculationService()
    
    # Infrastructure services - manage shared state
    self.performance_service = PerformanceOptimizationService(self._picklist_cache)
    self.batch_service = BatchProcessingService(self._picklist_cache)
    
    # External integration service
    self.gpt_service = PicklistGPTService()
    
    # Preserve baseline attributes for compatibility
    self._preserve_baseline_attributes()
```

#### 2. **Main Workflow Coordination**
```python
async def generate_picklist(self, pick_position, priorities, **kwargs):
    # Phase 1: Cache and Performance Management
    cache_key = self.performance_service.generate_cache_key(...)
    cached_result = self.performance_service.get_cached_result(cache_key)
    if cached_result:
        return self._format_cached_response(cached_result)
    
    # Phase 2: Data Preparation
    teams_data = self.data_service.get_teams_for_analysis(...)
    normalized_priorities = self.priority_service.normalize_priorities(priorities)
    
    # Phase 3: Processing Strategy Decision
    if self._should_use_batch_processing(...):
        return await self._coordinate_batch_processing(...)
    else:
        return await self._coordinate_single_processing(...)
```

#### 3. **Batch Processing Coordination**
```python
async def _coordinate_batch_processing(self, ...):
    # Initialize batch processing
    batch_info = self.batch_service.calculate_batch_info(...)
    self.batch_service.initialize_batch_processing(cache_key, batch_info["total_batches"])
    
    # Create batches and reference teams
    team_batches = self.batch_service.create_team_batches(...)
    reference_teams = self.team_analysis.select_reference_teams(...)
    
    # Process batches with coordination
    batch_results = await self.batch_service.process_batches_with_progress(
        cache_key=cache_key,
        batch_processor_func=self._process_single_batch,
        batches=team_batches,
        reference_teams=reference_teams,
        ...
    )
    
    # Combine and finalize results
    combined_results = self.batch_service.combine_batch_results(batch_results)
    return self._finalize_picklist_response(combined_results, cache_key)
```

---

## Detailed Implementation Steps

### Phase 1: Service Infrastructure Setup

#### Step 1.1: Import and Dependency Management
```python
# Import all decomposed services
from app.services.data_aggregation_service import DataAggregationService
from app.services.team_analysis_service import TeamAnalysisService
from app.services.priority_calculation_service import PriorityCalculationService
from app.services.batch_processing_service import BatchProcessingService
from app.services.performance_optimization_service import PerformanceOptimizationService
from app.services.picklist_gpt_service import PicklistGPTService

# Preserve existing dependencies
from app.services.progress_tracker import ProgressTracker
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
```

#### Step 1.2: Class Structure Preservation
```python
class PicklistGeneratorService:
    """Preserve original docstring and class-level cache"""
    
    # CRITICAL: Preserve class-level cache for compatibility
    _picklist_cache = {}
    
    def __init__(self, unified_dataset_path: str):
        """Preserve exact constructor signature"""
        # Initialize orchestrated services
        self._initialize_services(unified_dataset_path)
        
        # Preserve baseline attributes for API compatibility
        self._preserve_baseline_compatibility()
```

#### Step 1.3: Baseline Attribute Preservation
```python
def _preserve_baseline_compatibility(self):
    """Ensure all baseline attributes are available for compatibility"""
    self.dataset_path = self.data_service.dataset_path
    self.dataset = self.data_service.dataset
    self.teams_data = self.data_service.teams_data
    self.year = self.data_service.year
    self.event_key = self.data_service.event_key
    self.game_context = self.data_service.load_game_context()
    self.token_encoder = self.gpt_service.token_encoder
```

### Phase 2: Core Method Orchestration

#### Step 2.1: Main Picklist Generation
```python
async def generate_picklist(
    self,
    your_team_number: int,
    pick_position: str,
    priorities: List[Dict[str, Any]],
    exclude_teams: Optional[List[int]] = None,
    request_id: Optional[int] = None,
    cache_key: Optional[str] = None,
    batch_size: int = 20,
    reference_teams_count: int = 3,
    reference_selection: str = "top_middle_bottom",
    use_batching: bool = False,
    final_rerank: bool = True,
) -> Dict[str, Any]:
    """
    CRITICAL: Preserve exact method signature and behavior
    
    Orchestrates the complete picklist generation workflow using
    the 6 decomposed services while maintaining identical behavior.
    """
    
    # Step 1: Performance and caching
    if not cache_key:
        cache_key = self.performance_service.generate_cache_key(
            your_team_number=your_team_number,
            pick_position=pick_position,
            priorities=priorities,
            exclude_teams=exclude_teams,
            team_count=len(self.teams_data)
        )
    
    # Step 2: Check for existing results
    cached_result = self.performance_service.get_cached_result(cache_key)
    if cached_result and cached_result.get("status") == "success":
        return cached_result
    
    # Step 3: Mark as processing
    self.performance_service.mark_cache_processing(cache_key)
    
    try:
        # Step 4: Data preparation
        teams_data = self.data_service.get_teams_for_analysis(exclude_teams=exclude_teams)
        normalized_priorities = self.priority_service.normalize_priorities(priorities)
        
        # Step 5: Processing decision
        should_batch = self.batch_service.should_use_batching(
            teams_count=len(teams_data),
            batch_size=batch_size,
            use_batching=use_batching
        )
        
        if should_batch:
            result = await self._orchestrate_batch_processing(
                teams_data=teams_data,
                your_team_number=your_team_number,
                pick_position=pick_position,
                normalized_priorities=normalized_priorities,
                cache_key=cache_key,
                batch_size=batch_size,
                reference_teams_count=reference_teams_count,
                reference_selection=reference_selection,
                final_rerank=final_rerank
            )
        else:
            result = await self._orchestrate_single_processing(
                teams_data=teams_data,
                your_team_number=your_team_number,
                pick_position=pick_position,
                normalized_priorities=normalized_priorities,
                cache_key=cache_key
            )
        
        # Step 6: Store and return result
        self.performance_service.store_cached_result(cache_key, result)
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "cache_key": cache_key,
            "processing_time": 0.0
        }
        self.performance_service.store_cached_result(cache_key, error_result)
        return error_result
```

#### Step 2.2: Missing Teams Analysis
```python
async def rank_missing_teams(
    self,
    existing_picklist: List[Dict[str, Any]],
    your_team_number: int,
    pick_position: str,
    priorities: List[Dict[str, Any]],
    exclude_teams: Optional[List[int]] = None,
    request_id: Optional[int] = None,
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    CRITICAL: Preserve exact method signature and behavior
    
    Orchestrates missing teams analysis using the decomposed services.
    """
    
    # Identify missing teams
    existing_team_numbers = {team.get("team_number") for team in existing_picklist}
    all_teams = self.data_service.get_teams_for_analysis(exclude_teams=exclude_teams)
    missing_team_numbers = [
        team["team_number"] for team in all_teams 
        if team["team_number"] not in existing_team_numbers
    ]
    
    if not missing_team_numbers:
        return {
            "status": "success",
            "picklist": [],
            "total_teams": 0,
            "processing_time": 0.0
        }
    
    # Generate analysis using GPT service
    normalized_priorities = self.priority_service.normalize_priorities(priorities)
    
    # Create prompts
    system_prompt = self.gpt_service.create_missing_teams_system_prompt(
        pick_position=pick_position,
        team_count=len(missing_team_numbers)
    )
    
    user_prompt = self.gpt_service.create_missing_teams_user_prompt(
        missing_team_numbers=missing_team_numbers,
        ranked_teams=existing_picklist,
        your_team_number=your_team_number,
        pick_position=pick_position,
        priorities=normalized_priorities,
        teams_data=all_teams
    )
    
    # Execute analysis
    analysis_result = await self.gpt_service.analyze_teams(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        teams_data=all_teams
    )
    
    if analysis_result.get("status") == "success":
        return {
            "status": "success",
            "picklist": analysis_result["picklist"],
            "total_teams": len(analysis_result["picklist"]),
            "processing_time": analysis_result.get("processing_time", 0.0),
            "cache_key": cache_key
        }
    else:
        return {
            "status": "error",
            "error": analysis_result.get("error", "Analysis failed"),
            "cache_key": cache_key,
            "processing_time": analysis_result.get("processing_time", 0.0)
        }
```

#### Step 2.3: Batch Status Delegation
```python
def get_batch_processing_status(self, cache_key: str) -> Dict[str, Any]:
    """
    CRITICAL: Preserve exact method signature and behavior
    
    Delegates to BatchProcessingService while maintaining response format.
    """
    return self.batch_service.get_batch_processing_status(cache_key)
```

#### Step 2.4: Picklist Merging Delegation
```python
def merge_and_update_picklist(
    self,
    existing_picklist: List[Dict[str, Any]],
    new_rankings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    CRITICAL: Preserve exact method signature and behavior
    
    Delegates to TeamAnalysisService for picklist merging logic.
    """
    # Combine the picklists
    combined_teams = existing_picklist + new_rankings
    
    # Remove duplicates (keep highest score)
    seen_teams = {}
    for team in combined_teams:
        team_number = team.get("team_number")
        if team_number not in seen_teams or team.get("score", 0) > seen_teams[team_number].get("score", 0):
            seen_teams[team_number] = team
    
    # Sort by score (highest first)
    merged_picklist = list(seen_teams.values())
    merged_picklist.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return merged_picklist
```

### Phase 3: Service Coordination Helpers

#### Step 3.1: Batch Processing Orchestration
```python
async def _orchestrate_batch_processing(self, **kwargs) -> Dict[str, Any]:
    """Coordinate batch processing across multiple services"""
    
    teams_data = kwargs["teams_data"]
    batch_size = kwargs["batch_size"]
    reference_teams_count = kwargs["reference_teams_count"]
    
    # Calculate batch information
    batch_info = self.batch_service.calculate_batch_info(
        teams_count=len(teams_data),
        batch_size=batch_size
    )
    
    # Initialize batch processing
    self.batch_service.initialize_batch_processing(
        kwargs["cache_key"], 
        batch_info["total_batches"]
    )
    
    # Get reference teams for normalization
    initially_ranked = self.team_analysis.rank_teams_by_score(
        teams_data, kwargs["normalized_priorities"]
    )
    reference_teams = self.team_analysis.select_reference_teams(
        initially_ranked, reference_teams_count, kwargs["reference_selection"]
    )
    
    # Create and process batches
    team_batches = self.batch_service.create_team_batches(teams_data, batch_size)
    
    batch_results = await self.batch_service.process_batches_with_progress(
        cache_key=kwargs["cache_key"],
        batch_processor_func=self._process_single_batch,
        batches=team_batches,
        reference_teams=reference_teams,
        **kwargs
    )
    
    # Combine results
    combined_picklist = self.batch_service.combine_batch_results(
        batch_results, reference_teams_count
    )
    
    # Final reranking if requested
    if kwargs.get("final_rerank", True) and len(combined_picklist) > 10:
        combined_picklist = await self._perform_final_reranking(
            combined_picklist, kwargs
        )
    
    return {
        "status": "success",
        "picklist": combined_picklist,
        "total_teams": len(combined_picklist),
        "cache_key": kwargs["cache_key"],
        "batch_processing": True,
        "batches_processed": len(batch_results)
    }
```

#### Step 3.2: Single Processing Orchestration
```python
async def _orchestrate_single_processing(self, **kwargs) -> Dict[str, Any]:
    """Coordinate single-request processing"""
    
    # Prepare data for GPT analysis
    teams_data = kwargs["teams_data"]
    
    # Create prompts
    system_prompt = self.gpt_service.create_system_prompt(
        pick_position=kwargs["pick_position"],
        team_count=len(teams_data),
        game_context=self.game_context
    )
    
    user_prompt = self.gpt_service.create_user_prompt(
        your_team_number=kwargs["your_team_number"],
        pick_position=kwargs["pick_position"],
        priorities=kwargs["normalized_priorities"],
        teams_data=teams_data
    )
    
    # Execute GPT analysis
    analysis_result = await self.gpt_service.analyze_teams(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        teams_data=teams_data
    )
    
    if analysis_result.get("status") == "success":
        return {
            "status": "success",
            "picklist": analysis_result["picklist"],
            "total_teams": len(analysis_result["picklist"]),
            "processing_time": analysis_result.get("processing_time", 0.0),
            "cache_key": kwargs["cache_key"]
        }
    else:
        return {
            "status": "error",
            "error": analysis_result.get("error", "Analysis failed"),
            "cache_key": kwargs["cache_key"],
            "processing_time": analysis_result.get("processing_time", 0.0)
        }
```

### Phase 4: Validation and Testing Integration

#### Step 4.1: Extend Integration Tests
```python
# Add to test_services_integration.py

class TestOrchestratorIntegration(unittest.TestCase):
    """Test the refactored orchestrator against baseline behavior"""
    
    def test_orchestrator_api_compatibility(self):
        """Verify all public methods maintain exact signatures"""
        
    def test_baseline_behavior_preservation(self):
        """Compare orchestrator outputs against baseline service"""
        
    def test_performance_impact_validation(self):
        """Ensure performance within 5% of baseline"""
        
    def test_service_coordination_patterns(self):
        """Validate all services work together correctly"""
```

#### Step 4.2: Baseline Comparison Framework
```python
def compare_with_baseline(orchestrator_result, baseline_result):
    """Compare orchestrator output with baseline for validation"""
    
    # Compare response structure
    assert set(orchestrator_result.keys()) == set(baseline_result.keys())
    
    # Compare picklist ordering (allow for minor GPT variation)
    if "picklist" in both results:
        assert len(orchestrator_result["picklist"]) == len(baseline_result["picklist"])
        # Validate team numbers and score ranges match
        
    # Compare metadata
    assert orchestrator_result["status"] == baseline_result["status"]
    assert abs(orchestrator_result.get("total_teams", 0) - baseline_result.get("total_teams", 0)) <= 1
```

---

## Risk Mitigation Strategies

### Service Coordination Risks
1. **Service Initialization Order**: Ensure proper dependency initialization
2. **Shared State Management**: Coordinate cache access between services
3. **Error Propagation**: Maintain error handling patterns across services
4. **Performance Overhead**: Minimize service coordination latency

### API Compatibility Risks
1. **Method Signature Changes**: Strict validation against baseline signatures
2. **Response Format Drift**: Automated comparison against baseline responses
3. **Error Handling Changes**: Preserve exact error response formats
4. **Behavioral Regression**: Comprehensive functional testing

### Performance Risks
1. **Service Call Overhead**: Optimize service coordination patterns
2. **Memory Usage Increase**: Monitor and optimize service initialization
3. **Cache Efficiency Loss**: Maintain cache hit rates through proper coordination

---

## Success Validation Checklist

### ✅ Implementation Completion
- [ ] All 5 public methods refactored to use service coordination
- [ ] Service initialization and dependency management implemented
- [ ] Error handling and response formatting preserved
- [ ] Performance optimization patterns maintained

### ✅ API Compatibility Validation
- [ ] Method signatures exactly match baseline service
- [ ] Response formats identical to baseline
- [ ] Error responses match baseline patterns
- [ ] Class-level behavior preserved (cache, constants)

### ✅ Functional Validation
- [ ] Core picklist generation produces equivalent results
- [ ] Missing teams analysis maintains same logic
- [ ] Batch processing coordination works correctly
- [ ] Cache management behaves identically

### ✅ Performance Validation
- [ ] Response times within 5% of baseline
- [ ] Memory usage maintained or improved
- [ ] Cache efficiency preserved or enhanced
- [ ] Batch processing performance maintained

### ✅ Integration Validation
- [ ] All integration tests pass
- [ ] Frontend components work unchanged
- [ ] Existing service dependencies maintained
- [ ] External API integrations preserved

---

This implementation plan provides a comprehensive roadmap for completing the architectural transformation while maintaining the highest standards of quality, safety, and baseline preservation established throughout the refactoring project.