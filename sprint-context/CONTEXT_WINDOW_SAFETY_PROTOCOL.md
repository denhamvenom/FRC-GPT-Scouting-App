# Context Window Safety Protocol for Sprint 8

⚠️ **CRITICAL**: Sprint 8 involves the largest service refactoring (3,113 lines) and may span multiple automatic context windows.

## **Automatic Context Window Behavior**

Claude Code automatically:
1. **Summarizes context** when approaching limits
2. **Transitions to new window** without user intervention  
3. **Continues execution** based on summary

## **Risks with Automatic Transitions**

### **High Risk Areas:**
1. **Baseline Reference Loss**: May lose access to `git show baseline:...` commands
2. **Service State Confusion**: May not accurately track which services are extracted
3. **API Contract Drift**: May lose track of exact interface preservation requirements
4. **Documentation Context**: May summarize away critical decomposition decisions

## **Safety Measures Required**

### **Before Context Window Ends:**
```bash
# Save critical state to files
git add . && git commit -m "Sprint 8 checkpoint: [current phase]"
git show baseline:backend/app/services/picklist_generator_service.py > sprint-context/baseline-picklist-service.py
echo "CURRENT STATE: [describe exact progress]" > sprint-context/current-state.md
echo "NEXT STEPS: [specific instructions]" > sprint-context/next-steps.md
```

### **Critical Files to Preserve:**
1. **baseline-picklist-service.py** - Original service for comparison
2. **sprint-8-session-intent.md** - Complete context and objectives  
3. **sprint-8-decomposition-strategy.md** - Service boundary definitions
4. **current-state.md** - Exact progress checkpoint
5. **next-steps.md** - Specific resumption instructions

### **Recovery Commands for Next Context Window:**
```bash
# If context seems lost, restore critical context
cat sprint-context/NEXT_SESSION_START_HERE.md
cat sprint-context/sprint-8-session-intent.md
cat sprint-context/current-state.md
git log --oneline -5  # See recent progress
git diff baseline --stat  # See what's changed
```

## **User Monitoring Guidelines**

### **Watch For These Indicators:**
- ✅ **Good**: "Creating checkpoint before context transition..."
- ✅ **Good**: "Saved baseline reference to sprint-context/..."  
- ✅ **Good**: "Context transition successful, resuming Sprint 8..."
- ⚠️ **Warning**: "Starting Sprint 8..." (should be "Resuming Sprint 8...")
- ❌ **Bad**: Any attempt to re-read baseline without referencing saved copy
- ❌ **Bad**: Starting over instead of continuing from checkpoint

### **When to Intervene:**
Only intervene if you see signs that context was lost:
```
EMERGENCY: Context transition issue detected.
Please read sprint-context/NEXT_SESSION_START_HERE.md and sprint-context/sprint-8-session-intent.md to recover proper context.
Resume Sprint 8 from documented checkpoint state.
Validate current progress against sprint-context/current-state.md.
```

## **Success Indicators**

### **Proper Context Transition:**
- References saved baseline copy instead of re-extracting
- Continues service extraction from documented checkpoint
- Maintains API contract preservation focus
- References specific service decomposition plan

### **Failed Context Transition:**
- Attempts to restart Sprint 8 from beginning
- Tries to re-analyze baseline without using saved copy
- Loses track of which services are already extracted
- Deviates from documented decomposition strategy

## **Emergency Recovery**

If automatic transition fails completely:
1. **Stop immediately** - Don't let it continue incorrectly
2. **Check git status** - See what was actually completed
3. **Read checkpoint docs** - Understand current state
4. **Provide recovery prompt** with specific context restoration

Remember: **The automatic context transition is helpful but not perfect for complex refactoring. Our safety measures ensure continuity even if the automatic summary loses critical details.**