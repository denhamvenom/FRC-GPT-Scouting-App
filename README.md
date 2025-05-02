# FRC-GPT-Scouting-App

A year‑agnostic, team‑agnostic, data‑agnostic toolkit that automates FRC event scouting, data validation, pick‑list building and live alliance‑selection using GPT‑4.

## Purpose & Scope
* **Field Selection** – Select which fields from your scouting spreadsheet to analyze; optionally use game manual for strategic insights
* **Validation** – Flag missing or outlier match rows and let users rescout virtually, replace with averages, or ignore with reason
* **Pick‑List Builder** – Create ranked first/second/third‑pick lists from validated data given user‑ranked priorities; allow manual drag‑drop
* **Alliance‑Selection Assistant** – Live draft tracker that strikes picked teams and re‑ranks remaining candidates

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
│   │   ├── picklist.py        # Picklist generator
│   │   └── sheets.py          # Google Sheets integration
│   ├── services/
│   │   ├── statbotics_client.py
│   │   ├── tba_client.py
│   │   ├── learning_setup_service.py
│   │   ├── data_validation_service.py
│   │   ├── unified_event_data_service.py
│   │   ├── picklist_service.py
│   │   ├── sheets_service.py
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
│   │   └── Validation.tsx
│   ├── components/
│   │   └── Navbar.tsx
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
| `/api/validate/enhanced` | GET | `{ unified_dataset_path }` | Validation results with outliers |
| `/api/validate/apply-correction` | POST JSON | `{ team_number, match_number, corrections }` | Correction status |

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
* Front‑end pages for Alliance Selection
* Visualizations for team performance
* Mobile compatibility improvements
* OAuth / token management UI for Sheets, TBA, Statbotics, OpenAI
* Add user-friendly error handling and recovery