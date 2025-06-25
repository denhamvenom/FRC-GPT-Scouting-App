# Sprint Context Documentation Guide

## Quick Reference for Sprint Documentation Requirements

**Purpose**: Ensure every sprint creates consistent documentation for seamless context transfer between Claude Code sessions.

---

## 📋 Required Documents for EVERY Sprint

### 1. Session Intent Document ✅
**File**: `sprint-context/sprint-[N]-session-intent.md`  
**Template**: SESSION_INTENT_TEMPLATE.md  
**When**: Create BEFORE starting any work  

**Must Include**:
- Session overview with objectives
- Baseline reference status
- WHY this work matters
- Specific approach and validation plan
- Critical context for next session
- Handoff requirements

### 2. Baseline Analysis Document ✅
**File**: `sprint[N]_baseline_analysis.md`  
**When**: Create immediately after baseline extraction  

**Must Include**:
- Target file path and size
- Line count and complexity metrics
- All public methods/functions
- Key dependencies
- Performance characteristics
- Critical behaviors to preserve

### 3. Decomposition Strategy Document ✅
**File**: `sprint-context/[component]-decomposition-strategy.md`  
**When**: Create after baseline analysis, before implementation  

**Must Include**:
- Current structure analysis
- Proposed service/component boundaries
- Dependency mapping
- Migration approach
- Risk mitigation strategies
- Success metrics

### 4. API/Component Contracts Document ✅
**File**: `sprint-context/[component]-contracts.md`  
**When**: Create during implementation  

**Must Include**:
- All public interfaces with signatures
- Parameter specifications
- Return value contracts
- Error behavior documentation
- Performance guarantees
- Baseline compatibility promises

### 5. Validation Report ✅
**File**: `sprint[N]_validation_report.md`  
**When**: Create after implementation complete  

**Must Include**:
- Baseline comparison results
- Test results summary
- Performance benchmarks
- API compatibility verification
- Risk mitigation outcomes
- Success criteria achievement

### 6. Handoff Checklist ✅
**File**: `sprint-context/sprint-[N]-handoff-checklist.md`  
**When**: Complete at sprint end  

**Must Include**:
- Baseline preservation status
- Context capture verification
- Key decisions and discoveries
- Next session setup
- Emergency information
- Handoff validation

---

## 🚀 Sprint Documentation Workflow

### Sprint Start
```bash
# 1. Create session intent
cp Refactor\ Documents/SESSION_INTENT_TEMPLATE.md sprint-context/sprint-[N]-session-intent.md

# 2. Extract baseline for analysis
git show baseline:path/to/target.py > baseline_target.py

# 3. Create baseline analysis
echo "# Sprint [N] Baseline Analysis" > sprint[N]_baseline_analysis.md
# Add metrics, public interfaces, etc.

# 4. Create decomposition strategy
echo "# [Component] Decomposition Strategy" > sprint-context/[component]-decomposition-strategy.md
```

### During Sprint
```bash
# Update session intent with discoveries
vim sprint-context/sprint-[N]-session-intent.md

# Document contracts as you create services/components
vim sprint-context/[component]-contracts.md

# Track decisions and constraints
echo "## Decision: [Title]" >> sprint-context/sprint-[N]-session-intent.md
```

### Sprint End
```bash
# 1. Create validation report
echo "# Sprint [N] Validation Report" > sprint[N]_validation_report.md

# 2. Complete handoff checklist
vim sprint-context/sprint-[N]-handoff-checklist.md

# 3. Verify all documents exist
ls -la sprint-context/sprint-[N]-*.md
ls -la sprint[N]_*.md
```

---

## 📝 Document Templates Summary

### Session Intent Sections
1. Session Overview
2. Baseline Reference Status
3. Intent and Context (WHY)
4. This Session's Specific Intent
5. Critical Context for Next Session
6. Session Execution Log
7. Session Completion Status

### Decomposition Strategy Sections
1. Baseline Analysis
2. Decomposition Strategy
3. Service/Component Boundaries
4. Dependency Design
5. Risk Mitigation
6. Migration Path
7. Success Metrics

### Contracts Document Sections
1. Purpose Statement
2. Public Interface Documentation
3. Baseline Compatibility Notes
4. Integration Patterns
5. Testing Contracts
6. Migration Guide

### Handoff Checklist Sections
1. Baseline Preservation Status
2. Context Capture
3. Key Decisions and Discoveries
4. Next Session Setup
5. Handoff Validation
6. Emergency Information

---

## ✅ Quality Checklist

Before completing any sprint, verify:

- [ ] All 6 required documents created
- [ ] Session intent has complete handoff section
- [ ] Baseline analysis documents all preserved behaviors
- [ ] Decomposition strategy is clear and actionable
- [ ] Contracts guarantee baseline compatibility
- [ ] Validation report shows success metrics met
- [ ] Handoff checklist enables independent next session

---

## 🔍 Common Patterns by Sprint Type

### Backend Service Refactoring
- Focus on service boundaries and API preservation
- Document dependency injection patterns
- Emphasize performance benchmarks
- Map error handling carefully

### Frontend Component Refactoring
- Document all CSS classes and visual structure
- Map component props and state
- Preserve event handlers exactly
- Focus on render behavior

### Infrastructure/Testing Sprints
- Document framework choices
- Capture configuration decisions
- Map integration points
- Define success metrics clearly

---

## 🚨 Red Flags - When Documentation is Incomplete

**Missing Session Intent**: No context for next session
**Missing Baseline Analysis**: Can't verify preservation
**Missing Decomposition Strategy**: No clear approach
**Missing Contracts**: API compatibility at risk
**Missing Validation Report**: Success not proven
**Missing Handoff Checklist**: Next session will struggle

---

## 💡 Best Practices

1. **Start Early**: Create session intent BEFORE any code changes
2. **Update Continuously**: Don't wait until sprint end
3. **Be Specific**: Vague documentation helps no one
4. **Include Commands**: Next session needs exact commands
5. **Document Surprises**: Discoveries and constraints are critical
6. **Think Handoff**: Write for someone who wasn't there

---

## 📊 Sprint 6 Example (Reference)

**Component**: sheets_service.py  
**Documents Created**:
1. ✅ `sprint-6-session-intent.md` (10.6 KB)
2. ✅ `sprint6_baseline_analysis.md` (2.1 KB)
3. ✅ `sheets-service-decomposition-strategy.md` (9.2 KB)
4. ✅ `sheets-service-contracts.md` (13.3 KB)
5. ✅ `sprint6_validation_report.md` (12.8 KB)
6. ✅ `sprint-6-handoff-checklist.md` (8.1 KB)

**Result**: 70% complexity reduction with 100% API compatibility

---

Remember: Good documentation enables great refactoring. The sprint-context folder is your project's memory between Claude Code sessions.