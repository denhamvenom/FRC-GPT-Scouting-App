# FRC GPT Scouting App - Frontend Migration Completion Plan

## Plan Status and Progress Tracking

### Current Status
- **Overall Progress**: 0.0% (0/6 sprints completed)
- **Current Phase**: Migration Phase - API Client Integration (**NOT STARTED**)
- **Priority**: **CRITICAL** - Addressing incomplete Phase 3 Frontend Refactoring
- **Created**: 2025-06-10
- **Created By**: Claude Code - Migration Analysis
- **Purpose**: Complete the unfinished API client migration and legacy code cleanup from Phase 3

### Migration Summary
| Sprint | Focus Area | Estimated Tokens | Files Modified | Status |
|--------|------------|------------------|----------------|---------|
| M.1 | API Client Migration (Core Components) | ~120K | 8 files | Not Started |
| M.2 | API Client Migration (Remaining Components) | ~140K | 12 files | Not Started |
| M.3 | Legacy Endpoint Cleanup | ~80K | 6 files | Not Started |
| M.4 | Complete Component Refactoring | ~160K | 15 files | Not Started |
| M.5 | Environment & Configuration | ~100K | 8 files | Not Started |
| M.6 | Integration Testing & Validation | ~120K | 10 files | Not Started |
| **Total** | **Migration Completion** | **~720K** | **59 files** | **0% Complete** |

## Quick Start for New Context Windows

### For Continuing Migration Work
```bash
# 1. Read this file to understand current migration status
# 2. Check the "Sprint Status Tracking" section below
# 3. Find the next sprint to execute (status: "Ready" or "In Progress")
# 4. Review sprint deliverables and required changes
# 5. Execute sprint following the detailed specifications
# 6. Update this file with progress and results
# 7. Ask user to continue before moving to next Sprint
```

### Key Context Files
- `REFACTORING_PLAN.md` - Original refactoring context and what was "completed"
- `frontend/src/services/` - API client infrastructure (created but not used)
- `frontend/src/providers/ApiProvider.tsx` - Centralized API provider
- Files with hardcoded URLs - Primary migration targets

---

## Executive Summary

**CRITICAL ISSUE**: Phase 3 Frontend Refactoring was marked as "COMPLETED ✅" but the core API client migration was never executed. This resulted in:

- **10+ components** still using hardcoded `http://localhost:8000` URLs
- **Legacy endpoints** being called instead of modern API services
- **Connection issues** due to bypassing proper API infrastructure
- **Inconsistent error handling** across the application

## Root Cause Analysis

### What Was Actually Completed in Phase 3:
✅ **Sprint 3.1-3.2**: Component decomposition (AllianceSelection, Picklist)  
✅ **Sprint 3.3**: API client infrastructure **created** (but not used)  
✅ **Sprint 3.4-3.5**: Common components and state management  
✅ **Sprint 3.6**: Some page refactoring (incomplete)

### What Was NEVER Completed:
❌ **Critical**: Migration of existing components to use API client  
❌ **Critical**: Removal of hardcoded localhost URLs  
❌ **Critical**: Legacy endpoint cleanup  
❌ **Critical**: End-to-end testing of new API structure  
❌ **Critical**: Complete component modularization

---

## Sprint Status Tracking

### Sprint M.1: API Client Migration (Core Components)
- **Status**: Ready
- **Estimated Tokens**: ~120K
- **Files to Modify**: 8 files
- **Priority**: CRITICAL
- **Dependencies**: None
- **Started**: Not started
- **Completed**: Not completed

**Target Components** (High Traffic/Critical):
- `EventArchiveManager.tsx` - 6 hardcoded URLs
- `PicklistGenerator.tsx` - 6 hardcoded URLs
- `SheetConfigManager.tsx` - 4 hardcoded URLs
- `ProgressTracker.tsx` - 1 hardcoded URL
- `TeamComparisonModal.tsx` - 1 hardcoded URL

**Deliverables:**
```
frontend/src/components/
├── EventArchiveManager.tsx       # Convert to use EventService
├── PicklistGenerator.tsx         # Convert to use PicklistService  
├── SheetConfigManager.tsx        # Convert to use proper API client
├── ProgressTracker.tsx           # Convert to use generic API client
└── TeamComparisonModal.tsx       # Convert to use PicklistService

Updated imports and service usage:
- Replace all fetch() calls with service methods
- Add proper error handling through API client
- Use centralized base URL configuration
- Implement proper loading states
```

