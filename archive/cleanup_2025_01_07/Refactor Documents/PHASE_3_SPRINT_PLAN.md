# Phase 3: Incremental Expansion Sprint Plan

**Version**: 1.0  
**Date**: 2025-06-24  
**Status**: ACTIVE - Ready for execution following Phase 2 success  
**Approach**: Apply proven patterns from Team Comparison canary to additional components

---

## Executive Summary

Phase 3 extends the successful refactoring patterns validated in Phase 2 to additional high-value components. Based on codebase analysis, we've identified optimal targets that share similar characteristics to the Team Comparison workflow:
- Complex monolithic structure (400-700 lines)
- Clear decomposition boundaries
- High business value
- Minimal external dependencies

---

## Component Selection Analysis

### Backend Service Candidates

| Service | Lines | Complexity | Value | Selected |
|---------|-------|------------|-------|----------|
| **sheets_service.py** | 654 | High - Multiple Google API responsibilities | Critical for data ingestion | ✅ Sprint 6 |
| unified_event_data_service.py | 529 | High - Data aggregation complexity | Core data processing | ✅ Sprint 8 |
| archive_service.py | 730 | Medium - File management complexity | Important for data persistence | Future |
| picklist_analysis_service.py | 963 | Very High - Complex GPT integration | Already partially decomposed | Future |

### Frontend Component Candidates

| Component | Lines | Complexity | Value | Selected |
|---------|-------|------------|-------|----------|
| **PicklistGenerator.tsx** | 1440 | Very High - Multiple UI responsibilities | Core user workflow | ✅ Sprint 7 |
| EventArchiveManager.tsx | 699 | High - Complex state management | Important for data management | ✅ Sprint 8 |
| SheetConfigManager.tsx | 588 | Medium - Configuration UI | Critical for setup | Future |
| AllianceSelection.tsx (page) | 1231 | Very High - Complex workflow | Strategic importance | Future |

---

## Sprint 6: Backend Service Refactoring - Sheets Service

**Duration**: 2 days  
**Risk Level**: Medium  
**Target**: `backend/app/services/sheets_service.py` (654 lines)

### Baseline Consultation Protocol

#### **CRITICAL: Start with Baseline Analysis**
Before making any changes, consult the baseline branch to understand original behavior:

```bash
# 1. Extract baseline version for reference
git show baseline:backend/app/services/sheets_service.py > baseline_sheets_service.py

# 2. Analyze baseline characteristics
wc -l baseline_sheets_service.py
grep "class\|def " baseline_sheets_service.py

# 3. Document baseline public interface
grep "def [^_]" baseline_sheets_service.py | head -20

# 4. Identify baseline dependencies
grep "import\|from " baseline_sheets_service.py

# 5. Save baseline analysis for validation
echo "Baseline Analysis - Sprint 6" > sprint6_baseline_analysis.md
echo "File: sheets_service.py" >> sprint6_baseline_analysis.md
echo "Lines: $(wc -l < baseline_sheets_service.py)" >> sprint6_baseline_analysis.md
echo "Public Methods: $(grep -c "def [^_]" baseline_sheets_service.py)" >> sprint6_baseline_analysis.md
```

### Objectives
1. Decompose monolithic Google Sheets service into focused services
2. Separate authentication, data fetching, and data transformation
3. Improve error handling and retry logic
4. **Maintain exact API compatibility with baseline behavior**

### Decomposition Strategy

```
Current Structure (654 lines):
SheetsService
├── Authentication and credential management
├── Google API client initialization
├── Sheet metadata operations
├── Data reading operations
├── Data writing operations
├── Header management
├── Tab validation
├── Error handling and retries
└── Caching logic

Proposed Structure:
SheetsService (orchestrator ~100 lines)
├── GoogleAuthService (authentication & credentials)
├── SheetReaderService (read operations & caching)
├── SheetWriterService (write operations)
├── SheetMetadataService (tabs, headers, validation)
└── RetryService (error handling & retry logic)
```

### Deliverables
```
backend/app/services/
├── sheets_service.py (refactored orchestrator)
├── google_auth_service.py (NEW)
├── sheet_reader_service.py (NEW)
├── sheet_writer_service.py (NEW)
├── sheet_metadata_service.py (NEW)
└── retry_service.py (NEW - reusable for other Google services)
```

### Success Criteria
- [ ] All existing API endpoints continue working identically
- [ ] Google Sheets operations maintain same performance
- [ ] Error handling remains consistent
- [ ] Caching behavior unchanged
- [ ] No breaking changes to dependent services
- [ ] Unit tests for each new service

