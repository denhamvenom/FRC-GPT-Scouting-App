# Sprint Execution Checklist V2 - Enhanced with Context Documentation

## Document Version
- **Version**: 2.0
- **Date**: 2025-06-24
- **Purpose**: Comprehensive checklist ensuring consistent sprint execution with full context preservation
- **Enhancement**: Added mandatory sprint-context documentation requirements

---

## CRITICAL: Sprint Context Documentation Requirements

### Mandatory Documents for EVERY Sprint
Each sprint MUST create these documents in the `sprint-context/` folder:

1. **Session Intent Document** (`sprint-[N]-session-intent.md`)
   - Use SESSION_INTENT_TEMPLATE.md
   - Fill out BEFORE starting any work
   - Update throughout the sprint
   - Complete handoff section at end

2. **Decomposition Strategy** (`[component]-decomposition-strategy.md`)
   - Required for any refactoring sprint
   - Document service/component boundaries
   - Map dependencies and relationships
   - Define migration approach

3. **API/Component Contracts** (`[component]-contracts.md`)
   - Document all public interfaces
   - Specify preservation requirements
   - Include behavior guarantees
   - Define testing contracts

4. **Handoff Checklist** (`sprint-[N]-handoff-checklist.md`)
   - Complete at sprint end
   - Verify baseline preservation
   - Document decisions and discoveries
   - Setup next sprint clearly

5. **Baseline Analysis** (`sprint[N]_baseline_analysis.md`)
   - Extract and analyze baseline version
   - Document characteristics to preserve
   - List all public interfaces
   - Capture performance metrics

---

## Pre-Sprint Checklist

### Environment Setup
- [ ] Development environment running
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`cd frontend && npm install`)
- [ ] API keys configured in `.env`
- [ ] Docker daemon running (if using Docker)
- [ ] Git configured with correct user
- [ ] **sprint-context folder exists**: `mkdir -p sprint-context`

### Baseline Verification and Context Setup
- [ ] On correct branch: `git branch --show-current`
- [ ] Baseline branch exists: `git branch -r | grep baseline`
- [ ] No uncommitted changes: `git status`
- [ ] Latest code pulled: `git pull origin baseline`
- [ ] **MANDATORY: Baseline reference established**: `git checkout baseline && git log -1 --oneline`
- [ ] **Session intent document created**: `cp "Refactor Documents/SESSION_INTENT_TEMPLATE.md" "sprint-context/sprint-[N]-session-intent.md"`
- [ ] **Context window protocol reviewed**: Read CONTEXT_WINDOW_PROTOCOL.md

### Testing Infrastructure
- [ ] Pytest installed: `pytest --version`
- [ ] Tests passing on baseline: `pytest`
- [ ] Coverage tool working: `pytest --cov=backend`
- [ ] Can generate reports: `pytest --html=report.html`

---

## Sprint Start Checklist

### 1. Establish Baseline Reference (MANDATORY)
```bash
# CRITICAL: Always start with baseline reference
git checkout baseline
git log -1 --oneline  # Note baseline commit
echo "BASELINE COMMIT: $(git rev-parse HEAD)" > sprint-context/baseline-ref.txt

# Extract baseline version of target files
git show baseline:path/to/target/file.py > baseline_target_file.py

# Create baseline analysis document
echo "# Sprint [N] Baseline Analysis" > sprint[N]_baseline_analysis.md
echo "## Target: path/to/target/file.py" >> sprint[N]_baseline_analysis.md
echo "## Baseline Characteristics:" >> sprint[N]_baseline_analysis.md
echo "- Lines: $(wc -l < baseline_target_file.py)" >> sprint[N]_baseline_analysis.md
echo "- Public Methods: $(grep -c "def [^_]" baseline_target_file.py)" >> sprint[N]_baseline_analysis.md

# Create new sprint branch
git checkout -b refactor/sprint-[N]
```

