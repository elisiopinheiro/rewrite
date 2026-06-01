# clusters-metadata-api

Canonical metadata service for managed clusters. It runs alongside the legacy
`clusters-4wm` service against the **same** database during the migration window
(see `REWRITE_REVIEW.md`).

## Apps

- `src/app/main.py`: internal M4W API (`app.main:app`)
- `src/app/partner.py`: external partner read-only API (`app.partner:app`)

Both expose `/healthz` (liveness) and `/readyz` (readiness, checks the DB). The
M4W app also serves Prometheus metrics at `/metrics`.

## Local Setup

1. Install `uv`.
2. (Optional) Copy `.env.example` to `.env` and adjust — the apps also run on
   safe local defaults without it.
3. Sync dependencies: `uv sync --frozen --all-groups`.

## Local Commands

- Run the internal API: `PYTHONPATH=src uv run uvicorn app.main:app --reload`
- Run the partner API: `PYTHONPATH=src uv run uvicorn app.partner:app --reload --port 8001`
- Apply migrations: `uv run alembic upgrade head`
- Run tests: `uv run pytest`
- Lint: `uv run ruff check src tests migrations` and `uv run ruff format src tests migrations`
- Type check: `uv run mypy src`
- Generate OpenAPI: `PYTHONPATH=src uv run python scripts/generate_openapi_spec.py`
- Generate SDK: `bash scripts/generate_sdk.sh`

## Docker Compose

`docker compose up --build` starts Postgres, runs migrations once (the `migrate`
service), then the apps:

- Internal API: `http://localhost:8000`
- Partner API: `http://localhost:8001`

## CI

- `.github/workflows/ci.yaml`: lint (ruff), type check (mypy), tests (pytest),
  and an OpenAPI freshness check.

SDK generation (`scripts/generate_sdk.sh`) is run manually for now.

## Debugging

See `DEBUGGING.md` for VS Code launch/debug instructions.