### Baseline Validation Protocol
#### **Continuous Baseline Comparison**
At each decomposition step, validate against baseline:

```bash
# During refactoring - compare behavior
git diff baseline:backend/app/services/sheets_service.py backend/app/services/sheets_service.py

# Test identical public interface
python -c "
import sys
sys.path.append('.')
from app.services.sheets_service import SheetsService

# Verify same public methods as baseline
service = SheetsService()
methods = [m for m in dir(service) if not m.startswith('_')]
print('Public methods:', len(methods))
print('Methods:', sorted(methods))
"

# End-of-sprint validation
git show baseline:backend/app/services/sheets_service.py | grep "def [^_]" > baseline_methods.txt
grep "def [^_]" backend/app/services/sheets_service.py > current_methods.txt
diff baseline_methods.txt current_methods.txt || echo "Methods changed - REVIEW REQUIRED"
```

### Validation Approach
1. **Baseline Contract Testing**: Compare public interfaces with baseline version
2. **API Endpoint Testing**: Verify same responses as baseline behavior
3. **Integration Testing**: Google Sheets operations identical to baseline
4. **Performance Benchmarking**: Must be within 5% of baseline performance
5. **Error Scenario Testing**: Same error handling as baseline
6. **Cache Behavior Verification**: Identical caching patterns to baseline

---

## Sprint 7: Frontend Component Refactoring - Picklist Generator

**Duration**: 2 days  
**Risk Level**: Medium-High  
**Target**: `frontend/src/components/PicklistGenerator.tsx` (1440 lines)

### Baseline Consultation Protocol

#### **CRITICAL: Start with Baseline Analysis**
Before making any changes, consult the baseline branch to understand original visual and functional behavior:

```bash
# 1. Extract baseline component for reference
git show baseline:frontend/src/components/PicklistGenerator.tsx > baseline_picklist_generator.tsx

# 2. Analyze baseline characteristics
wc -l baseline_picklist_generator.tsx
grep -c "useState\|useEffect" baseline_picklist_generator.tsx
grep -c "className=" baseline_picklist_generator.tsx

# 3. Document baseline component structure
grep "const\|function\|return\|interface" baseline_picklist_generator.tsx | head -30

# 4. Identify baseline props and state
grep -A 5 -B 5 "interface.*Props\|useState<" baseline_picklist_generator.tsx

# 5. Save baseline analysis for validation
echo "Baseline Analysis - Sprint 7" > sprint7_baseline_analysis.md
echo "File: PicklistGenerator.tsx" >> sprint7_baseline_analysis.md
echo "Lines: $(wc -l < baseline_picklist_generator.tsx)" >> sprint7_baseline_analysis.md
echo "State hooks: $(grep -c useState baseline_picklist_generator.tsx)" >> sprint7_baseline_analysis.md
echo "Effect hooks: $(grep -c useEffect baseline_picklist_generator.tsx)" >> sprint7_baseline_analysis.md
echo "CSS classes: $(grep -c className= baseline_picklist_generator.tsx)" >> sprint7_baseline_analysis.md

# 6. Capture baseline visual structure (CSS classes)
grep -o 'className="[^"]*"' baseline_picklist_generator.tsx | sort | uniq > baseline_css_classes.txt
```

### Objectives
1. Decompose the largest frontend component into manageable pieces
2. Separate UI concerns from business logic
3. Extract reusable sub-components
4. **Maintain pixel-perfect visual behavior identical to baseline**

### Decomposition Strategy

```
Current Structure (1440 lines):
PicklistGenerator
├── Complex state management (15+ state variables)
├── Priority builder UI
├── Team display and management
├── Picklist generation logic
├── Real-time progress tracking
├── Analysis results display
├── Comparison modal integration
├── Export functionality
├── Error handling
└── Loading states

Proposed Structure:
PicklistGenerator (orchestrator ~200 lines)
├── PriorityBuilder (metric selection & weighting)
├── TeamListManager (team display & selection)
├── GenerationProgress (real-time status & progress)
├── AnalysisResults (results display & actions)
├── PicklistActions (export, save, compare)
├── usePicklistGeneration (custom hook for API)
└── usePicklistState (state management hook)
```

### Deliverables
```
frontend/src/
├── components/
│   ├── PicklistGenerator.tsx (refactored orchestrator)
│   ├── PriorityBuilder.tsx (NEW)
│   ├── TeamListManager.tsx (NEW)
│   ├── GenerationProgress.tsx (NEW)
│   ├── AnalysisResults.tsx (NEW)
│   └── PicklistActions.tsx (NEW)
├── hooks/
│   ├── usePicklistGeneration.ts (NEW)
│   └── usePicklistState.ts (NEW)
└── utils/
    └── picklistUtils.ts (NEW - shared utilities)
```

