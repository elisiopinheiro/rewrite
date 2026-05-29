#!/usr/bin/env bash

set -euo pipefail

OUTPUT_PATH="${1:-generated-sdk}"
META_MODE="${OPENAPI_PYTHON_CLIENT_META:-poetry}"
PACKAGE_VERSION="${OPENAPI_PYTHON_CLIENT_PACKAGE_VERSION:-0.0.0.dev0+$(git rev-parse --short HEAD)}"

# Generate OpenAPI spec from the app
PYTHONPATH=src uv run python scripts/generate_openapi_spec.py

# Generate SDK from the spec
uv run --with openapi-python-client openapi-python-client generate \
  --path openapi.json \
  --config sdk-config.yml \
  --output-path "${OUTPUT_PATH}" \
  --overwrite \
  --meta "${META_MODE}"

# Patch version in generated pyproject.toml
python - <<'PY' "${OUTPUT_PATH}/pyproject.toml" "${PACKAGE_VERSION}"
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
version = sys.argv[2]
path.write_text(re.sub(r'^version = ".*"$', f'version = "{version}"', path.read_text(), flags=re.MULTILINE))
PY
