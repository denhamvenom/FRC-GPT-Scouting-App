# Strategic Data Enhancement Plan v2.0
**Comprehensive Planning Document**

---

## Executive Summary

The current performance band system (High/Med/Low) destroys critical strategic granularity needed for accurate alliance selection. This plan outlines a complete transformation from performance bands to strategic intelligence synthesis, enabling GPT to make nuanced alliance selection decisions while dramatically reducing token usage.

---

## Problem Analysis

### Core Strategic Issues
1. **Granularity Loss**: Team scoring 10 vs 5 coral on L4 both labeled "Med" - massive strategic difference lost
2. **Consistency Blindness**: Team A (4,4,4,4,4) vs Team B (8,8,0,0,4) both average 4 but vastly different reliability
3. **Specialization Obscured**: Can't distinguish auto specialists from teleop powerhouses from endgame clutch performers
4. **Context Destruction**: Performance bands eliminate situational performance patterns (trending, pressure response, etc.)
5. **Token Waste**: Verbose game manual context repeated in every API call

### Real-World Impact Example
**From Lake Superior Regional Analysis:**
- **Team 8044**: Offensive powerhouse (75.78 avg, 61.56 teleop) with climb weakness
- **Team 16**: Balanced contributor (67.0 avg) with climbing strength (9.11 endgame avg)  
- **Team 364**: Developing team (23.89 avg) with mechanical reliability issues

**Current System Output**: All three might get similar "Med" ratings in key metrics
**Strategic Reality**: Completely different alliance roles and value propositions

---

## Solution Architecture: Strategic Intelligence Synthesis

### 1. Performance Signature System

**Replace Performance Bands With:**
```
Current: coral_L4: "Med"
Proposed: coral_L4: "4.2±0.3 (reliable, n=5, stable)"
```

**Signature Components:**
- **Performance Level**: 4.2 average
- **Reliability Indicator**: ±0.3 standard deviation  
- **Confidence Metric**: n=5 sample size
- **Trend Analysis**: stable/improving/declining
- **Strategic Context**: reliable/volatile/clutch

### 2. Strategic Profile Generation

**Transform Raw Metrics Into Strategic Roles:**

**Scoring Profiles:**
- `auto_specialist: 12.3±1.1 (strong)`
- `teleop_volume: 47.2±8.3 (consistent)`  
- `endgame_clutch: 11.8±2.1 (reliable)`

**Operational Profiles:**
- `cycle_speed: fast`
- `defense_resistance: moderate` 
- `pressure_response: clutch`
- `mechanical_reliability: high`

**Synergy Indicators:**
- `alliance_anchor: yes`
- `perfect_second_pick: yes`
- `needs_carrying: no`

### 3. Capability Extraction

**From Match Data Patterns:**
- `floor_intake_both`: Can intake coral and algae from floor
- `coral_L4_specialist`: Consistent high-level scoring
- `climbing_12pts`: Reliable endgame climbing
- `fast_cycles`: Efficient game piece handling

**From Text Field Intelligence:**
- `strategy_field`: "Aggressive defense" → `defense_specialist: aggressive_style`
- `scout_comments`: "Gets rattled" → `pressure_response: struggles`

### 4. Dynamic Context Synthesis

**Year-Specific Game Manual Compression:**

**Current Approach:**
- Send 2000+ character manual sections with every API call
- Repetitive, verbose, token-heavy

**Proposed Approach:**
1. **Setup Phase**: User selects relevant TOC sections (scoring rules, strategic elements, etc.)
2. **Synthesis Phase**: GPT creates compressed strategic context from selected sections
3. **Cache Phase**: Store synthesized context for entire year/game
4. **Usage Phase**: Include compressed context (~300-400 chars) in every picklist call

**Example Synthesized Context:**
```
"Reefscape 2025: Auto coral L4=8pts (high-risk), Teleop coral=1-4pts by level, 
Climbing=12pts (match-critical), Defense impacts cycles significantly, 
Alliance needs auto+teleop+endgame balance, Specialization beats generalization"
```

