"""
Shared database engine singleton.

This module provides a single shared SQLAlchemy engine instance that is reused
across all repositories, preventing connection pool explosion that occurs when
each repository creates its own engine.

For RDS PostgreSQL with the new rds_reserved feature (PG 17.1+, 16.5+, etc.),
some connections are reserved for administrative purposes. This module ensures
we use a controlled connection pool that stays within limits.
"""

import logging
import threading
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Global engine singleton
_engine: Optional[Engine] = None
_engine_lock = threading.Lock()


def get_engine(
    db_url: str,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 1800,
    pool_pre_ping: bool = True,
) -> Engine:
    """
    Get or create a shared database engine singleton.

    This function ensures only one engine (and thus one connection pool) exists
    for the entire application, preventing connection exhaustion on small RDS
    instances like db.t4g.small (~110 max_connections).

    Args:
        db_url: SQLAlchemy database URL
        pool_size: Number of connections to maintain in the pool (default: 5)
        max_overflow: Max additional connections above pool_size (default: 10)
        pool_timeout: Seconds to wait for a connection from pool (default: 30)
        pool_recycle: Seconds before recycling a connection (default: 1800)
        pool_pre_ping: Whether to test connections before use (default: True)

    Returns:
        Shared SQLAlchemy Engine instance
    """
    global _engine

    # Fast path: engine already exists
    if _engine is not None:
        return _engine

    # Slow path: create engine with lock to prevent race conditions
    with _engine_lock:
        # Double-check after acquiring lock
        if _engine is not None:
            return _engine

        logger.info(
            f"Creating shared database engine with pool_size={pool_size}, "
            f"max_overflow={max_overflow}, pool_recycle={pool_recycle}s"
        )

        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            # Echo SQL for debugging (disabled in production)
            echo=False,
        )

        # Add event listeners for connection monitoring
        @event.listens_for(_engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log when a connection is checked out from the pool."""
            logger.debug(f"Connection checked out: {id(dbapi_conn)}")

        @event.listens_for(_engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            """Log when a connection is returned to the pool."""
            logger.debug(f"Connection checked in: {id(dbapi_conn)}")

        logger.info("Shared database engine created successfully")
        return _engine


def dispose_engine() -> None:
    """
    Dispose of the shared engine and close all connections.

    This should be called during application shutdown or when
    reconfiguring the database connection.
    """
    global _engine

    with _engine_lock:
        if _engine is not None:
            logger.info("Disposing shared database engine")
            _engine.dispose()
            _engine = None


def get_pool_status() -> dict:
    """
    Get current connection pool status for monitoring.

    Returns:
        Dictionary with pool statistics
    """
    if _engine is None:
        return {"status": "not_initialized"}

    pool = _engine.pool
    return {
        "status": "active",
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount if hasattr(pool, "invalidatedcount") else 0,
    }
