# Baseline Creation and Management Guide

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Establish immutable baseline for safe refactoring

## Overview

The baseline branch serves as an immutable reference point throughout the refactoring process. It represents the last known working state and enables:
- Safe comparison of changes
- Quick rollback capability
- Performance benchmarking
- Functionality verification

## Initial Baseline Creation

### Step 1: Verify Current State
```bash
# Ensure you're on the main branch
git checkout master

# Verify it's up to date
git pull origin master

# Check for uncommitted changes
git status

# Ensure working directory is clean
git clean -n  # Dry run to see what would be cleaned
```

### Step 2: Run Validation Tests
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, verify API health
curl http://localhost:8000/health

# Run any existing tests (if present)
pytest 2>/dev/null || echo "No tests found (expected)"

# Test critical endpoints
curl http://localhost:8000/api/v1/schema
curl http://localhost:8000/api/v1/teams

# Stop backend with Ctrl+C
```

### Step 3: Create Baseline Branch
```bash
# Create baseline from current master
git checkout -b baseline

# Push to remote with upstream tracking
git push -u origin baseline

# Protect branch on GitHub (manual step):
# 1. Go to Settings > Branches
# 2. Add branch protection rule for "baseline"
# 3. Enable: Require pull request reviews
# 4. Enable: Dismiss stale pull request approvals
# 5. Enable: Include administrators
```

### Step 4: Document System State
```bash
# Create baseline documentation directory
mkdir -p docs/baseline

# Document Python dependencies
pip freeze > docs/baseline/requirements-baseline.txt

# Document Node dependencies
cd frontend
npm list --depth=0 > ../docs/baseline/npm-packages-baseline.txt
cd ..

# Document current file structure
tree -I 'node_modules|__pycache__|*.pyc|.git' > docs/baseline/file-structure-baseline.txt

# Generate initial checksums
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > docs/baseline/python-checksums-baseline.txt
find frontend/src -name "*.ts" -o -name "*.tsx" | xargs sha1sum | sort > docs/baseline/typescript-checksums-baseline.txt

