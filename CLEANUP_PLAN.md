# Project Cleanup Plan

## Files/Folders to Move to Archive

### Root Level Sprint and Implementation Files
- AUTOMATIC_SETUP_COMPLETE_IMPLEMENTATION.md
- DUPLICATE_LABEL_PREVENTION_IMPLEMENTATION.md
- EXTRACTION_INTEGRATION_COMPLETE.md
- GAME_CONTEXT_OPTIMIZATION_PLAN.md
- GAME_LABEL_EXTRACTION_SPRINT_PLAN.md
- PICKLIST_ENHANCEMENT_SPRINT_PLAN.md
- TEXT_DATA_TYPE_IMPLEMENTATION.md
- UNIFIED_FIELD_SELECTIONS_IMPLEMENTATION.md

### Root Level Test Files
- test_comparative_reasoning.py
- test_dataset_enhancement.py
- test_data_volume_optimization.py
- test_end_to_end_workflow.py
- test_event_based_field_selections.py
- test_field_selection_preservation.py
- test_metric_filtering.py
- test_reconstruction_validation.py
- test_router_fix.py
- test_sprint4_integration.py

### Sprint Context Directories
- sprint-context/ (entire directory)
- sprint-reconstruction/ (entire directory)
- Refactor Documents/ (entire directory)

### Backend Test Files
- backend/test_*.py files (various test scripts)
- backend/debug_*.py files
- backend/demonstration_script.py
- backend/migrate_custom_events.py
- backend/rebuild_dataset_test.py
- backend/baseline_sheets_service.py
- backend/reconstruction_validation.log

### Temporary Files
- encode.txt, part1.txt, part2.txt
- picklist_generator.log
- server.log

### Cache and Backup Directories
- backend/cache/ (keep structure, archive old cache files)
- backend/backups/
- backend/checksums/
- backend/coverage-reports/
- backend/metrics/
- backend/rollbacks/

## Files to Keep (Essential Documentation)
- README.md
- CLAUDE.md
- docs/ (structured documentation)
- Dockerfile, docker-compose.yml
- requirements files
- Backend app/ structure (core application)
- Frontend src/ structure (core application)
- Essential data files in backend/app/data/