**Migration Pattern:**
```typescript
// OLD - Direct fetch with hardcoded URL
const response = await fetch('http://localhost:8000/api/archive/list');

// NEW - Use service with proper error handling
const { eventService } = useApiContext();
const archives = await eventService.listArchives();
```

**AI Session Focus:**
- Identify all hardcoded URL patterns in each component
- Replace with appropriate service calls from existing API services
- Maintain exact same functionality while using proper infrastructure
- Add proper error handling and loading states
- Test that all existing features continue to work

**Validation Criteria:**
- ✅ No hardcoded `localhost:8000` URLs remain in target files
- ✅ All API calls go through centralized services
- ✅ Error handling works consistently
- ✅ Loading states properly managed
- ✅ Existing functionality preserved

---

### Sprint M.2: API Client Migration (Remaining Components)
- **Status**: Blocked (depends on M.1)
- **Estimated Tokens**: ~140K
- **Files to Modify**: 12 files
- **Priority**: CRITICAL
- **Dependencies**: Sprint M.1
- **Started**: Not started
- **Completed**: Not completed

**Target Components** (Remaining):
- `pages/AllianceSelection/hooks/useAllianceSelection.ts` - hardcoded base URL
- `pages/FieldSelection/hooks/useFieldSelection.ts` - all localhost URLs (ALREADY PARTIALLY FIXED)
- `pages/Setup/hooks/useSetup.ts` - setup API calls
- `pages/Setup/hooks/useEventData.ts` - event data management
- `pages/Validation/hooks/useValidation.ts` - validation endpoints
- `pages/PicklistView/hooks/usePicklistView.ts` - picklist operations
- `pages/SchemaMapping/hooks/useSchemaMapping.ts` - schema operations
- `pages/UnifiedDatasetBuilder.tsx` - dataset building
- `pages/Workflow.tsx` - workflow management
- `pages/SchemaSuperMapping.tsx` - super scouting schema
- `pages/Home.tsx` - home page API calls
- Any other discovered hardcoded URLs

**Deliverables:**
```
frontend/src/pages/
├── AllianceSelection/hooks/useAllianceSelection.ts  # Use AllianceService
├── Setup/hooks/
│   ├── useSetup.ts                                  # Use EventService
│   └── useEventData.ts                              # Use EventService
├── Validation/hooks/useValidation.ts                # Use ValidationService
├── PicklistView/hooks/usePicklistView.ts            # Use PicklistService
├── SchemaMapping/hooks/useSchemaMapping.ts          # Use API client
├── UnifiedDatasetBuilder.tsx                        # Use DatasetService
├── Workflow.tsx                                     # Use appropriate services
├── SchemaSuperMapping.tsx                           # Use API client
└── Home.tsx                                         # Use appropriate services

Service Integration:
- Update all hooks to use injected API services
- Replace direct fetch calls with service methods
- Implement consistent error handling patterns
- Add proper TypeScript typing for all API interactions
```

**Migration Strategy:**
```typescript
// Pattern 1: Hook using useApiContext
const { validationService } = useApiContext();
const result = await validationService.validateDataset(request);

// Pattern 2: Hook with proper error handling
const { isLoading, error, data, execute } = useApiCall(
  () => datasetService.buildDataset(config),
  { immediate: false }
);
```

**AI Session Focus:**
- Complete migration of all remaining components with hardcoded URLs
- Ensure consistent API client usage patterns across all hooks
- Implement proper error boundary integration
- Add loading state management through existing hook infrastructure
- Verify no direct fetch calls remain anywhere in codebase

**Validation Criteria:**
- ✅ Zero hardcoded `localhost` URLs in entire frontend codebase
- ✅ All API calls use centralized service layer
- ✅ Consistent error handling patterns
- ✅ Proper loading state management
- ✅ TypeScript compilation passes without warnings

---

### Sprint M.3: Legacy Endpoint Cleanup
- **Status**: Blocked (depends on M.2)
- **Estimated Tokens**: ~80K
- **Files to Modify**: 6 files
- **Priority**: HIGH
- **Dependencies**: Sprint M.2
- **Started**: Not started
- **Completed**: Not completed