### Success Criteria
- [ ] Zero visual changes (pixel-perfect preservation)
- [ ] All interactions work identically
- [ ] State management patterns preserved
- [ ] Team comparison modal integration maintained
- [ ] Performance within 5% of original
- [ ] TypeScript compilation without errors

### Baseline Visual Preservation Protocol
#### **Continuous Visual Validation Against Baseline**

```bash
# During refactoring - validate visual preservation
git diff baseline:frontend/src/components/PicklistGenerator.tsx frontend/src/components/PicklistGenerator.tsx

# CSS class preservation check
grep -o 'className="[^"]*"' frontend/src/components/PicklistGenerator.tsx | sort | uniq > current_css_classes.txt
diff baseline_css_classes.txt current_css_classes.txt || echo "CSS classes changed - VISUAL REGRESSION RISK"

# Props interface preservation
grep -A 10 "interface.*Props" baseline_picklist_generator.tsx > baseline_props.txt
grep -A 10 "interface.*Props" frontend/src/components/PicklistGenerator.tsx > current_props.txt
diff baseline_props.txt current_props.txt || echo "Props interface changed - REVIEW REQUIRED"

# Build validation (must succeed)
npm run build || echo "BUILD FAILED - ABORT REFACTORING"

# State hook count validation (should remain similar)
baseline_hooks=$(grep -c useState baseline_picklist_generator.tsx)
current_hooks=$(grep -c useState frontend/src/components/PicklistGenerator.tsx)
echo "State hooks: baseline=$baseline_hooks, current=$current_hooks"
```

### Visual Preservation Requirements
- **Maintain exact layout grid system** (compare with baseline)
- **Preserve all Tailwind CSS classes** (validate against baseline_css_classes.txt)
- **Keep animation timings identical** (copy from baseline)
- **Maintain responsive breakpoints** (preserve baseline breakpoint classes)
- **Preserve color schemes and theming** (exact color class matching)

---

## Sprint 8: Critical Backend Refactoring - Picklist Generator Service

**Duration**: 3 days  
**Risk Level**: High  
**Target**: `backend/app/services/picklist_generator_service.py` (3,113 lines)

### CRITICAL: Largest Technical Debt in Codebase
This sprint targets the most significant refactoring opportunity in the entire application - a 3,113-line monolithic service that represents 5x the complexity of previously refactored components.

### Baseline Consultation Protocol

#### **CRITICAL: Start with Baseline Analysis**
Before making any changes, consult the baseline branch to understand original behavior:

```bash
# 1. Extract baseline version for reference
git show baseline:backend/app/services/picklist_generator_service.py > baseline_picklist_generator_service.py

# 2. Analyze baseline characteristics
wc -l baseline_picklist_generator_service.py
grep "class\|def " baseline_picklist_generator_service.py | head -30

# 3. Document baseline public interface
grep "def [^_]" baseline_picklist_generator_service.py | head -20

# 4. Identify baseline dependencies
grep "import\|from " baseline_picklist_generator_service.py

# 5. Save baseline analysis for validation
echo "Baseline Analysis - Sprint 8" > sprint8_baseline_analysis.md
echo "File: picklist_generator_service.py" >> sprint8_baseline_analysis.md
echo "Lines: $(wc -l < baseline_picklist_generator_service.py)" >> sprint8_baseline_analysis.md
echo "Public Methods: $(grep -c "def [^_]" baseline_picklist_generator_service.py)" >> sprint8_baseline_analysis.md
echo "Classes: $(grep -c "^class " baseline_picklist_generator_service.py)" >> sprint8_baseline_analysis.md
```

### Objectives
1. Decompose 3,113-line monolithic service into 6-8 focused services
2. **Preserve ALL API contracts exactly as baseline**
3. Maintain identical performance within 5% of baseline
4. **Maintain exact functional behavior vs baseline**

### Decomposition Strategy

```
Current Structure (3,113 lines):
PicklistGeneratorService
├── Complex GPT integration logic
├── Batch processing management
├── Team analysis algorithms
├── Priority calculation engine
├── Data aggregation logic
├── Performance optimization
├── Error handling and retries
├── Caching and persistence
└── Result formatting

Proposed Structure:
PicklistGeneratorService (orchestrator ~200 lines)
├── GPTAnalysisService (GPT integration & prompts)
├── BatchProcessingService (batch management & progress)
├── TeamAnalysisService (team evaluation algorithms)
├── PriorityCalculationService (scoring & ranking logic)
├── DataAggregationService (data collection & preparation)
├── PerformanceOptimizationService (caching & optimization)
├── MetricsExtractionService (ALREADY EXISTS - integrate)
└── RetryService (ALREADY EXISTS - reuse from sheets refactor)
```

