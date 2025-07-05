# Game Label Extraction Feature - Sprint Plan

**Purpose**: Add scouting data field label extraction after manual parsing to improve field categorization and GPT understanding  
**Timeline**: 3-4 Claude-Code sessions  
**Priority**: Functional implementation over polish

## CRITICAL CLARIFICATION - WHAT ARE "LABELS"?

**❌ NOT this**: Game elements from manual (L1, L2, CORAL, REEF, etc.)  
**✅ THIS**: Scouting data field metrics teams would track about robot performance

**Examples of CORRECT labels:**
- `auto_coral_L1_scored` - Count of coral scored in L1 during autonomous
- `teleop_defense_effectiveness_rating` - 1-5 rating of defense effectiveness  
- `endgame_climb_successful` - Boolean for successful climb
- `reliability_mechanical_failures` - Count of mechanical breakdowns

**Purpose**: These labels help categorize actual scouting data columns when teams import their spreadsheets. Instead of generic "auto_points", we want specific "auto_coral_L4_scored" that GPT can understand and use for better analysis.

## Important: Context Management
Each sprint will be executed in a new Claude Code session. The prompts include specific files to read first to ensure proper context. Always paste the entire prompt including the file reading instructions to maintain consistency across implementation.

## Technical Requirements
- Use existing .env for GPT model selection (OPENAI_MODEL)
- Maintain current frontend visual structure
- Support ngrok deployment with frontend REACT_APP_API_BASE_URL
- Leverage existing service patterns and infrastructure

## CRITICAL MISSING PIECES (Address These First!)

### 1. **Manual Data Format** ✅ RESOLVED
The system already produces `manual_text_{year}.json` in the correct format for label extraction.

### 2. **Integration Point** ✅ IDENTIFIED
Label extraction should happen in `backend/app/api/manuals.py` in the `trigger_context_extraction()` function (line 22-148), right after game context extraction.

### 3. **UI Flow Integration** ✅ SOLUTION
**Approach**: Add "Review Game Labels" button in the success message after manual processing (Setup.tsx line 965-972). This makes it optional and non-blocking.
**Implementation**: Button triggers navigation to `/setup/labels` route.

### 4. **Error Recovery Strategy** ✅ SOLUTION
**Approach**: Label extraction is optional. If it fails, show warning but allow user to continue. Store empty labels file as fallback.
**Implementation**: Try-catch around label extraction, graceful degradation.

### 5. **Quick Test Data** ✅ SOLUTION
**Approach**: Use existing `backend/app/data/manual_text_2025.json` file for testing during development.
**Implementation**: Load this file in test scripts and validate label extraction.

### 6. **Success Validation** ✅ SOLUTION
**Approach**: Create simple test that compares GPT responses with and without labels using same team data.
**Implementation**: Test script that calls picklist generation twice - once with labels, once without.

### 7. **Data Processing Integration** ✅ IDENTIFIED
**Current State**: Field mappings are applied during parsing in `scouting_parser.py` and `superscout_parser_enhanced.py` using schema files.
**Required Change**: Schema files need to include game label mappings, and parsers need to use label-enhanced field names.
**Integration Point**: Modify Field Selection (Sprint 3) to save label mappings in schema files.

---

## Sprint 1: Backend Label Extraction Service ✅ COMPLETED
**Duration**: 1 Claude-Code session  
**Goal**: Create backend service for extracting scouting data field labels from manual

### User Prompt:
```
First, please read these files for context:
1. GAME_LABEL_EXTRACTION_SPRINT_PLAN.md - for the overall feature plan
2. CLAUDE.md - for coding standards and patterns
3. backend/app/services/game_context_extractor_service.py - for service pattern reference
4. backend/app/services/picklist_gpt_service.py - for GPT integration patterns
5. backend/.env.example - for environment variable structure

I need to implement Sprint 1 of the game label extraction feature. Create a new service that extracts SCOUTING DATA FIELD LABELS from manual - metrics teams would track about robot performance (like auto_coral_L1_scored, teleop_defense_rating, endgame_climb_successful). The service should:
1. Create game_label_extractor_service.py following existing service patterns
2. Add extraction method that identifies specific scouting metrics teams would track
3. Store results in backend/app/data/game_labels_YEAR.json
4. Add API endpoints in a new game_labels.py file
5. Use OPENAI_MODEL from .env for GPT calls
6. INTEGRATE label extraction into backend/app/api/manuals.py trigger_context_extraction() function (line 22-148) - call after game context extraction succeeds

CRITICAL: Label extraction should be optional - if it fails, log warning but continue. Test with existing manual_text_2025.json file.
```

### Deliverables:
- [x] `backend/app/services/game_label_extractor_service.py` - Service extracts 34 scouting metrics
- [x] `backend/app/api/v1/endpoints/game_labels.py` - Complete REST API 
- [x] Update `backend/app/main.py` to include new router
- [x] Integration with `backend/app/api/manuals.py` - Optional execution after context extraction
- [x] Test extraction with sample manual data - Successfully extracted metrics like auto_coral_L1_scored, teleop_defense_effectiveness_rating, endgame_climb_successful, etc.