**Legacy Endpoints to Remove:**
```python
# Backend endpoints that should be removed:
@app.get("/api/unified/status")          # Legacy unified status
@app.post("/api/unified/build")          # Legacy unified build
@router.get("/enhanced")                 # Legacy enhanced validation
@router.get("/todo-list")               # Legacy todo list
@router.get("/preview-virtual-scout")   # Legacy virtual scout preview
```

**Frontend Legacy References to Remove:**
```typescript
// Remove any remaining calls to:
'/api/unified/status?event_key=...'
'/api/unified/build'
'/api/validate/enhanced?unified_dataset_path=...'
'/api/validate/todo-list?unified_dataset_path=...'
'/api/validate/preview-virtual-scout'
```

**Deliverables:**
```
backend/app/
├── main.py                              # Remove legacy endpoint definitions
└── api/validate.py                      # Remove legacy validation endpoints

frontend/src/
├── [Search all files for legacy endpoint references]
├── [Update any found references to use new API structure]
└── [Remove any unused legacy code]

Documentation Updates:
├── Update API documentation to reflect removed endpoints
├── Update any remaining references in comments
└── Clean up any orphaned legacy utility functions
```

**Search and Destroy Pattern:**
```bash
# Comprehensive search for legacy patterns:
grep -r "unified/status" frontend/src/
grep -r "unified/build" frontend/src/
grep -r "validate/enhanced" frontend/src/
grep -r "validate/todo-list" frontend/src/
grep -r "preview-virtual-scout" frontend/src/
```

**AI Session Focus:**
- Systematically search for and remove all legacy endpoint references
- Ensure replacement endpoints exist and are being used correctly
- Remove orphaned legacy code and utilities
- Update any remaining documentation or comments
- Verify backend endpoints can be safely removed

**Validation Criteria:**
- ✅ No references to legacy endpoints in frontend code
- ✅ Legacy backend endpoints successfully removed
- ✅ All functionality works with new API structure
- ✅ No orphaned legacy utility functions remain
- ✅ Documentation updated to reflect changes

---

### Sprint M.4: Complete Component Refactoring
- **Status**: Blocked (depends on M.3)
- **Estimated Tokens**: ~160K
- **Files to Create**: 15 files
- **Priority**: MEDIUM
- **Dependencies**: Sprint M.3
- **Started**: Not started
- **Completed**: Not completed

**Missing Modular Structures to Create:**

**1. UnifiedDatasetBuilder Modularization:**
```
frontend/src/pages/UnifiedDatasetBuilder/
├── UnifiedDatasetBuilder.tsx     # Main container (~150 lines, down from 278)
├── types.ts                      # TypeScript definitions
├── hooks/
│   ├── useDatasetBuilder.ts      # Dataset building logic
│   ├── useBuildProgress.ts       # Build progress tracking
│   └── useDatasetStatus.ts       # Dataset status management
└── components/
    ├── BuildConfiguration.tsx    # Build config UI
    ├── BuildProgress.tsx         # Progress display
    ├── DatasetPreview.tsx        # Dataset preview
    └── BuildActions.tsx          # Action controls
```

**2. PicklistView Component Completion:**
```
frontend/src/pages/PicklistView/
├── components/                   # Missing component implementations
│   ├── PicklistTable.tsx         # Team listing with ranking
│   ├── PicklistFilters.tsx       # Filtering and search
│   ├── PicklistActions.tsx       # Export, edit, lock actions
│   ├── TeamDetailsModal.tsx      # Individual team details
│   └── ComparisonView.tsx        # Team comparison interface
└── index.ts                      # Component exports
```

**3. Remaining Large File Refactoring:**
```
frontend/src/pages/
├── Setup.tsx                     # 586 lines → modular structure
├── Validation.tsx                # Should be fully modular
├── SchemaMapping.tsx             # 412 lines → modular structure
└── SchemaSuperMapping.tsx        # Should be modular
```

**AI Session Focus:**
- Break down large monolithic components into focused, single-responsibility modules
- Create proper hook abstractions for complex business logic
- Implement reusable UI components following established patterns
- Ensure consistent TypeScript typing throughout
- Maintain backward compatibility with existing page routes

**Validation Criteria:**
- ✅ All target files under 200 lines
- ✅ Clear separation of concerns between components
- ✅ Proper hook abstractions for business logic
- ✅ Consistent component patterns with Phase 3 work
- ✅ Full TypeScript compliance

---

