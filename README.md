# clusters-metadata-api

Canonical metadata service for managed clusters.

## Apps

- `src/app/main.py`: internal M4W API
- `src/app/partner.py`: external partner read-only API

## Local Setup

1. Install `uv`.
2. Create a local env file from `.env.example`.
3. Sync dependencies with `uv sync --frozen --all-groups`.

## Local Commands

- Run the internal API: `PYTHONPATH=src uv run uvicorn app.main:app --reload`
- Run the partner API: `PYTHONPATH=src uv run uvicorn app.partner:app --reload --port 8001`
- Run tests: `uv run pytest`
- Run Ruff: `uv run ruff check src tests migrations`
- Generate OpenAPI: `PYTHONPATH=src uv run python scripts/generate_openapi_spec.py`
- Generate SDK: `bash scripts/generate_sdk.sh`

## Docker Compose

- Start services: `docker compose up --build`
- Internal API: `http://localhost:8000`
- Partner API: `http://localhost:8001`

## CI Workflows

- `.github/workflows/ci-checks.yaml`
- `.github/workflows/openapi-check.yml`
- `.github/workflows/publish-clusters-metadata-sdk-preview.yml`
- `.github/workflows/publish-clusters-metadata-sdk-release.yml`

## Debugging

See `DEBUGGING.md` for VS Code launch/debug instructions.
