"""
Main FastAPI Application
"""
from contextlib import asynccontextmanager

import structlog
from ai_smart_city_concierge.infrastructure.config.database import close_db, init_db
from ai_smart_city_concierge.infrastructure.config.redis import close_redis
from ai_smart_city_concierge.infrastructure.config.settings import get_settings
from ai_smart_city_concierge.infrastructure.config.vector_store import (
    close_vector_store,
    init_vector_store,
)
from ai_smart_city_concierge.interfaces.api.v1.middleware import (
    AuthMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from ai_smart_city_concierge.interfaces.api.v1.routes import (
    analytics,
    auth,
    conversations,
    feedback,
    health,
    itineraries,
    media,
    pois,
    transit,
    users,
    weather,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()

    logger.info("Starting application", version=settings.app_version, environment=settings.environment)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize vector store
    await init_vector_store()
    logger.info("Vector store initialized")

    # Create default collections
    from .infrastructure.config.vector_store import Collections, get_vector_store
    vector_store = get_vector_store()
    for collection in [
        Collections.POI_EMBEDDINGS,
        Collections.CONVERSATION_EMBEDDINGS,
        Collections.ITINERARY_EMBEDDINGS,
        Collections.MEDIA_EMBEDDINGS,
        Collections.DOCUMENT_EMBEDDINGS,
        Collections.LANDMARK_EMBEDDINGS,
    ]:
        await vector_store.create_collection(
            name=collection,
            dimension=settings.ai.embedding_dimensions,
            distance="cosine",
        )
    logger.info("Vector collections created")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_vector_store()
    await close_redis()
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-grade AI Smart City Concierge API",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods_list,
        allow_headers=settings.cors_allow_headers_list,
    )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Custom middleware (order matters - last added runs first)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)

    # Include routers
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(pois.router, prefix=settings.api_prefix)
    app.include_router(conversations.router, prefix=settings.api_prefix)
    app.include_router(itineraries.router, prefix=settings.api_prefix)
    app.include_router(transit.router, prefix=settings.api_prefix)
    app.include_router(weather.router, prefix=settings.api_prefix)
    app.include_router(media.router, prefix=settings.api_prefix)
    app.include_router(feedback.router, prefix=settings.api_prefix)
    app.include_router(analytics.router, prefix=settings.api_prefix)

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
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use structlog
    )