# Document API endpoints
grep -r "router\." backend/app/api/*.py | grep -E "(get|post|put|delete|patch)" > docs/baseline/api-endpoints-baseline.txt

# Commit baseline documentation
git add docs/baseline/
git commit -m "feat: establish baseline documentation for refactoring"
git push
```

### Step 5: Create Performance Baseline
Create `scripts/baseline_performance.py`:
```python
#!/usr/bin/env python3
"""Baseline performance testing script."""

import time
import requests
import json
from statistics import mean, stdev

BASE_URL = "http://localhost:8000"
ITERATIONS = 10

endpoints = [
    ("/api/v1/health", "GET", None),
    ("/api/v1/schema", "GET", None),
    ("/api/v1/teams", "GET", None),
    # Add more endpoints as needed
]

results = {}

print("Running baseline performance tests...")
for endpoint, method, data in endpoints:
    times = []
    for i in range(ITERATIONS):
        start = time.time()
        
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        end = time.time()
        times.append((end - start) * 1000)  # Convert to ms
        
    results[endpoint] = {
        "method": method,
        "mean_ms": round(mean(times), 2),
        "stdev_ms": round(stdev(times), 2) if len(times) > 1 else 0,
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2)
    }
    
    print(f"{endpoint}: {results[endpoint]['mean_ms']}ms ± {results[endpoint]['stdev_ms']}ms")

# Save results
with open("docs/baseline/performance-baseline.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nBaseline performance saved to docs/baseline/performance-baseline.json")
```

Run it:
```bash
# Make script executable
chmod +x scripts/baseline_performance.py

# Run performance baseline (ensure backend is running)
python scripts/baseline_performance.py

# Commit results
git add scripts/baseline_performance.py docs/baseline/performance-baseline.json
git commit -m "feat: add performance baseline metrics"
git push
```

## Baseline Maintenance Rules

### What CAN be Added to Baseline
1. **Documentation** in `docs/baseline/`
2. **Scripts** for testing/validation
3. **Security fixes** that don't change functionality
4. **Critical bug fixes** with team approval

### What CANNOT be Added to Baseline
1. **Feature changes**
2. **Refactoring**
3. **Dependency updates** (unless security critical)
4. **Configuration changes** affecting behavior

### Update Process (If Necessary)
```bash
# Only for critical fixes
git checkout baseline
git pull origin baseline

# Make minimal fix
# ... edit files ...

# Test thoroughly
pytest  # if tests exist
python scripts/baseline_performance.py

# Commit with clear message
git add .
git commit -m "fix(baseline): [CRITICAL] <description>"

# Require review (create PR)
git push
# Create PR from baseline to baseline (GitHub will allow this)
# Require 2 reviewers
```

## Using Baseline During Refactoring

### Comparing Changes
```bash
# Compare current branch with baseline
git diff baseline..HEAD --stat

# Compare specific file
git diff baseline -- backend/app/services/some_service.py

# Compare functionality (visual diff)
git difftool baseline..HEAD
```

### Verifying Functionality
```bash
# Run same test on baseline and current branch
git checkout baseline
pytest tests/integration/test_critical_flow.py > baseline-test.log

git checkout refactor/sprint-X
pytest tests/integration/test_critical_flow.py > sprint-test.log

# Compare outputs
diff baseline-test.log sprint-test.log
```

### Performance Comparison
```python
#!/usr/bin/env python3
"""Compare performance with baseline."""

import json
import sys

# Load baseline
with open("docs/baseline/performance-baseline.json", "r") as f:
    baseline = json.load(f)

# Run current performance test
# ... (same code as baseline_performance.py)

# Compare results
print("\nPerformance Comparison:")
print(f"{'Endpoint':<30} {'Baseline':<10} {'Current':<10} {'Delta':<10} {'Status':<10}")
print("-" * 80)

for endpoint, baseline_data in baseline.items():
    if endpoint in results:
        current_data = results[endpoint]
        delta = current_data['mean_ms'] - baseline_data['mean_ms']
        delta_pct = (delta / baseline_data['mean_ms']) * 100
        
        status = "✓ OK" if abs(delta_pct) < 10 else "⚠ CHECK"
        if delta_pct > 20:
            status = "✗ FAIL"
            
        print(f"{endpoint:<30} {baseline_data['mean_ms']:<10} {current_data['mean_ms']:<10} "
              f"{delta:+.2f}ms ({delta_pct:+.1f}%) {status:<10}")
```

## Baseline Recovery Procedures

### Full System Recovery
```bash
# Discard all changes and return to baseline
git checkout baseline
git branch -D refactor/current-sprint  # Delete failed branch

# Reset working directory
git clean -fd
git reset --hard

# Reinstall dependencies
cd backend
pip install -r requirements.txt
cd ../frontend
npm install
```

### Partial Recovery
```bash
# Restore specific files from baseline
git checkout baseline -- backend/app/services/critical_service.py

# Restore entire directory
git checkout baseline -- backend/app/api/

# Cherry-pick specific commits from baseline
git cherry-pick <commit-hash>
```

### Emergency Baseline Archive
```bash
# Create full archive of baseline state
git checkout baseline
mkdir -p archives

# Create timestamped archive
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
git archive --format=tar.gz -o archives/baseline_${TIMESTAMP}.tar.gz baseline

# Include dependencies
tar -czf archives/baseline_full_${TIMESTAMP}.tar.gz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.git \
  .

# Document archive
echo "Baseline archived on $(date)" >> archives/README.md
echo "File: baseline_full_${TIMESTAMP}.tar.gz" >> archives/README.md
echo "SHA256: $(sha256sum archives/baseline_full_${TIMESTAMP}.tar.gz)" >> archives/README.md
```

## Baseline Validation Checklist

### Daily Validation
- [ ] Baseline branch still protected on GitHub
- [ ] No unauthorized commits to baseline
- [ ] Baseline tests still passing
- [ ] Performance metrics unchanged

### Sprint Start Validation
- [ ] Pull latest baseline
- [ ] Run full test suite on baseline
- [ ] Verify all dependencies installed
- [ ] Check baseline checksums match
- [ ] Run performance baseline

### Sprint End Validation
- [ ] Compare coverage: baseline vs current
- [ ] Compare performance: baseline vs current
- [ ] Run integration tests on both
- [ ] Document any acceptable deviations
- [ ] Update comparison reports

## Troubleshooting

### "Baseline has diverged"
```bash
# Check for unauthorized changes
git log baseline --oneline -10

# If changes are authorized, document them
echo "Baseline updated on $(date) - Reason: <reason>" >> docs/baseline/CHANGELOG.md

# If unauthorized, report to team lead immediately
```

### "Can't find baseline branch"
```bash
# Check if it exists remotely
git fetch --all
git branch -r | grep baseline

# If missing, restore from archive
tar -xzf archives/baseline_full_<latest>.tar.gz
git checkout -b baseline
git push -u origin baseline
```

### "Performance regression from baseline"
1. Run profiler on both versions
2. Compare flame graphs
3. Check for algorithm changes
4. Review database queries
5. Document findings in sprint log

---

**Remember**: The baseline is your safety net. Protect it, validate against it, and never modify it without team consensus.