---

## Strategic Intelligence Format

### Complete Team Data Packet
```json
{
  "team": 8044,
  "nickname": "Denham Venom",
  "scoring": {
    "auto_coral_L4": "1.33±0.5 (consistent, n=9)",
    "teleop_total": "61.56±12.4 (high_volume, n=9)", 
    "endgame": "1.56±3.2 (climb_unreliable, n=9)"
  },
  "profile": {
    "specialty": "offensive_powerhouse",
    "reliability": "high_consistency",
    "trend": "stable_dominance",
    "pressure": "clutch_performer"
  },
  "strategic": {
    "role": "primary_scorer",
    "capabilities": "floor_intake_both|coral_L4_specialist|fast_cycles",
    "synergy": "alliance_anchor",
    "counters": "defense_resistant"
  },
  "intel": "8-1 record, 77.01 EPA, floor intake mastery, weak endgame"
}
```

### What This Enables GPT To Understand
- **Performance + Context**: Not just "4.2 average" but "4.2±0.3 reliable performer"
- **Strategic Roles**: "Offensive powerhouse that needs endgame support"
- **Alliance Chemistry**: "Perfect first pick, pairs well with climbing specialists"
- **Risk Assessment**: "High consistency but climb weakness in close matches"

---

## Implementation Strategy

### Phase 1: Context Synthesis Infrastructure
**Objective**: Replace verbose manual context with intelligent compression

**Tasks:**
1. Create game context synthesis service
2. Implement TOC-based section selection in setup
3. Build GPT-powered context compression pipeline
4. Add caching system for synthesized contexts
5. Update picklist generation to use compressed context

**Deliverable**: Year-specific strategic context generation system

### Phase 2: Performance Signature System
**Objective**: Replace performance bands with strategic signatures using hybrid app+GPT approach

#### **2.1: Game-Agnostic Signature Architecture**

**Universal Signature Format:**
```
metric_name: "value±reliability (context, n=sample_size, trend)"
```

**Game-Independent Strategic Qualifiers:**
- **Performance Levels**: dominant (90th+ percentile), strong (75th+), solid (50th+), developing (improving), struggling
- **Reliability Tiers**: machine_like (CV<15%), consistent (15-25%), reliable (25-40%), volatile (40-60%), unpredictable (60%+)
- **Trend Indicators**: improving, stable, declining, limited_data

#### **2.2: Event-Based Statistical Foundation**

**Post-Validation Processing Pipeline:**
1. **Data Validation & Cleaning**: Raw scouting data → validated dataset
2. **Event-Wide Statistical Analysis**: Calculate percentiles across entire event field
3. **Team Signature Generation**: App-based statistical processing using event baselines
4. **Strategic Intelligence Enhancement**: GPT-powered strategic context assignment

**Event Baseline Calculation:**
```python
def calculate_event_baselines(clean_dataset):
    """Calculate percentiles and statistics across entire event"""
    event_stats = {}
    for metric_name in all_metrics:
        all_values = extract_metric_across_all_teams(metric_name)
        event_stats[metric_name] = {
            'percentiles': np.percentile(all_values, [10, 25, 50, 75, 90]),
            'mean': np.mean(all_values),
            'std': np.std(all_values),
            'field_size': len(all_values)
        }
    return event_stats
```

#### **2.3: Hybrid Processing Architecture**

**App-Based Processing (Fast, Deterministic):**
- Core statistical calculations (mean, std dev, percentiles)
- Event-context percentile ranking
- Basic performance/reliability tier classification
- Trend analysis via linear regression
- Base signature formatting

**GPT-Based Processing (Strategic Intelligence):**
- Strategic context synthesis from performance patterns
- Text field intelligence extraction (strategy, comments)
- Nuanced strategic qualifier assignment
- Cross-team pattern recognition

