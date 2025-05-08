# FRC-GPT-Scouting-App Technical Overview

## Project Description

This application is a year-agnostic, team-agnostic, data-agnostic toolkit that automates FRC (FIRST Robotics Competition) event scouting, data validation, pick-list building, and live alliance selection using GPT-4. It's designed to help FRC teams streamline their scouting process, validate data quality, and make strategic decisions during competitions.

## Core Features

1. **Field Selection** – Select which fields from scouting spreadsheets to analyze; optionally use game manual for strategic insights
2. **Data Validation** – Flag missing or outlier match rows and let users rescout virtually, replace with averages, or ignore with reason
3. **Pick-List Builder** – Create ranked first/second/third-pick lists from validated data given user-ranked priorities
4. **Realistic Alliance Selection** – Automatically excludes alliance captains when generating second and third picks; live draft tracker

## Technical Architecture

### Technology Stack
- **Backend**: Python 3.12 + FastAPI (async, typed)
- **Frontend**: React/TypeScript with Vite and TailwindCSS
- **LLM Integration**: OpenAI GPT-4o via openai-python ≥1.0 (structured JSON output)
- **External APIs**:
  - Statbotics API (per-year EPA metrics)
  - The Blue Alliance API (teams/matches)
  - Google Sheets API (scouting data)

### Data Flow

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

### Key Components

#### 1. Unified Dataset Builder
- Located in `/backend/app/services/unified_event_data_service.py`
- Combines data from all sources (TBA, Statbotics, Google Sheets)
- Creates a single JSON file with complete dataset
- Includes expected matches, team info, match schedule, and scouting data

#### 2. Data Validation Service
- Located in `/backend/app/services/data_validation_service.py`
- Identifies missing match data and statistical outliers
- Uses Z-score and IQR methods for outlier detection
- Provides correction suggestions based on team averages

#### 3. Virtual Scout Generator
- Creates scouting records for missed matches
- Adjusts values based on match context and alliance performance
- Allows user to continue analysis with complete dataset

#### 4. GPT-Based Picklist Analysis
- Located in `/backend/app/services/picklist_analysis_service.py`
- Identifies important metrics based on statistical correlation with winning
- Creates suggested priority metrics based on game context
- Interprets natural language strategy descriptions into metrics

#### 5. Picklist Generator
- Located in `/backend/app/services/picklist_generator_service.py`
- Uses GPT to rank teams based on weighted priorities
- Drafts, evaluates, and refines rankings with explanations
- Handles different pick positions (first, second, third)
- Implements realistic alliance selection logic

## Database & Configuration

- No traditional database - data stored in JSON files
- Configuration files in `/backend/app/config/` for field mappings
- Cached JSON files in `/backend/app/data/` for datasets and analysis results
- Year-specific configurations allow adaptation to new FRC games

## API Endpoints

### Core Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/setup/start` | POST | Initialize for a specific FRC year, load game manual |
| `/api/schema/save-selections` | POST | Save field selections from scouting sheet |
| `/api/unified/build` | POST | Build unified dataset from all sources |
| `/api/validate/enhanced` | GET | Validate dataset for completeness and outliers |
| `/api/validate/create-virtual-scout` | POST | Create virtual scout for missing data |
| `/api/picklist/analyze` | POST | Analyze dataset to identify key metrics |
| `/api/picklist/generate` | POST | Generate ranked picklist with reasoning |

### Frontend Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/field-selection` | `FieldSelection.tsx` | Map spreadsheet fields to metrics |
| `/build-dataset` | `UnifiedDatasetBuilder.tsx` | Create unified dataset |
| `/validation` | `Validation.tsx` | Validate data and fix issues |
| `/picklist` | `PicklistNew.tsx` | Generate and manage picklists |

## Special Features

### 1. GPT Integration
- Custom system prompts in `picklist_analysis_service.py` and `picklist_generator_service.py`
- Structured JSON responses for deterministic output
- Context-aware analysis using game manual as reference

### 2. Statistical Analysis
- Team-specific and global outlier detection
- Metrics prioritized by correlation with winning
- Automated identification of key performance indicators

### 3. Alliance Selection Logic
- Recognizes FRC draft rules (alliance captains can't be second/third picks)
- Excludes top 8 ranked teams when generating second pick recommendations
- Adjusts recommendations based on current team and pick position

## Getting Started with Development

1. **Environment Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ../frontend
   npm install
   ```

2. **Required Environment Variables**:
   ```
   OPENAI_API_KEY=your_key_here
   TBA_API_KEY=your_key_here
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_SERVICE_ACCOUNT_FILE=path_to_service_account.json
   ```

3. **Running Development Servers**:
   ```bash
   # Backend
   cd backend
   uvicorn app.main:app --reload

   # Frontend
   cd frontend
   npm run dev
   ```

## Common Development Tasks

### Adding Support for a New Year
1. Create a new field map in `/backend/app/config/statbotics_field_map_YYYY.json`
2. Update UI to include the new year option in dropdowns

### Adding New Metrics
1. Extend the field selection schema in `field_selection.py`
2. Update metric categories in the frontend components

### Modifying GPT Prompts
1. Edit system prompts in `picklist_analysis_service.py` or `picklist_generator_service.py`
2. Ensure JSON structure remains consistent for frontend consumption

## Key Dependencies

- **openai**: For GPT-4o access (1.0.0+)
- **fastapi**: Backend API framework
- **httpx**: Async HTTP client for API calls
- **statbotics**: Python client for Statbotics API
- **numpy**: For statistical analysis
- **React**: Frontend UI library
- **TailwindCSS**: Utility-first CSS framework
- **Vite**: Frontend build tool

## Testing Approach

- Backend tests use pytest
- Manual testing for GPT integrations
- Focus on validating statistical analysis methods

## Current Limitations and Future Work

- Event key selector currently has limited flexibility
- Enhanced visualizations for team performance needed
- Mobile optimization could be improved
- OAuth / token management UI for third-party services