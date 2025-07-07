# SPRINT EXECUTION PLAN - PICKLIST RECONSTRUCTION

## 🎯 MISSION CRITICAL SUCCESS CRITERIA
- Process 55+ teams in single request without rate limiting
- Return all teams without duplicates  
- Maintain sub-200ms API response times
- Preserve all refactored architectural benefits

---

## 📋 PHASE 1: FOUNDATION RESTORATION (Estimated: 1.5 hours)

### Task 1.1: Restore Core GPT Service Algorithms
**File**: `backend/app/services/picklist_gpt_service.py`
**Estimated Time**: 45 minutes

#### Step 1.1.1: Restore Ultra-Compact JSON System
```python
def create_system_prompt(self, pick_position: str, team_count: int, game_context: Optional[str] = None, use_ultra_compact: bool = True) -> str:
    """RESTORE EXACT ORIGINAL FORMAT"""
    
    position_context = {
        "first": "First pick teams should be overall powerhouse teams that excel in multiple areas.",
        "second": "Second pick teams should complement the first pick and address specific needs.", 
        "third": "Third pick teams are more specialized, often focusing on a single critical function.",
    }
    
    context_note = position_context.get(pick_position, "")
    
    if use_ultra_compact:
        # ORIGINAL ULTRA-COMPACT FORMAT - CRITICAL FOR TOKEN OPTIMIZATION
        return f"""You are GPT‑4.1, an FRC alliance strategist.
Return one‑line minified JSON:
{{"p":[[index,score,"reason"]…],"s":"ok"}}

CRITICAL RULES
• Rank all {team_count} indices, each exactly once.  
• Use indices 1-{team_count} from TEAM_INDEX_MAP exactly once.
• Sort by weighted performance, then synergy with Team {{your_team_number}} for {pick_position} pick.  
• Each reason must be ≤10 words, NO REPETITION, cite 1 metric (e.g. "Strong auto: 3.2 avg").
• NO repetitive words or phrases. Be concise and specific.
• If you cannot complete all teams due to length limits, respond only {{"s":"overflow"}}.

{context_note}

EXAMPLE: {{"p":[[1,8.5,"Strong auto: 2.8 avg"],[2,7.9,"Consistent defense"],[3,6.2,"Reliable endgame"]],"s":"ok"}}"""
    else:
        # Fallback format for smaller requests
        return self._create_standard_format_prompt(pick_position, team_count, game_context)
```

#### Step 1.1.2: Restore Token Counting System
```python
def check_token_count(self, system_prompt: str, user_prompt: str, max_tokens: int = 100000) -> None:
    """EXACT RESTORATION OF ORIGINAL TOKEN VALIDATION"""
    try:
        system_tokens = len(self.token_encoder.encode(system_prompt))
        user_tokens = len(self.token_encoder.encode(user_prompt))
        total_tokens = system_tokens + user_tokens
        
        logger.info(f"Token count: system={system_tokens}, user={user_tokens}, total={total_tokens}")
        
        if total_tokens > max_tokens:
            raise ValueError(
                f"Prompt too large: {total_tokens} tokens exceeds limit of {max_tokens}. Consider batching teams or trimming fields."
            )
    except Exception as e:
        logger.warning(f"Token counting failed: {str(e)}, proceeding without check")
```

