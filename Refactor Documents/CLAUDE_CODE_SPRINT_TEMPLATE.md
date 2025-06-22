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

3. **Verify Baseline Integrity**
   ```bash
   # Run existing tests (if any)
   cd backend && python -m pytest --tb=short -q || echo "No tests found (expected)"
   
   # Test basic functionality
   python -c "from app.main import app; print('✅ Backend imports successfully')"
   ```

4. **Create Sprint Branch**
   ```bash
   git checkout -b refactor/sprint-[NUMBER]
   echo "Sprint [NUMBER] started on $(date)" > sprint-logs/sprint-[NUMBER].md
   ```

5. **Generate Starting Checksums**
   ```bash
   find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/sprint-[NUMBER]-start.txt
   find frontend/src -name "*.ts" -o -name "*.tsx" -type f -exec sha1sum {} \; 2>/dev/null | sort >> checksums/sprint-[NUMBER]-start.txt
   echo "Starting checksums generated: $(wc -l < checksums/sprint-[NUMBER]-start.txt) files"
   ```

## Sprint Execution Protocol

### Step 1: Understand Current State
- Use Read tool to examine target files
- Use Glob tool to find related files
- Use Grep tool to understand patterns
- Document findings in sprint log

### Step 2: Plan Changes
- Identify specific files to modify
- Plan modification sequence
- Estimate scope and impact
- Update sprint log with plan

### Step 3: Implement Changes Incrementally
For each file modification:

1. **Pre-Modification Check**
   ```bash
   sha1sum [FILE_PATH]  # Record current checksum
   ```

2. **Make Changes**
   - Use Edit or MultiEdit tool
   - Add comprehensive docstrings per template
   - Follow coding standards

3. **Post-Modification Verification**
   ```bash
   # Verify syntax
   python -m py_compile [FILE_PATH]  # For Python files
   
   # Update checksum
   sha1sum [FILE_PATH] >> checksums/sprint-[NUMBER]-changes.txt
   
   # Run related tests
   cd backend && python -m pytest tests/[RELATED_TEST] -v
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

```markdown
## Sprint [NUMBER] Session Handoff

### Session Status
- **Time**: [TIMESTAMP]
- **Progress**: [X]% complete
- **Current Task**: [SPECIFIC_TASK]
- **Files Open**: [LIST]

### What Just Happened
[DESCRIPTION_OF_LAST_ACTIONS]

### Current File States
```bash
# Run this to get current checksums
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/handoff-$(date +%H%M%S).txt
```

### Exact Next Steps
1. [SPECIFIC_COMMAND_TO_RUN]
2. [SPECIFIC_FILE_TO_EDIT]
3. [SPECIFIC_TEST_TO_RUN]

### Critical Context
- **Important**: [KEY_DECISION_OR_CONSTRAINT]
- **Warning**: [POTENTIAL_ISSUE_TO_WATCH]
- **Remember**: [DON'T_FORGET_THIS]

### Continuation Command
To resume this sprint, new Claude Code session should run:
```bash
cd [REPO_PATH]
git checkout refactor/sprint-[NUMBER]
git status  # Should show current state
# Verify checksums match handoff file
```
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