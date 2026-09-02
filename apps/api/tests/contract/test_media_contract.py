"""
Contract Tests - Media Service
Validates the media service API contract.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestMediaContract:
    """Test media service API contract."""

    async def test_transcribe_endpoint_exists(self, client: AsyncClient):
        """Verify transcribe endpoint exists."""
        response = await client.post("/api/v1/media/transcribe")
        assert response.status_code in [200, 401, 422]

    async def test_analyze_image_endpoint_exists(self, client: AsyncClient):
        """Verify analyze image endpoint exists."""
        response = await client.post("/api/v1/media/analyze-image")
        assert response.status_code in [200, 401, 422]

    async def test_upload_endpoint_exists(self, client: AsyncClient):
        """Verify upload endpoint exists."""
        response = await client.post("/api/v1/media/upload")
        assert response.status_code in [200, 401, 422]

    async def test_media_response_schema(self, client: AsyncClient, auth_headers: dict):
        """Verify media response follows schema."""
        response = await client.get("/api/v1/media", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
