"""
Performance Tests
Benchmarks for critical API operations.
"""
import time

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestAPIPerformance:
    """Performance benchmarks for API endpoints."""

    async def test_health_check_latency(self, client: AsyncClient):
        """Health check should respond in under 100ms."""
        start = time.time()
        response = await client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1

    async def test_poi_search_latency(self, client: AsyncClient):
        """POI search should respond in under 500ms."""
        start = time.time()
        response = await client.get("/api/v1/pois/nearby?lat=37.7749&lng=-122.4194&radius=1000")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5

    async def test_concurrent_requests(self, client: AsyncClient):
        """API should handle concurrent requests."""
        import asyncio

        async def make_request():
            return await client.get("/health")

        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
