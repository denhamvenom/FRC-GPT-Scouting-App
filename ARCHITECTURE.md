# Architecture

## Component Overview
* **Frontend (React/Vite)** – user flows: Field Selection, Validation, Pick‑List, Alliance
* **FastAPI backend** – REST API, orchestration, GPT calls, config loading
* **Statbotics client** – pulls per‑team, per‑year EPA using field maps
* **TBA client** – async wrapper around Blue Alliance v3 endpoints
* **Google Sheets API** – fetches and parses scouting data rows
* **OpenAI GPT‑4o** – variable selection assistance, outlier analysis, and pick‑list generation

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
│                                             │
│            Unified Dataset Builder           │
│                                             │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│                                             │
│            Data Validation Service           │
│                                             │
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
│                                                     │
│            Manual Corrections & Virtual Scouts       │
│                                                     │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│                                             │
│             Picklist Generation              │
│                                             │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│                                             │
│            Alliance Selection UI             │
│                                             │
└─────────────────────────────────────────────┘
```

## Key Workflows

### Field Selection Workflow
1. User selects which fields from Google Sheets to include in analysis
2. User categorizes each field (auto, teleop, endgame, etc.)
3. Optionally, user provides game manual URL for strategic insights
4. Field selections are saved as JSON config for the given year

### Unified Dataset Building
1. Pull data from three sources:
   - Google Sheets (scouting & superscouting data)
   - The Blue Alliance (teams, matches, rankings)
   - Statbotics (EPA metrics)
2. Filter and include only user-selected fields
3. Merge data with consistent team number keys
4. Add expected match records for validation
5. Save as JSON with timestamp and metadata

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

### Picklist Generation
1. Summarize team performance metrics
2. Apply user-defined priority weights
3. If game manual provided, extract strategic insights
4. Use GPT-4o to rank teams based on priorities and data
5. Provide reasoning for each team's ranking

## Security & Data Flow
* All auth tokens stored in .env, not committed to repo
* Data refreshable without losing manual corrections
* Validation corrections stored with audit trail (who, when, why)
* All datasets include metadata on creation time and source

## Technology Choices
* **FastAPI** – async Python for efficient API calls to TBA & OpenAI
* **React** – component-based UI with TypeScript safety
* **GPT-4o** – High-quality text generation with deterministic JSON output
* **Statbotics & TBA** – Community-maintained data sources with established APIs