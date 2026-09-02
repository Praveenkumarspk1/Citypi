"""
WebSocket Server
Main WebSocket endpoint and message routing
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer

from ...infrastructure.auth.jwt_auth import verify_token
from .handlers import (
    chat_handler,
    connection_manager,
    itinerary_handler,
    location_handler,
    notification_handler,
    transit_handler,
)
from .schemas.messages import (
    WSAuthMessage,
    WSError,
    WSMessage,
    WSMessageType,
    WSPingMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Security scheme for WebSocket
security = HTTPBearer(auto_error=False)


async def authenticate_websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
    authorization: str | None = None,
) -> dict | None:
    """Authenticate WebSocket connection"""
    # Try to get token from query param or Authorization header
    auth_token = token
    if not auth_token and authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    if not auth_token:
        return None

    # Verify token
    payload = verify_token(auth_token)
    if not payload:
        return None

    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
    }


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    device_id: str | None = Query(None),
    platform: str | None = Query(None),
    app_version: str | None = Query(None),
):
    """
    Main WebSocket endpoint

    Query Parameters:
    - token: JWT authentication token (optional, can also use Authorization header)
    - device_id: Unique device identifier
    - platform: Client platform (ios, android, web)
    - app_version: Client app version
    """
    # Accept connection
    connection_id = await connection_manager.connect(websocket)

    # Try to authenticate
    user = await authenticate_websocket(websocket, token)

    if user:
        await connection_manager.authenticate(
            connection_id=connection_id,
            user_id=UUID(user["id"]),
            device_id=device_id,
            platform=platform,
            app_version=app_version,
        )

        # Send auth success
        auth_success = WSMessage(
            type=WSMessageType.AUTH_SUCCESS,
            payload={
                "user_id": user["id"],
                "connection_id": str(connection_id),
            },
        )
        await connection_manager.send_message(connection_id, auth_success)
    else:
        # Send auth required (but allow unauthenticated connection for public features)
        auth_required = WSMessage(
            type=WSMessageType.AUTH_ERROR,
            payload={
                "message": "Authentication required for full features",
                "code": "AUTH_REQUIRED",
            },
        )
        await connection_manager.send_message(connection_id, auth_required)

    # Initialize handlers
    await location_handler.initialize()
    await transit_handler.initialize()
    await notification_handler.initialize()

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            # Update activity
            await connection_manager.update_activity(connection_id)

            try:
                message = WSMessage.model_validate_json(data)
            except Exception as e:
                error_msg = WSMessage(
                    type=WSMessageType.ERROR,
                    payload=WSError(code="INVALID_JSON", message=str(e)).model_dump(),
                )
                await connection_manager.send_message(connection_id, error_msg)
                continue

            # Handle message based on type
            response = await route_message(connection_id, message)

            if response:
                await connection_manager.send_message(connection_id, response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await connection_manager.disconnect(connection_id)


async def route_message(connection_id: UUID, message: WSMessage) -> WSMessage | None:
    """Route message to appropriate handler"""
    msg_type = message.type

    # Handle system messages
    if msg_type == WSMessageType.PING:
        ping_msg = WSPingMessage(**message.payload)
        pong = await connection_manager.handle_ping(connection_id, ping_msg)
        return WSMessage(
            type=WSMessageType.PONG,
            payload=pong.model_dump(),
            correlation_id=message.message_id,
        )

    if msg_type == WSMessageType.AUTH:
        # Re-authentication
        try:
            auth_msg = WSAuthMessage(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_AUTH", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        payload = verify_token(auth_msg.token)
        if not payload:
            return WSMessage(
                type=WSMessageType.AUTH_ERROR,
                payload=WSError(code="INVALID_TOKEN", message="Invalid or expired token").model_dump(),
                correlation_id=message.message_id,
            )

        user_id = UUID(payload["sub"])
        success = await connection_manager.authenticate(
            connection_id=connection_id,
            user_id=user_id,
            device_id=auth_msg.device_id,
            platform=auth_msg.platform,
            app_version=auth_msg.app_version,
        )

        if success:
            return WSMessage(
                type=WSMessageType.AUTH_SUCCESS,
                payload={"user_id": str(user_id), "connection_id": str(connection_id)},
                correlation_id=message.message_id,
            )
        else:
            return WSMessage(
                type=WSMessageType.AUTH_ERROR,
                payload=WSError(code="AUTH_FAILED", message="Authentication failed").model_dump(),
                correlation_id=message.message_id,
            )

    # Route to handlers
    # Chat messages
    if msg_type in [
        WSMessageType.CHAT_MESSAGE,
        WSMessageType.CHAT_HISTORY,
        WSMessageType.CHAT_TYPING,
        WSMessageType.CHAT_READ,
    ]:
        return await chat_handler.handle_message(connection_id, message)

    # Location messages
    if msg_type in [
        WSMessageType.LOCATION_UPDATE,
        WSMessageType.LOCATION_SUBSCRIBE,
        WSMessageType.LOCATION_UNSUBSCRIBE,
        WSMessageType.NEARBY_USERS,
    ]:
        return await location_handler.handle_message(connection_id, message)

    # Transit messages
    if msg_type in [
        WSMessageType.TRANSIT_SUBSCRIBE,
        WSMessageType.TRANSIT_UNSUBSCRIBE,
        WSMessageType.VEHICLE_POSITION,
        WSMessageType.TRIP_UPDATE,
        WSMessageType.SERVICE_ALERT,
    ]:
        return await transit_handler.handle_message(connection_id, message)

    # Itinerary messages
    if msg_type in [
        WSMessageType.ITINERARY_UPDATE,
        WSMessageType.ITINERARY_ITEM_ADDED,
        WSMessageType.ITINERARY_ITEM_UPDATED,
        WSMessageType.ITINERARY_ITEM_REMOVED,
        WSMessageType.ITINERARY_COLLABORATOR_JOINED,
        WSMessageType.ITINERARY_COLLABORATOR_LEFT,
    ]:
        return await itinerary_handler.handle_message(connection_id, message)

    # Notification messages
    if msg_type in [
        WSMessageType.NOTIFICATION,
        WSMessageType.NOTIFICATION_READ,
    ]:
        return await notification_handler.handle_message(connection_id, message)

    # Unknown message type
    return WSMessage(
        type=WSMessageType.ERROR,
        payload=WSError(code="UNKNOWN_MESSAGE_TYPE", message=f"Unknown message type: {msg_type}").model_dump(),
        correlation_id=message.message_id,
    )


# Health check endpoint for WebSocket
@router.get("/health")
async def websocket_health():
    """WebSocket service health check"""
    stats = connection_manager.get_stats()
    return {
        "status": "healthy",
        "service": "websocket",
        "stats": stats,
    }


# Stats endpoint
@router.get("/stats")
async def websocket_stats():
    """WebSocket connection statistics"""
    return connection_manager.get_stats()
