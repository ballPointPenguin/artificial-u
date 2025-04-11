from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from artificial_u.api.config import get_settings
from artificial_u.api.middlewares.logging_middleware import LoggingMiddleware
from artificial_u.api.middlewares.error_handler import add_error_handlers
from artificial_u.api.utils.logging import setup_logging

# Import routers
from artificial_u.api.routers.health import router as health_router
from artificial_u.api.routers.index import router as index_router
from artificial_u.api.routers.professors import router as professors_router
from artificial_u.api.routers.departments import router as departments_router


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
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middlewares
    app.add_middleware(LoggingMiddleware)

    # Add error handlers
    add_error_handlers(app)

    # Include routers with proper prefixes
    app.include_router(index_router, prefix="/api")
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(professors_router, prefix="/api/v1")
    app.include_router(departments_router, prefix="/api/v1")

    return app


app = create_application()

# For direct execution with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("artificial_u.api.app:app", host="0.0.0.0", port=8000, reload=True)
