# Rollback Procedures and Emergency Recovery

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Emergency procedures for recovering from failed refactoring attempts

## Overview

This document provides step-by-step procedures for rolling back changes when refactoring goes wrong. Every procedure is designed to restore functionality quickly while preserving any valuable work.

## Rollback Decision Matrix

| Severity | Symptoms | Action | Recovery Time |
|----------|----------|--------|---------------|
| **Critical** | Production down, data loss risk | Immediate full rollback | < 5 minutes |
| **High** | Major features broken, tests failing | Sprint rollback | < 15 minutes |
| **Medium** | Performance degradation, minor bugs | Selective rollback | < 30 minutes |
| **Low** | Code quality issues, warnings | Fix forward | Variable |

## Pre-Rollback Checklist

Before rolling back, quickly assess:

1. **Can it be fixed forward?** (< 30 min fix)
2. **Is data at risk?**
3. **Are users affected?**
4. **Is it just test failures?**
5. **Have you saved current state?**

## Emergency Rollback Procedures

### Level 1: Immediate Full Rollback (< 5 minutes)

For critical failures requiring immediate action:

```bash
#!/bin/bash
# EMERGENCY ROLLBACK SCRIPT

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# 1. Stop all services
echo "Stopping services..."
pkill -f "uvicorn"
pkill -f "npm run dev"

# 2. Save current state for analysis
echo "Saving current state..."
git stash push -m "EMERGENCY: State before rollback $(date +%Y%m%d_%H%M%S)"

# 3. Hard reset to baseline
echo "Reverting to baseline..."
git checkout baseline
git reset --hard origin/baseline

# 4. Clean workspace
echo "Cleaning workspace..."
git clean -fdx
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 5. Reinstall dependencies
echo "Reinstalling dependencies..."
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 6. Restart services
echo "Restarting services..."
cd ../backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev &

echo "✅ EMERGENCY ROLLBACK COMPLETE"
echo "Baseline restored. Services restarting..."
```

### Level 2: Sprint Rollback (< 15 minutes)

For rolling back a failed sprint:

```bash
#!/bin/bash
# Sprint Rollback Procedure

SPRINT_NUMBER=$1

if [ -z "$SPRINT_NUMBER" ]; then
    echo "Usage: ./rollback_sprint.sh <sprint_number>"
    exit 1
fi

echo "Rolling back Sprint $SPRINT_NUMBER..."

# 1. Document the failure
mkdir -p rollbacks/sprint-$SPRINT_NUMBER
git log --oneline > rollbacks/sprint-$SPRINT_NUMBER/git_log.txt
git diff --stat baseline > rollbacks/sprint-$SPRINT_NUMBER/changes.txt
pytest > rollbacks/sprint-$SPRINT_NUMBER/test_failures.txt 2>&1 || true

# 2. Create failure report
cat > rollbacks/sprint-$SPRINT_NUMBER/report.md << EOF
# Sprint $SPRINT_NUMBER Rollback Report
Date: $(date)
Branch: $(git branch --show-current)
Reason: [FILL IN]

## Symptoms
- [ ] Tests failing: $(grep -c "FAILED" rollbacks/sprint-$SPRINT_NUMBER/test_failures.txt || echo "0")
- [ ] Build errors
- [ ] Runtime errors
- [ ] Performance issues

## Files Changed
$(git diff --name-only baseline | wc -l) files modified

## Rollback Decision
[EXPLAIN WHY ROLLBACK WAS NECESSARY]
EOF

# 3. Save work in progress
git add -A
git commit -m "WIP: Sprint $SPRINT_NUMBER before rollback" || true
git branch backup/sprint-$SPRINT_NUMBER-$(date +%Y%m%d_%H%M%S)

# 4. Return to last known good state
git checkout baseline
git checkout -b refactor/sprint-$SPRINT_NUMBER-retry

echo "✅ Sprint $SPRINT_NUMBER rolled back"
echo "Backup saved to: backup/sprint-$SPRINT_NUMBER-*"
echo "New branch created: refactor/sprint-$SPRINT_NUMBER-retry"
```

### Level 3: Selective File Rollback (< 30 minutes)

For rolling back specific files:

