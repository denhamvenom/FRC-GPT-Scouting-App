# User Execution Guide - Simple Step-by-Step Instructions

## Your Role
You have 3 simple responsibilities:
1. **Paste prompts** to Claude Code
2. **Test the website** in your browser
3. **Report any problems** you see

You will NOT need to:
- Write any code
- Understand technical details
- Make technical decisions
- Use command line directly

## Before Starting

### 1. Check Your Setup
- [ ] VSCode is open
- [ ] Claude Code extension is installed
- [ ] You can see the terminal at bottom of VSCode
- [ ] The website runs when you test it

### 2. Test Current Website
1. Open your web browser
2. Go to: `http://localhost:3000` (or `http://localhost:5173` if using Vite)
3. Click through all pages and workflows
4. Note: Manual screenshots have already been captured and integrated into the safety system
5. Make note of how everything looks - this is your reference

## Phase 1: Safety Setup (Day 1-2)

### Sprint 1 - Create Safety Systems

**Step 1: Start Claude Code**
In VSCode terminal, paste exactly:
```
Execute Sprint 1: Safety Infrastructure for FRC Scouting App refactoring.
Follow MASTER_REFACTORING_GUIDE.md Phase 1, Sprint 1.
Repository: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App
Create comprehensive safety systems before any code changes.
```

**Step 2: Wait**
- Claude Code will work for 30-60 minutes
- You'll see lots of text scrolling
- Wait for "Sprint 1 Complete" message

**Step 3: Check Results**
When Claude Code says it's done:
1. Look for any error messages
2. If errors, copy and paste them back to Claude Code
3. If no errors, proceed to capture baselines (next step)

**Step 4: Capture Baseline Data**
IMPORTANT: You must start the application and capture baselines:
1. Start the application: Run `docker-compose up` in terminal
2. Wait for both services to start (backend on :8000, frontend on :3000 or :5173)
3. Run these commands in terminal (copy one at a time):
   ```bash
   python safety/baseline_metrics.py --capture
   python safety/data_integrity_validator.py --snapshot
   ```
4. Verify visual baselines are ready (manual screenshots already integrated)
5. If successful, move to Sprint 2

### Sprint 2 - Prepare for Changes

**Step 1: Continue**
Paste exactly:
```
Execute Sprint 2: Canary Selection and Analysis.
Follow MASTER_REFACTORING_GUIDE.md Phase 1, Sprint 2.
Select Team Comparison workflow as canary.
Prepare for safe refactoring with zero visual changes.
```

**Step 2: Wait and Verify**
- Another 30-45 minutes
- Claude Code will analyze the code
- Wait for completion message

## Phase 2: Test Refactoring (Day 3-5)

### Sprint 3 - Backend Changes

**Step 1: Start Backend Refactoring**
Paste exactly:
```
Execute Sprint 3: Canary Backend Refactoring for Team Comparison service.
Follow MASTER_REFACTORING_GUIDE.md Phase 2, Sprint 3.
Target: backend/app/services/team_comparison_service.py
Preserve ALL API contracts exactly. Zero functional changes allowed.
```

**Step 2: Test When Complete**
1. Open website in browser
2. Go to Team Comparison feature
3. Test everything still works exactly the same
4. If ANYTHING is different, report immediately

**Step 3: Report Results**
- If everything works: "Sprint 3 testing complete. No issues found."
- If something broke: "PROBLEM: [describe what's wrong]"

### Sprint 4 - Frontend Changes

**CRITICAL**: This sprint might change how things look. Test carefully!

**Step 1: Take "Before" Screenshots**
1. Open Team Comparison modal
2. Screenshot every state:
   - Modal closed
   - Modal open
   - Selecting teams
   - Viewing comparison
   - Any error states

**Step 2: Start Frontend Refactoring**
Paste exactly:
```
Execute Sprint 4: Canary Frontend Component Refactoring.
Follow MASTER_REFACTORING_GUIDE.md Phase 2, Sprint 4.
Target: TeamComparisonModal component.
CRITICAL: Zero visual changes allowed. Pixel-perfect preservation required.
```

