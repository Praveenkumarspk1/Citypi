"""
ChromaDB Vector Store Adapter
"""
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from .base_vector_store import BaseVectorStore, VectorSearchResult, VectorStoreConfig


class ChromaDBAdapter(BaseVectorStore):
    """ChromaDB vector store adapter for development and production"""

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._client: chromadb.Client | None = None
        self._collections: dict[str, Collection] = {}

    async def initialize(self) -> None:
        """Initialize ChromaDB client"""
        if self._initialized:
            return

        # Create ChromaDB client
        if self.config.host and self.config.port:
            # HTTP client for remote ChromaDB
            self._client = chromadb.HttpClient(
                host=self.config.host,
                port=self.config.port,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        else:
            # In-memory client for testing
            self._client = chromadb.Client(
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=False,
                )
            )

        # Ensure default collection exists
        await self.create_collection(
            name=self.config.collection_name,
            dimension=self.config.dimension,
            distance_metric=self.config.distance_metric,
        )

        self._initialized = True

    async def close(self) -> None:
        """Close ChromaDB client"""
        if self._client:
            # ChromaDB HTTP client doesn't need explicit close
            self._client = None
            self._collections.clear()
            self._initialized = False

    def _get_collection(self, name: str) -> Collection:
        """Get or create collection"""
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": self.config.distance_metric},
            )
        return self._collections[name]

    async def create_collection(
        self,
        name: str,
        dimension: int,
        distance_metric: str = "cosine",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection"""
        if not self._initialized:
            await self.initialize()

        collection_metadata = {"hnsw:space": distance_metric}
        if metadata:
            collection_metadata.update(metadata)

        self._client.create_collection(
            name=name,
            metadata=collection_metadata,
        )
        # Clear cache
        self._collections.pop(name, None)

    async def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        if not self._initialized:
            await self.initialize()

        self._client.delete_collection(name=name)
        self._collections.pop(name, None)

    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        if not self._initialized:
            await self.initialize()

        try:
            self._client.get_collection(name=name)
            return True
        except Exception:
            return False

    async def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert vectors into collection"""
        if not self._initialized:
            await self.initialize()

        coll = self._get_collection(collection)

        # ChromaDB expects documents, we'll store a placeholder
        documents = [metadata.get("text", "") for metadata in metadatas]

        coll.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

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
        if not self._initialized:
            await self.initialize()

        coll = self._get_collection(collection)

        include = ["metadatas", "distances"]
        if include_embeddings:
            include.append("embeddings")

        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include,
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert distance to similarity score (1 - distance for cosine)
                score = 1.0 - distance if self.config.distance_metric == "cosine" else 1.0 / (1.0 + distance)

                embedding = None
                if include_embeddings and results["embeddings"]:
                    embedding = results["embeddings"][0][i]

                search_results.append(VectorSearchResult(
                    id=id_,
                    score=score,
                    metadata=metadata,
                    embedding=embedding,
                ))

        return search_results

    async def get(
        self,
        collection: str,
        ids: list[str],
        include_embeddings: bool = False,
    ) -> list[VectorSearchResult]:
        """Get vectors by IDs"""
        if not self._initialized:
            await self.initialize()

        coll = self._get_collection(collection)

        include = ["metadatas"]
        if include_embeddings:
            include.append("embeddings")

        results = coll.get(
            ids=ids,
            include=include,
        )

        search_results = []
        if results["ids"]:
            for i, id_ in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}

                embedding = None
                if include_embeddings and results["embeddings"]:
                    embedding = results["embeddings"][i]

                search_results.append(VectorSearchResult(
                    id=id_,
                    score=1.0,  # Exact match
                    metadata=metadata,
                    embedding=embedding,
                ))

        return search_results

    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> None:
        """Delete vectors by IDs"""
        if not self._initialized:
            await self.initialize()

        coll = self._get_collection(collection)
        coll.delete(ids=ids)

    async def count(self, collection: str) -> int:
        """Get count of vectors in collection"""
        if not self._initialized:
            await self.initialize()

        coll = self._get_collection(collection)
        return coll.count()

    async def list_collections(self) -> list[str]:
        """List all collections"""
        if not self._initialized:
            await self.initialize()

        collections = self._client.list_collections()
        return [c.name for c in collections]

    async def get_collection_info(self, name: str) -> dict[str, Any]:
        """Get collection metadata"""
        if not self._initialized:
            await self.initialize()

        coll = self._client.get_collection(name=name)
        return {
            "name": coll.name,
            "count": coll.count(),
            "metadata": coll.metadata,
        }

    async def reset(self) -> None:
        """Reset the database (delete all collections)"""
        if not self._initialized:
            await self.initialize()

        self._client.reset()
        self._collections.clear()
