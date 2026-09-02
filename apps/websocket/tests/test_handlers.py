"""
Tests for WebSocket Handlers.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocketDisconnect


class TestChatHandler:
    """Tests for ChatHandler."""

    @pytest.mark.asyncio
    async def test_handle_connection_sends_welcome(self, chat_handler, mock_websocket):
        """Test that handle_connection sends welcome message."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)

        await chat_handler.handle_connection(mock_websocket, "user_123")

        # Check welcome message was sent
        calls = mock_websocket.send_json.call_args_list
        welcome_sent = any(
            call[0][0].get("type") == "chat_welcome" for call in calls
        )
        assert welcome_sent

    @pytest.mark.asyncio
    async def test_handle_connection_sends_history(self, chat_handler, mock_websocket, mock_redis):
        """Test that handle_connection sends recent history."""
        # Mock Redis to return some history
        mock_redis.lrange.return_value = [
            json.dumps({"type": "chat_message", "content": "hello", "sender_id": "user_456"})
        ]

        mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)

        await chat_handler.handle_connection(mock_websocket, "user_123")

        # Check history was requested
        mock_redis.lrange.assert_called()
        # Check history was sent
        calls = mock_websocket.send_json.call_args_list
        history_sent = any(
            call[0][0].get("type") == "chat_history" for call in calls
        )
        assert history_sent

    @pytest.mark.asyncio
    async def test_send_message_stores_and_delivers(self, chat_handler, mock_redis):
        """Test send_message stores message and delivers to recipient."""
        # Mock send_to_user to return 1 (delivered)
        chat_handler.connection_manager.send_to_user = AsyncMock(return_value=1)

        result = await chat_handler.send_message(
            recipient_id="user_456",
            sender_id="user_123",
            content="Hello!",
            message_type="text",
        )

        assert result["status"] == "sent"
        assert result["delivered"] is True
        assert "message_id" in result

        # Verify message was stored in Redis
        mock_redis.lpush.assert_called()
        mock_redis.ltrim.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_not_delivered_when_offline(self, chat_handler, mock_redis):
        """Test send_message when recipient is offline."""
        chat_handler.connection_manager.send_to_user = AsyncMock(return_value=0)

        result = await chat_handler.send_message(
            recipient_id="offline_user",
            sender_id="user_123",
            content="Hello!",
        )

        assert result["status"] == "sent"
        assert result["delivered"] is False

    @pytest.mark.asyncio
    async def test_handle_chat_message_stores_for_both(self, chat_handler, mock_redis):
        """Test that incoming chat message is stored for both sender and recipient."""
        chat_handler.connection_manager.send_to_user = AsyncMock(return_value=1)

        await chat_handler._handle_chat_message("user_123", {
            "recipient_id": "user_456",
            "content": "Hello!",
            "message_type": "text",
        })

        # Should store for both recipient and sender
        assert mock_redis.lpush.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_chat_message_sends_to_recipient(self, chat_handler, mock_redis):
        """Test that chat message is sent to recipient."""
        chat_handler.connection_manager.send_to_user = AsyncMock(return_value=1)

        await chat_handler._handle_chat_message("user_123", {
            "recipient_id": "user_456",
            "content": "Hello!",
        })

        # Check send_to_user called for recipient
        calls = chat_handler.connection_manager.send_to_user.call_args_list
        recipient_called = any(
            call[0][0] == "user_456" for call in calls
        )
        assert recipient_called

    @pytest.mark.asyncio
    async def test_handle_chat_message_ignores_invalid(self, chat_handler, mock_redis, caplog):
        """Test that invalid chat messages are ignored."""
        await chat_handler._handle_chat_message("user_123", {"content": "no recipient"})
        await chat_handler._handle_chat_message("user_123", {"recipient_id": "user_456"})

        assert "Invalid chat message" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_chat_history(self, chat_handler, mock_redis):
        """Test handling chat history request."""
        mock_redis.lrange.return_value = [
            json.dumps({"type": "chat_message", "content": "msg1"}),
            json.dumps({"type": "chat_message", "content": "msg2"}),
        ]
        chat_handler.connection_manager.send_to_user = AsyncMock()

        await chat_handler._handle_chat_history("user_123", {
            "conversation_id": "conv_1",
            "limit": 10,
            "offset": 0,
        })

        mock_redis.lrange.assert_called()
        chat_handler.connection_manager.send_to_user.assert_called_once()
        call_args = chat_handler.connection_manager.send_to_user.call_args
        assert call_args[0][0] == "user_123"
        assert call_args[0][1]["type"] == "chat_history"
        assert len(call_args[0][1]["messages"]) == 2

    @pytest.mark.asyncio
    async def test_handle_typing_indicator(self, chat_handler):
        """Test typing indicator handling."""
        chat_handler.connection_manager.send_to_user = AsyncMock()

        await chat_handler._handle_typing_indicator("user_123", {
            "recipient_id": "user_456",
            "is_typing": True,
        })

        chat_handler.connection_manager.send_to_user.assert_called_once()
        call_args = chat_handler.connection_manager.send_to_user.call_args
        assert call_args[0][0] == "user_456"
        assert call_args[0][1]["type"] == "chat_typing"
        assert call_args[0][1]["is_typing"] is True

    @pytest.mark.asyncio
    async def test_handle_read_receipt(self, chat_handler, mock_redis):
        """Test read receipt handling."""
        chat_handler.connection_manager.send_to_user = AsyncMock()

        await chat_handler._handle_read_receipt("user_123", {
            "message_ids": ["msg_1", "msg_2"],
            "sender_id": "user_456",
        })

        # Should store read receipts in Redis
        assert mock_redis.set.call_count == 2
        # Should notify sender
        chat_handler.connection_manager.send_to_user.assert_called_once()
        call_args = chat_handler.connection_manager.send_to_user.call_args
        assert call_args[0][0] == "user_456"
        assert call_args[0][1]["type"] == "chat_read"


