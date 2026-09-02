"""
Unit tests for embedding generation tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.worker.src.tasks.embedding_generation import (
    generate_poi_embedding,
    generate_itinerary_embedding,
    generate_conversation_embedding,
    batch_generate_embeddings,
)
from ai_smart_city_concierge.domain.aggregates.poi_aggregate import POIAggregate
from ai_smart_city_concierge.domain.aggregates.itinerary_aggregate import ItineraryAggregate
from ai_smart_city_concierge.domain.aggregates.conversation_aggregate import ConversationAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityFeatures
from ai_smart_city_concierge.domain.value_objects.rating import Rating


class TestEmbeddingGeneration:
    """Test cases for embedding generation tasks"""

    @pytest.fixture
    def mock_poi(self):
        """Create a mock POI aggregate"""
        poi = POIAggregate.create(
            name="Eiffel Tower",
            description="Iconic iron lattice tower",
            category="landmark",
            subcategory="tower",
            coordinates=Coordinates(latitude=48.8584, longitude=2.2945),
            address="Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
            opening_hours=OpeningHours(),
            accessibility=AccessibilityFeatures(),
            rating=Rating(value=4.5, review_count=10000),
            tags=["tourist_attraction", "landmark", "paris"],
        )
        return poi

    @pytest.fixture
    def mock_itinerary(self):
        """Create a mock itinerary aggregate"""
        from datetime import date, time, timedelta
        from ai_smart_city_concierge.domain.value_objects.money import Money
        from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode

        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            description="3 days in Paris",
            start_date=start_date,
            end_date=end_date,
            timezone="Europe/Paris",
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1 - Arrival")
        itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Eiffel Tower",
            start_time=time(10, 0),
            end_time=time(12, 0),
            duration_minutes=120,
            address="Eiffel Tower",
            estimated_cost=Money(amount=25.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        return itinerary

    @pytest.fixture
    def mock_conversation(self):
        """Create a mock conversation aggregate"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Paris Travel Planning",
            language="en",
        )
        conversation.add_message(role="user", content="I want to visit Paris for 3 days")
        conversation.add_message(role="assistant", content="Great! Paris is a wonderful destination...")
        conversation.add_message(role="user", content="What are the must-see attractions?")
        return conversation

    @pytest.mark.asyncio
    async def test_generate_poi_embedding(self, mock_poi):
        """Test generating embedding for a POI"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_text.return_value = [0.1] * 1024  # BGE-M3 embedding dimension
            mock_client.return_value = mock_client_instance

            embedding = await generate_poi_embedding(mock_poi)

            assert embedding is not None
            assert len(embedding) == 1024
            mock_client_instance.embed_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_itinerary_embedding(self, mock_itinerary):
        """Test generating embedding for an itinerary"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_text.return_value = [0.1] * 1024
            mock_client.return_value = mock_client_instance

            embedding = await generate_itinerary_embedding(mock_itinerary)

            assert embedding is not None
            assert len(embedding) == 1024
            mock_client_instance.embed_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_conversation_embedding(self, mock_conversation):
        """Test generating embedding for a conversation"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_text.return_value = [0.1] * 1024
            mock_client.return_value = mock_client_instance

            embedding = await generate_conversation_embedding(mock_conversation)

            assert embedding is not None
            assert len(embedding) == 1024
            mock_client_instance.embed_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self, mock_poi, mock_itinerary, mock_conversation):
        """Test batch generating embeddings"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_batch.return_value = [[0.1] * 1024] * 3
            mock_client.return_value = mock_client_instance

            items = [
                ("poi", mock_poi),
                ("itinerary", mock_itinerary),
                ("conversation", mock_conversation),
            ]

            embeddings = await batch_generate_embeddings(items)

            assert len(embeddings) == 3
            assert all(len(e) == 1024 for e in embeddings)
            mock_client_instance.embed_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_poi_embedding_handles_error(self, mock_poi):
        """Test that embedding generation handles errors gracefully"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_text.side_effect = Exception("API Error")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="API Error"):
                await generate_poi_embedding(mock_poi)

    @pytest.mark.asyncio
    async def test_embedding_text_content(self, mock_poi):
        """Test that the correct text content is used for embedding"""
        with patch('apps.worker.src.tasks.embedding_generation.get_bge_m3_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.embed_text.return_value = [0.1] * 1024
            mock_client.return_value = mock_client_instance

            await generate_poi_embedding(mock_poi)

            # Check that embed_text was called with relevant POI information
            call_args = mock_client_instance.embed_text.call_args[0][0]
            assert "Eiffel Tower" in call_args
            assert "Iconic iron lattice tower" in call_args
            assert "landmark" in call_args
            assert "tower" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])