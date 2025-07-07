#!/bin/bash
# Comprehensive Safety Check Runner
# Runs all safety validations and generates report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}=== FRC Scouting App Safety Check Suite ===${NC}"
echo "Running comprehensive safety validations..."
echo ""

cd "$PROJECT_ROOT"

# Initialize results
CHECKS_PASSED=0
CHECKS_FAILED=0
RESULTS_FILE="safety/safety_check_results_$(date +%Y%m%d_%H%M%S).txt"

# Function to run a check and record result
run_check() {
    local check_name="$1"
    local check_command="$2"
    
    echo -e "${YELLOW}Running: ${check_name}${NC}"
    
    if eval "$check_command" > /tmp/check_output.txt 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        echo "[$check_name] PASSED" >> "$RESULTS_FILE"
    else
        echo -e "${RED}✗ FAILED${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
        echo "[$check_name] FAILED" >> "$RESULTS_FILE"
        echo "Error output:" >> "$RESULTS_FILE"
        cat /tmp/check_output.txt >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
    fi
    echo ""
}

# Create results file
mkdir -p safety
echo "Safety Check Results - $(date)" > "$RESULTS_FILE"
echo "================================" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# 1. Check if services are running
echo -e "${BLUE}1. Checking Services${NC}"
if lsof -ti:8000 >/dev/null 2>&1 || netstat -an | grep -q ":8000.*LISTENING"; then
    echo -e "${GREEN}✓ Backend service is running${NC}"
else
    echo -e "${YELLOW}⚠ Backend service not detected on port 8000${NC}"
    echo "Start with: cd backend && uvicorn app.main:app --reload"
fi

if lsof -ti:3000 >/dev/null 2>&1 || netstat -an | grep -q ":3000.*LISTENING"; then
    echo -e "${GREEN}✓ Frontend service is running${NC}"
else
    echo -e "${YELLOW}⚠ Frontend service not detected on port 3000${NC}"
    echo "Start with: cd frontend && npm start"
fi
echo ""

# 2. Baseline Metrics Check
run_check "Baseline Metrics Validation" "python safety/baseline_metrics.py --verify"

# 3. API Contract Tests
run_check "API Contract Validation" "python safety/api_contract_tests.py"

# 4. Data Integrity Check
run_check "Data Integrity Validation" "python safety/data_integrity_validator.py --validate"

# 5. Integration Tests
echo -e "${BLUE}5. Integration Tests${NC}"
if command -v pytest >/dev/null 2>&1; then
    run_check "End-to-End Workflows" "python tests/integration/end_to_end_workflows.py"
    run_check "Error Scenarios" "python tests/integration/error_scenario_tests.py"
else
    echo -e "${YELLOW}⚠ pytest not installed - skipping integration tests${NC}"
    echo "Install with: pip install pytest"
fi
echo ""

# 6. Progress Status
echo -e "${BLUE}6. Progress Status${NC}"
python safety/progress_tracker.py --check-criteria
echo ""

# Summary
echo -e "${BLUE}=== Safety Check Summary ===${NC}"
echo -e "Checks Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks Failed: ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All safety checks PASSED!${NC}"
    echo "Safe to proceed with refactoring."
    EXIT_CODE=0
else
    echo -e "${RED}❌ Safety checks FAILED!${NC}"
    echo "Please review failures before proceeding."
    echo "Detailed results saved to: $RESULTS_FILE"
    EXIT_CODE=1
fi

# Generate comprehensive report
echo ""
echo -e "${BLUE}Generating comprehensive safety report...${NC}"
REPORT_FILE="safety/safety_report_$(date +%Y%m%d_%H%M%S).md"

{
    echo "# Safety Check Report"
    echo ""
    echo "**Date**: $(date)"
    echo "**Status**: $([ $CHECKS_FAILED -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
    echo ""
    echo "## Summary"
    echo "- Checks Passed: $CHECKS_PASSED"
    echo "- Checks Failed: $CHECKS_FAILED"
    echo ""
    echo "## Detailed Results"
    cat "$RESULTS_FILE"
    echo ""
    echo "## Recommendations"
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo "All safety checks passed. Safe to proceed with next sprint."
    else
        echo "Safety violations detected. Please:"
        echo "1. Review the failed checks above"
        echo "2. Run rollback if necessary: ./safety/emergency_rollback.sh"
        echo "3. Fix issues before proceeding"
    fi
} > "$REPORT_FILE"

echo "Full report saved to: $REPORT_FILE"
echo ""

# Clean up
rm -f /tmp/check_output.txt

exit $EXIT_CODE