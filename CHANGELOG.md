## 2025-05-09
* Implemented Live Alliance Selection feature with database persistence
* Added Lock/Unlock functionality for picklists to prevent edits after finalization
* Created team grid display for Alliance Selection sorted by picklist ranking
* Added Alliance Board display showing current alliance selections
* Implemented proper handling of Round 3 backup picks for World Championship events
* Added team status tracking (captain, picked, declined) in alliance selection
* Ensured teams that declined can still be selected as captains (per FRC rules)
* Fixed navigation between Alliance Selection and Picklist to prevent auto-regeneration
* Added SQLAlchemy models and API endpoints for alliance selection tracking

## 2025-05-07
* Added superscouting metrics to picklist generation for more qualitative robot assessment
* Enhanced strategy parsing to better recognize robot capabilities in natural language descriptions
* Implemented realistic alliance selection logic (excludes alliance captains for 2nd/3rd picks)
* Added dataset retrieval endpoint with support for both path and event_key loading
* Improved error handling with fallback dataset mechanism for offline/error scenarios
* Added detailed UI information showing which teams are excluded during picklist generation
* Fixed issues with Windows path encoding in dataset loading

## 2025‑05‑01
* Refactored field selection approach to use direct Google Sheets headers instead of GPT-derived fields
* Added unified dataset endpoint for building comprehensive event datasets
* Implemented enhanced validation with outlier detection using statistical methods
* Added Workflow component to guide users through application flow
* Built Validation page for identifying and fixing missing and outlier data
* Updated picklist generation to incorporate game strategy insights when available

## 2025‑04‑29
* Added learning setup endpoint and service
* Implemented year‑mapped `statbotics_client` with default fallback
* Fixed path resolution for config files (absolute from `__file__`)
* Added `python-multipart` dependency for form uploads

## 2025‑04‑28
* Superscouting validation bug fixed (integer team keys)
* Defined modular roadmap: Learning → Validation → Pick‑List → Alliance
* Patched Superscouting validator to use per-team check
* Added expected_matches into Unified Event Dataset during build

## 2025‑04‑27
* FastAPI skeleton, CORS, health route
* Initial data validation service and unified dataset builder (legacy)
* Built unified_event_data_service to merge scouting, superscouting, TBA, and Statbotics
* Built data_validation_service to check completeness

## 2025‑04‑26
* Integrated Google Sheets service account read/write
* Created auto-schema mapping wizard (schema_2025.json, schema_superscout_2025.json)
* Integrated The Blue Alliance API v3 client

## 2025‑04‑25
* Initial FastAPI and React project bootstrap