**Step 3: Intensive Testing**
When complete:
1. Open Team Comparison again
2. Compare with your screenshots
3. Look for ANY differences:
   - Colors
   - Positions
   - Fonts
   - Spacing
   - Animations

**Step 4: Report**
- If IDENTICAL: "Sprint 4 visual testing complete. No changes detected."
- If ANY difference: "VISUAL CHANGE DETECTED: [describe exactly what's different]"

### Sprint 5 - Final Validation

**Step 1: Complete Testing**
Paste exactly:
```
Execute Sprint 5: Integration Validation and Decision Point.
Follow MASTER_REFACTORING_GUIDE.md Phase 2, Sprint 5.
Run comprehensive validation of Team Comparison workflow.
Prepare go/no-go decision report.
```

**Step 2: Full Test**
1. Test entire website thoroughly
2. Focus on Team Comparison
3. Check performance (does it feel slower?)
4. Verify all data is correct

**Step 3: Decision Time**
Based on Claude Code's report and your testing:
- If everything perfect: "Approve continuation to Phase 3"
- If any issues: "Stop here. Issues found: [list them]"

## If Something Goes Wrong

### Small Problems
If something seems wrong but website still works:
```
Minor issue detected: [describe what you see]
Please investigate and fix while preserving all visuals.
```

### Big Problems  
If website is broken or looks different:
```
EMERGENCY: System broken. Execute emergency rollback immediately.
Visual changes detected in [describe where].
```

### Understanding Baseline Validation
During Phase 3, Claude Code will frequently reference the "baseline" - this is the original code before any changes. You'll see messages like:
- "Comparing against baseline version..."
- "Baseline analysis complete..."
- "Validating interface matches baseline..."

This is normal and means Claude Code is being extra careful to preserve original behavior.

### After Emergency
1. Claude Code will restore the original
2. Test website works again
3. Take a break before retrying

## Testing Checklist

### For Every Sprint
- [ ] Website still loads
- [ ] All pages accessible
- [ ] No visual changes (compare to baseline/screenshots)
- [ ] All features work exactly as before
- [ ] No error messages in browser console
- [ ] Same speed/performance (or better)
- [ ] Data integrity maintained

### Visual Testing Focus
- [ ] Colors exactly the same
- [ ] Nothing moved position
- [ ] Same fonts and sizes
- [ ] Spacing unchanged
- [ ] Animations identical
- [ ] No new elements
- [ ] No missing elements

### Team Comparison Specific
- [ ] Modal opens/closes same way
- [ ] Team selection works
- [ ] Data displays correctly
- [ ] Charts look identical
- [ ] Export features work
- [ ] No loading delays

## Common Claude Code Responses

### When It Needs Help
"I encountered an error: [technical details]"
→ Copy the ENTIRE error message and paste it back

### When It's Thinking
"Let me analyze the current state..."
→ Just wait, this is normal

### When It's Done
"Sprint X complete. All objectives achieved."
→ Time to test!

## Tips for Success

1. **Be Patient**
   - Each sprint takes 30-90 minutes
   - Don't interrupt Claude Code while working
   - Wait for clear completion messages

2. **Test Thoroughly**
   - Click everything
   - Try edge cases
   - Compare with screenshots
   - Trust your eyes

3. **Report Clearly**
   - Describe what you see, not what you think
   - Include exact error messages
   - Note which page/feature has issues
   - Screenshot problems

4. **Stay Calm**
   - Rollback always available
   - Nothing permanently broken
   - Each sprint is reversible
   - Learning from failures is good

## What You'll See: Sprint Documentation Process

Starting with Sprint 6, you'll notice Claude Code spends extra time creating documentation. This is NORMAL and CRITICAL. Here's what to expect:

