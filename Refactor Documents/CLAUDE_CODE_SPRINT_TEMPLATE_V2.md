# Claude Code Sprint Execution Template V2

## Document Version
- **Version**: 2.0
- **Date**: 2025-06-24
- **Purpose**: Enhanced template with mandatory sprint-context documentation
- **Key Enhancement**: Full integration of sprint-context documentation requirements

---

## Overview

This enhanced template ensures every Claude Code sprint creates comprehensive documentation in the sprint-context folder for seamless context transfer between sessions. It integrates all lessons learned from Sprint 6.

---

## 📋 MANDATORY Sprint Documentation Requirements

Every sprint MUST create these documents in `sprint-context/`:

1. **Session Intent Document** - `sprint-[N]-session-intent.md`
2. **Baseline Analysis** - `sprint[N]_baseline_analysis.md`
3. **Decomposition Strategy** - `[component]-decomposition-strategy.md`
4. **API/Component Contracts** - `[component]-contracts.md`
5. **Validation Report** - `sprint[N]_validation_report.md`
6. **Handoff Checklist** - `sprint-[N]-handoff-checklist.md`

---

## Claude Code Sprint Template

### Pre-Sprint Setup Message

```markdown
You are Claude Code, executing Sprint [NUMBER] of the FRC GPT Scouting App refactoring.

## Sprint Context
- **Repository**: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App
- **Current Branch**: baseline
- **Target Branch**: refactor/sprint-[NUMBER]
- **Sprint Goal**: [SPECIFIC_OBJECTIVE]
- **Target Component**: [FILE_OR_SERVICE_PATH]
- **Time Limit**: [X] hours
- **Success Criteria**: [SPECIFIC_METRICS]

## CRITICAL Documentation Requirements
This sprint MUST create ALL of these documents in sprint-context/:
1. Session Intent Document (BEFORE starting work)
2. Baseline Analysis (AFTER extraction)
3. Decomposition Strategy (BEFORE implementation)
4. API/Component Contracts (DURING implementation)
5. Validation Report (AFTER implementation)
6. Handoff Checklist (AT sprint end)
```

---

## Pre-Flight Checklist with Documentation

### 1. Verify Repository and Create Documentation Structure
```bash
# Verify location
pwd  # Should show correct repository path
ls -la  # Verify ARCHITECTURE.md, backend/, frontend/ exist

# Create sprint-context if needed
mkdir -p sprint-context

# Verify documentation templates exist
ls -la "Refactor Documents/SESSION_INTENT_TEMPLATE.md"
ls -la "Refactor Documents/SPRINT_CONTEXT_DOCUMENTATION_GUIDE.md"
```

### 2. Create Session Intent Document (MANDATORY - DO FIRST!)
```bash
# Copy template BEFORE any other work
cp "Refactor Documents/SESSION_INTENT_TEMPLATE.md" \
   "sprint-context/sprint-[NUMBER]-session-1-intent.md"

echo "⚠️  CRITICAL: Fill out session intent NOW before proceeding!"
echo "📝 Edit: sprint-context/sprint-[NUMBER]-session-1-intent.md"

# Key sections to complete immediately:
# - Session Overview (objectives, success metrics)
# - Baseline Reference Status (target files)
# - Intent and Context (WHY this matters)
# - This Session's Specific Intent
```

### 3. Establish Baseline Reference and Create Analysis
```bash
# Switch to baseline branch
git checkout baseline
git log -1 --oneline  # Note baseline commit
echo "BASELINE COMMIT: $(git rev-parse HEAD)" > sprint-context/baseline-ref.txt

# Extract baseline version of target
git show baseline:[TARGET_FILE_PATH] > baseline_[component].py

# Create baseline analysis document
cat > sprint[NUMBER]_baseline_analysis.md << EOF
# Sprint [NUMBER] Baseline Analysis

## Target Component
- **File**: [TARGET_FILE_PATH]
- **Baseline Size**: $(wc -l < baseline_[component].py) lines
- **Baseline Commit**: $(git rev-parse HEAD)

## Public Interface Analysis
### Public Methods/Functions
$(grep "def [^_]" baseline_[component].py | nl)

### Class Definitions
$(grep "^class " baseline_[component].py | nl)

## Key Characteristics
- **Complexity**: [HIGH/MEDIUM/LOW]
- **Dependencies**: [LIST_KEY_IMPORTS]
- **API Endpoints**: [IF_APPLICABLE]
- **State Management**: [IF_APPLICABLE]

## Critical Behaviors to Preserve
1. [BEHAVIOR_1]
2. [BEHAVIOR_2]
3. [BEHAVIOR_3]

## Performance Baseline
- **Import Time**: [MEASURE_IF_RELEVANT]
- **Key Operation Time**: [MEASURE_IF_RELEVANT]
EOF

# Switch to work branch
git checkout refactor/sprint-[NUMBER] 2>/dev/null || git checkout -b refactor/sprint-[NUMBER]
```

