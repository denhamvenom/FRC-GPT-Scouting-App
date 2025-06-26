# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend
pip install -r requirements.txt           # Install dependencies
pip install -r requirements-dev.txt      # Install dev dependencies
uvicorn app.main:app --reload            # Start development server
python migrate_locked_picklist.py       # Run database migrations
./run_migrations.sh                      # Run all migrations
pytest                                   # Run tests
pytest -m integration                    # Run integration tests
black . --line-length 100               # Format code
ruff check .                            # Lint code
mypy .                                   # Type checking
```

### Frontend (React/TypeScript)
```bash
cd frontend
npm install                              # Install dependencies
npm run dev                             # Start development server
npm run build                           # Build for production
npm run preview                         # Preview production build
```

### Docker
```bash
docker-compose up --build               # Run full stack
```

## Architecture Overview

This is an FRC robotics scouting application that uses GPT-4 for intelligent data analysis and picklist generation. The system follows a service-oriented architecture with clear separation between data sources, processing, and presentation layers.

### Core Data Flow
1. **Data Ingestion**: Pulls from Google Sheets (scouting), The Blue Alliance API (teams/matches), and Statbotics (EPA metrics)
2. **Unified Processing**: Combines all sources with user-selected field mappings into comprehensive datasets
3. **Validation Pipeline**: Statistical outlier detection with Z-score, IQR, and team-specific analysis
4. **AI Processing**: Uses GPT-4.1 with ultra-compact JSON format (75% token reduction) for picklist generation
5. **Alliance Selection**: Live draft tracking with FRC-compliant rules and real-time status updates

### Key Architectural Patterns
- **Service Layer Pattern**: Business logic separated from API endpoints in `backend/app/services/`
- **Repository Pattern**: Database access abstracted through SQLAlchemy models
- **Progress Tracking**: Non-blocking operations with real-time updates via threading
- **Caching Strategy**: Multi-layer caching (in-memory, LocalStorage, file cache, database)
- **Ultra-Compact JSON**: Custom serialization format for efficient GPT token usage

### Database Models
- **LockedPicklist**: Generated picklists with excluded teams and strategy prompts
- **AllianceSelection**: Draft event state tracking
- **Alliance/TeamSelectionStatus**: Team assignments and status (captain/picked/declined)
- **SheetConfiguration**: Google Sheets tab mapping per event
- **ArchivedEvent**: Complete event data backups

## Critical Integrations

### External APIs
- **OpenAI GPT-4.1**: Picklist generation, team comparison, strategy parsing
- **The Blue Alliance**: Team data, match results, event information
- **Statbotics**: EPA metrics with year-specific field mapping
- **Google Sheets API**: Scouting and superscouting data retrieval

### Year-Specific Configuration
- Field mappings in `backend/app/config/statbotics_field_map_YEAR.json`
- Schema definitions in `backend/app/data/schema_YEAR.json`
- Robot groups and critical mappings in `backend/app/data/`

## Environment Setup

Required environment variables in `backend/.env`:
```
OPENAI_API_KEY=your_key_here
TBA_API_KEY=your_key_here
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=path_to_service_account.json
```

Google service account JSON file should be placed in `secrets/google-service-account.json`.

## Code Style Requirements

### Python (Backend)
- Black formatting with line-length 100
- Ruff linting with specific ignores: E402, E712, F401, F823, F841
- Strict type hints enforced by mypy
- Async/await for all I/O operations
- Google-style docstrings on public functions
- Thread safety considerations for progress tracking

### TypeScript (Frontend)
- Functional components with hooks only
- Strict TypeScript interfaces for all props and state
- Tailwind CSS for styling
- LocalStorage with proper serialization
- Custom hooks for shared logic

## Testing Strategy

### Backend Tests
```bash
pytest -q                               # Quick unit tests (no external APIs)
pytest -m integration                   # Integration tests (may hit external APIs)
```

### Frontend Tests
- Component render tests
- Service layer mocking
- Error boundary testing

## Performance Considerations

### Ultra-Compact JSON Format
The system uses a custom compact JSON format for GPT responses that reduces token usage by 75%. This involves:
- Abbreviating field names to single characters
- Omitting null values
- Using arrays instead of objects where possible
- Custom parsing logic in `picklist_generator_service.py`

### Progress Tracking
Long-running operations (picklist generation, dataset building) use threading with real-time progress updates:
- Progress stored in global cache with percentage and time estimates
- Non-blocking API endpoints with separate status checking
- Automatic cleanup of completed operations

### Caching Layers
1. **In-Memory**: Active operations and progress tracking
2. **File Cache**: Unified datasets with timestamps (`backend/app/cache/`)
3. **Database**: Locked picklists and alliance selections
4. **LocalStorage**: Frontend UI state persistence

## Common Workflows

### Adding New Game Year Support
1. Create field mapping in `backend/app/config/statbotics_field_map_YEAR.json`
2. Add schema definition in `backend/app/data/schema_YEAR.json`
3. Update robot groups and critical mappings
4. Test field selection and dataset building

### Extending Validation Logic
1. Add detection methods to `data_validation_service.py`
2. Update correction logic in `validate.py` API endpoint
3. Ensure audit trail preservation
4. Test with various outlier scenarios

### Modifying Picklist Generation
1. Update compact JSON format in `picklist_generator_service.py`
2. Adjust GPT prompts for strategy parsing
3. Test token usage and response quality
4. Verify progress tracking accuracy

## Debugging and Monitoring

### Log Files
- `backend/logs/`: Timestamped service logs
- `backend/picklist_generator.log`: Picklist generation details
- Debug logs viewer at `/api/debug/logs/picklist`

### Progress Tracking
- Real-time status via `/api/progress/{operation_id}`
- Percentage completion and time estimates
- Error recovery and retry logic

### Database Inspection
SQLite database at `backend/data/scouting_app.db` can be inspected with any SQLite browser for debugging alliance selections and locked picklists.