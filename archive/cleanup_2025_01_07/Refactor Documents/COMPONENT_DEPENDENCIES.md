# Component Dependencies Mapping

This document maps all component dependencies and prop flow patterns in the original FRC GPT Scouting App. This serves as a preservation reference during refactoring to ensure component relationships remain intact.

**Created**: 2025-06-12  
**Source**: Component interface analysis from original codebase  
**Purpose**: Prevent component dependency breakage during refactoring efforts

---

## Dependency Graph Overview

```
App (Router)
├── Navbar
└── Page Components
    ├── Home (no dependencies)
    ├── Setup
    │   ├── EventArchiveManager
    │   └── SheetConfigManager  
    ├── FieldSelection
    │   └── CategoryTabs
    ├── Validation (no child components)
    ├── PicklistNew
    │   ├── PicklistGenerator
    │   │   ├── ProgressIndicator
    │   │   ├── BatchProgressIndicator
    │   │   ├── MissingTeamsModal
    │   │   └── TeamComparisonModal
    │   └── ProgressTracker
    ├── AllianceSelection (no child components)
    ├── PicklistView
    │   └── PicklistGenerator (shared component)
    ├── UnifiedDatasetBuilder
    │   └── ProgressTracker (shared component)
    └── Other Pages (no child components)
```

---

## Detailed Component Dependencies

### 1. Application Root Level

#### App.tsx
- **Role**: Root routing component
- **Dependencies**: 
  - React Router (`BrowserRouter`, `Routes`, `Route`)
  - All page components
  - Navbar component
- **Props Passed**: None (routing only)
- **State Management**: None (stateless router)

#### Navbar.tsx
- **Role**: Global navigation
- **Dependencies**: 
  - React Router (`Link`, `useLocation`)
- **Props Received**: None
- **State Management**: None (uses location hook)

---

### 2. Page Component Dependencies

#### Home.tsx
- **Role**: Landing page with navigation cards
- **Child Components**: None
- **Props Passed**: N/A
- **State Dependencies**:
  - `health: string` (from `/api/health`)
  - `eventInfo: EventInfo` (from `/api/setup/info`)
- **Navigation**: Links to all other pages via React Router

#### Setup.tsx
- **Role**: Multi-step setup wizard
- **Child Components**:
  1. **EventArchiveManager**
  2. **SheetConfigManager**
- **Props Passed to Children**:
  ```typescript
  // To EventArchiveManager
  {
    currentEventKey?: string,
    currentYear?: number,
    onArchiveSuccess?: () => void,
    onRestoreSuccess?: () => void
  }
  
  // To SheetConfigManager
  {
    currentEventKey?: string,
    currentYear?: number,
    onConfigurationChange?: () => void,
    onConfigurationConfirmed?: () => void
  }
  ```
- **State Management**: Complex multi-step state with step tracking

#### FieldSelection.tsx
- **Role**: Field categorization interface
- **Child Components**:
  1. **CategoryTabs**
- **Props Passed to CategoryTabs**:
  ```typescript
  {
    categories: Category[],                 // Static category definitions
    activeCategory: string,                 // Current active tab
    onCategoryChange: (categoryId: string) => void,  // Tab change handler
    countsPerCategory?: Record<string, number>,      // Field counts per category
    totalCount?: number                     // Total field count
  }
  ```
- **State Dependencies**: Headers from multiple Google Sheets tabs

#### PicklistNew.tsx
- **Role**: Primary picklist generation interface
- **Child Components**:
  1. **PicklistGenerator** (main component)
  2. **ProgressTracker**
- **Props Passed to PicklistGenerator**:
  ```typescript
  {
    datasetPath: string,                    // Path to unified dataset
    yourTeamNumber: number,                 // User's team number
    pickPosition: "first" | "second" | "third",  // Current pick position
    priorities: MetricPriority[],           // Metric priorities for position
    allPriorities?: {                       // All priorities for exclusions
      first: MetricPriority[],
      second: MetricPriority[],
      third: MetricPriority[]
    },
    excludeTeams?: number[],                // Teams excluded from ranking
    onPicklistGenerated?: (result: PicklistResult) => void,  // Success callback
    initialPicklist?: Team[],               // Pre-existing picklist
    onExcludeTeam?: (teamNumber: number) => void,  // Exclude team callback
    isLocked?: boolean,                     // Whether picklist is locked
    onPicklistCleared?: () => void          // Clear picklist callback
  }
  ```
