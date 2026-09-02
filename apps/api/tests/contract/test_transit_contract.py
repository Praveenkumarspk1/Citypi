"""
Transit API Contract Tests using Schemathesis
"""
import schemathesis
import pytest
from hypothesis import given, settings
import uuid


# Load the OpenAPI schema from the running API
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")


# Transit-specific test cases
@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/transit/routes"]["GET"].as_strategy())
def test_transit_routes_list_contract(case, data):
    """Test transit routes list endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/transit/routes/{route_id}"]["GET"].as_strategy())
def test_transit_route_get_contract(case, data):
    """Test get transit route by ID endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/transit/stops"]["GET"].as_strategy())
def test_transit_stops_list_contract(case, data):
    """Test transit stops list endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/transit/stops/{stop_id}"]["GET"].as_strategy())
def test_transit_stop_get_contract(case, data):
    """Test get transit stop by ID endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/transit/plan"]["POST"].as_strategy())
def test_transit_plan_contract(case, data):
    """Test transit route planning endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/transit/favorites"]["GET"].as_strategy())
def test_transit_favorites_list_contract(case, data):
    """Test transit favorites list endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/transit/favorites"]["POST"].as_strategy())
def test_transit_favorite_create_contract(case, data):
    """Test create transit favorite endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/transit/favorites/{favorite_id}"]["DELETE"].as_strategy())
def test_transit_favorite_delete_contract(case, data):
    """Test delete transit favorite endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/transit/agencies"]["GET"].as_strategy())
def test_transit_agencies_list_contract(case, data):
    """Test transit agencies list endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


# Negative test cases
def test_transit_plan_invalid_params():
    """Test transit plan with invalid parameters"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/transit/plan", json={
                "origin": "",  # Invalid - empty
                "destination": "Times Square"
            })
            assert response.status_code == 422
    
    asyncio.run(_test())


def test_transit_route_not_found():
    """Test get transit route with invalid ID returns 404"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/transit/routes/{uuid.uuid4()}")
            assert response.status_code == 404
    
    asyncio.run(_test())


def test_transit_favorites_require_auth():
    """Test transit favorites require authentication"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/transit/favorites")
            assert response.status_code == 401
    
    asyncio.run(_test())


def test_transit_plan_missing_origin():
    """Test transit plan without origin returns 422"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/transit/plan", json={
                "destination": "Times Square"
            })
            assert response.status_code == 422
    
    asyncio.run(_test())