### 4. Create Decomposition Strategy Document
```bash
# Create strategy BEFORE implementation
cat > sprint-context/[component]-decomposition-strategy.md << EOF
# [Component] Decomposition Strategy

## Sprint [NUMBER] Decomposition Document

**Date**: $(date +%Y-%m-%d)
**Target**: [TARGET_FILE_PATH]
**Baseline Reference**: git baseline:[TARGET_FILE_PATH]

## Baseline Analysis
[Copy relevant sections from baseline analysis]

## Decomposition Strategy
### Service/Component Boundaries
[Define how to break down the monolithic component]

### Dependency Mapping
[Show relationships between new components]

### Migration Approach
[Step-by-step plan preserving baseline behavior]

## Risk Mitigation
[How to ensure zero breaking changes]
EOF
```

---

## Sprint Execution Protocol with Documentation

### Step 1: Implement with Continuous Documentation

For each significant change:

```bash
# 1. Update session intent with discoveries
echo "## Discovery: [WHAT_YOU_LEARNED]" >> sprint-context/sprint-[NUMBER]-session-1-intent.md

# 2. Document contracts as you create them
cat >> sprint-context/[component]-contracts.md << EOF
## [Service/Component Name]

### Public Interface
\`\`\`python
[EXACT_METHOD_SIGNATURES]
\`\`\`

### Baseline Compatibility
- [WHAT_IS_PRESERVED]
- [BEHAVIOR_GUARANTEES]
EOF

# 3. Track decisions
echo "## Decision: [TITLE]
**Rationale**: [WHY]
**Impact**: [WHAT]
**Baseline**: [HOW_PRESERVED]" >> sprint-context/sprint-[NUMBER]-session-1-intent.md
```

### Step 2: Validate Against Baseline Continuously

```bash
# Compare public interfaces
diff <(grep "def [^_]" baseline_[component].py) \
     <(grep "def [^_]" [current_file].py)

# Test API compatibility (if applicable)
# [SPECIFIC_VALIDATION_COMMANDS]

# Update validation results
echo "## Validation at $(date +%H:%M)
- Public methods: ✅ Preserved
- API responses: ✅ Identical
- Performance: ✅ Within 5%" >> sprint[NUMBER]_validation_report.md
```

---

## Sprint Completion Protocol with Full Documentation

### 1. Complete Validation Report
```bash
cat > sprint[NUMBER]_validation_report.md << EOF
# Sprint [NUMBER] Validation Report

**Date**: $(date +%Y-%m-%d)
**Sprint**: Phase 3, Sprint [NUMBER]
**Target**: [TARGET_FILE]
**Status**: ✅ COMPLETED SUCCESSFULLY

## Executive Summary
[BRIEF_SUMMARY_OF_ACHIEVEMENTS]

## Baseline Comparison
### Code Metrics
| Metric | Baseline | Refactored | Improvement |
|--------|----------|------------|-------------|
| Lines | [X] | [Y] | [Z]% reduction |
| Methods | [A] | [A] | 100% preserved |

## API Contract Preservation
✅ All [N] public methods preserved exactly
[LIST_METHODS]

## Testing Results
- Integration Tests: [X]/[X] passing
- Unit Tests: [Y]/[Y] passing
- Performance: Within [Z]% of baseline

## Risk Mitigation Results
✅ Zero breaking changes confirmed
✅ Performance maintained
✅ All dependent services working
EOF
```

### 2. Complete All Contract Documentation
```bash
# Ensure all services/components have contracts documented
for service in [LIST_OF_NEW_SERVICES]; do
  echo "Checking contract documentation for $service..."
  [ -f "sprint-context/${service}-contracts.md" ] || echo "❌ Missing!"
done
```