### Deliverables
```
backend/app/services/
├── picklist_generator_service.py (refactored orchestrator)
├── gpt_analysis_service.py (ALREADY EXISTS - enhance)
├── batch_processing_service.py (NEW)
├── team_analysis_service.py (NEW)
├── priority_calculation_service.py (NEW)
├── data_aggregation_service.py (NEW)
├── performance_optimization_service.py (NEW)
├── metrics_extraction_service.py (ALREADY EXISTS - integrate)
└── retry_service.py (ALREADY EXISTS - reuse)
```

### Success Criteria
- [ ] All existing API endpoints continue working identically to baseline
- [ ] Picklist generation performance within 5% of baseline
- [ ] GPT integration behavior unchanged from baseline
- [ ] Batch processing patterns preserved exactly
- [ ] No breaking changes to dependent services (frontend components)
- [ ] Error handling remains consistent with baseline
- [ ] Caching behavior identical to baseline

### Baseline Validation Protocol
#### **Continuous Baseline Comparison**
At each decomposition step, validate against baseline:

```bash
# During refactoring - compare behavior
git diff baseline:backend/app/services/picklist_generator_service.py backend/app/services/picklist_generator_service.py

# Test identical public interface
python -c "
import sys
sys.path.append('.')
from app.services.picklist_generator_service import PicklistGeneratorService

# Verify same public methods as baseline
service = PicklistGeneratorService()
methods = [m for m in dir(service) if not m.startswith('_')]
print('Public methods:', len(methods))
print('Methods:', sorted(methods))
"

# End-of-sprint validation
git show baseline:backend/app/services/picklist_generator_service.py | grep "def [^_]" > baseline_methods.txt
grep "def [^_]" backend/app/services/picklist_generator_service.py > current_methods.txt
diff baseline_methods.txt current_methods.txt || echo "Methods changed - REVIEW REQUIRED"
```

### Validation Approach
1. **Baseline Contract Testing**: Compare public interfaces with baseline version
2. **API Endpoint Testing**: Verify same responses as baseline behavior
3. **Picklist Generation Testing**: Identical results to baseline
4. **Performance Benchmarking**: Must be within 5% of baseline performance
5. **GPT Integration Testing**: Same prompts and processing as baseline
6. **Batch Processing Verification**: Identical batch patterns to baseline

---

## Risk Assessment & Mitigation

### Identified Risks from Phase 2 Experience

1. **Service Dependencies**
   - **Risk**: Sheets service has many dependent services
   - **Mitigation**: Careful interface preservation, extensive integration testing

2. **Component Complexity**
   - **Risk**: PicklistGenerator is 2.4x larger than TeamComparison
   - **Mitigation**: More granular decomposition, additional validation time

3. **State Management**
   - **Risk**: Complex state interactions in PicklistGenerator
   - **Mitigation**: Centralized state pattern proven in Phase 2

4. **Performance Impact**
   - **Risk**: Additional service boundaries may affect performance
   - **Mitigation**: Benchmark continuously, optimize service communication

### Abort Conditions

**Stop Sprint 6 If**:
- Google Sheets API integration breaks
- Performance degradation >10%
- Authentication failures

**Stop Sprint 7 If**:
- Any visual regression detected
- State management corruption
- Team comparison integration fails

**Stop Sprint 8 If**:
- Sprint 6 or 7 validations fail
- User reports critical issues
- Performance unacceptable

---

## Success Metrics

### Sprint Success Criteria
- **Code Quality**: 50-70% complexity reduction per component
- **Visual Preservation**: 100% (zero changes)
- **Functional Preservation**: 100%
- **Performance**: Within 5% of baseline
- **Test Coverage**: Increase by 20%+

### Phase 3 Overall Success
- **Minimum**: 2 components successfully refactored
- **Target**: 4 components improved
- **Stretch**: Second service pair completed

---

## Execution Timeline

### Week 1
- **Day 1-2**: Sprint 6 - Sheets Service refactoring
- **Day 3-4**: Sprint 7 - PicklistGenerator refactoring
- **Day 5**: Sprint 8 Part A - Integration validation

### Week 2 (If Approved)
- **Day 1**: Sprint 8 Part B - Second service pair
- **Day 2**: Final validation and documentation

---

## Baseline Consultation Checklist

