import math

from redis.asyncio import Redis

FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]

local limit = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local grace_ms = tonumber(ARGV[3])

-- Get Redis server time in milliseconds
local time = redis.call("TIME")

local now_ms = tonumber(time[1]) * 1000 + math.floor(tonumber(time[2]) / 1000)

-- Read existing window state
local count = tonumber(redis.call("HGET", key, "count"))

local window_start = tonumber(
    redis.call("HGET", key, "window_started_at")
)

-- Initialize or reset expired window
if not count or not window_start
    or now_ms - window_start >= window_ms then

    count = 0
    window_start = now_ms
end

local allowed = 0

-- Apply rate limit
if count < limit then
    count = count + 1
    allowed = 1
end

redis.call(
    "HSET",
    key,
    "count", count,
    "window_started_at", window_start
)

-- Calculate response state
local elapsed_ms = now_ms - window_start
local retry_after_ms = 0

if allowed == 0 then
    retry_after_ms = math.max(0, window_ms - elapsed_ms)
end

local remaining = math.max(0, limit - count)

local ttl_ms = math.max(
    1,
    window_ms - elapsed_ms + grace_ms
)

redis.call("PEXPIRE", key, ttl_ms)

return {
    allowed,
    count,
    remaining,
    retry_after_ms
}
"""


async def evaluate_fixed_window(
    redis_client: Redis,
    key: str,
    limit: int,
    window_seconds: float,
    grace_ms: int = 5000,
) -> tuple[bool, int, int, int]:
    if limit <= 0:
        raise ValueError("Limit must be positive")

    if not math.isfinite(window_seconds) or window_seconds <= 0:
        raise ValueError("Window duration must be finite and positive")

    if type(grace_ms) is not int or grace_ms < 0:
        raise ValueError("Grace period must be a non-negative integer")

    window_ms = math.ceil(window_seconds * 1000)

    result = await redis_client.eval(
        FIXED_WINDOW_SCRIPT,
        1,
        key,
        limit,
        window_ms,
        grace_ms,
    )

    return (
        bool(result[0]),
        int(result[1]),
        int(result[2]),
        int(result[3]),
    )


SLIDING_WINDOW_SCRIPT = """
    local key = KEYS[1]
    
    local limit = tonumber(ARGV[1])
    local window_ms = tonumber(ARGV[2])
    local grace_ms = tonumber(ARGV[3])
    local request_id = ARGV[4]
    
    local time = redis.call("TIME")
    local now_ms = tonumber(time[1]) * 1000 + math.floor(tonumber(time[2]) / 1000)
    
    -- Sliding window boundry
    local window_start = now_ms - window_ms
    
    -- Remove expired requests
    redis.call(
        "ZREMRANGEBYSCORE",
        key,
        "-inf",
        window_start
    )
    
    -- Count request inside active window
    local count = redis.call("ZCARD", key)
    
    local allowed = 0
    local retry_after_ms = 0
    
    if count < limit then
        redis.call("ZADD", key, now_ms, request_id)
        
        allowed = 1
        count = count + 1
    else
        -- calculate retry time using oldest active request
        local oldest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
        
        retry_after_ms = math.max(0, tonumber(oldest[2]) + window_ms - now_ms)
    end
    
    
    local remaining = math.max(0, limit - count)
    
    redis.call("PEXPIRE", key, window_ms + grace_ms)

    return {
        allowed,
        count,
        remaining,
        retry_after_ms
    }
"""


async def evaluate_sliding_window(
    redis_client: Redis,
    key: str,
    limit: int,
    window_seconds: float,
    request_id: str,
    grace_ms: int = 5000,
) -> tuple[bool, int, int, int]:
    if limit <= 0:
        raise ValueError("Limit must be positive")

    if not math.isfinite(window_seconds) or window_seconds <= 0:
        raise ValueError("Window duration must be finite and positive")

    if not isinstance(grace_ms, int) or grace_ms < 0:
        raise ValueError("Grace period must be a non-negative integer")

    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("Request ID must be a non-empty string")

    window_ms = math.ceil(window_seconds * 1000)

    result = await redis_client.eval(
        SLIDING_WINDOW_SCRIPT,
        1,
        key,
        limit,
        window_ms,
        grace_ms,
        request_id,
    )

    return (
        bool(result[0]),
        int(result[1]),
        int(result[2]),
        int(result[3]),
    )


TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local grace_ms = tonumber(ARGV[3])

-- Get Redis server time in milliseconds
local time = redis.call("TIME")

local now_ms = tonumber(time[1]) * 1000
    + math.floor(tonumber(time[2]) / 1000)

-- Read existing bucket state
local tokens = tonumber(redis.call("HGET", key, "tokens"))
local updated_at = tonumber(redis.call("HGET", key, "updated_at"))

-- Initialize bucket if it does not exist
if not tokens or not updated_at then
    tokens = capacity
    updated_at = now_ms
end

-- Calculate elapsed time
local elapsed_seconds = math.max(0, now_ms - updated_at) / 1000

-- Refill tokens
tokens = math.min(
    capacity,
    tokens + (elapsed_seconds * refill_rate)
)

-- Update timestamp
updated_at = now_ms

local allowed = 0
local retry_after_ms = 0

-- Consume one token if available
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
else
    -- Calculate time required to obtain one token
    retry_after_ms = math.ceil(
        ((1 - tokens) / refill_rate) * 1000
    )
end

-- Calculate remaining whole tokens
local remaining = math.floor(tokens)

-- Persist bucket state
redis.call(
    "HSET",
    key,
    "tokens", tokens,
    "updated_at", updated_at
)

-- Calculate TTL based on time needed to refill the bucket
local ttl_ms = math.ceil(
    (capacity / refill_rate) * 1000
) + grace_ms

redis.call("PEXPIRE", key, math.max(1, ttl_ms))

return {
    allowed,
    tokens,
    remaining,
    retry_after_ms
}
"""


