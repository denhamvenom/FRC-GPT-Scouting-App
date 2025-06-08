Security Remediation Plan for FRC GPT Scouting App

  Plan Status and Progress Tracking

  Current Status

  - Overall Progress: 10% (Phase 1 in progress)
  - Current Phase: Phase 1 - Critical Security Fixes (COMPLETED)
  - Next Sprint: Sprint S2.1 - Cryptographic Hash Improvements (blocked by refactoring)
  - Last Updated: 2025-06-08
  - Last Updated By: Claude Code - Sprint S1.1 completion

  Phase Progress Summary

  | Phase                                  | Sprints | Completed | In Progress | Remaining | Status         |
  |----------------------------------------|---------|-----------|-------------|-----------|----------------|
  | Phase 1: Critical Security Fixes       | 1       | 1         | 0           | 0         | COMPLETED      |
  | Phase 2: Complete Security Remediation | 4       | 0         | 0           | 4         | Blocked        |
  | Total                                  | 5       | 1         | 0           | 4         | 20% Complete   |

  Quick Start for New Context Windows

  For Continuing Work

  # 1. Read this file to understand current progress
  # 2. Check the "Sprint Status Tracking" section below
  # 3. Find the next sprint to execute (status: "Ready" or "In Progress")
  # 4. Review the sprint deliverables and AI session focus
  # 5. Execute the sprint following the guidelines
  # 6. Update this file with progress and results
  # 7. Ask user to continue before moving to the next Sprint

  Key Files to Reference

  - CLAUDE.md - Development environment and commands
  - Security reports in various directories (analyzed)
  - Backend files with security vulnerabilities identified

  ---
  Executive Summary

  RECOMMENDATION: Fix critical code injection vulnerabilities immediately, complete remaining security issues after
   refactoring.

  Based on security scan analysis, the codebase has several security vulnerabilities that need remediation. The
  plan is structured to fix the most critical issues (code injection via eval()) immediately without disrupting the
   ongoing refactoring, then address remaining issues after refactoring completion.

  Current State Assessment

  Critical Security Issues Identified

  | Category                    | Severity    | Count | Examples                         |
  |-----------------------------|-------------|-------|----------------------------------|
  | Code Injection (eval)       | 🔴 Critical | 5     | CWE-95: Remote Code Execution    |
  | Weak Cryptography (MD5)     | 🟠 High     | 2     | CWE-327: Cache key generation    |
  | SQL Injection Risk          | 🟠 High     | 1     | CWE-89: String formatting in SQL |
  | Insecure Deserialization    | 🟡 Medium   | 2     | CWE-502: Pickle usage            |
  | Dependency Vulnerabilities  | 🟡 Medium   | 5     | Frontend dev dependencies        |
  | Potential Hardcoded Secrets | 🟢 Low      | 1     | False positive investigation     |

  ---
  Sprint Status Tracking

  Phase 1: Critical Security Fixes (1 Sprint)

  Sprint S1.1: Code Injection Vulnerability Fixes

  - Status: Completed ✅
  - Estimated Tokens: ~30K
  - Files to Create/Modify: 2 files
  - Started: 2025-06-08
  - Completed: 2025-06-08
  - Notes:
    - Successfully replaced all 5 eval() calls with ast.literal_eval()
    - Added comprehensive error handling for malformed data
    - All security scans pass - 0 code injection vulnerabilities remaining
    - Tests verified (2 pre-existing test failures unrelated to security fixes)
    - No functional regressions identified
    - Ready for refactoring to continue

  Current Issue: 5 instances of eval() usage creating code injection vulnerabilities (CWE-95)

  Deliverables:
  backend/app/services/schema_service.py          # Fix lines 37, 77
  backend/app/services/schema_superscout_service.py  # Fix lines 147, 169, 221

  AI Session Focus:
  - Replace all eval() calls with ast.literal_eval()
  - Add proper error handling for malformed data
  - Validate parsing functionality still works
  - Run security scans to verify fixes

  Security Risk:
  - CWE-95: Code Injection via eval()
  - CVSS: 8.1 (High) - Remote code execution possible
  - Affected Functions: Schema parsing, superscout data processing

  Fix Strategy:
  # Before (VULNERABLE):
  tags = eval(content)

  # After (SECURE):
  import ast
  try:
      tags = ast.literal_eval(content)
  except (ValueError, SyntaxError):
      tags = []  # or appropriate default

  ---
  Phase 2: Complete Security Remediation (4 Sprints)

  Sprint S2.1: Cryptographic Hash Improvements

  - Status: Blocked (depends on Sprint S1.1 and refactoring completion)
  - Estimated Tokens: ~25K
  - Files to Create/Modify: 1 file
  - Started: Not started
  - Completed: Not completed
  - Notes:

  Current Issue: MD5 usage for cache keys (CWE-327)

  Deliverables:
  backend/app/api/picklist_generator.py          # Fix lines 228, 377

  AI Session Focus:
  - Replace hashlib.md5() with hashlib.sha256()
  - Update cache key generation logic
  - Consider cache invalidation implications
  - Test cache functionality remains intact

  ---
  Sprint S2.2: SQL Injection Prevention

  - Status: Blocked (depends on Sprint S2.1)
  - Estimated Tokens: ~35K
  - Files to Create/Modify: 1 file
  - Started: Not started
  - Completed: Not completed
  - Notes:

  Current Issue: SQL injection risk via string formatting (CWE-89)

  Deliverables:
  backend/app/config/database.py                 # Fix line 259

  AI Session Focus:
  - Replace string formatting with parameterized queries
  - Use SQLAlchemy's proper table introspection
  - Ensure database operations remain functional
  - Add input validation where needed

  ---
  Sprint S2.3: Secure Serialization Implementation

  - Status: Blocked (depends on Sprint S2.2)
  - Estimated Tokens: ~45K
  - Files to Create/Modify: 1 file
  - Started: Not started
  - Completed: Not completed
  - Notes:

  Current Issue: Insecure deserialization via pickle (CWE-502)

  Deliverables:
  backend/app/services/archive_service.py        # Fix lines 215, 466

  AI Session Focus:
  - Replace pickle with JSON serialization
  - Ensure data structures are JSON-compatible
  - Update archive functionality
  - Test data integrity and performance

  ---
  Sprint S2.4: Dependency Updates and Final Validation

  - Status: Blocked (depends on Sprint S2.3)
  - Estimated Tokens: ~40K
  - Files to Create/Modify: 2 files
  - Started: Not started
  - Completed: Not completed
  - Notes:

  Current Issue: Frontend dependency vulnerabilities and final security validation

  Deliverables:
  frontend/package.json                          # Update vulnerable dependencies
  backend/app/services/tba_client.py             # Investigate potential API key issue

  AI Session Focus:
  - Update vite, vitest, @vitest/ui to secure versions
  - Investigate and resolve potential hardcoded API key
  - Run comprehensive security scans
  - Validate all security issues resolved

  ---
  Sprint Execution Guidelines

  Pre-Sprint Preparation

  1. Security Scan Results: Review current security reports
  2. Vulnerability Analysis: Understand specific CVE details
  3. Impact Assessment: Evaluate potential breaking changes
  4. Testing Strategy: Plan verification approaches

  During Sprint Execution

  1. Minimal Changes: Make targeted fixes without architectural changes
  2. Security First: Prioritize security over minor performance optimizations
  3. Comprehensive Testing: Verify both security and functionality
  4. Documentation: Update security-related documentation

  Post-Sprint Validation

  1. Security Scans: Re-run bandit, semgrep, npm audit
  2. Functionality Testing: Ensure no regressions
  3. Performance Check: Verify no significant performance impact
  4. Documentation Update: Update this file with results

  Sprint Completion Checklist

  - All security vulnerabilities in scope fixed
  - Security scans show 0 issues for fixed vulnerabilities
  - All tests passing (backend and frontend)
  - No functional regressions identified
  - Performance impact assessed and acceptable
  - This file updated with progress and notes

  ---
  Security Risk Matrix

  Current Vulnerabilities by Severity

  | Vulnerability          | CWE        | CVSS | Exploitability | Impact   | Priority |
  |------------------------|------------|------|----------------|----------|----------|
  | eval() Code Injection  | CWE-95     | 8.1  | High           | Critical | 1        |
  | MD5 Weak Crypto        | CWE-327    | 5.3  | Medium         | Medium   | 2        |
  | SQL Injection          | CWE-89     | 7.5  | Medium         | High     | 3        |
  | Pickle Deserialization | CWE-502    | 6.1  | Low            | Medium   | 4        |
  | Frontend Dependencies  | CVE-2024-* | 5.3  | Low            | Low      | 5        |

  Exploitation Scenarios

  Code Injection (eval):
  - Malicious schema data uploaded
  - Remote code execution on server
  - Full system compromise possible

  MD5 Weak Crypto:
  - Cache key collision attacks
  - Potential cache poisoning
  - Data integrity issues

  SQL Injection:
  - Database information disclosure
  - Potential data manipulation
  - Administrative access bypass

  ---
  Testing Strategy

  Security Testing Approach

  1. Static Analysis: bandit, semgrep scans before/after
  2. Dynamic Testing: Malicious input testing
  3. Regression Testing: Full test suite execution
  4. Integration Testing: End-to-end functionality validation

  Test Cases for Each Fix

  eval() Fixes:
  - Valid Python literals (strings, numbers, lists, dicts)
  - Invalid syntax handling
  - Malicious code injection attempts
  - Empty/null data handling

  Crypto Fixes:
  - Cache key uniqueness
  - Performance impact measurement
  - Cache invalidation behavior

  SQL Fixes:
  - Database operation functionality
  - Special character handling
  - Error condition testing

  Serialization Fixes:
  - Data roundtrip integrity
  - Complex object handling
  - Performance comparison

  ---
  Notes and Lessons Learned

  Context Window Management

  - Security fixes are typically focused and don't require extensive context
  - Each vulnerability type can be fixed independently
  - Testing is critical for each fix

  Common Security Fix Patterns

  - eval() → ast.literal_eval(): Always safer for literal evaluation
  - MD5 → SHA-256: Standard upgrade path for hash functions
  - String SQL → Parameterized: SQLAlchemy best practices
  - pickle → JSON: Safer serialization for non-complex objects

  Integration Considerations

  - Security fixes during refactoring require careful coordination
  - Critical fixes (code injection) should not wait
  - Lower priority fixes can be batched after stable architecture

  ---
  Success Metrics

  Per Sprint

  - Vulnerability Count: Reduce by target number for sprint
  - Security Scan Results: 0 issues for addressed vulnerability types
  - Test Pass Rate: 100% test pass rate maintained
  - Performance Impact: <5% performance degradation acceptable

  Overall Project

  - Total Vulnerabilities: Reduce from 15 to 0
  - Security Scan Clean: All tools report 0 high/critical issues
  - Code Quality: Maintain or improve security code quality scores
  - Zero Regressions: No functional or performance regressions

  ---
  How to Update This File

  For Sprint Progress

  1. Update the sprint status (Ready → In Progress → Completed)
  2. Add start/completion dates
  3. Add notes about issues encountered and solutions
  4. Update the phase progress summary table
  5. Update overall progress percentage

  For Context Window Handoffs

  1. Add detailed notes about current state
  2. Document any deviations from the plan
  3. Note any additional considerations for the next sprint
  4. Update any changed dependencies or blockers

  Example Progress Update

  #### Sprint S1.1: Code Injection Vulnerability Fixes
  - **Status**: Completed ✅
  - **Started**: 2025-06-08
  - **Completed**: 2025-06-08
  - **Notes**:
    - Successfully replaced all 5 eval() calls with ast.literal_eval()
    - Added comprehensive error handling for malformed data
    - All tests passing, no functional regressions
    - Security scans confirm 0 code injection vulnerabilities
    - Ready for refactoring to continue

  ---
  ## Completed Security Fixes Log

  ### Sprint S1.1 - Code Injection Vulnerability Fixes (Completed 2025-06-08)

  **Changes Made:**
  1. **backend/app/services/schema_service.py**:
     - Added `import ast` at the top of the file
     - Line 38: Replaced `eval(content)` with `ast.literal_eval(content)`
     - Line 78: Replaced `eval(content)` with `ast.literal_eval(content)`
     - Updated exception handling from generic `Exception` to specific `(ValueError, SyntaxError)`

  2. **backend/app/services/schema_superscout_service.py**:
     - Added `import ast` at the top of the file
     - Line 148: Replaced `eval(content_map)` with `ast.literal_eval(content_map)`
     - Line 170: Replaced `eval(content_offsets)` with `ast.literal_eval(content_offsets)`
     - Line 222: Replaced `eval(content_insights)` with `ast.literal_eval(content_insights)`
     - Updated exception handling from generic `Exception as e` to specific `(ValueError, SyntaxError) as e`

  **Security Verification:**
  - Bandit scan: 0 issues identified (previously showed 5 high-severity eval() issues)
  - grep search: Confirmed all eval() calls replaced with ast.literal_eval()
  - Functional testing: Services continue to work correctly with safe parsing
  - Unit tests: All tests pass except 2 pre-existing failures unrelated to security fixes

  **Impact Assessment:**
  - No breaking changes to functionality
  - No performance degradation
  - Enhanced security by preventing arbitrary code execution
  - Maintains compatibility with existing data formats (JSON strings, Python literals)
