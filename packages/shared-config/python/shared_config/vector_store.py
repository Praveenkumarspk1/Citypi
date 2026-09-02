"""
Vector Store Settings

Configuration for vector databases (ChromaDB, Qdrant, etc.).
"""
from typing import List
from pydantic import Field
from .base import BaseSettings


class VectorStoreSettings(BaseSettings):
    """Vector store configuration."""
    
    # Provider
    vector_store_provider: str = "chromadb"  # chromadb, qdrant, pinecone

    # ChromaDB
    chromadb_host: str = Field(default="localhost", validation_alias="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, validation_alias="CHROMADB_PORT")
    chromadb_api_key: str = Field(default="", validation_alias="CHROMADB_API_KEY")
    chromadb_ssl: bool = False
    chromadb_tenant: str = "default"
    chromadb_database: str = "default"

    # Qdrant
    qdrant_host: str = Field(default="localhost", validation_alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, validation_alias="QDRANT_PORT")
    qdrant_api_key: str = Field(default="", validation_alias="QDRANT_API_KEY")
    qdrant_ssl: bool = False
    qdrant_prefer_grpc: bool = False

    # Pinecone
    pinecone_api_key: str = Field(default="", validation_alias="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="", validation_alias="PINECONE_ENVIRONMENT")
    pinecone_index: str = Field(default="concierge", validation_alias="PINECONE_INDEX")

    # Embedding
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32

    # Collections
    collection_poi_embeddings: str = "poi_embeddings"
    collection_conversation_embeddings: str = "conversation_embeddings"
    collection_itinerary_embeddings: str = "itinerary_embeddings"
    collection_media_embeddings: str = "media_embeddings"
    collection_document_embeddings: str = "document_embeddings"
    collection_landmark_embeddings: str = "landmark_embeddings"

    # Search
    default_search_limit: int = 10
    default_distance_metric: str = "cosine"  # cosine, euclidean, dot
    hnsw_ef_search: int = 128
    hnsw_ef_construction: int = 256
    hnsw_m: int = 16