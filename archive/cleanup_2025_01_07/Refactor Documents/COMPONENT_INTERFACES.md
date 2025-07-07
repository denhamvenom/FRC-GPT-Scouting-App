# Component Interfaces Documentation

This document contains comprehensive interface documentation for all React components in the original FRC GPT Scouting App codebase. This serves as a preservation reference during refactoring to ensure component contracts remain intact.

**Created**: 2025-06-12  
**Source**: Original codebase backup before refactoring  
**Purpose**: Prevent interface breakage during refactoring efforts

---

## Application Structure

### App.tsx
- **File Path**: `/frontend/src/App.tsx`
- **Type**: Root Application Component
- **Props**: None (root component)
- **State**: None (pure routing component)
- **Hooks**: None
- **Child Components**: 
  - Navbar
  - All page components via React Router
- **Routes Defined**:
  - `/` → Home
  - `/setup` → Setup
  - `/field-selection` → FieldSelection
  - `/validation` → Validation
  - `/picklist` → PicklistNew
  - `/build-dataset` → UnifiedDatasetBuilder
  - `/alliance-selection` → AllianceSelection
  - `/alliance-selection/:selectionId` → AllianceSelection
  - `/schema` → FieldSelection (redirect)
  - `/workflow` → Workflow
  - `/debug/logs` → DebugLogs

---

## Page Components

### Home.tsx
- **File Path**: `/frontend/src/pages/Home.tsx`
- **Type**: Landing Page Component
- **Props**: None
- **State Variables**:
  ```typescript
  health: string                    // Backend connection status
  eventInfo: EventInfo             // Current event information
  isLoadingEvent: boolean          // Loading state for event data
  ```
- **Hooks**: `useEffect` for initial API calls
- **API Dependencies**: 
  - `/api/health` - Backend status
  - `/api/setup/info` - Event information
- **Navigation Links**: Links to all major workflow pages
- **Parent Components**: App (via Router)

### Setup.tsx
- **File Path**: `/frontend/src/pages/Setup.tsx`
- **Type**: Multi-Step Setup Wizard
- **Props**: None
- **State Variables**:
  ```typescript
  currentStep: number              // Active setup step (1-4)
  completedSteps: Set<number>      // Completed steps tracking
  // Step 1 - Manual Training
  isTrainingComplete: boolean
  trainingProgress: number
  // Step 2 - Event Selection
  eventKey: string
  year: number
  eventOptions: Event[]
  // Step 3 - Archive Management
  archiveAction: 'create' | 'restore' | null
  // Step 4 - Sheet Configuration
  isSheetConfigured: boolean
  ```
- **Hooks**: `useState`, `useEffect`, `useNavigate`
- **Child Components**: 
  - EventArchiveManager
  - SheetConfigManager
- **Workflow Steps**:
  1. Manual training completion
  2. Event selection
  3. Archive management
  4. Google Sheets configuration
- **Parent Components**: App (via Router)

### FieldSelection.tsx
- **File Path**: `/frontend/src/pages/FieldSelection.tsx`
- **Type**: Field Mapping Interface
- **Props**: None
- **State Variables**:
  ```typescript
  scoutingHeaders: string[]        // Headers from scouting spreadsheet
  superscoutingHeaders: string[]   // Headers from superscout spreadsheet
  pitScoutingHeaders: string[]     // Headers from pit scouting
  selectedFields: { [key: string]: string }  // Field categorization mapping
  activeCategory: string           // Active tab ('match', 'pit', 'super', 'critical')
  criticalFieldMappings: CriticalMappings     // Required field mappings
  isLoading: boolean
  error: string | null
  ```
- **Hooks**: `useState`, `useEffect`, `useNavigate`
- **Child Components**: CategoryTabs
- **Categories**:
  - **match**: Match scouting fields
  - **pit**: Pit scouting fields  
  - **super**: Superscout fields
  - **critical**: Required mappings (team number, match number)
- **Parent Components**: App (via Router)

### Validation.tsx
- **File Path**: `/frontend/src/pages/Validation.tsx`
- **Type**: Data Validation Interface
- **Props**: None
- **State Variables**:
  ```typescript
  validationResult: ValidationResult | null   // Validation analysis results
  activeTab: 'missing' | 'outliers' | 'todo'  // Active validation tab
  selectedIssue: TeamMatch | ValidationIssue | null  // Selected validation issue
  corrections: { [key: string]: number }      // Correction values
  todoList: TodoItem[]                        // Manual scouting tasks
  isLoading: boolean
  ```
