# GRAPHICAL ANALYSIS SPRINT PLAN
**Project**: Multi-Axis Radar Chart Analysis for Unified Scouting Data  
**Version**: 1.0  
**Created**: January 7, 2025  

## INSTRUCTIONS FOR CONTEXT WINDOWS

### CRITICAL: How to Use This Document
**EVERY context window MUST follow these steps:**

1. **READ FIRST**: Always read this entire document before starting any work
2. **USE FOR REFERENCE**: Check previous sprint completion notes for context and dependencies
3. **USE FOR COORDINATION**: Follow the exact copy-paste prompt for your assigned sprint
4. **UPDATE REQUIRED**: After completing work, you MUST update this document with:
   - Specific changes made and file locations
   - Code snippets of key modifications
   - Challenges encountered and solutions
   - Important context for the next sprint
   - Validation results

### Document Update Process
```markdown
### Sprint X Completion Notes
**Changes Made**:
- Created/Updated file_name.tsx: specific_component_name to do X
- Added new hook useHookName() in file_name.tsx lines X-Y
- Modified existing_component() to handle chart_data_structure

**Code Locations**:
- /frontend/src/pages/GraphicalAnalysis.tsx:1-150 (new page component)
- /frontend/src/components/Navbar.tsx:45-48 (added navigation tab)
- /frontend/src/hooks/useUnifiedData.ts:1-80 (data fetching hook)

**Challenges Encountered**:
- Issue with X: solved by Y
- Chart rendering concern Z: addressed with optimization A

**Important Context for Next Sprint**:
- New hook available: useUnifiedData() returns merged team data
- Chart library configured with responsive settings
- Metric selection state management implemented

**Validation Notes**:
- Tested with unified_event_2025lake.json: SUCCESS
- Dynamic field loading verified: SUCCESS
- Chart rendering confirmed: SUCCESS
```

### Sprint Handoff Requirements
**BEFORE starting your sprint**: Verify all previous sprints are marked complete
**AFTER finishing your sprint**: Mark your sprint complete and update "Last Updated" date
**IF encountering blockers**: Document clearly for next context window to address

---

## PROJECT OVERVIEW

### Goal
Create a new graphical analysis tab that allows users to visualize and compare team data using Multi-Axis Radar/Spider Charts. The system must be completely data-agnostic, pulling metrics dynamically from unified event data.

### Key Requirements
1. **Data Agnostic**: No hardcoded metrics, teams, or game-specific information
2. **Dynamic Visualization**: Radar charts that adapt to available metrics
3. **Team Comparison**: Select and compare multiple teams simultaneously
4. **Event-Based**: Pull data from current event's unified dataset
5. **User-Friendly**: Clean interface appropriate for FRC team use

### Architecture Context
- **Unified Data**: Dynamic loading from `/api/unified/dataset` endpoint
- **Field Metadata**: Pull labels and categories from field_selections files
- **Navigation**: New tab in main header after "Alliance Selection"
- **Chart Library**: Recharts (React-friendly, good radar chart support)

---

## SPRINT 1: Infrastructure Setup & Basic Component
**Estimated Tokens**: ~12,000  
**Focus**: Install dependencies, create page component, add navigation

### Sprint 1 Objectives
1. Install Recharts charting library
2. Create GraphicalAnalysis page component with basic structure
3. Add navigation tab to main header
4. Register route in App.tsx
5. Create basic data fetching hook for unified dataset

### Files to Create/Modify
- `/frontend/package.json` - Add Recharts dependency
- `/frontend/src/pages/GraphicalAnalysis.tsx` - New page component
- `/frontend/src/components/Navbar.tsx` - Add navigation tab
- `/frontend/src/App.tsx` - Register new route
- `/frontend/src/hooks/useUnifiedData.ts` - Data fetching hook

### Key Implementation Details
1. **Recharts Installation**: Use latest stable version
2. **Component Structure**: Follow existing page patterns (loading states, error handling)
3. **Navigation**: Place after "Alliance Selection" tab
4. **Route Path**: `/graphical-analysis`
5. **Data Hook**: Fetch from `/api/unified/dataset` with event_key parameter

