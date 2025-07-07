# Game Context Optimization Implementation Plan

**Project**: FRC GPT Scouting App - Game Context Optimization  
**Created**: 2025-06-26  
**Status**: 🔴 Not Started  
**Estimated Duration**: 3-4 days  
**Risk Level**: Medium  

---

## Executive Summary

Currently, the FRC GPT Scouting App sends ~91KB of game manual text with every GPT API call, consuming significant tokens and potentially degrading performance. This plan implements a preprocessing step where GPT analyzes the game manual once during setup to extract only the essential information needed for picklist generation, reducing token usage by an estimated 80-90%.

---

## Current State Analysis

### Problem Statement
- **Data Size**: 91KB of game manual text sent with each GPT request
- **Token Impact**: ~23,000 tokens per request (using cl100k_base encoding)
- **Cost Impact**: Approximately $0.46-$0.92 per picklist generation in unnecessary tokens
- **Performance**: Increased latency due to larger payloads
- **Redundancy**: Full manual includes arena specifications, safety rules, and other irrelevant data

### Current Architecture
```
┌─────────────────────┐
│   JSON Manual File  │ (91KB raw text)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ DataAggregationSvc  │ (loads full text)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ PicklistGenerator   │ (passes to GPT)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   GPT API Calls     │ (includes full text)
└─────────────────────┘
```

---

## Proposed Solution

### New Architecture
```
┌─────────────────────┐
│   JSON Manual File  │ (91KB raw text)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ GameContextExtractor│ (NEW - one-time processing)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Extracted Context   │ (5-10KB focused data)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ DataAggregationSvc  │ (loads extracted context)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   GPT API Calls     │ (uses compact context)
└─────────────────────┘
```

### Key Components

1. **GameContextExtractorService** (New Service)
   - One-time processing of game manual
   - GPT-powered extraction of relevant information
   - Caching of extracted context
   - Validation of extraction quality

2. **Extracted Context Structure**
   ```json
   {
     "game_year": 2025,
     "game_name": "REEFSCAPE",
     "extraction_version": "1.0",
     "extraction_date": "2025-06-26",
     "scoring_summary": {
       "autonomous": {...},
       "teleop": {...},
       "endgame": {...}
     },
     "strategic_elements": [...],
     "alliance_considerations": [...],
     "key_metrics": [...],
     "original_manual_hash": "..."
   }
   ```

3. **Integration Points**
   - Modified `load_game_context()` method
   - New extraction command/endpoint
   - Fallback to full manual if extraction fails
   - Version tracking for re-extraction

---

## Implementation Plan

### Phase 1: Infrastructure Setup (Day 1)
- [ ] **1.1** Create `game_context_extractor_service.py`
- [ ] **1.2** Define extracted context schema/types
- [ ] **1.3** Create test framework for extraction service
- [ ] **1.4** Implement extraction result caching mechanism
- [ ] **1.5** Add configuration for extraction parameters

### Phase 2: Extraction Service Implementation (Day 1-2)
- [ ] **2.1** Implement GPT-powered extraction logic
- [ ] **2.2** Create extraction prompts optimized for game analysis
- [ ] **2.3** Implement extraction validation and quality checks
- [ ] **2.4** Add extraction result versioning
- [ ] **2.5** Create extraction command for manual/automated runs
- [ ] **2.6** Implement comprehensive error handling

### Phase 3: Integration (Day 2)
- [ ] **3.1** Modify `DataAggregationService.load_game_context()`
- [ ] **3.2** Update context loading to check for extracted version first
- [ ] **3.3** Implement fallback to full manual
- [ ] **3.4** Update GPT prompts to use extracted context format
- [ ] **3.5** Add extraction status to system health checks

### Phase 4: Testing & Validation (Day 3)
- [ ] **4.1** Unit tests for extraction service
- [ ] **4.2** Integration tests with existing services
- [ ] **4.3** A/B testing comparing picklist quality
- [ ] **4.4** Performance benchmarking (token usage, speed)
- [ ] **4.5** Cost analysis validation
- [ ] **4.6** Edge case testing (missing data, malformed manual)

### Phase 5: Safety & Rollback (Day 3-4)
- [ ] **5.1** Create baseline snapshots of current picklist outputs
- [ ] **5.2** Implement feature flag for extraction usage
- [ ] **5.3** Create rollback procedure documentation
- [ ] **5.4** Implement extraction result archiving
- [ ] **5.5** Add monitoring for extraction quality metrics

### Phase 6: Documentation & Deployment (Day 4)
- [ ] **6.1** Update API documentation
- [ ] **6.2** Create extraction usage guide
- [ ] **6.3** Update CLAUDE.md with new workflow
- [ ] **6.4** Create extraction troubleshooting guide
- [ ] **6.5** Deploy with staged rollout plan

---

## Technical Details

### Extraction Service API

```python
class GameContextExtractorService:
    """Extract essential game information for picklist generation."""
    
    async def extract_game_context(
        self,
        manual_path: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Extract relevant context from game manual."""
        
    def validate_extraction(
        self,
        extracted_context: Dict[str, Any],
        original_manual: str
    ) -> ValidationResult:
        """Validate extraction completeness and accuracy."""
        
    def get_extraction_prompt(self) -> str:
        """Get optimized prompt for game context extraction."""
```

