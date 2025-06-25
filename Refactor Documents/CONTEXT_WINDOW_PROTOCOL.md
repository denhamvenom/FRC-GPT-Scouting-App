# Context Window Protocol for Claude Code

## Purpose
This protocol ensures continuity between Claude Code context windows by:
1. **Maintaining reference to unedited baseline code**
2. **Preserving intent and decision context**
3. **Enabling seamless handoffs between sessions**

## Critical Requirements

### 1. MANDATORY Baseline Reference
Every Claude Code session MUST:

#### At Session Start
```bash
# REQUIRED: Always start with baseline comparison
git checkout baseline  # Switch to unedited reference
git log -1 --oneline   # Note baseline commit
git checkout refactor/sprint-[N]  # Return to work branch
git diff baseline --stat  # See what's changed from original
```

#### During Development
```bash
# Before modifying any file, compare with original
git show baseline:backend/app/services/target_service.py > /tmp/original.py
# Read the original to understand current implementation
# Then make changes while preserving interface
```

#### Before Each Change
- **Read baseline version** of target file first
- **Understand original logic** before refactoring
- **Preserve exact API interface** from baseline
- **Maintain identical behavior** to baseline

### 2. Intent Communication Protocol

#### Session Intent Document
Create `sprint-context/sprint-[N]-session-[X]-intent.md`:

```markdown
# Sprint [N] Session [X] Intent

## Session Overview
- **Start Time**: [TIMESTAMP]
- **Planned Duration**: [HOURS]
- **Primary Goal**: [SPECIFIC_OBJECTIVE]
- **Success Metric**: [HOW_TO_MEASURE_SUCCESS]

## WHY This Work Matters
- **Business Reason**: [Why this change is needed]
- **Technical Reason**: [What problem this solves]
- **Risk Mitigation**: [What failure this prevents]

## Current Understanding
### From Baseline Analysis
- **Original Logic**: [How baseline currently works]
- **Key Dependencies**: [What the original code depends on]
- **Interface Contracts**: [What must be preserved]
- **Edge Cases**: [Special handling in original]

### From Previous Sessions
- **Decisions Made**: [Key architectural choices]
- **Constraints Discovered**: [Limitations found]
- **Assumptions Validated**: [What we learned]
- **Assumptions Remaining**: [What we still need to verify]

## Specific Session Intent
### What I Will Do
1. [SPECIFIC_ACTION_1] - because [REASON]
2. [SPECIFIC_ACTION_2] - because [REASON]
3. [SPECIFIC_ACTION_3] - because [REASON]

### What I Will NOT Do
1. [AVOIDED_ACTION_1] - because [RISK]
2. [AVOIDED_ACTION_2] - because [CONSTRAINT]

### Decision Points
- **If X happens**: Do Y because [REASON]
- **If Z is discovered**: Stop and document because [RISK]

## Next Session Requirements
### Must Pass To Next Window
- **Critical Context**: [What next session MUST know]
- **Open Questions**: [What needs investigation]
- **Alternative Approaches**: [Options to consider]
- **Specific Intent**: [What next session should accomplish]

### Validation Requirements
- [ ] All changes tested against baseline behavior
- [ ] Performance within 5% of baseline
- [ ] API contracts identical to baseline
- [ ] Visual interface unchanged from baseline
```

## Baseline Reference Procedures

### Understanding Original Code
```bash
# STEP 1: Read baseline implementation
git show baseline:backend/app/services/team_comparison_service.py | head -50

# STEP 2: Understand baseline API contracts
git show baseline:backend/app/api/team_comparison.py | grep -E "router\.(get|post)"

# STEP 3: Check baseline tests (if any)
git show baseline:backend/tests/ 2>/dev/null || echo "No tests in baseline"

# STEP 4: Extract baseline dependencies
git show baseline:backend/app/services/team_comparison_service.py | grep "^import\|^from"
```

### Preserving Baseline Behavior
```python
# TEMPLATE for refactoring while preserving baseline behavior

# 1. Read and understand baseline implementation
"""
BASELINE ANALYSIS:
Original function at baseline:backend/app/services/team_service.py:45-67

Original logic:
- Takes team_dict parameter
- Validates required fields: team_number, stats
- Computes ranking_score using formula: stats.opr * 0.4 + stats.endgame * 0.6  
- Returns dict with team_number, ranking_score, computed_at timestamp
- Handles missing stats by setting score to 0
- Raises ValueError for invalid team_number

Interface Contract:
- Input: Dict with team_number (int), stats (dict)
- Output: Dict with team_number, ranking_score, computed_at
- Exceptions: ValueError for invalid input
- Side effects: None (pure function)
"""

def compute_team_ranking(team_dict: dict) -> dict:
    """
    REFACTORED VERSION - PRESERVES BASELINE BEHAVIOR
    
    Baseline Reference: baseline:backend/app/services/team_service.py:45-67
    Original Logic: OPR * 0.4 + Endgame * 0.6 formula
    Interface: MUST match baseline exactly
    """
    # NEW: Input validation (improvement)
    if not isinstance(team_dict, dict):
        raise ValueError("team_dict must be a dictionary")
    
    # PRESERVED: Exact same logic as baseline
    team_number = team_dict.get("team_number")
    if not isinstance(team_number, int) or team_number <= 0:
        raise ValueError("Invalid team_number")
    
    stats = team_dict.get("stats", {})
    
    # PRESERVED: Exact same calculation as baseline
    opr = stats.get("opr", 0)
    endgame = stats.get("endgame", 0)
    ranking_score = opr * 0.4 + endgame * 0.6
    
    # PRESERVED: Exact same return format as baseline
    return {
        "team_number": team_number,
        "ranking_score": ranking_score,
        "computed_at": datetime.now().isoformat()
    }
```

