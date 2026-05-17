from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any


class APISuccessResponse(BaseModel):
    success: bool = True
    data: Any
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APIErrorResponse(BaseModel):
    success: bool = False
    error: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
