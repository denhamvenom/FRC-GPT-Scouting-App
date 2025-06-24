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
Paste:
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

### After Emergency
1. Claude Code will restore the original
2. Test website works again
3. Take a break before retrying

## Testing Checklist

### For Every Sprint
- [ ] Website still loads
- [ ] All pages accessible
- [ ] No visual changes
- [ ] All features work
- [ ] No error messages
- [ ] Same speed/performance

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

## Phase 3: Expansion (Only If Phase 2 Perfect)

If Team Comparison refactoring went perfectly, we can carefully expand:

### Sprints 6-8
Similar process but for different features:
- Sprint 6: Another backend service
- Sprint 7: Another frontend component  
- Sprint 8: Final validation

Use same testing approach for each.

## Success Looks Like

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