### Baseline Validation
```bash
# After any change, validate against baseline

# 1. Test identical inputs produce identical outputs
echo "Testing baseline compatibility..."

# 2. Compare API responses
curl -s http://localhost:8000/api/team/254 > current_response.json
git show baseline:test_data/expected_team_254.json > baseline_response.json
diff current_response.json baseline_response.json || echo "API DIFFERENCE DETECTED!"

# 3. Compare performance
time curl -s http://localhost:8000/api/teams > /dev/null
# Should be within 5% of baseline timing

# 4. Visual validation (for frontend changes)
# Take screenshot and compare with baseline screenshots
```

## Session Handoff Protocol

### End of Session Checklist
```markdown
## Session [X] Handoff Checklist

### Baseline Preservation Status
- [ ] All changes compared against baseline behavior
- [ ] API contracts verified identical to baseline
- [ ] Performance within acceptable range of baseline
- [ ] No visual changes from baseline interface

### Context Capture
- [ ] Intent document updated with discoveries
- [ ] Decision rationale documented
- [ ] Constraints discovered and recorded
- [ ] Alternative approaches documented

### Next Session Setup
- [ ] Specific next steps documented
- [ ] Open questions identified
- [ ] Blocking issues noted
- [ ] Success criteria defined
```

### Session Intent Handoff
```markdown
## For Next Claude Code Session

### Immediate Context
**Current State**: [What was just completed]
**Next Goal**: [Specific next objective]
**Time Estimate**: [Expected duration]

### Critical Knowledge Transfer
**What Works**: [Validated approaches]
**What Doesn't Work**: [Failed attempts and why]
**Hidden Constraints**: [Discovered limitations]
**Key Insights**: [Important realizations]

### Baseline Preservation Notes
**Interface Changes**: None allowed
**Behavior Changes**: None allowed  
**Performance Impact**: Must stay within 5%
**Visual Impact**: Zero tolerance

### Specific Intent for Next Session
1. **Primary Goal**: [Exact objective]
2. **Approach**: [Recommended method]
3. **Validation**: [How to verify success]
4. **Abort Criteria**: [When to stop and rollback]

### Reference Commands
```bash
# Commands the next session should run first
git checkout baseline && git show HEAD:path/to/file.py
git checkout refactor/sprint-N && git diff baseline path/to/file.py
```
```

## Decision Documentation Format

### For Each Significant Decision
```markdown
## Decision: [SHORT_TITLE]
**Date**: [TIMESTAMP]
**Context**: [What problem this solves]
**Alternatives**: [Other options considered]
**Choice**: [What we decided]
**Rationale**: [Why this choice]
**Baseline Impact**: [How this preserves/affects baseline behavior]
**Risks**: [What could go wrong]
**Validation**: [How we'll verify this works]
**Future Intent**: [How this affects future sessions]
```

### Decision Examples
```markdown
## Decision: Extract Team Model from Service
**Context**: team_comparison_service.py is 847 lines, needs decomposition
**Alternatives**: 
1. Extract to separate module
2. Break into multiple services
3. Use inheritance hierarchy
**Choice**: Extract Team model to domain/models/team.py
**Rationale**: Preserves service interface while improving testability
**Baseline Impact**: Zero - same API, same responses, same timing
**Risks**: Circular import between model and service
**Validation**: All API tests pass, performance unchanged
**Future Intent**: Next session should extract comparison logic using this model

## Decision: Sprint 8 Service Decomposition Approach
**Context**: picklist_generator_service.py is 3,113 lines, largest service in codebase
**Alternatives**:
1. Gradual extraction over multiple sessions
2. Complete decomposition in single session
3. Partial refactoring with most critical areas first
**Choice**: Complete decomposition with context window management
**Rationale**: Service is too complex for partial refactoring, need clean boundaries
**Baseline Impact**: Zero - must preserve exact API contracts and performance
**Risks**: Context window limits, complex service interactions
**Validation**: All picklist generation workflows identical to baseline
**Future Intent**: If context window reached, continue with documented service boundaries
```

## Emergency Context Recovery

### If Context is Lost
```bash
# 1. Return to baseline for reference
git checkout baseline
echo "BASELINE REFERENCE: Use this as source of truth"

# 2. Check what was being worked on
git checkout refactor/sprint-[N]
git log --oneline -5

# 3. Find latest intent document
ls -la sprint-context/sprint-*-session-*-intent.md | tail -1

# 4. Check what was changed
git diff baseline --stat

# 5. Validate current state
pytest tests/ || echo "Tests failing - check rollback"
```

### Context Reconstruction
1. **Read baseline** version of all changed files
2. **Review intent documents** from previous sessions
3. **Analyze git diff** to understand changes made
4. **Run validation tests** to ensure system works
5. **Create new intent document** for current session

## Best Practices

### DO
- ✅ Always read baseline version before editing
- ✅ Document every decision with rationale
- ✅ Preserve exact API interfaces from baseline
- ✅ Test against baseline behavior constantly
- ✅ Create intent documents for next session

### DON'T
- ❌ Modify code without understanding baseline
- ❌ Change interfaces without explicit approval
- ❌ Make assumptions about what previous sessions did
- ❌ Skip baseline comparison steps
- ❌ Leave intent undocumented for next session

## Success Criteria

A session is successful when:
1. **Baseline behavior preserved** - identical API responses
2. **Intent communicated** - next session has clear direction
3. **Context documented** - decisions and constraints recorded
4. **Progress measurable** - specific objectives completed
5. **System stable** - all tests pass, performance maintained

---

**Remember**: The baseline is your source of truth. Every change must be justified against preserving baseline behavior while improving internal structure.