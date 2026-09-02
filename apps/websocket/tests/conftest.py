"""
Pytest configuration and fixtures for WebSocket service tests.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis
from fastapi import WebSocket


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock(spec=redis.Redis)
    mock.ping = AsyncMock(return_value=True)
    mock.set = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=True)
    mock.sadd = AsyncMock(return_value=1)
    mock.srem = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.lpush = AsyncMock(return_value=1)
    mock.ltrim = AsyncMock(return_value=True)
    mock.lrange = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    mock = AsyncMock(spec=WebSocket)
    mock.accept = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_json = AsyncMock()
    mock.close = AsyncMock()
    mock.client = MagicMock()
    mock.client.host = "127.0.0.1"
    mock.client.port = 12345
    return mock


@pytest.fixture
def mock_websocket_disconnect():
    """Create a mock WebSocket that raises WebSocketDisconnect on receive."""
    from fastapi import WebSocketDisconnect
    mock = AsyncMock(spec=WebSocket)
    mock.accept = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_json = AsyncMock(side_effect=WebSocketDisconnect(code=1000))
    mock.close = AsyncMock()
    return mock


@pytest.fixture
async def connection_manager(mock_redis):
    """Create a ConnectionManager instance with mock Redis."""
    from ws_service.connection_manager import ConnectionManager
    manager = ConnectionManager(mock_redis)
    yield manager
    await manager.disconnect_all()


@pytest.fixture
async def chat_handler(connection_manager, mock_redis):
    """Create a ChatHandler instance."""
    from ws_service.handlers.chat_handler import ChatHandler
    return ChatHandler(connection_manager, mock_redis)


@pytest.fixture
async def location_handler(connection_manager, mock_redis):
    """Create a LocationHandler instance."""
    from ws_service.handlers.location_handler import LocationHandler
    return LocationHandler(connection_manager, mock_redis)


@pytest.fixture
async def transit_handler(connection_manager, mock_redis):
    """Create a TransitHandler instance."""
    from ws_service.handlers.transit_handler import TransitHandler
    return TransitHandler(connection_manager, mock_redis)


@pytest.fixture
async def notification_handler(connection_manager, mock_redis):
    """Create a NotificationHandler instance."""
    from ws_service.handlers.notification_handler import NotificationHandler
    return NotificationHandler(connection_manager, mock_redis)