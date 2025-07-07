# Context Preservation Guide

## Document Version
- **Version**: 1.0
- **Date**: 2025-06-22
- **Purpose**: Ensure AI and human context continuity across refactoring sessions

## Overview

Context preservation is critical for successful AI-assisted refactoring. This guide provides templates, standards, and procedures to maintain complete context across:
- AI session boundaries
- Team member handoffs
- Sprint transitions
- Extended time gaps

**NOTE**: This guide focuses on code-level context preservation. For session-level context management, see [CONTEXT_WINDOW_PROTOCOL.md](CONTEXT_WINDOW_PROTOCOL.md) and [SESSION_INTENT_TEMPLATE.md](SESSION_INTENT_TEMPLATE.md).

## Core Principles

1. **Explicit Over Implicit**: Document everything, assume nothing
2. **Checksums Are Truth**: File state tracked by SHA-1
3. **Context In Code**: Docstrings contain AI-relevant information
4. **Audit Everything**: Every decision and change is logged

## Mandatory Docstring Template

Every modified function/class MUST include:

```python
"""
Purpose: [Concise description of what this does]
Inputs: [Parameter types and constraints]
Outputs: [Return type and possible values]
Side-Effects: [Database writes, API calls, file I/O, global state changes]
Dependencies: [Required services, modules, or external resources]

AI-Context:
- Sprint: [Sprint number when last modified]
- Baseline-Reference: [How this relates to baseline:file.py implementation]
- Complexity: [Simple|Medium|Complex]
- Patterns: [Design patterns used]
- Gotchas: [Non-obvious behavior or constraints]
- Refactor-Notes: [Why structured this way]

Example:
    >>> # Example usage if non-trivial
    >>> result = function_name(param1, param2)
    >>> assert result == expected_value

Modified: Sprint-[N] | SHA-1: [Post-modification checksum]
"""
```

### Real Example
```python
"""
Purpose: Generate ranked picklist using GPT-4 for alliance selection
Inputs: 
  - teams: List[Dict] with team_number, stats, and performance metrics
  - strategy: str describing alliance priorities
  - excluded_teams: Set[int] of unavailable team numbers
Outputs: List[int] of team numbers in pick order
Side-Effects: 
  - Calls OpenAI API (costs tokens)
  - Caches results in memory
  - Logs token usage to picklist_generator.log
Dependencies: 
  - OpenAI API key in environment
  - tiktoken for token counting
  - Valid unified dataset loaded

AI-Context:
- Sprint: 5
- Complexity: Complex
- Patterns: Strategy pattern for ranking algorithms
- Gotchas: GPT-4 token limit requires chunking for >50 teams
- Refactor-Notes: Extracted from monolithic service to enable unit testing

Example:
    >>> teams = [{"team_number": 254, "stats": {...}}, ...]
    >>> strategy = "Strong autonomous, reliable climber"
    >>> picklist = generate_picklist(teams, strategy, {180, 971})
    >>> assert isinstance(picklist, list)
    >>> assert all(isinstance(t, int) for t in picklist)

Modified: Sprint-5 | SHA-1: a94a8fe5ccb19ba61c4c0873d391e987982fbbd3
"""
```

## File Header Context Block

Every Python file MUST start with:

```python
"""
Module: [Full module path, e.g., backend.src.services.picklist_service]
Purpose: [One-line description]
Sprint-Created: [N]
Sprint-Modified: [M]

Dependencies:
  - [External packages with versions]
  - [Internal modules with relationships]

AI-Refactor-History:
  - Sprint-1: [What changed]
  - Sprint-3: [What changed]
  - Sprint-5: [Current state]

Integration-Points:
  - Called by: [List of callers]
  - Calls: [List of dependencies]
  - API endpoints: [If applicable]

File-SHA1: [Current checksum]
"""
```

## Sprint Context Documents

### Sprint Start Document
Create `sprint-context/sprint-[N]-start.md`:

```markdown
# Sprint [N] Context Start

## Previous Sprint Summary
- Completed: [What was done]
- Pending: [What wasn't finished]
- Issues: [Problems encountered]

## Current System State
### Modified Files (with checksums)
```
backend/app/services/service1.py: a94a8fe5ccb19ba61c4c0873d391e987982fbbd3
backend/app/services/service2.py: b45a9f6e5ddb29ca71d5d0974e918f8a92fbbda4
```

### Test Status
- Total tests: [N]
- Passing: [N]
- Coverage: [N]%
- Performance baseline: [Link to metrics]

## This Sprint's Goals
1. [Specific objective]
2. [Specific objective]
3. [Success criteria]

## Context Warnings
- [Gotcha 1]: [Description]
- [Gotcha 2]: [Description]

## Decisions Made
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

## External Context
- Related PRs: [List]
- Team discussions: [Summary]
- Blocking issues: [List]
```