#### Step 1.1.3: Restore Exponential Backoff Retry System
```python
async def _execute_api_call_with_retry(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """EXACT RESTORATION OF ORIGINAL RETRY LOGIC"""
    max_retries = 3
    initial_delay = 1.0
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "length":
                return {
                    "status": "error",
                    "error": "Response truncated due to length",
                    "error_type": "response_truncated"
                }
            
            # Parse JSON response
            response_data = json.loads(content)
            
            # Check for overflow status
            if response_data.get("s") == "overflow" or response_data.get("status") == "overflow":
                return {
                    "status": "error", 
                    "error": "GPT indicated data overflow",
                    "error_type": "data_overflow"
                }
            
            return {
                "status": "success",
                "response_data": response_data,
                "finish_reason": finish_reason,
            }
            
        except Exception as e:
            # CRITICAL: Check if it's a rate limit error
            is_rate_limit = "429" in str(e)
            
            if is_rate_limit and retry_count < max_retries:
                retry_count += 1
                delay = initial_delay * (2**retry_count)  # Exponential backoff
                
                logger.warning(
                    f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retry_count}/{max_retries})"
                )
                await asyncio.sleep(delay)
            else:
                return {
                    "status": "error",
                    "error": f"API call failed: {str(e)}",
                    "error_type": "rate_limit" if is_rate_limit else "api_error"
                }
    
    return {
        "status": "error",
        "error": f"Failed after {max_retries} retries",
        "error_type": "max_retries_exceeded"
    }
```

### Task 1.2: Restore Advanced User Prompt Creation
**Estimated Time**: 30 minutes

#### Step 1.2.1: Restore Index Mapping for ALL Requests
```python
def create_user_prompt(
    self,
    your_team_number: int,
    pick_position: str,
    priorities: List[Dict[str, Any]],
    teams_data: List[Dict[str, Any]],
    team_numbers: Optional[List[int]] = None,
    force_index_mapping: bool = True  # CHANGED: Force for all requests
) -> Tuple[str, Optional[Dict[int, int]]]:
    """RESTORE ORIGINAL USER PROMPT WITH FORCED INDEX MAPPING"""
    
    # CRITICAL: Always create index mapping for consistency
    team_index_map = {}
    for index, team in enumerate(teams_data, start=1):
        team_index_map[index] = team["team_number"]
    
    # Find your team's data
    your_team_info = next(
        (team for team in teams_data if team["team_number"] == your_team_number),
        None,
    )
    
    # EXACT RESTORATION OF ORIGINAL WARNING SYSTEM
    team_index_info = f"""
TEAM_INDEX_MAP = {json.dumps(team_index_map)}
⚠️ CRITICAL: Use indices 1 through {len(team_index_map)} from TEAM_INDEX_MAP exactly once.
⚠️ Your response MUST use indices, NOT team numbers: [[1,score,"reason"],[2,score,"reason"]...]
⚠️ Each index from 1 to {len(team_index_map)} must appear EXACTLY ONCE.
"""

    # RESTORE ORIGINAL CONDENSED FORMAT
    prompt = f"""YOUR_TEAM_PROFILE = {json.dumps(your_team_info) if your_team_info else "{}"} 
PRIORITY_METRICS  = {json.dumps(priorities)}   # include weight field
GAME_CONTEXT      = {json.dumps(self.game_context) if hasattr(self, 'game_context') and self.game_context else "null"}
TEAM_NUMBERS_TO_INCLUDE = {json.dumps(team_numbers)}{team_index_info}
AVAILABLE_TEAMS = {json.dumps(self._prepare_condensed_teams_data(teams_data, team_index_map))}     # include pre‑computed weighted_score

Please produce output following RULES.
"""
    
    return prompt, team_index_map
```

### Task 1.3: Restore Error Recovery System  
**Estimated Time**: 15 minutes

