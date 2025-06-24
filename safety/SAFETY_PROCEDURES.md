# Safety Infrastructure Documentation

## Overview
This document describes the comprehensive safety infrastructure created for the FRC Scouting App refactoring project. All systems are designed to prevent the failures experienced in previous refactoring attempts.

## Safety Components

### 1. Baseline Metrics Capture (`baseline_metrics.py`)
Captures and validates system performance and behavior metrics.

**Usage:**
```bash
# Capture baseline metrics
python safety/baseline_metrics.py --capture

# Verify current state against baseline
python safety/baseline_metrics.py --verify
```

**What it captures:**
- API endpoint responses and timing
- Performance benchmarks
- Database state
- System configuration
- Frontend build information

**Success Criteria:**
- All API endpoints maintain status codes
- Performance within 5% of baseline
- No unexpected data changes

### 2. API Contract Tests (`api_contract_tests.py`)
Ensures API responses maintain exact structure and data types.

**Usage:**
```bash
# Run API contract validation
python safety/api_contract_tests.py
```

**What it validates:**
- Response structures match expected format
- Required fields are present
- Data types are correct
- Error responses follow consistent format

**Key Endpoints Tested:**
- `/api/health` - System health check
- `/api/schema` - Schema configuration
- `/api/team-comparison/*` - Team comparison functionality
- `/api/picklist/*` - Picklist generation

### 3. Visual Regression Testing (`visual_regression_setup.py`)
Detects any visual changes in the UI.

**Usage:**
```bash
# Capture baseline screenshots
python safety/visual_regression_setup.py --capture

# Compare current UI against baseline
python safety/visual_regression_setup.py --compare visual_current

# Generate comparison report
python safety/visual_regression_setup.py --compare visual_current --report
```

**Critical Pages Monitored:**
- Home page (/)
- Setup page (/setup)
- Event Manager (/event-manager)
- Schema Mapping (/schema-mapping)
- Validation (/validation)
- Picklist (/picklist)
- Alliance Selection (/alliance-selection)
- Workflow (/workflow)

**Zero Tolerance Policy:**
ANY visual change detected will fail validation and require rollback.

### 4. Emergency Rollback (`emergency_rollback.sh`)
WSL-compatible script for immediate system restoration.

**Usage:**
```bash
# Dry run (see what would happen)
./safety/emergency_rollback.sh --dry-run

# Full rollback
./safety/emergency_rollback.sh

# Force rollback without confirmation
./safety/emergency_rollback.sh --force

# Rollback without preserving logs
./safety/emergency_rollback.sh --no-preserve-logs
```

**What it does:**
1. Saves diagnostic information
2. Stops running services
3. Reverts git changes to baseline
4. Cleans build artifacts
5. Restores dependencies
6. Verifies system state

### 5. Data Integrity Validator (`data_integrity_validator.py`)
Ensures data consistency throughout refactoring.

**Usage:**
```bash
# Create data snapshot
python safety/data_integrity_validator.py --snapshot

# Run validation checks
python safety/data_integrity_validator.py --validate

# Compare snapshots
python safety/data_integrity_validator.py --compare baseline.json current.json
```

**What it validates:**
- Database schema integrity
- Data consistency across tables
- API data consistency
- Configuration file integrity

### 6. Integration Test Suite
Comprehensive end-to-end testing of all workflows.

**Test Files:**
- `tests/integration/end_to_end_workflows.py` - Complete user workflows
- `tests/integration/error_scenario_tests.py` - Error handling validation
- `tests/integration/cross_browser_validation.py` - Browser compatibility

**Usage:**
```bash
# Run end-to-end workflow tests
python tests/integration/end_to_end_workflows.py

# Run error scenario tests
python tests/integration/error_scenario_tests.py

# Setup cross-browser validation
python tests/integration/cross_browser_validation.py
```

### 7. Progress Tracking (`progress_tracker.py`)
Tracks refactoring progress and validates safety criteria.

