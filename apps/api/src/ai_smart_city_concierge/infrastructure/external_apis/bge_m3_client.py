"""
BAAI/bge-m3 Embedding Client
"""
import os

import torch
from sentence_transformers import SentenceTransformer

from ...application.ports.external_services import EmbeddingServicePort


class BGEM3Client(EmbeddingServicePort):
    """BAAI/bge-m3 embedding model client (local)"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir or os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
        self._model: SentenceTransformer | None = None
        self._dimension = 1024  # bge-m3 dimension

    def _get_model(self) -> SentenceTransformer:
        """Lazy load model"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
            )
        return self._model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name

    async def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = await self.generate_embedding(text1)
        emb2 = await self.generate_embedding(text2)

        import numpy as np
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10,
    ) -> list[Dict[str, Any]]:
        """Rerank documents by relevance to query (using cross-encoder if available)"""
        # For bge-m3, we can use the dense embeddings for reranking
        query_emb = await self.generate_embedding(query)
        doc_embs = await self.generate_embeddings(documents)

        import numpy as np
        query_vec = np.array(query_emb)

        scores = []
        for i, doc_emb in enumerate(doc_embs):
            doc_vec = np.array(doc_emb)
            score = float(np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)))
            scores.append({"index": i, "score": score, "document": documents[i]})

        # Sort by score descending
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]


# For cross-encoder reranking (bge-reranker-base)
class BGERerankerClient:
    """BAAI/bge-reranker-base cross-encoder for reranking"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str | None = None,
        cache_dir: str | None = None,
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir or os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy load cross-encoder model"""
        if self._model is None:
            # Use CrossEncoder for reranking
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
            )
        return self._model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10,
    ) -> list[Dict[str, Any]]:
        """Rerank documents using cross-encoder"""
        model = self._get_model()

        # Prepare pairs for cross-encoder
        pairs = [[query, doc] for doc in documents]

        # Get scores
        scores = model.predict(pairs, show_progress_bar=False)

        results = []
        for i, score in enumerate(scores):
            results.append({
                "index": i,
                "score": float(score),
                "document": documents[i],
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