#### Step 1.3.1: Implement 4-Layer Error Recovery
```python
def parse_response_with_recovery(
    self,
    response_data: Dict[str, Any],
    raw_content: str,
    teams_data: List[Dict[str, Any]],
    team_index_map: Optional[Dict[int, int]] = None,
) -> List[Dict[str, Any]]:
    """EXACT RESTORATION OF ORIGINAL 4-LAYER RECOVERY SYSTEM"""
    
    # Layer 1: Ultra-compact format parsing
    if "p" in response_data and isinstance(response_data["p"], list):
        return self._parse_ultra_compact_format(response_data, teams_data, team_index_map)
    
    # Layer 2: Standard compact format parsing
    if "picklist" in response_data:
        return self._parse_standard_format(response_data, teams_data, team_index_map)
    
    # Layer 3: Regex extraction from malformed JSON
    logger.warning("Attempting regex extraction from malformed response")
    return self._regex_extract_teams(raw_content, teams_data, team_index_map)
    
    # Layer 4: Empty response (complete failure)
    logger.error("All parsing methods failed, returning empty picklist")
    return []

def _regex_extract_teams(self, content: str, teams_data: List[Dict[str, Any]], team_index_map: Optional[Dict[int, int]] = None) -> List[Dict[str, Any]]:
    """RESTORE ORIGINAL REGEX EXTRACTION PATTERNS"""
    import re
    
    # Pattern for ultra-compact format: [index, score, "reason"]
    compact_pattern = r'\[\s*(\d+)\s*,\s*([\d\.]+)\s*,\s*"([^"]*)"\s*\]'
    matches = re.findall(compact_pattern, content)
    
    picklist = []
    seen_teams = set()
    
    for match in matches:
        try:
            index_or_team = int(match[0])
            score = float(match[1])
            reason = match[2]
            
            # Convert index to team number if mapping provided
            if team_index_map and index_or_team in team_index_map:
                team_number = team_index_map[index_or_team]
            else:
                team_number = index_or_team
            
            if team_number not in seen_teams:
                seen_teams.add(team_number)
                
                # Get team data
                team_data = next(
                    (t for t in teams_data if t.get("team_number") == team_number), None
                )
                nickname = team_data.get("nickname", f"Team {team_number}") if team_data else f"Team {team_number}"
                
                picklist.append({
                    "team_number": team_number,
                    "nickname": nickname,
                    "score": score,
                    "reasoning": reason,
                })
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse regex match {match}: {e}")
            continue
    
    return sorted(picklist, key=lambda x: x["score"], reverse=True)
```

---

## 📋 PHASE 2: PROCESSING STRATEGY RESTORATION (Estimated: 1 hour)

### Task 2.1: Restore Automatic Batching Logic
**File**: `backend/app/services/picklist_generator_service.py`
**Estimated Time**: 30 minutes

#### Step 2.1.1: Implement Original Decision Logic
```python
def _determine_processing_strategy(self, teams_data: List[Dict[str, Any]], use_batching: Optional[bool] = None) -> Tuple[bool, str]:
    """RESTORE ORIGINAL AUTOMATIC BATCHING DECISION"""
    
    team_count = len(teams_data)
    
    # ORIGINAL LOGIC: Automatic batching for >20 teams
    if use_batching is None:
        # Auto-decide based on team count (ORIGINAL THRESHOLD)
        should_batch = team_count > 20
        reason = f"Auto-selected {'batching' if should_batch else 'single'} for {team_count} teams (threshold: 20)"
    else:
        # Respect explicit user choice
        should_batch = use_batching
        reason = f"User-specified {'batching' if should_batch else 'single'} for {team_count} teams"
    
    logger.info(f"Processing strategy: {reason}")
    return should_batch, reason

def _calculate_optimal_batch_size(self, team_count: int, priorities_count: int) -> int:
    """RESTORE ORIGINAL BATCH SIZE CALCULATION"""
    
    # ORIGINAL CONSTANTS
    base_batch_size = 20
    max_batch_size = 25
    min_batch_size = 15
    
    # Adjust based on priorities complexity (original had this logic)
    if priorities_count > 5:
        adjusted_size = base_batch_size - 2
    elif priorities_count > 3:
        adjusted_size = base_batch_size - 1
    else:
        adjusted_size = base_batch_size
    
    # Ensure within bounds
    return max(min_batch_size, min(max_batch_size, adjusted_size))
```

### Task 2.2: Restore Missing Team Detection
**Estimated Time**: 30 minutes

