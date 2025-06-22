# Sprint Execution Checklist

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Step-by-step checklist for executing each sprint

## Pre-Sprint Checklist

### Environment Setup
- [ ] Development environment running
- [ ] All dependencies installed (`pip install -r requirements-dev.txt`)
- [ ] Frontend dependencies installed (`cd frontend && npm install`)
- [ ] API keys configured in `.env`
- [ ] Docker daemon running (if using Docker)
- [ ] Git configured with correct user

### Baseline Verification
- [ ] On correct branch: `git branch --show-current`
- [ ] Baseline branch exists: `git branch -r | grep baseline`
- [ ] No uncommitted changes: `git status`
- [ ] Latest code pulled: `git pull origin baseline`

### Testing Infrastructure
- [ ] Pytest installed: `pytest --version`
- [ ] Tests passing on baseline: `pytest`
- [ ] Coverage tool working: `pytest --cov=backend`
- [ ] Can generate reports: `pytest --html=report.html`

## Sprint Start Checklist

### 1. Create Sprint Branch
```bash
# Create new sprint branch from baseline
git checkout baseline
git pull origin baseline
git checkout -b refactor/sprint-<<NUMBER>>

# Verify branch
git branch --show-current
```

### 2. Generate Initial Checksums
```bash
# Create checksums directory if not exists
mkdir -p checksums

# Generate checksums for Python files
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/sprint-<<NUMBER>>-start.txt

# Generate checksums for TypeScript files (if needed)
find frontend/src -name "*.ts" -o -name "*.tsx" -type f -exec sha1sum {} \; | sort >> checksums/sprint-<<NUMBER>>-start.txt

# Verify checksum file created
wc -l checksums/sprint-<<NUMBER>>-start.txt
```

### 3. Document Starting State
```bash
# Run tests and save output
pytest -v --tb=short > test-results/sprint-<<NUMBER>>-start.txt 2>&1

# Check current coverage
pytest --cov=backend --cov-report=term-missing > coverage-reports/sprint-<<NUMBER>>-start.txt

# Save performance baseline (if API is running)
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### 4. Create Sprint Log
Create file: `sprint-logs/sprint-<<NUMBER>>.md`
```markdown
# Sprint <<NUMBER>> Log

## Start Time: <<TIMESTAMP>>
## Branch: refactor/sprint-<<NUMBER>>
## Developer: <<NAME>>

### Starting Metrics
- Test Count: <<COUNT>>
- Coverage: <<PERCENTAGE>>%
- Failing Tests: <<COUNT>>

### Objectives
1. <<OBJECTIVE-1>>
2. <<OBJECTIVE-2>>
3. <<OBJECTIVE-3>>

### Files to Modify
- [ ] <<FILE-1>>
- [ ] <<FILE-2>>
- [ ] <<FILE-3>>
```

## During Sprint Checklist

### Every File Modification
- [ ] Verify checksum before edit
- [ ] Make changes incrementally
- [ ] Run relevant tests after each change
- [ ] Update docstrings with context
- [ ] Commit with descriptive message

### Every Hour
- [ ] Run full test suite
- [ ] Check for performance regression
- [ ] Update sprint log with progress
- [ ] Verify no functionality lost
- [ ] Push changes to remote

### Code Quality Checks
- [ ] Run linter: `ruff check backend/`
- [ ] Run formatter: `black backend/`
- [ ] Type check: `mypy backend/` (if configured)
- [ ] Check imports: `isort backend/`

## Sprint Completion Checklist

### 1. Final Testing
```bash
# Run all tests with coverage
pytest --cov=backend --cov-report=html --cov-report=term-missing

# Run specific integration tests
pytest tests/integration/ -v

# Performance test (if applicable)
python scripts/performance_test.py
```

### 2. Generate Final Checksums
```bash
# Generate ending checksums
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/sprint-<<NUMBER>>-end.txt

# Compare with starting checksums
diff checksums/sprint-<<NUMBER>>-start.txt checksums/sprint-<<NUMBER>>-end.txt > checksums/sprint-<<NUMBER>>-diff.txt

# List modified files
grep "^[<>]" checksums/sprint-<<NUMBER>>-diff.txt | cut -d' ' -f3 | sort | uniq
```

### 3. Documentation Updates
- [ ] Update all modified file docstrings
- [ ] Add AI-Context to complex functions
- [ ] Update API documentation if changed
- [ ] Document any new dependencies
- [ ] Update architecture diagrams if needed

### 4. Create Sprint Summary
Create file: `sprint-summaries/sprint-<<NUMBER>>-summary.md`
```markdown
# Sprint <<NUMBER>> Summary

