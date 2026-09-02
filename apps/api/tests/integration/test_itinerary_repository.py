"""
Integration tests for ItineraryRepository
"""
import pytest
from datetime import date, time, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.repositories.itinerary_repository import ItineraryRepository
from ai_smart_city_concierge.domain.aggregates.itinerary_aggregate import ItineraryAggregate
from ai_smart_city_concierge.domain.value_objects.money import Money
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode


@pytest.mark.asyncio
class TestItineraryRepository:
    """Integration tests for ItineraryRepository"""

    async def test_save_and_get_itinerary(self, db_session: AsyncSession):
        """Test saving and retrieving an itinerary"""
        repo = ItineraryRepository(db_session)
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

        await repo.save(itinerary)
        await db_session.commit()

        # Retrieve the itinerary
        retrieved = await repo.get_by_id(itinerary.id)
        assert retrieved is not None
        assert retrieved.id == itinerary.id
        assert retrieved.user_id == user_id
        assert retrieved.title == "Paris Trip"
        assert retrieved.description == "3 days in Paris"
        assert retrieved.start_date == start_date
        assert retrieved.end_date == end_date
        assert retrieved.timezone == "Europe/Paris"
        assert retrieved.status == "draft"
        assert len(retrieved.days) == 1
        assert retrieved.days[0].title == "Day 1 - Arrival"
        assert len(retrieved.days[0].items) == 1
        assert retrieved.days[0].items[0].title == "Eiffel Tower"

    async def test_get_itineraries_by_user(self, db_session: AsyncSession):
        """Test getting itineraries by user"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        other_user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        # Create itineraries for user
        itin1 = ItineraryAggregate.create(user_id=user_id, title="Trip 1", start_date=start_date, end_date=end_date)
        itin2 = ItineraryAggregate.create(user_id=user_id, title="Trip 2", start_date=start_date, end_date=end_date)
        itin3 = ItineraryAggregate.create(user_id=other_user_id, title="Trip 3", start_date=start_date, end_date=end_date)

        await repo.save(itin1)
        await repo.save(itin2)
        await repo.save(itin3)
        await db_session.commit()

        # Get itineraries for user
        itineraries = await repo.get_by_user_id(user_id)
        assert len(itineraries) == 2
        assert all(i.user_id == user_id for i in itineraries)

    async def test_get_itineraries_by_status(self, db_session: AsyncSession):
        """Test getting itineraries by status"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        draft_itin = ItineraryAggregate.create(user_id=user_id, title="Draft Trip", start_date=start_date, end_date=end_date)
        published_itin = ItineraryAggregate.create(user_id=user_id, title="Published Trip", start_date=start_date, end_date=end_date)
        published_itin.publish()

        await repo.save(draft_itin)
        await repo.save(published_itin)
        await db_session.commit()

        drafts = await repo.get_by_status("draft")
        published = await repo.get_by_status("published")

        assert len(drafts) == 1
        assert drafts[0].id == draft_itin.id
        assert len(published) == 1
        assert published[0].id == published_itin.id

    async def test_update_itinerary(self, db_session: AsyncSession):
        """Test updating an itinerary"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Original Title",
            start_date=start_date,
            end_date=end_date,
        )
        await repo.save(itinerary)
        await db_session.commit()

        # Update itinerary
        new_start = start_date + timedelta(days=1)
        new_end = end_date + timedelta(days=1)
        itinerary.update(
            title="Updated Title",
            description="Updated description",
            start_date=new_start,
            end_date=new_end,
        )
        day_id = itinerary.add_day(date=new_start, title="New Day")
        itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Louvre Museum",
            start_time=time(10, 0),
            end_time=time(13, 0),
            duration_minutes=180,
            address="Louvre Museum",
            estimated_cost=Money(amount=17.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )

        await repo.save(itinerary)
        await db_session.commit()

        # Verify update
        retrieved = await repo.get_by_id(itinerary.id)
        assert retrieved.title == "Updated Title"
        assert retrieved.description == "Updated description"
        assert retrieved.start_date == new_start
        assert retrieved.end_date == new_end
        assert len(retrieved.days) == 1
        assert retrieved.days[0].title == "New Day"
        assert len(retrieved.days[0].items) == 1
        assert retrieved.days[0].items[0].title == "Louvre Museum"

    async def test_delete_itinerary(self, db_session: AsyncSession):
        """Test deleting an itinerary"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="To Delete",
            start_date=start_date,
            end_date=end_date,
        )
        await repo.save(itinerary)
        await db_session.commit()

        # Delete itinerary
        await repo.delete(itinerary.id)
        await db_session.commit()

        # Verify deletion
        retrieved = await repo.get_by_id(itinerary.id)
        assert retrieved is None

    async def test_get_shared_itinerary(self, db_session: AsyncSession):
        """Test getting a shared itinerary by share token"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Shared Trip",
            start_date=start_date,
            end_date=end_date,
        )
        share_token = itinerary.share()
        await repo.save(itinerary)
        await db_session.commit()

        # Retrieve by share token
        retrieved = await repo.get_by_share_token(share_token)
        assert retrieved is not None
        assert retrieved.id == itinerary.id
        assert retrieved.title == "Shared Trip"
        assert retrieved.is_shared is True

    async def test_get_nonexistent_share_token(self, db_session: AsyncSession):
        """Test getting itinerary with nonexistent share token"""
        repo = ItineraryRepository(db_session)

        retrieved = await repo.get_by_share_token("nonexistent-token")
        assert retrieved is None

    async def test_itinerary_persistence_with_events(self, db_session: AsyncSession):
        """Test that domain events are persisted with itinerary"""
        repo = ItineraryRepository(db_session)
        user_id = uuid4()
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=2)

        itinerary = ItineraryAggregate.create(
            user_id=user_id,
            title="Event Test",
            start_date=start_date,
            end_date=end_date,
        )
        day_id = itinerary.add_day(date=start_date, title="Day 1")
        itinerary.add_item(
            day_id=day_id,
            type="poi",
            title="Test POI",
            start_time=time(10, 0),
            end_time=time(12, 0),
            duration_minutes=120,
            address="Test Address",
            estimated_cost=Money(amount=10.0, currency="EUR"),
            transport_mode=TransportMode.WALKING,
        )
        itinerary.share()

        events = itinerary.get_uncommitted_events()
        assert len(events) == 4  # Created, DayAdded, ItemAdded, Shared

        await repo.save(itinerary)
        await db_session.commit()

        # Events should be cleared after save
        assert len(itinerary.get_uncommitted_events()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])