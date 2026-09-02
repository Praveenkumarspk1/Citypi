"""
Vector Database Adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.external_services import VectorDatabasePort


class BaseVectorDBAdapter(VectorDatabasePort, ABC):
    """Base vector database adapter"""

    @abstractmethod
    async def _upsert_request(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert embeddings request"""
        pass

    @abstractmethod
    async def _query_request(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Query embeddings request"""
        pass

    @abstractmethod
    async def _delete_request(self, collection: str, ids: list[str]) -> None:
        """Delete embeddings request"""
        pass

    @abstractmethod
    async def _get_request(self, collection: str, id: str) -> dict[str, Any] | None:
        """Get embedding request"""
        pass

    async def upsert_embeddings(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert embeddings"""
        await self._upsert_request(collection, ids, embeddings, metadatas)

    async def query_embeddings(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query similar embeddings"""
        return await self._query_request(collection, query_embedding, n_results, where)

    async def delete_embeddings(self, collection: str, ids: list[str]) -> None:
        """Delete embeddings"""
        await self._delete_request(collection, ids)

    async def get_embedding(self, collection: str, id: str) -> dict[str, Any] | None:
        """Get embedding by ID"""
        return await self._get_request(collection, id)


class ChromaDBAdapter(BaseVectorDBAdapter):
    """ChromaDB adapter"""

    def __init__(self, host: str = "localhost", port: int = 8000, persist_directory: str | None = None):
        self.host = host
        self.port = port
        self.persist_directory = persist_directory
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import chromadb
            if self.persist_directory:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
        return self._client

    async def _upsert_request(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        client = await self._get_client()
        col = client.get_or_create_collection(collection)
        col.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    async def _query_request(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        col = client.get_collection(collection)
        return col.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    async def _delete_request(self, collection: str, ids: list[str]) -> None:
        client = await self._get_client()
        col = client.get_collection(collection)
        col.delete(ids=ids)

    async def _get_request(self, collection: str, id: str) -> dict[str, Any] | None:
        client = await self._get_client()
        col = client.get_collection(collection)
        result = col.get(ids=[id])
        if result and result["ids"]:
            return {
                "id": result["ids"][0],
                "embedding": result["embeddings"][0] if result["embeddings"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None,
            }
        return None


class PineconeAdapter(BaseVectorDBAdapter):
    """Pinecone adapter"""

    def __init__(self, api_key: str, environment: str, index_name: str):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self._index = None

    async def _get_index(self):
        if self._index is None:
            import pinecone
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self._index = pinecone.Index(self.index_name)
        return self._index

    async def _upsert_request(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        index = await self._get_index()
        vectors = [
            {
                "id": id,
                "values": embedding,
                "metadata": metadata,
            }
            for id, embedding, metadata in zip(ids, embeddings, metadatas, strict=False)
        ]
        index.upsert(vectors=vectors, namespace=collection)

    async def _query_request(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None,
    ) -> dict[str, Any]:
        index = await self._get_index()
        result = index.query(
            vector=query_embedding,
            top_k=n_results,
            namespace=collection,
            filter=where,
            include_metadata=True,
            include_values=True,
        )

        return {
            "ids": [match["id"] for match in result["matches"]],
            "embeddings": [match["values"] for match in result["matches"]],
            "metadatas": [match["metadata"] for match in result["matches"]],
            "distances": [match["score"] for match in result["matches"]],
        }

    async def _delete_request(self, collection: str, ids: list[str]) -> None:
        index = await self._get_index()
        index.delete(ids=ids, namespace=collection)

    async def _get_request(self, collection: str, id: str) -> dict[str, Any] | None:
        index = await self._get_index()
        result = index.fetch(ids=[id], namespace=collection)
        if id in result["vectors"]:
            vec = result["vectors"][id]
            return {
                "id": id,
                "embedding": vec["values"],
                "metadata": vec["metadata"],
            }
        return None


class WeaviateAdapter(BaseVectorDBAdapter):
    """Weaviate adapter"""

    def __init__(self, url: str = "http://localhost:8080", api_key: str | None = None):
        self.url = url
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import weaviate
            auth_config = None
            if self.api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            self._client = weaviate.Client(url=self.url, auth_client_secret=auth_config)
        return self._client

    async def _upsert_request(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        client = await self._get_client()

        # Ensure class exists
        class_name = collection.capitalize()
        if not client.schema.exists(class_name):
            class_obj = {
                "class": class_name,
                "vectorizer": "none",
                "properties": [
                    {"name": "metadata", "dataType": ["text"]},
                ],
            }
            client.schema.create_class(class_obj)

        with client.batch as batch:
            batch.batch_size = 100
            for id, embedding, metadata in zip(ids, embeddings, metadatas, strict=False):
                batch.add_data_object(
                    data_object={"metadata": str(metadata)},
                    class_name=class_name,
                    uuid=id,
                    vector=embedding,
                )

    async def _query_request(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        class_name = collection.capitalize()

        query = client.query.get(class_name, ["metadata"]).with_near_vector({
            "vector": query_embedding,
        }).with_limit(n_results)

        if where:
            # Convert where filter to Weaviate format
            pass

        result = query.do()

        objects = result.get("data", {}).get("Get", {}).get(class_name, [])

        return {
            "ids": [obj.get("_additional", {}).get("id", "") for obj in objects],
            "embeddings": [],  # Weaviate doesn't return vectors by default
            "metadatas": [obj.get("metadata", {}) for obj in objects],
            "distances": [obj.get("_additional", {}).get("certainty", 0) for obj in objects],
        }

    async def _delete_request(self, collection: str, ids: list[str]) -> None:
        client = await self._get_client()
        class_name = collection.capitalize()

        for id in ids:
            client.data_object.delete(uuid=id, class_name=class_name)

    async def _get_request(self, collection: str, id: str) -> dict[str, Any] | None:
        client = await self._get_client()
        class_name = collection.capitalize()

        try:
            result = client.data_object.get_by_id(uuid=id, class_name=class_name, with_vector=True)
            if result:
                return {
                    "id": id,
                    "embedding": result.get("vector"),
                    "metadata": result.get("properties", {}).get("metadata", {}),
                }
        except Exception:
            pass
        return None


class QdrantAdapter(BaseVectorDBAdapter):
    """Qdrant adapter"""

    def __init__(self, host: str = "localhost", port: int = 6333, api_key: str | None = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
            )
        return self._client

    async def _upsert_request(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        client = await self._get_client()

        # Ensure collection exists
        collections = client.get_collections().collections
        if collection not in [c.name for c in collections]:
            client.create_collection(
                collection_name=collection,
                vectors_config={"size": len(embeddings[0]), "distance": "Cosine"},
            )

        points = [
            {
                "id": id,
                "vector": embedding,
                "payload": metadata,
            }
            for id, embedding, metadata in zip(ids, embeddings, metadatas, strict=False)
        ]

        client.upsert(collection_name=collection, points=points)

    async def _query_request(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None,
    ) -> dict[str, Any]:
        client = await self._get_client()

        filter_condition = None
        if where:
            # Convert where to Qdrant filter
            from qdrant_client.models import FieldCondition, Filter, MatchValue
            conditions = []
            for key, value in where.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            filter_condition = Filter(must=conditions)

        result = client.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=filter_condition,
            with_payload=True,
            with_vectors=True,
        )

        return {
            "ids": [hit.id for hit in result],
            "embeddings": [hit.vector for hit in result],
            "metadatas": [hit.payload for hit in result],
            "distances": [hit.score for hit in result],
        }

    async def _delete_request(self, collection: str, ids: list[str]) -> None:
        client = await self._get_client()
        client.delete(collection_name=collection, points_selector=ids)

    async def _get_request(self, collection: str, id: str) -> dict[str, Any] | None:
        client = await self._get_client()

        result = client.retrieve(collection_name=collection, ids=[id], with_vectors=True, with_payload=True)
        if result:
            point = result[0]
            return {
                "id": point.id,
                "embedding": point.vector,
                "metadata": point.payload,
            }
        return None
