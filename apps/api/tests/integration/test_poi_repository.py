"""
Integration tests for POI Repository
"""
import pytest
from uuid import uuid4
from datetime import datetime

from ai_smart_city_concierge.domain.aggregates.poi_aggregate import POI, POICategory
from ai_smart_city_concierge.domain.value_objects.address import Address
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours, DayOfWeek, TimeRange
from ai_smart_city_concierge.domain.value_objects.rating import Rating
from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.repositories.poi_repository import POIRepository


@pytest.fixture
async def poi_repository(db_session):
    """Create a POI repository instance"""
    return POIRepository(db_session)


@pytest.fixture
def sample_poi():
    """Create a sample POI for testing"""
    return POI.create(
        name="Test Restaurant",
        category=POICategory.RESTAURANT,
        address=Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        ),
        coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
        description="A great test restaurant",
        phone="+1-555-0123",
        website="https://example.com",
        opening_hours=OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [TimeRange(time(9, 0), time(22, 0))],
                DayOfWeek.TUESDAY: [TimeRange(time(9, 0), time(22, 0))],
                DayOfWeek.WEDNESDAY: [TimeRange(time(9, 0), time(22, 0))],
                DayOfWeek.THURSDAY: [TimeRange(time(9, 0), time(22, 0))],
                DayOfWeek.FRIDAY: [TimeRange(time(9, 0), time(23, 0))],
                DayOfWeek.SATURDAY: [TimeRange(time(10, 0), time(23, 0))],
                DayOfWeek.SUNDAY: [TimeRange(time(10, 0), time(21, 0))],
            }
        ),
        rating=Rating(value=4.5, count=100),
        price_level=2,
        tags=["italian", "pizza", "casual"],
    )


