"""
Unit tests for itinerary generation tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, time, timedelta
from uuid import uuid4

from apps.worker.src.tasks.itinerary_generation import (
    generate_itinerary,
    optimize_itinerary,
    generate_itinerary_from_preferences,
    suggest_pois_for_itinerary,
)
from ai_smart_city_concierge.domain.aggregates.itinerary_aggregate import ItineraryAggregate
from ai_smart_city_concierge.domain.aggregates.user_aggregate import UserAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.money import Money
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityFeatures
from ai_smart_city_concierge.domain.value_objects.rating import Rating


class TestItineraryGeneration:
    """Test cases for itinerary generation tasks"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user aggregate"""
        user = UserAggregate.create(
            email="test@example.com",
            name="Test User",
            preferences={
                "travel_style": "cultural",
                "budget_level": "moderate",
                "preferred_transport": ["walking", "transit"],
                "interests": ["museums", "landmarks", "food"],
                "accessibility_needs": [],
            },
        )
        return user

    @pytest.fixture
    def mock_pois(self):
        """Create mock POIs"""
        pois = []
        poi_data = [
            ("Eiffel Tower", "landmark", 48.8584, 2.2945, 4.5),
            ("Louvre Museum", "museum", 48.8606, 2.3376, 4.7),
            ("Notre Dame", "landmark", 48.8530, 2.3499, 4.6),
            ("Montmartre", "neighborhood", 48.8867, 2.3431, 4.4),
            ("Seine River Cruise", "activity", 48.8566, 2.3522, 4.3),
        ]
        for name, category, lat, lon, rating in poi_data:
            poi = POIAggregate.create(
                name=name,
                description=f"Description for {name}",
                category=category,
                subcategory=category,
                coordinates=Coordinates(latitude=lat, longitude=lon),
                address=f"Address for {name}",
                opening_hours=OpeningHours(),
                accessibility=AccessibilityFeatures(),
                rating=Rating(value=rating, review_count=1000),
                tags=[category, "paris"],
            )
            pois.append(poi)
        return pois

    @pytest.mark.asyncio
    async def test_generate_itinerary(self, mock_user, mock_pois):
        """Test generating an itinerary"""
        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini, \
             patch('apps.worker.src.tasks.itinerary_generation.get_poi_repository') as mock_poi_repo:

            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.generate_itinerary.return_value = {
                "title": "3 Days in Paris",
                "description": "Cultural highlights of Paris",
                "days": [
                    {
                        "date": "2024-06-15",
                        "title": "Day 1 - Icons",
                        "items": [
                            {"type": "poi", "title": "Eiffel Tower", "start_time": "09:00", "end_time": "11:00", "duration_minutes": 120},
                            {"type": "poi", "title": "Seine River Cruise", "start_time": "11:30", "end_time": "12:30", "duration_minutes": 60},
                        ],
                    },
                    {
                        "date": "2024-06-16",
                        "title": "Day 2 - Art & Culture",
                        "items": [
                            {"type": "poi", "title": "Louvre Museum", "start_time": "09:00", "end_time": "13:00", "duration_minutes": 240},
                        ],
                    },
                ],
            }
            mock_gemini.return_value = mock_gemini_instance

            mock_poi_repo_instance = AsyncMock()
            mock_poi_repo_instance.search.return_value = mock_pois
            mock_poi_repo.return_value = mock_poi_repo_instance

            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=2)

            itinerary = await generate_itinerary(
                user_id=mock_user.id,
                start_date=start_date,
                end_date=end_date,
                preferences=mock_user.preferences,
            )

            assert itinerary is not None
            assert itinerary.title == "3 Days in Paris"
            assert len(itinerary.days) == 2
            mock_gemini_instance.generate_itinerary.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_itinerary(self, mock_user, mock_pois):
        """Test optimizing an existing itinerary"""
        # Create an initial itinerary
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)
        
        itinerary = ItineraryAggregate.create(
            user_id=mock_user.id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )
        day_id = itinerary.add_day(date=start_date, title="Day 1")
        itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Eiffel Tower",
            start_time=time(14, 0),  # Afternoon - not optimal
            end_time=time(16, 0),
            duration_minutes=120,
            address="Eiffel Tower",
            estimated_cost=Money(amount=25.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )
        itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Louvre Museum",
            start_time=time(9, 0),  # Morning - better for Louvre
            end_time=time(13, 0),
            duration_minutes=240,
            address="Louvre Museum",
            estimated_cost=Money(amount=17.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini:
            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.optimize_itinerary.return_value = {
                "days": [
                    {
                        "date": str(start_date),
                        "title": "Day 1 - Optimized",
                        "items": [
                            {"type": "poi", "title": "Louvre Museum", "start_time": "09:00", "end_time": "13:00", "duration_minutes": 240},
                            {"type": "poi", "title": "Eiffel Tower", "start_time": "14:00", "end_time": "16:00", "duration_minutes": 120},
                        ],
                    },
                ],
            }
            mock_gemini.return_value = mock_gemini_instance

            optimized = await optimize_itinerary(itinerary)

            assert optimized is not None
            assert len(optimized.days) == 1
            # Louvre should come first (morning)
            assert optimized.days[0].items[0].title == "Louvre Museum"
            mock_gemini_instance.optimize_itinerary.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_itinerary_from_preferences(self, mock_user):
        """Test generating itinerary from user preferences only"""
        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini, \
             patch('apps.worker.src.tasks.itinerary_generation.get_poi_repository') as mock_poi_repo:

            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.generate_itinerary.return_value = {
                "title": "Foodie Paris",
                "description": "Best food experiences in Paris",
                "days": [
                    {
                        "date": "2024-06-15",
                        "title": "Day 1 - Food Tour",
                        "items": [
                            {"type": "poi", "title": "Le Marais Food Tour", "start_time": "10:00", "end_time": "13:00", "duration_minutes": 180},
                        ],
                    },
                ],
            }
            mock_gemini.return_value = mock_gemini_instance

            mock_poi_repo_instance = AsyncMock()
            mock_poi_repo_instance.search.return_value = []
            mock_poi_repo.return_value = mock_poi_repo_instance

            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=1)

            itinerary = await generate_itinerary_from_preferences(
                user_id=mock_user.id,
                start_date=start_date,
                end_date=end_date,
            )

            assert itinerary is not None
            assert itinerary.title == "Foodie Paris"

    @pytest.mark.asyncio
    async def test_suggest_pois_for_itinerary(self, mock_pois):
        """Test suggesting POIs for an itinerary"""
        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini, \
             patch('apps.worker.src.tasks.itinerary_generation.get_poi_repository') as mock_poi_repo:

            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.suggest_pois.return_value = [
                {"poi_id": str(mock_pois[0].id), "reason": "Iconic landmark, must-see"},
                {"poi_id": str(mock_pois[1].id), "reason": "World-class museum"},
            ]
            mock_gemini.return_value = mock_gemini_instance

            mock_poi_repo_instance = AsyncMock()
            mock_poi_repo_instance.get_by_ids.return_value = mock_pois[:2]
            mock_poi_repo.return_value = mock_poi_repo_instance

            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=2)

            suggestions = await suggest_pois_for_itinerary(
                destination="Paris",
                start_date=start_date,
                end_date=end_date,
                interests=["landmarks", "museums"],
                budget="moderate",
            )

            assert suggestions is not None
            assert len(suggestions) == 2
            assert suggestions[0]["poi_id"] == str(mock_pois[0].id)
            mock_gemini_instance.suggest_pois.assert_called_once()

    @pytest.mark.asyncio
    async def test_generation_handles_no_pois_found(self, mock_user):
        """Test generation when no POIs are found"""
        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini, \
             patch('apps.worker.src.tasks.itinerary_generation.get_poi_repository') as mock_poi_repo:

            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.generate_itinerary.return_value = {
                "title": "Empty Itinerary",
                "description": "No POIs available",
                "days": [],
            }
            mock_gemini.return_value = mock_gemini_instance

            mock_poi_repo_instance = AsyncMock()
            mock_poi_repo_instance.search.return_value = []
            mock_poi_repo.return_value = mock_poi_repo_instance

            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=2)

            itinerary = await generate_itinerary(
                user_id=mock_user.id,
                start_date=start_date,
                end_date=end_date,
                preferences=mock_user.preferences,
            )

            assert itinerary is not None
            assert len(itinerary.days) == 0

    @pytest.mark.asyncio
    async def test_generation_handles_api_error(self, mock_user):
        """Test generation handles API errors"""
        with patch('apps.worker.src.tasks.itinerary_generation.get_gemini_client') as mock_gemini:
            mock_gemini_instance = AsyncMock()
            mock_gemini_instance.generate_itinerary.side_effect = Exception("Gemini API error")
            mock_gemini.return_value = mock_gemini_instance

            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=2)

            with pytest.raises(Exception, match="Gemini API error"):
                await generate_itinerary(
                    user_id=mock_user.id,
                    start_date=start_date,
                    end_date=end_date,
                    preferences=mock_user.preferences,
                )


# Need to import POIAggregate for the test
from ai_smart_city_concierge.domain.aggregates.poi_aggregate import POIAggregate

if __name__ == "__main__":
    pytest.main([__file__, "-v"])