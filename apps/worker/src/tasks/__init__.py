"""
Worker Tasks Package

Background job tasks for the AI Smart City Concierge.
"""

from .conversation_analysis import ConversationAnalysisTask
from .conversation_analysis import ConversationAnalysisTask as ConversationAnalysisTaskClass
from .embedding_generation import EmbeddingGenerationTask, EmbeddingTask
from .itinerary_generation import ItineraryGenerationTask
from .itinerary_generation import ItineraryGenerationTask as ItineraryGenerationTaskClass
from .media_processing import MediaProcessingTask
from .media_processing import MediaProcessingTask as MediaProcessingTaskClass
from .poi_enrichment import POIEnrichmentTask
from .poi_enrichment import POIEnrichmentTask as POIEnrichmentTaskClass
from .transit_sync import TransitSyncTask
from .transit_sync import TransitSyncTask as TransitSyncTaskClass
from .weather_sync import WeatherSyncTask
from .weather_sync import WeatherSyncTask as WeatherSyncTaskClass

__all__ = [
    "EmbeddingGenerationTask",
    "EmbeddingTask",
    "POIEnrichmentTask",
    "TransitSyncTask",
    "WeatherSyncTask",
    "ItineraryGenerationTask",
    "MediaProcessingTask",
    "ConversationAnalysisTask",
]
