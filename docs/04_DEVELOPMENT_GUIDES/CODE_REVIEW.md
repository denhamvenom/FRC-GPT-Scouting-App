# Code Review Guide

**Purpose**: Comprehensive code review process and quality standards  
**Audience**: Developers, reviewers, and AI assistants  
**Scope**: Code review workflow, standards, and automated quality checks  

---

## Code Review Philosophy

The FRC GPT Scouting App uses **systematic code review** to ensure code quality, knowledge sharing, and continuous improvement while supporting AI-assisted development.

### Core Review Principles
- **Quality First**: Every line of code is reviewed before merging
- **Educational**: Reviews are learning opportunities for all participants
- **Constructive**: Feedback is specific, actionable, and respectful
- **Efficient**: Reviews are timely and focused on what matters
- **AI-Aware**: Special considerations for AI-generated and AI-assisted code
- **Standards-Driven**: Consistent application of coding standards

---

## Review Process Overview

### Review Workflow

```
1. Developer Creates PR
   ├── Self-review and checklist completion
   ├── Automated quality checks run
   └── Request reviewers

2. Automated Validation
   ├── Code formatting (Prettier, Black)
   ├── Linting (ESLint, flake8)
   ├── Type checking (TypeScript, mypy)
   ├── Test execution and coverage
   └── Security scanning

3. Human Review
   ├── Code functionality and logic
   ├── Architecture and design patterns
   ├── Test quality and coverage
   ├── Documentation completeness
   └── Performance considerations

4. Review Resolution
   ├── Address reviewer feedback
   ├── Re-run automated checks
   ├── Obtain approval from required reviewers
   └── Merge when all criteria met
```

### Review Roles and Responsibilities

**Author Responsibilities**:
- Complete self-review before requesting review
- Provide clear PR description and context
- Respond promptly to reviewer feedback
- Ensure all automated checks pass
- Update documentation as needed

**Reviewer Responsibilities**:
- Review within 24 hours of request
- Provide specific, actionable feedback
- Focus on important issues (not nitpicks)
- Approve when quality standards are met
- Ask questions when context is unclear

**Maintainer Responsibilities**:
- Ensure review standards are followed
- Make final merge decisions
- Resolve conflicts between reviewers
- Update review guidelines as needed

---

## Review Checklist

### Pre-Review Checklist (Author)

**Before Requesting Review**:
- [ ] Self-review completed (read through all changes)
- [ ] All automated quality checks passing
- [ ] Tests written and passing (>90% coverage for new code)
- [ ] Documentation updated (code comments, README, API docs)
- [ ] PR description clearly explains what and why
- [ ] Breaking changes are identified and documented
- [ ] Security implications considered and addressed

**PR Description Template**:
```markdown
## Summary
Brief description of what this PR does and why.

## Changes Made
- List of specific changes
- New features or capabilities added
- Bug fixes implemented
- Refactoring performed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Edge cases tested

## Documentation
- [ ] Code comments added where needed
- [ ] API documentation updated
- [ ] README or guides updated
- [ ] Architecture docs updated (if applicable)

## Breaking Changes
- None / List breaking changes

## AI Assistance
- [ ] AI-generated code reviewed and validated
- [ ] AI-assisted development documented
- [ ] Quality standards applied to AI contributions

## Related Issues
Fixes #123, Related to #456
```

### Code Quality Checklist

**Functionality**:
- [ ] Code solves the intended problem correctly
- [ ] Edge cases and error conditions are handled
- [ ] Input validation is comprehensive
- [ ] Business logic is sound and defensible
- [ ] Integration points work as expected

**Design and Architecture**:
- [ ] Code follows established architectural patterns
- [ ] Service boundaries are respected
- [ ] Dependencies are appropriate and minimal
- [ ] Abstractions are well-designed
- [ ] Code is modular and reusable

**Code Quality**:
- [ ] Follows coding standards (see [Coding Standards](CODING_STANDARDS.md))
- [ ] Naming is clear and descriptive
- [ ] Functions and classes have single responsibilities
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Comments explain why, not what

**Performance**:
- [ ] No obvious performance bottlenecks
- [ ] Database queries are optimized
- [ ] Caching is used appropriately
- [ ] Memory usage is reasonable
- [ ] API response times are acceptable

