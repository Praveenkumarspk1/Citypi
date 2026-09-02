"""
End-to-End API Tests
Tests full request flows through the API.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.anyio
class TestAuthFlow:
    """Test authentication flow end-to-end."""

    async def test_register_and_login(self, client: AsyncClient):
        # Register
        register_data = {
            "email": "e2e_test@example.com",
            "password": "SecurePass123!",
            "display_name": "E2E Test User",
        }
        response = await client.post("/api/v1/users/register", json=register_data)
        assert response.status_code == 201

        # Login
        login_data = {
            "email": "e2e_test@example.com",
            "password": "SecurePass123!",
        }
        response = await client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()


@pytest.mark.anyio
class TestConversationFlow:
    """Test conversation flow end-to-end."""

    async def test_create_conversation(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/conversations",
            json={"initial_message": "Hello, test message"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "conversation_id" in data


@pytest.mark.anyio
class TestPOISearch:
    """Test POI search end-to-end."""

    async def test_search_pois(self, client: AsyncClient):
        response = await client.get("/api/v1/pois?query=coffee&lat=37.7749&lng=-122.4194")
        assert response.status_code == 200

    async def test_nearby_pois(self, client: AsyncClient):
        response = await client.get("/api/v1/pois/nearby?lat=37.7749&lng=-122.4194&radius=1000")
        assert response.status_code == 200


@pytest.mark.anyio
class TestTransitRoutes:
    """Test transit route planning end-to-end."""

    async def test_plan_route(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/transit/routes",
            json={
                "origin_lat": 37.7749,
                "origin_lng": -122.4194,
                "destination_lat": 37.8199,
                "destination_lng": -122.4783,
            },
        )
        assert response.status_code == 200


@pytest.mark.anyio
class TestWeather:
    """Test weather endpoints end-to-end."""

    async def test_current_weather(self, client: AsyncClient):
        response = await client.get("/api/v1/weather/current?lat=37.7749&lng=-122.4194")
        assert response.status_code == 200

    async def test_weather_forecast(self, client: AsyncClient):
        response = await client.get("/api/v1/weather/forecast?lat=37.7749&lng=-122.4194&days=7")
        assert response.status_code == 200