### Expected Claude Code Behavior
- **More initial setup time**: Creating session intent documents before starting work
- **Frequent baseline references**: Messages about "extracting baseline version" and "comparing with baseline"
- **Documentation updates**: Creating multiple .md files in sprint-context folder
- **Validation reports**: Comprehensive testing against original behavior
- **Handoff preparation**: Setting up context for potential next sessions

### What You'll See Created
For each sprint, Claude Code will create 6 documents:
1. Session intent document (planning and context)
2. Baseline analysis (original behavior to preserve)
3. Decomposition strategy (how to break down complex code)
4. API/Component contracts (interface guarantees)
5. Validation report (proof everything works)
6. Handoff checklist (setup for next work)

### Why This Matters
This documentation ensures:
- Nothing gets broken during refactoring
- Any future work can continue seamlessly
- All decisions are tracked and explained
- Quality is proven, not assumed

**This is good!** The extra documentation time prevents problems and enables confident continued improvement.

---

## Phase 3: Expansion (Only If Phase 2 Perfect)

**IMPORTANT**: Only proceed if Sprint 5 resulted in "GO TO PHASE 3" decision.

If Team Comparison refactoring went perfectly, we can carefully expand to improve more of the codebase:

### Sprint 6 - Backend Service Refactoring (Sheets Service)

**Step 1: Start Sheets Service Refactoring**
Paste exactly:
```
Execute Sprint 6: Backend Service Refactoring - Sheets Service.
Follow MASTER_REFACTORING_GUIDE.md and CONTEXT_WINDOW_PROTOCOL.md for detailed requirements.
Target: backend/app/services/sheets_service.py

CRITICAL REQUIREMENTS:
- Reference baseline branch for all original code
- Create session intent document for context preservation
- Validate all changes preserve exact baseline behavior
- Document decisions for next context window

MANDATORY DOCUMENTATION REQUIREMENTS:
- Create session intent document BEFORE starting any work
- Document baseline analysis with all preserved behaviors
- Create decomposition strategy for the service refactoring
- Document all API contracts and preservation guarantees
- Create comprehensive validation report
- Complete handoff checklist for next session

BASELINE PRESERVATION:
- START by extracting baseline version: git show baseline:backend/app/services/sheets_service.py
- Document baseline characteristics before any changes
- Decompose into 5 focused services per plan
- Preserve ALL Google Sheets API functionality exactly (validate against baseline)
- Maintain authentication and caching behavior identical to baseline
- Zero breaking changes to dependent services
- Create comprehensive integration tests
- Continuously compare against baseline during refactoring
```

**Step 2: Test Google Sheets Integration**
When complete:
1. Test data import from Google Sheets
2. Try sheet configuration features
3. Verify authentication still works
4. Check that data loads correctly
5. Make sure export functions work

**Step 3: Report Results**
- If everything works: "Sprint 6 testing complete. Google Sheets integration working perfectly."
- If problems: "PROBLEM with sheets: [describe what's broken]"

### Sprint 7 - Frontend Component Refactoring (Picklist Generator)

**CRITICAL**: This is the largest component - test extra carefully!

**Step 1: Take "Before" Screenshots**
1. Open Picklist Generator page
2. Screenshot every state:
   - Initial load
   - Priority selection
   - Team list display
   - Generation in progress
   - Results display
   - Export functions

**Step 2: Start Picklist Generator Refactoring**
Paste exactly:
```
Execute Sprint 7: Frontend Component Refactoring - PicklistGenerator.
Follow MASTER_REFACTORING_GUIDE.md and CONTEXT_WINDOW_PROTOCOL.md for detailed requirements.
Target: frontend/src/components/PicklistGenerator.tsx

CRITICAL REQUIREMENTS:
- Reference baseline branch for all original code
- Create session intent document for context preservation
- Validate all changes preserve exact baseline behavior
- Document decisions for next context window

MANDATORY DOCUMENTATION REQUIREMENTS:
- Create session intent document BEFORE starting any work
- Document baseline visual analysis with all preserved behaviors
- Create component decomposition strategy
- Document all component contracts and visual preservation
- Create comprehensive validation report
- Complete handoff checklist for next session

BASELINE PRESERVATION:
- START by extracting baseline version: git show baseline:frontend/src/components/PicklistGenerator.tsx
- Document baseline visual structure (CSS classes, props, state)
- Decompose into 6+ focused components per plan
- ZERO visual changes - pixel-perfect preservation vs baseline required
- Maintain all state management patterns identical to baseline
- Preserve Team Comparison modal integration (already refactored)
- Extract custom hooks for logic separation
- Validate CSS classes and props interfaces against baseline continuously
```