### Copy-Paste Prompt for Sprint 1
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire GRAPHICAL_ANALYSIS_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 1 of the Graphical Analysis project. 

MANDATORY FIRST STEP: Read /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md completely and verify no previous sprints are incomplete.

CONTEXT: We're adding a new graphical analysis feature with Multi-Axis Radar Charts for team comparison. The system must be completely data-agnostic, dynamically loading metrics from unified event data.

SPRINT 1 OBJECTIVES:
1. Install Recharts library for React-based charting
2. Create new GraphicalAnalysis page component with loading/error states
3. Add "Graphical Analysis" tab to Navbar before "Picklist"
4. Register route "/graphical-analysis" in App.tsx
5. Create useUnifiedData hook for fetching event data

KEY FILES TO READ FIRST:
- /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md (CRITICAL: Read instructions section)
- /frontend/src/components/Navbar.tsx (navigation pattern)
- /frontend/src/App.tsx (routing pattern)
- /frontend/src/pages/Validation.tsx (page component pattern to follow)
- /backend/app/data/field_selections_2025lake.json (understand data structure)

IMPLEMENTATION REQUIREMENTS:
1. Use npm install recharts@latest to add chart library
2. Follow existing page patterns for state management and API calls
3. Create useUnifiedData hook that fetches from /api/unified/dataset
4. Include proper TypeScript types for data structures
5. Add responsive design considerations

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 1 Completion Notes section in GRAPHICAL_ANALYSIS_SPRINT_PLAN.md using Edit tool
2. Follow exact template in "Document Update Process" section
3. Include specific changes, code locations, challenges, context for Sprint 2
4. Update "Last Updated" field at bottom of document
5. Verify all Sprint 1 Success Criteria are met before marking complete

FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK PROJECT COORDINATION.

START IMPLEMENTATION.
```

### Sprint 1 Success Criteria
- [x] Recharts library installed and configured
- [x] GraphicalAnalysis page component created with proper structure
- [x] Navigation tab added and functional
- [x] Route registered and accessible
- [x] useUnifiedData hook fetches data successfully
- [x] TypeScript types defined for data structures

### Sprint 1 Completion Notes
[To be filled during implementation]

---

## SPRINT 2: Data Processing & Metric Selection
**Estimated Tokens**: ~13,000  
**Focus**: Process unified data, implement metric selection UI

### Sprint 2 Objectives
1. Parse unified dataset to extract available metrics
2. Load field metadata for metric labels and categories
3. Create metric selection interface (checkboxes/multi-select)
4. Implement team selection dropdown
5. Structure data for radar chart consumption

### Files to Create/Modify
- `/frontend/src/pages/GraphicalAnalysis.tsx` - Add metric/team selection UI
- `/frontend/src/hooks/useFieldMetadata.ts` - Field metadata loading
- `/frontend/src/utils/chartDataProcessing.ts` - Data transformation utilities
- `/frontend/src/types/graphicalAnalysis.ts` - TypeScript types

### Key Implementation Details
1. **Metric Discovery**: Dynamically extract numeric fields from team stats
2. **Category Grouping**: Group metrics by category (auto, teleop, endgame)
3. **Label Mapping**: Use field_selections for human-readable labels
4. **Team Selection**: Multi-select dropdown for comparing teams
5. **Data Normalization**: Scale metrics for radar chart (0-100)

### Copy-Paste Prompt for Sprint 2
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire GRAPHICAL_ANALYSIS_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 2 of the Graphical Analysis project.

MANDATORY FIRST STEP: Read /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md completely and verify Sprint 1 is marked as complete with proper completion notes.

CONTEXT: Sprint 1 set up the basic infrastructure. Now we need to process unified data and create metric/team selection interfaces.

SPRINT 2 OBJECTIVES:
1. Parse unified dataset to dynamically extract available metrics
2. Create useFieldMetadata hook to load field labels and categories
3. Implement metric selection UI with category grouping
4. Add team selection dropdown (multi-select)
5. Create data processing utilities for radar chart format

KEY FILES TO READ FIRST:
- /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md (CRITICAL: Read instructions AND Sprint 1 notes)
- /backend/app/data/field_selections_2025lake.json (field metadata structure)
- /backend/app/data/unified_event_2025lake.json (team data structure)
- /frontend/src/pages/GraphicalAnalysis.tsx (current implementation from Sprint 1)

IMPLEMENTATION REQUIREMENTS:
1. Extract numeric fields from team.stats dynamically (no hardcoding)
2. Group metrics by category using field_selections metadata
3. Create intuitive metric selection (consider using checkboxes by category)
4. Team selection should support 1-6 teams for comparison
5. Normalize data for radar chart (consider different metric scales)

DATA PROCESSING:
- Filter out non-numeric fields
- Use label_mapping for display names
- Group by category (autonomous, teleop, endgame, strategic)
- Handle missing data gracefully

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 2 Completion Notes section in GRAPHICAL_ANALYSIS_SPRINT_PLAN.md
2. Include all code locations and specific changes
3. Document any data processing decisions
4. Provide context for Sprint 3 chart implementation
5. Mark Sprint 2 as complete with validation notes

START IMPLEMENTATION.
```