**Security**:
- [ ] Input sanitization and validation
- [ ] No hardcoded secrets or credentials
- [ ] Authentication and authorization handled properly
- [ ] SQL injection prevention
- [ ] XSS prevention (frontend)

**Testing**:
- [ ] Test coverage is >90% for new code
- [ ] Tests are meaningful and test real scenarios
- [ ] Both positive and negative test cases
- [ ] Integration tests for service interactions
- [ ] Mocking is appropriate and realistic

---

## Python Backend Review Standards

### Code Structure Review

**Service Implementation**:
```python
# ✅ Good: Clear service structure following patterns
class DataAggregationService:
    """
    Service for unified data loading and preparation.
    
    Follows established service patterns with proper error handling,
    logging, and performance considerations.
    """
    
    def __init__(self, dataset_path: str) -> None:
        """Initialize with comprehensive validation."""
        self._validate_dataset_path(dataset_path)
        self.dataset_path = Path(dataset_path)
        self.teams_data = self._load_dataset()
        logger.info(f"Initialized {self.__class__.__name__} with {len(self.teams_data)} teams")
    
    def get_teams_for_analysis(self, 
                              exclude_teams: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get filtered teams with proper error handling."""
        try:
            self._validate_input(exclude_teams)
            result = self._filter_teams(exclude_teams)
            logger.info(f"Filtered teams: {len(result)} remaining")
            return result
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ServiceError(f"Failed to get teams: {e}")

# ❌ Poor: Missing error handling, logging, validation
class BadService:
    def __init__(self, path):
        self.data = json.load(open(path))  # No error handling
    
    def get_data(self, filter=None):  # No type hints
        return [x for x in self.data if x != filter]  # Unclear logic
```

**Error Handling Review**:
```python
# ✅ Good: Comprehensive error handling
def process_team_data(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process team data with comprehensive error handling."""
    try:
        # Input validation
        if not team_data:
            raise ValueError("Team data cannot be empty")
        
        required_fields = ['team_number', 'nickname']
        missing_fields = [field for field in required_fields if field not in team_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Processing logic
        result = self._transform_data(team_data)
        
        # Success logging
        logger.info(f"Successfully processed team {team_data.get('team_number')}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in {self.__class__.__name__}: {e}")
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise ServiceError(f"Failed to process team data: {e}")

# ❌ Poor: No error handling
def bad_process(self, data):
    return data['team_number'] * 2  # Will crash if key missing
```

### API Endpoint Review

**FastAPI Endpoint Structure**:
```python
# ✅ Good: Complete endpoint with validation, docs, error handling
@router.post("/picklist/generate", 
             response_model=PicklistResponse,
             summary="Generate team picklist",
             description="Generate ranked team picklist based on priorities and constraints")
async def generate_picklist(
    request: PicklistRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> PicklistResponse:
    """
    Generate picklist with comprehensive validation and error handling.
    
    Args:
        request: Picklist generation request with team number, priorities, etc.
        background_tasks: For async operations like cache warming
        current_user: Authenticated user context
        
    Returns:
        PicklistResponse with ranked teams and analysis
        
    Raises:
        HTTPException: For validation errors, service failures, etc.
    """
    try:
        # Input validation (handled by Pydantic model)
        logger.info(f"Generating picklist for team {request.your_team_number}")
        
        # Service call with proper error handling
        result = await picklist_service.generate_picklist(
            your_team_number=request.your_team_number,
            pick_position=request.pick_position,
            priorities=request.priorities,
            exclude_teams=request.exclude_teams
        )
        
        # Background task for analytics
        background_tasks.add_task(track_picklist_generation, request, current_user.id)
        
        return PicklistResponse(
            status="success",
            data=result,
            metadata={
                "request_id": str(uuid.uuid4()),
                "processing_time": result.get("processing_time"),
                "cached": result.get("cached", False)
            }
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HTTPException(status_code=500, detail="Internal service error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ❌ Poor: No validation, documentation, or error handling
@router.post("/bad_endpoint")
def bad_endpoint(data):
    return service.process(data)  # Many issues here
```

---

## TypeScript Frontend Review Standards

### Component Review

