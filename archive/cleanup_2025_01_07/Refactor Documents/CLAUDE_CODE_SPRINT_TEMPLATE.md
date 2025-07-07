# Claude Code Sprint Execution Template

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Standardized template for Claude Code sprint execution

## Overview

This template is specifically designed for use with Claude Code's CLI interface. It provides a structured approach for executing refactoring sprints with built-in safety checks, context preservation, and automated verification.

## Claude Code Sprint Template

### Pre-Sprint Setup Message

```markdown
You are Claude Code, executing Sprint [NUMBER] of the FRC GPT Scouting App refactoring.

## Sprint Context
- **Repository**: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App
- **Current Branch**: baseline
- **Target Branch**: refactor/sprint-[NUMBER]
- **Sprint Goal**: [SPECIFIC_OBJECTIVE]
- **Time Limit**: [X] hours
- **Success Criteria**: [SPECIFIC_METRICS]

## Pre-Flight Checklist
Before making ANY changes, complete this checklist:

1. **Verify Repository Location**
   ```bash
   pwd  # Should show correct repository path
   ls -la  # Verify ARCHITECTURE.md, backend/, frontend/ exist
   ```

2. **Check Git Status**
   ```bash
   git status  # Should show clean working directory
   git branch --show-current  # Should show 'baseline'
   git log -1 --oneline  # Note current commit
   ```

3. **MANDATORY: Establish Baseline Reference**
   ```bash
   # Verify baseline branch exists and is accessible
   git checkout baseline
   git log -1 --oneline  # Note baseline commit for reference
   echo "BASELINE COMMIT: $(git rev-parse HEAD)" > sprint-context/baseline-ref.txt
   
   # Return to work branch and compare
   git checkout refactor/sprint-[NUMBER] 2>/dev/null || git checkout -b refactor/sprint-[NUMBER]
   git diff baseline --stat > sprint-context/changes-from-baseline.txt
   echo "Current changes from baseline: $(wc -l < sprint-context/changes-from-baseline.txt) files modified"
   ```

4. **Create Session Intent Document**
   ```bash
   # Copy template and fill in session-specific intent
   cp "Refactor Documents/SESSION_INTENT_TEMPLATE.md" "sprint-context/sprint-[NUMBER]-session-[X]-intent.md"
   echo "CRITICAL: Fill out intent document before proceeding"
   echo "Location: sprint-context/sprint-[NUMBER]-session-[X]-intent.md"
   ```

5. **Verify Baseline Integrity**
   ```bash
   # Run existing tests (if any)
   cd backend && python -m pytest --tb=short -q || echo "No tests found (expected)"
   
   # Test basic functionality
   python -c "from app.main import app; print('✅ Backend imports successfully')"
   ```

6. **Generate Starting Checksums**
   ```bash
   find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/sprint-[NUMBER]-start.txt
   find frontend/src -name "*.ts" -o -name "*.tsx" -type f -exec sha1sum {} \; 2>/dev/null | sort >> checksums/sprint-[NUMBER]-start.txt
   echo "Starting checksums generated: $(wc -l < checksums/sprint-[NUMBER]-start.txt) files"
   ```

## Sprint Execution Protocol

### Step 1: Baseline Analysis (MANDATORY)
```bash
# REQUIRED: Read baseline version of target files FIRST
git show baseline:backend/app/services/target_service.py > /tmp/baseline_version.py
```

- **Read baseline version** of target files to understand original logic
- **Document baseline behavior** that must be preserved
- **Identify API contracts** that cannot change
- **Note dependencies** and integration points
- **Use Read tool** to examine current state and compare with baseline

### Step 2: Plan Changes with Baseline Preservation
- **Identify specific files** to modify and their baseline versions
- **Plan modification sequence** that preserves all baseline behavior
- **Estimate scope and impact** on baseline compatibility
- **Update sprint log** with plan and baseline preservation strategy
- **Document intent** in session intent document

### Step 3: Implement Changes with Baseline Validation
For each file modification:

1. **Pre-Modification Baseline Check**
   ```bash
   # REQUIRED: Compare with baseline version before editing
   git show baseline:[FILE_PATH] | head -20  # See original logic
   git diff baseline [FILE_PATH]  # See current changes
   sha1sum [FILE_PATH]  # Record current checksum
   ```

2. **Make Changes with Baseline Preservation**
   - **Read baseline version** using Read tool first
   - **Understand original logic** completely before modifying
   - **Use Edit or MultiEdit tool** while preserving exact API interfaces
   - **Add comprehensive docstrings** including baseline reference
   - **Follow coding standards** from baseline

3. **Post-Modification Baseline Validation**
   ```bash
   # Verify syntax
   python -m py_compile [FILE_PATH]  # For Python files
   
   # CRITICAL: Test behavior matches baseline
   python -c "
   # Test that refactored code produces identical results to baseline
   # Add specific validation for the modified functionality
   print('✅ Behavior matches baseline')
   "
   
   # Update checksum
   sha1sum [FILE_PATH] >> checksums/sprint-[NUMBER]-changes.txt
   
   # Run related tests
   cd backend && python -m pytest tests/[RELATED_TEST] -v
   
   # Compare with baseline behavior
   echo 'Validating against baseline...'
   git diff baseline [FILE_PATH] --stat
   ```

### Step 4: Continuous Validation
After every significant change:

```bash
# Run full test suite
cd backend && python -m pytest --tb=short