### Sprint 2 Success Criteria
- [x] Metrics dynamically extracted from unified data
- [x] Field metadata loaded and applied for labels
- [x] Metric selection UI functional with categories
- [x] Team selection supports multiple teams
- [x] Data properly structured for radar chart
- [x] No hardcoded metrics or game-specific data

### Sprint 2 Completion Notes
**Changes Made**:
- Created useFieldMetadata hook in /frontend/src/hooks/useFieldMetadata.ts to load field labels and categories
- Added field-metadata API endpoint in /backend/app/api/field_selection.py:216-240
- Created chartDataProcessing utilities in /frontend/src/utils/chartDataProcessing.ts for data normalization and radar chart formatting
- Updated GraphicalAnalysis component in /frontend/src/pages/GraphicalAnalysis.tsx:1-400 with complete metric and team selection UI
- Created TypeScript types in /frontend/src/types/graphicalAnalysis.ts with comprehensive type definitions

**Code Locations**:
- /frontend/src/hooks/useFieldMetadata.ts:1-207 (field metadata loading with category grouping)
- /frontend/src/utils/chartDataProcessing.ts:1-368 (data processing utilities for radar charts)
- /frontend/src/types/graphicalAnalysis.ts:1-391 (TypeScript type definitions and validation)
- /frontend/src/pages/GraphicalAnalysis.tsx:1-400 (updated component with full UI implementation)
- /backend/app/api/field_selection.py:216-240 (new API endpoint for field metadata)

**Challenges Encountered**:
- Field metadata API required new endpoint: solved by adding field-metadata endpoint to existing router
- Complex state management for selections: addressed with comprehensive state interface and handlers
- Data processing complexity: resolved with utility functions for normalization and chart data conversion

**Important Context for Next Sprint**:
- useFieldMetadata() hook provides dynamic metric categories and labels from field_selections data
- processUnifiedDataForChart() function ready for radar chart implementation in Sprint 3
- State management handles metric presets, category expansion, and team selection (max 6 teams)
- Data preview shows actual team values for selected metrics
- All data processing is event-agnostic and dynamically extracts numeric fields

**Validation Notes**:
- Tested with unified_event_2025lake.json: SUCCESS - dynamic metric extraction working
- Field metadata loading verified: SUCCESS - categories and labels loaded correctly
- Metric selection UI functional: SUCCESS - category grouping and checkboxes working
- Team selection with multi-select: SUCCESS - supports 1-6 teams with validation
- Data processing utilities tested: SUCCESS - normalization and chart data conversion ready
- No hardcoded game-specific data: SUCCESS - all metrics extracted dynamically

---

## SPRINT 3: Radar Chart Implementation
**Estimated Tokens**: ~14,000  
**Focus**: Implement interactive radar chart visualization

### Sprint 3 Objectives
1. Implement Multi-Axis Radar Chart using Recharts
2. Add responsive design for various screen sizes
3. Create interactive tooltips with detailed information
4. Implement legend for team identification
5. Add chart customization options (colors, scale)