**React Component Structure**:
```tsx
// ✅ Good: Well-structured component with types, error handling
import React, { useState, useCallback, useMemo } from 'react';
import { TeamData, Priority } from '../types';
import { usePicklistGeneration } from '../hooks/usePicklistGeneration';

interface PicklistGeneratorProps {
  teamNumber: number;
  onPicklistGenerated: (results: PicklistResults) => void;
  className?: string;
}

/**
 * Picklist generator component with comprehensive form handling.
 * 
 * Provides interface for configuring priorities and generating
 * team rankings with real-time validation and error handling.
 */
export const PicklistGenerator: React.FC<PicklistGeneratorProps> = ({
  teamNumber,
  onPicklistGenerated,
  className = ''
}) => {
  // State management
  const [priorities, setPriorities] = useState<Priority[]>([]);
  const [excludeTeams, setExcludeTeams] = useState<number[]>([]);
  const [pickPosition, setPickPosition] = useState<'first' | 'second' | 'third'>('first');

  // Custom hook for API integration
  const {
    generatePicklist,
    isLoading,
    error,
    clearError
  } = usePicklistGeneration();

  // Memoized calculations
  const isFormValid = useMemo(() => {
    return priorities.length > 0 && 
           priorities.every(p => p.weight > 0) &&
           teamNumber > 0;
  }, [priorities, teamNumber]);

  // Event handlers
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!isFormValid) {
      return;
    }

    try {
      const results = await generatePicklist({
        your_team_number: teamNumber,
        pick_position: pickPosition,
        priorities,
        exclude_teams: excludeTeams
      });
      
      onPicklistGenerated(results);
    } catch (error) {
      // Error handling done by hook
      console.error('Picklist generation failed:', error);
    }
  }, [teamNumber, pickPosition, priorities, excludeTeams, generatePicklist, onPicklistGenerated, isFormValid, clearError]);

  const handleAddPriority = useCallback(() => {
    setPriorities(prev => [...prev, {
      metric: 'autonomous_score',
      weight: 1,
      description: ''
    }]);
  }, []);

  // Render with proper error boundaries
  return (
    <form onSubmit={handleSubmit} className={`picklist-generator ${className}`}>
      {error && (
        <div className="error-banner" role="alert">
          Error: {error.message}
        </div>
      )}
      
      <div className="form-section">
        <label htmlFor="pick-position">Pick Position</label>
        <select
          id="pick-position"
          value={pickPosition}
          onChange={(e) => setPickPosition(e.target.value as any)}
          required
        >
          <option value="first">First Pick</option>
          <option value="second">Second Pick</option>
          <option value="third">Third Pick</option>
        </select>
      </div>

      {/* Priority configuration */}
      <PrioritySection
        priorities={priorities}
        onChange={setPriorities}
        onAdd={handleAddPriority}
      />

      <button
        type="submit"
        disabled={!isFormValid || isLoading}
        className="submit-button"
      >
        {isLoading ? 'Generating...' : 'Generate Picklist'}
      </button>
    </form>
  );
};

// ❌ Poor: No types, error handling, or proper structure
export function BadComponent(props) {
  const [data, setData] = useState();
  
  function handleClick() {
    fetch('/api/data').then(r => r.json()).then(setData);  // No error handling
  }
  
  return <div onClick={handleClick}>{data}</div>;  // Many issues
}
```

**API Service Review**:
```typescript
// ✅ Good: Comprehensive API service with error handling
class PicklistApiService {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = '/api/v1', timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Generate picklist with comprehensive error handling.
   */
  async generatePicklist(request: PicklistRequest): Promise<PicklistData> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/picklist/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      const data: ApiResponse<PicklistData> = await response.json();
      
      if (data.status === 'error') {
        throw new ApiError(data.error || 'API request failed', 400);
      }

      return data.data!;
    } catch (error) {
      if (error instanceof AbortError) {
        throw new ApiError('Request timeout', 408);
      }
      
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0
      );
    }
  }

  /**
   * Type-safe error class for API errors.
   */
  private handleApiError(response: Response, data: any): never {
    const message = data.detail || data.error || `HTTP ${response.status}`;
    throw new ApiError(message, response.status, data);
  }
}

// ❌ Poor: No error handling, typing, or structure
async function badApiCall(data) {
  const response = await fetch('/api/endpoint', {
    method: 'POST',
    body: JSON.stringify(data)  // No content-type, error handling, etc.
  });
  return response.json();  // Will crash on error responses
}
```

---

