#!/bin/bash
# setup_refactoring.sh - Initial setup for FRC Scouting App refactoring
# Compatible with WSL Ubuntu on Windows

set -e  # Exit on any error

echo "🚀 Setting up FRC Scouting App Refactoring Environment"
echo "================================================"

# Detect if running in WSL
if grep -qi microsoft /proc/version; then
    echo "Detected WSL environment"
    IS_WSL=true
else
    IS_WSL=false
fi

# Colors for output (work in both Windows Terminal and standard terminals)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -f "ARCHITECTURE.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the FRC-GPT-Scouting-App root directory"
    print_warning "Current directory: $(pwd)"
    if [ "$IS_WSL" = true ]; then
        print_warning "In WSL, make sure you're in the mounted Windows directory"
        print_warning "Example: cd /mnt/c/Users/[YourUsername]/Documents/FRC-GPT-Scouting-App/FRC-GPT-Scouting-App"
    fi
    exit 1
fi

print_step "Checking prerequisites..."

# Check required tools
MISSING_TOOLS=0

if ! check_command git; then ((MISSING_TOOLS++)); fi
if ! check_command python; then ((MISSING_TOOLS++)); fi
if ! check_command node; then ((MISSING_TOOLS++)); fi
if ! check_command npm; then ((MISSING_TOOLS++)); fi

if [ $MISSING_TOOLS -gt 0 ]; then
    print_error "$MISSING_TOOLS required tools are missing. Please install them first."
    exit 1
fi

print_step "Verifying current system state..."

# Check if system is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Working directory has uncommitted changes"
    echo "Uncommitted files:"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N): " continue_dirty
    if [[ $continue_dirty != "y" && $continue_dirty != "Y" ]]; then
        print_error "Please commit or stash changes before running setup"
        exit 1
    fi
fi

# Verify we're on master branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "master" ]; then
    print_warning "Currently on branch '$CURRENT_BRANCH', not 'master'"
    read -p "Switch to master branch? (y/N): " switch_master
    if [[ $switch_master == "y" || $switch_master == "Y" ]]; then
        git checkout master
        git pull origin master
        print_success "Switched to master branch"
    fi
fi

print_step "Creating directory structure..."

# Create required directories
mkdir -p checksums
mkdir -p sprint-logs
mkdir -p sprint-context
mkdir -p sprint-summaries
mkdir -p sprint-scorecards
mkdir -p test-results
mkdir -p coverage-reports
mkdir -p metrics
mkdir -p rollbacks
mkdir -p backups

print_success "Directory structure created"

print_step "Setting up Python environment..."

# Check Python version - handle both python and python3 commands
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
if [[ $PYTHON_VERSION < "3.9" ]]; then
    print_error "Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi
print_success "Python version: $PYTHON_VERSION (using $PYTHON_CMD)"

# Ensure pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    print_warning "pip not found, installing..."
    $PYTHON_CMD -m ensurepip --default-pip || apt-get install python3-pip -y
fi

PIP_CMD="$PYTHON_CMD -m pip"

# Install Python dependencies
cd backend
if [ ! -f requirements-dev.txt ]; then
    print_warning "requirements-dev.txt not found, creating basic version"
    cat > requirements-dev.txt << EOF
# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
httpx>=0.24.0
black>=23.0.0
ruff>=0.0.260
mypy>=1.0.0
coverage>=7.0.0
radon>=5.1.0
pre-commit>=3.0.0
EOF
fi

$PIP_CMD install -r requirements-dev.txt
print_success "Python development dependencies installed"

# Install main dependencies
$PIP_CMD install -r requirements.txt
print_success "Python main dependencies installed"

cd ..

print_step "Setting up Node.js environment..."

# Check Node version
NODE_VERSION=$(node --version)
print_success "Node.js version: $NODE_VERSION"

# Install frontend dependencies
cd frontend
npm install
print_success "Node.js dependencies installed"
cd ..

print_step "Configuring development tools..."

# Set up pytest configuration if it doesn't exist
if [ ! -f backend/pytest.ini ]; then
    cat > backend/pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    e2e: marks tests as end-to-end tests
    benchmark: marks performance benchmark tests
EOF
    print_success "pytest configuration created"
fi

# Set up coverage configuration
if [ ! -f backend/.coveragerc ]; then
    cat > backend/.coveragerc << EOF
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */conftest.py

