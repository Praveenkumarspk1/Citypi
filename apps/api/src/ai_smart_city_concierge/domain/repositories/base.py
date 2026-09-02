"""
Base Repository Interfaces
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar
from uuid import UUID

T = TypeVar("T")  # Entity type
ID = TypeVar("ID", bound=UUID)  # ID type


@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    page_size: int = 20

    def __post_init__(self):
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 1
        if self.page_size > 100:
            self.page_size = 100

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class PaginatedResult[T]:
    """Paginated result"""
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


@dataclass
class SortParams:
    """Sorting parameters"""
    field: str = "created_at"
    order: str = "desc"  # asc or desc

    def __post_init__(self):
        if self.order not in ("asc", "desc"):
            self.order = "desc"


@dataclass
class FilterParams:
    """Filter parameters"""
    filters: dict[str, Any] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class BaseRepository[T, ID: UUID](ABC):
    """Base repository interface"""

    @abstractmethod
    async def get_by_id(self, id: ID) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_by_ids(self, ids: list[ID]) -> list[T]:
        """Get multiple entities by IDs"""
        pass

    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if entity exists"""
        pass

    @abstractmethod
    async def count(self, filters: FilterParams | None = None) -> int:
        """Count entities matching filters"""
        pass

    @abstractmethod
    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[T]:
        """List entities with pagination, sorting, and filtering"""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete entity by ID (soft delete)"""
        pass

    @abstractmethod
    async def hard_delete(self, id: ID) -> bool:
        """Permanently delete entity"""
        pass


class ReadOnlyRepository[T, ID: UUID](ABC):
    """Read-only repository interface"""

    @abstractmethod
    async def get_by_id(self, id: ID) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_by_ids(self, ids: list[ID]) -> list[T]:
        """Get multiple entities by IDs"""
        pass

    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if entity exists"""
        pass

    @abstractmethod
    async def count(self, filters: FilterParams | None = None) -> int:
        """Count entities matching filters"""
        pass

    @abstractmethod
    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[T]:
        """List entities with pagination, sorting, and filtering"""
        pass


# Specification Pattern
class Specification[T](ABC):
    """Specification pattern for complex queries"""

    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies specification"""
        pass

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]):
        self.spec = spec

    def is_satisfied_by(self, entity: T) -> bool:
        return not self.spec.is_satisfied_by(entity)


# Common Specifications
class IdSpecification(Specification[T]):
    def __init__(self, id: ID):
        self.id = id

    def is_satisfied_by(self, entity: T) -> bool:
        return getattr(entity, 'id', None) == self.id


class ActiveSpecification(Specification[T]):
    """Specification for active entities"""
    def is_satisfied_by(self, entity: T) -> bool:
        return getattr(entity, 'is_active', True) is True


class DeletedSpecification(Specification[T]):
    """Specification for deleted entities"""
    def is_satisfied_by(self, entity: T) -> bool:
        return getattr(entity, 'deleted_at', None) is not None


class DateRangeSpecification(Specification[T]):
    def __init__(self, field: str, start: datetime | None = None, end: datetime | None = None):
        self.field = field
        self.start = start
        self.end = end

    def is_satisfied_by(self, entity: T) -> bool:
        value = getattr(entity, self.field, None)
        if value is None:
            return False
        if self.start and value < self.start:
            return False
        if self.end and value > self.end:
            return False
        return True


