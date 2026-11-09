import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import text

from app.algorithms.fixed_window import FixedWindowCounter
from app.algorithms.leaky_bucket import LeakyBucket
from app.algorithms.sliding_window_log import SlidingWindowLog
from app.algorithms.token_bucket import TokenBucket
from app.data_access.client_data_access import ClientRepository
from app.data_access.policy_data_access import PolicyRepository
from app.db.postgres.client import AsyncSessionFactory, engine
from app.db.redis.client import create_redis_client
from app.routes import client, health, policy, rate_limit
from app.services.policy_service import PolicyService
from app.services.rate_limiting_service import RateLimitingService

load_dotenv(override=True)

redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_password = os.getenv("REDIS_PASSWORD")
env = os.getenv("ENV")


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = create_redis_client(
        host=redis_host,
        port=redis_port,
        password=redis_password,
    )

    try:
        await redis_client.ping()
        print("Redis connected successfully")

        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        print("PostgreSQL connected successfully")

        app.state.redis = redis_client
        app.state.engine = engine
        app.state.db_session_factory = AsyncSessionFactory
        app.state.client_repository = ClientRepository()
        app.state.policy_repository = PolicyRepository()

        app.state.rate_limiting_service = RateLimitingService(
            leaky_bucket=LeakyBucket(redis_client=redis_client),
            token_bucket=TokenBucket(redis_client=redis_client),
            fixed_window_counter=FixedWindowCounter(redis_client=redis_client),
            sliding_window_counter=SlidingWindowLog(redis_client=redis_client),
            policy_service=PolicyService(
                policy=app.state.policy_repository, client=app.state.client_repository
            ),
            environment=env,
        )

        yield

    finally:
        await redis_client.aclose()
        await engine.dispose()
        print("Database and Redis connections closed")


app = FastAPI(
    title="Rate Limiting Microservice",
    version="1.0.0",
    description="Applies rate limiting for different applications",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(rate_limit.router, prefix="/rate", tags=["Rate Limit"])
app.include_router(client.router, prefix="/client", tags=["Clients"])
app.include_router(
    policy.router,
    prefix="/policies",
    tags=["Policies"],
)
