"""
Unit tests for ItineraryAggregate
"""
import pytest
from datetime import datetime, date, time, timezone, timedelta
from uuid import uuid4

from ai_smart_city_concierge.domain.aggregates.itinerary_aggregate import ItineraryAggregate
from ai_smart_city_concierge.domain.value_objects.time_range import TimeRange
from ai_smart_city_concierge.domain.value_objects.money import Money
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode
from ai_smart_city_concierge.domain.events.itinerary_events import (
    ItineraryCreated,
    ItineraryDayAdded,
    ItineraryItemAdded,
    ItineraryUpdated,
    ItineraryShared,
    ItineraryPublished,
)


class TestItineraryAggregate:
    """Test cases for ItineraryAggregate"""

    def test_create_itinerary(self):
        """Test creating a new itinerary"""
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

        assert itinerary.user_id == user_id
        assert itinerary.title == "Paris Trip"
        assert itinerary.description == "3 days in Paris"
        assert itinerary.start_date == start_date
        assert itinerary.end_date == end_date
        assert itinerary.timezone == "Europe/Paris"
        assert itinerary.status == "draft"
        assert len(itinerary.days) == 0
        assert itinerary.created_at is not None
        assert itinerary.updated_at is not None

    def test_add_day(self):
        """Test adding a day to itinerary"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(
            date=start_date,
            title="Day 1 - Arrival",
            notes="Arrive in Paris",
        )

        assert len(itinerary.days) == 1
        day = itinerary.days[0]
        assert day.id == day_id
        assert day.date == start_date
        assert day.title == "Day 1 - Arrival"
        assert day.notes == "Arrive in Paris"
        assert len(day.items) == 0

    def test_add_multiple_days(self):
        """Test adding multiple days"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=3)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        itinerary.add_day(date=start_date, title="Day 1")
        itinerary.add_day(date=start_date + timedelta(days=1), title="Day 2")
        itinerary.add_day(date=start_date + timedelta(days=2), title="Day 3")

        assert len(itinerary.days) == 3
        assert itinerary.days[0].title == "Day 1"
        assert itinerary.days[1].title == "Day 2"
        assert itinerary.days[2].title == "Day 3"

    def test_add_item_to_day(self):
        """Test adding an item to a day"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1")

        item_id = itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Eiffel Tower",
            description="Visit the Eiffel Tower",
            start_time=time(10, 0),
            end_time=time(12, 0),
            duration_minutes=120,
            address="Champ de Mars, 5 Avenue Anatole France, 75007 Paris",
            estimated_cost=Money(amount=25.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        day = itinerary.get_day(day_id)
        assert day is not None
        assert len(day.items) == 1
        item = day.items[0]
        assert item.id == item_id
        assert item.type == "poi"
        assert item.title == "Eiffel Tower"
        assert item.start_time == time(10, 0)
        assert item.end_time == time(12, 0)
        assert item.duration_minutes == 120
        assert item.estimated_cost.amount == 25.0
        assert item.transport_mode == TransportMode.WALKING

    def test_add_multiple_items_to_day(self):
        """Test adding multiple items to a day"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1")

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

        itinerary.add_item(
            day_id=day_id,
            type="restaurant",
            title="Lunch at Le Jules Verne",
            start_time=time(12, 30),
            end_time=time(14, 0),
            duration_minutes=90,
            address="Eiffel Tower",
            estimated_cost=Money(amount=120.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        day = itinerary.get_day(day_id)
        assert len(day.items) == 2
        assert day.items[0].title == "Eiffel Tower"
        assert day.items[1].title == "Lunch at Le Jules Verne"

    def test_remove_item(self):
        """Test removing an item from a day"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1")
        item_id = itinerary.add_item(
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

        assert len(itinerary.get_day(day_id).items) == 1

        itinerary.remove_item(day_id=day_id, item_id=item_id)

        assert len(itinerary.get_day(day_id).items) == 0

    def test_update_itinerary(self):
        """Test updating itinerary details"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            description="Original description",
            start_date=start_date,
            end_date=end_date,
        )

        new_start = start_date + timedelta(days=1)
        new_end = end_date + timedelta(days=1)

        itinerary.update(
            title="Updated Paris Trip",
            description="Updated description",
            start_date=new_start,
            end_date=new_end,
        )

        assert itinerary.title == "Updated Paris Trip"
        assert itinerary.description == "Updated description"
        assert itinerary.start_date == new_start
        assert itinerary.end_date == new_end
        assert itinerary.updated_at is not None

    def test_share_itinerary(self):
        """Test sharing an itinerary"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        share_token = itinerary.share()

        assert itinerary.is_shared is True
        assert itinerary.share_token == share_token
        assert len(share_token) > 0

    def test_unshare_itinerary(self):
        """Test unsharing an itinerary"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        itinerary.share()
        assert itinerary.is_shared is True

        itinerary.unshare()
        assert itinerary.is_shared is False
        assert itinerary.share_token is None

    def test_publish_itinerary(self):
        """Test publishing an itinerary"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        itinerary.publish()

        assert itinerary.status == "published"
        assert itinerary.published_at is not None

    def test_get_total_duration(self):
        """Test getting total duration of itinerary"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1")

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

        itinerary.add_item(
            day_id=day_id,
            type="restaurant",
            title="Lunch",
            start_time=time(12, 30),
            end_time=time(14, 0),
            duration_minutes=90,
            address="Restaurant",
            estimated_cost=Money(amount=50.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        total_duration = itinerary.get_total_duration_minutes()
        assert total_duration == 210  # 120 + 90

    def test_get_total_estimated_cost(self):
        """Test getting total estimated cost"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=1)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        day_id = itinerary.add_day(date=start_date, title="Day 1")

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

        itinerary.add_item(
            day_id=day_id,
            type="restaurant",
            title="Lunch",
            start_time=time(12, 30),
            end_time=time(14, 0),
            duration_minutes=90,
            address="Restaurant",
            estimated_cost=Money(amount=50.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        total_cost = itinerary.get_total_estimated_cost()
        assert total_cost.amount == 75.0
        assert total_cost.currency == "EUR"

    def test_itinerary_events_emitted(self):
        """Test that domain events are emitted"""
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Paris Trip",
            start_date=start_date,
            end_date=end_date,
        )

        # Check ItineraryCreated event
        events = itinerary.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ItineraryCreated)
        assert events[0].user_id == user_id
        assert events[0].title == "Paris Trip"

        # Clear events and add day
        itinerary.clear_events()
        day_id = itinerary.add_day(date=start_date, title="Day 1")

        events = itinerary.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ItineraryDayAdded)
        assert events[0].day_id == day_id
        assert events[0].title == "Day 1"

        # Clear events and add item
        itinerary.clear_events()
        item_id = itinerary.add_item(
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

        events = itinerary.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ItineraryItemAdded)
        assert events[0].item_id == item_id
        assert events[0].title == "Eiffel Tower"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])