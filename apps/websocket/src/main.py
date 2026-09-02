"""
WebSocket Service Main Entry Point

Real-time WebSocket server for the AI Smart City Concierge.
Handles chat, location sharing, transit updates, and notifications.
"""

from contextlib import asynccontextmanager

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from ws_service.config.settings import get_settings
from ws_service.connection_manager import ConnectionManager
from ws_service.handlers.chat_handler import ChatHandler
from ws_service.handlers.location_handler import LocationHandler
from ws_service.handlers.notification_handler import NotificationHandler
from ws_service.handlers.transit_handler import TransitHandler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class WebSocketService:
    """Main WebSocket service that coordinates all real-time connections."""

    def __init__(self, settings):
        self.settings = settings
        self._running = False

        # Core infrastructure
        self.redis: redis.Redis | None = None

        # Connection manager
        self.connection_manager: ConnectionManager | None = None

        # Handlers
        self.chat_handler: ChatHandler | None = None
        self.location_handler: LocationHandler | None = None
        self.transit_handler: TransitHandler | None = None
        self.notification_handler: NotificationHandler | None = None

    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info("Initializing WebSocket service...")

        # Initialize Redis
        self.redis = redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.redis.ping()
        logger.info("Connected to Redis")

        # Initialize connection manager
        self.connection_manager = ConnectionManager(self.redis)
        logger.info("Initialized connection manager")

        # Initialize handlers
        self.chat_handler = ChatHandler(self.connection_manager, self.redis)
        self.location_handler = LocationHandler(self.connection_manager, self.redis)
        self.transit_handler = TransitHandler(self.connection_manager, self.redis)
        self.notification_handler = NotificationHandler(self.connection_manager, self.redis)

        logger.info("Initialized all handlers")

    async def start(self) -> None:
        """Start the WebSocket service."""
        if self._running:
            return

        self._running = True
        logger.info("Starting WebSocket service...")

        # Start connection manager cleanup task
        await self.connection_manager.start_cleanup_task()

        logger.info("WebSocket service started successfully")

    async def stop(self) -> None:
        """Stop the WebSocket service."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping WebSocket service...")

        # Stop cleanup task
        await self.connection_manager.stop_cleanup_task()

        # Close all connections
        await self.connection_manager.disconnect_all()

        # Close Redis connection
        if self.redis:
            await self.redis.close()

        logger.info("WebSocket service stopped")

    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running

    async def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self._running,
            "connections": self.connection_manager.get_stats() if self.connection_manager else {},
        }


# Global WebSocket service instance
_ws_service: WebSocketService | None = None


async def get_ws_service() -> WebSocketService:
    """Get or create the WebSocket service instance."""
    global _ws_service
    if _ws_service is None:
        settings = get_settings()
        _ws_service = WebSocketService(settings)
        await _ws_service.initialize()
    return _ws_service


async def shutdown_ws_service() -> None:
    """Shutdown the WebSocket service."""
    global _ws_service
    if _ws_service:
        await _ws_service.stop()
        _ws_service = None


@asynccontextmanager
async def ws_lifespan(app: FastAPI):
    """Application lifespan manager for WebSocket service."""
    settings = get_settings()

    logger.info("Starting WebSocket application", version=settings.app_version, environment=settings.environment)

    # Initialize service
    service = await get_ws_service()
    await service.start()

    yield

    # Shutdown
    logger.info("Shutting down WebSocket application")
    await shutdown_ws_service()
    logger.info("WebSocket application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application for WebSocket service."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} - WebSocket Service",
        version=settings.app_version,
        description="Real-time WebSocket server for AI Smart City Concierge",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=ws_lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods_list,
        allow_headers=settings.cors_allow_headers_list,
    )

    # Health check endpoints
    @app.get("/health/live")
    async def liveness_check():
        """Liveness probe for Kubernetes."""
        return {"status": "alive", "service": "websocket"}

    @app.get("/health/ready")
    async def readiness_check():
        """Readiness probe for Kubernetes."""
        service = await get_ws_service()
        return {
            "status": "ready" if service.is_running() else "not_ready",
            "service": "websocket",
            "connections": service.connection_manager.get_stats() if service.connection_manager else {},
        }

    @app.get("/health/status")
    async def detailed_status():
        """Detailed status endpoint."""
        service = await get_ws_service()
        return await service.get_status()

    # WebSocket endpoints
    @app.websocket("/ws/chat/{user_id}")
    async def websocket_chat(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for chat messaging."""
        service = await get_ws_service()
        await service.chat_handler.handle_connection(websocket, user_id)

    @app.websocket("/ws/location/{user_id}")
    async def websocket_location(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for location sharing."""
        service = await get_ws_service()
        await service.location_handler.handle_connection(websocket, user_id)

    @app.websocket("/ws/transit/{user_id}")
    async def websocket_transit(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for transit updates."""
        service = await get_ws_service()
        await service.transit_handler.handle_connection(websocket, user_id)

    @app.websocket("/ws/notifications/{user_id}")
    async def websocket_notifications(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for notifications."""
        service = await get_ws_service()
        await service.notification_handler.handle_connection(websocket, user_id)

    # Unified WebSocket endpoint (handles all message types)
    @app.websocket("/ws/{user_id}")
    async def websocket_unified(websocket: WebSocket, user_id: str):
        """Unified WebSocket endpoint handling all message types."""
        service = await get_ws_service()
        await service.connection_manager.connect(websocket, user_id)

        try:
            while True:
                data = await websocket.receive_json()
                await service.connection_manager.handle_message(user_id, data)
        except WebSocketDisconnect:
            await service.connection_manager.disconnect(user_id)
        except Exception as e:
            logger.error("WebSocket error", user_id=user_id, error=str(e))
            await service.connection_manager.disconnect(user_id)

    # REST endpoints for sending messages
    @app.post("/api/v1/chat/send")
    async def send_chat_message(message: dict):
        """Send a chat message to a user via REST."""
        service = await get_ws_service()
        await service.chat_handler.send_message(
            recipient_id=message.get("recipient_id"),
            sender_id=message.get("sender_id"),
            content=message.get("content"),
            message_type=message.get("message_type", "text"),
        )
        return {"status": "sent"}

    @app.post("/api/v1/location/broadcast")
    async def broadcast_location(location: dict):
        """Broadcast location update via REST."""
        service = await get_ws_service()
        await service.location_handler.broadcast_location(
            user_id=location.get("user_id"),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
            accuracy=location.get("accuracy"),
            heading=location.get("heading"),
            speed=location.get("speed"),
        )
        return {"status": "broadcast"}

    @app.post("/api/v1/transit/alert")
    async def send_transit_alert(alert: dict):
        """Send transit alert via REST."""
        service = await get_ws_service()
        await service.transit_handler.send_alert(
            user_ids=alert.get("user_ids", []),
            route_id=alert.get("route_id"),
            message=alert.get("message"),
            severity=alert.get("severity", "info"),
        )
        return {"status": "sent"}

    @app.post("/api/v1/notifications/send")
    async def send_notification(notification: dict):
        """Send notification via REST."""
        service = await get_ws_service()
        await service.notification_handler.send_notification(
            user_id=notification.get("user_id"),
            title=notification.get("title"),
            body=notification.get("body"),
            notification_type=notification.get("type", "info"),
            data=notification.get("data", {}),
        )
        return {"status": "sent"}

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_config=None,  # Use structlog
    )