**Division of Labor:**
```python
def generate_performance_signature(metric_name, match_values, field_metadata, event_baselines):
    # STEP 1: App calculates core statistics (instant)
    stats = calculate_core_statistics(match_values)
    percentile = calculate_event_percentile(stats.mean, event_baselines[metric_name])
    
    # STEP 2: App determines basic classifications (instant)  
    performance_tier = get_performance_tier(percentile)
    reliability_tier = get_reliability_tier(stats.cv)
    
    # STEP 3: App creates base signature (instant)
    base_signature = f"{stats.mean:.1f}±{stats.std:.1f} ({performance_tier}_{reliability_tier}, n={stats.sample_size})"
    
    # STEP 4: GPT adds strategic context (cached after first time)
    strategic_context = get_strategic_context_from_gpt(metric_name, match_values, stats, field_metadata)
    
    # STEP 5: Combine for final signature
    return f"{base_signature}, {strategic_context}"
```

#### **2.4: Batched GPT Processing Strategy**

**Strategic Batching Approach:**
- Process teams in batches of 20 for manageable token usage
- Include comprehensive event-wide statistical context with each batch
- Use index mapping to ensure complete team coverage and response validation
- Enable cross-team insights within batch while maintaining field perspective

**Event-Wide Statistical Context (Sent with Each Batch):**
```json
{
  "event_baselines": {
    "auto_coral_L4": {
      "min": 0, "max": 3, "mean": 1.2, "std": 0.8,
      "percentiles": {"10th": 0, "25th": 0, "50th": 1, "75th": 2, "90th": 3},
      "top_performers": 8,
      "field_size": 48
    },
    "teleop_total": {
      "min": 8, "max": 78, "mean": 42.3, "std": 18.2,
      "percentiles": {"10th": 18, "25th": 28, "50th": 41, "75th": 58, "90th": 68},
      "top_performers": 5,
      "field_size": 48
    }
  },
  "competitive_context": {
    "total_teams": 48,
    "avg_matches_per_team": 7.2,
    "event_level": "regional",
    "score_inflation": "moderate"
  }
}
```

**Batch GPT Payload Structure with Index Mapping:**
```json
{
  "task": "Generate strategic signatures for batch 1/4",
  "batch_info": {
    "batch_number": 1,
    "total_batches": 4,
    "teams_in_batch": 20
  },
  "team_index_map": {
    "1": 8044, "2": 16, "3": 364, "4": 2973, "5": 1421,
    "6": 3526, "7": 5653, "8": 3102, "9": 2080, "10": 456,
    "11": 3468, "12": 9761, "13": 6107, "14": 9660, "15": 9456,
    "16": 1622, "17": 4087, "18": 8808, "19": 4336, "20": 5863
  },
  "event_baselines": { /* statistical context above */ },
  "teams": [
    {
      "index": 1,
      "team": 8044,
      "nickname": "Denham Venom",
      "performance_data": {
        "auto_coral_L4": {"values": [1,2,1,0,2,1,2], "avg": 1.33, "std": 0.7, "percentile": 85},
        "teleop_total": {"values": [52,61,58,47,72,65,61], "avg": 59.4, "std": 8.1, "percentile": 78}
      },
      "qualitative": {
        "strategy": "Fast movement, floor intake both",
        "comments": "Dominant scorer, struggles climbing"
      }
    }
    // ... indices 2-20 for remaining teams in batch
  ]
}
```

