# AGENTS.md

## Role

You are an AI coding assistant working on this Python project.
Focus on small, incremental changes and avoid unnecessary abstractions or rewrites.

## How to run the project

- Create venv: `uv venv`
- Activate venv (Unix): `source .venv/bin/activate`
- Activate venv (Windows): `.venv\Scripts\activate`
- Install dependencies: `uv sync`
- Run tests: `pytest`
- Lint: `ruff check .`  # or `flake8 .`
- Format: `ruff format .`  # or `black .`

Only use these commands unless explicitly asked for something else.

## Project layout

- `backend/` – main backend application code
- `frontend/` - main frontend application code
- `integrations/`- main third party systems integratin with the chatbot
- `docker/`- main docker infra with the files to run psql database, redis cache memory, etc

When adding new code, prefer placing it in an existing module instead of creating new top-level folders.

## Coding style (keep it simple)

- Use type hints for public functions, but do not refactor large areas just to add types.
- Prefer straightforward, readable code over “clever” patterns.
- Avoid introducing new dependencies unless requested.
- Do not create extra layers (managers, factories, base classes) unless there is a clear, current need.

## Boundaries

Always do (no need to ask):
- Run tests for files you modify.
- Keep changes small and focused on the current task.
- Improve or add tests when changing behavior.

Ask first:
- Adding new third-party libraries.
- Large refactors, new architectures, or new folders.
- Changes to CI/CD, production configs, or database schemas.

Never do:
- Remove existing tests without replacing them.
- Perform repo-wide rewrites or mass renames on your own.
- Send any secrets or private data outside this repository.
