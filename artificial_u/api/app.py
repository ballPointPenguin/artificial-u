import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from artificial_u.api.config import get_settings
from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.events import JobEventHub
from artificial_u.api.middlewares.cors_middleware import setup_cors
from artificial_u.api.middlewares.error_handler import add_error_handlers
from artificial_u.api.middlewares.logging_middleware import LoggingMiddleware
from artificial_u.api.routers.auth import router as auth_router
from artificial_u.api.routers.courses import router as courses_router
from artificial_u.api.routers.departments import router as departments_router
from artificial_u.api.routers.health import router as health_router
from artificial_u.api.routers.index import router as index_router
from artificial_u.api.routers.jobs import router as jobs_router
from artificial_u.api.routers.lectures import router as lectures_router
from artificial_u.api.routers.professors import router as professors_router
from artificial_u.api.routers.topics import course_topics_router
from artificial_u.api.routers.topics import router as topics_router
from artificial_u.api.routers.voices import router as voice_router
from artificial_u.api.utils.logging import setup_logging
from artificial_u.api.worker import Worker
from artificial_u.config.settings import Environment


def create_application() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application
    """
    settings = get_settings()

    # Setup logging first
    setup_logging(settings)

    # Prepare worker now so it's available in lifespan closure
    repository_factory = get_repository_factory()
    job_events = JobEventHub()
    worker = Worker(repository_factory, event_hub=job_events)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # attach event hub to app state for routers and worker to use
        app.state.job_events = job_events
        # Increase default executor for blocking offloads
        loop = asyncio.get_running_loop()
        if not hasattr(app.state, "default_executor"):
            app.state.default_executor = ThreadPoolExecutor(max_workers=8)
        loop.set_default_executor(app.state.default_executor)
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()

    app = FastAPI(
        title="Artificial University API",
        description="""
        API for Artificial University, managing audio generations and model interactions
        """,
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        # Add global dependencies that will be applied to all routes
        dependencies=[Depends(get_repository_factory)],
        # Use debug mode only in development environment
        debug=settings.environment == Environment.DEVELOPMENT,
        lifespan=lifespan,
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
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(courses_router, prefix="/api/v1")
    app.include_router(departments_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(lectures_router, prefix="/api/v1")
    app.include_router(professors_router, prefix="/api/v1")
    app.include_router(course_topics_router, prefix="/api/v1")
    app.include_router(topics_router, prefix="/api/v1")
    app.include_router(voice_router, prefix="/api/v1")

    return app


app = create_application()

# For direct execution with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("artificial_u.api.app:app", host="0.0.0.0", port=8000, reload=True)
