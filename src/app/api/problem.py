"""RFC 7807 problem-detail exception handlers shared by both apps.

Domain errors (``ProblemException``) and transport errors (``HTTPException``,
e.g. auth 401/403) are rendered as ``application/problem+json``. Request
validation errors are deliberately left in FastAPI's default shape so they keep
matching the generated OpenAPI/SDK 422 schema.
"""

from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.errors import ProblemException

PROBLEM_JSON = "application/problem+json"


def _problem(
    *,
    status: int,
    title: str,
    detail: str,
    type: str = "about:blank",
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"type": type, "title": title, "status": status, "detail": detail}
    return JSONResponse(status_code=status, media_type=PROBLEM_JSON, content=body, headers=headers)


async def _handle_problem(_request: Request, exc: ProblemException) -> JSONResponse:
    return _problem(status=exc.status, title=exc.title, detail=exc.detail, type=exc.type)


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    title = HTTPStatus(exc.status_code).phrase
    detail = exc.detail if isinstance(exc.detail, str) else title
    return _problem(status=exc.status_code, title=title, detail=detail, headers=exc.headers)


def register_exception_handlers(app: FastAPI) -> None:
    """Register the shared problem-detail handlers on a FastAPI app."""
    app.add_exception_handler(ProblemException, _handle_problem)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