async def evaluate_token_bucket(
    redis_client: Redis,
    key: str,
    capacity: int,
    refill_rate: float,
    grace_ms: int = 5000,
) -> tuple[bool, float, int, int]:
    if capacity <= 0:
        raise ValueError("Capacity must be positive")

    if not math.isfinite(refill_rate) or refill_rate <= 0:
        raise ValueError("Refill rate must be finite and positive")

    if not isinstance(grace_ms, int) or grace_ms < 0:
        raise ValueError("Grace period must be a non-negative integer")

    result = await redis_client.eval(
        TOKEN_BUCKET_SCRIPT,
        1,
        key,
        capacity,
        refill_rate,
        grace_ms,
    )

    return (
        bool(result[0]),
        float(result[1]),
        int(result[2]),
        int(result[3]),
    )


LEAKY_BUCKET_SCRIPT = """
local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local leak_rate = tonumber(ARGV[2])
local grace_ms = tonumber(ARGV[3])

-- Get Redis server time in milliseconds
local time = redis.call("TIME")

local now_ms = tonumber(time[1]) * 1000
    + math.floor(tonumber(time[2]) / 1000)

-- Read existing bucket state
local water_level = tonumber(
    redis.call("HGET", key, "water_level")
)

local updated_at = tonumber(
    redis.call("HGET", key, "updated_at")
)

if not water_level or not updated_at then
    water_level = 0
    updated_at = now_ms
end

-- Calculate elapsed time
local elapsed_seconds = math.max(
    0,
    now_ms - updated_at
) / 1000

-- Leak water based on elapsed time
water_level = math.max(
    0,
    water_level - (elapsed_seconds * leak_rate)
)

-- Update timestamp
updated_at = now_ms

local allowed = 0
local retry_after_ms = 0

-- Accept request if capacity is available
if water_level + 1 <= capacity then
    water_level = water_level + 1
    allowed = 1
else
    -- Calculate time until one unit of capacity becomes available
    retry_after_ms = math.ceil(
        ((water_level - (capacity - 1)) / leak_rate) * 1000
    )
end

-- Calculate remaining whole capacity
local remaining = math.floor(
    math.max(0, capacity - water_level)
)

-- Persist bucket state
redis.call(
    "HSET",
    key,
    "water_level", water_level,
    "updated_at", updated_at
)

-- Set TTL based on the maximum time required to empty the bucket
local ttl_ms = math.ceil(
    (capacity / leak_rate) * 1000
) + grace_ms

redis.call("PEXPIRE", key, math.max(1, ttl_ms))

return {
    allowed,
    water_level,
    remaining,
    retry_after_ms
}
"""


async def evaluate_leaky_bucket(
    redis_client: Redis,
    key: str,
    capacity: int,
    leak_rate: float,
    grace_ms: int = 5000,
) -> tuple[bool, float, int, int]:
    if capacity <= 0:
        raise ValueError("Capacity must be positive")

    if not math.isfinite(leak_rate) or leak_rate <= 0:
        raise ValueError("Leak rate must be finite and positive")

    if not isinstance(grace_ms, int) or grace_ms < 0:
        raise ValueError("Grace period must be a non-negative integer")

    result = await redis_client.eval(
        LEAKY_BUCKET_SCRIPT,
        1,
        key,
        capacity,
        leak_rate,
        grace_ms,
    )

    return (
        bool(result[0]),
        float(result[1]),
        int(result[2]),
        int(result[3]),
    )
