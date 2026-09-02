"""
Embedding Service Adapters
"""
from abc import ABC, abstractmethod

from ....application.ports.external_services import EmbeddingServicePort


class BaseEmbeddingAdapter(EmbeddingServicePort, ABC):
    """Base embedding adapter"""

    @abstractmethod
    async def _generate_embedding_request(self, text: str) -> list[float]:
        """Generate embedding request"""
        pass

    @abstractmethod
    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings request"""
        pass

    @abstractmethod
    def _get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

    @abstractmethod
    def _get_model_name(self) -> str:
        """Get model name"""
        pass

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text"""
        return await self._generate_embedding_request(text)

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        return await self._generate_embeddings_request(texts)

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self._get_dimension()

    def get_model_name(self) -> str:
        """Get model name"""
        return self._get_model_name()


class BGEEmbeddingAdapter(BaseEmbeddingAdapter):
    """BAAI/bge-m3 embedding adapter (local)"""

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

    async def _load_model(self):
        if self._model is None:
            from transformers import AutoModel, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()

    async def _generate_embedding_request(self, text: str) -> list[float]:
        await self._load_model()
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            # Use CLS token embedding
            embedding = outputs.last_hidden_state[:, 0].cpu().numpy()[0]

        return embedding.tolist()

    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        await self._load_model()
        import torch

        inputs = self._tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0].cpu().numpy()

        return embeddings.tolist()

    def _get_dimension(self) -> int:
        return 1024  # bge-m3 dimension

    def _get_model_name(self) -> str:
        return self.model_name


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """OpenAI embedding adapter"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def _generate_embedding_request(self, text: str) -> list[float]:
        client = await self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        client = await self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [data.embedding for data in response.data]

    def _get_dimension(self) -> int:
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(self.model, 1536)

    def _get_model_name(self) -> str:
        return self.model


class CohereEmbeddingAdapter(BaseEmbeddingAdapter):
    """Cohere embedding adapter"""

    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import cohere
            self._client = cohere.AsyncClient(api_key=self.api_key)
        return self._client

    async def _generate_embedding_request(self, text: str) -> list[float]:
        client = await self._get_client()
        response = await client.embed(
            texts=[text],
            model=self.model,
            input_type="search_document",
        )
        return response.embeddings[0]

    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        client = await self._get_client()
        response = await client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document",
        )
        return response.embeddings

    def _get_dimension(self) -> int:
        dimensions = {
            "embed-english-v3.0": 1024,
            "embed-multilingual-v3.0": 1024,
            "embed-english-light-v3.0": 384,
            "embed-multilingual-light-v3.0": 384,
        }
        return dimensions.get(self.model, 1024)

    def _get_model_name(self) -> str:
        return self.model


class SentenceTransformersAdapter(BaseEmbeddingAdapter):
    """Sentence Transformers adapter (local)"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    async def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)

    async def _generate_embedding_request(self, text: str) -> list[float]:
        await self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        await self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings.tolist()

    def _get_dimension(self) -> int:
        # Common dimensions for popular models
        dimensions = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/all-MiniLM-L12-v2": 384,
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
        }
        return dimensions.get(self.model_name, 384)

    def _get_model_name(self) -> str:
        return self.model_name


class InstructorEmbeddingAdapter(BaseEmbeddingAdapter):
    """Instructor embedding adapter (local)"""

    def __init__(self, model_name: str = "hkunlp/instructor-xl", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    async def _load_model(self):
        if self._model is None:
            from InstructorEmbedding import INSTRUCTOR
            self._model = INSTRUCTOR(self.model_name, device=self.device)

    async def _generate_embedding_request(self, text: str) -> list[float]:
        await self._load_model()
        # Instructor requires instruction
        instruction = "Represent the document for retrieval:"
        embedding = self._model.encode([[instruction, text]])[0]
        return embedding.tolist()

    async def _generate_embeddings_request(self, texts: list[str]) -> list[list[float]]:
        await self._load_model()
        instruction = "Represent the document for retrieval:"
        pairs = [[instruction, text] for text in texts]
        embeddings = self._model.encode(pairs)
        return embeddings.tolist()

    def _get_dimension(self) -> int:
        dimensions = {
            "hkunlp/instructor-xl": 768,
            "hkunlp/instructor-large": 768,
            "hkunlp/instructor-base": 768,
        }
        return dimensions.get(self.model_name, 768)

    def _get_model_name(self) -> str:
        return self.model_name
