import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import ConnectionPoolEntry, PoolProxiedConnection

from app.core.metrics import (
    POSTGRES_CONNECTION_HOLD_DURATION_SECONDS,
    POSTGRES_CONNECTIONS_CHECKED_IN_TOTAL,
    POSTGRES_CONNECTIONS_CHECKED_OUT_TOTAL,
    POSTGRES_CONNECTIONS_IN_USE,
)

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

# Read Neon connection string
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is not configured")

# Parse the URL and configure it for asyncpg
url = make_url(database_url)

query_params = dict(url.query)

# asyncpg uses ssl, not sslmode
if "sslmode" in query_params:
    sslmode = query_params.pop("sslmode")
    query_params["ssl"] = "require" if sslmode == "require" else sslmode

# Not needed by asyncpg
query_params.pop("channel_binding", None)

url = url.set(
    drivername="postgresql+asyncpg",
    query=query_params,
)

# Create asynchronous engine
engine = create_async_engine(
    url, echo=False, pool_pre_ping=True, pool_size=15, max_overflow=5, pool_timeout=5
)

logger = logging.getLogger(__name__)


@event.listens_for(engine.sync_engine, "checkout")
def on_connection_checkout(
    dbapi_connection: PoolProxiedConnection,
    connection_record: ConnectionPoolEntry,
    connection_proxy: Connection,
) -> None:
    connection_record.info["checkout_time"] = time.perf_counter()

    POSTGRES_CONNECTIONS_IN_USE.inc()
    POSTGRES_CONNECTIONS_CHECKED_OUT_TOTAL.inc()


@event.listens_for(engine.sync_engine, "checkin")
def on_connection_checkin(
    dbapi_connection: PoolProxiedConnection,
    connection_record: ConnectionPoolEntry,
) -> None:
    checkout_time = connection_record.info.pop("checkout_time", None)

    if checkout_time is not None:
        duration = time.perf_counter() - checkout_time

        POSTGRES_CONNECTION_HOLD_DURATION_SECONDS.observe(duration)

        logger.info(
            "Database connection checked in | connection_hold_duration=%.4f seconds",
            duration,
        )

        POSTGRES_CONNECTIONS_CHECKED_IN_TOTAL.inc()
        POSTGRES_CONNECTIONS_IN_USE.dec()


# Create session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