### Pre-Sprint Checklist (All Sprints)
- [ ] Extract baseline files using `git show baseline:...`
- [ ] Document baseline characteristics (lines, methods, interfaces)
- [ ] Analyze baseline dependencies and public contracts
- [ ] Create baseline analysis document for sprint
- [ ] Capture baseline performance metrics where applicable

### During-Sprint Checklist (All Sprints)
- [ ] Compare current work with baseline using `git diff baseline:...`
- [ ] Validate public interfaces match baseline exactly
- [ ] Preserve all baseline behavior patterns
- [ ] Test against baseline error scenarios
- [ ] Maintain baseline performance characteristics

### End-of-Sprint Checklist (All Sprints)
- [ ] Final comparison against baseline interfaces
- [ ] Validate no breaking changes from baseline
- [ ] Document any discoveries about baseline behavior
- [ ] Confirm baseline contract preservation
- [ ] Update session intent with baseline validation results

---

## Claude Code Prompts

### Sprint 6 Prompt
```
Execute Sprint 6: Backend Service Refactoring - Sheets Service.
Follow PHASE_3_SPRINT_PLAN.md for detailed requirements.
Target: backend/app/services/sheets_service.py

CRITICAL REQUIREMENTS:
- START by extracting baseline version: git show baseline:backend/app/services/sheets_service.py
- Document baseline characteristics before any changes
- Decompose into 5 focused services per plan
- Preserve ALL Google Sheets API functionality exactly (validate against baseline)
- Maintain authentication and caching behavior identical to baseline
- Zero breaking changes to dependent services
- Create comprehensive integration tests
- Continuously compare against baseline during refactoring
```

### Sprint 7 Prompt
```
Execute Sprint 7: Frontend Component Refactoring - PicklistGenerator.
Follow PHASE_3_SPRINT_PLAN.md for detailed requirements.
Target: frontend/src/components/PicklistGenerator.tsx

CRITICAL REQUIREMENTS:
- START by extracting baseline version: git show baseline:frontend/src/components/PicklistGenerator.tsx
- Document baseline visual structure (CSS classes, props, state)
- Decompose into 6+ focused components per plan
- ZERO visual changes - pixel-perfect preservation vs baseline required
- Maintain all state management patterns identical to baseline
- Preserve Team Comparison modal integration (already refactored)
- Extract custom hooks for logic separation
- Validate CSS classes and props interfaces against baseline continuously
```

### Sprint 8 Prompt
```
Execute Sprint 8: Critical Backend Refactoring - Picklist Generator Service.
Follow MASTER_REFACTORING_GUIDE.md and CONTEXT_WINDOW_PROTOCOL.md for detailed requirements.
Target: backend/app/services/picklist_generator_service.py (3,113 lines)

CRITICAL REQUIREMENTS:
- Reference baseline branch for all original code
- Create session intent document for context preservation
- Validate all changes preserve exact baseline behavior
- Document decisions for next context window

MANDATORY DOCUMENTATION REQUIREMENTS:
- Create session intent document BEFORE starting any work
- Document baseline analysis with all preserved behaviors
- Create service decomposition strategy for the 3,113-line service
- Document all API contracts and preservation guarantees
- Create comprehensive validation report
- Complete handoff checklist for next session

BASELINE PRESERVATION:
- START by extracting baseline version: git show baseline:backend/app/services/picklist_generator_service.py
- Document baseline characteristics before any changes
- Decompose into 6-8 focused services per plan
- Preserve ALL picklist generation functionality exactly (validate against baseline)
- Maintain GPT integration and batch processing behavior identical to baseline
- Zero breaking changes to dependent services (frontend components)
- Create comprehensive integration tests
- Continuously compare against baseline during refactoring

TARGET DECOMPOSITION:
- GPTAnalysisService (GPT integration & prompts)
- BatchProcessingService (batch management & progress)
- TeamAnalysisService (team evaluation algorithms)
- PriorityCalculationService (scoring & ranking logic)
- DataAggregationService (data collection & preparation)
- PerformanceOptimizationService (caching & optimization)
- Integrate existing MetricsExtractionService
- Reuse existing RetryService from sheets refactor
```

---

## Notes for Future Phases

Based on Phase 3 execution, consider for Phase 4:
1. **Page Components**: AllianceSelection, Setup, PicklistNew
2. **Complex Services**: picklist_analysis_service, picklist_generator_service
3. **Architectural Patterns**: Consider introducing design patterns like Repository, Factory
4. **Cross-Cutting Concerns**: Logging, caching, error handling standardization

---

**This plan provides the detailed structure missing from the Master Refactoring Guide, enabling confident execution of Phase 3.**