"""
WebSocket Message Router
Routes incoming WebSocket messages to appropriate handlers based on message type.
"""
import logging
from uuid import UUID

from .handlers import (
    chat_handler,
    itinerary_handler,
    location_handler,
    notification_handler,
    transit_handler,
)
from .schemas.messages import WSMessage, WSMessageType

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes WebSocket messages to the correct handler."""

    async def route(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route message to appropriate handler based on type."""
        msg_type = message.type

        # Chat messages
        if msg_type in (
            WSMessageType.CHAT_MESSAGE,
            WSMessageType.CHAT_HISTORY,
            WSMessageType.CHAT_TYPING,
            WSMessageType.CHAT_READ,
        ):
            return await chat_handler.handle_message(connection_id, message)

        # Location messages
        if msg_type in (
            WSMessageType.LOCATION_UPDATE,
            WSMessageType.LOCATION_SHARE,
        ):
            return await location_handler.handle_message(connection_id, message)

        # Transit messages
        if msg_type in (
            WSMessageType.TRANSIT_SUBSCRIBE,
            WSMessageType.TRANSIT_UNSUBSCRIBE,
            WSMessageType.TRANSIT_NEARBY,
        ):
            return await transit_handler.handle_message(connection_id, message)

        # Itinerary messages
        if msg_type in (
            WSMessageType.ITINERARY_UPDATE,
            WSMessageType.ITINERARY_COLLAB,
        ):
            return await itinerary_handler.handle_message(connection_id, message)

        # Notification messages
        if msg_type in (
            WSMessageType.NOTIFICATION_READ,
            WSMessageType.NOTIFICATION_SUBSCRIBE,
        ):
            return await notification_handler.handle_message(connection_id, message)

        logger.warning("Unknown message type: %s from connection %s", msg_type, connection_id)
        return None
