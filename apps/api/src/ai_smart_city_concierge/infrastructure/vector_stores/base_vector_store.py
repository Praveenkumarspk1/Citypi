"""
Base Vector Store Abstract Class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorSearchResult:
    """Result of a vector search"""
    id: str
    score: float
    metadata: dict[str, Any]
    embedding: list[float] | None = None


@dataclass
class VectorStoreConfig:
    """Configuration for vector store"""
    host: str = "localhost"
    port: int = 8000
    api_key: str | None = None
    collection_name: str = "default"
    dimension: int = 1024
    distance_metric: str = "cosine"  # cosine, euclidean, dot
    timeout: int = 30


class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""

    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self._client = None
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection"""
        pass

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance_metric: str = "cosine",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection"""
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        pass

    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        pass

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors into collection"""
        pass

    @abstractmethod
    async def query(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        include_embeddings: bool = False,
    ) -> list[VectorSearchResult]:
        """Query similar vectors"""
        pass

    @abstractmethod
    async def get(
        self,
        collection: str,
        ids: list[str],
        include_embeddings: bool = False,
    ) -> list[VectorSearchResult]:
        """Get vectors by IDs"""
        pass

    @abstractmethod
    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> None:
        """Delete vectors by IDs"""
        pass

    @abstractmethod
    async def count(self, collection: str) -> int:
        """Get count of vectors in collection"""
        pass

    @abstractmethod
    async def list_collections(self) -> list[str]:
        """List all collections"""
        pass

    @abstractmethod
    async def get_collection_info(self, name: str) -> dict[str, Any]:
        """Get collection metadata"""
        pass

    async def health_check(self) -> bool:
        """Health check"""
        try:
            await self.list_collections()
            return True
        except Exception:
            return False