**Expected GPT Response with Index Validation:**
```json
{
  "batch_info": {
    "batch_number": 1,
    "teams_processed": 20,
    "missing_teams": [],
    "processing_status": "complete"
  },
  "team_signatures": [
    {
      "index": 1,
      "team": 8044,
      "enhanced_metrics": {
        "auto_coral_L4": "1.33±0.7 (dominant_consistent_auto_specialist, n=7)",
        "teleop_total": "59.4±8.1 (strong_reliable_volume_scorer, n=7)"
      },
      "strategic_profile": "offensive_powerhouse_needs_endgame_support"
    }
    // ... indices 2-20
  ],
  "batch_insights": {
    "standout_performers": [1, 2, 4],  // indices of top teams in batch
    "developing_teams": [3, 15],
    "specialist_roles": {
      "auto_specialists": [1, 2, 4],
      "endgame_clutch": [2, 8]
    }
  }
}
```

**Index Mapping Validation Process:**
```python
def validate_batch_response(response, expected_indices):
    """Ensure all teams are processed and none are missing"""
    
    processed_indices = {team["index"] for team in response["team_signatures"]}
    expected_indices_set = set(expected_indices)
    
    missing_indices = expected_indices_set - processed_indices
    unexpected_indices = processed_indices - expected_indices_set
    
    if missing_indices:
        logger.error(f"Missing teams in batch response: {missing_indices}")
        return False, f"Missing indices: {missing_indices}"
    
    if unexpected_indices:
        logger.warning(f"Unexpected teams in batch response: {unexpected_indices}")
    
    return True, "All expected teams processed"

def process_signature_batches(teams, event_baselines):
    """Process all teams in batches with validation"""
    
    batches = create_batches(teams, batch_size=20)
    all_signatures = {}
    
    for batch_num, batch_teams in enumerate(batches, 1):
        # Create index mapping for this batch
        batch_index_map = {i+1: team["team_number"] for i, team in enumerate(batch_teams)}
        
        # Process batch with GPT
        batch_response = process_batch_with_gpt(batch_teams, batch_index_map, event_baselines, batch_num)
        
        # Validate response completeness
        is_valid, message = validate_batch_response(batch_response, list(batch_index_map.keys()))
        if not is_valid:
            raise ProcessingError(f"Batch {batch_num} validation failed: {message}")
        
        # Convert indices back to team numbers and store
        for team_sig in batch_response["team_signatures"]:
            team_number = batch_index_map[team_sig["index"]]
            all_signatures[team_number] = team_sig
    
    return all_signatures
```

**Token Economics (Revised):**
- **Event baselines**: ~800 tokens per batch (shared context)
- **Team data**: ~150 tokens × 20 teams = 3,000 tokens per batch
- **Index mapping + prompting**: ~500 tokens per batch
- **Total per batch**: ~4,300 tokens
- **For 80 teams (4 batches)**: 17,200 tokens total
- **Savings vs current**: 57% reduction (17k vs 40k tokens)

**Strategic Advantages:**
- **Complete Coverage**: Index mapping ensures no teams are missed
- **Field Context**: Event baselines provide competitive landscape understanding
- **Batch Consistency**: Cross-team insights within manageable token limits
- **Validation**: Systematic verification of response completeness
- **Recovery**: Clear error handling for incomplete responses

**Note: No Manual Context Required**
- Performance signature creation focuses on data analysis and strategic pattern recognition
- Game manual context reserved for actual picklist generation phase
- Event statistical context provides sufficient competitive framework

#### **2.5: Strategic Intelligence File Output**

**Comprehensive Strategic Playbook:**
```python
def create_strategic_intelligence_file(enhanced_profiles):
    output = {
        "event_key": "2025lake",
        "analysis_timestamp": datetime.now(),
        "event_baselines": event_stats_summary,
        "strategic_profiles": enhanced_profiles,
        "alliance_recommendations": gpt_alliance_insights
    }
    save_file("strategic_intelligence_2025lake.json", output)
```

**Tasks:**
1. Implement game-agnostic signature architecture
2. Create event-wide statistical baseline calculation system
3. Build hybrid app+GPT processing pipeline
4. Develop batched GPT strategic analysis system (20 teams per batch)
5. Implement index mapping and response validation system
6. Create strategic intelligence file generation from batched results
7. Build event baseline context generation for batch processing
8. Implement batch response validation and error handling
9. Create signature aggregation system across multiple batches
10. Build validation testing against known team performances