### Sprint M.5: Environment & Configuration Standardization
- **Status**: Blocked (depends on M.4)
- **Estimated Tokens**: ~100K
- **Files to Modify**: 8 files
- **Priority**: MEDIUM
- **Dependencies**: Sprint M.4
- **Started**: Not started
- **Completed**: Not completed

**Environment Configuration Issues:**
- Different behavior in development vs production
- Hardcoded localhost assumptions
- Missing environment variable handling
- Inconsistent proxy configuration

**Deliverables:**
```
frontend/
├── .env.example                  # Environment variable template
├── .env.development              # Development-specific config
├── .env.production               # Production-specific config
├── vite.config.ts                # Enhanced with environment handling
└── src/
    ├── config/
    │   ├── environment.ts        # Environment detection and config
    │   ├── api-config.ts         # API endpoint configuration
    │   └── constants.ts          # Application constants
    └── providers/
        └── ApiProvider.tsx       # Updated with environment config

docker-compose.yml                # Enhanced with proper networking
README.md                         # Updated setup instructions
```

**Environment Configuration Pattern:**
```typescript
// New environment-aware API configuration
const getApiConfig = () => {
  if (import.meta.env.MODE === 'development') {
    return {
      baseURL: '/api', // Uses Vite proxy
      timeout: 30000,
    };
  }
  
  return {
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: import.meta.env.VITE_API_TIMEOUT || 30000,
  };
};
```

**AI Session Focus:**
- Create comprehensive environment configuration system
- Ensure proper development vs production API handling
- Add Docker networking optimization
- Create clear setup documentation
- Test configuration in different deployment scenarios

**Validation Criteria:**
- ✅ Works correctly in development with proxy
- ✅ Works correctly in production with proper base URLs
- ✅ Docker networking properly configured
- ✅ Environment variables properly documented
- ✅ No hardcoded environment assumptions

---

### Sprint M.6: Integration Testing & Validation
- **Status**: Blocked (depends on M.5)
- **Estimated Tokens**: ~120K
- **Files to Create**: 10 files
- **Priority**: CRITICAL
- **Dependencies**: Sprint M.5
- **Started**: Not started
- **Completed**: Not completed

**Comprehensive Testing Requirements:**

**1. API Integration Tests:**
```
frontend/src/__tests__/integration/
├── api-migration.test.tsx        # Test all migrated API calls
├── component-integration.test.tsx # Test component interactions
├── error-handling.test.tsx       # Test error scenarios
└── performance.test.tsx          # Test performance implications
```

**2. End-to-End Workflow Tests:**
```
frontend/src/__tests__/e2e/
├── field-selection-flow.test.tsx # Complete field selection workflow
├── picklist-generation.test.tsx  # Complete picklist workflow
├── alliance-selection.test.tsx   # Complete alliance selection
└── data-validation.test.tsx      # Complete validation workflow
```

**3. Migration Validation Script:**
```
scripts/
├── validate-migration.js         # Comprehensive migration validation
├── api-endpoint-check.js         # Verify no legacy endpoints called
└── performance-comparison.js     # Before/after performance metrics
```

**Validation Checklist:**
```typescript
interface MigrationValidation {
  // API Integration
  noHardcodedUrls: boolean;
  allApiCallsUseServices: boolean;
  errorHandlingConsistent: boolean;
  
  // Performance
  noPerformanceRegression: boolean;
  cacheStrategyWorking: boolean;
  
  // Functionality
  allFeaturesWorking: boolean;
  noNewBugs: boolean;
  
  // Architecture
  componentModularityAchieved: boolean;
  typeScriptCompliance: boolean;
}
```

**AI Session Focus:**
- Create comprehensive test suite covering all migrated functionality
- Validate that every component works correctly with new API infrastructure
- Performance testing to ensure no regressions
- End-to-end testing of complete user workflows
- Documentation of test results and any remaining issues

**Validation Criteria:**
- ✅ All integration tests pass
- ✅ No performance regressions detected
- ✅ All original functionality preserved
- ✅ Error handling working consistently
- ✅ Complete user workflows tested successfully

---

## Sprint Execution Guidelines

### Pre-Sprint Preparation
1. **Context Review**: Read this migration plan and understand current state
2. **File Analysis**: Examine target files to understand current implementation
3. **Dependency Check**: Ensure previous sprint work is complete
4. **Service Inventory**: Understand available API services and their methods

### During Sprint Execution
1. **Pattern Consistency**: Follow established migration patterns exactly
2. **Functionality Preservation**: Maintain exact same user-facing functionality
3. **Error Handling**: Implement proper error handling through API client
4. **Testing**: Test each change immediately after implementation

