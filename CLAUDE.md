# Claude Code Development Guide

**Purpose**: Comprehensive guide for Claude Code autonomous development  
**Last Updated**: June 25, 2025  
**Version**: 2.0  

---

## Quick Start for Claude Code

### Project Overview
The FRC GPT Scouting App is an AI-powered team analysis and alliance selection platform for FIRST Robotics Competition. It uses a service-oriented architecture with 6 specialized services orchestrated by a main coordinator.

**Key Technologies**:
- Backend: Python 3.11 + FastAPI + SQLite
- Frontend: React 18 + TypeScript + Vite
- AI: OpenAI GPT-4 integration
- Deployment: Docker + Docker Compose

### Architecture Quick Reference
```
┌─────────────────────────────────────┐
│          Orchestrator               │
│    PicklistGeneratorService         │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   Data Layer  Analysis   AI Layer
      │           │         │
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │  Data   │ │  Team   │ │Picklist │
   │Aggreg.  │ │Analysis │ │   GPT   │
   └─────────┘ └─────────┘ └─────────┘
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Perform. │ │Priority │ │ Batch   │
   │Optimiz. │ │ Calc.   │ │Process  │
   └─────────┘ └─────────┘ └─────────┘
```

---

## Development Standards

### Code Quality Requirements
- **Python**: Follow PEP 8 with 100-char lines, comprehensive type hints, docstrings for all public methods
- **TypeScript**: Strict mode, explicit types, JSDoc comments for complex functions
- **Testing**: >90% coverage required, TDD approach preferred
- **Error Handling**: Comprehensive logging, structured error responses
- **Performance**: API <200ms, services <5s, cache hit rate >80%

### Service Development Pattern
All services must follow this exact pattern:

```python
class NewService:
    """
    Service for [specific responsibility].
    
    Thread Safety: [Thread-safe/Not thread-safe]
    Dependencies: [List dependencies]
    """
    
    def __init__(self, dependencies) -> None:
        """Initialize with validation and logging."""
        self._validate_dependencies(dependencies)
        self.dependencies = dependencies
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def public_method(self, param: TypeHint) -> ReturnType:
        """
        Public method with comprehensive documentation.
        
        Args:
            param: Description with type and constraints
            
        Returns:
            Description of return value
            
        Raises:
            ValueError: When validation fails
            ServiceError: When processing fails
        """
        try:
            self._validate_input(param)
            result = self._process_data(param)
            logger.info(f"Successfully processed: {param}")
            return result
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise ServiceError(f"Operation failed: {e}")
```

---

## Common Development Tasks

### Adding New Service
1. Create service file in `backend/app/services/`
2. Follow service pattern above with comprehensive error handling
3. Add to orchestrator in `PicklistGeneratorService.__init__()`
4. Create comprehensive tests in `backend/tests/test_services/`
5. Update service contracts documentation
6. Run quality checks: `pytest --cov=app && flake8 app/ && mypy app/`

### Adding API Endpoint
1. Create endpoint in `backend/app/api/v1/endpoints/`
2. Use FastAPI with Pydantic models for validation
3. Include comprehensive error handling and logging
4. Add OpenAPI documentation with examples
5. Create integration tests
6. Update API contracts documentation

### Adding Frontend Component
1. Create component in `src/components/` with TypeScript
2. Include proper error handling and loading states
3. Use custom hooks for API integration
4. Add comprehensive tests with React Testing Library
5. Follow accessibility guidelines
6. Update component documentation

### Bug Fixes
1. Write failing test that reproduces the bug
2. Fix the issue while maintaining all existing tests
3. Ensure fix follows established patterns
4. Add regression test if needed
5. Run full test suite to ensure no breakage

---

## Testing Strategy

### Test Structure
```
backend/tests/
├── test_services/           # Unit tests (70%)
├── test_integration/        # Integration tests (25%)
└── test_e2e/               # End-to-end tests (5%)

frontend/src/
├── components/__tests__/    # Component tests
├── hooks/__tests__/        # Hook tests
└── e2e/                   # Playwright E2E tests
```

