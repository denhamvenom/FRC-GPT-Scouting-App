# Claude Code Prompt Guide and Templates

## Document Version
- **Version**: 2.0 (Claude Code Optimized)
- **Date**: 2025-06-22
- **Purpose**: Standardized prompts for Claude Code refactoring execution

## Overview

This guide provides Claude Code-specific templates and best practices for executing the FRC Scouting App refactoring. All templates are designed for Claude Code's CLI interface and tool capabilities, ensuring consistent, safe, and high-quality results.

## Claude Code Principles

### 1. Tool-First Approach
- Use Read tool before any edits
- Use Bash tool for verification
- Use Glob/Grep for discovery
- Use Edit/MultiEdit for changes

### 2. Built-in Safety
- Claude Code runs in working directory
- Git operations are safe by default
- File operations are atomic
- Rollback is always possible

### 3. Session Continuity
- Each session is independent
- Context must be re-established via CONTEXT_WINDOW_PROTOCOL.md
- Baseline reference mandatory at session start
- Session intent documents for context preservation
- File states verified via checksums
- TodoWrite/TodoRead for progress tracking

## Master Claude Code Sprint Template

**Use this exact message to start any sprint with Claude Code:**

```markdown
You are Claude Code executing Sprint <<SPRINT-NUMBER>> of the FRC GPT Scouting App refactoring.

## Repository Context
- **Path**: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App
- **Baseline**: baseline (immutable reference branch)
- **Target**: refactor/sprint-<<SPRINT-NUMBER>>

## Sprint Objective
<<SPECIFIC-OBJECTIVE>>

## Success Criteria
- [ ] <<CRITERIA-1>>
- [ ] <<CRITERIA-2>>  
- [ ] <<CRITERIA-3>>

## CRITICAL REQUIREMENTS
Follow CONTEXT_WINDOW_PROTOCOL.md for:
- Baseline reference before all changes
- Session intent document creation
- Decision documentation for next context window
- Continuous validation against baseline behavior

## Pre-Execution Checklist
MANDATORY: Complete these checks before ANY file modifications:

1. **Verify Location & Status**
   ```bash
   pwd  # Confirm repository path
   git status  # Should be clean
   git branch --show-current  # Should be 'baseline'
   ls -la  # Verify ARCHITECTURE.md, backend/, frontend/ exist
   ```

2. **Create Sprint Branch**
   ```bash
   git checkout -b refactor/sprint-<<SPRINT-NUMBER>>
   ```

3. **Generate Starting Checksums**
   ```bash
   find backend -name "*.py" -exec sha1sum {} \; | sort > checksums/sprint-<<SPRINT-NUMBER>>-start.txt
   echo "Generated checksums for $(wc -l < checksums/sprint-<<SPRINT-NUMBER>>-start.txt) files"
   ```

4. **Verify System Health**
   ```bash
   cd backend && python -c "from app.main import app; print('✅ Baseline working')"
   ```

## Execution Protocol
1. Use Read tool to understand current code
2. Use TodoWrite to track progress  
3. Make incremental changes with Edit/MultiEdit
4. Use Bash to verify after each change
5. Update TodoWrite with completion status

## Modified File Requirements
Every modified function MUST include this docstring:

```python
"""
Purpose: [What this does]
Inputs: [Parameter types]
Outputs: [Return type]
Side-Effects: [Any side effects]
Dependencies: [Required modules/services]

Claude-Context:
- Sprint: <<SPRINT-NUMBER>>
- Modification: [Why changed]
- Complexity: [Simple|Medium|Complex]
- Test-Status: [Coverage achieved]

Example:
    >>> # Usage example if non-trivial

Modified: Sprint-<<SPRINT-NUMBER>> | $(date +%Y-%m-%d)
"""
```

## Continuous Verification
After each file modification:

```bash
# Syntax check
python -m py_compile [FILE]

# Import check  
cd backend && python -c "from app.main import app; print('✅ Still imports')"

# Run relevant tests
python -m pytest tests/[RELATED] -v
```

## Sprint Completion
When objectives met:

```bash
# Final verification
cd backend && python -m pytest --tb=short