class TestLocationHandler:
    """Tests for LocationHandler."""

    @pytest.mark.asyncio
    async def test_handle_connection(self, location_handler, mock_websocket):
        """Test location handler connection."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)

        await location_handler.handle_connection(mock_websocket, "user_123")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_location(self, location_handler, mock_redis):
        """Test broadcasting location update."""
        location_handler.connection_manager.broadcast = AsyncMock(return_value=5)

        result = await location_handler.broadcast_location(
            user_id="user_123",
            latitude=40.7128,
            longitude=-74.0060,
            accuracy=10.0,
            heading=90.0,
            speed=5.0,
        )

        assert result["status"] == "broadcast"
        location_handler.connection_manager.broadcast.assert_called_once()
        call_args = location_handler.connection_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "location_update"
        assert call_args["user_id"] == "user_123"
        assert call_args["latitude"] == 40.7128
        assert call_args["longitude"] == -74.0060


class TestTransitHandler:
    """Tests for TransitHandler."""

    @pytest.mark.asyncio
    async def test_handle_connection(self, transit_handler, mock_websocket):
        """Test transit handler connection."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)

        await transit_handler.handle_connection(mock_websocket, "user_123")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert(self, transit_handler):
        """Test sending transit alert."""
        transit_handler.connection_manager.broadcast_to_users = AsyncMock(return_value=3)

        result = await transit_handler.send_alert(
            user_ids=["user_1", "user_2", "user_3"],
            route_id="route_123",
            message="Delay on line 5",
            severity="warning",
        )

        assert result["status"] == "sent"
        transit_handler.connection_manager.broadcast_to_users.assert_called_once()
        call_args = transit_handler.connection_manager.broadcast_to_users.call_args
        assert call_args[0][0] == ["user_1", "user_2", "user_3"]
        assert call_args[0][1]["type"] == "transit_alert"
        assert call_args[0][1]["route_id"] == "route_123"
        assert call_args[0][1]["severity"] == "warning"


class TestNotificationHandler:
    """Tests for NotificationHandler."""

    @pytest.mark.asyncio
    async def test_handle_connection(self, notification_handler, mock_websocket):
        """Test notification handler connection."""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect(code=1000)

        await notification_handler.handle_connection(mock_websocket, "user_123")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification(self, notification_handler):
        """Test sending notification."""
        notification_handler.connection_manager.send_to_user = AsyncMock(return_value=1)

        result = await notification_handler.send_notification(
            user_id="user_123",
            title="New Message",
            body="You have a new message",
            notification_type="info",
            data={"conversation_id": "conv_1"},
        )

        assert result["status"] == "sent"
        notification_handler.connection_manager.send_to_user.assert_called_once()
        call_args = notification_handler.connection_manager.send_to_user.call_args
        assert call_args[0][0] == "user_123"
        assert call_args[0][1]["type"] == "notification"
        assert call_args[0][1]["title"] == "New Message"
        assert call_args[0][1]["notification_type"] == "info"

    @pytest.mark.asyncio
    async def test_send_notification_not_delivered(self, notification_handler):
        """Test notification when user is offline."""
        notification_handler.connection_manager.send_to_user = AsyncMock(return_value=0)

        result = await notification_handler.send_notification(
            user_id="offline_user",
            title="Test",
            body="Test body",
        )

        assert result["status"] == "sent"
        # Still returns sent even if not delivered (stored for later)


class TestUnifiedWebSocket:
    """Tests for unified WebSocket endpoint logic."""

    @pytest.mark.asyncio
    async def test_connection_manager_handles_all_message_types(self, connection_manager):
        """Test that connection manager can register and handle multiple message types."""
        from ws_service.handlers.chat_handler import ChatHandler
        from ws_service.handlers.location_handler import LocationHandler
        from ws_service.handlers.transit_handler import TransitHandler
        from ws_service.handlers.notification_handler import NotificationHandler

        # Create handlers (they register themselves)
        chat = ChatHandler(connection_manager, connection_manager.redis)
        location = LocationHandler(connection_manager, connection_manager.redis)
        transit = TransitHandler(connection_manager, connection_manager.redis)
        notification = NotificationHandler(connection_manager, connection_manager.redis)

        # Verify all handlers registered their message types
        expected_types = {
            "chat_message", "chat_history", "chat_typing", "chat_read",
            "location_update", "location_subscribe", "location_unsubscribe",
            "transit_subscribe", "transit_unsubscribe", "transit_alert",
            "notification", "notification_read",
        }

        for msg_type in expected_types:
            assert msg_type in connection_manager._message_handlers