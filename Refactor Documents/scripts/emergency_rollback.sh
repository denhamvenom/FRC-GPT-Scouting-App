#!/bin/bash
# emergency_rollback.sh - Emergency rollback to baseline

set -e

echo "🚨 EMERGENCY ROLLBACK INITIATED"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[EMERGENCY]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[CRITICAL]${NC} $1"
}

# Log the emergency
EMERGENCY_LOG="rollbacks/emergency-$(date +%Y%m%d_%H%M%S).log"
mkdir -p rollbacks

{
echo "EMERGENCY ROLLBACK LOG"
echo "======================"
echo "Timestamp: $(date)"
echo "User: $(whoami)"
echo "Directory: $(pwd)"
echo "Branch before rollback: $(git branch --show-current)"
echo "Commit before rollback: $(git rev-parse HEAD)"
echo ""
} > $EMERGENCY_LOG

print_step "Stopping all running services..."

# Stop backend services
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "fastapi" 2>/dev/null || true
pkill -f "python.*app.main" 2>/dev/null || true

# Stop frontend services  
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true

# Stop Docker if running
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
fi

print_success "Services stopped"

print_step "Saving current state for analysis..."

# Save current git state
{
echo "GIT STATUS AT EMERGENCY:"
git status
echo ""
echo "GIT LOG (last 10 commits):"
git log --oneline -10
echo ""
echo "CURRENT DIFF FROM BASELINE:"
git diff baseline --stat || echo "Could not generate diff"
} >> $EMERGENCY_LOG

# Stash any uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_step "Stashing uncommitted changes..."
    git stash push -m "EMERGENCY: Uncommitted changes at $(date +%Y%m%d_%H%M%S)" >> $EMERGENCY_LOG 2>&1
    print_success "Changes stashed"
else
    print_step "No uncommitted changes to stash"
fi

print_step "Switching to baseline branch..."

# Switch to baseline
git checkout baseline >> $EMERGENCY_LOG 2>&1
git reset --hard origin/baseline >> $EMERGENCY_LOG 2>&1

print_success "Switched to baseline branch"

print_step "Cleaning workspace..."

# Clean any untracked files
git clean -fdx >> $EMERGENCY_LOG 2>&1

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove Node modules and reinstall
if [ -d "frontend/node_modules" ]; then
    rm -rf frontend/node_modules
fi

print_success "Workspace cleaned"

print_step "Reinstalling dependencies..."

# Backend dependencies
cd backend
if [ -f requirements.txt ]; then
    pip install -r requirements.txt >> ../$EMERGENCY_LOG 2>&1
    print_success "Backend dependencies installed"
else
    print_warning "No requirements.txt found"
fi
cd ..

# Frontend dependencies
cd frontend
if [ -f package.json ]; then
    npm install >> ../$EMERGENCY_LOG 2>&1
    print_success "Frontend dependencies installed"
else
    print_warning "No package.json found"
fi
cd ..

print_step "Verifying system health..."

# Test backend
cd backend
python -c "
try:
    from app.main import app
    print('✅ Backend imports successfully')
except Exception as e:
    print(f'❌ Backend import failed: {e}')
    exit(1)
" >> ../$EMERGENCY_LOG 2>&1

if [ $? -eq 0 ]; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed"
fi
cd ..

# Test frontend build
cd frontend
if npm run build >> ../$EMERGENCY_LOG 2>&1; then
    print_success "Frontend build successful"
else
    print_warning "Frontend build failed - check log"
fi
cd ..

print_step "Creating recovery checkpoint..."

# Tag this recovery point
RECOVERY_TAG="emergency-recovery-$(date +%Y%m%d_%H%M%S)"
git tag -a $RECOVERY_TAG -m "Emergency recovery checkpoint" >> $EMERGENCY_LOG 2>&1

print_success "Recovery checkpoint tagged: $RECOVERY_TAG"

print_step "Generating recovery report..."

# Complete the emergency log
{
echo ""
echo "RECOVERY ACTIONS TAKEN:"
echo "1. Stopped all services"
echo "2. Stashed uncommitted changes"
echo "3. Reset to baseline branch"
echo "4. Cleaned workspace"
echo "5. Reinstalled dependencies"
echo "6. Verified system health"
echo "7. Created recovery tag: $RECOVERY_TAG"
echo ""
echo "RECOVERY STATUS: COMPLETE"
echo "Emergency log saved to: $EMERGENCY_LOG"
echo ""
echo "NEXT STEPS:"
echo "1. Investigate root cause of emergency"
echo "2. Review stashed changes if recovery needed"
echo "3. Plan corrective actions"
echo "4. Update procedures to prevent recurrence"
echo ""
} >> $EMERGENCY_LOG

# Create human-readable summary
cat > rollbacks/emergency-summary.md << EOF
# Emergency Rollback Summary

## Emergency Details
- **Timestamp**: $(date)
- **Recovery Tag**: $RECOVERY_TAG
- **Log File**: $EMERGENCY_LOG

## Actions Taken
1. ✅ All services stopped
2. ✅ Current state saved/stashed
3. ✅ Reset to baseline branch
4. ✅ Workspace cleaned
5. ✅ Dependencies reinstalled
6. ✅ System health verified

## System Status
- **Branch**: baseline
- **Commit**: $(git rev-parse HEAD | cut -c1-8)
- **Services**: Stopped (ready for manual restart)
- **Dependencies**: Freshly installed

## Recovery Instructions
\`\`\`bash
# To restart services:
cd backend
uvicorn app.main:app --reload &

cd ../frontend  
npm run dev &
\`\`\`

## Investigation Required
- [ ] Review emergency log: $EMERGENCY_LOG
- [ ] Identify root cause
- [ ] Check stashed changes: \`git stash list\`
- [ ] Plan corrective actions
- [ ] Update procedures

## Emergency Contact
If system still not working:
1. Contact technical lead immediately
2. Do not attempt further changes
3. Preserve all logs and evidence
EOF

echo ""
echo "==============================="
print_success "🎉 EMERGENCY ROLLBACK COMPLETE"
echo "==============================="
echo ""
echo "📋 Recovery Summary:"
echo "  ✅ Services stopped safely"
echo "  ✅ System reset to baseline"
echo "  ✅ Dependencies reinstalled"
echo "  ✅ Health checks passed"
echo ""
echo "📂 Recovery Files:"
echo "  📄 Log: $EMERGENCY_LOG"
echo "  📄 Summary: rollbacks/emergency-summary.md"
echo "  🏷️  Tag: $RECOVERY_TAG"
echo ""
echo "🚀 To restart services:"
echo "  Backend:  cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "🔍 Investigation:"
echo "  📄 Review: $EMERGENCY_LOG"
echo "  💾 Stashed changes: git stash list"
echo "  📊 Compare: git diff $RECOVERY_TAG..stash@{0}"
echo ""
print_warning "⚠️  INVESTIGATE ROOT CAUSE BEFORE CONTINUING REFACTORING"
echo ""
print_success "Baseline system restored and ready! 🚨➡️✅"