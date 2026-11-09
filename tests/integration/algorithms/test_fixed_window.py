from uuid import uuid4

import pytest
from app.algorithms.fixed_window import evaluate_fixed_window
from app.helpers.redis_key_builder import make_redis_key
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_allow_request_limit(redis_client: Redis) -> None:
    client_id = uuid4()

    key = make_redis_key(
        quota_key="user:naman",
        client_id=client_id,
        resource="ai-devops",
        algorithm="fixed-window",
        environment="test",
        policy_identifier="test-fixed-window",
    )

    try:
        result = await evaluate_fixed_window(
            redis_client=redis_client, key=key, limit=2, window_seconds=60
        )

        result_2 = await evaluate_fixed_window(
            redis_client=redis_client, key=key, limit=2, window_seconds=60
        )

        assert result == (True, 1, 1, 0)
        assert result_2 == (True, 2, 0, 0)
    finally:
        await redis_client.delete(key)


# @pytest.mark.asyncio
# async def test_rejects_requests_when_limit_is_reached() -> None:
#     client_id = uuid4()

#     key = make_redis_key(
#         quota_key="user:naman",
#         client_id=client_id,
#         resource="ai-devops",
#         algorithm="fixed-window",
#         environment="test",
#         policy_identifier="test-fixed-window",
#     )

#     try:
#         result = await evaluate_fixed_window()
