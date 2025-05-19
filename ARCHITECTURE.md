# Architecture

## Component Overview
* **Frontend (React/Vite/TypeScript)** – user flows: Field Selection, Validation, Pick‑List, Alliance
* **FastAPI backend** – REST API, orchestration, GPT calls, config loading, progress tracking
* **SQLite Database** – Persistent storage for locked picklists and alliance selections
* **Statbotics client** – pulls team EPA metrics using field maps
* **TBA client** – async wrapper around Blue Alliance v3 endpoints
* **Google Sheets API** – fetches and parses scouting data rows
* **OpenAI GPT‑4.1** – variable selection assistance, outlier analysis, and pick‑list generation
* **Progress Tracking** – Real-time status updates for long-running operations

## Data Flow

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│  Google   │     │    The    │     │   Stat-   │
│  Sheets   │     │   Blue    │     │  botics   │
│   API     │     │ Alliance  │     │   API     │
└─────┬─────┘     └─────┬─────┘     └─────┬─────┘
      │                 │                 │
      ▼                 ▼                 ▼
┌─────────────────────────────────────────────┐
│            Unified Dataset Builder           │
│         (with caching & optimization)        │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│            Data Validation Service           │
│        (outlier detection & correction)      │
└─────────────────────────┬───────────────────┘
                          │
      ┌───────────────────┴───────────────────┐
      │                                       │
      ▼                                       ▼
┌─────────────┐                       ┌───────────────┐
│ Missing     │                       │  Statistical  │
│ Data        │                       │  Outliers     │
└──────┬──────┘                       └───────┬───────┘
       │                                      │
       ▼                                      ▼
┌─────────────────────────────────────────────────────┐
│            Manual Corrections & Virtual Scouts       │
│                  (with audit trail)                  │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│             Picklist Generation              │
│         (with progress tracking)             │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│               SQLite Database                │
│         (locked picklists & selections)      │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│            Alliance Selection UI             │
│         (real-time draft tracking)           │
└─────────────────────────────────────────────┘
```

## Key Workflows

### Field Selection Workflow
1. User selects which fields from Google Sheets to include in analysis
2. User categorizes each field (auto, teleop, endgame, etc.)
3. Optionally, user provides game manual URL for strategic insights
4. Field selections are saved as JSON config for the given year
5. Natural language parsing of strategy descriptions into weighted priorities

### Unified Dataset Building
1. Pull data from three sources:
   - Google Sheets (scouting & superscouting data)
   - The Blue Alliance (teams, matches, rankings)
   - Statbotics (EPA metrics with year-specific field mapping)
2. Filter and include only user-selected fields
3. Merge data with consistent team number keys
4. Add expected match records for validation
5. Save as JSON with timestamp and metadata
6. Cache results for performance optimization

### Validation Workflow
1. Check for missing data (matches without scouting records)
2. Detect statistical outliers using:
   - Z-score analysis (values far from global mean)
   - IQR method (values outside interquartile range)
   - Team-specific comparison (values unusual for a specific team)
3. Allow users to:
   - View and sort issues by type
   - Get suggested corrections for outliers
   - Apply corrections with audit trail
   - Refresh data while preserving corrections
   - Mark outliers as acceptable with reasons

### Picklist Generation
1. Summarize team performance metrics
2. Apply user-defined priority weights
3. Parse natural language strategy descriptions
4. Use GPT-4.1 with ultra-compact JSON format for efficiency
5. Generate rankings with progress tracking
6. Provide reasoning for each team's ranking
7. Handle missing teams with automatic fallback
8. Support batch processing for large events
9. Allow manual adjustments and re-ranking

### Alliance Selection
1. Load locked picklists from database
2. Display team grid sorted by picklist ranking
3. Track team status (captain, picked, declined)
4. Apply FRC rules (declined teams can be captains)
5. Automatically exclude appropriate teams by round
6. Update UI in real-time as selections are made
7. Support full 3-round selection with backup picks
8. Archive completed selections for later reference

## Security & Data Flow
* All auth tokens stored in .env, not committed to repo
* Data refreshable without losing manual corrections
* Validation corrections stored with audit trail (who, when, why)
* All datasets include metadata on creation time and source
* Database migrations handled safely with backward compatibility
* Comprehensive error logging with debug viewer

## Technology Choices
* **FastAPI** – async Python for efficient API calls to TBA & OpenAI
* **React with TypeScript** – type-safe component-based UI
* **SQLite/SQLAlchemy** – lightweight database with ORM for data persistence
* **GPT-4.1** – High-quality text generation with deterministic JSON output
* **Threading** – Non-blocking API calls with progress updates
* **LocalStorage** – Frontend state persistence across page navigation
* **Ultra-Compact JSON** – 75% token reduction for GPT responses

## Caching Strategy
* **In-Memory Cache** – Active operations and progress tracking
* **LocalStorage** – UI state including picklists and selections
* **Database** – Persistent storage for locked picklists and alliance selections
* **File Cache** – Unified datasets with timestamps
* **Request Deduplication** – Prevents duplicate API calls

## Error Handling
* **Robust JSON Parsing** – Fallback mechanisms for truncated responses
* **Rate Limit Management** – Exponential backoff with retries
* **Progress Recovery** – Resume operations after failures
* **Validation Errors** – Clear user feedback with suggested fixes
* **API Failures** – Graceful degradation with cached data

## Performance Optimizations
* **Ultra-Compact JSON Format** – Reduces GPT token usage by 75%
* **Threading for API Calls** – Non-blocking operations with progress updates
* **Smart Data Condensing** – Only essential fields sent to GPT
* **Batch Processing** – Efficient handling of large team counts
* **Progress Tracking** – Real-time feedback for long operations
* **Request Deduplication** – Cache keys prevent redundant work