## Completion Time: <<TIMESTAMP>>
## Duration: <<HOURS>> hours

### Objectives Completed
- [x] <<OBJECTIVE-1>>
- [x] <<OBJECTIVE-2>>
- [ ] <<OBJECTIVE-3>> (if not completed, explain)

### Files Modified
1. `<<FILE>>` - <<CHANGE-DESCRIPTION>>
2. `<<FILE>>` - <<CHANGE-DESCRIPTION>>

### Metrics
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Test Count | <<N>> | <<N>> | <<+N>> |
| Coverage | <<N>>% | <<N>>% | <<+N>>% |
| Avg Response Time | <<N>>ms | <<N>>ms | <<-N>>ms |
| Max Line Length | <<N>> | <<N>> | <<-N>> |

### Key Decisions
1. <<DECISION-1>>
2. <<DECISION-2>>

### Known Issues
1. <<ISSUE-1>>
2. <<ISSUE-2>>

### Next Sprint Prerequisites
1. <<PREREQUISITE-1>>
2. <<PREREQUISITE-2>>
```

### 5. Create Pull Request
```bash
# Push sprint branch
git push -u origin refactor/sprint-<<NUMBER>>

# Create PR via GitHub CLI (if installed)
gh pr create --title "Sprint <<NUMBER>>: <<DESCRIPTION>>" \
  --body-file sprint-summaries/sprint-<<NUMBER>>-summary.md \
  --base baseline

# Or create manually on GitHub with summary content
```

### 6. Backup Critical Files
```bash
# Create sprint backup
mkdir -p backups/sprint-<<NUMBER>>
cp -r backend/src backups/sprint-<<NUMBER>>/
cp checksums/sprint-<<NUMBER>>-*.txt backups/sprint-<<NUMBER>>/
cp sprint-summaries/sprint-<<NUMBER>>-summary.md backups/sprint-<<NUMBER>>/

# Create compressed archive
tar -czf backups/sprint-<<NUMBER>>.tar.gz backups/sprint-<<NUMBER>>/
```

## Post-Sprint Checklist

### Merge Preparation
- [ ] All tests passing
- [ ] Coverage increased or maintained
- [ ] No performance regression
- [ ] Code review completed
- [ ] Documentation updated

### Knowledge Transfer
- [ ] Sprint summary shared with team
- [ ] Key decisions documented
- [ ] Blockers communicated
- [ ] Next sprint planned
- [ ] Lessons learned captured

### Cleanup
- [ ] Old branches deleted (after merge)
- [ ] Temporary files removed
- [ ] Logs archived
- [ ] Metrics recorded
- [ ] Success criteria verified

## Emergency Procedures

### If Tests Fail
1. Check test output for specific failures
2. Run failed tests in isolation
3. Compare with baseline behavior
4. Use git bisect if needed
5. Document failure pattern

### If Checksum Mismatch
1. **STOP** immediately
2. Run `git status` to check for changes
3. Compare with expected modifications
4. Investigate unauthorized changes
5. Restore from baseline if needed

### If Performance Degrades
1. Run profiler on affected code
2. Compare with baseline metrics
3. Check for N+1 queries
4. Review algorithm changes
5. Consider caching strategies

### Rollback Procedure
```bash
# Immediate rollback to baseline
git checkout baseline
git branch -D refactor/sprint-<<NUMBER>>

# Partial rollback (specific files)
git checkout baseline -- path/to/file.py

# Restore from backup
tar -xzf backups/sprint-<<NUMBER>>.tar.gz
cp -r backups/sprint-<<NUMBER>>/src/* backend/src/
```

## Sprint-Specific Additions

### Sprint 1 (Test Framework)
- [ ] Create `pytest.ini` with settings
- [ ] Set up `conftest.py` with fixtures
- [ ] Configure coverage exclusions
- [ ] Create test data factories
- [ ] Document test patterns

### Sprint 3 (Domain Models)
- [ ] Install Pydantic
- [ ] Create model validation tests
- [ ] Document business rules
- [ ] Set up model factories
- [ ] Verify serialization

### Sprint 5 (Service Decomposition)
- [ ] Benchmark current performance
- [ ] Map method dependencies
- [ ] Create service interfaces
- [ ] Test each extraction
- [ ] Verify API compatibility

### Sprint 8 (Monitoring)
- [ ] Install OpenTelemetry
- [ ] Configure exporters
- [ ] Add trace decorators
- [ ] Create dashboards
- [ ] Test metric collection

---

**Remember**: This checklist ensures consistent, safe execution of each sprint. Never skip steps, especially checksum verification and testing.