### 3. Create Comprehensive Handoff Checklist
```bash
cat > sprint-context/sprint-[NUMBER]-handoff-checklist.md << EOF
# Sprint [NUMBER] Handoff Checklist

## Session Handoff Document

**Date**: $(date +%Y-%m-%d)
**Sprint**: [SPRINT_DETAILS]
**Status**: COMPLETED ✅
**Next Sprint**: [NEXT_TARGET]

## Baseline Preservation Status
### ✅ All Changes Validated Against Baseline
- [x] Original [component] extracted from baseline branch
- [x] All [N] public methods compared and preserved
- [x] API contracts verified identical to baseline
- [x] Performance maintained within acceptable range

## Context Capture
### ✅ Documentation Created
- [x] Session intent document with full details
- [x] Baseline analysis with metrics
- [x] Decomposition strategy defined
- [x] All contracts documented
- [x] Validation report complete

## Key Decisions and Discoveries
[DOCUMENT_ALL_IMPORTANT_DECISIONS]

## Next Session Setup
### Critical Knowledge Transfer
[WHAT_NEXT_SESSION_MUST_KNOW]

### Reference Commands
\`\`\`bash
# Commands for next sprint
cd [REPO_PATH]
git checkout baseline && git show HEAD:[NEXT_TARGET] > baseline_next.py
\`\`\`
EOF
```

### 4. Update Session Intent with Completion
```bash
# Complete the session intent document
cat >> sprint-context/sprint-[NUMBER]-session-1-intent.md << EOF

## Session Completion Status

### Objectives Achieved
- [x] [OBJECTIVE_1]
- [x] [OBJECTIVE_2]

### Baseline Preservation Verified
- [x] API responses identical to baseline
- [x] Performance within 5% of baseline
- [x] Visual interface unchanged
- [x] All existing tests pass

### Context Captured
- [x] Intent for next session documented
- [x] Decision rationale recorded
- [x] Constraints and discoveries noted
- [x] Alternative approaches identified

**Session Status**: COMPLETED
**Next Session Ready**: YES
EOF
```

### 5. Final Documentation Verification
```bash
# Verify all required documents exist
echo "=== Sprint [NUMBER] Documentation Checklist ==="
for doc in \
  "sprint-context/sprint-[NUMBER]-session-1-intent.md" \
  "sprint[NUMBER]_baseline_analysis.md" \
  "sprint-context/[component]-decomposition-strategy.md" \
  "sprint-context/[component]-contracts.md" \
  "sprint[NUMBER]_validation_report.md" \
  "sprint-context/sprint-[NUMBER]-handoff-checklist.md"; do
  
  if [ -f "$doc" ]; then
    echo "✅ $doc ($(wc -l < "$doc") lines)"
  else
    echo "❌ MISSING: $doc"
  fi
done

# Create documentation summary
echo "
## Sprint [NUMBER] Documentation Summary
Total Documents: 6
Total Lines: $(wc -l sprint-context/sprint-[NUMBER]-*.md sprint[NUMBER]_*.md | tail -1 | awk '{print $1}')
" > sprint-context/sprint-[NUMBER]-doc-summary.txt
```

---

## Context Handoff Template for Mid-Sprint Sessions

If ending mid-sprint, MUST complete:

```bash
# 1. Update session intent with current status
cat >> sprint-context/sprint-[NUMBER]-session-[X]-intent.md << EOF

## Session [X] Handoff Status

### Work Completed This Session
- [WHAT_WAS_DONE]
- [CURRENT_STATE]

### Discoveries Made
- [KEY_FINDING_1]
- [KEY_FINDING_2]

### Next Session MUST
1. Read this intent document first
2. Check baseline differences: git diff baseline [FILE]
3. Continue with: [SPECIFIC_NEXT_TASK]
4. Validate: [WHAT_TO_TEST]

### Critical Context
[ANYTHING_NOT_OBVIOUS_THAT_NEXT_SESSION_NEEDS]
EOF

# 2. Create quick handoff note
echo "Sprint [NUMBER] Session [X] ended at $(date)
Next: $(tail -5 sprint-context/sprint-[NUMBER]-session-[X]-intent.md)" \
> sprint-context/HANDOFF_NOTE.txt
```

---

## Documentation Quality Checklist

Before considering any sprint complete:

- [ ] **Session Intent**: Has complete handoff section?
- [ ] **Baseline Analysis**: Documents all preserved behaviors?
- [ ] **Decomposition Strategy**: Clear service boundaries?
- [ ] **Contracts**: All public interfaces documented?
- [ ] **Validation Report**: Shows success metrics met?
- [ ] **Handoff Checklist**: Enables independent next session?

---

## Success Validation with Documentation

Sprint is successful when:

1. **All objectives met** ✅
2. **All tests passing** ✅  
3. **No performance degradation** ✅
4. **Code quality improved** ✅
5. **All 6 documents complete** ✅
6. **Context fully preserved** ✅

---

## Ready for Next Sprint

Hand off with confidence when:
- All sprint-context documents committed
- Validation shows 100% baseline preservation
- Next sprint setup clearly documented
- System verified working
- Context enables seamless continuation

---

**Remember**: Documentation is not optional - it's the foundation of successful incremental refactoring. The sprint-context folder is your project's memory between Claude Code sessions.