class TestPOIRepository:
    """Test POI Repository integration"""
    
    @pytest.mark.asyncio
    async def test_create_poi(self, poi_repository, sample_poi):
        """Test creating a POI in the database"""
        created_poi = await poi_repository.create(sample_poi)
        
        assert created_poi.id is not None
        assert created_poi.name == "Test Restaurant"
        assert created_poi.category == POICategory.RESTAURANT
        assert created_poi.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_poi_by_id(self, poi_repository, sample_poi):
        """Test retrieving a POI by ID"""
        created_poi = await poi_repository.create(sample_poi)
        
        retrieved_poi = await poi_repository.get_by_id(created_poi.id)
        
        assert retrieved_poi is not None
        assert retrieved_poi.id == created_poi.id
        assert retrieved_poi.name == created_poi.name
        assert retrieved_poi.category == created_poi.category
    
    @pytest.mark.asyncio
    async def test_get_poi_by_id_not_found(self, poi_repository):
        """Test retrieving a non-existent POI"""
        non_existent_id = uuid4()
        retrieved_poi = await poi_repository.get_by_id(non_existent_id)
        
        assert retrieved_poi is None
    
    @pytest.mark.asyncio
    async def test_update_poi(self, poi_repository, sample_poi):
        """Test updating a POI"""
        created_poi = await poi_repository.create(sample_poi)
        
        created_poi.update(name="Updated Restaurant", description="Updated description")
        updated_poi = await poi_repository.update(created_poi)
        
        assert updated_poi.name == "Updated Restaurant"
        assert updated_poi.description == "Updated description"
        assert updated_poi.updated_at > created_poi.created_at
    
    @pytest.mark.asyncio
    async def test_delete_poi(self, poi_repository, sample_poi):
        """Test deleting a POI"""
        created_poi = await poi_repository.create(sample_poi)
        
        result = await poi_repository.delete(created_poi.id)
        
        assert result is True
        
        # Verify it's deleted
        retrieved_poi = await poi_repository.get_by_id(created_poi.id)
        assert retrieved_poi is None
    
    @pytest.mark.asyncio
    async def test_delete_poi_not_found(self, poi_repository):
        """Test deleting a non-existent POI"""
        non_existent_id = uuid4()
        result = await poi_repository.delete(non_existent_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_pois(self, poi_repository, sample_poi):
        """Test listing POIs with pagination"""
        # Create multiple POIs
        poi1 = await poi_repository.create(sample_poi)
        
        poi2 = POI.create(
            name="Test Cafe",
            category=POICategory.CAFE,
            address=Address("456 Cafe St", "New York", "NY", "10002", "USA"),
            coordinates=Coordinates(40.7580, -73.9855),
        )
        await poi_repository.create(poi2)
        
        poi3 = POI.create(
            name="Test Museum",
            category=POICategory.MUSEUM,
            address=Address("789 Museum Ave", "New York", "NY", "10003", "USA"),
            coordinates=Coordinates(40.7794, -73.9632),
        )
        await poi_repository.create(poi3)
        
        # List with pagination
        pois, total = await poi_repository.list(page=1, page_size=2)
        
        assert total == 3
        assert len(pois) == 2
        
        # Second page
        pois_page2, total2 = await poi_repository.list(page=2, page_size=2)
        assert total2 == 3
        assert len(pois_page2) == 1
    
    @pytest.mark.asyncio
    async def test_list_pois_with_category_filter(self, poi_repository, sample_poi):
        """Test listing POIs filtered by category"""
        await poi_repository.create(sample_poi)  # RESTAURANT
        
        cafe = POI.create(
            name="Test Cafe",
            category=POICategory.CAFE,
            address=Address("456 Cafe St", "New York", "NY", "10002", "USA"),
            coordinates=Coordinates(40.7580, -73.9855),
        )
        await poi_repository.create(cafe)
        
        # Filter by RESTAURANT
        pois, total = await poi_repository.list(category=POICategory.RESTAURANT)
        
        assert total == 1
        assert len(pois) == 1
        assert pois[0].category == POICategory.RESTAURANT
    
    @pytest.mark.asyncio
    async def test_search_pois_by_name(self, poi_repository, sample_poi):
        """Test searching POIs by name"""
        await poi_repository.create(sample_poi)
        
        cafe = POI.create(
            name="Another Cafe",
            category=POICategory.CAFE,
            address=Address("456 Cafe St", "New York", "NY", "10002", "USA"),
            coordinates=Coordinates(40.7580, -73.9855),
        )
        await poi_repository.create(cafe)
        
        # Search for "Restaurant"
        pois = await poi_repository.search_by_name("Restaurant")
        
        assert len(pois) == 1
        assert pois[0].name == "Test Restaurant"
    
    @pytest.mark.asyncio
    async def test_search_pois_nearby(self, poi_repository, sample_poi):
        """Test searching POIs near coordinates"""
        await poi_repository.create(sample_poi)  # Near NYC
        
        # Create POI far away (LA)
        la_poi = POI.create(
            name="LA Restaurant",
            category=POICategory.RESTAURANT,
            address=Address("123 LA St", "Los Angeles", "CA", "90001", "USA"),
            coordinates=Coordinates(34.0522, -118.2437),
        )
        await poi_repository.create(la_poi)
        
        # Search near NYC (within 50km)
        nyc_coords = Coordinates(40.7128, -74.0060)
        pois = await poi_repository.search_nearby(nyc_coords, radius_km=50)
        
        assert len(pois) == 1
        assert pois[0].name == "Test Restaurant"
    
    @pytest.mark.asyncio
    async def test_get_pois_by_category(self, poi_repository, sample_poi):
        """Test getting POIs by category"""
        await poi_repository.create(sample_poi)
        
        cafe = POI.create(
            name="Test Cafe",
            category=POICategory.CAFE,
            address=Address("456 Cafe St", "New York", "NY", "10002", "USA"),
            coordinates=Coordinates(40.7580, -73.9855),
        )
        await poi_repository.create(cafe)
        
        restaurants = await poi_repository.get_by_category(POICategory.RESTAURANT)
        
        assert len(restaurants) == 1
        assert restaurants[0].category == POICategory.RESTAURANT
    
    @pytest.mark.asyncio
    async def test_count_pois(self, poi_repository, sample_poi):
        """Test counting POIs"""
        initial_count = await poi_repository.count()
        
        await poi_repository.create(sample_poi)
        
        new_count = await poi_repository.count()
        assert new_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_count_pois_by_category(self, poi_repository, sample_poi):
        """Test counting POIs by category"""
        initial_count = await poi_repository.count_by_category(POICategory.RESTAURANT)
        
        await poi_repository.create(sample_poi)
        
        new_count = await poi_repository.count_by_category(POICategory.RESTAURANT)
        assert new_count == initial_count + 1
        
        # Other category should not change
        cafe_count = await poi_repository.count_by_category(POICategory.CAFE)
        assert cafe_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])