```bash
#!/bin/bash
# Selective File Rollback

FILES_TO_ROLLBACK=$@

if [ -z "$FILES_TO_ROLLBACK" ]; then
    echo "Usage: ./rollback_files.sh <file1> <file2> ..."
    exit 1
fi

echo "Rolling back selected files..."

# 1. Verify files exist in baseline
for file in $FILES_TO_ROLLBACK; do
    if ! git show baseline:$file > /dev/null 2>&1; then
        echo "WARNING: $file does not exist in baseline"
    fi
done

# 2. Create backup of current state
git stash push -m "Backup before selective rollback: $FILES_TO_ROLLBACK"

# 3. Rollback each file
for file in $FILES_TO_ROLLBACK; do
    echo "Rolling back: $file"
    git checkout baseline -- $file
done

# 4. Run tests for affected files
echo "Running tests for affected areas..."
for file in $FILES_TO_ROLLBACK; do
    # Find and run associated tests
    test_file="tests/unit/test_$(basename $file)"
    if [ -f "$test_file" ]; then
        pytest $test_file -v
    fi
done

echo "✅ Selective rollback complete"
echo "Rolled back: $FILES_TO_ROLLBACK"
```

## Rollback Recovery Procedures

### Analyzing What Went Wrong

```bash
#!/bin/bash
# Post-Rollback Analysis

FAILURE_DIR="rollbacks/analysis-$(date +%Y%m%d_%H%M%S)"
mkdir -p $FAILURE_DIR

echo "Collecting failure data..."

# 1. Git history
git reflog > $FAILURE_DIR/git_reflog.txt
git log --graph --oneline -20 > $FAILURE_DIR/git_graph.txt

# 2. Test results
pytest -v > $FAILURE_DIR/test_results.txt 2>&1 || true

# 3. Coverage delta
pytest --cov=backend/src --cov-report=term > $FAILURE_DIR/coverage.txt 2>&1 || true

# 4. Performance comparison
python scripts/baseline_performance.py > $FAILURE_DIR/performance.txt 2>&1 || true

# 5. Dependency tree
pip freeze > $FAILURE_DIR/pip_freeze.txt
cd frontend && npm list > ../$FAILURE_DIR/npm_list.txt 2>&1 || true

# 6. System state
df -h > $FAILURE_DIR/disk_space.txt
free -m > $FAILURE_DIR/memory.txt

# Generate analysis report
cat > $FAILURE_DIR/analysis.md << EOF
# Failure Analysis Report

## Timeline
- Failure detected: $(date)
- Last successful commit: $(git log baseline -1 --format="%h %s")
- Failed branch: $(git branch --show-current)

## Test Summary
\`\`\`
$(grep -E "(FAILED|ERROR|passed)" $FAILURE_DIR/test_results.txt | tail -20)
\`\`\`

## Likely Causes
- [ ] Dependency conflict
- [ ] Import error
- [ ] API contract violation
- [ ] Database schema mismatch
- [ ] Performance regression
- [ ] External service failure

## Recommended Actions
1. Review test failures in detail
2. Check for circular imports
3. Verify all mocks are correct
4. Compare with baseline behavior
5. Review sprint objectives

## Lessons Learned
[TO BE FILLED AFTER INVESTIGATION]
EOF

echo "Analysis saved to: $FAILURE_DIR/"
echo "Review $FAILURE_DIR/analysis.md for next steps"
```

### Recovering Lost Work

```bash
#!/bin/bash
# Recover Work from Failed Branch

FAILED_BRANCH=$1
RECOVERY_BRANCH="recovery/$(date +%Y%m%d_%H%M%S)"

echo "Recovering work from $FAILED_BRANCH..."

# 1. Create recovery branch
git checkout -b $RECOVERY_BRANCH

# 2. Cherry-pick good commits
echo "Available commits to recover:"
git log baseline..$FAILED_BRANCH --oneline

echo "Enter commit SHAs to recover (space-separated):"
read COMMITS_TO_RECOVER

for commit in $COMMITS_TO_RECOVER; do
    echo "Recovering commit: $commit"
    git cherry-pick $commit || {
        echo "Conflict in $commit, resolve manually"
        exit 1
    }
done

# 3. Run tests after each recovery
pytest || {
    echo "Tests failing, review recovered changes"
}

echo "✅ Recovery complete on branch: $RECOVERY_BRANCH"
```

## Rollback Communication

### Internal Team Notification

```markdown
## 🚨 Rollback Notification

**Sprint**: [NUMBER]
**Time**: [TIMESTAMP]
**Severity**: [Critical/High/Medium]
**Impact**: [User-facing/Development only]

### What Happened
[Brief description of the failure]

### Actions Taken
1. Rolled back to baseline
2. Saved failed state for analysis
3. Created recovery branch

### Next Steps
- [ ] Root cause analysis by [ASSIGNEE]
- [ ] Fix implementation by [DATE]
- [ ] Review session at [TIME]

### Lessons Learned
[Initial observations]

**Branch Status**:
- Safe: `baseline`
- Failed: `refactor/sprint-X`
- Recovery: `recovery/[timestamp]`
```

## Preventing Future Rollbacks

### Pre-Sprint Safety Checks

