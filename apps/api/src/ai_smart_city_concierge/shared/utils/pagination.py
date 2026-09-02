"""
Shared Utilities - Pagination helpers
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PageParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass(frozen=True)
class PaginatedResponse:
    """Paginated response wrapper."""
    items: list[Any]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


def paginate(items: list[Any], total: int, page_params: PageParams) -> PaginatedResponse:
    """Create paginated response from items and total count."""
    return PaginatedResponse(
        items=items,
        total=total,
        page=page_params.page,
        page_size=page_params.page_size,
    )