**Deliverable**: Game-agnostic performance signature system with strategic intelligence enhancement

### Phase 3: Strategic Profile Generation  
**Objective**: Transform raw metrics into strategic intelligence

**Tasks:**
1. Develop strategic role classification algorithms
2. Implement capability extraction from match patterns
3. Create synergy indicator generation
4. Build text field intelligence processing
5. Design strategic profile output format

**Deliverable**: Complete strategic profiling system

### Phase 4: Intelligence Integration & Compatibility
**Objective**: Integrate strategic intelligence while preserving existing system compatibility

**Tasks:**
1. Design dual data strategy: strategic intelligence + legacy unified dataset preservation
2. Implement strategic intelligence file generation (post-validation trigger)
3. Create selective service integration for picklist functions only
4. Build enhanced Compare & Rerank with full unified dataset + compressed manual context
5. Implement fallback mechanisms for graceful degradation
6. Update PicklistGeneratorService with dual data source initialization
7. Create strategic intelligence caching and refresh mechanisms
8. Ensure zero disruption to existing GraphAnalysis, TeamComparison, and other functions
9. Implement comprehensive testing with both data formats
10. Performance optimization and token usage validation across both approaches

**Critical Compatibility Requirements:**
- **Zero Changes**: No modifications to existing `unified_event_2025lake.json` structure
- **Additive Only**: All enhancements are additional files/functionality
- **Backward Compatible**: All existing API endpoints continue unchanged
- **Selective Enhancement**: Strategic intelligence only for picklist generation
- **Granular Fallback**: Compare & Rerank uses full data for maximum precision

**Data Flow Architecture:**
```
Legacy Flow (Preserved):
unified_event_2025lake.json → GraphAnalysis, TeamComparison, etc.

Enhanced Flow (New):
unified_event_2025lake.json → Strategic Intelligence Processing → strategic_intelligence_2025lake.json → Enhanced Picklist

Hybrid Flow (Compare & Rerank):
unified_event_2025lake.json + Compressed Manual Context → Granular Team Comparison
```

**Deliverable**: Complete strategic intelligence system with full legacy compatibility

---

## Expected Outcomes

### Token Economics
- **Current Usage**: ~500 tokens per team × 80 teams = 40,000 tokens
- **Projected Usage**: ~75 tokens per team × 80 teams = 6,000 tokens
- **Reduction**: 85% token savings with enhanced strategic value

### Strategic Improvements
- **Granular Differentiation**: Distinguish reliable vs volatile performers
- **Specialization Recognition**: Clear identification of strategic roles
- **Consistency Assessment**: Performance reliability indicators
- **Trend Analysis**: Team trajectory and improvement patterns
- **Alliance Chemistry**: Synergy and complementary capability insights

### Operational Benefits
- **Elimination of Batching**: Single-pass processing through token efficiency
- **Enhanced Accuracy**: Decision-critical information preservation
- **Strategic Reasoning**: AI understanding of team roles and chemistry
- **Scalable Architecture**: Adaptable to different games and strategies

---

## Success Metrics

### Technical Metrics
- **Token Usage**: Target 85% reduction while maintaining information quality
- **Processing Speed**: Single-pass picklist generation for 80+ teams
- **Data Compression**: 10:1 compression ratio with strategic value enhancement

### Strategic Metrics
- **Picklist Accuracy**: Improved team differentiation and ranking quality
- **Alliance Selection**: Better strategic role identification and pairing
- **Consistency Recognition**: Reliable vs volatile performer distinction
- **Specialization Capture**: Clear auto/teleop/endgame specialist identification

### User Experience Metrics
- **Setup Efficiency**: Streamlined context synthesis during game setup
- **Result Clarity**: Enhanced strategic insights in picklist output
- **Decision Support**: Actionable intelligence for alliance selection