**Step 3: Intensive Visual Testing**
When complete:
1. Compare with your screenshots pixel by pixel
2. Test all picklist generation workflows
3. Verify Team Comparison integration still works
4. Check priority selection interface
5. Test all export functions
6. Verify loading animations and progress bars

**Step 4: Report**
- If IDENTICAL: "Sprint 7 visual testing complete. No changes detected in Picklist Generator."
- If ANY difference: "VISUAL CHANGE DETECTED in Picklist Generator: [describe exactly what's different]"

### Sprint 8 - Critical Backend Refactoring (Picklist Generator Service)

**CRITICAL**: This is the largest refactoring in the entire project - 3,113 lines of complex business logic!

**Step 1: Take System Performance Baseline**
Before starting:
1. Test complete picklist generation workflow
2. Note generation times (how long it takes)
3. Test batch processing if used
4. Check GPT analysis features
5. Screenshot all states for reference

**Step 2: Start Critical Service Refactoring**
Paste exactly:
```
Execute Sprint 8: Critical Backend Refactoring - Picklist Generator Service.
Follow MASTER_REFACTORING_GUIDE.md and CONTEXT_WINDOW_PROTOCOL.md for detailed requirements.
Target: backend/app/services/picklist_generator_service.py (3,113 lines)

CRITICAL REQUIREMENTS:
- Reference baseline branch for all original code
- Create session intent document for context preservation
- Validate all changes preserve exact baseline behavior
- Document decisions for next context window

MANDATORY DOCUMENTATION REQUIREMENTS:
- Create session intent document BEFORE starting any work
- Document baseline analysis with all preserved behaviors
- Create service decomposition strategy for the 3,113-line service
- Document all API contracts and preservation guarantees
- Create comprehensive validation report
- Complete handoff checklist for next session

BASELINE PRESERVATION:
- START by extracting baseline version: git show baseline:backend/app/services/picklist_generator_service.py
- Document baseline characteristics before any changes
- Decompose into 6-8 focused services per plan
- Preserve ALL picklist generation functionality exactly (validate against baseline)
- Maintain GPT integration and batch processing behavior identical to baseline
- Zero breaking changes to dependent services (frontend components)
- Create comprehensive integration tests
- Continuously compare against baseline during refactoring

TARGET DECOMPOSITION:
- GPTAnalysisService (GPT integration & prompts)
- BatchProcessingService (batch management & progress)
- TeamAnalysisService (team evaluation algorithms)
- PriorityCalculationService (scoring & ranking logic)
- DataAggregationService (data collection & preparation)
- PerformanceOptimizationService (caching & optimization)
- Integrate existing MetricsExtractionService
- Reuse existing RetryService from sheets refactor
```

**Step 3: Intensive Backend Testing**
When complete (this may take 2-3 hours, or may require multiple sessions due to complexity):
1. Test ALL picklist generation workflows:
   - Standard generation
   - Batch processing mode
   - Different priority configurations
   - Various team count scenarios
2. Verify GPT analysis features work identically
3. Check all data export functions
4. Test error scenarios and recovery
5. Compare performance with your baseline notes

**Step 4: Critical Performance Check**
- Generation times should be same or better
- Memory usage should not increase significantly
- All API responses should be identical
- No new error messages or warnings

**Step 5: Report**
- If IDENTICAL behavior: "Sprint 8 testing complete. Picklist generation working perfectly, performance maintained."
- If ANY issues: "CRITICAL ISSUE in picklist generation: [describe exactly what's wrong]"