#### Step 2.2.1: Implement Original Missing Team Logic
```python
async def _handle_missing_teams(
    self,
    picklist: List[Dict[str, Any]],
    all_teams_data: List[Dict[str, Any]],
    your_team_number: int,
    pick_position: str,
    priorities: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """EXACT RESTORATION OF ORIGINAL MISSING TEAM HANDLING"""
    
    # ORIGINAL SET DIFFERENCE CALCULATION
    available_team_numbers = {team["team_number"] for team in all_teams_data}
    ranked_team_numbers = {team["team_number"] for team in picklist}
    missing_team_numbers = available_team_numbers - ranked_team_numbers
    
    if not missing_team_numbers:
        logger.info("No missing teams detected")
        return picklist
    
    logger.warning(f"Missing {len(missing_team_numbers)} teams: {sorted(missing_team_numbers)}")
    
    # ORIGINAL MISSING TEAM RANKING WITH SMALLER BATCH SIZE
    missing_teams_data = [t for t in all_teams_data if t["team_number"] in missing_team_numbers]
    
    missing_result = await self.gpt_service.analyze_teams(
        system_prompt=self.gpt_service.create_missing_teams_system_prompt(
            pick_position, len(missing_teams_data)
        ),
        user_prompt=self.gpt_service.create_missing_teams_user_prompt(
            list(missing_team_numbers), picklist, your_team_number,
            pick_position, priorities, missing_teams_data
        ),
        teams_data=missing_teams_data
    )
    
    if missing_result.get("status") == "success":
        missing_picklist = missing_result.get("picklist", [])
        logger.info(f"Successfully ranked {len(missing_picklist)} missing teams")
        
        # MERGE WITH ORIGINAL PICKLIST
        combined_picklist = picklist + missing_picklist
        
        # ORIGINAL DEDUPLICATION AND SORTING
        seen_teams = {}
        for team in combined_picklist:
            team_number = team.get("team_number")
            if team_number not in seen_teams or team.get("score", 0) > seen_teams[team_number].get("score", 0):
                seen_teams[team_number] = team
        
        return sorted(seen_teams.values(), key=lambda x: x.get("score", 0), reverse=True)
    
    logger.error("Failed to rank missing teams")
    return picklist
```

---

## 📋 PHASE 3: OPTIMIZATION SERVICE RESTORATION (Estimated: 1 hour)

### Task 3.1: Restore Team Data Condensation
**File**: `backend/app/services/performance_optimization_service.py`
**Estimated Time**: 45 minutes

#### Step 3.1.1: Implement Original Data Condensation
```python
def condense_team_data_for_gpt(self, teams_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """EXACT RESTORATION OF ORIGINAL TEAM DATA CONDENSATION"""
    
    condensed_teams = []
    
    for team_data in teams_data:
        condensed_team = {
            "team_number": team_data["team_number"],
            "nickname": team_data.get("nickname", f"Team {team_data['team_number']}")
        }
        
        # ORIGINAL METRICS CONDENSATION
        if "scouting_data" in team_data and team_data["scouting_data"]:
            condensed_team["metrics"] = self._condense_metrics(team_data["scouting_data"])
        
        # ORIGINAL STATBOTICS INTEGRATION
        if "statbotics" in team_data:
            for key, value in team_data["statbotics"].items():
                condensed_team[f"statbotics_{key}"] = value
        
        # ORIGINAL SUPERSCOUTING LIMITATION (1 note max)
        if "superscouting" in team_data and team_data["superscouting"]:
            notes = team_data["superscouting"]
            if isinstance(notes, list) and notes:
                condensed_team["superscouting"] = notes[0]  # Take only first note
            elif isinstance(notes, str):
                condensed_team["superscouting"] = notes[:100]  # Limit to 100 chars
        
        condensed_teams.append(condensed_team)
    
    return condensed_teams

def _condense_metrics(self, scouting_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """RESTORE ORIGINAL METRICS AVERAGING"""
    
    if not scouting_data:
        return {}
    
    # ORIGINAL ESSENTIAL FIELDS ONLY
    essential_fields = [
        "auto_points", "teleop_points", "endgame_points",
        "auto_mobility", "auto_docking", "teleop_scoring_rate",
        "defense_rating", "driver_skill", "consistency_rating"
    ]
    
    metrics = {}
    for field in essential_fields:
        values = [match.get(field, 0) for match in scouting_data if isinstance(match.get(field), (int, float))]
        if values:
            metrics[field] = round(sum(values) / len(values), 2)
    
    return metrics

def calculate_weighted_score(self, team_data: Dict[str, Any], priorities: List[Dict[str, Any]]) -> float:
    """RESTORE ORIGINAL WEIGHTED SCORING"""
    
    if not priorities:
        return 0.0
    
    total_score = 0.0
    total_weight = 0.0
    
    for priority in priorities:
        field_name = priority.get("id", "")
        weight = priority.get("weight", 1.0)
        
        # ORIGINAL FIELD MAPPING
        field_value = self._extract_field_value(team_data, field_name)
        
        if field_value is not None:
            total_score += field_value * weight
            total_weight += weight
    
    return round(total_score / total_weight if total_weight > 0 else 0.0, 2)
```