### 2. Create Session Intent Document (MANDATORY)
```bash
# Fill out the session intent BEFORE starting work
# This is CRITICAL for context preservation
vim sprint-context/sprint-[N]-session-intent.md

# Key sections to complete:
# - Session Overview (objectives, success metrics)
# - Baseline Reference Status (files, behaviors to preserve)
# - Intent and Context (WHY this work matters)
# - This Session's Specific Intent (approach, validation)
# - Critical Context for Next Session (what to transfer)
```

### 3. Create Decomposition Strategy (For Refactoring Sprints)
```bash
# Create strategy document for the component/service
echo "# [Component] Decomposition Strategy" > sprint-context/[component]-decomposition-strategy.md

# Document:
# - Baseline structure analysis
# - Service/component boundaries
# - Dependency mapping
# - Migration approach
# - Risk mitigation strategies
```

### 4. Document Starting State
```bash
# Run tests and save output
pytest -v --tb=short > test-results/sprint-[N]-start.txt 2>&1

# Check current coverage
pytest --cov=backend --cov-report=term-missing > coverage-reports/sprint-[N]-start.txt

# Save performance baseline
python -c "import time; start=time.time(); # YOUR TEST CODE HERE; print(f'Baseline: {time.time()-start:.3f}s')"
```

---

## During Sprint Checklist

### Every File Modification
- [ ] **Read baseline version first**: `git show baseline:path/to/file.py`
- [ ] Verify behavior preservation requirements
- [ ] Make changes incrementally
- [ ] Run relevant tests after each change
- [ ] Update intent document with discoveries
- [ ] Commit with descriptive message referencing baseline

### Continuous Baseline Validation
```bash
# Compare current implementation with baseline
git diff baseline path/to/modified/file.py

# Verify public interface preserved
diff <(git show baseline:file.py | grep "def [^_]") <(grep "def [^_]" file.py)

# Test API compatibility
curl baseline-endpoint > baseline-response.json
curl current-endpoint > current-response.json
diff baseline-response.json current-response.json
```

### Documentation Updates
- [ ] Update decomposition strategy with discoveries
- [ ] Document any constraints found
- [ ] Note decisions and rationale in intent document
- [ ] Capture alternative approaches considered

---

## Sprint Completion Checklist

### 1. Create API/Component Contracts Document
```bash
# Document all public interfaces
echo "# [Component] API Contracts" > sprint-context/[component]-contracts.md

# Include:
# - Public method signatures
# - Parameter types and constraints
# - Return value specifications
# - Error behavior
# - Performance characteristics
# - Baseline compatibility guarantees
```

### 2. Complete Validation Report
```bash
# Create comprehensive validation report
echo "# Sprint [N] Validation Report" > sprint[N]_validation_report.md

# Include:
# - Baseline comparison metrics
# - API compatibility verification
# - Performance benchmarks
# - Test results summary
# - Risk mitigation results
```

### 3. Final Testing Against Baseline
```bash
# Run all tests
pytest --cov=backend --cov-report=html --cov-report=term-missing

# Verify baseline behavior preserved
python test_baseline_compatibility.py

# Performance comparison
python benchmark_against_baseline.py
```

### 4. Complete Handoff Checklist (MANDATORY)
```bash
# Create handoff document
cp sprint-context/sprint-6-handoff-checklist.md sprint-context/sprint-[N]-handoff-checklist.md

# Complete all sections:
# - Baseline Preservation Status
# - Context Capture
# - Key Decisions and Discoveries
# - Next Session Setup
# - Handoff Validation
```

### 5. Update Session Intent Document
- [ ] Complete "Session Completion Status" section
- [ ] Fill in "Next Session Intent" thoroughly
- [ ] Document all discoveries and constraints
- [ ] Provide specific commands for next session