### Post-Sprint Validation
1. **No Hardcoded URLs**: Verify no `localhost:8000` URLs remain
2. **Service Usage**: Confirm all API calls use centralized services
3. **Error Testing**: Test error scenarios work correctly
4. **Integration Testing**: Verify component still works with rest of application

### Sprint Completion Checklist
- [ ] All deliverables implemented as specified
- [ ] No hardcoded URLs in modified files
- [ ] All API calls use proper service layer
- [ ] Error handling works consistently
- [ ] Existing functionality preserved
- [ ] TypeScript compilation passes
- [ ] Manual testing completed
- [ ] This file updated with progress

---

## Migration Patterns and Best Practices

### API Service Usage Pattern
```typescript
// Standard pattern for component migration
import { useApiContext } from '../providers/ApiProvider';
import { useAsync } from '../hooks/useAsync';

const MyComponent = () => {
  const { picklistService } = useApiContext();
  
  const {
    data: picklists,
    loading,
    error,
    execute: loadPicklists
  } = useAsync(
    () => picklistService.getPicklists(),
    { immediate: true }
  );
  
  // Component implementation...
};
```

### Error Handling Pattern
```typescript
// Consistent error handling through API client
const handleApiCall = async () => {
  try {
    const result = await service.method(params);
    setData(result);
  } catch (error) {
    // Error is already processed by API client interceptors
    // Additional component-specific handling if needed
    setLocalError(error.message);
  }
};
```

### Loading State Pattern
```typescript
// Use existing loading state infrastructure
const { isLoading, error, data, execute } = useApiCall(
  () => service.operation(params),
  { 
    immediate: false,
    onSuccess: (result) => handleSuccess(result),
    onError: (error) => handleError(error)
  }
);
```

---

## Success Metrics

### Per Sprint
- **Zero Hardcoded URLs**: No `localhost:8000` references in modified files
- **Service Integration**: All API calls use centralized service layer
- **Functionality Preservation**: All existing features continue to work
- **Error Handling**: Consistent error handling patterns implemented

### Overall Migration
- **Complete API Integration**: 100% of components use API client infrastructure
- **Legacy Code Elimination**: No legacy endpoints or hardcoded URLs remain
- **Performance Maintenance**: No performance regressions introduced
- **Architecture Consistency**: All components follow established patterns

---

## Risk Assessment and Mitigation

### High-Risk Areas
1. **Complex Components**: Large components with multiple API interactions
2. **Error Handling**: Ensuring error scenarios continue to work correctly
3. **State Management**: Maintaining existing state patterns during migration
4. **Dependencies**: Components that depend on multiple services

### Mitigation Strategies
1. **Incremental Migration**: One component at a time with full testing
2. **Functionality Tests**: Comprehensive testing after each change
3. **Rollback Plan**: Keep track of original implementations
4. **User Validation**: Test real user workflows after migration

---

## Notes and Lessons Learned

### From Previous Refactoring Issues
- **Incomplete Migration**: Phase 3 created infrastructure but didn't migrate existing code
- **Documentation vs Reality**: Marked as complete when only partially done
- **Testing Gap**: Lack of end-to-end testing revealed issues late

### Best Practices for This Migration
- **Validate Early**: Test each component immediately after migration
- **Document Reality**: Only mark sprints as complete when fully tested
- **User Focus**: Maintain exact same user experience throughout migration
- **Integration Testing**: Test component interactions, not just individual components

---

## How to Update This File

### For Sprint Progress
1. Update sprint status (`Ready` → `In Progress` → `Completed`)
2. Add start/completion dates
3. Document any issues encountered and solutions
4. Update overall progress percentage
5. Note any deviations from planned approach

### For Context Window Handoffs
1. Document current state of migration work
2. Note any discoveries about codebase structure
3. Update file modification lists if needed
4. Record any new dependencies or blockers discovered

### Example Progress Update
```markdown
### Sprint M.1: API Client Migration (Core Components)
- **Status**: Completed ✅
- **Started**: 2025-06-10
- **Completed**: 2025-06-10
- **Notes**: 
  - Successfully migrated all 5 core components
  - Removed 18 hardcoded localhost URLs
  - All functionality preserved and tested
  - Error handling working correctly through API client
  - Ready for Sprint M.2
```