### Task 3.2: Restore Token Optimization
**Estimated Time**: 15 minutes

#### Step 3.2.1: Implement Token Counting and Caching
```python
def estimate_token_usage(
    self, 
    teams_count: int, 
    priorities_count: int, 
    use_ultra_compact: bool = True
) -> Dict[str, int]:
    """RESTORE ORIGINAL TOKEN ESTIMATION"""
    
    # ORIGINAL TOKEN ESTIMATION FORMULAS
    base_system_tokens = 200 if use_ultra_compact else 400
    base_user_tokens = 150
    
    # ORIGINAL PER-TEAM TOKEN COSTS
    tokens_per_team = 25 if use_ultra_compact else 45
    tokens_per_priority = 15
    
    estimated_input = (
        base_system_tokens + 
        base_user_tokens + 
        (teams_count * tokens_per_team) + 
        (priorities_count * tokens_per_priority)
    )
    
    # ORIGINAL OUTPUT ESTIMATION
    estimated_output = teams_count * (8 if use_ultra_compact else 15)
    
    return {
        "input_tokens": estimated_input,
        "output_tokens": estimated_output,
        "total_tokens": estimated_input + estimated_output,
        "optimization_used": "ultra_compact" if use_ultra_compact else "standard"
    }
```

---

## 📋 PHASE 4: BATCH PROCESSING RESTORATION (Estimated: 30 minutes)

### Task 4.1: Restore Original Batch Processing
**File**: `backend/app/services/batch_processing_service.py`
**Estimated Time**: 30 minutes