- **Props Passed to ProgressTracker**:
  ```typescript
  {
    operationId: string,                    // Operation ID for tracking
    onComplete?: (success: boolean) => void, // Completion callback
    pollingInterval?: number                // Polling interval (default 1000ms)
  }
  ```
- **State Management**: Complex state with localStorage persistence for all priority arrays

---

### 3. Shared Component Dependencies

#### PicklistGenerator.tsx
- **Role**: Core picklist generation logic (used by PicklistNew and PicklistView)
- **Child Components**:
  1. **ProgressIndicator** (custom progress bar)
  2. **BatchProgressIndicator** (batch processing progress)
  3. **MissingTeamsModal** (modal for teams missing from dataset)
  4. **TeamComparisonModal** (AI-powered team comparison)
- **Props Passed to TeamComparisonModal**:
  ```typescript
  {
    isOpen: boolean,                        // Modal visibility
    onClose: () => void,                    // Close modal callback
    teamNumbers: number[],                  // Teams to compare
    datasetPath: string,                    // Dataset path
    yourTeamNumber: number,                 // User's team number
    prioritiesMap: PrioritiesMap,           // All priorities mapping
    onApply: (teams: Team[]) => void        // Apply reordering callback
  }
  ```
- **State Management**: Complex generation state with pagination and progress tracking

#### ProgressTracker.tsx
- **Role**: Operation progress tracking (used by PicklistNew and UnifiedDatasetBuilder)
- **Child Components**: None
- **Props Interface**:
  ```typescript
  {
    operationId: string,                    // Required: Operation ID
    onComplete?: (success: boolean) => void, // Optional: Completion callback
    pollingInterval?: number                // Optional: Polling interval
  }
  ```
- **State Management**: Polling-based progress updates

---

### 4. Specialized Component Dependencies

#### EventArchiveManager.tsx
- **Role**: Event archiving functionality (used only by Setup)
- **Parent**: Setup.tsx
- **Child Components**: None
- **Props Dependencies**:
  ```typescript
  {
    currentEventKey?: string,               // Current event context
    currentYear?: number,                   // Current year context
    onArchiveSuccess?: () => void,          // Archive success callback
    onRestoreSuccess?: () => void           // Restore success callback
  }
  ```
- **State Management**: Archive operations and confirmation dialogs

#### SheetConfigManager.tsx
- **Role**: Google Sheets configuration (used only by Setup)
- **Parent**: Setup.tsx
- **Child Components**: None
- **Props Dependencies**:
  ```typescript
  {
    currentEventKey?: string,               // Current event context
    currentYear?: number,                   // Current year context
    onConfigurationChange?: () => void,     // Configuration change callback
    onConfigurationConfirmed?: () => void   // Configuration confirmed callback
  }
  ```
- **State Management**: Sheet configuration and connection testing

#### CategoryTabs.tsx
- **Role**: Tab navigation component (used only by FieldSelection)
- **Parent**: FieldSelection.tsx
- **Child Components**: None
- **Props Dependencies**:
  ```typescript
  {
    categories: Category[],                 // Required: Available categories
    activeCategory: string,                 // Required: Currently active category
    onCategoryChange: (categoryId: string) => void,  // Required: Change handler
    countsPerCategory?: Record<string, number>,      // Optional: Item counts
    totalCount?: number                     // Optional: Total count
  }
  ```
- **State Management**: None (controlled component)

#### TeamComparisonModal.tsx
- **Role**: AI-powered team comparison (used only by PicklistGenerator)
- **Parent**: PicklistGenerator.tsx
- **Child Components**: None
- **Props Dependencies**:
  ```typescript
  {
    isOpen: boolean,                        // Required: Modal visibility
    onClose: () => void,                    // Required: Close callback
    teamNumbers: number[],                  // Required: Teams to compare
    datasetPath: string,                    // Required: Dataset path
    yourTeamNumber: number,                 // Required: User's team number
    prioritiesMap: PrioritiesMap,           // Required: Priorities mapping
    onApply: (teams: Team[]) => void        // Required: Apply callback
  }
  ```
