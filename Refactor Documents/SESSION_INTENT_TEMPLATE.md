# Session Intent Template

## Purpose
Template for capturing and communicating intent between Claude Code context windows. Copy this template for each session to ensure seamless handoffs.

## Template: SESSION_INTENT_[SPRINT]_[SESSION].md

```markdown
# Sprint [N] Session [X] Intent Document

## Session Overview
- **Sprint**: [N]
- **Session**: [X] 
- **Start Time**: [YYYY-MM-DD HH:MM]
- **Planned Duration**: [X hours]
- **Primary Objective**: [ONE SPECIFIC GOAL]
- **Success Metric**: [HOW TO MEASURE COMPLETION]

## Baseline Reference Status
### Current Branch State
```bash
# Run these commands to establish baseline context
git branch --show-current     # Should be: refactor/sprint-[N]
git diff baseline --stat      # Show changes from original
git log baseline..HEAD --oneline  # Show commits since baseline
```

### Baseline Files for Reference
- **Primary Target**: `[FILE_PATH]` - [WHAT IT DOES IN BASELINE]
- **Dependencies**: `[FILE_PATH]` - [HOW IT CONNECTS]
- **API Contracts**: `[FILE_PATH]` - [INTERFACES TO PRESERVE]

### Baseline Behavior to Preserve
```markdown
Critical behaviors that MUST remain identical:
1. [BEHAVIOR_1]: [API endpoint X returns exactly same JSON structure]
2. [BEHAVIOR_2]: [Performance within 5% of baseline timing]
3. [BEHAVIOR_3]: [Visual interface pixel-perfect match]
```

## Intent and Context

### WHY This Work Is Needed
**Business Context**: [Why this change matters to users]
**Technical Context**: [What problem this solves in the code]
**Risk Context**: [What breaks if we don't do this]

### Previous Session Results
**What Was Completed**: 
- [X] [COMPLETED_TASK_1]
- [X] [COMPLETED_TASK_2]

**What Was Discovered**:
- [INSIGHT_1]: [Important learning about the codebase]
- [CONSTRAINT_1]: [Limitation that affects our approach]
- [ASSUMPTION_VALIDATED]: [Something we confirmed is true]

**What Didn't Work**:
- [FAILED_APPROACH_1]: [Why it failed and what was learned]
- [BLOCKED_ITEM]: [What couldn't be completed and why]

### Current Understanding
**How Baseline Currently Works**:
```python
# From baseline analysis
def current_implementation():
    """
    Baseline Logic Summary:
    - [STEP_1]: [What happens first]
    - [STEP_2]: [What happens next]  
    - [EDGE_CASE]: [Special handling for X]
    
    Interface Contract:
    - Input: [TYPE] - [CONSTRAINTS]
    - Output: [TYPE] - [FORMAT]
    - Side Effects: [WHAT IT CHANGES]
    """