---

## Risk Assessment

### Technical Risks
- **Context Synthesis Quality**: GPT-generated context may lose critical details
- **Signature Accuracy**: Performance signatures must preserve ranking information
- **Processing Complexity**: Increased system complexity vs current implementation

### Mitigation Strategies
- **Context Validation**: Manual review and adjustment of synthesized contexts
- **Signature Testing**: Extensive validation against known team performances  
- **Incremental Implementation**: Phase-by-phase rollout with fallback capabilities

---

## Next Steps

### Immediate Actions
1. **Create Context Synthesis Prototype**: Test GPT's ability to compress game manual sections
2. **Performance Signature Algorithm**: Develop and test signature generation logic
3. **Strategic Profile Framework**: Design classification system for team roles
4. **Token Usage Analysis**: Validate projected token savings with real data
5. **Event Baseline Infrastructure**: Build statistical foundation for event-wide percentile calculations
6. **Hybrid Processing Pipeline**: Design app+GPT integration architecture

### Sprint Planning Preparation
1. **Task Breakdown**: Detailed implementation tasks for each phase
2. **Dependency Mapping**: Identify critical path and component dependencies
3. **Testing Strategy**: Comprehensive validation approach for each component
4. **Success Criteria**: Specific, measurable outcomes for each development phase

---

## Detailed Architecture Decisions

### Performance Signature Processing Flow

**Critical Decision: Post-Validation Integration**
- Performance signature generation occurs AFTER data validation is complete
- Enables stable event-wide statistical baselines for percentile calculations
- Creates deterministic signature generation independent of analysis subset
- Provides foundation for consistent strategic intelligence across all teams

**Processing Sequence:**
```
Raw Data → Validation → Event Baselines → Signature Generation → Strategic Enhancement → Intelligence File
```

**Key Benefits:**
- **Stable Rankings**: Team percentile doesn't change based on analysis subset
- **Strategic Context**: Event-wide competitive landscape understanding  
- **Consistent Baselines**: Same statistical foundation for all analyses
- **Cacheable Results**: Event baselines calculated once, reused for all signature generation

### Hybrid App+GPT Architecture Rationale

**App Processing Advantages:**
- ⚡ **Speed**: Instant statistical calculations, no API latency
- 🎯 **Deterministic**: Same input always produces same statistical output
- 💰 **Cost**: No token usage for mathematical operations
- 🔄 **Cacheable**: Statistical results can be reliably cached

**GPT Processing Advantages:**
- 🧠 **Intelligence**: Strategic pattern recognition and context synthesis
- 🔍 **Nuance**: Interpretation of qualitative data and performance patterns
- 🤝 **Synthesis**: Cross-team strategic insights and alliance chemistry
- 🎯 **Consistency**: Uniform strategic standards applied across all teams

**Integration Strategy:**
- App generates deterministic statistical foundation
- GPT adds strategic intelligence layer on top
- Results combined into comprehensive strategic signatures
- Caching reduces GPT calls for similar performance patterns

### Dual Data Strategy: Enhanced vs Legacy Compatibility

**Preservation of Existing Data Structures:**
- **Unified Dataset Integrity**: No changes to existing `unified_event_2025lake.json` structure
- **Legacy Compatibility**: All existing functionality continues to use original data format
- **Parallel Enhancement**: Create new strategic intelligence datasets alongside existing data
- **Selective Enhancement**: Apply strategic intelligence only to picklist generation functions

**Strategic Data Separation:**
```
Existing Data Flow:
unified_event_2025lake.json → Existing Functions (Compare, GraphAnalysis, etc.)

New Enhanced Flow:
unified_event_2025lake.json → Strategic Intelligence Processing → strategic_intelligence_2025lake.json → Enhanced Picklist Functions
```

