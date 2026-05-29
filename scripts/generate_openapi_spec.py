"""Generate OpenAPI specification file."""

import json
from pathlib import Path

from api.m4w.main import app


def generate_openapi_spec() -> None:
    """
    Generate OpenAPI specification.

    This script extracts the OpenAPI schema from the FastAPI application
    and writes it to a JSON file in the project root directory.
    """
    openapi_schema = app.openapi()

    # Get the project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    output_file = project_root / "openapi.json"

    # Write the OpenAPI spec to file with pretty formatting
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")  # Add EOF newline

    # Print summary for CI logs
    info = openapi_schema.get("info", {})
    paths = openapi_schema.get("paths", {})
    endpoint_count = sum(len(methods) for methods in paths.values())

    print(f"✓ Generated OpenAPI specification at {output_file}")
    print(f"  Title: {info.get('title', 'N/A')}")
    print(f"  Version: {info.get('version', 'N/A')}")
    print(f"  Endpoints: {endpoint_count}")


if __name__ == "__main__":
    generate_openapi_spec()