### **If Claude Code Reaches Context Window:**

⚠️ **IMPORTANT**: Claude Code automatically continues to next context window. You do NOT need to start a new session manually.

**What You'll See:**
Claude Code will say something like: "Approaching context limits. Creating handoff documentation..." then automatically continue.

**What To Do:**
1. **Let it work** - It will automatically transition and continue
2. **Watch for checkpoint commits** - It should save state before transitioning  
3. **Don't interrupt** - The automatic transition will handle continuity
4. **Only test after** it says "Sprint 8 Complete" (may be multiple transitions)

**If Something Goes Wrong During Transition:**
Only if you see errors or Claude Code seems confused after transition:
```
EMERGENCY: Context transition issue detected.
Please read sprint-context/NEXT_SESSION_START_HERE.md and sprint-context/sprint-8-session-intent.md to recover proper context.
Resume Sprint 8 from documented checkpoint state.
```

### Phase 3 Testing Focus

**Additional Testing for Phase 3:**
- [ ] Google Sheets authentication works
- [ ] Data import/export unchanged
- [ ] **Picklist generation identical behavior (CRITICAL for Sprint 8)**
- [ ] **Batch processing works exactly as before (CRITICAL for Sprint 8)**
- [ ] **GPT analysis features unchanged (CRITICAL for Sprint 8)**
- [ ] Team comparison integration preserved
- [ ] All workflows connect properly
- [ ] **Performance same or better (especially picklist generation)**
- [ ] No visual regressions anywhere

### Sprint 8 Specific Testing Checklist

**Core Picklist Generation:**
- [ ] Can create picklist with different priority settings
- [ ] Batch processing mode works (if you use it)
- [ ] GPT analysis generates same quality insights
- [ ] Team ranking algorithms produce identical results
- [ ] Export functions work for all formats
- [ ] Error handling shows same messages
- [ ] Progress tracking displays correctly
- [ ] Performance within 5% of original timing

**Integration Testing:**
- [ ] Frontend PicklistGenerator component unaffected
- [ ] Team Comparison modal still works with generated data
- [ ] Data persistence and caching unchanged
- [ ] All dependent features continue working

### Sprint 9 - Final Orchestrator Implementation (COMPLETION)

**CRITICAL**: This sprint completes the transformation - the final integration step!

**Step 1: Verify Sprint 8 Foundation**
Before starting Sprint 9, verify Sprint 8 was successful:
1. All 6 services should be created in backend/app/services/
2. Integration tests should be passing
3. All picklist functionality still working
4. Sprint 8 validation report should show success

**Step 2: Complete the Transformation**
After Sprint 8 creates all decomposed services, paste exactly:
```
Execute Sprint 9: Main Orchestrator Implementation.
Follow Refactor Documents/SPRINT_9_SESSION_INTENT.md for complete requirements.
Target: Complete the architectural transformation by refactoring picklist_generator_service.py from 3,113-line monolith to lightweight orchestrator.

CRITICAL REQUIREMENTS:
- Read sprint-context/sprint-8-validation-report.md for foundation status
- Read Refactor Documents/SPRINT_9_IMPLEMENTATION_PLAN.md for detailed approach
- Transform main service into ~200-line orchestrator that coordinates 6 services
- Preserve ALL 5 public method signatures exactly
- Maintain 100% API compatibility with baseline
- Coordinate: DataAggregationService, TeamAnalysisService, PriorityCalculationService, BatchProcessingService, PerformanceOptimizationService, PicklistGPTService
- Zero breaking changes to frontend or dependent services
- Performance within 5% of baseline metrics
- Comprehensive validation against baseline behavior

IMPLEMENTATION PHASES:
1. Service Infrastructure Setup (30 min)
2. Core Method Orchestration (90 min)  
3. Integration and Validation (60 min)
4. Final Validation and Documentation (30 min)

VALIDATION REQUIREMENTS:
- All 5 public methods return identical results to baseline
- Response formats exactly match baseline service
- Error handling produces identical error responses
- Performance within 5% tolerance
- All integration tests pass
- Frontend components work unchanged

This completes the most significant architectural transformation in the project's history.
```

