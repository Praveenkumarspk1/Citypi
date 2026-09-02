"""
Tests for WebSocket Connection Manager.
"""
import pytest
from fastapi import WebSocketDisconnect


class TestConnectionManagerConnect:
    """Tests for connection management."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, connection_manager, mock_websocket):
        """Test that connect accepts the WebSocket and returns connection_id."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123")

        mock_websocket.accept.assert_called_once()
        assert connection_id is not None
        assert isinstance(connection_id, str)
        assert len(connection_id) > 0

    @pytest.mark.asyncio
    async def test_connect_stores_connection_locally(self, connection_manager, mock_websocket):
        """Test that connection is stored in local dictionaries."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123", {"key": "value"})

        assert connection_id in connection_manager._connections
        assert connection_manager._connections[connection_id] == mock_websocket
        assert connection_manager._connection_user[connection_id] == "user_123"
        assert connection_manager._connection_metadata[connection_id] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_connect_tracks_user_connections(self, connection_manager, mock_websocket):
        """Test that user_connections tracking works."""
        await connection_manager.connect(mock_websocket, "user_123")

        assert "user_123" in connection_manager._user_connections
        assert connection_id in connection_manager._user_connections["user_123"]

    @pytest.mark.asyncio
    async def test_connect_stores_in_redis(self, connection_manager, mock_redis, mock_websocket):
        """Test that connection info is stored in Redis."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123", {"handler": "chat"})

        mock_redis.set.assert_called_once()
        mock_redis.sadd.assert_called_once()
        mock_redis.expire.assert_called_once()

        call_args = mock_redis.set.call_args
        assert f"ws:connection:{connection_id}" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_connect_multiple_connections_same_user(self, connection_manager, mock_websocket):
        """Test multiple connections for the same user."""
        ws2 = mock_websocket
        cid1 = await connection_manager.connect(mock_websocket, "user_123")
        cid2 = await connection_manager.connect(ws2, "user_123")

        assert cid1 != cid2
        assert len(connection_manager._user_connections["user_123"]) == 2


class TestConnectionManagerDisconnect:
    """Tests for disconnection."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_local_tracking(self, connection_manager, mock_websocket):
        """Test that disconnect removes connection from local tracking."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123")
        await connection_manager.disconnect(connection_id)

        assert connection_id not in connection_manager._connections
        assert connection_id not in connection_manager._connection_user
        assert connection_id not in connection_manager._connection_metadata
        assert "user_123" not in connection_manager._user_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_redis(self, connection_manager, mock_redis, mock_websocket):
        """Test that disconnect removes connection from Redis."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123")
        await connection_manager.disconnect(connection_id)

        mock_redis.delete.assert_called()
        mock_redis.srem.assert_called()

    @pytest.mark.asyncio
    async def test_disconnect_closes_websocket(self, connection_manager, mock_websocket):
        """Test that disconnect closes the WebSocket."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123")
        await connection_manager.disconnect(connection_id)

        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection(self, connection_manager):
        """Test that disconnect handles nonexistent connection gracefully."""
        await connection_manager.disconnect("nonexistent_id")  # Should not raise

    @pytest.mark.asyncio
    async def test_disconnect_user_removes_all_connections(self, connection_manager, mock_websocket):
        """Test that disconnect_user removes all connections for a user."""
        cid1 = await connection_manager.connect(mock_websocket, "user_123")
        cid2 = await connection_manager.connect(mock_websocket, "user_123")

        await connection_manager.disconnect_user("user_123")

        assert "user_123" not in connection_manager._user_connections
        assert cid1 not in connection_manager._connections
        assert cid2 not in connection_manager._connections


class TestConnectionManagerSend:
    """Tests for sending messages."""

    @pytest.mark.asyncio
    async def test_send_to_connection_success(self, connection_manager, mock_websocket):
        """Test sending message to a specific connection."""
        connection_id = await connection_manager.connect(mock_websocket, "user_123")
        message = {"type": "test", "data": "hello"}

        result = await connection_manager.send_to_connection(connection_id, message)

        assert result is True
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_connection_not_found(self, connection_manager):
        """Test sending to nonexistent connection returns False."""
        result = await connection_manager.send_to_connection("nonexistent", {"type": "test"})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_connection_failure_disconnects(self, connection_manager, mock_websocket):
        """Test that send failure disconnects the connection."""
        mock_websocket.send_json.side_effect = Exception("Connection lost")
        connection_id = await connection_manager.connect(mock_websocket, "user_123")

        result = await connection_manager.send_to_connection(connection_id, {"type": "test"})

        assert result is False
        assert connection_id not in connection_manager._connections

    @pytest.mark.asyncio
    async def test_send_to_user_single_connection(self, connection_manager, mock_websocket):
        """Test sending to user with single connection."""
        await connection_manager.connect(mock_websocket, "user_123")
        message = {"type": "test"}

        sent = await connection_manager.send_to_user("user_123", message)

        assert sent == 1
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_multiple_connections(self, connection_manager, mock_websocket):
        """Test sending to user with multiple connections."""
        cid1 = await connection_manager.connect(mock_websocket, "user_123")
        cid2 = await connection_manager.connect(mock_websocket, "user_123")

        sent = await connection_manager.send_to_user("user_123", {"type": "test"})

        assert sent == 2
        assert mock_websocket.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_send_to_user_not_connected(self, connection_manager):
        """Test sending to user with no connections returns 0."""
        sent = await connection_manager.send_to_user("unknown_user", {"type": "test"})

        assert sent == 0


