# Changelog

## 2025-06-05

### Enhanced Team Comparison & Re-Ranking Feature

- **Complete redesign of TeamComparisonModal** with professional two-panel layout
  - Left panel: Selected teams, strategy selection, ranking results, and controls
  - Right panel: Chat-style GPT analysis interface with conversation history
- **Chat-style conversational interface** for team analysis
  - Initial analysis provides comprehensive narrative explaining team rankings
  - Follow-up questions maintain conversation context for deeper insights
  - Auto-scrolling chat with proper message formatting and timestamps
- **Enhanced backend analysis** with custom system prompts for detailed explanations
  - New `_create_comparison_system_prompt()` method for narrative analysis
  - Structured JSON response format with both ranking data and 200-400 word summaries
  - Improved response parsing to handle detailed analysis format
- **Visual improvements** including loading states, error handling, and professional styling
- **Keyboard shortcuts** (Enter to send, Shift+Enter for new lines)
- **Chat management** with options to clear conversation or reset analysis
- Updated API endpoint `/api/picklist/compare-teams` with chat history support

## 2025-05-20

- Documentation refreshed with database model overview
- Added Docker quickstart instructions to README
- Updated requirements to latest versions
- New Architecture section for database models

## 2025-05-19

- Implemented real-time progress tracking for picklist generation
- Added ProgressTracker component with percentage completion and time estimates
- Enhanced picklist generator service with threading for non-blocking API calls
- Updated frontend to show progress immediately when generation starts
- Fixed issue where progress bar wouldn't update during API calls
- Added progressive updates during long-running GPT operations

## 2025-05-16

- Enhanced database migration system for locked picklists
- Added excluded_teams and strategy_prompts columns to LockedPicklist table
- Created comprehensive migration script with logging and error handling
- Updated MIGRATION.md documentation with detailed instructions
- Improved event archival to include all picklist generation context

## 2025-05-12

- Implemented event archival system for preserving historical data
- Created archive service and API endpoints for event backup
- Added EventArchiveManager component for managing archived events
- Enhanced unified dataset with event metadata and team lists
- Integrated progress tracking for archive operations

## 2025-05-09

- Implemented Live Alliance Selection feature with database persistence
- Added Lock/Unlock functionality for picklists to prevent edits after finalization
- Created team grid display for Alliance Selection sorted by picklist ranking
- Added Alliance Board display showing current alliance selections
- Implemented proper handling of Round 3 backup picks for World Championship events
- Added team status tracking (captain, picked, declined) in alliance selection
- Ensured teams that declined can still be selected as captains (per FRC rules)
- Fixed navigation between Alliance Selection and Picklist to prevent auto-regeneration
- Added SQLAlchemy models and API endpoints for alliance selection tracking

## 2025-05-08

- Implemented ultra-compact JSON format for GPT responses (75% token reduction)
- Added comprehensive progress tracking during picklist generation
- Enhanced error recovery with robust JSON parsing and fallback mechanisms
- Added visual indicators for auto-added teams in picklists
- Implemented request deduplication to prevent redundant API calls
- Created debug logging system with dedicated UI viewer

## 2025-05-07

- Added superscouting metrics to picklist generation for more qualitative robot assessment
- Enhanced strategy parsing to better recognize robot capabilities in natural language descriptions
- Implemented realistic alliance selection logic (excludes alliance captains for 2nd/3rd picks)
- Added dataset retrieval endpoint with support for both path and event_key loading
- Improved error handling with fallback dataset mechanism for offline/error scenarios
- Added detailed UI information showing which teams are excluded during picklist generation
- Fixed issues with Windows path encoding in dataset loading

## 2025-05-06

- Switched from chunking to one-shot picklist generation to avoid duplication
- Implemented two-phase ranking with automatic fallback for missing teams
- Added LocalStorage persistence for picklist data across page navigation
- Created PicklistNew page with enhanced UI for picklist building
- Added pagination controls for picklist viewing with configurable page size
- Implemented confirmation dialogs for data clearing operations

## 2025‑05‑01

- Refactored field selection approach to use direct Google Sheets headers instead of GPT-derived fields
- Added unified dataset endpoint for building comprehensive event datasets
- Implemented enhanced validation with outlier detection using statistical methods
- Added Workflow component to guide users through application flow
- Built Validation page for identifying and fixing missing and outlier data
- Updated picklist generation to incorporate game strategy insights when available
- Added natural language parsing for strategy descriptions

## 2025‑04‑29

- Added learning setup endpoint and service
- Implemented year‑mapped `statbotics_client` with default fallback
- Fixed path resolution for config files (absolute from `__file__`)
- Added `python-multipart` dependency for form uploads
- Created sheet configuration management system

## 2025‑04‑28

- Superscouting validation bug fixed (integer team keys)
- Defined modular roadmap: Learning → Validation → Pick‑List → Alliance
- Patched Superscouting validator to use per-team check
- Added expected_matches into Unified Event Dataset during build
- Enhanced schema mapping with user correction wizard

## 2025‑04‑27

- FastAPI skeleton, CORS, health route
- Initial data validation service and unified dataset builder (legacy)
- Built unified_event_data_service to merge scouting, superscouting, TBA, and Statbotics
- Built data_validation_service to check completeness
- Added TypeScript to frontend for better type safety

## 2025‑04‑26

- Integrated Google Sheets service account read/write
- Created auto-schema mapping wizard (schema_2025.json, schema_superscout_2025.json)
- Integrated The Blue Alliance API v3 client
- Added field categorization system for metrics

## 2025‑04‑25

- Initial FastAPI and React project bootstrap
- Created basic project structure and documentation
- Set up development environment and dependencies
