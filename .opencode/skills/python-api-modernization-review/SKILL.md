---
name: python-api-modernization-review
description: Review, simplify, cleanup, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, uv, Docker, Compose, Helm, OpenAPI, SDK generation, GitHub Actions, release automation, routers, schemas, services, repositories, models. Use when auditing or refactoring a code or repo-tooling chunk of this Python API for current best practices and low-risk simplification.
---

# Python API Modernization Review

Use this skill to review or refactor one chunk at a time. A chunk can be a file, folder, layer, endpoint family, model group, or one concern such as settings, validation, transactions, queries, tests, packaging, migrations, CI, containerization, deployment config, release automation, or SDK generation.

## Goals

- simplify existing code without broad rewrites
- simplify repo tooling and automation without broad process churn
- align touched code with current official docs for FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, pytest, Ruff, and Python 3.12
- align touched repo tooling with current official docs for uv, GitHub Actions, Docker Compose, Helm, Dependabot, pre-commit, and SDK tooling
- keep API behavior stable unless the user asks for a behavior change
- keep build, release, deployment, and automation behavior stable unless the user asks for a workflow change
- prefer smaller, safer edits over architectural churn

## Repo Context

- Python `>=3.12`
- app code lives in `src/app`
- entrypoints:
  - `src/app/main.py`
  - `src/app/partner.py`
- layers:
  - `api`
  - `schemas`
  - `services`
  - `repositories`
  - `models`
  - `core`
- tooling:
  - dependency/runtime: `uv`
  - lint: `ruff`
  - type checking: `mypy --strict`
  - tests: `pytest`
  - migrations: `alembic`
  - CI/CD: GitHub Actions
  - container/dev runtime: Dockerfile + `compose.yaml`
  - deployment: Helm chart under `applications/clusters-metadata-api`
  - contract + SDK: `openapi.json`, `scripts/generate_openapi_spec.py`, `scripts/generate_sdk.sh`, `sdk-config.yml`
- `openapi.json` is checked in and should be regenerated only when API contract changes are intentional
- the current stack is already on current major versions; do not recommend upgrades for their own sake

## How To Work

1. Scope the chunk first.
   - If the user did not name a chunk, ask one short question to narrow the review to a file, folder, layer, or concern.
   - If the request is too broad, propose the smallest meaningful slice first.

2. Read before changing.
   - Inspect the relevant implementation, neighboring types, dependencies, and tests.
   - Read migrations or OpenAPI artifacts if the change touches DB shape or API contract.

3. Verify guidance against official docs.
   - Fetch the relevant official docs pages before finalizing recommendations or edits.
   - Prefer official docs over blogs, forum posts, or memory.
   - Default references:
     - Pydantic: `https://docs.pydantic.dev/latest/`
     - FastAPI: `https://fastapi.tiangolo.com/`
     - SQLAlchemy ORM 2.0: `https://docs.sqlalchemy.org/en/20/`
     - Alembic: `https://alembic.sqlalchemy.org/en/latest/`
     - Pytest: `https://docs.pytest.org/en/latest/`
     - Ruff: `https://docs.astral.sh/ruff/`
     - uv: `https://docs.astral.sh/uv/`
     - GitHub Actions: `https://docs.github.com/en/actions`
     - Docker Compose: `https://docs.docker.com/compose/`
     - Helm: `https://helm.sh/docs/`
     - openapi-python-client: `https://github.com/openapi-generators/openapi-python-client`
     - pre-commit: `https://pre-commit.com/`
     - Dependabot: `https://docs.github.com/en/code-security/dependabot`
     - release-please: `https://github.com/googleapis/release-please`

4. Review in this order.
   - correctness and regressions
   - simplification and duplication removal
   - current-library best practices
   - typing and validation clarity
   - query and transaction efficiency
   - build, CI, and release reliability
   - deployment and operations clarity
   - test coverage for changed behavior

5. Edit minimally.
   - Keep changes inside the requested chunk unless a nearby fix is required for correctness.
   - Do not add abstraction unless it removes real duplication or confusion.
   - Do not add compatibility shims unless the code has an actual external contract or persisted-data need.
   - If a refactor would touch many files, stop and suggest a smaller follow-up slice.
   - Preserve established repo behavior unless there is a concrete correctness, safety, or maintainability gain.
   - Preserve release tags, workflow triggers, deployment semantics, and migration compatibility unless the user explicitly wants to change them.

