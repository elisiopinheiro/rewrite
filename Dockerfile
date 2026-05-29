FROM python:3.12.13-slim

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

RUN pip3 install "poetry==2.3.2" --no-cache-dir

RUN useradd -ms /bin/bash api-user
USER api-user
WORKDIR /home/api-user

COPY --chown=api-user poetry.lock pyproject.toml alembic.ini ./

RUN poetry install --no-root

COPY --chown=api-user src/api ./api
COPY --chown=api-user migrations ./migrations

CMD ["poetry", "run", "uvicorn", "api.m4w.main:app", "--host", "0.0.0.0", "--port", "8000"]