- **Hooks**: `useState`, `useEffect`
- **API Dependencies**:
  - `/api/validate/enhanced` - Enhanced validation with outliers
  - `/api/validate/apply-correction` - Apply corrections
  - `/api/validate/todo-list` - Get todo list
- **Validation Types**:
  - **missing**: Missing scouting data
  - **outliers**: Statistical outliers
  - **todo**: Manual scouting tasks
- **Parent Components**: App (via Router)

### PicklistNew.tsx
- **File Path**: `/frontend/src/pages/PicklistNew.tsx`
- **Type**: Primary Picklist Generation Interface
- **Props**: None
- **State Variables**:
  ```typescript
  datasetPath: string             // Path to unified dataset
  yourTeamNumber: number          // User's team number
  universalMetrics: Metric[]      // Available universal metrics
  gameMetrics: Metric[]           // Available game-specific metrics
  
  // Priority arrays for each pick position
  firstPickPriorities: MetricPriority[]
  secondPickPriorities: MetricPriority[]
  thirdPickPriorities: MetricPriority[]
  
  // Generated picklist arrays
  firstPickRanking: Team[]
  secondPickRanking: Team[]
  thirdPickRanking: Team[]
  
  // Team exclusion management
  excludedFromSecondPick: number[]
  excludedFromThirdPick: number[]
  
  // UI state
  activeTab: "first" | "second" | "third"
  isLocked: boolean
  ```
- **Hooks**: `useState`, `useEffect` with localStorage persistence
- **Child Components**: 
  - PicklistGenerator (main generation component)
  - ProgressTracker (for generation progress)
- **LocalStorage Keys**:
  - `firstPickPriorities`, `secondPickPriorities`, `thirdPickPriorities`
  - `firstPickRanking`, `secondPickRanking`, `thirdPickRanking`
  - `excludedFromSecondPick`, `excludedFromThirdPick`
- **Parent Components**: App (via Router)

### AllianceSelection.tsx
- **File Path**: `/frontend/src/pages/AllianceSelection.tsx`
- **Type**: Live Alliance Selection Interface
- **Props**: None
- **State Variables**:
  ```typescript
  picklist: LockedPicklist | null     // Locked picklist data
  selection: SelectionState | null    // Alliance selection state
  selectedTeam: number | null         // Currently selected team
  selectedAlliance: number | null     // Selected alliance number
  action: 'captain' | 'accept' | 'decline' | null  // Pending action
  isLoading: boolean
  ```
- **Hooks**: `useState`, `useEffect`, `useParams` (for selectionId), `useNavigate`
- **URL Parameters**: `selectionId` (optional) - For existing alliance selection
- **API Dependencies**:
  - `/api/alliance-selection/` - CRUD operations
  - `/api/picklist/locked` - Get locked picklist
- **Parent Components**: App (via Router)

---

## Reusable Components

### Navbar.tsx
- **File Path**: `/frontend/src/components/Navbar.tsx`
- **Type**: Navigation Component
- **Props**: None
- **State**: None (stateless component)
- **Hooks**: `useLocation` (for active link highlighting)
- **Navigation Items**:
  - Home, Setup, Field Selection, Validation, Picklist, Alliance Selection
- **Styling**: Tailwind CSS with active state highlighting
- **Parent Components**: App

### PicklistGenerator.tsx
- **File Path**: `/frontend/src/components/PicklistGenerator.tsx`
- **Type**: Core Picklist Generation Component
- **Props Interface**:
  ```typescript
  interface PicklistGeneratorProps {
    datasetPath: string;                    // Path to unified dataset
    yourTeamNumber: number;                 // User's team number
    pickPosition: "first" | "second" | "third";  // Current pick position
    priorities: MetricPriority[];           // Metric priorities for this position
    allPriorities?: {                       // All priorities for cross-pick exclusions
      first: MetricPriority[];
      second: MetricPriority[];
      third: MetricPriority[];
    };
    excludeTeams?: number[];                // Teams to exclude from ranking
    onPicklistGenerated?: (result: PicklistResult) => void;  // Success callback
    initialPicklist?: Team[];               // Pre-existing picklist data
    onExcludeTeam?: (teamNumber: number) => void;  // Exclude team callback
    isLocked?: boolean;                     // Whether picklist is locked
    onPicklistCleared?: () => void;         // Clear picklist callback
  }
  ```
