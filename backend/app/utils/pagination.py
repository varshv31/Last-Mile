"""Pagination utility."""
from __future__ import annotations

from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    limit: int
    offset: int
    has_next: bool

    @classmethod
    def create(cls, items: Sequence[T], total: int, limit: int, offset: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_next=(offset + limit) < total,
        )