### Test Requirements
- All new code must have >90% test coverage
- Tests must use realistic data and scenarios
- Mock external services (especially OpenAI API)
- Include both positive and negative test cases
- Performance tests for critical paths

### Running Tests
```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
flake8 app/ tests/
mypy app/

# Frontend
cd frontend
npm test -- --coverage
npm run lint
npm run type-check
```

---

## AI Integration Guidelines

### OpenAI Service Usage
- Always mock OpenAI client in tests
- Implement exponential backoff for rate limits
- Track token usage and costs
- Validate response formats before processing
- Handle API errors gracefully

```python
# Example AI service test
@patch('app.services.picklist_gpt_service.openai_client')
async def test_ai_analysis(mock_client):
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"result": "test"}'))]
    mock_client.chat.completions.create.return_value = mock_response
    
    result = await service.execute_analysis(messages)
    assert result["response"] is not None
```

### AI Code Review Standards
- Identify AI-generated code in PRs
- Document prompts used for AI generation
- Validate AI logic and edge case handling
- Ensure AI code follows project patterns
- Test AI-generated code thoroughly

---

## Performance Guidelines

### Caching Strategy
- Use memory cache for frequently accessed data
- Implement TTL-based cache expiration
- Generate deterministic cache keys
- Monitor cache hit rates (target >80%)

```python
def generate_cache_key(self, params: Dict) -> str:
    """Generate deterministic cache key."""
    import hashlib
    import json
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()[:16]
```

### Database Optimization
- Use SQLAlchemy with proper indexes
- Implement query optimization for large datasets
- Use batch processing for >50 teams
- Monitor query performance (<100ms target)

### API Performance
- Target <200ms response times
- Implement request timeout handling
- Use async/await for concurrent operations
- Monitor and log performance metrics

---

## Security Requirements

### Input Validation
- Validate all inputs with Pydantic models
- Sanitize user-provided data
- Use parameterized queries for database access
- Implement rate limiting for API endpoints

### Secret Management
- Store secrets in environment variables
- Never commit API keys or credentials
- Use secure random generation for tokens
- Implement proper authentication flows

### Error Handling
- Don't expose internal error details to users
- Log security events appropriately
- Implement proper CORS configuration
- Use HTTPS in production

---

## Documentation Standards

### Code Documentation
- Docstrings for all public methods with examples
- Type hints for all function parameters and returns
- Inline comments for complex logic only
- Clear variable and function naming

### API Documentation
- OpenAPI schemas for all endpoints
- Request/response examples
- Error response documentation
- Rate limiting information

### Architecture Documentation
- Keep service contracts updated
- Document integration patterns
- Update deployment guides for changes
- Maintain troubleshooting guides

---

## Deployment and Operations

### Local Development
```bash
# Docker setup (recommended)
docker-compose -f docker-compose.dev.yml up -d

# Manual setup
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
cd frontend && npm run dev
```

### Environment Variables
```env
# Required
OPENAI_API_KEY=sk-your_key_here
DATABASE_URL=sqlite:///./app/data/scouting_app.db

# Optional
DEBUG=true
LOG_LEVEL=DEBUG
FRONTEND_URL=http://localhost:3000
```

### Quality Gates
All changes must pass:
- [ ] All tests passing (>90% coverage)
- [ ] Code formatting (Black, Prettier)
- [ ] Linting (flake8, ESLint)
- [ ] Type checking (mypy, TypeScript)
- [ ] Security scanning (Bandit)
- [ ] Performance benchmarks met

---

## Troubleshooting

### Common Issues

**Import Errors (Python)**:
```bash
# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or run from backend directory
cd backend && python -m app.main
```

**API Errors**:
- Check OpenAI API key is valid
- Verify environment variables are loaded
- Check database file permissions
- Review logs for detailed error messages

**Test Failures**:
- Ensure test database is isolated
- Check for test data conflicts
- Verify mocks are properly configured
- Run tests individually to isolate issues

**Performance Issues**:
- Check cache hit rates in logs
- Monitor database query performance
- Profile API endpoint response times
- Review OpenAI token usage