```bash
#!/bin/bash
# Pre-Sprint Safety Check

echo "🔍 Running pre-sprint safety checks..."

# 1. Baseline integrity
echo "Checking baseline integrity..."
git checkout baseline
pytest > /tmp/baseline_tests.txt 2>&1
BASELINE_TESTS=$(grep -c "passed" /tmp/baseline_tests.txt || echo "0")

# 2. No uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Uncommitted changes detected"
    exit 1
fi

# 3. Dependencies up to date
pip install -r requirements.txt > /dev/null 2>&1
cd frontend && npm install > /dev/null 2>&1

# 4. Disk space check
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "❌ Low disk space: ${DISK_USAGE}%"
    exit 1
fi

# 5. Create safety checkpoint
git tag -a "checkpoint-$(date +%Y%m%d_%H%M%S)" -m "Pre-sprint checkpoint"

echo "✅ All safety checks passed"
echo "Baseline tests passing: $BASELINE_TESTS"
echo "Safe to proceed with sprint"
```

### Incremental Validation

```python
# scripts/incremental_validation.py
#!/usr/bin/env python3
"""Validate changes incrementally during sprint."""

import subprocess
import sys
from pathlib import Path

def run_tests_for_changed_files():
    """Run only tests affected by current changes."""
    # Get changed files
    result = subprocess.run(
        ["git", "diff", "--name-only", "baseline"],
        capture_output=True,
        text=True
    )
    
    changed_files = result.stdout.strip().split('\n')
    test_files = set()
    
    # Map source files to test files
    for file in changed_files:
        if file.endswith('.py') and 'backend/' in file:
            # Convert source path to test path
            test_path = file.replace('backend/app/', 'backend/tests/unit/')
            test_path = test_path.replace('.py', '_test.py')
            if Path(test_path).exists():
                test_files.add(test_path)
    
    if test_files:
        print(f"Running {len(test_files)} affected test files...")
        cmd = ["pytest"] + list(test_files) + ["-v"]
        result = subprocess.run(cmd)
        return result.returncode == 0
    else:
        print("No test files found for changed code")
        return True

if __name__ == "__main__":
    if run_tests_for_changed_files():
        print("✅ Incremental validation passed")
        sys.exit(0)
    else:
        print("❌ Incremental validation failed")
        sys.exit(1)
```

## Rollback Metrics

Track rollback frequency and causes:

```python
# scripts/rollback_metrics.py
#!/usr/bin/env python3
"""Track rollback metrics for process improvement."""

import json
from datetime import datetime
from pathlib import Path

METRICS_FILE = Path("rollbacks/metrics.json")

def record_rollback(sprint_number, severity, cause, recovery_time):
    """Record a rollback event."""
    if not METRICS_FILE.parent.exists():
        METRICS_FILE.parent.mkdir(parents=True)
    
    # Load existing metrics
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
    else:
        metrics = {"rollbacks": []}
    
    # Add new rollback
    metrics["rollbacks"].append({
        "timestamp": datetime.now().isoformat(),
        "sprint": sprint_number,
        "severity": severity,
        "cause": cause,
        "recovery_time_minutes": recovery_time
    })
    
    # Calculate statistics
    total_rollbacks = len(metrics["rollbacks"])
    by_cause = {}
    for rb in metrics["rollbacks"]:
        cause = rb.get("cause", "unknown")
        by_cause[cause] = by_cause.get(cause, 0) + 1
    
    metrics["statistics"] = {
        "total_rollbacks": total_rollbacks,
        "by_cause": by_cause,
        "average_recovery_time": sum(
            rb.get("recovery_time_minutes", 0) 
            for rb in metrics["rollbacks"]
        ) / total_rollbacks if total_rollbacks > 0 else 0
    }
    
    # Save metrics
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Rollback recorded. Total rollbacks: {total_rollbacks}")
    print(f"Most common cause: {max(by_cause, key=by_cause.get)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: rollback_metrics.py <sprint> <severity> <cause> <recovery_time>")
        sys.exit(1)
    
    record_rollback(
        sprint_number=int(sys.argv[1]),
        severity=sys.argv[2],
        cause=sys.argv[3],
        recovery_time=int(sys.argv[4])
    )
```

## Emergency Contacts

During critical rollbacks:

1. **Technical Lead**: Review rollback decision
2. **DevOps**: Infrastructure issues
3. **Product Owner**: User impact assessment
4. **Team Members**: Code review and fixes

## Post-Rollback Checklist

After successful rollback:

- [ ] Services restored and verified
- [ ] Users notified (if affected)
- [ ] Failure analysis completed
- [ ] Recovery plan created
- [ ] Metrics recorded
- [ ] Lessons learned documented
- [ ] Process improvements identified
- [ ] Next attempt planned

---

**Remember**: Rollbacks are learning opportunities. Every rollback should make the next sprint safer and more successful.