### Sprint End Document
Create `sprint-context/sprint-[N]-end.md`:

```markdown
# Sprint [N] Context End

## Completed Objectives
- [x] Objective 1: [Details]
- [x] Objective 2: [Details]
- [ ] Objective 3: [Why not completed]

## Files Modified
| File | Before SHA-1 | After SHA-1 | Changes |
|------|--------------|-------------|---------|
| service1.py | a94a8fe5... | d73b9af2... | Extracted model classes |
| service2.py | b45a9f6e... | e82a7c91... | Added interfaces |

## Test Delta
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Tests | 45 | 67 | +22 |
| Coverage | 42% | 58% | +16% |
| Avg Response | 124ms | 118ms | -6ms |

## Key Code Changes
### Extraction of Domain Models
```python
# Before (in service)
class ServiceClass:
    def process_team(self, team_dict):
        # 100 lines of mixed logic

# After (separated)
# In domain/models/team.py
class Team(BaseModel):
    # Pure domain logic

# In services/team_service.py  
class TeamService:
    def process_team(self, team: Team):
        # Orchestration only
```

## Decisions & Rationale
1. **Used Pydantic for models**: Type safety and validation
2. **Kept service interfaces**: Avoided breaking changes
3. **Added caching decorator**: Improved performance

## Discovered Issues
1. **Issue**: Circular dependency between services
   **Resolution**: Introduced interfaces
   **Follow-up**: Sprint 7 will complete decoupling

2. **Issue**: Tests became flaky after extraction
   **Resolution**: Added proper mocks
   **Follow-up**: Document mock patterns

## Next Sprint Requirements
- Complete interface definitions
- Resolve remaining circular dependencies
- Update API documentation
- Performance test new structure

## Handoff Checklist
- [ ] All tests passing
- [ ] Checksums documented
- [ ] Decisions recorded
- [ ] Issues logged
- [ ] Next sprint planned
```

## AI Session Handoff Template

When switching AI sessions or team members:

```markdown
# AI Session Handoff - Sprint [N]

## Session Ending: [Timestamp]
## Session Duration: [Hours]
## Files Currently Open: [List]

## Current Task State
### Working On
- File: [path]
- Function: [name]
- Status: [In progress|Blocked|Complete]
- Next step: [Specific action]

### Command History (Last 5)
```bash
1. pytest tests/unit/test_service.py::test_function
2. git diff baseline -- backend/app/services/service.py  
3. ruff check backend/app/services/
4. git add -p
5. git commit -m "refactor(sprint-5): extract Team model from service"
```

### Test Results
```
===== 67 passed, 2 skipped, 0 failed in 4.32s =====
Coverage: 58% (up from 42%)
```

### Uncommitted Changes
```bash
$ git status --short
M backend/app/services/team_service.py
A backend/src/domain/models/team.py
? backend/tests/unit/test_team_model.py
```

## Context Switches
### Why Stopping
- [ ] Natural break point
- [ ] Blocked on: [Issue]
- [ ] Time limit reached
- [ ] Switching to different sprint

### Critical Context for Next Session
1. **Important**: [Key information]
2. **Warning**: [Potential issue]
3. **Remember**: [Don't forget this]

### Exact Next Steps
1. Run: `[Specific command]`
2. Fix: `[Specific issue]`
3. Test: `[Specific validation]`
4. Continue: `[Specific task]`

## File Checksums at Handoff
```
[Generated by script - do not edit manually]
```

## Session Metrics
- Lines changed: [N]
- Tests added: [N]
- Coverage delta: [+N%]
- Commits made: [N]
```

## Code Context Anchors

For complex refactoring, add context anchors:

```python
# CONTEXT-ANCHOR: Sprint-5-Extraction-Point
# This is where we extracted the Team model from the monolithic service.
# The original logic was in process_team() method (lines 245-389).
# Preserved behavior by maintaining same validation order.
# See: docs/refactor/sprint-5-extraction-decision.md
```

## Context Preservation Scripts

