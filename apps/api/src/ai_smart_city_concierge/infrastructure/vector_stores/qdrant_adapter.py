"""
Qdrant Vector Store Adapter
"""
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .base_vector_store import BaseVectorStore, VectorSearchResult, VectorStoreConfig


class QdrantAdapter(BaseVectorStore):
    """Qdrant vector store adapter for production use"""

    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._client: QdrantClient | None = None

    async def initialize(self) -> None:
        """Initialize Qdrant client"""
        if self._initialized:
            return

        # Create Qdrant client
        if self.config.api_key:
            self._client = QdrantClient(
                host=self.config.host,
                port=self.config.port,
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )
        else:
            self._client = QdrantClient(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
            )

        # Ensure default collection exists
        await self.create_collection(
            name=self.config.collection_name,
            dimension=self.config.dimension,
            distance_metric=self.config.distance_metric,
        )

        self._initialized = True

    async def close(self) -> None:
        """Close Qdrant client"""
        if self._client:
            self._client.close()
            self._client = None
            self._initialized = False

    def _get_distance_metric(self, metric: str) -> Distance:
        """Convert string metric to Qdrant Distance enum"""
        metric_map = {
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID,
            "dot": Distance.DOT,
        }
        return metric_map.get(metric.lower(), Distance.COSINE)

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

        distance = self._get_distance_metric(distance_metric)

        self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=distance,
            ),
        )

    async def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        if not self._initialized:
            await self.initialize()

        self._client.delete_collection(collection_name=name)

    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        if not self._initialized:
            await self.initialize()

        try:
            self._client.get_collection(collection_name=name)
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

        points = []
        for _i, (id_, embedding, metadata) in enumerate(zip(ids, embeddings, metadatas, strict=False)):
            points.append(PointStruct(
                id=id_,
                vector=embedding,
                payload=metadata,
            ))

        self._client.upsert(
            collection_name=collection,
            points=points,
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

        # Build filter from where clause
        query_filter = None
        if where:
            conditions = []
            for key, value in where.items():
                if isinstance(value, dict):
                    # Handle operators like $eq, $ne, $in, etc.
                    for op, val in value.items():
                        if op == "$eq":
                            conditions.append(FieldCondition(key=key, match=MatchValue(value=val)))
                        elif op == "$in":
                            conditions.append(FieldCondition(key=key, match=MatchValue(value=val)))
                else:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

            if conditions:
                query_filter = Filter(must=conditions)

        search_result = self._client.search(
            collection_name=collection,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=n_results,
            with_payload=True,
            with_vectors=include_embeddings,
        )

        search_results = []
        for hit in search_result:
            embedding = hit.vector if include_embeddings and hit.vector else None
            search_results.append(VectorSearchResult(
                id=str(hit.id),
                score=hit.score,
                metadata=hit.payload or {},
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

        points = self._client.retrieve(
            collection_name=collection,
            ids=ids,
            with_payload=True,
            with_vectors=include_embeddings,
        )

        search_results = []
        for point in points:
            embedding = point.vector if include_embeddings and point.vector else None
            search_results.append(VectorSearchResult(
                id=str(point.id),
                score=1.0,  # Exact match
                metadata=point.payload or {},
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

        self._client.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=ids),
        )

    async def count(self, collection: str) -> int:
        """Get count of vectors in collection"""
        if not self._initialized:
            await self.initialize()

        info = self._client.get_collection(collection_name=collection)
        return info.points_count

    async def list_collections(self) -> list[str]:
        """List all collections"""
        if not self._initialized:
            await self.initialize()

        collections = self._client.get_collections()
        return [c.name for c in collections.collections]

    async def get_collection_info(self, name: str) -> dict[str, Any]:
        """Get collection metadata"""
        if not self._initialized:
            await self.initialize()

        info = self._client.get_collection(collection_name=name)
        return {
            "name": name,
            "count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": info.status,
            "optimizer_status": info.optimizer_status,
            "config": {
                "params": info.config.params,
                "hnsw_config": info.config.hnsw_config,
            } if info.config else {},
        }

    async def create_payload_index(
        self,
        collection: str,
        field_name: str,
        field_type: str = "keyword",
    ) -> None:
        """Create payload index for faster filtering"""
        if not self._initialized:
            await self.initialize()

        field_type_map = {
            "keyword": models.PayloadSchemaType.KEYWORD,
            "integer": models.PayloadSchemaType.INTEGER,
            "float": models.PayloadSchemaType.FLOAT,
            "geo": models.PayloadSchemaType.GEO,
            "text": models.PayloadSchemaType.TEXT,
            "bool": models.PayloadSchemaType.BOOL,
        }

        self._client.create_payload_index(
            collection_name=collection,
            field_name=field_name,
            field_schema=field_type_map.get(field_type, models.PayloadSchemaType.KEYWORD),
        )

    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        offset: int | None = None,
        with_payload: bool = True,
        with_vectors: bool = False,
        filter_: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Scroll through collection"""
        if not self._initialized:
            await self.initialize()

        query_filter = None
        if filter_:
            conditions = []
            for key, value in filter_.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            query_filter = Filter(must=conditions)

        points, next_offset = self._client.scroll(
            collection_name=collection,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            scroll_filter=query_filter,
        )

        search_results = []
        for point in points:
            embedding = point.vector if with_vectors and point.vector else None
            search_results.append(VectorSearchResult(
                id=str(point.id),
                score=1.0,
                metadata=point.payload or {},
                embedding=embedding,
            ))

        return search_results