### 6. Verify Sprint Context Documentation
```bash
# Ensure all required documents exist
ls -la sprint-context/sprint-[N]-*.md
ls -la sprint-context/[component]-*.md

# Required files:
# - sprint-[N]-session-intent.md
# - [component]-decomposition-strategy.md
# - [component]-contracts.md
# - sprint-[N]-handoff-checklist.md
# - sprint[N]_baseline_analysis.md (in root or sprint-context)
# - sprint[N]_validation_report.md (in root or sprint-context)
```

---

## Post-Sprint Checklist

### Documentation Archive
- [ ] All sprint-context documents committed
- [ ] Validation reports included
- [ ] Decision rationale captured
- [ ] Next sprint setup documented

### Knowledge Transfer
- [ ] Handoff checklist reviewed
- [ ] Key insights highlighted
- [ ] Constraints clearly stated
- [ ] Success patterns documented

### Next Sprint Preparation
```bash
# Commands for next sprint to run
echo "Next Sprint Quick Start:" > sprint-context/next-sprint-setup.sh
echo "cd /path/to/repo" >> sprint-context/next-sprint-setup.sh
echo "git checkout baseline" >> sprint-context/next-sprint-setup.sh
echo "git show baseline:path/to/next/target.py > baseline_next_target.py" >> sprint-context/next-sprint-setup.sh
echo "cat sprint-context/sprint-[N]-handoff-checklist.md" >> sprint-context/next-sprint-setup.sh
```

---

## Sprint-Specific Documentation Examples

### Backend Service Refactoring (like Sprint 6)
Required documents:
1. `sheets-service-decomposition-strategy.md`
2. `sheets-service-contracts.md`
3. `sprint-6-session-intent.md`
4. `sprint-6-handoff-checklist.md`
5. `sprint6_baseline_analysis.md`
6. `sprint6_validation_report.md`

### Frontend Component Refactoring (like Sprint 7)
Required documents:
1. `picklist-generator-decomposition-strategy.md`
2. `picklist-generator-contracts.md`
3. `sprint-7-session-intent.md`
4. `sprint-7-handoff-checklist.md`
5. `sprint7_baseline_analysis.md`
6. `sprint7_validation_report.md`

---

## Emergency Procedures with Context Preservation

### If Context is Lost
```bash
# Recover from sprint-context documents
cat sprint-context/sprint-[N]-session-intent.md
cat sprint-context/sprint-[N]-handoff-checklist.md
cat sprint-context/[component]-decomposition-strategy.md

# Check baseline differences
git diff baseline --stat
git show baseline:path/to/file.py
```

### Documentation Recovery Checklist
1. Read previous sprint's handoff checklist
2. Review session intent for current sprint
3. Check decomposition strategy for approach
4. Verify contracts for preservation requirements
5. Consult baseline analysis for original behavior

---

## Quality Gates

### Before Proceeding to Next Sprint
- [ ] All 6 required documents created and complete
- [ ] Baseline preservation verified
- [ ] Performance within 5% of baseline
- [ ] Zero breaking changes confirmed
- [ ] Handoff checklist reviewed
- [ ] Next sprint clearly defined

### Documentation Completeness Check
```bash
#!/bin/bash
SPRINT_NUM=$1
COMPONENT=$2

# Check required files exist
REQUIRED_FILES=(
    "sprint-context/sprint-${SPRINT_NUM}-session-intent.md"
    "sprint-context/${COMPONENT}-decomposition-strategy.md"
    "sprint-context/${COMPONENT}-contracts.md"
    "sprint-context/sprint-${SPRINT_NUM}-handoff-checklist.md"
    "sprint${SPRINT_NUM}_baseline_analysis.md"
    "sprint${SPRINT_NUM}_validation_report.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
    else
        echo "✅ Found: $file"
    fi
done
```

---

**Remember**: Complete documentation is not optional - it's critical for maintaining context across Claude Code sessions and ensuring successful refactoring. The sprint-context folder is your knowledge base for seamless handoffs.