### Key Results:
- **34 scouting metrics extracted** covering autonomous, teleop, endgame, defense, reliability, and strategic categories
- **Data types**: count, rating, boolean, time with appropriate ranges
- **Sample metrics**: `auto_coral_L1_scored` (count 0-3), `defense_effectiveness_rating` (rating 1-5), `endgame_climb_successful_shallow` (boolean)
- **File generated**: `backend/app/data/game_labels_2025.json`

---

## Sprint 2: Frontend Label Management UI
**Duration**: 1 Claude-Code session  
**Goal**: Create UI for reviewing and editing extracted labels

### User Prompt:
```
First, please read these files for context:
1. GAME_LABEL_EXTRACTION_SPRINT_PLAN.md - for the overall feature plan
2. CLAUDE.md - for coding standards
3. frontend/src/pages/FieldSelection.tsx - for UI style reference
4. frontend/src/components/PicklistGenerator/hooks/usePicklistState.ts - for state management patterns
5. frontend/src/config.ts - for API configuration patterns
6. backend/app/api/v1/endpoints/game_labels.py - to understand the API (from Sprint 1)

I need to implement Sprint 2 - the frontend UI for scouting label management. Create a new component that:
1. Integrates into existing setup flow after manual parsing
2. Shows extracted SCOUTING METRICS in an editable table/list format with columns for label name, category, data type, range, description
3. Allows adding, editing, and removing scouting metrics
4. Maintains the existing visual style (similar to Field Selection page)
5. Uses REACT_APP_API_BASE_URL from frontend .env for API calls
6. Saves labels back to the backend
7. Add routing for /setup/labels path
8. Add "Review Scouting Labels" button to Setup.tsx success message (line 965-972)

CRITICAL: UI should be optional - users can skip if they want. Test with the 34 scouting metrics extracted in Sprint 1 (auto_coral_L1_scored, etc.).
```

### Deliverables:
- [ ] `frontend/src/components/GameLabelManager.tsx`
- [ ] `frontend/src/hooks/useGameLabels.ts` (API integration)
- [ ] Add routing for /setup/labels path
- [ ] Add "Review Game Labels" button to Setup.tsx success message
- [ ] Test with labels from Sprint 1

---

## Sprint 3: Field Selection Integration
**Duration**: 1 Claude-Code session  
**Goal**: Enhance Field Selection with label awareness

### User Prompt:
```
First, please read these files for context:
1. GAME_LABEL_EXTRACTION_SPRINT_PLAN.md - for the overall feature plan
2. frontend/src/pages/FieldSelection.tsx - the file we'll be modifying
3. frontend/src/hooks/useGameLabels.ts - API hook from Sprint 2
4. backend/app/data/schema_2025.json - to understand schema structure
5. frontend/src/components/GameLabelManager.tsx - to see the label structure from Sprint 2
6. backend/app/services/scouting_parser.py - to see how schema is used in parsing
7. backend/app/services/schema_loader.py - to understand schema loading

I need to implement Sprint 3 - integrating scouting labels into Field Selection. Please:
1. Modify FieldSelection.tsx to load scouting labels for the current year
2. Enhance autoCategorizeField() to check against scouting labels first (e.g., match "Auto_Coral_L1" column to "auto_coral_L1_scored" label)
3. Show matched label info when a field matches a scouting label (display label description, data type, expected range)
4. Update the field mapping to include label references in schema files
5. Ensure the visual layout remains the same, just add label context
6. Store label-field mappings in the schema files for use by data parsers
7. CRITICAL: Schema files must include label mappings so scouting_parser.py can use enhanced field names like "auto_coral_L1_scored" instead of generic "auto_points"

This should dramatically improve auto-categorization accuracy by matching spreadsheet columns to specific scouting metrics.
```

### Deliverables:
- [ ] Enhanced `frontend/src/pages/FieldSelection.tsx`
- [ ] Updated auto-categorization logic with label awareness
- [ ] Label-field mapping storage in schema files
- [ ] Visual indicator for label matches
- [ ] Schema files include label mappings for data processing

---

## Sprint 4: GPT Context Enhancement & Testing
**Duration**: 1 Claude-Code session  
**Goal**: Include labels in GPT prompts and test full workflow

