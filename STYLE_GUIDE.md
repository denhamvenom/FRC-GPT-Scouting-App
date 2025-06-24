# Style Guide

## Python
* Black (`line‑length 100`) and isort enforced
* Strict type hints; mypy clean in CI
* Google‑style docstrings on all public funcs / classes
* One logical class/function per file when practical
* Descriptive variable names and clear function signatures
* Exception handling with specific error messages
* Use `async`/`await` for I/O operations
* Thread safety considerations for progress tracking

## React/TypeScript
* Functional components with hooks (no class components)
* Props and state interfaces clearly defined
* React Router for navigation with proper types
* Tailwind CSS for styling with consistent class usage
* Component organization by feature
* Custom hooks for shared logic
* Error boundaries for graceful error handling
* LocalStorage with proper serialization

## Database
* SQLAlchemy models with clear relationships
* Migrations documented and versioned
* Use transactions for multi-step operations
* Indexes on foreign keys and frequently queried fields
* Soft deletes where appropriate

## API Design
* RESTful endpoints with consistent naming
* Proper HTTP status codes
* Request/response validation with Pydantic
* Comprehensive error messages
* Pagination for large datasets
* Progress endpoints for long operations

## Folder Naming
* `backend/app/api`  – FastAPI routers only
* `backend/app/services` – logic helpers, no FastAPI imports
* `backend/app/database` – SQLAlchemy models and config
* `backend/app/config` – JSON/YAML configs
* `backend/tests` – pytest files mirroring service structure
* `frontend/src/pages` – Full page components
* `frontend/src/components` – Reusable UI components
* `frontend/src/services` – API client code

## Commit Messages
```
<scope>: <imperative summary>

Body: what & why (wrap ≤ 72 chars).  
Refs: #issue
```
Example: `picklist: add progress tracking for generation #42`

## Code Organization
* Services should be stateless and focused on a single responsibility
* API endpoints should be thin wrappers around service functions
* Frontend state should be managed at the appropriate level (page or component)
* Use TypeScript interfaces for shared data structures
* Common utilities should be extracted to separate modules
* Progress tracking should be non-blocking

## Testing
* `pytest -q`, no external API hits in unit tests (use fixtures)
* Integration tests marked `@pytest.mark.integration` may hit TBA/Statbotics
* Frontend components should have basic render tests
* Mock external services in tests
* Test error conditions and edge cases
* Progress tracking should be tested with mock timers

## Error Handling
* Use specific exception types
* Log errors with context
* Provide user-friendly error messages
* Implement retry logic for transient failures
* Graceful degradation when services unavailable

## Performance
* Cache frequently accessed data
* Use pagination for large datasets
* Optimize database queries (avoid N+1)
* Compress large JSON responses
* Use threading for blocking operations
* Progress updates at reasonable intervals

## Security
* Environment variables for secrets
* Input validation on all endpoints
* SQL injection prevention with ORM
* XSS prevention in React
* CORS properly configured
* API rate limiting

## Documentation
* README with setup instructions
* API documentation with examples
* Architecture diagrams updated
* Changelog maintained
* Inline comments for complex logic
* Progress tracking documented

## UI/UX Guidelines
* Loading states for all async operations
* Progress indicators for long operations
* Error messages with recovery actions
* Confirmation dialogs for destructive actions
* Keyboard shortcuts documented
* Mobile responsive design
* Accessible color contrast

## Git Workflow
* Feature branches from main
* PR reviews required
* Tests must pass before merge
* Squash commits on merge
* Tag releases with semver
* Keep commit history clean