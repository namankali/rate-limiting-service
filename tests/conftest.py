import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv(override=True)


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Redis]:
    redis_url = os.getenv("TEST_REDIS_URL")

    if not redis_url:
        pytest.fail("TEST_REDIS_URL env variaable is not configured")

    client = Redis.from_url(redis_url, decode_responses=True)

    try:
        await client.ping()
        yield client
    finally:
        await client.aclose()