# Check imports
python -c "from app.main import app; print('✅ App still imports')"

# Verify no circular imports
python -c "
import sys
sys.path.insert(0, 'backend')
try:
    from app.main import app
    print('✅ No circular imports')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"
```

## Required Docstring Template for All Modified Functions

```python
"""
Purpose: [Clear description of what this function/class does]
Inputs: [Parameter types and constraints]
Outputs: [Return type and meaning]
Side-Effects: [Database writes, API calls, global state changes]
Dependencies: [Required modules, services, or external resources]

Claude-Context:
- Sprint: [NUMBER]
- Refactor-Reason: [Why this change was made]
- Original-Location: [If moved from somewhere else]
- Complexity: [Simple|Medium|Complex]
- Test-Coverage: [Coverage level achieved]

Example:
    >>> # Include usage example if function is non-trivial
    >>> result = function_name(param1, param2)
    >>> assert isinstance(result, expected_type)

Modified: Sprint-[NUMBER] | SHA-1: [POST-EDIT-CHECKSUM]
"""
```

## Sprint Completion Protocol

### Final Validation
```bash
# 1. Run complete test suite
cd backend && python -m pytest --cov=app --cov-report=term-missing

# 2. Generate final checksums
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/sprint-[NUMBER]-end.txt

# 3. Calculate changes
diff checksums/sprint-[NUMBER]-start.txt checksums/sprint-[NUMBER]-end.txt > checksums/sprint-[NUMBER]-diff.txt

# 4. Performance check (if applicable)
cd backend && python -c "
import time
start = time.time()
from app.main import app
print(f'Import time: {(time.time() - start)*1000:.2f}ms')
"

# 5. Commit changes
git add .
git commit -m "feat(sprint-[NUMBER]): [DESCRIPTION]

- [CHANGE_1]
- [CHANGE_2]
- [CHANGE_3]

Tests: [PASS_COUNT] passing
Coverage: [PERCENTAGE]%
Sprint: [NUMBER] complete"
```

### Sprint Summary Creation
Create `sprint-summaries/sprint-[NUMBER]-summary.md`:

```markdown
# Sprint [NUMBER] Summary

## Completion Info
- **End Time**: $(date)
- **Duration**: [X] hours
- **Branch**: refactor/sprint-[NUMBER]
- **Commit**: $(git rev-parse HEAD | cut -c1-8)

## Objectives Status
- [x] Primary: [OBJECTIVE] ✅
- [x] Secondary: [OBJECTIVE] ✅  
- [ ] Stretch: [OBJECTIVE] ⏳ (if not completed)

## Files Modified
[LIST OF FILES WITH BRIEF DESCRIPTION OF CHANGES]

## Metrics Achieved
| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| Test Coverage | [X]% | [Y]% | [Z]% | ✅/❌ |
| Max Lines/Service | [X] | [Y] | [Z] | ✅/❌ |

## Key Decisions
1. [DECISION_1]: [RATIONALE]
2. [DECISION_2]: [RATIONALE]

## Issues Encountered
1. [ISSUE]: [RESOLUTION]