6. Verify the result.
   - Run targeted checks first, then broader checks if warranted.
   - Use repo commands:
     - `uv run ruff check src tests migrations`
     - `uv run pytest`
     - `PYTHONPATH=src uv run python scripts/generate_openapi_spec.py` if routes, schemas, or response models changed
     - `uv sync --frozen --all-groups` if dependency or lock changes were made
     - `docker compose config` if `compose.yaml` changed
     - `helm lint applications/clusters-metadata-api` if the chart changed
     - relevant workflow validation by careful static review when GitHub Actions files changed

## Review Checklist

### Pydantic v2 And Settings

Look for:

- v1 carryovers such as `class Config`, `validator`, `root_validator`, `parse_obj_as`, `from_orm`, `dict()`, `json()`, or `copy()` on models
- repeated `ConfigDict(extra="forbid")` or similar patterns that could be shared safely
- over-modeled or duplicated request and response schemas that could be merged without weakening the contract
- missing use of `model_dump(exclude_unset=True)`, `model_validate`, `computed_field`, `field_validator`, `model_validator`, or `TypeAdapter` where they materially simplify code
- settings logic that can be made clearer with `pydantic-settings` features instead of ad hoc parsing

Prefer:

- `ConfigDict`
- `field_validator` and `model_validator`
- `model_dump()` and `model_validate()`
- `Annotated[...]` when it improves validation metadata or dependency signatures
- strict, explicit types over `Any` where practical

Do not:

- replace working models just to use a newer API if there is no simplification or correctness gain
- force shared base models when input and output shapes are meaningfully different

### FastAPI

Look for:

- repeated query parameter lists that can become a query model or dependency
- duplicated router boilerplate
- unclear dependency injection or security wiring
- response models or status codes that are implicit or inconsistent
- sync endpoints doing blocking DB work in a way that mismatches the rest of the stack
- lifecycle logic that would be cleaner as lifespan setup

Prefer:

- typed dependencies and `Annotated` when it improves readability
- query and body models to collapse long repeated parameter lists
- explicit `response_model`, status codes, and error mapping
- stable OpenAPI output when changing API-facing code

Do not:

- switch sync code to async unless the whole call chain benefits and the change is justified
- change API contracts casually; if the contract changes, regenerate and review `openapi.json`

### SQLAlchemy 2 And Alembic

Look for:

- untyped or stringly typed ORM patterns that can be replaced with `Mapped[...]`, `mapped_column()`, typed relationships, or typed query composition
- repeated loader option blocks that can be centralized safely
- `getattr(Model, order_by)` or other dynamic attribute access that weakens type safety or input safety
- transaction boundaries that are too fine-grained, especially commit-in-loops
- repository and service splits that add indirection without value
- N+1 query risks or unnecessary refreshes

Prefer:

- SQLAlchemy 2 typed declarative patterns
- `select()` plus `Session.scalars()` or `execute(...).scalars()` as appropriate
- one clear transaction per unit of work
- eager loading only where it supports an actual response shape
- backward-compatible migrations only

This repo-specific rule matters:

- `docs/migration-guide.html` documents a shared-schema coexistence period with the legacy service
- any migration or schema assumption must remain backward compatible during that window

### Tests And Toolchain

Look for:

- API or service changes without targeted tests
- tests that repeat bulky setup which could move to fixtures or factories
- assertions that are too weak to protect refactors
- missed mypy or Ruff simplifications

Prefer:

- small targeted tests near the changed behavior
- using existing test structure and factories
- updating `openapi.json` only when contract changes are intentional

### uv, Packaging, And Local Developer Workflow

Look for:

- dependency groups or version ranges that add churn without clear value
- commands split across README, scripts, CI, and Docker in inconsistent ways
- `uv sync` usage that is inconsistent between local, CI, and image builds
- lockfile handling that is unclear or fragile
- generated artifacts or caches that should not be committed

Prefer:

- one clear documented path for install, test, lint, and run
- consistent `uv` usage across local, CI, and Docker where practical
- pinned, reproducible installs in CI and container builds

### Alembic And Migration Workflow

Look for:

- env/config duplication between app settings and `migrations/env.py`
- migration setup that is harder to reason about than necessary
- missing checks that the database is at head or that autogenerate changes are intentional
- migration scripts or config that ignore the shared-schema coexistence rule

Prefer:

- one clear source of truth for metadata and connection construction where practical
- explicit backward-compatible migration discipline
- simple migration commands and docs that match local and deployed behavior

### OpenAPI, SDK, And Contract Automation

Look for:

- drift between routes/schemas and `openapi.json`
- generator scripts that patch files in brittle ways
- duplicated versioning logic between release flow and SDK generation
- unclear assumptions about preview vs release SDK publishing

Prefer:

- deterministic spec generation
- deterministic SDK generation
- stable version injection and smoke tests
- clear separation between contract changes and non-contract refactors

### GitHub Actions, Release, And Automation

Look for:

- duplicated steps across workflows that could be centralized safely
- workflow triggers that are broader or narrower than intended
- secrets handling, token generation, and permissions that can be reduced or clarified
- places where reusable workflows are already used but local workflows still duplicate setup logic
- release automation that depends on brittle shell behavior or forced git operations

Prefer:

- least-privilege permissions
- concise workflows with clear job boundaries
- reusable workflow usage where it truly reduces duplication
- explicit summaries and failure messages

### Docker, Compose, And Runtime Images

Look for:

- inconsistencies between local dev, CI, and production image behavior
- duplicated healthchecks, environment wiring, or entrypoint logic
- container build steps that reinstall more than necessary
- dev targets that rely on assumptions not reflected in README or compose

Prefer:

- clear separation between dev and production targets
- reproducible builds
- consistent environment names and ports
- healthchecks that match the real app surface

### Helm And Deployment Config

Look for:

- chart values duplicated across env files without real variation
- templates that are harder to read than necessary
- deployment config that drifts from actual app/runtime assumptions
- init DB job behavior that is not aligned with local and CI migration expectations

Prefer:

- minimal, readable values files
- templates with clear helpers and limited duplication
- deployment configuration that matches the repo's actual startup, migration, and healthcheck behavior

## Output Style

If the user asked for a review:

1. List findings first, ordered by severity, with `file:line` references.
2. Keep findings concrete and actionable.
3. If there are no findings, say so and mention residual risks or missing verification.
4. After findings, include a brief change plan only if useful.

If the user asked for implementation:

1. Make the minimal correct changes.
2. Verify them with the relevant commands.
3. Summarize what changed, what was verified, and any remaining follow-up.

## Good First Slices In This Repo

- `src/app/core/config.py` and `src/app/core/db.py` for settings and session patterns
- `src/app/api/m4w/clusters.py` plus `src/app/schemas/clusters.py` for FastAPI query model simplification
- `src/app/repositories/*.py` for SQLAlchemy 2 typing and repeated loader cleanup
- `src/app/services/clusters/*.py` for transaction boundaries, mapper and translator split, and duplication
- `tests/api` and `tests/services` for targeted coverage improvements
- `pyproject.toml`, `uv.lock`, `README.md`, and `.pre-commit-config.yaml` for uv and local workflow consistency
- `alembic.ini`, `migrations/env.py`, and migration docs/process for Alembic simplification
- `scripts/generate_openapi_spec.py`, `scripts/generate_sdk.sh`, `sdk-config.yml`, and `openapi.json` workflow alignment
- `.github/workflows/*`, `release-please-config.json`, and `.github/dependabot.yaml` for CI/release automation cleanup
- `Dockerfile` and `compose.yaml` for image and local runtime alignment
- `applications/clusters-metadata-api/**` for Helm and deployment consistency

## Example Prompts

- `Review src/app/core/config.py for Pydantic v2 and settings cleanup.`
- `Review src/app/api/m4w/clusters.py and related schemas for FastAPI simplification.`
- `Review src/app/repositories for SQLAlchemy 2 cleanup and duplication removal.`
- `Implement the cleanup findings for src/app/services/clusters in the smallest safe diff.`
- `Review pyproject.toml, uv usage, and pre-commit config for simplification and consistency.`
- `Review Alembic config and migration workflow for SQLAlchemy 2 and Alembic best practices.`
- `Review GitHub Actions and release automation for duplication, permissions, and clarity.`
- `Review Docker, compose, and Helm chart files for runtime and deployment cleanup.`