# Generate ending checksums
find backend -name "*.py" -exec sha1sum {} \; | sort > checksums/sprint-<<SPRINT-NUMBER>>-end.txt

# Commit changes
git add .
git commit -m "feat(sprint-<<SPRINT-NUMBER>>): [DESCRIPTION]"
```

## Emergency Protocols
If ANYTHING breaks:
1. STOP immediately
2. Run: `git checkout baseline`
3. Verify: `cd backend && python -c "from app.main import app"`
4. Document issue in rollbacks/ directory

Begin sprint execution now.
```

## Claude Code Specific Sprint Templates

### Sprint 1: Test Framework Setup

**Claude Code Message:**
```
Execute Sprint 1: Test Framework Setup for FRC GPT Scouting App.

Repository: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App

## Objectives
1. Create pytest.ini configuration
2. Set up conftest.py with fixtures  
3. Generate test scaffolds for existing API endpoints
4. Achieve 50% test coverage minimum

## Tools to Use
- Read: Examine existing API endpoints in backend/app/api/
- Glob: Find all .py files needing tests
- Write: Create pytest.ini, conftest.py
- MultiEdit: Create multiple test files
- Bash: Run pytest and verify coverage

## Success Criteria
- pytest runs without errors
- Coverage report shows >50%
- All API endpoints have basic tests
- Test structure follows best practices

## Execution Steps
1. Use Read to examine backend/app/api/*.py files
2. Use Glob to find all API endpoints: "backend/app/api/*.py"
3. Create pytest.ini with appropriate settings
4. Create conftest.py with fixtures
5. Use MultiEdit to create test files for each API module
6. Use Bash to run: pytest --cov=backend/app --cov-report=term

Begin execution now.
```

### Sprint 3: Domain Model Extraction

**Claude Code Message:**
```
Execute Sprint 3: Domain Model Extraction for FRC GPT Scouting App.

Repository: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App

## Objectives
1. Extract Team, Match, Picklist domain models from services
2. Create backend/src/domain/models/ directory structure
3. Add Pydantic validation to all models
4. Create comprehensive unit tests for models

## Target Files to Analyze
Use Read tool to examine:
- backend/app/services/picklist_generator_service.py
- backend/app/services/team_comparison_service.py  
- backend/app/services/unified_event_data_service.py

## Tools to Use
- Read: Analyze existing service files for data structures
- Glob: Find all service files that use data models
- Write: Create new model files
- MultiEdit: Update services to use new models
- Bash: Run tests and verify imports

## Execution Steps
1. Use Read to identify data structures in service files
2. Create domain model classes with Pydantic
3. Create tests for each model
4. Update services to import and use new models
5. Verify all imports and tests pass

Begin execution now.
```

### Sprint 5: Service Decomposition

**Claude Code Message:**
```
Execute Sprint 5: Picklist Service Decomposition for FRC GPT Scouting App.

Repository: /mnt/c/Users/deila/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App

## Objective
Decompose the monolithic picklist_generator_service.py into smaller, focused services.

## Current Analysis Required
Use Read tool to examine backend/app/services/picklist_generator_service.py:
- Identify distinct responsibilities 
- Map method dependencies
- Find natural separation points

## Target Structure
Create these new files:
- backend/src/application/services/picklist_service.py (API orchestration)
- backend/src/application/services/ranking_service.py (ranking logic)
- backend/src/domain/services/ranking_algorithms.py (pure functions)

## Tools to Use
- Read: Analyze current monolithic service
- MultiEdit: Create new service files while preserving logic
- Edit: Update import statements across codebase
- Bash: Verify functionality preserved with tests

## Success Criteria
- Original API endpoints work identically
- Each new service <200 lines
- All tests pass
- No performance degradation

Begin execution now.
```

## Claude Code Error Recovery Templates

### Import Error Recovery

