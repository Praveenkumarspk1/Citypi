"""
Vector Store Configuration (ChromaDB / Qdrant)
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from .settings import get_settings

settings = get_settings()


class VectorStoreType(StrEnum):
    CHROMADB = "chromadb"
    QDRANT = "qdrant"


@dataclass
class VectorSearchResult:
    """Result from vector search"""
    id: str
    score: float
    payload: dict[str, Any]
    vector: list[float] | None = None


@dataclass
class VectorPoint:
    """Point to upsert into vector store"""
    id: str
    vector: list[float]
    payload: dict[str, Any]


class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections"""
        pass

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "cosine",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a collection"""
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
        points: list[VectorPoint],
    ) -> None:
        """Upsert points"""
        pass

    @abstractmethod
    async def upsert_batch(
        self,
        collection: str,
        points: list[VectorPoint],
        batch_size: int = 100,
    ) -> None:
        """Upsert points in batches"""
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        with_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> None:
        """Delete points by IDs"""
        pass

    @abstractmethod
    async def delete_by_filter(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> None:
        """Delete points by filter"""
        pass

    @abstractmethod
    async def get(
        self,
        collection: str,
        ids: list[str],
        with_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """Get points by IDs"""
        pass

    @abstractmethod
    async def count(self, collection: str) -> int:
        """Count points in collection"""
        pass


class ChromaDBVectorStore(BaseVectorStore):
    """ChromaDB implementation"""

    def __init__(self):
        self.client: chromadb.HttpClient | None = None
        self._collections: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize ChromaDB client"""
        self.client = chromadb.HttpClient(
            host=settings.chromadb.host,
            port=settings.chromadb.port,
            ssl=settings.chromadb.ssl,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        # Test connection
        await self._test_connection()

    async def _test_connection(self) -> None:
        """Test ChromaDB connection"""
        try:
            self.client.heartbeat()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ChromaDB: {e}")

    async def close(self) -> None:
        """Close connections"""
        self._collections.clear()
        self.client = None

    def _get_collection(self, name: str):
        """Get or create collection"""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name)
        return self._collections[name]

    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance: str = "cosine",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a collection"""
        if not self.client:
            await self.initialize()

        # ChromaDB doesn't require dimension at creation
        # but we can store it in metadata
        meta = metadata or {}
        meta["dimension"] = dimension
        meta["distance"] = distance

        self.client.create_collection(
            name=name,
            metadata=meta,
            get_or_create=True,
        )
        self._collections.pop(name, None)  # Clear cache

    async def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        if self.client:
            try:
                self.client.delete_collection(name)
                self._collections.pop(name, None)
            except Exception:
                pass  # Collection might not exist

    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        if not self.client:
            return False
        try:
            self.client.get_collection(name)
            return True
        except Exception:
            return False

    async def upsert(
        self,
        collection: str,
        points: list[VectorPoint],
    ) -> None:
        """Upsert points"""
        if not self.client:
            await self.initialize()

        coll = self._get_collection(collection)

        ids = [p.id for p in points]
        vectors = [p.vector for p in points]
        metadatas = [p.payload for p in points]

        coll.upsert(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas,
        )

    async def upsert_batch(
        self,
        collection: str,
        points: list[VectorPoint],
        batch_size: int = 100,
    ) -> None:
        """Upsert points in batches"""
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await self.upsert(collection, batch)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        with_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors"""
        if not self.client:
            await self.initialize()

        coll = self._get_collection(collection)

        # Build where clause for filtering
        where = self._build_where_clause(filter) if filter else None

        results = coll.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where,
            include=["metadatas", "distances", "embeddings"] if with_vectors else ["metadatas", "distances"],
        )

        return self._parse_search_results(results, with_vectors)

    def _build_where_clause(self, filter: dict[str, Any]) -> dict[str, Any]:
        """Build ChromaDB where clause from filter"""
        where = {}
        for key, value in filter.items():
            if isinstance(value, dict):
                # Handle operators like $eq, $ne, $gt, $lt, $in, $nin
                for op, val in value.items():
                    chroma_op = op.replace("$", "")
                    if chroma_op in ["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin"]:
                        where[key] = {chroma_op: val}
            else:
                where[key] = {"eq": value}
        return where

    def _parse_search_results(
        self,
        results: dict[str, Any],
        with_vectors: bool,
    ) -> list[VectorSearchResult]:
        """Parse ChromaDB search results"""
        search_results = []

        if not results["ids"] or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        embeddings = results.get("embeddings", [None])[0] if with_vectors else [None] * len(ids)

        for _i, (id_, distance, metadata, embedding) in enumerate(zip(ids, distances, metadatas, embeddings, strict=False)):
            # Convert distance to similarity score (1 - distance for cosine)
            score = 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance)

            search_results.append(VectorSearchResult(
                id=id_,
                score=score,
                payload=metadata or {},
                vector=embedding,
            ))

        return search_results

    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> None:
        """Delete points by IDs"""
        if not self.client:
            return

        coll = self._get_collection(collection)
        coll.delete(ids=ids)

    async def delete_by_filter(
        self,
        collection: str,
        filter: dict[str, Any],
    ) -> None:
        """Delete points by filter"""
        if not self.client:
            return

        coll = self._get_collection(collection)
        where = self._build_where_clause(filter)
        coll.delete(where=where)

    async def get(
        self,
        collection: str,
        ids: list[str],
        with_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """Get points by IDs"""
        if not self.client:
            await self.initialize()

        coll = self._get_collection(collection)

        results = coll.get(
            ids=ids,
            include=["metadatas", "embeddings"] if with_vectors else ["metadatas"],
        )

        search_results = []
        if results["ids"]:
            for i, id_ in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                embedding = results["embeddings"][i] if with_vectors and results.get("embeddings") else None

                search_results.append(VectorSearchResult(
                    id=id_,
                    score=1.0,
                    payload=metadata or {},
                    vector=embedding,
                ))

        return search_results

    async def count(self, collection: str) -> int:
        """Count points in collection"""
        if not self.client:
            await self.initialize()

        try:
            coll = self._get_collection(collection)
            return coll.count()
        except Exception:
            return 0


# Global vector store instance
_vector_store: BaseVectorStore | None = None


def get_vector_store() -> BaseVectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        store_type = settings.ai.vector_store_type
        if store_type == VectorStoreType.CHROMADB:
            _vector_store = ChromaDBVectorStore()
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")
    return _vector_store


async def init_vector_store() -> None:
    """Initialize vector store"""
    store = get_vector_store()
    await store.initialize()


async def close_vector_store() -> None:
    """Close vector store"""
    global _vector_store
    if _vector_store:
        await _vector_store.close()
        _vector_store = None


@asynccontextmanager
async def get_vector_store_context() -> AsyncGenerator[BaseVectorStore, None]:
    """Context manager for vector store"""
    store = get_vector_store()
    if not store.client:
        await store.initialize()
    try:
        yield store
    finally:
        pass


async def health_check_vector_store() -> bool:
    """Check vector store connectivity"""
    try:
        store = get_vector_store()
        if not store.client:
            await store.initialize()
        # Try to list collections as a health check
        await store.client.list_collections()
        return True
    except Exception:
        return False


# Collection names
class Collections:
    """Vector store collection names"""
    POI_EMBEDDINGS = "poi_embeddings"
    CONVERSATION_EMBEDDINGS = "conversation_embeddings"
    ITINERARY_EMBEDDINGS = "itinerary_embeddings"
    MEDIA_EMBEDDINGS = "media_embeddings"
    DOCUMENT_EMBEDDINGS = "document_embeddings"
    LANDMARK_EMBEDDINGS = "landmark_embeddings"