## AI-Generated Code Review

### Special Considerations for AI Code

**AI Code Identification**:
- AI-generated code must be clearly identified in PRs
- Include which AI tool was used (Claude Code, GitHub Copilot, etc.)
- Document prompts or context provided to AI
- Identify human modifications to AI output

**AI Code Quality Standards**:
```python
# ✅ Good: AI-generated code properly reviewed and documented
# Generated by: Claude Code
# Prompt: "Create a service for team priority calculations with normalization"
# Human modifications: Added custom validation logic, improved error messages

class PriorityCalculationService:
    """
    AI-generated service for priority calculations.
    
    Generated with Claude Code and enhanced with custom validation
    logic and improved error handling patterns.
    """
    
    def normalize_priorities(self, priorities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize priority weights to sum to 1.0.
        
        AI-generated with human validation and enhancement.
        """
        try:
            # AI-generated validation
            if not priorities:
                raise ValueError("Priorities list cannot be empty")
            
            # Human addition: Enhanced validation
            for i, priority in enumerate(priorities):
                if 'weight' not in priority:
                    raise ValueError(f"Priority {i} missing 'weight' field")
                if not isinstance(priority['weight'], (int, float)):
                    raise ValueError(f"Priority {i} weight must be numeric")
                if priority['weight'] <= 0:
                    raise ValueError(f"Priority {i} weight must be positive")
            
            # AI-generated normalization logic (verified by human)
            total_weight = sum(p['weight'] for p in priorities)
            
            normalized = []
            for priority in priorities:
                normalized_priority = priority.copy()
                normalized_priority['weight'] = priority['weight'] / total_weight
                normalized_priority['original_weight'] = priority['weight']
                normalized.append(normalized_priority)
            
            return normalized
            
        except Exception as e:
            # Human addition: Improved error handling
            logger.error(f"Priority normalization failed: {e}")
            raise
```

**AI Code Review Checklist**:
- [ ] AI-generated logic is sound and correct
- [ ] All edge cases are handled appropriately
- [ ] Error handling follows project patterns
- [ ] Code integrates properly with existing architecture
- [ ] Performance implications are acceptable
- [ ] Security considerations are addressed
- [ ] Tests cover AI-generated functionality thoroughly
- [ ] Documentation explains AI assistance used

---

## Review Feedback Guidelines

### Providing Effective Feedback

**Constructive Feedback Examples**:

```markdown
✅ Good Feedback:
"Consider using a more descriptive variable name here. `team_analysis_result` 
would be clearer than `result` since this method processes multiple types of data."

"This error handling looks good, but we should also log the team_number 
for debugging. Consider adding: logger.error(f'Processing failed for team {team_number}: {e}')"

"The logic here is correct, but this could be simplified using a list comprehension:
`filtered_teams = [team for team in teams if team['score'] > threshold]`"

❌ Poor Feedback:
"This is wrong."
"Bad naming."
"Fix this."
```

**Feedback Categories**:

**Must Fix (Blocking)**:
- Security vulnerabilities
- Functional bugs
- Breaking changes without documentation
- Missing critical tests
- Performance regressions

**Should Fix (Important)**:
- Code quality issues
- Missing documentation
- Inconsistent patterns
- Test coverage gaps
- Unclear naming

**Could Fix (Suggestions)**:
- Code style improvements
- Performance optimizations
- Alternative approaches
- Future considerations

### Responding to Feedback

**Author Response Guidelines**:

**Accepting Feedback**:
```markdown
✅ Good Response:
"Good catch! I've updated the variable name and added the team_number to 
the error logging. The logic is much clearer now."

"You're right about the security concern. I've added input validation 
and updated the tests to cover the edge case you identified."

❌ Poor Response:
"This works fine."
"I disagree."
"Will fix later."
```

**Disagreeing Constructively**:
```markdown
✅ Good Disagreement:
"I understand the concern about performance, but I think the clarity 
benefit outweighs the minimal performance cost here. The method is only 
called once per request, and the readability improvement helps with 
maintainability. What do you think?"

"That's a good suggestion for the future, but for this PR I think the 
current approach aligns better with our existing patterns. Could we 
create a follow-up issue to refactor this as part of a larger 
architecture improvement?"
```

---

## Automated Quality Checks

### Backend Quality Pipeline

