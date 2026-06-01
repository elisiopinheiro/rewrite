# syntax=docker/dockerfile:1
# Multi-stage uv build producing a single runtime image. The entrypoint app
# (internal vs partner) and the migration job are selected by overriding the
# command (Helm `api.command`, compose `command`) — not by separate images.

ARG PYTHON_IMAGE=python:3.12-slim
ARG UV_VERSION=0.11.15


# --- uv binary ---
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv


# --- Build: resolve dependencies and install the project into a venv ---
FROM ${PYTHON_IMAGE} AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY --from=uv /uv /usr/local/bin/uv
# Build the venv at the same path it runs at (/app/.venv) so the console-script
# shebangs (alembic, etc.) remain valid after the copy into the runtime stage.
WORKDIR /app

# Dependencies first for layer caching. The `migrations` group adds alembic so
# the init-db job can run from this image; the API itself never imports it.
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --group migrations

# Install the project (non-editable) so the runtime image needs no source tree.
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --group migrations


# --- Runtime ---
FROM ${PYTHON_IMAGE} AS runtime

RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/false app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Migration assets for the init-db job. alembic.ini uses a relative
# script_location, so it and migrations/ must sit under WORKDIR.
COPY alembic.ini ./
COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]

# Default to the internal API; partner deployments and the migration job override this.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
