# Development Environment Setup

**Purpose**: Complete local development setup and configuration  
**Target Time**: 30 minutes from zero to fully functional environment  
**Audience**: Developers and AI assistants  

---

## Overview

This guide provides comprehensive instructions for setting up a complete development environment for the FRC GPT Scouting App. Follow these steps to get from a fresh system to a fully functional development setup.

### What You'll Have After Setup
- Complete backend API with hot reloading
- Interactive frontend with live updates
- Database with sample data
- AI integration ready for testing
- Full development toolchain with linting and testing

---

## Prerequisites

### Required Software Versions
- **Python 3.11+** - Backend development and services
- **Node.js 18 LTS** - Frontend development and build tools
- **Docker 24.0+ & Docker Compose 2.20+** - Containerization (optional but recommended)
- **Git 2.40+** - Version control
- **VS Code or PyCharm** - Recommended IDEs with excellent plugin support

### System Requirements
- **Operating System**: Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum, 16GB recommended for AI development
- **Storage**: 5GB free space for dependencies and data
- **Network**: Reliable internet for package downloads and AI API calls

### Required Accounts
- **OpenAI Platform Account** - Get API key from [platform.openai.com](https://platform.openai.com/)
- **GitHub Account** - For version control and collaboration (recommended)

---

## Installation Methods

### Method 1: Docker Development Setup (Recommended)

**Best for**: Quick setup, consistent environments, AI assistant development

#### 1. Repository Setup
```bash
# Clone repository
git clone [repository-url]
cd FRC-GPT-Scouting-App

# Verify repository structure
ls -la
# Should see: README.md, docker-compose.yml, backend/, frontend/, docs/
```

#### 2. Environment Configuration
```bash
# Create backend environment file
cp backend/.env.example backend/.env

# Edit environment file (use your preferred editor)
nano backend/.env
# OR
code backend/.env
```

**Required Environment Variables**:
```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./app/data/scouting_app.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Frontend Configuration (for CORS)
FRONTEND_URL=http://localhost:3000

# Logging Configuration
LOG_LEVEL=DEBUG
```

#### 3. Docker Environment Startup
```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Verify all containers are running
docker-compose ps
# Should show: backend, frontend, database (all "Up")

# View logs for debugging if needed
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 4. Verification
```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Test API documentation
curl http://localhost:8000/docs
# Should return HTML for API docs

# Frontend should be accessible at http://localhost:3000
```

### Method 2: Manual Development Setup

**Best for**: Direct development, debugging, custom configuration

#### 1. Backend Environment Setup

**Python Environment**:
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Command Prompt):
venv\Scripts\activate.bat
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Verify activation (should show virtual environment path)
which python
```

**Install Dependencies**:
```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list | grep fastapi
pip list | grep openai
```

**Database Initialization**:
```bash
# Create data directory
mkdir -p app/data

# Initialize database schema
python -m app.database.init_db

# Load sample data (optional)
python -m app.database.load_sample_data
```

**Environment Configuration**:
```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

**Start Backend Server**:
```bash
# Start development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Start with debugging
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

#### 2. Frontend Environment Setup

**Node.js Environment** (new terminal):
```bash
# Navigate to frontend directory
cd frontend

# Verify Node.js version
node --version
# Should be 18.x.x or higher

# Install dependencies
npm install

# Verify critical packages
npm list react
npm list typescript
npm list vite
```

**Development Configuration**:
```bash
# Copy environment template (if exists)
cp .env.example .env.local

# Edit frontend environment
nano .env.local
```

**Frontend Environment Variables**:
```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Development Features
VITE_DEBUG_MODE=true
VITE_ENABLE_DEVTOOLS=true
```

**Start Frontend Server**:
```bash
# Start development server
npm run dev

# Alternative: Start with specific port
npm run dev -- --port 3000
```

---

## Development Workflow Setup

### IDE Configuration

#### Visual Studio Code Setup
**Essential Extensions**:
```bash
# Install VS Code extensions
code --install-extension ms-python.python
code --install-extension ms-python.pylint
code --install-extension ms-python.black-formatter
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
```

**VS Code Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "tailwindCSS.includeLanguages": {
    "typescript": "typescript",
    "typescriptreact": "typescriptreact"
  }
}
```

#### PyCharm Setup
**Configuration Steps**:
1. Open project directory in PyCharm
2. Configure Python Interpreter: `Settings > Python Interpreter > Add > Virtual Environment > Existing > backend/venv/bin/python`
3. Configure Database: `Database > Add > SQLite > backend/app/data/scouting_app.db`
4. Enable FastAPI support: `Settings > Languages & Frameworks > FastAPI`

### Git Configuration

**Git Hooks Setup**:
```bash
# Navigate to project root
cd FRC-GPT-Scouting-App