```

**Key Dependencies Identified**:
- [MODULE_1]: [How it's used and why it matters]
- [API_1]: [What data it provides]
- [SERVICE_1]: [What functionality it handles]

**Constraints and Limitations**:
- [TECHNICAL_CONSTRAINT]: [Why we can't do X]
- [BUSINESS_CONSTRAINT]: [User requirement that limits options]
- [PERFORMANCE_CONSTRAINT]: [Timing requirement to maintain]

## This Session's Specific Intent

### Primary Goal
**Objective**: [ONE CLEAR, MEASURABLE GOAL]
**Why Now**: [Why this is the logical next step]
**Success Looks Like**: [Specific criteria for completion]

### Approach Strategy
**Chosen Approach**: [SPECIFIC_METHOD]
**Why This Approach**: [Rationale over alternatives]
**Key Implementation Steps**:
1. [STEP_1]: [Specific action] - Expected duration: [TIME]
2. [STEP_2]: [Specific action] - Expected duration: [TIME]  
3. [STEP_3]: [Specific action] - Expected duration: [TIME]

**Validation Plan**:
- [ ] [VALIDATION_1]: [How to verify step 1 worked]
- [ ] [VALIDATION_2]: [How to verify step 2 worked]
- [ ] [VALIDATION_3]: [How to verify overall success]

### Alternative Approaches Considered
1. **[ALTERNATIVE_1]**: 
   - Pros: [BENEFITS]
   - Cons: [DOWNSIDES]
   - Why not chosen: [SPECIFIC_REASON]

2. **[ALTERNATIVE_2]**:
   - Pros: [BENEFITS]
   - Cons: [DOWNSIDES] 
   - Why not chosen: [SPECIFIC_REASON]

### What I Will NOT Do
- [AVOIDED_ACTION_1]: Because [RISK_OR_CONSTRAINT]
- [AVOIDED_ACTION_2]: Because [RISK_OR_CONSTRAINT]
- [SCOPE_LIMITATION]: [What's explicitly out of scope for this session]

### Decision Framework
**If [CONDITION_1] occurs**: Then [ACTION_1] because [REASON]
**If [CONDITION_2] occurs**: Then stop and document because [RISK]
**If performance degrades >5%**: Rollback immediately
**If visual changes detected**: Abort and investigate

## Critical Context for Next Session

### Must Transfer to Next Window
**Essential Knowledge**:
- [CRITICAL_FACT_1]: [Information next session cannot discover easily]
- [CRITICAL_FACT_2]: [Constraint that affects all future work]
- [CRITICAL_FACT_3]: [Insight that changes our approach]

**Decision Rationale**:
- **Why [DECISION_1]**: [Reasoning that next session needs to understand]
- **Why [DECISION_2]**: [Context behind choice that might not be obvious]

**Open Questions for Next Session**:
- [QUESTION_1]: [Investigation needed] - Priority: [HIGH/MED/LOW]
- [QUESTION_2]: [Research required] - Priority: [HIGH/MED/LOW]

### Next Session Intent
**Immediate Next Goal**: [SPECIFIC_NEXT_OBJECTIVE]
**Estimated Duration**: [TIME_ESTIMATE]
**Prerequisites**: [WHAT_MUST_BE_DONE_FIRST]

**Recommended Approach**: [SUGGESTED_METHOD]
**Alternative to Consider**: [BACKUP_APPROACH]

**Context Commands for Next Session**:
```bash
# Commands next session should run to get oriented
cd [REPO_PATH]
git checkout refactor/sprint-[N]
git diff baseline [SPECIFIC_FILE]  # See what's changed
git show baseline:[SPECIFIC_FILE] | head -20  # See original
```

### Handoff Validation
**Before Next Session Starts**:
- [ ] All tests passing: `pytest tests/`
- [ ] System still works: `curl http://localhost:8000/health`
- [ ] Changes committed: `git status` shows clean
- [ ] Intent documented: This file complete

**Next Session Should Verify**:
- [ ] Baseline reference accessible
- [ ] Current state matches expected
- [ ] Prerequisites met
- [ ] Context understood

## Session Execution Log

### Actions Taken
**[TIMESTAMP]**: [ACTION_TAKEN] - [RESULT]
**[TIMESTAMP]**: [ACTION_TAKEN] - [RESULT]
**[TIMESTAMP]**: [ACTION_TAKEN] - [RESULT]

### Discoveries Made
**[DISCOVERY_1]**: [WHAT_WAS_LEARNED] - [IMPACT_ON_PLAN]
**[DISCOVERY_2]**: [WHAT_WAS_LEARNED] - [IMPACT_ON_PLAN]

### Issues Encountered
**[ISSUE_1]**: [PROBLEM] - [RESOLUTION_OR_STATUS]
**[ISSUE_2]**: [PROBLEM] - [RESOLUTION_OR_STATUS]

### Decisions Made
**[DECISION_1]**: [CHOICE] - [RATIONALE] - [IMPACT]
**[DECISION_2]**: [CHOICE] - [RATIONALE] - [IMPACT]

## Session Completion Status

### Objectives Achieved
- [X] [COMPLETED_OBJECTIVE_1]
- [X] [COMPLETED_OBJECTIVE_2]  
- [ ] [INCOMPLETE_OBJECTIVE]: [WHY_NOT_COMPLETED]

### Baseline Preservation Verified
- [ ] API responses identical to baseline
- [ ] Performance within 5% of baseline  
- [ ] Visual interface unchanged
- [ ] All existing tests pass

### Context Captured
- [ ] Intent for next session documented
- [ ] Decision rationale recorded
- [ ] Constraints and discoveries noted
- [ ] Alternative approaches identified

