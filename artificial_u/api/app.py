import asyncio
import logging
import os
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
from artificial_u.api.routers.faculties import router as faculties_router
from artificial_u.api.routers.featured import router as featured_router
from artificial_u.api.routers.health import router as health_router
from artificial_u.api.routers.index import router as index_router
from artificial_u.api.routers.jobs import router as jobs_router
from artificial_u.api.routers.lectures import router as lectures_router
from artificial_u.api.routers.preferences import router as preferences_router
from artificial_u.api.routers.professors import router as professors_router
from artificial_u.api.routers.quickstart import router as quickstart_router
from artificial_u.api.routers.search import router as search_router
from artificial_u.api.routers.share import router as share_router
from artificial_u.api.routers.stats import router as stats_router
from artificial_u.api.routers.students import router as students_router
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
        # Store repository factory in app state for cleanup
        app.state.repository_factory = repository_factory
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
            # Stop worker first
            await worker.stop()

            # Close SSE connections by clearing the hub
            try:
                if hasattr(app.state, "job_events") and app.state.job_events:
                    # Clear all subscribers to close SSE connections
                    app.state.job_events._subscribers.clear()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Error closing SSE connections: {e}")

            # Dispose of database engines to close connections
            try:
                app.state.repository_factory.dispose_engines()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Error disposing repository engines: {e}")

            # Give a moment for connections to close
            await asyncio.sleep(0.1)

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
    app.include_router(faculties_router, prefix="/api/v1")
    app.include_router(featured_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(lectures_router, prefix="/api/v1")
    app.include_router(preferences_router, prefix="/api/v1")
    app.include_router(professors_router, prefix="/api/v1")
    app.include_router(students_router, prefix="/api/v1")
    app.include_router(course_topics_router, prefix="/api/v1")
    app.include_router(topics_router, prefix="/api/v1")
    app.include_router(voice_router, prefix="/api/v1")
    app.include_router(quickstart_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    # Share / unfurl endpoints for rich link previews (OG/Twitter tags)
    app.include_router(share_router)

    return app


app = create_application()

# For direct execution with Uvicorn
if __name__ == "__main__":
    import uvicorn

    port_env = os.environ.get("FASTAPI_PORT", "8000")
    try:
        port = int(port_env)
    except ValueError:
        logging.getLogger(__name__).warning(
            "Invalid FASTAPI_PORT '%s'; falling back to 8000", port_env
        )
        port = 8000

    uvicorn.run(
        "artificial_u.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        # Add timeout options for better shutdown behavior during development
        access_log=False,  # Disable access log during development to reduce noise
    )