[report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError

[html]
directory = htmlcov

[xml]
output = coverage.xml
EOF
    print_success "Coverage configuration created"
fi

# Set up pre-commit hooks
if [ ! -f .pre-commit-config.yaml ]; then
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        files: ^backend/
        
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.260
    hooks:
      - id: ruff
        files: ^backend/
        
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: bash -c 'cd backend && python -m pytest tests/ -x --tb=short'
        language: system
        pass_filenames: false
        always_run: false
        files: ^backend/.*\.py$
EOF
    print_success "Pre-commit configuration created"
fi

print_step "Testing current system..."

# Test backend
print_step "Testing backend..."
cd backend

# Check if tests exist and run them
if [ -d "tests" ] && [ "$(find tests -name '*.py' | wc -l)" -gt 0 ]; then
    $PYTHON_CMD -m pytest tests/ -x --tb=short || print_warning "Some backend tests failed"
else
    print_warning "No backend tests found - this is expected before Sprint 1"
fi

# Test if backend starts - handle WSL port binding
print_step "Testing backend startup..."
if [ "$IS_WSL" = true ]; then
    print_warning "In WSL, make sure Windows Firewall allows port 8000"
fi

timeout 10s $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 5  # Give more time in WSL

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend starts successfully"
else
    print_warning "Backend health check failed - may need configuration"
fi

# Stop backend
kill $BACKEND_PID 2>/dev/null || true
sleep 2

cd ..

# Test frontend
print_step "Testing frontend build..."
cd frontend
if npm run build > /dev/null 2>&1; then
    print_success "Frontend builds successfully"
else
    print_warning "Frontend build failed - may need attention"
fi
cd ..

print_step "Creating baseline branch..."

# Create baseline branch
if git branch -r | grep -q "origin/baseline"; then
    print_warning "Remote baseline branch already exists"
    git checkout baseline
    git pull origin baseline
else
    git checkout -b baseline
    git push -u origin baseline
    print_success "Baseline branch created and pushed"
fi

# Generate initial checksums
print_step "Generating initial checksums..."
find backend -name "*.py" -type f -exec sha1sum {} \; | sort > checksums/baseline-python.txt
find frontend/src -name "*.ts" -o -name "*.tsx" -type f -exec sha1sum {} \; 2>/dev/null | sort > checksums/baseline-typescript.txt || touch checksums/baseline-typescript.txt

print_success "Initial checksums generated"

# Create initial metrics
print_step "Collecting baseline metrics..."
if [ -f "Refactor Documents/scripts/collect_metrics.py" ]; then
    python "Refactor Documents/scripts/collect_metrics.py" || print_warning "Metrics collection failed - will set up in Sprint 1"
fi

print_step "Setting up Git hooks..."
# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    pre-commit install
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not available, skipping hooks"
fi

print_step "Creating initial documentation..."

# Create sprint 0 log
cat > sprint-logs/sprint-0-setup.md << EOF
# Sprint 0: Refactoring Setup

## Setup Date: $(date)
## Branch: $(git branch --show-current)
## Setup Script Version: 1.0

## Environment Verified
- Python: $(python --version 2>&1)
- Node.js: $(node --version)
- Git: $(git --version | head -1)

## Directories Created
- checksums/
- sprint-logs/
- sprint-context/
- metrics/
- rollbacks/
- backups/

## Baseline State
- Branch: baseline
- Commit: $(git rev-parse HEAD)
- Files tracked: $(find backend -name "*.py" | wc -l) Python, $(find frontend/src -name "*.ts*" 2>/dev/null | wc -l) TypeScript

## Next Steps
1. Review all refactoring documentation
2. Plan Sprint 1 objectives
3. Begin test framework setup
4. Start metrics collection

## Setup Status: COMPLETE ✅
EOF

print_success "Setup documentation created"

echo ""
echo "================================================"
print_success "🎉 FRC Scouting App Refactoring Setup Complete!"
echo "================================================"
echo ""
echo "📋 Setup Summary:"
echo "  ✅ Environment verified"
echo "  ✅ Dependencies installed" 
echo "  ✅ Directory structure created"
echo "  ✅ Baseline branch established"
echo "  ✅ Initial checksums generated"
echo "  ✅ Development tools configured"
echo ""
echo "📂 Key Locations:"
echo "  📁 Documentation: ./Refactor Documents/"
echo "  📁 Sprint Logs: ./sprint-logs/"
echo "  📁 Metrics: ./metrics/"
echo "  📁 Checksums: ./checksums/"
echo ""
echo "🎯 Next Steps:"
echo "  1. Review: ./Refactor Documents/AI_REFACTORING_PLAN.md"
echo "  2. Plan Sprint 1 using: ./Refactor Documents/SPRINT_EXECUTION_CHECKLIST.md"
echo "  3. Use AI templates from: ./Refactor Documents/AI_PROMPT_GUIDE.md"
echo ""
echo "🚨 Emergency Procedures:"
echo "  📄 See: ./Refactor Documents/ROLLBACK_PROCEDURES.md"
echo "  🔧 Run: ./Refactor Documents/scripts/emergency_rollback.sh"
echo ""
print_success "Ready to begin Sprint 1! 🚀"