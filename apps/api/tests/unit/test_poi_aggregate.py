"""
Unit tests for POI Aggregate
"""
import pytest
from uuid import uuid4
from datetime import datetime

from ai_smart_city_concierge.domain.aggregates.poi_aggregate import POI, POICategory
from ai_smart_city_concierge.domain.value_objects.address import Address
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.opening_hours import OpeningHours, DayOfWeek
from ai_smart_city_concierge.domain.value_objects.rating import Rating
from ai_smart_city_concierge.domain.value_objects.accessibility import AccessibilityInfo
from ai_smart_city_concierge.domain.value_objects.money import Money


class TestPOI:
    """Test POI aggregate"""
    
    def test_create_poi_minimal(self):
        """Test creating a POI with minimal required fields"""
        poi = POI.create(
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
        )
        
        assert poi.name == "Test Restaurant"
        assert poi.category == POICategory.RESTAURANT
        assert poi.id is not None
        assert poi.created_at is not None
        assert poi.updated_at is not None
        assert poi.is_active is True
    
    def test_create_poi_with_all_fields(self):
        """Test creating a POI with all optional fields"""
        poi = POI.create(
            name="Test Museum",
            category=POICategory.MUSEUM,
            address=Address(
                street="456 Museum Ave",
                city="New York",
                state="NY",
                postal_code="10002",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7580, longitude=-73.9855),
            description="A great museum",
            phone="+1-555-0123",
            website="https://example.com",
            email="info@example.com",
            opening_hours=OpeningHours(
                weekly_schedule={
                    DayOfWeek.MONDAY: [(datetime.strptime("09:00", "%H:%M").time(), datetime.strptime("17:00", "%H:%M").time())],
                }
            ),
            rating=Rating(value=4.5, count=100),
            price_level=2,
            accessibility=AccessibilityInfo(
                wheelchair_accessible=True,
                wheelchair_accessible_entrance=True,
                wheelchair_accessible_parking=True,
                wheelchair_accessible_restroom=True,
            ),
            tags=["art", "history", "culture"],
        )
        
        assert poi.name == "Test Museum"
        assert poi.category == POICategory.MUSEUM
        assert poi.description == "A great museum"
        assert poi.phone == "+1-555-0123"
        assert poi.website == "https://example.com"
        assert poi.email == "info@example.com"
        assert poi.opening_hours is not None
        assert poi.rating is not None
        assert poi.rating.value == 4.5
        assert poi.price_level == 2
        assert poi.accessibility is not None
        assert poi.accessibility.wheelchair_accessible is True
        assert "art" in poi.tags
    
    def test_update_poi(self):
        """Test updating POI fields"""
        poi = POI.create(
            name="Original Name",
            category=POICategory.CAFE,
            address=Address(
                street="789 Cafe St",
                city="New York",
                state="NY",
                postal_code="10003",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7505, longitude=-73.9934),
        )
        
        original_updated_at = poi.updated_at
        
        # Update fields
        poi.update(
            name="Updated Name",
            description="Updated description",
            phone="+1-555-9999",
        )
        
        assert poi.name == "Updated Name"
        assert poi.description == "Updated description"
        assert poi.phone == "+1-555-9999"
        assert poi.updated_at > original_updated_at
    
    def test_deactivate_poi(self):
        """Test deactivating a POI"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.PARK,
            address=Address(
                street="100 Park Ave",
                city="New York",
                state="NY",
                postal_code="10004",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7829, longitude=-73.9654),
        )
        
        assert poi.is_active is True
        
        poi.deactivate()
        
        assert poi.is_active is False
        assert poi.updated_at is not None
    
    def test_activate_poi(self):
        """Test activating a POI"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.PARK,
            address=Address(
                street="100 Park Ave",
                city="New York",
                state="NY",
                postal_code="10004",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7829, longitude=-73.9654),
        )
        
        poi.deactivate()
        assert poi.is_active is False
        
        poi.activate()
        
        assert poi.is_active is True
    
    def test_add_remove_tags(self):
        """Test adding and removing tags"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.ATTRACTION,
            address=Address(
                street="200 Attraction Blvd",
                city="New York",
                state="NY",
                postal_code="10005",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7589, longitude=-73.9851),
            tags=["initial"],
        )
        
        assert "initial" in poi.tags
        
        poi.add_tag("new_tag")
        assert "new_tag" in poi.tags
        
        # Adding duplicate should not create duplicate
        poi.add_tag("new_tag")
        assert poi.tags.count("new_tag") == 1
        
        poi.remove_tag("initial")
        assert "initial" not in poi.tags
        
        # Removing non-existent tag should not error
        poi.remove_tag("non_existent")
    
    def test_update_rating(self):
        """Test updating rating"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.RESTAURANT,
            address=Address(
                street="300 Restaurant Row",
                city="New York",
                state="NY",
                postal_code="10006",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7074, longitude=-74.0113),
        )
        
        assert poi.rating is None
        
        poi.update_rating(Rating(value=4.0, count=50))
        
        assert poi.rating is not None
        assert poi.rating.value == 4.0
        assert poi.rating.count == 50
    
    def test_update_opening_hours(self):
        """Test updating opening hours"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.MUSEUM,
            address=Address(
                street="400 Museum Mile",
                city="New York",
                state="NY",
                postal_code="10007",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7794, longitude=-73.9632),
        )
        
        assert poi.opening_hours is None
        
        hours = OpeningHours(
            weekly_schedule={
                DayOfWeek.MONDAY: [(datetime.strptime("10:00", "%H:%M").time(), datetime.strptime("18:00", "%H:%M").time())],
            }
        )
        poi.update_opening_hours(hours)
        
        assert poi.opening_hours is not None
        assert DayOfWeek.MONDAY in poi.opening_hours.weekly_schedule
    
    def test_poi_equality(self):
        """Test POI equality based on ID"""
        poi1 = POI.create(
            name="Test POI",
            category=POICategory.CAFE,
            address=Address(
                street="500 Coffee St",
                city="New York",
                state="NY",
                postal_code="10008",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7282, longitude=-73.9942),
        )
        
        poi2 = POI.create(
            name="Test POI",
            category=POICategory.CAFE,
            address=Address(
                street="500 Coffee St",
                city="New York",
                state="NY",
                postal_code="10008",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7282, longitude=-73.9942),
        )
        
        # Different instances with different IDs should not be equal
        assert poi1 != poi2
        
        # Same instance should be equal to itself
        assert poi1 == poi1
        
        # Create a copy with same ID
        poi3 = POI(
            id=poi1.id,
            name="Different Name",
            category=POICategory.RESTAURANT,
            address=Address(
                street="Different St",
                city="Boston",
                state="MA",
                postal_code="02101",
                country="USA"
            ),
            coordinates=Coordinates(latitude=42.3601, longitude=-71.0589),
            created_at=poi1.created_at,
            updated_at=poi1.updated_at,
        )
        
        # Same ID should be equal
        assert poi1 == poi3
    
    def test_poi_str_representation(self):
        """Test POI string representation"""
        poi = POI.create(
            name="Test POI",
            category=POICategory.HOTEL,
            address=Address(
                street="600 Hotel Ave",
                city="New York",
                state="NY",
                postal_code="10009",
                country="USA"
            ),
            coordinates=Coordinates(latitude=40.7505, longitude=-73.9934),
        )
        
        str_repr = str(poi)
        assert "Test POI" in str_repr
        assert "HOTEL" in str_repr
        assert str(poi.id) in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])