import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Load .env from the project root
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
    url,
    echo=False,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