## Next Sprint Prerequisites
- [PREREQUISITE_1]
- [PREREQUISITE_2]

## Context for Next Session
[CRITICAL_INFORMATION_FOR_CONTINUATION]
```

## Error Recovery Protocol

If anything goes wrong during the sprint:

### Minor Issues (Test failures, import errors)
1. **Stop immediately** - don't make more changes
2. **Identify the specific failure**:
   ```bash
   cd backend && python -m pytest --tb=long -v
   python -c "from app.main import app"  # Test imports
   ```
3. **Revert the problematic change**:
   ```bash
   git checkout HEAD~1 -- [PROBLEMATIC_FILE]
   ```
4. **Verify system works again**
5. **Re-attempt with smaller change**

### Major Issues (System broken, can't import)
1. **Immediate rollback to sprint start**:
   ```bash
   git reset --hard HEAD~[NUMBER_OF_COMMITS]
   # Or if needed:
   git checkout baseline
   git branch -D refactor/sprint-[NUMBER]
   ```

2. **Verify baseline works**:
   ```bash
   cd backend && python -c "from app.main import app; print('✅ Baseline restored')"
   ```

3. **Document the failure**:
   Create `rollbacks/sprint-[NUMBER]-failure.md` with full details

## Context Handoff Template

When ending a Claude Code session mid-sprint:

### CRITICAL: Update Session Intent Document
```bash
# REQUIRED: Update the session intent document with results
vi sprint-context/sprint-[NUMBER]-session-[X]-intent.md
# Complete the "Session Execution Log" and "Next Session Requirements" sections
```

### Session Handoff Checklist
```markdown
## Sprint [NUMBER] Session [X] Handoff

### Baseline Preservation Status
- [ ] All changes compared against baseline behavior
- [ ] API contracts verified identical to baseline: `git diff baseline backend/app/api/`
- [ ] Performance within 5% of baseline: [MEASUREMENT]
- [ ] Visual interface unchanged: [VERIFICATION_METHOD]

### Session Completion Status
- **Time**: [TIMESTAMP]  
- **Progress**: [X]% complete
- **Current Task**: [SPECIFIC_TASK]
- **Files Modified**: [LIST_WITH_BASELINE_DIFFS]

### What Was Accomplished
[DESCRIPTION_OF_COMPLETED_WORK]

### Baseline Comparisons Made
```bash
# Document what baseline analysis was done
git diff baseline --stat > handoff-baseline-comparison.txt
git show baseline:[KEY_FILE] | head -10  # Original logic preserved
```

### Critical Discoveries
- **About Baseline**: [WHAT_WAS_LEARNED_ABOUT_ORIGINAL_CODE]
- **Constraints Found**: [LIMITATIONS_DISCOVERED]
- **Decisions Made**: [CHOICES_AND_RATIONALE]

### Next Session Intent
**Immediate Goal**: [SPECIFIC_NEXT_OBJECTIVE]
**Baseline Reference**: [FILES_TO_COMPARE_WITH_BASELINE]
**Preservation Requirements**: [BEHAVIORS_THAT_MUST_REMAIN_IDENTICAL]

### Handoff Validation Commands
```bash
# Commands next session should run to verify state
cd [REPO_PATH]
git checkout refactor/sprint-[NUMBER]
git diff baseline --stat  # See all changes from original
git show baseline:[CRITICAL_FILE] | head -20  # Review original logic

# Verify system still works
cd backend && python -c "from app.main import app; print('✅ System functional')"
```

### Emergency Recovery
**If next session encounters issues**:
- Baseline reference: `git show baseline:[FILE]`
- Last known good state: `git log --oneline -5`
- Rollback command: `git reset --hard [SAFE_COMMIT]`
```

## Success Validation

Sprint is considered successful when:

1. **All objectives met** ✅
2. **All tests passing** ✅  
3. **No performance degradation** ✅
4. **Code quality improved** ✅
5. **Documentation complete** ✅
6. **Context preserved** ✅

## Ready for Next Sprint

Hand off to human or next Claude Code session with:
- Sprint summary complete
- All files committed
- Context documented
- Next sprint planned
- System verified working

---

**Remember**: Claude Code's strength is in systematic, careful execution. Use the tools methodically, verify at each step, and preserve context for seamless handoffs.
```