**Function-Specific Data Usage:**
- **Picklist Generation**: Uses new strategic intelligence format for token efficiency
- **Compare & Rerank**: Uses original unified dataset + compressed manual context for maximum granularity
- **Graphical Analysis**: Continues using existing unified dataset structure
- **Team Comparison**: Continues using existing unified dataset structure

### Compare & Rerank Enhanced Strategy

**Granular Comparison Approach:**
When comparing 2-3 teams specifically, use maximum detail approach:

**Enhanced Compare & Rerank Data Packet:**
```json
{
  "task": "Compare and rerank specific teams for alliance selection",
  "manual_context": "Reefscape 2025: Auto coral L4=8pts (high-risk)...", // Compressed manual
  "user_priorities": [
    {"id": "auto_coral_L4", "weight": 0.8, "name": "Auto Coral L4 Scoring"},
    {"id": "teleop_total", "weight": 0.6, "name": "Teleop Total Points"}
  ],
  "comparison_teams": [
    {
      "team": 8044,
      "nickname": "Denham Venom",
      "raw_match_data": {
        "auto_coral_L4": [1,2,1,0,2,1,2],
        "teleop_total": [52,61,58,47,72,65,61],
        "endgame_total": [0,0,0,6,0,0,5]
      },
      "aggregated_metrics": {
        "auto_coral_L4": 1.33,
        "teleop_total": 59.4,
        "match_count": 7
      },
      "qualitative_data": {
        "strategy_notes": ["Fast movement", "Floor intake both", "Dominant scorer"],
        "scout_comments": ["Struggles with climbing", "Very consistent scorer", "Fast cycles"]
      },
      "record": {"wins": 8, "losses": 1, "ties": 0}
    }
    // ... other teams with full detail
  ]
}
```

**Benefits of Dual Strategy:**
- **Maximum Granularity**: Compare & Rerank gets full match-by-match data for precise analysis
- **Token Efficiency**: Picklist generation uses compressed strategic intelligence
- **Legacy Preservation**: No disruption to existing functionality
- **Selective Enhancement**: Apply improvements only where most beneficial

### Implementation Compatibility Requirements

**Data Structure Preservation:**
- **No modifications** to existing unified dataset JSON structure
- **Additive approach**: Create new strategic intelligence files alongside existing data
- **Backward compatibility**: All existing API endpoints continue functioning unchanged
- **Selective integration**: Only picklist generation functions use enhanced data

**Service Integration Strategy:**
```python
class PicklistGeneratorService:
    def __init__(self, unified_dataset_path: str):
        # Existing initialization preserved
        self.unified_dataset = self._load_unified_dataset(unified_dataset_path)
        
        # New strategic intelligence initialization
        strategic_intel_path = unified_dataset_path.replace('.json', '_strategic_intelligence.json')
        self.strategic_intelligence = self._load_or_generate_strategic_intelligence(strategic_intel_path)
    
    async def generate_picklist(self, ...):
        """Use strategic intelligence for efficient picklist generation"""
        return await self._generate_with_strategic_intelligence(...)
    
    async def rank_missing_teams(self, ...):
        """Use strategic intelligence for missing teams"""
        return await self._rank_missing_with_strategic_intelligence(...)
    
    async def compare_and_rerank(self, team_numbers: List[int], ...):
        """Use full unified dataset + manual context for granular comparison"""
        # Extract full team data from unified dataset
        comparison_teams = self._extract_full_team_data(team_numbers)
        # Use compressed manual context + full data for maximum precision
        return await self._compare_with_full_context(comparison_teams, ...)
```

**Strategic Intelligence File Generation:**
- **Triggered post-validation**: Generate strategic intelligence after data validation complete
- **Cached results**: Store strategic intelligence file for reuse across picklist generations
- **Refresh mechanism**: Regenerate when underlying unified dataset changes
- **Fallback capability**: Graceful degradation to original system if strategic intelligence unavailable

---

**Document Status**: Planning Complete - Ready for Sprint Development
**Next Phase**: Sprint Planning and Implementation Roadmap