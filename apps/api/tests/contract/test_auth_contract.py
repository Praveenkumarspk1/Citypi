"""
Auth API Contract Tests using Schemathesis
"""
import schemathesis
import pytest
from hypothesis import given, settings
from hypothesis.strategies import text, emails, uuids, integers, floats, booleans, lists, dictionaries, none


# Load the OpenAPI schema from the running API
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")


# Auth-specific test cases
@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/auth/login"]["POST"].as_strategy())
def test_auth_login_contract(case, data):
    """Test login endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/auth/register"]["POST"].as_strategy())
def test_auth_register_contract(case, data):
    """Test register endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/auth/refresh"]["POST"].as_strategy())
def test_auth_refresh_contract(case, data):
    """Test token refresh endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/auth/forgot-password"]["POST"].as_strategy())
def test_auth_forgot_password_contract(case, data):
    """Test forgot password endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/auth/reset-password"]["POST"].as_strategy())
def test_auth_reset_password_contract(case, data):
    """Test reset password endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/auth/verify-email"]["POST"].as_strategy())
def test_auth_verify_email_contract(case, data):
    """Test verify email endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=5, deadline=None)
@given(data=schema["/api/v1/auth/resend-verification"]["POST"].as_strategy())
def test_auth_resend_verification_contract(case, data):
    """Test resend verification endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/auth/me"]["GET"].as_strategy())
def test_auth_me_contract(case, data):
    """Test get current user endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


@schema.parametrize()
@settings(max_examples=10, deadline=None)
@given(data=schema["/api/v1/auth/logout"]["POST"].as_strategy())
def test_auth_logout_contract(case, data):
    """Test logout endpoint contract compliance"""
    response = case.call_wsgi(data)
    case.validate_response(response)


# Custom strategies for auth payloads
auth_login_strategy = schema["/api/v1/auth/login"]["POST"].as_strategy()

auth_register_strategy = schema["/api/v1/auth/register"]["POST"].as_strategy()


# Negative test cases
def test_auth_login_invalid_credentials():
    """Test login with invalid credentials returns 401"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            })
            assert response.status_code == 401
    
    asyncio.run(_test())


def test_auth_register_duplicate_email():
    """Test register with duplicate email returns 409"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First register
            await client.post("/api/v1/auth/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123"
            })
            # Second register with same email
            response = await client.post("/api/v1/auth/register", json={
                "email": "test@example.com",
                "username": "testuser2",
                "password": "password123"
            })
            assert response.status_code == 409
    
    asyncio.run(_test())


def test_auth_me_requires_auth():
    """Test /me endpoint requires authentication"""
    from httpx import AsyncClient, ASGITransport
    from ai_smart_city_concierge.main import app
    
    import asyncio
    
    async def _test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 401
    
    asyncio.run(_test())