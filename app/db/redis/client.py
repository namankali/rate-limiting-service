import redis.asyncio as redis
from redis.asyncio import Redis


def create_redis_client(
    host: str,
    port: int,
    password: str | None,
    db: int = 0,
) -> Redis:
    return redis.Redis(
        host=host,
        port=port,
        password=password,
        db=db,
        decode_responses=True,
        max_connections=50,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
    )