class TestConnectionManagerBroadcast:
    """Tests for broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcast_to_all_users(self, connection_manager, mock_websocket):
        """Test broadcasting to all connected users."""
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")

        sent = await connection_manager.broadcast({"type": "broadcast"})

        assert sent == 2
        assert mock_websocket.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_excludes_user(self, connection_manager, mock_websocket):
        """Test broadcast with exclude_user parameter."""
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")

        sent = await connection_manager.broadcast({"type": "broadcast"}, exclude_user="user_1")

        assert sent == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_specific_users(self, connection_manager, mock_websocket):
        """Test broadcast_to_users method."""
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")
        await connection_manager.connect(mock_websocket, "user_3")

        sent = await connection_manager.broadcast_to_users(["user_1", "user_3"], {"type": "targeted"})

        assert sent == 2


class TestConnectionManagerHandlers:
    """Tests for message handler registration and routing."""

    @pytest.mark.asyncio
    async def test_register_handler(self, connection_manager):
        """Test registering a message handler."""
        async def dummy_handler(user_id, message):
            pass

        connection_manager.register_handler("test_type", dummy_handler)
        assert connection_manager._message_handlers["test_type"] == dummy_handler

    @pytest.mark.asyncio
    async def test_handle_message_routes_to_handler(self, connection_manager, mock_websocket):
        """Test that handle_message routes to the correct handler."""
        handler_called = []

        async def dummy_handler(user_id, message):
            handler_called.append((user_id, message))

        connection_manager.register_handler("test_type", dummy_handler)
        await connection_manager.connect(mock_websocket, "user_123")

        await connection_manager.handle_message("user_123", {"type": "test_type", "data": "value"})

        assert len(handler_called) == 1
        assert handler_called[0][0] == "user_123"
        assert handler_called[0][1]["type"] == "test_type"

    @pytest.mark.asyncio
    async def test_handle_message_no_handler(self, connection_manager, mock_websocket, caplog):
        """Test that unhandled message types are logged."""
        await connection_manager.connect(mock_websocket, "user_123")

        await connection_manager.handle_message("user_123", {"type": "unknown_type"})

        assert "No handler for message type" in caplog.text


class TestConnectionManagerStats:
    """Tests for statistics methods."""

    @pytest.mark.asyncio
    async def test_get_connection_count(self, connection_manager, mock_websocket):
        """Test get_connection_count."""
        assert connection_manager.get_connection_count() == 0

        await connection_manager.connect(mock_websocket, "user_1")
        assert connection_manager.get_connection_count() == 1

        await connection_manager.connect(mock_websocket, "user_2")
        assert connection_manager.get_connection_count() == 2

    @pytest.mark.asyncio
    async def test_get_user_count(self, connection_manager, mock_websocket):
        """Test get_user_count."""
        assert connection_manager.get_user_count() == 0

        await connection_manager.connect(mock_websocket, "user_1")
        assert connection_manager.get_user_count() == 1

        await connection_manager.connect(mock_websocket, "user_1")  # Same user
        assert connection_manager.get_user_count() == 1

        await connection_manager.connect(mock_websocket, "user_2")
        assert connection_manager.get_user_count() == 2

    @pytest.mark.asyncio
    async def test_get_user_connections(self, connection_manager, mock_websocket):
        """Test get_user_connections."""
        cid1 = await connection_manager.connect(mock_websocket, "user_1")
        cid2 = await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")

        conns = connection_manager.get_user_connections("user_1")
        assert len(conns) == 2
        assert cid1 in conns
        assert cid2 in conns

    @pytest.mark.asyncio
    async def test_is_user_connected(self, connection_manager, mock_websocket):
        """Test is_user_connected."""
        assert connection_manager.is_user_connected("user_1") is False

        await connection_manager.connect(mock_websocket, "user_1")
        assert connection_manager.is_user_connected("user_1") is True

        await connection_manager.disconnect_user("user_1")
        assert connection_manager.is_user_connected("user_1") is False

    @pytest.mark.asyncio
    async def test_get_stats(self, connection_manager, mock_websocket):
        """Test get_stats returns complete statistics."""
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")

        stats = connection_manager.get_stats()

        assert stats["total_connections"] == 3
        assert stats["unique_users"] == 2
        assert stats["connections_per_user"]["user_1"] == 2
        assert stats["connections_per_user"]["user_2"] == 1


class TestConnectionManagerCleanup:
    """Tests for cleanup task."""

    @pytest.mark.asyncio
    async def test_start_stop_cleanup_task(self, connection_manager):
        """Test starting and stopping the cleanup task."""
        await connection_manager.start_cleanup_task()
        assert connection_manager._running is True
        assert connection_manager._cleanup_task is not None

        await connection_manager.stop_cleanup_task()
        assert connection_manager._running is False

    @pytest.mark.asyncio
    async def test_disconnect_all(self, connection_manager, mock_websocket):
        """Test disconnect_all."""
        await connection_manager.connect(mock_websocket, "user_1")
        await connection_manager.connect(mock_websocket, "user_2")

        await connection_manager.disconnect_all()

        assert connection_manager.get_connection_count() == 0
        assert connection_manager.get_user_count() == 0