- **State Management**: Chat history and team reordering

---

## Critical Dependency Patterns

### 1. Parent-Child Prop Flow
```typescript
// Parent provides data and callbacks to child
Parent Component State → Props → Child Component

// Child communicates back via callbacks
Child Component Events → Callback Props → Parent Component State
```

### 2. Event Context Propagation
```typescript
// Many components need event context
Setup.tsx state → eventKey, year → Child components
```

### 3. Shared Component Reuse
```typescript
// PicklistGenerator used by multiple parents with different props
PicklistNew.tsx → PicklistGenerator (full feature set)
PicklistView.tsx → PicklistGenerator (display only)
```

### 4. Progress Tracking Pattern
```typescript
// ProgressTracker used for long operations
Parent Component → operationId → ProgressTracker → polling updates
```

### 5. Modal Communication Pattern
```typescript
// Modals managed by parent state
Parent: isOpen state → Modal: visibility
Modal: onClose callback → Parent: close modal
Modal: onApply callback → Parent: apply changes
```

---

## Data Flow Patterns

### 1. API Data Flow
```
Page Component → API Call → Local State → Props → Child Component
```

### 2. Form Data Flow
```
Child Component Input → Callback → Parent State → API Call → Response → State Update
```

### 3. LocalStorage Persistence
```
Component State ↔ localStorage ↔ Component Initialization
```

### 4. Navigation Flow
```
User Action → useNavigate Hook → React Router → Page Component Mount
```

---

## State Management Patterns

### 1. Local Component State
- Most components manage their own state
- State passed down via props
- Callbacks used for upward communication

### 2. LocalStorage Integration
- PicklistNew: Persists priority arrays and rankings
- No global state management system

### 3. API State Management
- Each component handles its own API calls
- Loading, error, and data states managed locally
- No shared API state cache

### 4. Event Context Sharing
- Event information passed as props
- No context providers for shared state

---

## Critical Preservation Requirements

During refactoring, these dependency patterns MUST be preserved:

### 1. Component Hierarchy
- **Exact parent-child relationships** must remain unchanged
- **Component nesting levels** must be preserved
- **Shared component usage** must remain consistent

### 2. Prop Interfaces
- **All prop names and types** must remain identical
- **Optional vs required props** must stay the same
- **Callback function signatures** must not change

### 3. State Management Patterns
- **LocalStorage key names** must remain unchanged
- **State variable names** must be preserved
- **API dependency patterns** must stay consistent

### 4. Event Flow Patterns
- **User interaction flows** must remain identical
- **Navigation patterns** must be preserved
- **Modal communication** must work the same way

### 5. Data Dependencies
- **API endpoint dependencies** must remain unchanged
- **Data transformation patterns** must be preserved
- **Error handling flows** must stay consistent

**Breaking any of these dependency patterns will cause cascading failures throughout the component tree.**

---

## Component Refactoring Guidelines

### Safe Refactoring Approaches
1. **Internal implementation changes** (hooks, logic reorganization)
2. **Styling improvements** (CSS, styling systems)
3. **Performance optimizations** (memoization, virtualization)
4. **Code quality improvements** (TypeScript, error handling)

### Dangerous Refactoring Changes
1. **Prop interface modifications** (breaking parent-child contracts)
2. **Component hierarchy changes** (moving components between parents)
3. **State management changes** (localStorage keys, state structure)
4. **Navigation pattern changes** (routing, URL structure)

### Required Coordination Points
1. **Shared components** (PicklistGenerator, ProgressTracker)
2. **Complex prop flows** (PicklistNew → PicklistGenerator)
3. **Modal interactions** (TeamComparisonModal)
4. **Multi-step workflows** (Setup wizard)

When refactoring shared components or complex prop flows, **all parent components must be updated simultaneously** to maintain compatibility.