#!/bin/bash
# Emergency Rollback Script
# WSL-compatible script to quickly restore system to baseline state

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory (works in both Windows and WSL)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}=== FRC Scouting App Emergency Rollback ===${NC}"
echo "Project root: $PROJECT_ROOT"

# Parse arguments
DRY_RUN=false
PRESERVE_LOGS=true
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
            shift
            ;;
        --no-preserve-logs)
            PRESERVE_LOGS=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--no-preserve-logs] [--force]"
            exit 1
            ;;
    esac
done

# Function to execute or print commands based on dry run mode
execute_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} $1"
    else
        echo -e "${GREEN}[EXECUTE]${NC} $1"
        eval "$1"
    fi
}

# Confirmation prompt (unless forced)
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    echo -e "${RED}WARNING: This will rollback all changes to the baseline state!${NC}"
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r confirmation
    if [ "$confirmation" != "yes" ]; then
        echo "Rollback cancelled."
        exit 0
    fi
fi

cd "$PROJECT_ROOT"

# Step 1: Save current state for diagnostics
if [ "$PRESERVE_LOGS" = true ]; then
    BACKUP_DIR="rollback_diagnostics_$(date +%Y%m%d_%H%M%S)"
    execute_cmd "mkdir -p \"$BACKUP_DIR\""
    
    echo -e "\n${YELLOW}Preserving diagnostic information...${NC}"
    execute_cmd "git status > \"$BACKUP_DIR/git_status.txt\" 2>&1 || true"
    execute_cmd "git diff > \"$BACKUP_DIR/git_diff.txt\" 2>&1 || true"
    execute_cmd "git log --oneline -10 > \"$BACKUP_DIR/git_log.txt\" 2>&1 || true"
    
    # Save any error logs
    if [ -d "backend/logs" ]; then
        execute_cmd "cp -r backend/logs \"$BACKUP_DIR/backend_logs\" 2>/dev/null || true"
    fi
fi

# Step 2: Stop any running services
echo -e "\n${YELLOW}Stopping services...${NC}"

# Check if backend is running
if command -v lsof >/dev/null 2>&1; then
    BACKEND_PID=$(lsof -ti:8000 2>/dev/null || true)
    if [ ! -z "$BACKEND_PID" ]; then
        execute_cmd "kill $BACKEND_PID"
        echo "Backend service stopped (PID: $BACKEND_PID)"
    fi
else
    # Windows alternative using netstat
    if netstat -an | grep -q ":8000.*LISTENING"; then
        echo -e "${YELLOW}Backend service appears to be running on port 8000${NC}"
        echo "Please stop it manually before continuing"
        if [ "$FORCE" = false ]; then
            exit 1
        fi
    fi
fi

# Check if frontend is running
if command -v lsof >/dev/null 2>&1; then
    FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || true)
    if [ ! -z "$FRONTEND_PID" ]; then
        execute_cmd "kill $FRONTEND_PID"
        echo "Frontend service stopped (PID: $FRONTEND_PID)"
    fi
else
    # Windows alternative
    if netstat -an | grep -q ":3000.*LISTENING"; then
        echo -e "${YELLOW}Frontend service appears to be running on port 3000${NC}"
        echo "Please stop it manually before continuing"
        if [ "$FORCE" = false ]; then
            exit 1
        fi
    fi
fi

# Step 3: Git rollback
echo -e "\n${YELLOW}Rolling back git changes...${NC}"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Stash any uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "Uncommitted changes detected, stashing..."
    execute_cmd "git stash push -m \"Emergency rollback stash $(date +%Y%m%d_%H%M%S)\""
fi

# Switch to baseline branch
if [ "$CURRENT_BRANCH" != "baseline" ]; then
    execute_cmd "git checkout baseline"
fi

# Verify we're on the correct commit
BASELINE_COMMIT=$(git rev-parse HEAD)
echo "Baseline commit: $BASELINE_COMMIT"

# Step 4: Clean build artifacts
echo -e "\n${YELLOW}Cleaning build artifacts...${NC}"

# Backend cleanup
if [ -d "backend/__pycache__" ]; then
    execute_cmd "find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"
fi

if [ -d "backend/.pytest_cache" ]; then
    execute_cmd "rm -rf backend/.pytest_cache"
fi

# Frontend cleanup
if [ -d "frontend/node_modules" ]; then
    echo "Cleaning frontend dependencies..."
    execute_cmd "rm -rf frontend/node_modules"
fi

if [ -d "frontend/build" ] || [ -d "frontend/dist" ]; then
    execute_cmd "rm -rf frontend/build frontend/dist"
fi

# Step 5: Restore dependencies
echo -e "\n${YELLOW}Restoring dependencies...${NC}"

# Backend dependencies
if [ -f "backend/requirements.txt" ]; then
    echo "Reinstalling backend dependencies..."
    if [ "$DRY_RUN" = false ]; then
        cd backend
        python -m pip install -r requirements.txt --quiet
        cd ..
    else
        echo -e "${YELLOW}[DRY RUN]${NC} Would install backend dependencies"
    fi
fi

# Frontend dependencies
if [ -f "frontend/package.json" ]; then
    echo "Reinstalling frontend dependencies..."
    if [ "$DRY_RUN" = false ]; then
        cd frontend
        npm install --silent
        cd ..
    else
        echo -e "${YELLOW}[DRY RUN]${NC} Would install frontend dependencies"
    fi
fi

# Step 6: Verify rollback
echo -e "\n${YELLOW}Verifying rollback...${NC}"

# Check git status
if [ "$DRY_RUN" = false ]; then
    git status --short
    
    # Run basic health checks
    echo -e "\n${GREEN}Rollback complete!${NC}"
    echo "System has been restored to baseline state."
    echo ""
    echo "Next steps:"
    echo "1. Start backend: cd backend && uvicorn app.main:app --reload"
    echo "2. Start frontend: cd frontend && npm start"
    echo "3. Verify application works correctly"
    
    if [ "$PRESERVE_LOGS" = true ]; then
        echo ""
        echo "Diagnostic information saved in: $BACKUP_DIR"
    fi
else
    echo -e "\n${YELLOW}Dry run complete. No changes were made.${NC}"
fi

# Step 7: Create rollback report
if [ "$DRY_RUN" = false ] && [ "$PRESERVE_LOGS" = true ]; then
    REPORT_FILE="$BACKUP_DIR/rollback_report.txt"
    {
        echo "Emergency Rollback Report"
        echo "========================"
        echo "Date: $(date)"
        echo "Baseline Commit: $BASELINE_COMMIT"
        echo "Previous Branch: $CURRENT_BRANCH"
        echo "Rollback Type: Emergency"
        echo ""
        echo "Actions Taken:"
        echo "- Git rolled back to baseline"
        echo "- Build artifacts cleaned"
        echo "- Dependencies restored"
        echo ""
        echo "Diagnostics preserved in this directory"
    } > "$REPORT_FILE"
    
    echo -e "\nRollback report saved: $REPORT_FILE"
fi

exit 0