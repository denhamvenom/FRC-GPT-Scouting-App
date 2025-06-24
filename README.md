# FRC-GPT-Scouting-App

A year‑agnostic, team‑agnostic, data‑agnostic toolkit that automates FRC event scouting, data validation, pick‑list building and live alliance‑selection using GPT‑4.

## Purpose & Scope
* **Field Selection** – Select which fields from your scouting spreadsheet to analyze; game manual analysis for strategic insights
* **Data Validation** – Flag missing or outlier match rows and let users rescout virtually, replace with averages, or ignore with reason
* **Pick‑List Builder** – Create ranked first/second/third‑pick lists from validated data given user‑ranked priorities; allow manual drag‑drop; includes both scouting and superscouting metrics
* **Team Comparison & Re-Ranking** – Interactive chat-style interface for comparing 2-3 teams using GPT analysis; provides detailed narrative explanations and suggested re-rankings with conversational follow-up questions
* **Alliance Selection** – Live draft tracker with realistic FRC rules; automatically excludes alliance captains for 2nd/3rd picks; real-time updates with visual team status indicators
* **Progress Tracking** – Real-time progress updates during picklist generation with percentage completion and time estimates

## Key Design Decisions
| Topic | Decision | Rationale |
| ----- | -------- | --------- |
| **Language** | Python 3.12 + FastAPI backend; React/Vite/TypeScript frontend | async, typing, rich ecosystem |
| **LLM** | OpenAI `gpt‑4.1` via openai‑python ≥1.52 | streaming JSON output, high quality |
| **Data sources** | Statbotics (EPA metrics), The Blue Alliance (teams/matches), Google Sheets (scouting) | open, documented APIs |
| **Config** | Year‑specific field‑map JSON under `backend/app/config` | zero code change for new games |
| **Database** | SQLite with SQLAlchemy ORM | lightweight, serverless, easy deployment |
| **Caching** | In-memory caching for active operations, LocalStorage for UI state | optimal performance balance |
| **Testing** | pytest for backend, Jest for frontend | comprehensive test coverage |

