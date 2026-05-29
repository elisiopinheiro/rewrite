# syntax=docker/dockerfile:1
# Multi-stage build using uv for fast dependency resolution.

ARG PYTHON_IMAGE=python:3.12-slim
ARG UV_VERSION=0.11.15


# --- Stage 0: Tooling ---
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv


# --- Stage 1: Build ---
FROM ${PYTHON_IMAGE} AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /build

# Install dependencies first (layer cache)
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Install the project itself into site-packages so the runtime image does not
# depend on the builder stage source tree.
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable


# --- Stage 2: Runtime base ---
FROM ${PYTHON_IMAGE} AS base

RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/false app

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]


# --- Stage 3a: M4W (internal management) app ---
# Canonical production image: one Uvicorn process per container.
FROM base AS m4w
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# --- Stage 3b: Partner (external read-only) app ---
FROM base AS partner
CMD ["python", "-m", "uvicorn", "app.partner:app", "--host", "0.0.0.0", "--port", "8000"]


# --- Stage 3c: Local development targets ---
FROM base AS m4w-dev
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]


FROM base AS partner-dev
CMD ["python", "-m", "uvicorn", "app.partner:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]


# Default image target for repository-level builds.
FROM m4w AS final