### Debug Commands
```bash
# Backend debugging
cd backend
python -c "from app.database import get_db; print('DB connection OK')"
python -c "import app.services.data_aggregation_service; print('Services OK')"

# Frontend debugging
cd frontend
npm run build  # Check for build errors
npm run lint:fix  # Auto-fix linting issues
```

---

## Key Files and Locations

### Configuration Files
- `backend/.env` - Environment variables
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `docker-compose.yml` - Container orchestration

### Core Services
- `backend/app/services/picklist_generator_service.py` - Main orchestrator
- `backend/app/services/data_aggregation_service.py` - Data loading
- `backend/app/services/team_analysis_service.py` - Team ranking
- `backend/app/services/picklist_gpt_service.py` - AI integration

### API Endpoints
- `backend/app/api/v1/endpoints/picklist.py` - Main API
- `backend/app/api/v1/endpoints/teams.py` - Team operations
- `backend/app/main.py` - FastAPI application

### Frontend Components
- `frontend/src/components/` - React components
- `frontend/src/hooks/` - Custom hooks
- `frontend/src/services/` - API integration
- `frontend/src/types/` - TypeScript definitions

---

## Development Workflow

### Feature Development
1. Create feature branch: `git checkout -b feature/feature-name`
2. Write tests first (TDD approach)
3. Implement feature following established patterns
4. Run quality checks and ensure all tests pass
5. Update documentation
6. Create PR with comprehensive description
7. Address review feedback
8. Merge after approval

### Bug Fixes
1. Create bug branch: `git checkout -b fix/bug-description`
2. Write test that reproduces the bug
3. Fix the issue
4. Ensure fix doesn't break existing functionality
5. Add regression test if needed
6. Follow same PR process as features

### Code Review Checklist
- [ ] Follows coding standards and patterns
- [ ] Has comprehensive tests (>90% coverage)
- [ ] Includes proper error handling and logging
- [ ] Performance requirements met
- [ ] Documentation updated
- [ ] Security considerations addressed

---

## Quick Command Reference

### Development Commands
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run quality checks (backend)
cd backend
pytest --cov=app --cov-report=html
black app/ tests/ --check
flake8 app/ tests/
mypy app/

# Run quality checks (frontend)
cd frontend
npm run lint
npm run type-check
npm test -- --coverage

# Database operations
cd backend
python -m app.database.init_db  # Initialize database
python -m app.database.load_sample_data  # Load test data
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Standard commit flow
git add .
git commit -m "feat: add new feature with comprehensive tests

- Implement new service following established patterns
- Add comprehensive test coverage (>90%)
- Update documentation and API contracts
- Include performance optimizations

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push and create PR
git push origin feature/new-feature
```

---

## Success Criteria

### Feature Completion Checklist
- [ ] Service implementation follows established patterns
- [ ] API endpoints have comprehensive validation
- [ ] Frontend components handle all states (loading, error, success)
- [ ] Test coverage >90% for all new code
- [ ] Performance requirements met (<200ms API, <5s services)
- [ ] Documentation updated (code, API, architecture)
- [ ] Security review completed
- [ ] Code review approved by team

### Quality Gates
- [ ] All automated tests pass
- [ ] Code formatting and linting clean
- [ ] Type checking passes without errors
- [ ] Security scan shows no new vulnerabilities
- [ ] Performance benchmarks maintained
- [ ] Documentation is complete and accurate

---

**Remember**: This project prioritizes code quality, comprehensive testing, and clear documentation. When in doubt, follow the established patterns and ask for clarification rather than deviating from proven approaches.

**Documentation Links**:
- [Complete Documentation](docs/) - Full documentation framework
- [AI Development Guide](docs/05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md) - AI-specific guidance
- [Service Contracts](docs/05_AI_FRAMEWORK/SERVICE_CONTRACTS.md) - Machine-readable specifications
- [Coding Standards](docs/04_DEVELOPMENT_GUIDES/CODING_STANDARDS.md) - Detailed coding guidelines
- [Testing Guide](docs/04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md) - Complete testing strategy