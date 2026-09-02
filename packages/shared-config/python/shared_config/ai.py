"""
AI Settings

Configuration for AI/ML models and services.
"""
from pydantic import Field
from .base import BaseSettings


class AISettings(BaseSettings):
    """AI/ML configuration."""
    
    # Embedding models
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_normalize: bool = True

    # LLM
    llm_model: str = "gemini-1.5-pro"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_top_p: float = 0.95
    llm_top_k: int = 40
    llm_timeout: int = 60
    llm_max_retries: int = 3

    # Speech-to-Text
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "float32"
    whisper_language: str = "en"
    whisper_task: str = "transcribe"

    # Vision
    clip_model_name: str = "openai/clip-vit-base-patch32"
    clip_device: str = "cpu"
    clip_batch_size: int = 32

    # Recommendation
    lightfm_components: int = 64
    lightfm_learning_rate: float = 0.05
    lightfm_loss: str = "warp"
    lightfm_epochs: int = 10
    lightfm_num_threads: int = 4
    lightfm_item_alpha: float = 1e-6
    lightfm_user_alpha: float = 1e-6

    # Reranking
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_device: str = "cpu"
    reranker_top_k: int = 50

    # Summarization
    summarization_model: str = "facebook/bart-large-cnn"
    summarization_max_length: int = 150
    summarization_min_length: int = 30

    # Sentiment
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    sentiment_device: str = "cpu"

    # Intent classification
    intent_model: str = "microsoft/DialoGPT-medium"
    intent_device: str = "cpu"
    intent_confidence_threshold: float = 0.7

    # Entity extraction
    ner_model: str = "dslim/bert-base-NER"
    ner_device: str = "cpu"
    ner_confidence_threshold: float = 0.8

    # Translation
    translation_model: str = "Helsinki-NLP/opus-mt-mul-en"
    translation_device: str = "cpu"

    # Cache
    model_cache_dir: str = "./models"
    enable_model_cache: bool = True