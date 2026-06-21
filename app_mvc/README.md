# Feature-Based MVC Blueprint

This package is a clean architectural blueprint for evolving the current project into a feature-based MVC structure with repository support.

## Goals

- keep shared infrastructure inside `core/`
- keep each feature isolated behind its own `view`, `controller`, `repo`, and `service` boundaries
- support dependency injection explicitly
- keep transport logic, business logic, persistence logic, and provider integrations separate
- provide documentation-first scaffolding without implementation details

## Top-Level Structure

```text
app_mvc/
  core/
  features/
    auth/
    session/
    websocket/
```

## Layer Responsibilities

- `view/`: FastAPI REST or WebSocket entrypoints only
- `controller/`: application use-case orchestration
- `repo/`: persistence and database access contracts/implementations
- `service/`: domain services or external-provider abstractions
- `core/`: shared configuration, database, security, dependency injection, routing, schemas, and failures

## Notes

- This package is intentionally non-executable scaffolding.
- Every class and method contains only signatures and documentation.
- Concrete implementation should be added later while keeping the boundaries defined here intact.