#### Step 4.1.1: Implement Threading-Based Progress Updates
```python
async def process_batches_with_threading(
    self,
    batches: List[List[Dict[str, Any]]],
    cache_key: str,
    batch_processor_func: Callable,
    **kwargs
) -> Dict[str, Any]:
    """RESTORE ORIGINAL THREADING-BASED BATCH PROCESSING"""
    
    total_batches = len(batches)
    successful_batches = 0
    combined_results = []
    
    # ORIGINAL PROGRESS TRACKER INITIALIZATION
    progress_tracker = ProgressTracker.create_tracker(cache_key)
    progress_tracker.update(0, f"Starting batch processing ({total_batches} batches)")
    
    for batch_idx, batch_teams in enumerate(batches):
        try:
            # ORIGINAL PROGRESS UPDATE PATTERN
            progress_msg = f"Processing batch {batch_idx + 1} of {total_batches}"
            progress_percentage = (batch_idx / total_batches) * 100
            progress_tracker.update(progress_percentage, progress_msg)
            
            # ORIGINAL THREADING FOR BATCH PROCESSING
            batch_complete = threading.Event()
            batch_result = None
            batch_error = None
            
            def process_batch():
                nonlocal batch_result, batch_error
                try:
                    result = await batch_processor_func(
                        teams_data=batch_teams,
                        batch_index=batch_idx,
                        cache_key=cache_key,
                        **kwargs
                    )
                    batch_result = result
                except Exception as e:
                    batch_error = e
                finally:
                    batch_complete.set()
            
            # Start batch processing in thread
            batch_thread = threading.Thread(target=process_batch)
            batch_thread.start()
            
            # ORIGINAL PROGRESS UPDATES DURING PROCESSING
            while not batch_complete.is_set():
                await asyncio.sleep(1)  # Update every second
                progress_tracker.update(
                    progress_percentage + (10 / total_batches),  # Show sub-progress
                    f"{progress_msg} - In progress..."
                )
            
            batch_thread.join()
            
            if batch_error:
                raise batch_error
            
            if batch_result and batch_result.get("status") == "success":
                combined_results.extend(batch_result.get("picklist", []))
                successful_batches += 1
                self.update_batch_progress(cache_key, batch_idx, batch_result)
            
        except Exception as e:
            logger.error(f"Batch {batch_idx + 1} failed: {str(e)}")
            progress_tracker.update(
                (batch_idx / total_batches) * 100,
                f"Batch {batch_idx + 1} failed: {str(e)}"
            )
    
    if successful_batches > 0:
        progress_tracker.complete(f"Batch processing completed: {successful_batches}/{total_batches} successful")
        return {
            "status": "success",
            "picklist": combined_results,
            "batches_processed": successful_batches,
            "total_batches": total_batches
        }
    else:
        progress_tracker.fail("All batches failed")
        return {
            "status": "error",
            "error": "All batches failed",
            "batches_processed": 0,
            "total_batches": total_batches
        }
```

---

## 📋 PHASE 5: INTEGRATION & VALIDATION (Estimated: 1 hour)

### Task 5.1: Integration Testing Protocol
**Estimated Time**: 30 minutes

#### Step 5.1.1: Create Comprehensive Test Suite
```python
# File: test_reconstruction_validation.py
import pytest
import asyncio
from app.services.picklist_generator_service import PicklistGeneratorService

class TestReconstructionValidation:
    """COMPREHENSIVE VALIDATION OF RECONSTRUCTED SYSTEM"""
    
    @pytest.mark.asyncio
    async def test_55_teams_single_request(self):
        """CRITICAL: Test 55 teams in single request without rate limits"""
        
        # Load actual dataset with 55 teams
        service = PicklistGeneratorService("app/data/unified_event_2025lake.json")
        
        result = await service.generate_picklist(
            your_team_number=1234,
            pick_position="first",
            priorities=[
                {"id": "auto_points", "weight": 2.0},
                {"id": "teleop_points", "weight": 1.5},
                {"id": "endgame_points", "weight": 1.0}
            ],
            use_batching=False  # Force single request
        )
        
        # VALIDATION CRITERIA
        assert result["status"] == "success"
        assert len(result["picklist"]) >= 50  # Should get most/all teams
        assert result["processing_time"] < 30  # Should complete quickly
        
        # Check for duplicates
        team_numbers = [team["team_number"] for team in result["picklist"]]
        assert len(team_numbers) == len(set(team_numbers))  # No duplicates
    
    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self):
        """Test rate limit handling with multiple requests"""
        
        service = PicklistGeneratorService("app/data/unified_event_2025lake.json")
        
        # Fire multiple requests to trigger rate limits
        tasks = []
        for i in range(5):
            task = service.generate_picklist(
                your_team_number=1000 + i,
                pick_position="first",
                priorities=[{"id": "auto_points", "weight": 1.0}],
                use_batching=False
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some should succeed despite rate limits
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        assert len(successful_results) >= 1
    
    def test_token_optimization(self):
        """Validate token usage is optimized"""
        
        service = PicklistGeneratorService("app/data/unified_event_2025lake.json")
        teams_data = service.data_service.get_teams_for_analysis()[:55]
        
        # Test ultra-compact vs standard format
        ultra_compact_prompt, _ = service.gpt_service.create_user_prompt(
            your_team_number=1234,
            pick_position="first", 
            priorities=[{"id": "auto_points", "weight": 1.0}],
            teams_data=teams_data,
            force_index_mapping=True
        )
        
        # Token count should be reasonable
        token_count = len(service.gpt_service.token_encoder.encode(ultra_compact_prompt))
        assert token_count < 50000  # Should be well under limit
        
        logger.info(f"Token usage for 55 teams: {token_count}")
```

