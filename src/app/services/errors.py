"""Domain errors for the service layer.

These are transport-agnostic: services raise them without importing FastAPI.
The API layer (``app.api.problem``) translates them into RFC 7807
``application/problem+json`` responses.
"""

from __future__ import annotations


class ProblemException(Exception):
    """A domain error carrying an RFC 7807 problem detail.

    ``title`` is a short, human-readable summary of the problem type, ``detail``
    explains this specific occurrence, and ``status`` is the HTTP status code.
    """

    def __init__(self, *, title: str, detail: str, status: int, type: str = "about:blank") -> None:
        super().__init__(detail)
        self.title = title
        self.detail = detail
        self.status = status
        self.type = type