# Make hooks executable
chmod +x .githooks/*

# Configure git to use project hooks
git config core.hooksPath .githooks
```

**Pre-commit Configuration**:
```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install pre-commit hooks
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files
```

---

## Development Tools and Quality

### Backend Quality Tools

**Linting and Formatting**:
```bash
# Navigate to backend directory
cd backend

# Run code formatting
black app/ tests/

# Run linting
flake8 app/ tests/

# Run type checking
mypy app/

# Run all quality checks
python -m scripts.quality_check
```

**Testing Setup**:
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v tests/
```

### Frontend Quality Tools

**Linting and Formatting**:
```bash
# Navigate to frontend directory
cd frontend

# Run TypeScript checking
npm run type-check

# Run linting
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Format code
npm run format

# Run all quality checks
npm run quality-check
```

**Testing Setup**:
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run end-to-end tests (if available)
npm run test:e2e
```

---

## Data and Sample Setup

### Sample Data Loading

**Backend Sample Data**:
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Load sample datasets
python -m app.scripts.load_sample_data

# Verify data loading
python -c "from app.database import get_db; print('Database ready')"
```

**Sample Dataset Structure**:
```json
{
  "teams": [
    {
      "team_number": 1234,
      "nickname": "Sample Team Alpha",
      "autonomous_score": 15.2,
      "teleop_avg_points": 45.8,
      "endgame_points": 12.0,
      "defense_rating": 3.5,
      "reliability_score": 0.85
    }
  ],
  "context": "2024 FIRST Robotics Competition - Sample Data",
  "game_info": "Crescendo game with note scoring and climbing"
}
```

### Testing Data

**Create Test Dataset**:
```bash
# Create minimal test data for development
cat > backend/app/data/test_minimal.json << 'EOF'
{
  "teams": [
    {"team_number": 1001, "nickname": "Test Alpha", "autonomous_score": 20, "teleop_avg_points": 50, "endgame_points": 15, "defense_rating": 4},
    {"team_number": 1002, "nickname": "Test Beta", "autonomous_score": 18, "teleop_avg_points": 48, "endgame_points": 12, "defense_rating": 3},
    {"team_number": 1003, "nickname": "Test Gamma", "autonomous_score": 22, "teleop_avg_points": 52, "endgame_points": 18, "defense_rating": 5}
  ],
  "context": "Minimal test dataset for development",
  "game_info": "Test competition with sample scoring"
}
EOF
```

---

## Environment Verification

### Comprehensive Health Check

**Backend Verification Script**:
```bash
# Create verification script
cat > backend/verify_setup.py << 'EOF'
#!/usr/bin/env python3
"""Development environment verification script."""

import sys
import requests
import json
from pathlib import Path

def verify_backend():
    """Verify backend is running and healthy."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def verify_database():
    """Verify database is accessible."""
    db_path = Path("app/data/scouting_app.db")
    if db_path.exists():
        print("✅ Database file exists")
        return True
    else:
        print("❌ Database file not found")
        return False

def verify_environment():
    """Verify environment variables."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            env_content = f.read()
            if "OPENAI_API_KEY" in env_content:
                print("✅ Environment configuration found")
                return True
    print("❌ Environment configuration missing")
    return False

def verify_ai_integration():
    """Test AI service integration."""
    try:
        # Test with minimal API call (requires valid API key)
        response = requests.post(
            "http://localhost:8000/api/test/ai",
            json={"test": "minimal"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ AI integration working")
            return True
        else:
            print(f"⚠️  AI integration test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  AI integration test error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying development environment setup...\n")
    
    checks = [
        verify_backend(),
        verify_database(),
        verify_environment(),
        verify_ai_integration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 Environment Check Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 Development environment is fully ready!")
        sys.exit(0)
    else:
        print("⚠️  Some issues need attention. Check output above.")
        sys.exit(1)
EOF

# Run verification
python verify_setup.py
```

**Frontend Verification**:
```bash
# Test frontend build
cd frontend
npm run build

# Check for build errors
echo $?
# Should be 0 for success

# Test development server response
curl http://localhost:3000
# Should return HTML content
```

### Performance Verification

**API Performance Test**:
```bash
# Test API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"

# Create curl format file for timing
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

---

## Troubleshooting Common Issues

### Backend Issues

**Python Version Problems**:
```bash
# Check Python version
python --version
# If not 3.11+, install correct version

# Check virtual environment
which python
# Should point to venv directory

# Recreate virtual environment if needed
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Import Errors**:
```bash
# Check if app module is importable
python -c "import app; print('Import successful')"

# Check PYTHONPATH
echo $PYTHONPATH

# Add current directory to path if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Database Issues**:
```bash
# Check database permissions
ls -la app/data/

# Recreate database
rm app/data/scouting_app.db
python -m app.database.init_db
```

### Frontend Issues

**Node.js Version Problems**:
```bash
# Check Node.js version
node --version

# Use Node Version Manager if needed
nvm install 18
nvm use 18
```

**Package Installation Issues**:
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Build Errors**:
```bash
# Check TypeScript compilation
npx tsc --noEmit

# Check for missing dependencies
npm ls --depth=0
```

### Docker Issues

**Container Problems**:
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs backend
docker-compose logs frontend

# Restart containers
docker-compose down
docker-compose up -d
```

**Permission Issues**:
```bash
# Fix file permissions (Linux/macOS)
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo usermod -aG docker $USER
# Logout and login again
```

### Network Issues

**Port Conflicts**:
```bash
# Check what's using ports
lsof -i :8000
lsof -i :3000

# Kill processes if needed
sudo kill -9 <PID>

# Use different ports
uvicorn app.main:app --port 8001
npm run dev -- --port 3001
```

**CORS Issues**:
```bash
# Check CORS configuration in backend/.env
FRONTEND_URL=http://localhost:3000

# Test CORS directly
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

---

## Development Workflow

### Daily Development Routine

**1. Start Development Session**:
```bash
# Option A: Docker
docker-compose up -d

# Option B: Manual
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd frontend && npm run dev &
```

**2. Run Quality Checks**:
```bash
# Backend
cd backend && pytest && flake8 app/

# Frontend  
cd frontend && npm run lint && npm test
```

**3. Make Changes and Test**:
```bash
# Backend changes auto-reload with uvicorn --reload
# Frontend changes auto-reload with Vite

# Run specific tests for changed areas
pytest tests/test_new_feature.py
```

**4. End Development Session**:
```bash
# Option A: Docker
docker-compose down

# Option B: Manual
# Ctrl+C to stop servers
deactivate  # Deactivate Python virtual environment
```

### Feature Development Workflow

**1. Create Feature Branch**:
```bash
git checkout -b feature/your-feature-name
```

**2. Develop with Tests**:
```bash
# Write tests first (TDD approach)
# Implement feature
# Verify tests pass
pytest tests/test_your_feature.py
```

**3. Quality Check**:
```bash
# Run full quality suite
cd backend && python -m scripts.quality_check
cd frontend && npm run quality-check
```

**4. Commit and Push**:
```bash
git add .
git commit -m "Add feature: description"
git push origin feature/your-feature-name
```

---

## Next Steps

### For New Developers
1. **[Coding Standards](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)** - Learn project coding conventions
2. **[Testing Guide](../04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md)** - Understand testing approach
3. **[Architecture Overview](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)** - Understand system design

### For AI Assistants
1. **[AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)** - Claude Code integration
2. **[Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md)** - Machine-readable specifications
3. **[Development Patterns](../05_AI_FRAMEWORK/PROMPT_TEMPLATES.md)** - Standard development approaches

### Advanced Setup
1. **[Docker Guide](DOCKER_SETUP.md)** - Advanced containerization
2. **[Database Setup](DATABASE_INITIALIZATION.md)** - Database management
3. **[Deployment Guide](../06_OPERATIONS/DEPLOYMENT_GUIDE.md)** - Production deployment

---

## Success Criteria

✅ **Environment Ready** when:
- Backend starts without errors and responds to health checks
- Frontend loads and connects to backend API
- Database is initialized and accessible
- All tests pass for both backend and frontend
- Code quality tools run without errors
- Sample data loads successfully

✅ **Development Ready** when:
- Hot reloading works for both backend and frontend
- IDE is configured with proper syntax highlighting and error detection
- Git hooks are working for pre-commit quality checks
- AI integration test passes with valid API key
- Full development workflow can be completed successfully

---

**Next**: [Docker Setup Guide](DOCKER_SETUP.md) | [Database Initialization](DATABASE_INITIALIZATION.md) | [Coding Standards](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)

---
**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Getting Started](../01_PROJECT_FOUNDATION/GETTING_STARTED.md), [Technology Stack](../01_PROJECT_FOUNDATION/TECHNOLOGY_STACK.md)