### Files to Modify
- `/frontend/src/pages/GraphicalAnalysis.tsx` - Add radar chart component
- `/frontend/src/components/RadarChartVisualization.tsx` - Dedicated chart component
- `/frontend/src/utils/chartColors.ts` - Color palette utilities

### Key Implementation Details
1. **Recharts Radar**: Use RadarChart, PolarGrid, PolarAngleAxis components
2. **Dynamic Axes**: Generate axes based on selected metrics
3. **Team Traces**: Each team as separate Radar component with unique color
4. **Responsive**: Chart resizes based on container
5. **Interactivity**: Hover tooltips, clickable legend

### Copy-Paste Prompt for Sprint 3
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire GRAPHICAL_ANALYSIS_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 3 of the Graphical Analysis project.

MANDATORY FIRST STEP: Read /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md completely and verify Sprints 1-2 are marked as complete with proper completion notes.

CONTEXT: Sprints 1-2 set up infrastructure and data processing. Now we implement the actual radar chart visualization.

SPRINT 3 OBJECTIVES:
1. Create RadarChartVisualization component using Recharts
2. Implement dynamic axes based on selected metrics
3. Add team comparison with distinct colors
4. Create interactive tooltips and legend
5. Ensure responsive design for different screens

KEY FILES TO READ FIRST:
- /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md (CRITICAL: Read Sprint 1-2 notes)
- /frontend/src/pages/GraphicalAnalysis.tsx (current state)
- Recharts documentation for RadarChart API

IMPLEMENTATION REQUIREMENTS:
1. Use Recharts RadarChart with proper configuration
2. Dynamic axis generation from selected metrics
3. Each team as separate Radar with unique color
4. Tooltips show exact values and team names
5. Legend identifies teams with toggle capability

CHART SPECIFICATIONS:
- PolarGrid for background grid
- PolarAngleAxis for metric labels
- PolarRadiusAxis for value scale (0-100)
- Responsive container for auto-sizing
- Smooth animations on data changes

UI CONSIDERATIONS:
- Chart takes 70% width, controls 30%
- Mobile responsive (stack vertically)
- Clear visual hierarchy
- Accessible color scheme

MANDATORY COMPLETION REQUIREMENTS:
1. Update Sprint 3 Completion Notes in GRAPHICAL_ANALYSIS_SPRINT_PLAN.md
2. Document chart configuration decisions
3. Include performance considerations
4. Provide context for Sprint 4 enhancements
5. Validate chart renders with real data

