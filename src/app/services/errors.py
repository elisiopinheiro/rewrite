"""Application errors — RFC 7807 problem responses."""

from fastapi import HTTPException


class ProblemException(HTTPException):
    """RFC 7807 Problem Details exception.

    Raises a FastAPI HTTPException with structured problem detail.
    """

    def __init__(self, *, title: str, detail: str, status: int) -> None:
        super().__init__(
            status_code=status,
            detail={"title": title, "detail": detail, "status": status},
        )