### User Prompt:
```
First, please read these files for context:
1. GAME_LABEL_EXTRACTION_SPRINT_PLAN.md - for the overall feature plan
2. backend/app/services/picklist_gpt_service.py - to modify GPT prompts
3. backend/app/services/data_aggregation_service.py - to add label loading
4. backend/app/data/game_labels_2025.json - to see the label format (from Sprint 1)
5. backend/app/data/schema_2025.json - to see label-field mappings (from Sprint 3)
6. backend/app/services/scouting_parser.py - to verify schema integration
7. CLAUDE.md - for testing standards

I need to implement Sprint 4 - the final integration. Please:
1. Update picklist_gpt_service.py to include scouting labels in prompts (e.g., "auto_coral_L1_scored: 2.3 avg" instead of "auto_points: 8.5")
2. Modify data_aggregation_service.py to load and use label mappings from schema files
3. Ensure scouting labels provide context when analyzing team data (GPT knows "auto_coral_L4_scored" means high-level autonomous scoring)
4. Verify that scouting_parser.py correctly uses label-enhanced schema files
5. Test the complete workflow from manual parsing through picklist generation
6. Add any missing error handling or edge cases
7. Create a simple test script to validate that GPT analysis improves with specific scouting metrics vs generic field names
Focus on making sure the scouting labels dramatically improve GPT's understanding of team performance data.
```

### Deliverables:
- [ ] Enhanced GPT services with label context
- [ ] Updated data processing to use labels
- [ ] Verified schema integration with data parsers
- [ ] Test script for validation
- [ ] Bug fixes and error handling
- [ ] End-to-end workflow testing

---

## Implementation Notes

### File Structure:
```
backend/
├── app/
│   ├── services/
│   │   └── game_label_extractor_service.py (NEW)
│   ├── api/v1/endpoints/
│   │   └── game_labels.py (NEW)
│   └── data/
│       └── game_labels_2025.json (Generated)
frontend/
├── src/
│   ├── components/
│   │   └── GameLabelManager.tsx (NEW)
│   └── hooks/
│       └── useGameLabels.ts (NEW)
```

### Environment Variables:
```bash
# Backend .env
OPENAI_MODEL=gpt-4o-mini

# Frontend .env
REACT_APP_API_BASE_URL=https://your-ngrok-url.ngrok.io
```

### Key Design Decisions:
1. **Minimal UI Changes**: Keep existing visual structure, add functionality inline
2. **Service Pattern**: Follow existing service patterns for consistency
3. **Storage Format**: JSON files in data directory (like existing schemas)
4. **API Design**: RESTful endpoints under /api/v1/game-labels
5. **Error Handling**: Graceful fallbacks if label extraction fails

### Testing Approach:
1. Test each sprint independently
2. Manual testing through UI
3. API testing with curl/Postman
4. End-to-end test in Sprint 4

### Risk Mitigation:
- If label extraction fails, system continues with existing categorization
- Labels are suggestions, not requirements
- All changes are backwards compatible
- No breaking changes to existing workflows

---

## Quick Reference Commands

### Backend Development:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development:
```bash
cd frontend
npm start
```

### Testing Label Extraction:
```bash
# Extract labels
curl -X POST http://localhost:8000/api/v1/game-labels/extract \
  -H "Content-Type: application/json" \
  -d '{"manual_data": {...}}'

# Get labels
curl http://localhost:8000/api/v1/game-labels/2025

# Update labels  
curl -X POST http://localhost:8000/api/v1/game-labels/2025 \
  -H "Content-Type: application/json" \
  -d '{"labels": [...]}'
```

---

## Progress Tracking
After each sprint, update the checkboxes in the Deliverables section to track completion. If a sprint reveals issues or needs from previous sprints, include those fixes in the current sprint rather than going back.

### Inter-Sprint Dependencies
- Sprint 2 depends on the API from Sprint 1
- Sprint 3 depends on components from Sprint 2  
- Sprint 4 depends on all previous sprints

If you need to check work from a previous sprint, the key files created will be:
- Sprint 1: `backend/app/services/game_label_extractor_service.py`, `backend/app/api/v1/endpoints/game_labels.py`
- Sprint 2: `frontend/src/components/GameLabelManager.tsx`, `frontend/src/hooks/useGameLabels.ts`
- Sprint 3: Modified `frontend/src/pages/FieldSelection.tsx` with label integration
- Sprint 4: Modified GPT services with label context

## Simplification Decisions (For Speed & Effectiveness)

### What We're NOT Doing:
- **Complex UI**: Basic table/list interface, no fancy styling
- **Advanced Validation**: Simple required field validation only
- **Migration Logic**: This is a new feature, no existing data migration
- **Extensive Testing**: Focus on manual testing, minimal automated tests
- **Performance Optimization**: Focus on functionality first
- **Multiple Game Years**: Start with current year (2025) only

### What We're Keeping Simple:
- **Storage**: Plain JSON files (no database changes)
- **API**: Simple REST endpoints with basic error handling
- **UI Integration**: Optional button in existing flow
- **Error Handling**: Log warnings, allow continuation
- **Validation**: GPT comparison test only

## Success Criteria
- [ ] Labels can be extracted from game manual
- [ ] Users can review and edit labels
- [ ] Field Selection uses labels for better categorization
- [ ] GPT receives label context for improved analysis
- [ ] No visual breaking changes
- [ ] Works with ngrok deployment
- [ ] Maintains existing error handling patterns