**Usage:**
```bash
# Start a new sprint
python safety/progress_tracker.py --start-sprint 1 --sprint-name "Safety Infrastructure"

# Complete a task
python safety/progress_tracker.py --complete-task "Created baseline metrics system"

# Record an issue
python safety/progress_tracker.py --record-issue "API timeout on large datasets" --severity minor

# Generate progress report
python safety/progress_tracker.py --report

# Check go/no-go criteria
python safety/progress_tracker.py --check-criteria
```

## Safety Procedures

### Before Starting Any Sprint

1. **Verify Baseline State**
   ```bash
   git checkout baseline
   git status  # Should be clean
   git checkout refactor/sprint-N
   ```

2. **Run Safety Checks**
   ```bash
   python safety/baseline_metrics.py --verify
   python safety/api_contract_tests.py
   python safety/data_integrity_validator.py --validate
   ```

3. **Start Progress Tracking**
   ```bash
   python safety/progress_tracker.py --start-sprint N --sprint-name "Sprint Name"
   ```

### During Development

1. **Before Modifying Any File**
   - Read baseline version: `git show baseline:path/to/file.py`
   - Understand current implementation
   - Document intended changes

2. **After Each Change**
   - Run relevant tests
   - Check API contracts still valid
   - Verify no visual changes

3. **If Issues Arise**
   ```bash
   python safety/progress_tracker.py --record-issue "Description" --severity major
   ```

### After Completing Work

1. **Run Full Validation Suite**
   ```bash
   # API validation
   python safety/api_contract_tests.py
   
   # Performance check
   python safety/baseline_metrics.py --verify
   
   # Data integrity
   python safety/data_integrity_validator.py --validate
   
   # Visual regression
   python safety/visual_regression_setup.py --compare current
   ```

2. **Check Go/No-Go Criteria**
   ```bash
   python safety/progress_tracker.py --check-criteria
   ```

3. **Generate Progress Report**
   ```bash
   python safety/progress_tracker.py --report
   ```

### Emergency Procedures

#### If System Breaks
```bash
# Immediate rollback
./safety/emergency_rollback.sh --force
```

#### If Visual Changes Detected
1. Stop all work immediately
2. Investigate cause of visual change
3. Rollback if cannot be resolved
4. Document in progress tracker

#### If Performance Degrades
1. Run performance profiling
2. Compare with baseline metrics
3. Identify bottleneck
4. Either fix or rollback

## Go/No-Go Decision Criteria

### PROCEED to next phase only if ALL of the following are true:
- ✅ Zero visual changes detected
- ✅ All API contracts maintained
- ✅ Performance within 5% of baseline
- ✅ All integration tests passing
- ✅ No unresolved critical issues
- ✅ Data integrity validated
- ✅ Progress tracker shows green status

### STOP and rollback if ANY of the following occur:
- ❌ Any visual difference detected
- ❌ API contract violations
- ❌ Performance degradation >5%
- ❌ Integration test failures
- ❌ Data integrity issues
- ❌ Multiple major issues recorded

## Quick Reference Commands

### Daily Validation
```bash
# Morning check
python safety/baseline_metrics.py --verify
python safety/api_contract_tests.py

# Evening report
python safety/progress_tracker.py --report
```

### Before Commit
```bash
# Full safety check
python safety/baseline_metrics.py --verify
python safety/api_contract_tests.py
python tests/integration/end_to_end_workflows.py
```

### Emergency
```bash
# Quick rollback
./safety/emergency_rollback.sh --force

# Check what went wrong
cat safety/data_validation_report.json
cat safety/api_contracts.json
```

## Important Notes

1. **Zero Tolerance for Visual Changes**: The UI must remain pixel-perfect identical
2. **API Contracts are Sacred**: No breaking changes allowed
3. **Performance Matters**: Stay within 5% of baseline
4. **Document Everything**: Use progress tracker for all tasks/issues
5. **When in Doubt, Rollback**: Better safe than sorry

Remember: The goal is internal code improvement with ZERO user-visible changes.