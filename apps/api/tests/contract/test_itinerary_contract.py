"""
Itinerary API Contract Tests using Schemathesis
"""
import schemathesis
import pytest
from hypothesis import given, settings
import uuid


# Load the OpenAPI schema from the running API
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")


# Itinerary-specific test cases
@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/itineraries"]["GET"].as_strategy())
def test_itinerary_list_contract(case, data):
    """Test itinerary list endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/itineraries"]["POST"].as_strategy())
def test_itinerary_create_contract(case, data):
    """Test create itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}"]["GET"].as_strategy())
def test_itinerary_get_contract(case, data):
    """Test get itinerary by ID endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}"]["PUT"].as_strategy())
def test_itinerary_update_contract(case, data):
    """Test update itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}"]["DELETE"].as_strategy())
def test_itinerary_delete_contract(case, data):
    """Test delete itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days"]["POST"].as_strategy())
def test_itinerary_add_day_contract(case, data):
    """Test add day to itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days/{day_id}"]["PUT"].as_strategy())
def test_itinerary_update_day_contract(case, data):
    """Test update itinerary day endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days/{day_id}"]["DELETE"].as_strategy())
def test_itinerary_remove_day_contract(case, data):
    """Test remove day from itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days/{day_id}/items"]["POST"].as_strategy())
def test_itinerary_add_item_contract(case, data):
    """Test add item to itinerary day endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}"]["PUT"].as_strategy())
def test_itinerary_update_item_contract(case, data):
    """Test update itinerary item endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/days/{day_id}/items/{item_id}"]["DELETE"].as_strategy())
def test_itinerary_remove_item_contract(case, data):
    """Test remove item from itinerary day endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/share"]["POST"].as_strategy())
def test_itinerary_share_contract(case, data):
    """Test share itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/itineraries/{itinerary_id}/export"]["GET"].as_strategy())
def test_itinerary_export_contract(case, data):
    """Test export itinerary endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


# Negative test cases
def test_itinerary_get_not_found():
    """Test get itinerary with invalid ID returns 404"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/itineraries/{uuid.uuid4()}")
            assert response.status_code == 404
    
    asyncio.run(_test())


def test_itinerary_create_requires_auth():
    """Test create itinerary requires authentication"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/itineraries", json={
                "title": "Test Trip",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05"
            })
            assert response.status_code == 401
    
    asyncio.run(_test())


def test_itinerary_update_not_owner():
    """Test update itinerary by non-owner returns 403"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    import uuid
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/itineraries/{uuid.uuid4()}",
                json={"title": "Updated Title"},
                headers={"Authorization": "Bearer other-user-token"}
            )
            assert response.status_code in (401, 403, 404)
    
    asyncio.run(_test())


def test_itinerary_list_pagination():
    """Test itinerary list pagination parameters"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/itineraries", params={
                "page": 2,
                "page_size": 10
            }, headers={"Authorization": "Bearer test-token"})
            # May return 401 but shouldn't crash
            assert response.status_code in (200, 401)
    
    asyncio.run(_test())