- **State Variables**:
  ```typescript
  picklist: Team[]                // Generated team ranking
  isGenerating: boolean           // Generation in progress
  hasGenerated: boolean           // Has generated at least once
  generationProgress: number      // Progress percentage (0-100)
  batchProgress: BatchProgress    // Batch processing progress
  missingTeams: number[]          // Teams missing from dataset
  showMissingModal: boolean       // Missing teams modal visibility
  showComparisonModal: boolean    // Team comparison modal visibility
  comparisonTeams: number[]       // Teams for comparison
  currentPage: number             // Pagination current page
  itemsPerPage: number            // Items per page (default 25)
  ```
- **Hooks**: `useState`, `useEffect` with polling for batch processing
- **Child Components**:
  - ProgressIndicator (custom progress bar)
  - BatchProgressIndicator (batch processing progress)
  - MissingTeamsModal (teams missing from dataset)
  - TeamComparisonModal (AI-powered team comparison)
- **API Dependencies**:
  - `/api/picklist/generate` - Generate picklist
  - `/api/picklist/progress/{operationId}` - Progress tracking
  - `/api/team-comparison` - Team comparison analysis
- **Parent Components**: PicklistNew, PicklistView

### CategoryTabs.tsx
- **File Path**: `/frontend/src/components/CategoryTabs.tsx`
- **Type**: Tab Navigation Component
- **Props Interface**:
  ```typescript
  interface CategoryTabsProps {
    categories: Category[];                 // Available categories
    activeCategory: string;                 // Currently active category
    onCategoryChange: (categoryId: string) => void;  // Category change handler
    countsPerCategory?: Record<string, number>;      // Optional item counts
    totalCount?: number;                    // Optional total count
  }
  
  interface Category {
    id: string;                            // Category identifier
    name: string;                          // Display name
    description?: string;                  // Optional description
  }
  ```
- **State**: None (controlled component)
- **Hooks**: None
- **Styling**: Tailwind CSS with active state and count badges
- **Parent Components**: FieldSelection

### EventArchiveManager.tsx
- **File Path**: `/frontend/src/components/EventArchiveManager.tsx`
- **Type**: Event Archive Management Component
- **Props Interface**:
  ```typescript
  interface ArchiveManagerProps {
    currentEventKey?: string;              // Current event key
    currentYear?: number;                  // Current event year
    onArchiveSuccess?: () => void;         // Archive success callback
    onRestoreSuccess?: () => void;         // Restore success callback
  }
  ```
- **State Variables**:
  ```typescript
  archiveAction: 'create' | 'restore' | null  // Active archive action
  archivedEvents: ArchivedEvent[]         // List of archived events
  isLoading: boolean                      // Loading state
  error: string | null                    // Error message
  showConfirmDialog: boolean              // Confirmation dialog visibility
  restoreEventKey: string                 // Event key for restoration
  ```
- **Hooks**: `useState`, `useEffect`
- **API Dependencies**:
  - `/api/archive/events` - List archived events
  - `/api/archive/create` - Create archive
  - `/api/archive/restore` - Restore from archive
- **Parent Components**: Setup

### SheetConfigManager.tsx
- **File Path**: `/frontend/src/components/SheetConfigManager.tsx`
- **Type**: Google Sheets Configuration Component
- **Props Interface**:
  ```typescript
  interface SheetConfigManagerProps {
    currentEventKey?: string;              // Current event key
    currentYear?: number;                  // Current event year
    onConfigurationChange?: () => void;    // Configuration change callback
    onConfigurationConfirmed?: () => void; // Configuration confirmed callback
  }
  ```
- **State Variables**:
  ```typescript
  config: SheetConfiguration             // Sheet configuration data
  isLoading: boolean                     // Loading state
  isTestingConnection: boolean           // Connection test state
  connectionStatus: 'success' | 'error' | null  // Connection test result
  availableTabs: string[]                // Available sheet tabs
  ```
- **Hooks**: `useState`, `useEffect`
- **API Dependencies**:
  - `/api/sheet-config` - CRUD operations for sheet configuration
  - `/api/sheets/test-connection` - Test Google Sheets connection
  - `/api/sheets/tabs` - Get available sheet tabs
- **Parent Components**: Setup

