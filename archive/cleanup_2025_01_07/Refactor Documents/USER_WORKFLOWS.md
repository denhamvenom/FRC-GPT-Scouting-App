# User Workflows Documentation

This document contains comprehensive user workflow documentation for the original FRC GPT Scouting App based on website screenshots. This serves as a preservation reference during refactoring to ensure user experience remains identical.

**Created**: 2025-06-12  
**Source**: Website screenshots from original working system  
**Purpose**: Prevent user workflow disruption during refactoring efforts

---

## Application Overview

### Navigation Structure
- **Header Navigation**: Blue header with "FRC Strategy Assistant" branding
- **Main Navigation**: Home | Setup | Field Selection | Validation | Picklist | Alliance Selection
- **Current Context**: Shows backend status ("Connected") and current event ("2025lake (2025)")

### Visual Design Characteristics
- **Color Scheme**: Blue header (#4F46E5), white/gray backgrounds
- **Typography**: Clean, modern sans-serif fonts
- **Layout**: Responsive grid-based layout with cards and panels
- **Status Indicators**: Color-coded cards (blue, green, purple, teal, red)

---

## Primary User Workflows

### 1. Initial Setup Workflow

#### 1.1 Home Page - Entry Point
![Home Page Reference](../original_codebase/Website Screenshots/Home.png)

**Visual Elements**:
- Main title: "FRC Strategy Assistant"
- Subtitle: "A year-agnostic, team-agnostic, data-agnostic toolkit for FRC event strategy"
- Status indicators: "Backend Status: Connected" | "Current Event: 2025lake (2025)"

**Action Cards** (2x3 grid):
1. **Setup** (Blue card)
   - Description: "Configure event details, upload a game manual, and setup your season parameters."
2. **Field Selection** (Green card)
   - Description: "Select which fields from your scouting spreadsheet to analyze."
3. **Validation** (Purple card)
   - Description: "Flag missing or outlier match data and fix issues interactively."
4. **Picklist Generator** (Teal card)
   - Description: "Create ranked first, second, and third pick lists based on your priorities."
5. **Alliance Selection** (Red card)
   - Description: "Live draft tracker that strikes picked teams and re-ranks candidates."

**Project Overview Section**:
- Three columns showing Learning, Validation, and Pick-List phases

**User Journey**: User starts here and navigates to Setup for initial configuration

---

#### 1.2 Setup Process (4 Steps)

##### Step 1: Manual Training
![Setup Step 1](../original_codebase/Website Screenshots/Setup1.png)

**Visual Elements**:
- Step indicator: Numbered circles (1-4) with progress line
- Active step highlighted in blue
- Step labels: "Manual Training | Event Selection | Database Alignment | Setup Complete"

**Form Fields**:
- **FRC Season Year**: Dropdown (default: 2025)
- **Game Manual PDF**: File upload button "Choose File" | "No file chosen"
- **Upload Manual** button (blue, full width)

**Existing Manuals Table**:
- Columns: Filename | Year | Uploaded | Actions
- Sample row: "2025GameManual.pdf | 2025 | 5/26/2025, 11:10:52 PM | Load ToC | Delete"

**Navigation**: Previous (disabled) | Next buttons

---

##### Step 2: Event Selection
![Setup Step 2](../original_codebase/Website Screenshots/Setup2.png)

**Visual Elements**:
- Step 1 completed (green checkmark)
- Step 2 active (blue)

**Current Event Display**:
- "Active Event: Bayou Regional (2025)" (blue link)

**Event Selection Form**:
- **FRC Season Year**: Dropdown (2025)
- **Select Event**: Dropdown showing "Bayou Regional - Kenner, LA, USA"
- **Event Details**: 
  - "Bayou Regional"
  - "Event Code: 2025lake (2025-04-02 to 2025-04-05)"
  - Description text about event selection purpose

**Set Event** button (blue, full width)
**Success Message**: "Event successfully configured!" (green alert)

---

##### Step 3: Database Alignment
![Setup Step 3](../original_codebase/Website Screenshots/Setup3.png)

**Continue to Step 4: Setup Complete**
![Setup Step 4](../original_codebase/Website Screenshots/Setup4.png)

**Expected Workflow**: Configuration of Google Sheets integration and final setup confirmation

---

### 2. Field Selection Workflow

#### 2.1 Field Categorization Interface
![Field Selection](../original_codebase/Website Screenshots/FieldSelection.png)

**Visual Elements**:
- Page title: "Field Selection"
- Success message: "Auto-categorized 30 fields based on naming patterns. Please review and adjust as needed." (green alert)

**Tab Navigation**:
- **Match Scouting** (33 fields) - Active tab (blue)
- **Pit Scouting** (13 fields)
- **Super Scouting** (3 fields)
- **Critical Fields** (4 fields) - Warning icon

**Progress Bar**: 0% to 100% completion indicator

**Field Mapping Table**:
- **Header Column**: Lists spreadsheet headers (Timestamp, Scout Name, Match Number, Team Number, Alliance, Auto Path, etc.)
- **Category Column**: Dropdown selectors with categories:
  - Ignore
  - Team Number
  - Match Number
  - Team Information
  - Autonomous
  - Teleop
  - Endgame
  - Strategy
  - Other

**Pre-categorization**: System automatically suggests categories based on header names (e.g., "Match Number" → "Match Number", "Team Number" → "Team Number")

**User Actions**:
1. Review auto-categorized fields
2. Adjust category assignments via dropdowns
3. Ensure critical fields (Team Number, Match Number) are properly mapped
4. Complete all required categorizations
5. Save field selections

---

### 3. Data Validation Workflow

#### 3.1 Validation Summary Dashboard
![Validation Overview](../original_codebase/Website Screenshots/DataValidation_Outliers.png)

**Visual Elements**:
- Page title: "Validation Summary"

**Summary Cards** (4 metrics):
1. **Missing Match Records**: 9 (pink background)
2. **Missing SuperScouting**: 54 (pink background)
3. **Statistical Outliers**: 115 (yellow background)
4. **Ignored Matches**: 0 (blue background)

**Action Buttons**:
- **Validation Complete** (green button)
- **Refresh Data** (blue button)

**Tab Navigation**:
- Missing Data
- **Outliers** (active - blue)
- To-Do List

---

#### 3.2 Outlier Correction Interface

**Left Panel - Issue List**:
- Scrollable list of teams/matches with issues
- Format: "Team XXXX, Match XX, 1 issues found"
- Color coding for different issue types

**Right Panel - Correction Details**:
- **Selected Issue**: "Team 2992 - Match 82"
- **Issues Detected**: Shows field name "auto" with current value "24"
- **Detection Method**: "z_score (z-score: 4.56)"

**Suggested Corrections Section**:
- Field name: "auto"
- Current value: 24
- Suggested values: "8.78 (team_average)" | "0 (zero)"
- **No Change** button (selected)

**Correction Reason**:
- Text area: "Why is this correction being made? (e.g., 'Verified with pit crew', 'Video review', etc.)"

**Action Buttons**:
- **Cancel** | **Apply Corrections** (blue)

**User Actions**:
1. Review flagged outliers in left panel
2. Select team/match to examine
3. Review detected issues and suggested corrections
4. Choose correction value or keep original
5. Provide reason for correction
6. Apply corrections or cancel
7. Continue until all outliers addressed

---

### 4. Picklist Generation Workflow

#### 4.1 Picklist Builder Interface
![Picklist Builder](../original_codebase/Website Screenshots/Picklist Builder.png)

**Visual Elements**:
- Page title: "Picklist Builder"
- **Clear All Data** button (red, top right)

**Data Source Information Panel**:
- **Event**: 2025lake (2025)
- **Teams**: 55 teams
- **Dataset File**: unified_event_2025lake.json
- **Matches**: 498 matches

**Your Team Information Panel**:
- **Your Team Number**: 8044 (input field)
- Note: "Required for generating rankings"

**Strategy Description Panel**:
- Large text area with placeholder: "Example: I need a second pick that is good at scoring on L4 and has a reliable auto routine."
- **Parse Strategy** button (blue)

**Tab Navigation**:
- **First Pick** (active - blue underline)
- Second Pick
- Third Pick

**First Pick Priorities Section**:
Numbered priority list (1-5):

1. **Where (teleop) [coral l4]** - Weight: 3x (blue pill)
   - Description: "Directly measures the ability to score at the L4 level during teleop..."
   - Remove button (X)

2. **Tele score** - Weight: 2x (blue pill)
   - Description: "Provides an overall assessment of scoring capability..."

3. **Driver skill** - Weight: 2x (blue pill)
   - Description: "A skilled driver can effectively maneuver the robot..."

4. **Reliability / Consistency** - Weight: 1.5x (blue pill)
   - Description: "Ensures that the robot consistently performs well..."

5. **comments** - Weight: 1x (blue pill)
   - Description: "Qualitative insights from superscouting..."

**Available Metrics Panel** (bottom):
- Search bar: "Search metrics..."
- Filterable list of available metrics to add as priorities

**User Actions**:
1. Enter team number
2. Describe strategy in natural language
3. Parse strategy to auto-populate priorities
4. Adjust priority weights using weight selectors (0.5x to 3x)
5. Add/remove metrics from priority list
6. Switch between First/Second/Third pick tabs
7. Configure priorities for each pick position
8. Generate picklist rankings

---

#### 4.2 Picklist Generation States

**During Generation**:
![During Generation](../original_codebase/Website Screenshots/Picklist Builder_DuringPicklistGeneration.png)
- Progress indicators
- Real-time status updates
- Batch processing progress

**After Completion**:
![After Generation](../original_codebase/Website Screenshots/PicklistBuilder_AfterPicklistDone.png)
- Generated team rankings
- Team cards with statistics
- Ability to exclude teams from later picks

**Locked Picklist**:
![Locked Picklist](../original_codebase/Website Screenshots/PicklistBuilder_LockedPicklist.png)
- Read-only view of locked rankings
- Preparation for alliance selection

---

### 5. Alliance Selection Workflow

#### 5.1 Live Draft Interface
![Alliance Selection](../original_codebase/Website Screenshots/AllianceSelection_BeforeChoice.png)

**Visual Elements**:
- Page title: "Live Alliance Selection"
- Round indicator: "Round 1 (First Picks)" with "In Progress" status

**Action Buttons** (top right):
- **Advance to Round 2** (blue)
- **Reset Selection** (red)
- **Back to Picklist** (gray)

**Team Selection Panel** (left side):
- Title: "Team Selection (1st Pick List)"
- **Highest Picks** column showing ranked teams:
  - 4087 (Voodoo Volts, 1st Pick #1, Current Round Pick)
  - 5653 (Iron Mosquitos, 1st Pick #2, Current Round Pick)
  - 16 (Bomb Squad, 1st Pick #3, Current Round Pick)
  - etc.

**Ranking Categories**:
- Highest Picks | High Priority | Priority | Medium Priority | Medium | Medium-Low | Low Priority | Lowest Priority

**Alliance Board Panel** (right side):
- **Alliance #1**: Captain (-), First Pick (-), Second Pick (-)
- **Alliance #2**: Captain (-), First Pick (-), Second Pick (-)
- **Alliance #3**: Captain (-), First Pick (-), Second Pick (-)

**Team Selection Process**:
![Team Action Selection](../original_codebase/Website Screenshots/AllianceSelection_ChoosePick.png)
- Click team to select
- Choose action: Captain | Accept | Decline
- Assign to alliance
- Track selection progress

**User Actions**:
1. Select team from ranked list
2. Choose action (Captain/Accept/Decline)
3. Assign to appropriate alliance
4. Track picks across multiple rounds
5. Advance to next round when ready
6. Monitor alliance formation progress

---

## Critical UI/UX Patterns

### 1. Navigation Consistency
- **Header**: Always visible blue navigation bar
- **Breadcrumbs**: Clear indication of current page
- **Status Display**: Consistent backend/event status indicators

### 2. Form Patterns
- **Step Indicators**: Numbered circles with progress lines
- **Required Fields**: Clear labeling of required information
- **Validation**: Immediate feedback for form errors
- **Action Buttons**: Consistent blue primary, red destructive, gray secondary

### 3. Data Display Patterns
- **Summary Cards**: Color-coded metric cards with counts
- **Tables**: Consistent header/data formatting
- **Progress Bars**: Visual progress indicators
- **Status Badges**: Color-coded status indicators

### 4. Interaction Patterns
- **Tabs**: Consistent tab styling with active state indicators
- **Dropdowns**: Standard select styling with clear options
- **Modal Dialogs**: Consistent modal patterns for confirmations
- **Loading States**: Progress indicators for long operations

### 5. Information Architecture
- **Progressive Disclosure**: Complex workflows broken into steps
- **Contextual Help**: Descriptions and tooltips where needed
- **Clear Hierarchy**: Visual hierarchy through typography and spacing
- **Logical Flow**: Sequential workflow from setup through alliance selection

---

## Workflow Dependencies

### 1. Setup → Field Selection
- User must complete setup before field selection is meaningful
- Event configuration drives available data

### 2. Field Selection → Validation
- Field categorization required for validation algorithms
- Critical fields must be mapped properly

### 3. Validation → Picklist
- Data quality issues should be resolved before picklist generation
- Clean data improves picklist accuracy

### 4. Picklist → Alliance Selection
- Picklist must be generated and locked before live selection
- Rankings drive alliance selection strategy

---

## Preservation Requirements

During refactoring, these workflow characteristics MUST be preserved:

### Visual Design
1. **Exact color scheme** - Blue header, color-coded cards
2. **Typography hierarchy** - Font sizes, weights, spacing
3. **Layout structure** - Grid systems, panel arrangements
4. **Component styling** - Buttons, forms, tables, cards

### User Experience
1. **Navigation flow** - Same page sequence and transitions
2. **Form behavior** - Same validation and interaction patterns
3. **Data display** - Same table structures and information density
4. **Progress indicators** - Same feedback mechanisms

### Functional Behavior
1. **Step-by-step workflows** - Same progression through setup
2. **Tab navigation** - Same tab structures and content organization
3. **Modal interactions** - Same confirmation and correction flows
4. **Real-time updates** - Same progress tracking and live updates

### Content and Messaging
1. **Page titles and descriptions** - Exact text content
2. **Help text and instructions** - Same user guidance
3. **Status messages** - Same success/error messaging
4. **Button labels** - Consistent action labeling

**Breaking any of these workflow patterns will disrupt user experience and require user retraining.**