### Handoff Ready
- [ ] Code committed and pushed
- [ ] Documentation updated
- [ ] Next session can proceed independently
- [ ] Rollback possible if needed

## Emergency Information

### If This Session Failed
**Rollback Command**: `git reset --hard [SAFE_COMMIT_HASH]`
**Baseline Return**: `git checkout baseline`
**Emergency Contact**: [PERSON_TO_NOTIFY]

### If Next Session Gets Stuck
**Context Recovery**: Read this document + run baseline comparisons
**Alternative Approach**: [BACKUP_PLAN_DETAILS]
**Expert Knowledge**: [WHERE_TO_FIND_HELP]

---
**Session Status**: [IN_PROGRESS / COMPLETED / FAILED / HANDED_OFF]
**Next Session Ready**: [YES / NO / NEEDS_REVIEW]
```

## Usage Instructions

### At Session Start
1. Copy this template to `sprint-context/sprint-[N]-session-[X]-intent.md`
2. Fill in all sections based on current context
3. Reference baseline files before making changes
4. Document your specific intent and approach

### During Session
1. Update the "Session Execution Log" as you work
2. Document discoveries and decisions immediately
3. Keep track of what works and what doesn't
4. Note any changes to your planned approach

### At Session End
1. Complete the "Session Completion Status" section
2. Fill in detailed "Next Session Intent"
3. Verify all context is captured for handoff
4. Commit and save the intent document

### For Next Session
1. Read the previous session's intent document
2. Verify the baseline reference state
3. Understand the context and constraints
4. Create new intent document for your session

## Template Examples

### Example: Session for Extracting Team Model

```markdown
# Sprint 3 Session 1 Intent Document

## Session Overview
- **Sprint**: 3
- **Session**: 1
- **Start Time**: 2025-06-23 09:00
- **Primary Objective**: Extract Team model from team_comparison_service.py
- **Success Metric**: Team class in domain/models with identical behavior

## Baseline Reference Status
### Current Branch State
```bash
git branch --show-current     # refactor/sprint-3
git diff baseline --stat      # 0 files changed (starting fresh)
```

### Baseline Files for Reference
- **Primary Target**: `backend/app/services/team_comparison_service.py` - 847 lines, contains Team logic mixed with comparison logic
- **Dependencies**: `backend/app/api/team_comparison.py` - API endpoints that call the service
- **API Contracts**: All endpoints in team_comparison.py must return identical responses

### Baseline Behavior to Preserve
1. **Team validation**: Team objects must validate same fields with same error messages
2. **Comparison logic**: Rankings must use identical algorithm (OPR * 0.4 + Endgame * 0.6)
3. **API responses**: JSON structure must be byte-identical to baseline

## Intent and Context

### WHY This Work Is Needed
**Business Context**: Team comparison is core functionality, needs to be testable
**Technical Context**: 847-line service is unmaintainable, needs decomposition
**Risk Context**: Breaking team comparison breaks alliance selection

### Current Understanding
**How Baseline Currently Works**:
Team data is embedded in service methods with validation scattered throughout.
Comparison logic directly manipulates dictionaries without type safety.

### This Session's Specific Intent
**Objective**: Create domain/models/team.py with Team class that encapsulates all team-related logic
**Approach**: Extract-and-preserve pattern - create new class with identical behavior, then gradually migrate service to use it
**Success**: Service uses Team class but produces identical API responses

### Critical Context for Next Session
**Next Goal**: Migrate comparison logic to use new Team model
**Prerequisites**: Team model must be thoroughly tested and service integration verified
```

## Best Practices

### For Intent Clarity
- Be specific about objectives (not "refactor service" but "extract Team model from team_comparison_service.py")
- Document WHY decisions were made, not just WHAT was decided
- Include code examples when explaining baseline behavior
- Capture constraints and limitations that affect future work

### For Context Preservation
- Always reference baseline behavior explicitly
- Document alternatives considered and why they were rejected
- Record discoveries that change understanding of the system
- Note any assumptions that were validated or invalidated

### For Seamless Handoffs
- Write intent as if explaining to a colleague who knows the project but wasn't in previous sessions
- Include specific commands the next session should run
- Provide enough context to continue work independently
- Plan for failure cases and recovery options

Remember: Good intent documentation enables confident, efficient work in the next context window.