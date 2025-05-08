# FRC-GPT-Scouting-App

A year‑agnostic, team‑agnostic, data‑agnostic toolkit that automates FRC event scouting, data validation, pick‑list building and live alliance‑selection using GPT‑4.

## Purpose & Scope
* **Field Selection** – Select which fields from your scouting spreadsheet to analyze; optionally use game manual for strategic insights
* **Validation** – Flag missing or outlier match rows and let users rescout virtually, replace with averages, or ignore with reason
* **Pick‑List Builder** – Create ranked first/second/third‑pick lists from validated data given user‑ranked priorities; allow manual drag‑drop; includes both scouting and superscouting metrics
* **Realistic Alliance Selection** – Automatically excludes alliance captains when generating second and third picks; live draft tracker that strikes picked teams and re‑ranks remaining candidates

## Key Design Decisions
| Topic | Decision | Rationale |
| ----- | -------- | --------- |
| **Language** | Python 3.12 + FastAPI backend; React/Vite frontend | async, typing, rich ecosystem |
| **LLM** | OpenAI `gpt‑4o` via openai‑python ≥1.0 | streaming JSON output, high quality |
| **Data sources** | Statbotics (per‑year EPA), The Blue Alliance (teams/matches), Google Sheets (scouting) | open, documented APIs |
| **Config** | Year‑specific field‑map JSON under `backend/app/config` | zero code change for new games |
| **Paths** | Always resolved from `__file__` | uvicorn and tests run consistently |
| **Testing** | pytest, `python -m` module runs | import‑safe, path‑safe |

## Folder / File Structure (trunk)
```
backend/
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── setup.py           # Learning module
│   │   ├── validate.py        # Validation API
│   │   ├── unified_dataset.py # Dataset builder
│   │   ├── schema_selections.py  # Field selections API
│   │   ├── picklist_generator.py # Picklist generator
│   │   ├── picklist_analysis.py  # Picklist metrics analysis
│   │   ├── debug_logs.py      # Debug logs API
│   │   └── sheets.py          # Google Sheets integration
│   ├── services/
│   │   ├── statbotics_client.py
│   │   ├── tba_client.py
│   │   ├── learning_setup_service.py
│   │   ├── data_validation_service.py
│   │   ├── unified_event_data_service.py
│   │   ├── picklist_generator_service.py   # Full picklist generation with GPT chunking
│   │   ├── picklist_analysis_service.py    # Metrics analysis service
│   │   ├── sheets_service.py
│   │   ├── schema_service.py
│   │   ├── schema_superscout_service.py
│   │   ├── schema_loader.py
│   │   └── manual_parser_service.py
│   ├── config/
│   │   ├── statbotics_field_map_2025.json
│   │   └── statbotics_field_map_DEFAULT.json
│   └── main.py
└── tests/
    └── test_statbotics_client.py
frontend/
├── src/
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Setup.tsx
│   │   ├── FieldSelection.tsx
│   │   ├── Workflow.tsx
│   │   ├── Validation.tsx
│   │   ├── PicklistNew.tsx       # Picklist generation page
│   │   ├── UnifiedDatasetBuilder.tsx # Dataset building UI
│   │   └── DebugLogs.tsx         # Debug logs viewer
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── PicklistGenerator.tsx    # Picklist generation component with pagination
│   │   └── ProgressTracker.tsx      # Progress tracking component
│   └── App.tsx
└── vite.config.ts
```

## Critical Data Models & Endpoints
### Endpoints
| Route | Method | Body | Response |
|-------|--------|------|----------|
| `/api/setup/start` | **POST multipart/form‑data** | `year:int` **required**  <br>`manual_url:str?` <br>`manual_file:PDF?` | `{ year, manual_info, sample_teams[] }` |
| `/api/health/ping` | GET | – | `{status:"ok"}` |
| `/api/schema/save-selections` | POST JSON | `{ field_selections, manual_url, year }` | Selection save status |
| `/api/unified/build` | POST JSON | `{ event_key, year, force_rebuild }` | Dataset build status & path |
| `/api/unified/dataset` | GET | `{ event_key }` or `{ path }` | Complete unified dataset |
| `/api/unified/status` | GET | `{ event_key, year }` | Dataset existence and status |
| `/api/validate/enhanced` | GET | `{ unified_dataset_path }` | Validation results with outliers |
| `/api/validate/apply-correction` | POST JSON | `{ team_number, match_number, corrections }` | Correction status |
| `/api/picklist/analyze` | POST JSON | `{ unified_dataset_path, [priorities], [strategy_prompt] }` | Available metrics, statistical analysis, team rankings |
| `/api/picklist/generate` | POST JSON | `{ unified_dataset_path, your_team_number, pick_position, priorities, exclude_teams }` | Ranked picklist with reasoning |
| `/api/debug/logs/picklist` | GET | `lines (optional)` | Recent picklist generation logs for debugging |

## Setup and Installation

1. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Set up `.env` file with:
   ```
   OPENAI_API_KEY=your_key_here
   TBA_API_KEY=your_key_here
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_SERVICE_ACCOUNT_FILE=path_to_service_account.json
   ```

4. Run the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

5. Run the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Open TODOs / Pain Points
* Event key selector (currently hard‑coded to `2025arc` in learning prototype)
* Visualizations for team performance
* Mobile compatibility improvements
* OAuth / token management UI for Sheets, TBA, Statbotics, OpenAI

## Recent Improvements
* **Complete Picklist Approach**: Switched from chunking to one-shot generation to avoid duplication and ensure complete coverage
* **Enhanced Missing Teams Handling**: Added two-phase ranking with auto-fallback for teams missed by GPT
* **Smart Handling of Auto-Added Teams**: UI now offers option to get more accurate rankings for auto-added teams
* **Improved Error Recovery**: Enhanced JSON parsing with robust fallback mechanisms for handling truncated responses
* **User Experience Enhancements**: Progress tracking with estimated completion time and percentage
* **Visual Indicators**: Clear badges and explanations for auto-added teams
* **Performance Optimization**: Optimized tokens (3500 for output) and reduced data size to fit complete picklists
* **Local Data Persistence**: Added localStorage-based persistence for picklist data, preventing data loss when navigating between pages
* **Debug Logging System**: Created comprehensive logging for picklist generation with a dedicated debug UI
* **Pagination Controls**: Added pagination to the picklist view with configurable items per page
* **Clear Data Confirmation**: Implemented confirmation dialog when clearing saved picklist data
* **Superscouting Integration**: Added superscouting metrics to picklist generation and analysis
* **Team Exclusion Logic**: Implemented realistic alliance selection logic (excludes alliance captains for 2nd/3rd picks)