START IMPLEMENTATION.
```

### Sprint 3 Success Criteria
- [ ] Radar chart renders with selected metrics
- [ ] Multiple teams display with distinct colors
- [ ] Interactive tooltips show detailed information
- [ ] Legend allows team identification
- [ ] Responsive design works on mobile/desktop
- [ ] Smooth transitions when data changes

### Sprint 3 Completion Notes
[To be filled during implementation]

---

## SPRINT 4: Analysis Features & Polish
**Estimated Tokens**: ~11,000  
**Focus**: Add analysis features and polish user experience

### Sprint 4 Objectives
1. Add chart export functionality (PNG/SVG)
2. Implement metric comparison mode (normalize by max)
3. Add preset metric groups (e.g., "Scoring", "Defense")
4. Create data table view alongside chart
5. Add help/instructions panel

### Files to Create/Modify
- `/frontend/src/pages/GraphicalAnalysis.tsx` - Add export and view modes
- `/frontend/src/components/MetricPresets.tsx` - Preset selection component
- `/frontend/src/components/DataTableView.tsx` - Tabular data display
- `/frontend/src/utils/chartExport.ts` - Export utilities

### Key Implementation Details
1. **Export**: Use html2canvas or Recharts built-in export
2. **Normalization**: Option to normalize by team max or dataset max
3. **Presets**: Common metric groupings for quick selection
4. **Data Table**: Show raw values in sortable table
5. **Help Panel**: Instructions for effective use

### Copy-Paste Prompt for Sprint 4
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire GRAPHICAL_ANALYSIS_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 4 of the Graphical Analysis project.

MANDATORY FIRST STEP: Read /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md completely and verify Sprints 1-3 are marked as complete with proper completion notes.

CONTEXT: Sprints 1-3 created the core functionality. Now we add analysis features and polish the user experience.

SPRINT 4 OBJECTIVES:
1. Add export functionality for charts (PNG/SVG)
2. Implement comparison modes (normalize by max)
3. Create metric preset groups for quick selection
4. Add data table view alongside chart
5. Include help/instructions for users

KEY FILES TO READ FIRST:
- /GRAPHICAL_ANALYSIS_SPRINT_PLAN.md (CRITICAL: Read all Sprint notes)
- /frontend/src/pages/GraphicalAnalysis.tsx (current implementation)
- Current UI/UX patterns in the app

IMPLEMENTATION REQUIREMENTS:
1. Export button that saves chart as image
2. Toggle for normalization modes
3. Preset buttons: "All Scoring", "Autonomous", "Endgame"
4. Sortable data table with selected metrics
5. Collapsible help panel with usage tips

FEATURE SPECIFICATIONS:
- Export: Include title and timestamp
- Normalization: By team max or global max
- Presets: Based on metric categories
- Table: Sortable columns, team names as rows
- Help: Clear instructions, example use cases

POLISH ITEMS:
- Loading states for all operations
- Error messages for edge cases
- Keyboard shortcuts for common actions
- Print-friendly styling
- Accessibility improvements

MANDATORY COMPLETION REQUIREMENTS:
1. Update Sprint 4 Completion Notes
2. Run manual testing of all features
3. Document any limitations
4. Update project status to COMPLETE
5. Provide maintenance notes

START IMPLEMENTATION.
```

### Sprint 4 Success Criteria
- [ ] Chart export works reliably
- [ ] Normalization modes function correctly
- [ ] Preset selections update chart instantly
- [ ] Data table displays alongside chart
- [ ] Help panel provides clear guidance
- [ ] Overall UX is polished and intuitive

### Sprint 4 Completion Notes
[To be filled during implementation]

---

## PROJECT COMPLETION VALIDATION

### End-to-End Test Scenarios
1. **Basic Flow**: Load page → Select metrics → Select teams → View chart
   - **Expected**: Chart renders with correct data
   - **Expected**: All interactions smooth and intuitive

2. **Advanced Analysis**: Use presets → Compare 4 teams → Export chart
   - **Expected**: Preset selection works instantly
   - **Expected**: Export includes all visual elements
   - **Expected**: File downloads successfully

3. **Data Integrity**: Switch events → Verify new metrics load
   - **Expected**: Metrics update based on event data
   - **Expected**: No hardcoded values appear
   - **Expected**: Categories reflect actual data

### Success Metrics
- [ ] Completely data-agnostic implementation
- [ ] No hardcoded game elements
- [ ] Responsive on all screen sizes
- [ ] Intuitive for FRC team members
- [ ] Performance acceptable with full dataset

### Known Limitations
- Maximum 6 teams for readability
- Text fields excluded from radar charts
- Requires numeric data for visualization

---

## MAINTENANCE NOTES

### Adding New Chart Types
1. Install additional Recharts components if needed
2. Create new visualization component
3. Add toggle in GraphicalAnalysis page
4. Ensure data processing supports new format

### Performance Optimization
- Consider data pagination for large events
- Implement chart memoization for re-renders
- Use web workers for heavy calculations

### Future Enhancements
- Time series analysis (match progression)
- Statistical overlays (averages, std dev)
- Custom metric formulas
- Collaborative annotations

### Troubleshooting Guide
- **Chart not rendering**: Check selected metrics have data
- **Export failing**: Verify browser supports canvas API
- **Slow performance**: Reduce number of selected metrics
- **Data missing**: Confirm unified dataset has team stats

---

**Document Status**: SPRINT 2 COMPLETE  
**Last Updated**: January 7, 2025  
**Project Status**: Graphical Analysis with Multi-Axis Radar Charts - SPRINT 2 COMPLETE