**Claude Code Message:**
```
I encountered import errors after refactoring. Help me diagnose and fix.

## Error Details
[PASTE EXACT ERROR MESSAGE]

## Investigation Required
1. Use Bash to run: `cd backend && python -c "from app.main import app"`
2. Use Read to check modified files for syntax errors
3. Use Bash to run: `find backend -name "*.py" -exec python -m py_compile {} \;`

## Tools to Use
- Bash: Test imports and syntax
- Read: Examine files with import issues  
- Edit: Fix import statements
- Glob: Find all files importing the problematic module

## Recovery Steps
1. Identify the specific import causing issues
2. Check if file was moved or renamed
3. Update import statements across codebase
4. Verify syntax of all modified files
5. Test imports progressively

Fix imports now.
```

### Test Failure Recovery

**Claude Code Message:**
```
Tests are failing after my changes. Help me analyze and fix them.

## Current Test Status
Use Bash to run: `cd backend && python -m pytest --tb=short -v`

## Analysis Required
1. Use Bash to identify specific failing tests
2. Use Read to examine failing test files
3. Use Bash to run individual tests: `pytest tests/specific_test.py -v`
4. Use Bash to compare with baseline if needed

## Tools to Use
- Bash: Run tests and get detailed output
- Read: Examine test files and source code
- Edit: Fix failing tests or source code
- Bash: Verify fixes with re-run

## Recovery Approach
1. Fix one test at a time
2. Ensure each fix doesn't break other tests
3. Focus on maintaining existing functionality
4. Add missing mocks if needed

Begin test recovery now.
```

## Claude Code Best Practices

### Session Management

**Starting a New Session:**
1. Always use TodoRead to check progress
2. Use Bash to verify current branch and status
3. Use Read to understand current file states
4. Use TodoWrite to set session objectives

**During a Session:**
1. Use TodoWrite to update progress frequently
2. Use Bash to verify after each significant change
3. Use Read before any edits to understand context
4. Use Edit/MultiEdit for atomic changes

**Ending a Session:**
1. Use TodoWrite to document current state
2. Use Bash to commit changes with descriptive messages
3. Use Bash to generate checksums for next session
4. Document any blockers or next steps

### Tool Usage Patterns

**Discovery Phase:**
```bash
# Use these tools to understand the codebase
- Glob: "backend/app/services/*.py" (find service files)
- Grep: "class.*Service" (find service classes)  
- Read: [specific files identified]
- LS: /path/to/directory (understand structure)
```

**Implementation Phase:**
```bash
# Use these tools to make changes
- Read: [target file] (understand before changing)
- Edit or MultiEdit: [make specific changes]
- Bash: python -m py_compile [file] (verify syntax)
- Bash: cd backend && python -c "from app.main import app" (test imports)
```

**Verification Phase:**
```bash
# Use these tools to validate changes
- Bash: cd backend && python -m pytest (run tests)
- Bash: git status (check what changed)
- Bash: git diff (review changes)
- TodoWrite: [update progress]
```

### Emergency Recovery

**If Something Breaks:**
1. **STOP** - Don't make more changes
2. **Use Bash:** `git status` to see current state
3. **Use Bash:** `git checkout baseline` to return to safety
4. **Use Bash:** `cd backend && python -c "from app.main import app"` to verify baseline works
5. **Document the issue** for later analysis

### Context Preservation for Claude Code

**Every Sprint Should:**
1. Start with TodoWrite to set objectives
2. Use systematic tool progression: Read → Edit → Bash → TodoWrite
3. End with TodoWrite summary and Bash commit
4. Generate checksums for next session handoff

**File Modifications Must:**
1. Include comprehensive docstrings per template
2. Be verified with Bash syntax/import checks
3. Be tested with Bash pytest runs
4. Be committed with descriptive messages

### Success Patterns

**Effective Workflow:**
```
TodoRead → Bash(git status) → Read(target files) → 
TodoWrite(plan) → Edit(changes) → Bash(verify) → 
TodoWrite(progress) → Bash(test) → TodoWrite(complete) → 
Bash(commit)
```

**Sprint Completion Checklist:**
- [ ] All objectives in TodoWrite marked complete
- [ ] All tests passing via Bash pytest
- [ ] All imports working via Bash python checks
- [ ] All changes committed via Bash git
- [ ] Next sprint prerequisites documented

---

**Remember**: Claude Code's strength is systematic execution. Use the tools methodically, verify at each step, and maintain clear progress tracking with TodoWrite.