### Task 5.2: Performance Benchmarking
**Estimated Time**: 30 minutes

#### Step 5.2.1: Create Performance Validation Suite
```python
# File: performance_benchmark.py
import time
import asyncio
import statistics
from app.services.picklist_generator_service import PicklistGeneratorService

async def benchmark_reconstruction_performance():
    """PERFORMANCE VALIDATION OF RECONSTRUCTED SYSTEM"""
    
    service = PicklistGeneratorService("app/data/unified_event_2025lake.json")
    
    # Test scenarios
    scenarios = [
        {"teams": 20, "batching": False, "description": "20 teams single request"},
        {"teams": 35, "batching": False, "description": "35 teams single request"},
        {"teams": 55, "batching": False, "description": "55 teams single request"},
        {"teams": 55, "batching": True, "description": "55 teams with batching"},
    ]
    
    results = {}
    
    for scenario in scenarios:
        times = []
        success_count = 0
        
        # Run each scenario 3 times
        for run in range(3):
            start_time = time.time()
            
            try:
                result = await service.generate_picklist(
                    your_team_number=1234,
                    pick_position="first",
                    priorities=[
                        {"id": "auto_points", "weight": 2.0},
                        {"id": "teleop_points", "weight": 1.5}
                    ],
                    use_batching=scenario["batching"]
                )
                
                processing_time = time.time() - start_time
                times.append(processing_time)
                
                if result.get("status") == "success":
                    success_count += 1
                    
            except Exception as e:
                print(f"Scenario {scenario['description']} run {run+1} failed: {e}")
        
        if times:
            results[scenario["description"]] = {
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "success_rate": success_count / 3,
                "runs": len(times)
            }
    
    # Print results
    print("\n=== PERFORMANCE BENCHMARK RESULTS ===")
    for scenario, metrics in results.items():
        print(f"\n{scenario}:")
        print(f"  Average time: {metrics['avg_time']:.2f}s")
        print(f"  Min time: {metrics['min_time']:.2f}s") 
        print(f"  Max time: {metrics['max_time']:.2f}s")
        print(f"  Success rate: {metrics['success_rate']*100:.1f}%")
    
    return results
```

---

## 📋 PHASE 6: FINAL VALIDATION & DEPLOYMENT (Estimated: 30 minutes)

### Task 6.1: End-to-End Validation
**Estimated Time**: 20 minutes

#### Step 6.1.1: Full System Test
```bash
# Run complete validation suite
cd backend
python -m pytest test_reconstruction_validation.py -v
python performance_benchmark.py

# Test with actual frontend
cd ../frontend
npm run dev

# Navigate to picklist page and test with:
# - 55 teams (2025lake dataset)
# - First pick position  
# - Standard priorities
# - Both single and batch processing
```

### Task 6.2: Documentation Update
**Estimated Time**: 10 minutes

