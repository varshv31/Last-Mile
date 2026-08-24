"""Common Pydantic schemas — error responses, pagination wrappers."""
from __future__ import annotations

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class PaginatedData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_next: bool