## Folder / File Structure (trunk)
```
backend/
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── setup.py               # Learning module & event setup
│   │   ├── validate.py            # Validation API with outlier detection
│   │   ├── unified_dataset.py     # Dataset builder & retrieval
│   │   ├── schema_selections.py   # Field selections API
│   │   ├── schema.py             # Schema mapping endpoints
│   │   ├── schema_save.py        # Schema persistence
│   │   ├── schema_superscout.py  # Superscouting schema management
│   │   ├── picklist_generator.py  # Picklist generation endpoint
│   │   ├── picklist_analysis.py   # Picklist metrics analysis
│   │   ├── alliance_selection.py  # Alliance selection API
│   │   ├── field_selection.py     # Field categorization
│   │   ├── progress.py           # Progress tracking API
│   │   ├── debug_logs.py         # Debug logs viewer
│   │   ├── archive.py            # Event archival system
│   │   ├── sheet_config.py       # Sheet configuration management
│   │   ├── sheets_headers.py     # Sheet header retrieval
│   │   └── sheets.py             # Google Sheets integration
│   ├── database/
│   │   ├── db.py                 # SQLAlchemy DB configuration
│   │   └── models.py             # Database models
│   ├── services/
│   │   ├── statbotics_client.py           # EPA metrics retrieval
│   │   ├── tba_client.py                  # The Blue Alliance API wrapper
│   │   ├── learning_setup_service.py      # Learning module service
│   │   ├── data_validation_service.py     # Validation logic with outliers
│   │   ├── unified_event_data_service.py  # Dataset building service
│   │   ├── picklist_generator_service.py  # GPT picklist generation
│   │   ├── picklist_analysis_service.py   # Metrics analysis service
│   │   ├── team_comparison_service.py     # Team comparison with narrative analysis
│   │   ├── sheets_service.py              # Google Sheets service
│   │   ├── sheet_config_service.py        # Sheet configuration
│   │   ├── schema_service.py              # Schema management
│   │   ├── schema_superscout_service.py   # Superscout schema
│   │   ├── schema_loader.py               # Schema file loader
│   │   ├── manual_parser_service.py       # Game manual parser
│   │   ├── progress_tracker.py            # Operation progress tracking
│   │   ├── archive_service.py             # Event archival logic
│   │   ├── scouting_parser.py             # Scouting data parser
│   │   ├── superscout_parser.py           # Enhanced superscout parser
│   │   └── cache_service.py               # Caching utilities
│   ├── config/
│   │   ├── statbotics_field_map_2025.json
│   │   └── statbotics_field_map_DEFAULT.json
│   ├── data/
│   │   ├── scouting_app.db               # SQLite database
│   │   └── embeddings/                   # Cached embeddings
│   └── main.py
├── logs/                                  # Log files directory
├── tests/
│   ├── test_health.py
│   ├── test_statbotics_client.py
│   └── test_picklist.py
├── requirements.txt                       # Python dependencies
├── requirements-dev.txt                   # Development dependencies
├── MIGRATION.md                          # Database migration guide
├── PICKLIST_COMPACT.md                   # Picklist optimization docs
└── picklist_generator.log                # Picklist generation logs

frontend/
├── src/
│   ├── pages/
│   │   ├── Home.tsx                      # Landing page
│   │   ├── Setup.tsx                     # Initial setup wizard
│   │   ├── FieldSelection.tsx            # Field categorization
│   │   ├── EventManager.tsx              # Event selection/management
│   │   ├── SchemaMapping.tsx             # Schema mapping UI
│   │   ├── SchemaSuperMapping.tsx        # Superscout schema UI
│   │   ├── Workflow.tsx                  # Workflow guide
│   │   ├── Validation.tsx                # Data validation UI
│   │   ├── PicklistNew.tsx               # Picklist builder
│   │   ├── PicklistView.tsx              # Picklist viewer
│   │   ├── AllianceSelection.tsx         # Live alliance selection
│   │   ├── UnifiedDatasetBuilder.tsx     # Dataset building UI
│   │   └── DebugLogs.tsx                 # Debug log viewer
│   ├── components/
│   │   ├── Navbar.tsx                    # Navigation component
│   │   ├── PicklistGenerator.tsx         # Picklist display component
│   │   ├── TeamComparisonModal.tsx       # Team comparison & re-ranking modal
│   │   ├── ProgressTracker.tsx           # Progress tracking UI
│   │   ├── EventArchiveManager.tsx       # Event archive UI
│   │   ├── SheetConfigManager.tsx        # Sheet config UI
│   │   └── CategoryTabs.tsx              # Tab navigation
│   ├── services/
│   │   └── AppStateService.ts            # Application state management
│   └── App.tsx                           # Main app component
├── public/                               # Static assets
├── tailwind.config.js                    # Tailwind CSS config
├── vite.config.ts                        # Vite configuration
├── package.json                          # Node dependencies
└── README.md                             # Frontend documentation
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
| `/api/validate/enhanced` | POST JSON | `{ unified_dataset_path }` | Validation results with outliers |
| `/api/validate/apply-correction` | POST JSON | `{ unified_dataset_path, year, corrections }` | Correction status |
| `/api/picklist/analyze` | POST JSON | `{ unified_dataset_path, [priorities], [strategy_prompt] }` | Available metrics & analysis |
| `/api/picklist/generate` | POST JSON | `{ unified_dataset_path, your_team_number, pick_position, priorities, exclude_teams, cache_key? }` | Ranked picklist |
| `/api/picklist/generate/status` | POST JSON | `{ cache_key }` | Generation progress status |
| `/api/picklist/compare-teams` | POST JSON | `{ unified_dataset_path, team_numbers[], your_team_number, pick_position, priorities, question?, chat_history? }` | Team comparison with narrative analysis |
| `/api/progress/{operation_id}` | GET | - | Progress tracking data |
| `/api/alliance/lock-picklist` | POST JSON | `{ team_number, event_key, year, first_pick_data, second_pick_data, third_pick_data }` | Lock picklist |
| `/api/alliance/picklist/{picklist_id}` | DELETE | - | Unlock picklist |
| `/api/alliance/selection/create` | POST JSON | `{ picklist_id, event_key, year, team_list }` | Create alliance selection |
| `/api/alliance/selection/{selection_id}` | GET | - | Alliance selection state |
| `/api/alliance/selection/team-action` | POST JSON | `{ selection_id, team_number, action, alliance_number }` | Record team action |
| `/api/archive/event-summary` | GET | `{ event_key, year }` | Event archive summary |
| `/api/archive/event` | POST JSON | `{ event_key, year }` | Archive event data |
| `/api/debug/logs/picklist` | GET | `lines (optional)` | Recent picklist logs |

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/frc-gpt-scouting-app.git
   cd frc-gpt-scouting-app
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Set up `.env` file in backend directory:
   ```
   OPENAI_API_KEY=your_key_here
   TBA_API_KEY=your_key_here
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_SERVICE_ACCOUNT_FILE=path_to_service_account.json
   ```

5. Run database migrations:
   ```bash
   cd backend
   python migrate_locked_picklist.py
   ```

6. Run the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

7. Run the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
### Docker Quickstart
To run the stack with Docker, install Docker and Docker Compose then execute:
```bash
docker-compose up --build
```
The backend will be on http://localhost:8000 and the frontend on http://localhost:5173.


## Features

### Data Management
* **Unified Dataset Building**: Combines data from Google Sheets, The Blue Alliance, and Statbotics into a comprehensive dataset
* **Schema Mapping**: Auto-maps spreadsheet columns to standardized fields with user correction
* **LocalStorage Persistence**: Maintains UI state across page navigation
* **Event Archival**: Complete event data backup with team lists and picklists

### Validation
* **Missing Data Detection**: Identifies matches without scouting records
* **Statistical Outlier Detection**: Uses Z-score, IQR, and team-specific analysis
* **Virtual Rescouting**: Replace missing data with averages or manual entry
* **Audit Trail**: Tracks all corrections with timestamps and reasons

### Picklist Generation
* **Ultra-Compact JSON Format**: 75% token reduction for efficient GPT usage
* **Progress Tracking**: Real-time updates with percentage and time estimates
* **Natural Language Strategy**: Parse strategy descriptions into weighted priorities
* **Superscouting Integration**: Qualitative metrics for robot assessment
* **Team Exclusion Logic**: Realistic alliance selection rules
* **Batch Processing**: Handles large team counts efficiently

### Alliance Selection
* **FRC Rules Compliance**: Teams that decline can become captains
* **Live Draft Board**: Real-time updates with visual status indicators
* **Three Round Support**: Full alliance selection including backup robots
* **Automatic Exclusions**: Smart filtering based on pick position
* **Team Status Tracking**: Visual indicators for captain/picked/declined

### User Experience
* **Progress Indicators**: Loading bars with estimated completion times
* **Error Recovery**: Robust JSON parsing with fallback mechanisms
* **Pagination**: Configurable items per page for large datasets
* **Confirmation Dialogs**: Prevent accidental data loss
* **Debug Logging**: Comprehensive logs with viewer UI

## Current Limitations & Future Work
* Event key selector needs improvement (currently defaults to 2025arc)
* Mobile compatibility needs optimization
* OAuth implementation for better API key management
* Additional visualizations for team performance analysis
* Support for multiple simultaneous events
* Export functionality for picklists and alliance selections

## Recent Updates (May 2025)
* **Progress Tracking**: Added real-time progress updates during picklist generation
* **Ultra-Compact JSON**: Implemented 75% token reduction for GPT responses
* **Event Archival**: Complete event backup system with all associated data
* **Performance Optimization**: Threading for API calls with progress updates
* **UI Enhancements**: Better visual indicators and user feedback
* **Database Migrations**: Added support for excluded teams and strategy prompts

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
* FIRST Robotics Competition for the amazing community
* Statbotics for EPA metrics
* The Blue Alliance for comprehensive FRC data
* OpenAI for GPT-4 capabilities