**pytest and Coverage**:
```bash
# Run all quality checks
pytest --cov=app --cov-report=term-missing --cov-fail-under=90

# Type checking
mypy app/ --strict

# Code formatting
black app/ tests/ --check

# Import sorting
isort app/ tests/ --check-only

# Linting
flake8 app/ tests/

# Security scanning
bandit -r app/
```

**Pre-commit Configuration**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, app/]
```

### Frontend Quality Pipeline

**TypeScript and Linting**:
```bash
# Type checking
tsc --noEmit

# Linting
eslint src/ --ext .ts,.tsx

# Formatting check
prettier --check src/

# Tests with coverage
npm test -- --coverage --watchAll=false
```

**Quality Gate Configuration**:
```json
{
  "scripts": {
    "quality-check": "npm run type-check && npm run lint && npm run test:coverage && npm run format:check",
    "type-check": "tsc --noEmit",
    "lint": "eslint src/ --ext .ts,.tsx --max-warnings 0",
    "format:check": "prettier --check src/",
    "test:coverage": "npm test -- --coverage --watchAll=false --coverageThreshold='{\"global\":{\"branches\":80,\"functions\":80,\"lines\":80,\"statements\":80}}'"
  }
}
```

---

## Review Metrics and Monitoring

### Review Quality Metrics

**Tracking Review Effectiveness**:
- Average time from PR creation to first review
- Average time from PR creation to merge
- Number of review rounds per PR
- Post-merge bug discovery rate
- Review participation across team members

**Quality Indicators**:
- Test coverage percentage
- Automated check pass rate
- Security scan results
- Performance regression detection
- Documentation completeness

### Review Process Improvement

**Regular Review Retrospectives**:
- Monthly review of review metrics
- Identification of common issues
- Process improvement suggestions
- Tool and automation enhancements

**Common Review Issues and Solutions**:

| Issue | Solution |
|-------|----------|
| Reviews taking too long | Set SLA targets, assign backup reviewers |
| Inconsistent feedback | Provide reviewer training, update guidelines |
| Missing edge cases | Improve test requirements, add edge case checklist |
| Architecture concerns late in process | Earlier design reviews, architecture approval gates |
| AI code quality issues | Enhanced AI code review checklist, specific training |

---

## Review Tools and Integration

### GitHub Integration

**Required Status Checks**:
```yaml
# .github/branch_protection.yml
required_status_checks:
  - "Backend Tests"
  - "Frontend Tests"
  - "Type Checking"
  - "Security Scan"
  - "Coverage Check"

required_reviews:
  required_reviewers: 2
  dismiss_stale_reviews: true
  require_code_owner_reviews: true
```

**Review Templates**:
```markdown
<!-- .github/pull_request_template.md -->
## Review Checklist

### Functionality
- [ ] Code solves the intended problem
- [ ] Edge cases are handled
- [ ] Error conditions are managed appropriately

### Quality
- [ ] Follows coding standards
- [ ] Naming is clear and descriptive
- [ ] Code is well-structured and maintainable

### Testing
- [ ] Tests are comprehensive (>90% coverage)
- [ ] Tests cover both positive and negative cases
- [ ] Integration tests verify service interactions

### Documentation
- [ ] Code is self-documenting with clear comments
- [ ] API documentation is updated
- [ ] Architecture docs updated if needed

### AI Code (if applicable)
- [ ] AI-generated code is clearly identified
- [ ] AI code has been reviewed and validated
- [ ] Human modifications are documented
```

### IDE Integration

**VS Code Review Extensions**:
- GitHub Pull Requests and Issues
- GitLens for git blame and history
- Code Review for inline comments
- Better Comments for comment highlighting

**Review Shortcuts and Automation**:
```json
{
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true
}
```

---

**Next Steps**: [Feature Development Guide](FEATURE_DEVELOPMENT.md) | [Testing Guide](TESTING_GUIDE.md) | [AI Development Guide](../05_AI_FRAMEWORK/AI_DEVELOPMENT_GUIDE.md)

---

**Last Updated**: June 25, 2025  
**Maintainer**: Development Team  
**Related Documents**: [Coding Standards](CODING_STANDARDS.md), [Testing Guide](TESTING_GUIDE.md), [Service Architecture](../03_ARCHITECTURE/SERVICE_ARCHITECTURE.md)