### Extraction Prompt Strategy

```python
EXTRACTION_SYSTEM_PROMPT = """You are an FRC game analyst extracting ONLY the information needed for alliance selection and team evaluation.

Focus on:
1. Scoring mechanisms and point values
2. Game piece types and interactions
3. Autonomous period strategies
4. Endgame/climbing requirements
5. Strategic robot capabilities
6. Alliance cooperation elements

Exclude:
- Safety rules
- Field setup procedures
- Competition scheduling
- Referee signals
- Administrative rules

Output as structured JSON with clear categories."""
```

### Quality Metrics

1. **Token Reduction**: Target 80-90% reduction
2. **Extraction Time**: < 30 seconds one-time
3. **Picklist Quality**: No degradation vs baseline
4. **Coverage**: All strategic elements captured

---

## Risk Mitigation

### Identified Risks

1. **Extraction Quality Risk**
   - *Mitigation*: Comprehensive validation suite
   - *Mitigation*: Human review of first extraction
   - *Mitigation*: A/B testing with baseline

2. **Missing Information Risk**
   - *Mitigation*: Iterative prompt refinement
   - *Mitigation*: Fallback to full manual
   - *Mitigation*: Version tracking for updates

3. **Integration Risk**
   - *Mitigation*: Feature flag deployment
   - *Mitigation*: Comprehensive testing
   - *Mitigation*: Gradual rollout

4. **Performance Risk**
   - *Mitigation*: Caching at multiple levels
   - *Mitigation*: Async processing
   - *Mitigation*: Background extraction

---

## Success Criteria

### Quantitative Metrics
- [ ] Token usage reduced by ≥80%
- [ ] API costs reduced by ≥$0.40 per picklist
- [ ] No degradation in picklist quality scores
- [ ] Extraction completes in <30 seconds
- [ ] 100% test coverage on new code

### Qualitative Metrics
- [ ] Extracted context is human-readable
- [ ] Easy to update for new games
- [ ] Clear documentation for maintenance
- [ ] Smooth integration with existing flow

---

## Rollback Plan

1. **Immediate Rollback** (< 5 minutes)
   - Disable extraction via feature flag
   - System reverts to full manual loading

2. **Data Rollback** (< 30 minutes)
   - Delete extracted context cache
   - Force regeneration from manual

3. **Code Rollback** (< 1 hour)
   - Revert service changes
   - Restore original data loading

---

## Future Enhancements

1. **Multi-Game Support**: Extract contexts for multiple years
2. **Incremental Updates**: Update extraction for rule changes
3. **Custom Extractions**: Team-specific strategic focuses
4. **ML Optimization**: Learn optimal extraction patterns
5. **Real-time Updates**: Extract from competition updates

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review plan with team
- [ ] Backup current system state
- [ ] Set up monitoring dashboard
- [ ] Prepare rollback procedures

### During Implementation
- [ ] Follow TDD approach
- [ ] Regular commit checkpoints
- [ ] Continuous integration testing
- [ ] Performance monitoring

### Post-Implementation
- [ ] Validate all success criteria
- [ ] Monitor system for 48 hours
- [ ] Collect user feedback
- [ ] Document lessons learned

---

## Maintenance Notes

### Regular Tasks
- Re-extract when game manual updates
- Monitor extraction quality metrics
- Update extraction prompts based on feedback
- Archive old extractions for comparison

### Troubleshooting Guide
1. **Extraction Fails**: Check OpenAI API status, validate manual format
2. **Poor Quality**: Review extraction prompts, check for manual changes
3. **Performance Issues**: Check cache status, monitor API limits
4. **Integration Problems**: Verify schema compatibility, check versions

---

## Prompt to Start Implementation

```
I need to implement the Game Context Optimization Plan located at /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App/GAME_CONTEXT_OPTIMIZATION_PLAN.md

This plan optimizes how game manual data is processed by extracting only essential information for picklist generation, reducing token usage by 80-90%.

Please start with Phase 1: Infrastructure Setup, following these requirements:
1. Use TDD approach - write tests first
2. Follow the existing service patterns in the codebase
3. Ensure full compatibility with current system
4. Include comprehensive error handling and logging
5. Create the service structure as defined in the plan

Begin by:
1. Creating the game_context_extractor_service.py file
2. Setting up the test framework
3. Implementing the basic service structure with proper typing

Maintain the safety protocols and testing standards defined in CLAUDE.md throughout the implementation.
```

---

## Progress Tracking

### Phase Status
- [ ] Phase 1: Infrastructure Setup
- [ ] Phase 2: Extraction Service Implementation  
- [ ] Phase 3: Integration
- [ ] Phase 4: Testing & Validation
- [ ] Phase 5: Safety & Rollback
- [ ] Phase 6: Documentation & Deployment

### Key Milestones
- [ ] Extraction service created and tested
- [ ] First successful extraction completed
- [ ] Integration tests passing
- [ ] A/B testing shows no quality degradation
- [ ] Production deployment complete

---

*Last Updated: 2025-06-26*  
*Next Review: After Phase 1 completion*