# Getting Started with FRC GPT Scouting App

**Purpose**: Rapid developer onboarding and system setup  
**Target Time**: 15 minutes to running application  
**Audience**: Developers, strategists, and AI assistants  

---

## Quick Start Overview

The FRC GPT Scouting App helps FIRST Robotics Competition teams make strategic alliance selection decisions using AI-powered analysis. This guide gets you from zero to running application in 15 minutes.

### What You'll Accomplish
- Set up complete development environment
- Start frontend and backend services
- Load sample data and generate your first picklist
- Understand core workflow for team analysis

---

## Prerequisites

### Required Software
- **Python 3.11+** - Backend API and services
- **Node.js 18+** - Frontend development and build
- **Docker & Docker Compose** - Containerized development (recommended)
- **Git** - Version control

### Required Accounts
- **OpenAI API Account** - For GPT-4 analysis (get key from [OpenAI Platform](https://platform.openai.com/))

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet access for AI analysis and data fetching

---

## Installation Methods

### Option 1: Docker Setup (Recommended - 5 minutes)

**Best for**: Quick setup, consistent environments, production-like testing

```bash
# 1. Clone repository
git clone [repository-url]
cd FRC-GPT-Scouting-App

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY=your_key_here

# 3. Start services
docker-compose up -d

# 4. Verify installation
curl http://localhost:8000/health
```

**Services Started**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Manual Setup (10-15 minutes)

**Best for**: Development work, debugging, service modification

#### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY=your_key_here

# Initialize database
python -m app.database.init_db

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup (new terminal)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Environment Configuration

### Required Environment Variables

Create `backend/.env` file:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./app/data/scouting_app.db

# Logging Configuration
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Optional Configuration
```env
# Performance Tuning
CACHE_TTL=3600
MAX_WORKERS=4
REQUEST_TIMEOUT=30

# Development Features
DEBUG_MODE=false
ENABLE_PROFILING=false
```

---

## Verification & First Use

### 1. Verify Installation

**Backend Health Check**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

**Frontend Access**:
- Open http://localhost:3000
- Should see FRC GPT Scouting App interface

**API Documentation**:
- Open http://localhost:8000/docs
- Interactive API documentation available

### 2. Load Sample Data

**Using provided sample dataset**:
```bash
# Copy sample data (if available)
cp backend/sample_data/unified_dataset.json backend/app/data/

# Or create minimal test dataset
cat > backend/app/data/test_dataset.json << 'EOF'
{
  "teams": [
    {
      "team_number": 1234,
      "nickname": "Test Team Alpha",
      "autonomous_score": 15.2,
      "teleop_avg_points": 45.8,
      "endgame_points": 12.0,
      "defense_rating": 3.5
    },
    {
      "team_number": 5678,
      "nickname": "Test Team Beta", 
      "autonomous_score": 18.1,
      "teleop_avg_points": 42.3,
      "endgame_points": 15.0,
      "defense_rating": 4.2
    }
  ],
  "context": "Test competition data for development"
}
EOF
```

### 3. Generate Your First Picklist

**Using the Web Interface**:
1. Navigate to http://localhost:3000
2. Upload your dataset or use test data
3. Configure priorities (autonomous: 30%, teleop: 40%, endgame: 20%, defense: 10%)
4. Select "First Pick" position
5. Enter your team number (e.g., 1234)
6. Click "Generate Picklist"

**Using the API directly**:
```bash
curl -X POST "http://localhost:8000/api/picklist/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "your_team_number": 1234,
    "pick_position": "first",
    "priorities": [
      {"metric": "autonomous_score", "weight": 0.3},
      {"metric": "teleop_avg_points", "weight": 0.4},
      {"metric": "endgame_points", "weight": 0.2},
      {"metric": "defense_rating", "weight": 0.1}
    ],
    "exclude_teams": [],
    "dataset_path": "app/data/test_dataset.json"
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "data": {
    "ranked_teams": [
      {
        "team_number": 5678,
        "rank": 1,
        "score": 85.2,
        "reasoning": "Strong overall performance with excellent autonomous..."
      }
    ],
    "summary": "Detailed analysis of team capabilities and strategic fit...",
    "processing_time": 2.34,
    "cached": false
  }
}
```

---

## Understanding the Core Workflow

### 1. Data Input Phase
- **Team Data**: Performance metrics, capabilities, match history
- **Competition Context**: Game-specific information, venue details
- **Strategic Priorities**: Weight different aspects (auto, teleop, defense, etc.)

### 2. Analysis Phase
- **Data Aggregation**: Combine multiple data sources
- **Team Evaluation**: Score teams based on priorities
- **Strategic Analysis**: AI evaluation of alliance fit
- **Ranking Generation**: Ordered recommendations with reasoning

### 3. Results Phase
- **Ranked Picklist**: Teams ordered by strategic value
- **Detailed Analysis**: Strengths, weaknesses, synergies
- **Interactive Exploration**: Compare teams, ask follow-up questions
- **Export Options**: Share insights with alliance selection team

---

## Common Workflows

### For Alliance Selection Strategists
1. **Data Preparation**: Import scouting data and competition info
2. **Priority Setting**: Define what matters most for your strategy
3. **Picklist Generation**: Get AI-powered team rankings
4. **Strategic Analysis**: Deep dive into top recommendations
5. **Alliance Planning**: Use insights for draft strategy

### For Development Teams
1. **Environment Setup**: Get development environment running
2. **Code Exploration**: Understand service architecture
3. **Feature Development**: Add new capabilities or integrations
4. **Testing**: Validate changes with comprehensive test suite
5. **Deployment**: Ship improvements to production

### For AI Assistants (Claude Code)
1. **Context Loading**: Read comprehensive documentation
2. **Pattern Recognition**: Understand established development patterns  
3. **Feature Implementation**: Autonomously develop new capabilities
4. **Quality Validation**: Ensure compliance with standards
5. **Integration**: Seamlessly integrate with existing architecture

---

## Next Steps

### For Users
- **[Architecture Overview](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)** - Understand system design
- **[API Documentation](../03_ARCHITECTURE/API_CONTRACTS.md)** - Complete API reference
- **[User Guide](../06_OPERATIONS/USER_GUIDE.md)** - Advanced features and workflows

### For Developers  
- **[Development Environment](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)** - Detailed development setup
- **[Coding Standards](../04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md)** - Code quality guidelines
- **[Testing Guide](../04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md)** - Testing strategies and frameworks

### For AI Assistants
- **[AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)** - Claude Code integration
- **[Service Contracts](../05_AI_FRAMEWORK/SERVICE_CONTRACTS.md)** - Machine-readable specifications
- **[Development Patterns](../05_AI_FRAMEWORK/PROMPT_TEMPLATES.md)** - Standardized development approaches

---

## Troubleshooting Quick Fixes

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip list | grep fastapi

# Check environment variables
cat backend/.env | grep OPENAI_API_KEY
```

### Frontend Build Errors
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API Connection Issues
```bash
# Test backend health
curl http://localhost:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker-compose up -d --build

# Check container logs
docker-compose logs backend
docker-compose logs frontend
```

**📖 Complete Troubleshooting**: [Troubleshooting Guide](../06_OPERATIONS/TROUBLESHOOTING.md)

---

## Success Indicators

✅ **Installation Complete** when:
- Backend health check returns `{"status": "healthy"}`
- Frontend loads at http://localhost:3000
- API documentation accessible at http://localhost:8000/docs
- Sample picklist generation succeeds
- No error messages in console logs

✅ **Ready for Development** when:
- All tests pass: `pytest backend/tests/`
- Code quality checks pass: `flake8 backend/app/`
- Frontend builds successfully: `npm run build`
- Hot reload works for both frontend and backend

✅ **Ready for Production** when:
- Docker containers start without errors
- Environment variables properly configured
- Database initialization completes
- SSL certificates configured (if needed)
- Monitoring and logging operational

---

**Next**: [Technology Stack Overview](TECHNOLOGY_STACK.md) | [Development Environment Setup](../02_DEVELOPMENT_SETUP/DEVELOPMENT_ENVIRONMENT.md)

---
**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [README.md](../../README.md), [Architecture Overview](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)