#### Step 6.2.1: Update CLAUDE.md with Reconstruction Notes
```markdown
## Reconstruction Summary

**Date**: [Current Date]
**Status**: ✅ COMPLETED - Production Ready

### Restored Algorithms:
- ✅ Ultra-compact JSON format (75% token reduction)
- ✅ Exponential backoff rate limiting (2s→4s→8s)
- ✅ Index mapping for all requests (prevents duplicates)
- ✅ 4-layer error recovery system
- ✅ Automatic batching threshold (20 teams)
- ✅ Missing team detection and ranking
- ✅ Threading-based progress updates
- ✅ Token optimization and validation

### Performance Validation:
- ✅ 55 teams processed in single request
- ✅ No rate limiting issues
- ✅ No duplicate teams
- ✅ Sub-30 second processing time
- ✅ Complete progress tracking

### Architecture Preserved:
- ✅ Service separation maintained
- ✅ Testability improved
- ✅ Code organization clean
- ✅ Error handling robust
```

---

## 🚨 CRITICAL SUCCESS CHECKPOINTS

### Checkpoint 1: After Phase 1
- [ ] Ultra-compact JSON format working
- [ ] Rate limit retry working with exponential backoff
- [ ] Token counting and validation working
- [ ] Error recovery system functional

### Checkpoint 2: After Phase 2  
- [ ] Automatic batching at 20 team threshold
- [ ] Missing team detection working
- [ ] Index mapping preventing duplicates
- [ ] Batch processing restored

### Checkpoint 3: After Phase 3
- [ ] Team data condensation optimized
- [ ] Token usage reduced by >50%
- [ ] Weighted scoring accurate
- [ ] Performance metrics tracked

### Checkpoint 4: After Phase 4
- [ ] Progress tracking with threading
- [ ] Batch processing with progress updates
- [ ] Error handling in batch mode
- [ ] Cache management working

### Checkpoint 5: After Phase 5
- [ ] 55 teams processed successfully
- [ ] No rate limits encountered
- [ ] All teams returned (no duplicates)
- [ ] Performance under 30 seconds

### Final Checkpoint: After Phase 6
- [ ] Frontend integration working
- [ ] End-to-end testing passed
- [ ] Performance benchmarks met
- [ ] Documentation updated

---

## ⚠️ RISK MITIGATION

### Risk 1: Rate Limiting During Testing
**Mitigation**: 
- Use test datasets with fewer teams initially
- Implement API key rotation if available
- Test during off-peak hours

### Risk 2: Token Limit Exceeded
**Mitigation**:
- Implement progressive team data condensation
- Add dynamic batch size adjustment
- Fallback to smaller batch sizes

### Risk 3: Error Recovery Failure
**Mitigation**:
- Test with malformed GPT responses
- Validate all regex patterns
- Implement additional safety checks

### Risk 4: Performance Regression
**Mitigation**:
- Benchmark before and after each phase
- Maintain performance metrics
- Rollback capability at each checkpoint

---

## 📊 SUCCESS METRICS

### Primary Success Criteria:
1. **Functionality**: Process 55+ teams without errors
2. **Performance**: Complete in <30 seconds  
3. **Reliability**: Handle rate limits gracefully
4. **Accuracy**: Return all teams without duplicates
5. **Architecture**: Maintain refactored service boundaries

### Secondary Success Criteria:
1. **Token Efficiency**: <50,000 tokens for 55 teams
2. **Error Recovery**: Handle malformed responses
3. **Progress Tracking**: Real-time updates during processing
4. **Maintainability**: Clean, documented code
5. **Testability**: Comprehensive test coverage

---

## 🎯 POST-SPRINT ACTIONS

### Immediate (Same Day):
1. Deploy to development environment
2. Run full regression test suite
3. Update monitoring and alerting
4. Document any remaining issues

### Short Term (Within Week):
1. Performance monitoring in production
2. User acceptance testing
3. Optimization opportunities identified
4. Knowledge transfer completed

### Long Term (Within Month):
1. Advanced optimization implementation
2. Additional error scenarios covered
3. Performance benchmarking automated
4. Architecture documentation updated