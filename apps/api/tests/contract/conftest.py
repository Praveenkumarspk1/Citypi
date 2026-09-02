"""
Pytest configuration and fixtures for contract tests
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from ai_smart_city_concierge.main import app


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for API"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def openapi_url() -> str:
    """OpenAPI spec URL"""
    return "http://localhost:8000/openapi.json"


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    """Default auth headers for tests"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def override_env(monkeypatch):
    """Override environment for testing"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")