### Generate Context Snapshot
`scripts/context_snapshot.py`:
```python
#!/usr/bin/env python3
"""Generate context snapshot for current state."""

import subprocess
import json
import hashlib
from datetime import datetime
from pathlib import Path

def get_git_info():
    """Get current git state."""
    return {
        "branch": subprocess.check_output(["git", "branch", "--show-current"]).decode().strip(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
        "status": subprocess.check_output(["git", "status", "--short"]).decode().strip(),
        "uncommitted_files": subprocess.check_output(["git", "diff", "--name-only"]).decode().strip().split('\n')
    }

def get_test_status():
    """Run tests and get status."""
    try:
        result = subprocess.run(
            ["pytest", "--tb=short", "-q"],
            capture_output=True,
            text=True
        )
        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    except Exception as e:
        return {"passed": False, "output": str(e)}

def get_file_checksums(pattern="backend/**/*.py"):
    """Get checksums for Python files."""
    checksums = {}
    for path in Path(".").glob(pattern):
        if "__pycache__" not in str(path):
            with open(path, "rb") as f:
                checksums[str(path)] = hashlib.sha1(f.read()).hexdigest()
    return checksums

def main():
    """Generate and save context snapshot."""
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "git": get_git_info(),
        "tests": get_test_status(),
        "checksums": get_file_checksums(),
    }
    
    # Save snapshot
    snapshot_dir = Path("sprint-context/snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(snapshot_dir / filename, "w") as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"Context snapshot saved to {snapshot_dir / filename}")
    
    # Also save as 'latest'
    with open(snapshot_dir / "latest.json", "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
```

### Verify Context Continuity
`scripts/verify_context.py`:
```python
#!/usr/bin/env python3
"""Verify context continuity from snapshot."""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

def load_snapshot(filename="latest"):
    """Load context snapshot."""
    snapshot_path = Path(f"sprint-context/snapshots/{filename}.json")
    if not snapshot_path.exists():
        print(f"ERROR: Snapshot {snapshot_path} not found")
        sys.exit(1)
    
    with open(snapshot_path) as f:
        return json.load(f)

def verify_checksums(expected_checksums):
    """Verify file checksums match."""
    mismatches = []
    
    for filepath, expected_sha in expected_checksums.items():
        path = Path(filepath)
        if not path.exists():
            mismatches.append(f"MISSING: {filepath}")
            continue
            
        with open(path, "rb") as f:
            actual_sha = hashlib.sha1(f.read()).hexdigest()
            
        if actual_sha != expected_sha:
            mismatches.append(f"MISMATCH: {filepath}")
            mismatches.append(f"  Expected: {expected_sha}")
            mismatches.append(f"  Actual:   {actual_sha}")
    
    return mismatches

def main():
    """Verify context continuity."""
    # Load snapshot
    snapshot_file = sys.argv[1] if len(sys.argv) > 1 else "latest"
    snapshot = load_snapshot(snapshot_file)
    
    print(f"Verifying context from: {snapshot['timestamp']}")
    print(f"Original branch: {snapshot['git']['branch']}")
    print(f"Original commit: {snapshot['git']['commit'][:8]}")
    print()
    
    # Verify checksums
    print("Verifying file checksums...")
    mismatches = verify_checksums(snapshot['checksums'])
    
    if mismatches:
        print("ERROR: Context verification failed!")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(snapshot['checksums'])} files match")
        print("\nContext verified. Safe to continue.")

if __name__ == "__main__":
    main()
```

## Context Recovery Procedures

### Lost Context Recovery
1. Find latest snapshot: `ls sprint-context/snapshots/`
2. Verify against snapshot: `python scripts/verify_context.py`
3. Check sprint documents: `ls sprint-context/sprint-*-end.md`
4. Review git log: `git log --oneline -20`
5. Restore from checkpoint if needed

### Context Conflict Resolution
When contexts conflict:
1. Checksums are authoritative
2. Git history provides timeline
3. Sprint documents explain decisions
4. Test results validate functionality

## Best Practices

### DO's
1. **DO** run context snapshot before stopping work
2. **DO** verify context when resuming work  
3. **DO** document every non-obvious decision
4. **DO** include examples in docstrings
5. **DO** update checksums after every change

### DON'Ts  
1. **DON'T** trust memory over documentation
2. **DON'T** skip checksum verification
3. **DON'T** leave TODOs without context
4. **DON'T** assume AI remembers previous sessions
5. **DON'T** modify files without updating context

---

**Remember**: Perfect context preservation enables perfect refactoring. When in doubt, over-document.