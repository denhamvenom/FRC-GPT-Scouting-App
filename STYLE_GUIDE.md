# Style Guide

## Python
* Black (`line‑length 100`) and isort enforced
* Strict type hints; mypy clean in CI
* Google‑style docstrings on all public funcs / classes
* One logical class/function per file when practical
* Descriptive variable names and clear function signatures
* Exception handling with specific error messages

## React/TypeScript
* Functional components with hooks
* Props and state interfaces clearly defined
* React Router for navigation
* Tailwind CSS for styling with consistent class usage
* Component organization by feature

## Folder Naming
* `backend/app/api`  – FastAPI routers only
* `backend/app/services` – logic helpers, no FastAPI imports
* `backend/app/config` – JSON/YAML configs
* `backend/tests` – pytest files mirroring service structure
* `frontend/src/pages` – Full page components
* `frontend/src/components` – Reusable UI components

## Commit Messages
```
<scope>: <imperative summary>

Body: what & why (wrap ≤ 72 chars).  
Refs: #issue
```
Example: `validation: add outlier‑threshold slider #31`

## Code Organization
* Services should be stateless and focused on a single responsibility
* API endpoints should be thin wrappers around service functions
* Frontend state should be managed at the appropriate level (page or component)
* Use TypeScript interfaces for shared data structures
* Common utilities should be extracted to separate modules

## Testing
* `pytest -q`, no external API hits in unit tests (use fixtures)
* Integration tests marked `@pytest.mark.integration` may hit TBA/Statbotics
* Frontend components should have basic render tests