### TeamComparisonModal.tsx
- **File Path**: `/frontend/src/components/TeamComparisonModal.tsx`
- **Type**: AI-Powered Team Comparison Component
- **Props Interface**:
  ```typescript
  interface TeamComparisonModalProps {
    isOpen: boolean;                       // Modal visibility
    onClose: () => void;                   // Close modal callback
    teamNumbers: number[];                 // Teams to compare
    datasetPath: string;                   // Path to dataset
    yourTeamNumber: number;                // User's team number
    prioritiesMap: PrioritiesMap;          // Metric priorities mapping
    onApply: (teams: Team[]) => void;      // Apply reordering callback
  }
  
  interface PrioritiesMap {
    first: MetricPriority[];
    second: MetricPriority[];
    third: MetricPriority[];
  }
  ```
- **State Variables**:
  ```typescript
  chatHistory: ChatMessage[]             // Chat conversation history
  currentMessage: string                 // Current user message
  isLoading: boolean                     // AI response loading
  comparisonData: TeamComparisonData     // Team comparison analysis
  reorderedTeams: Team[]                 // Reordered team list
  ```
- **Hooks**: `useState`, `useRef` (for chat scroll), `useEffect`
- **API Dependencies**:
  - `/api/team-comparison` - AI-powered team comparison
- **Features**:
  - Chat interface with AI for team analysis
  - Team reordering based on AI recommendations
  - Metric-based comparison with priorities
- **Parent Components**: PicklistGenerator

### ProgressTracker.tsx
- **File Path**: `/frontend/src/components/ProgressTracker.tsx`
- **Type**: Operation Progress Tracking Component
- **Props Interface**:
  ```typescript
  interface ProgressTrackerProps {
    operationId: string;                   // Operation ID for tracking
    onComplete?: (success: boolean) => void;  // Completion callback
    pollingInterval?: number;              // Polling interval in ms (default 1000)
  }
  ```
- **State Variables**:
  ```typescript
  progress: ProgressData                 // Progress information
  isPolling: boolean                     // Polling state
  error: string | null                   // Error message
  
  interface ProgressData {
    percentage: number;                  // Progress percentage (0-100)
    current_step: string;                // Current operation step
    total_steps: number;                 // Total number of steps
    estimated_time_remaining: number;    // Estimated seconds remaining
    status: 'running' | 'completed' | 'failed';  // Operation status
  }
  ```
- **Hooks**: `useState`, `useEffect` with polling
- **API Dependencies**:
  - `/api/progress/{operationId}` - Progress tracking endpoint
- **Features**:
  - Real-time progress updates
  - Time estimation
  - Error handling and display
- **Parent Components**: PicklistNew, UnifiedDatasetBuilder

---

## Critical Interface Patterns

### 1. Event Context Pattern
Many components require event context information:
```typescript
currentEventKey?: string
currentYear?: number
```

### 2. Callback Pattern
Components use consistent callback naming:
```typescript
onSuccess?: () => void
onChange?: (value: any) => void
onComplete?: (result: any) => void
onError?: (error: string) => void
```

### 3. Loading State Pattern
Most data-driven components follow this pattern:
```typescript
isLoading: boolean
error: string | null
data: DataType | null
```

### 4. Pagination Pattern
List components with pagination use:
```typescript
currentPage: number
itemsPerPage: number
totalItems: number
```

### 5. LocalStorage Persistence Pattern
State persistence uses consistent localStorage keys:
```typescript
// Save
localStorage.setItem('keyName', JSON.stringify(data))

// Load
const saved = localStorage.getItem('keyName')
const data = saved ? JSON.parse(saved) : defaultValue
```

---

## Data Flow Architecture

### Parent → Child Data Flow
1. **App** → Page components (routing only)
2. **PicklistNew** → PicklistGenerator (dataset path, team number, priorities)
3. **Setup** → EventArchiveManager, SheetConfigManager (event context)
4. **FieldSelection** → CategoryTabs (categories, active state)

### Child → Parent Communication
1. **Callback props** for state changes
2. **Navigation** through useNavigate hook
3. **LocalStorage** for cross-component persistence

### API Integration Points
1. **Page components** handle primary API calls
2. **Child components** may have specific API dependencies
3. **Progress tracking** uses polling pattern
4. **Error handling** at component level

---

## Preservation Requirements

During refactoring, these interfaces MUST be preserved:

1. **All component prop interfaces** - Exact prop names and types
2. **LocalStorage key names** - For state persistence
3. **API endpoint dependencies** - Components rely on specific endpoints
4. **Navigation routes** - URL structure and parameters
5. **State variable patterns** - Loading, error, data patterns
6. **Callback function signatures** - Parent-child communication contracts

**Critical**: Any changes to these interfaces will break the component hierarchy and require coordinated updates across multiple files.