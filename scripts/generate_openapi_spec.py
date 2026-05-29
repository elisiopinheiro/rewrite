"""Generate OpenAPI specification file for the clusters API."""

import json
from pathlib import Path

from app.main import app


def generate_openapi_spec() -> None:
    openapi_schema = app.openapi()

    project_root = Path(__file__).parent.parent
    output_file = project_root / "openapi.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    generate_openapi_spec()
