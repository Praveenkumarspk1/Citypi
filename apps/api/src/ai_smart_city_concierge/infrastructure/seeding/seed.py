"""
Database Seeding Script
Populates the database with sample data for development.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from passlib.hash import bcrypt

from ai_smart_city_concierge.domain.entities.conversation import ConversationStatus
from ai_smart_city_concierge.domain.entities.itinerary import ItineraryStatus
from ai_smart_city_concierge.domain.entities.poi import POICategory, POISource
from ai_smart_city_concierge.domain.entities.user import UserRole, UserStatus
from ai_smart_city_concierge.infrastructure.config.database import get_async_session, get_engine
from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.models import (
    Base,
    ConversationModel,
    ItineraryDayModel,
    ItineraryItemModel,
    ItineraryModel,
    MessageModel,
    POIModel,
    TransitAgencyModel,
    TransitStopModel,
    UserModel,
    WeatherForecastModel,
)

logger = logging.getLogger(__name__)


async def seed_users(session) -> list[UUID]:
    """Seed sample users."""
    user_ids = []
    users = [
        {
            "email": "admin@concierge.city",
            "display_name": "Admin User",
            "role": UserRole.ADMIN,
            "password_hash": bcrypt.hash("AdminPass123!"),
            "interests": ["technology", "food", "travel"],
        },
        {
            "email": "demo@concierge.city",
            "display_name": "Demo User",
            "role": UserRole.USER,
            "password_hash": bcrypt.hash("DemoPass123!"),
            "interests": ["museums", "parks", "restaurants"],
        },
        {
            "email": "test@concierge.city",
            "display_name": "Test User",
            "role": UserRole.USER,
            "password_hash": bcrypt.hash("TestPass123!"),
            "interests": ["hiking", "photography", "coffee"],
        },
    ]

    for user_data in users:
        user = UserModel(
            id=uuid4(),
            email=user_data["email"],
            display_name=user_data["display_name"],
            role=user_data["role"],
            status=UserStatus.ACTIVE,
            password_hash=user_data["password_hash"],
            email_verified=True,
            interests=user_data["interests"],
            budget_level="moderate",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(user)
        user_ids.append(user.id)

    await session.flush()
    logger.info("Seeded %d users", len(user_ids))
    return user_ids


async def seed_pois(session) -> list[UUID]:
    """Seed sample POIs."""
    poi_ids = []
    pois = [
        {
            "name": "Golden Gate Park",
            "category": POICategory.PARK,
            "latitude": 37.7694,
            "longitude": -122.4862,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Large urban park with gardens, museums, and trails.",
            "tags": ["park", "nature", "hiking", "family"],
            "rating": 4.8,
        },
        {
            "name": "San Francisco Museum of Modern Art",
            "category": POICategory.MUSEUM,
            "latitude": 37.7857,
            "longitude": -122.4011,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Contemporary art museum with rotating exhibitions.",
            "tags": ["art", "museum", "culture", "indoor"],
            "rating": 4.6,
        },
        {
            "name": "Ferry Building Marketplace",
            "category": POICategory.RESTAURANT,
            "latitude": 37.7956,
            "longitude": -122.3933,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Artisanal food market with local vendors and restaurants.",
            "tags": ["food", "market", "shopping", "local"],
            "rating": 4.7,
        },
        {
            "name": "Tartine Bakery",
            "category": POICategory.CAFE,
            "latitude": 37.7614,
            "longitude": -122.4241,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Famous bakery known for bread, pastries, and coffee.",
            "tags": ["coffee", "bakery", "breakfast", "local"],
            "rating": 4.5,
        },
        {
            "name": "California Academy of Sciences",
            "category": POICategory.MUSEUM,
            "latitude": 37.7699,
            "longitude": -122.4661,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Natural history museum with aquarium and planetarium.",
            "tags": ["science", "museum", "family", "indoor"],
            "rating": 4.7,
        },
        {
            "name": "Dolores Park",
            "category": POICategory.PARK,
            "latitude": 37.7596,
            "longitude": -122.4269,
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "description": "Popular park with city views, picnic areas, and events.",
            "tags": ["park", "outdoor", "views", "family"],
            "rating": 4.6,
        },
    ]

    for poi_data in pois:
        poi = POIModel(
            id=uuid4(),
            source=POISource.MANUAL,
            name=poi_data["name"],
            category=poi_data["category"],
            latitude=poi_data["latitude"],
            longitude=poi_data["longitude"],
            city=poi_data["city"],
            state=poi_data["state"],
            country=poi_data["country"],
            description=poi_data["description"],
            tags=poi_data["tags"],
            wheelchair_accessible=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(poi)
        poi_ids.append(poi.id)

    await session.flush()
    logger(f"Seeded {len(poi_ids)} POIs")
    return poi_ids


async def seed_conversations(session, user_ids: list[UUID]):
    """Seed sample conversations."""
    conv_count = 0
    for user_id in user_ids[:2]:
        conv = ConversationModel(
            id=uuid4(),
            user_id=user_id,
            title="Exploring San Francisco",
            status=ConversationStatus.ACTIVE,
            message_count=2,
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow(),
        )
        session.add(conv)
        await session.flush()

        # Add messages
        messages = [
            MessageModel(
                id=uuid4(),
                conversation_id=conv.id,
                role="user",
                content="What are some good places to visit in San Francisco?",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            MessageModel(
                id=uuid4(),
                conversation_id=conv.id,
                role="assistant",
                content="San Francisco has many great attractions! I recommend Golden Gate Park, the Ferry Building, and the California Academy of Sciences.",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
        ]
        session.add_all(messages)
        conv_count += 1

    await session.flush()
    logger(f"Seeded {conv_count} conversations with messages")


async def seed_itineraries(session, user_ids: list[UUID], poi_ids: list[UUID]):
    """Seed sample itineraries."""
    if not user_ids or not poi_ids:
        return

    itinerary = ItineraryModel(
        id=uuid4(),
        user_id=user_ids[0],
        title="SF Weekend Adventure",
        description="A 2-day itinerary exploring the best of San Francisco",
        status=ItineraryStatus.DRAFT,
        start_date=datetime.utcnow().date() + timedelta(days=7),
        end_date=datetime.utcnow().date() + timedelta(days=9),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(itinerary)
    await session.flush()

    # Add days
    for day_num in range(1, 3):
        day = ItineraryDayModel(
            id=uuid4(),
            itinerary_id=itinerary.id,
            day_number=day_num,
            title=f"Day {day_num}",
        )
        session.add(day)
        await session.flush()

        # Add items
        for i, poi_id in enumerate(poi_ids[:3]):
            item = ItineraryItemModel(
                id=uuid4(),
                day_id=day.id,
                poi_id=poi_id,
                order_index=i,
                start_time=f"{10 + i * 2}:00",
                end_time=f"{11 + i * 2}:00",
                duration_minutes=60,
            )
            session.add(item)

    await session.flush()
    logger("Seeded 1 itinerary with 2 days and items")


async def seed_transit_agencies(session):
    """Seed sample transit agencies."""
    agency = TransitAgencyModel(
        id=uuid4(),
        external_id="sfmta",
        name="San Francisco Municipal Transportation Agency",
        url="https://www.sfmta.com",
        timezone="America/Los_Angeles",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(agency)
    await session.flush()

    # Add sample stops
    stops = [
        {"name": "Powell St Station", "lat": 37.7844, "lng": -122.4079},
        {"name": "Civic Center Station", "lat": 37.7796, "lng": -122.4138},
        {"name": "Embarcadero Station", "lat": 37.7930, "lng": -122.3964},
    ]
    for stop_data in stops:
        stop = TransitStopModel(
            id=uuid4(),
            agency_id=agency.id,
            external_id=f"stop_{stop_data['name'].lower().replace(' ', '_')}",
            name=stop_data["name"],
            latitude=stop_data["lat"],
            longitude=stop_data["lng"],
        )
        session.add(stop)

    await session.flush()
    logger("Seeded 1 transit agency with 3 stops")


async def seed_weather_data(session):
    """Seed sample weather forecasts."""
    forecasts = []
    base_date = datetime.utcnow()
    for day_offset in range(7):
        forecast = WeatherForecastModel(
            id=uuid4(),
            latitude=37.7749,
            longitude=-122.4194,
            forecast_time=base_date,
            valid_time=base_date + timedelta(days=day_offset),
            temperature=15.0 + day_offset * 0.5,
            humidity=65,
            wind_speed=12.0,
            weather_code=1,
            weather_description="Partly cloudy",
            source="open-meteo",
        )
        forecasts.append(forecast)

    session.add_all(forecasts)
    await session.flush()
    logger(f"Seeded {len(forecasts)} weather forecasts")


async def main():
    """Run all seed functions."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_async_session() as session:
        user_ids = await seed_users(session)
        poi_ids = await seed_pois(session)
        await seed_conversations(session, user_ids)
        await seed_itineraries(session, user_ids, poi_ids)
        await seed_transit_agencies(session)
        await seed_weather_data(session)
        await session.commit()

    logger("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
