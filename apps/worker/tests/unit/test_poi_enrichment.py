"""
Unit tests for POI enrichment tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from apps.worker.src.tasks.poi_enrichment import (
    enrich_poi_from_overpass,
    enrich_poi_from_nominatim,
    enrich_poi_photos,
    enrich_poi_reviews,
    batch_enrich_pois,
)
from ai_smart_city_concierge.domain.aggregates.poi_aggregate import POIAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityFeatures
from ai_smart_city_concierge.domain.value_objects.rating import Rating


class TestPOIEnrichment:
    """Test cases for POI enrichment tasks"""

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

    @pytest.mark.asyncio
    async def test_enrich_poi_from_overpass(self, mock_poi):
        """Test enriching POI from Overpass API"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_overpass_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_poi_details.return_value = {
                "opening_hours": "Mo-Su 09:00-23:00",
                "phone": "+33 8 92 70 12 39",
                "website": "https://www.toureiffel.paris",
                "wheelchair": "yes",
                "wikidata": "Q243",
                "wikipedia": "en:Eiffel Tower",
            }
            mock_client.return_value = mock_client_instance

            enriched_poi = await enrich_poi_from_overpass(mock_poi)

            assert enriched_poi is not None
            assert enriched_poi.phone == "+33 8 92 70 12 39"
            assert enriched_poi.website == "https://www.toureiffel.paris"
            assert enriched_poi.wikidata_id == "Q243"
            assert enriched_poi.wikipedia_url == "https://en.wikipedia.org/wiki/Eiffel_Tower"
            mock_client_instance.get_poi_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_poi_from_nominatim(self, mock_poi):
        """Test enriching POI from Nominatim API"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_nominatim_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.reverse_geocode.return_value = {
                "address": {
                    "road": "Avenue Anatole France",
                    "suburb": "Champ de Mars",
                    "city": "Paris",
                    "postcode": "75007",
                    "country": "France",
                    "country_code": "fr",
                },
                "display_name": "Eiffel Tower, Avenue Anatole France, Champ de Mars, 75007 Paris, France",
            }
            mock_client.return_value = mock_client_instance

            enriched_poi = await enrich_poi_from_nominatim(mock_poi)

            assert enriched_poi is not None
            assert "Avenue Anatole France" in enriched_poi.address
            assert "75007" in enriched_poi.address
            mock_client_instance.reverse_geocode.assert_called_once_with(
                mock_poi.coordinates.latitude, mock_poi.coordinates.longitude
            )

    @pytest.mark.asyncio
    async def test_enrich_poi_photos(self, mock_poi):
        """Test enriching POI with photos"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_clip_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.search_images.return_value = [
                {
                    "url": "https://example.com/photo1.jpg",
                    "thumbnail_url": "https://example.com/thumb1.jpg",
                    "attribution": "Photo by John Doe",
                    "license": "CC BY-SA 4.0",
                },
                {
                    "url": "https://example.com/photo2.jpg",
                    "thumbnail_url": "https://example.com/thumb2.jpg",
                    "attribution": "Photo by Jane Smith",
                    "license": "CC BY 2.0",
                },
            ]
            mock_client.return_value = mock_client_instance

            enriched_poi = await enrich_poi_photos(mock_poi, max_photos=5)

            assert enriched_poi is not None
            assert len(enriched_poi.photos) == 2
            assert enriched_poi.photos[0].url == "https://example.com/photo1.jpg"
            assert enriched_poi.photos[1].attribution == "Photo by Jane Smith"
            mock_client_instance.search_images.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_poi_reviews(self, mock_poi):
        """Test enriching POI with reviews"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.generate_reviews_summary.return_value = {
                "summary": "Visitors love the stunning views from the top. The tower is iconic but can be crowded.",
                "sentiment": "positive",
                "key_topics": ["views", "crowds", "iconic", "expensive"],
                "sample_reviews": [
                    {"rating": 5, "text": "Amazing experience!", "date": "2024-01-15"},
                    {"rating": 4, "text": "Great views but long lines", "date": "2024-01-10"},
                ],
            }
            mock_client.return_value = mock_client_instance

            enriched_poi = await enrich_poi_reviews(mock_poi)

            assert enriched_poi is not None
            assert "stunning views" in enriched_poi.reviews_summary
            assert enriched_poi.reviews_sentiment == "positive"
            assert "views" in enriched_poi.review_topics
            mock_client_instance.generate_reviews_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_enrich_pois(self, mock_poi):
        """Test batch enriching multiple POIs"""
        poi2 = POIAggregate.create(
            name="Louvre Museum",
            description="World's largest art museum",
            category="museum",
            subcategory="art_museum",
            coordinates=Coordinates(latitude=48.8606, longitude=2.3376),
            address="Rue de Rivoli, 75001 Paris",
            opening_hours=OpeningHours(),
            accessibility=AccessibilityFeatures(),
            rating=Rating(value=4.7, review_count=50000),
            tags=["museum", "art", "paris"],
        )

        with patch('apps.worker.src.tasks.poi_enrichment.enrich_poi_from_overpass') as mock_overpass, \
             patch('apps.worker.src.tasks.poi_enrichment.enrich_poi_from_nominatim') as mock_nominatim, \
             patch('apps.worker.src.tasks.poi_enrichment.enrich_poi_photos') as mock_photos, \
             patch('apps.worker.src.tasks.poi_enrichment.enrich_poi_reviews') as mock_reviews:

            mock_overpass.return_value = mock_poi
            mock_nominatim.return_value = mock_poi
            mock_photos.return_value = mock_poi
            mock_reviews.return_value = mock_poi

            pois = [mock_poi, poi2]
            enriched = await batch_enrich_pois(pois)

            assert len(enriched) == 2
            assert mock_overpass.call_count == 2
            assert mock_nominatim.call_count == 2
            assert mock_photos.call_count == 2
            assert mock_reviews.call_count == 2

    @pytest.mark.asyncio
    async def test_enrichment_handles_missing_data(self, mock_poi):
        """Test that enrichment handles missing data gracefully"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_overpass_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_poi_details.return_value = {}
            mock_client.return_value = mock_client_instance

            enriched_poi = await enrich_poi_from_overpass(mock_poi)

            assert enriched_poi is not None
            # Should not crash, just not add new data
            assert enriched_poi.phone is None or enriched_poi.phone == mock_poi.phone

    @pytest.mark.asyncio
    async def test_enrichment_handles_api_error(self, mock_poi):
        """Test that enrichment handles API errors gracefully"""
        with patch('apps.worker.src.tasks.poi_enrichment.get_overpass_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_poi_details.side_effect = Exception("API timeout")
            mock_client.return_value = mock_client_instance

            # Should not raise, should return original POI
            enriched_poi = await enrich_poi_from_overpass(mock_poi)
            assert enriched_poi is not None
            assert enriched_poi.id == mock_poi.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])