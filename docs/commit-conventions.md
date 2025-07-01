# Commit Message Conventions

Based on the error message, this project requires commit messages to start with a task ID in square brackets.

## Format

```
[CATEGORY-NUMBER] Brief description

Optional longer description
```

## Categories

- **BE**: Backend tasks
- **FE**: Frontend tasks  
- **INF**: Infrastructure tasks
- **ALL**: General/cross-cutting tasks

## Examples

```
[BE-001] Add health check endpoint
[FE-003] Create form component
[INF-002] Configure Terraform
[ALL-001] Update documentation
```

## For Team Tasks

Since Teams Alpha and Beta don't have specific task IDs in this format, we can use:

- Team Alpha (Backend/AI): Use `[BE-XXX]` prefix
- Team Beta (Frontend/Infrastructure): Use `[FE-XXX]` or `[INF-XXX]` prefix

Example mappings:
- α-1 through α-13 → `[BE-001]` through `[BE-013]`
- β-1 through β-5 (infrastructure) → `[INF-001]` through `[INF-005]`
- β-6 through β-15 (frontend/integration) → `[FE-001]` through `[FE-010]`