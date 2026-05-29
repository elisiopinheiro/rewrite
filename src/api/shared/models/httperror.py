from pydantic import BaseModel


class HTTPError(BaseModel):
    """Response model for HTTPException error responses"""

    detail: str