**Step 3: FINAL COMPREHENSIVE Testing (THE MOST IMPORTANT)**
🎯 **THIS IS THE ULTIMATE TEST** - Everything must work perfectly after the complete transformation:

**Core Functionality Validation:**
1. **Test ALL picklist generation workflows thoroughly:**
   - Different priority configurations  
   - Various team count scenarios
   - Batch processing mode (if you use it)
   - All export formats and options
2. **Test team comparison and analysis features**
3. **Test data loading and Google Sheets integration**
4. **Test GPT integration and AI analysis quality**
5. **Test error handling and edge cases**
6. **Test performance - should be same or better than original**

**Visual Validation:**
7. **Compare with your original baseline screenshots from Day 1:**
   - Every interface should look identical
   - No new buttons, colors, or layout changes
   - All animations and transitions same
   - Loading indicators and progress bars unchanged

**Performance Validation:**
8. **Time the major operations:**
   - Picklist generation speed
   - Data loading times
   - GPT analysis duration
   - Export operation speed
   - Should match or beat your Day 1 baseline

**Integration Validation:**
9. **Test complete end-to-end workflows:**
   - Load data → Generate picklist → Compare teams → Export results
   - Try multiple priority configurations
   - Test with different team datasets
   - Verify all dependent features work

**Step 4: Success Verification**
If all tests pass perfectly:
✅ **TRANSFORMATION COMPLETE!**
- The 3,113-line monolith has been successfully transformed into 6+ focused services
- Original service is now a lightweight orchestrator (~200 lines)
- Architecture is dramatically more maintainable and scalable  
- Zero breaking changes achieved
- Performance maintained or improved
- Code quality exponentially improved
- Project ready for confident future development

**Step 5: Final Report**
If everything works perfectly:
```
SPRINT 9 COMPLETE - ARCHITECTURAL TRANSFORMATION SUCCESSFUL
All functionality working identically to Day 1 baseline.
Performance same or better than original.
No visual changes detected.
3,113-line monolith successfully transformed to modular architecture.
Ready for future development with dramatically improved maintainability.
```

If any issues detected:
```
FINAL INTEGRATION ISSUE DETECTED in Sprint 9:
Issue: [describe exactly what's wrong]
Expected: [what should happen based on Day 1 baseline]
Actual: [what's happening instead]
Feature affected: [which part of the system]
Severity: [Critical/Major/Minor]
```

## SUCCESS CRITERIA

✅ **Complete Success Achieved When:**
1. All website functionality works exactly as it did on Day 1
2. No visual changes detected anywhere
3. Performance is same or better than Day 1 baseline
4. All error conditions handled properly
5. Code architecture dramatically improved (3,113-line monolith → 6+ focused services + orchestrator)
6. Zero breaking changes to any integrations
7. Sprint 9 final validation report shows 100% success

This transformation represents the largest technical improvement in the project's history while maintaining perfect functionality!

- Website works exactly as before
- No visual changes at all
- Maybe slightly faster
- Code is cleaner (you won't see this)
- Easy to add features later

## Remember

1. **You're the quality gatekeeper** - Your testing prevents problems
2. **Visual changes = failure** - Even tiny differences matter
3. **When in doubt, report it** - Better safe than sorry
4. **Rollback is always safe** - We can always go back
5. **This is iterative** - Learn and improve each time

## Quick Reference Card

```
Start Sprint: Copy → Paste prompt → Wait → Test
Find Problem: Screenshot → Describe → Paste to Claude
Emergency: Paste "EMERGENCY" prompt → Wait → Verify fixed
Continue: Test passed → Paste next sprint prompt
Stop: Problems found → Document → Plan next steps
```

Good luck! Remember, you're just pasting prompts and testing. Claude Code does all the technical work.