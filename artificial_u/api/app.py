from fastapi import Depends, FastAPI

from artificial_u.api.config import get_settings
from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.middlewares.cors_middleware import setup_cors
from artificial_u.api.middlewares.error_handler import add_error_handlers
from artificial_u.api.middlewares.logging_middleware import LoggingMiddleware
from artificial_u.api.routers.courses import router as courses_router
from artificial_u.api.routers.departments import router as departments_router

# Import routers
from artificial_u.api.routers.health import router as health_router
from artificial_u.api.routers.index import router as index_router
from artificial_u.api.routers.lectures import router as lectures_router
from artificial_u.api.routers.professors import router as professors_router
from artificial_u.api.utils.logging import setup_logging
from artificial_u.config.settings import Environment


def create_application() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application
    """
    settings = get_settings()

    # Setup logging first
    setup_logging(settings)

    app = FastAPI(
        title="Artificial University API",
        description="API for Artificial University, managing audio generations and model interactions",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        # Add global dependencies that will be applied to all routes
        dependencies=[Depends(get_repository_factory)],
        # Use debug mode only in development environment
        debug=settings.environment == Environment.DEVELOPMENT,
    )

    # Configure CORS
    setup_cors(app)

    # Add custom middlewares
    app.add_middleware(LoggingMiddleware)

    # Add error handlers
    add_error_handlers(app)

    # Include routers with proper prefixes
    app.include_router(index_router, prefix="/api")
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(professors_router, prefix="/api/v1")
    app.include_router(departments_router, prefix="/api/v1")
    app.include_router(courses_router, prefix="/api/v1")
    app.include_router(lectures_router, prefix="/api/v1")

    return app


app = create_application()

# For direct execution with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("artificial_u.api.app:app", host="0.0.0.0", port=8000, reload=True)
