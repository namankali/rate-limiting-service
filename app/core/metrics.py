from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
)

RATE_LIMIT_DECISIONS_TOTAL = Counter(
    "rate_limit_decisions_total",
    "Total rate-limiting decisions",
    ["algorithm", "decision"],
)

RATE_LIMIT_ALGORITHM_TOTAL = Counter(
    "rate_limit_algorithm_total",
    "Total executions per rate-limiting algorithm",
    ["algorithm"],
)

REDIS_OPERATIONS_TOTAL = Counter(
    "redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"],
)

REDIS_OPERATION_DURATION_SECONDS = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation execution duration in seconds",
    ["operation"],
)

REDIS_ERRORS_TOTAL = Counter(
    "redis_errors_total",
    "Total number of Redis errors",
    ["operation"],
)

POSTGRES_OPERATIONS_TOTAL = Counter(
    "postgres_operations_total",
    "Total number of PostgreSQL operations",
    ["operation", "status"],
)

POSTGRES_OPERATION_DURATION_SECONDS = Histogram(
    "postgres_operation_duration_seconds",
    "PostgreSQL operation execution duration in seconds",
    ["operation"],
)

POSTGRES_ERRORS_TOTAL = Counter(
    "postgres_errors_total",
    "Total number of PostgreSQL errors",
    ["operation"],
)

POSTGRES_CONNECTIONS_IN_USE = Gauge(
    "postgres_connections_in_use",
    "Number of PostgreSQL connections currently checked out",
)

POSTGRES_CONNECTIONS_IDLE = Gauge(
    "postgres_connections_idle",
    "Number of idle connections in the SQLAlchemy connection pool",
)

POSTGRES_CONNECTIONS_CHECKED_OUT_TOTAL = Counter(
    "postgres_connections_checked_out_total",
    "Total number of PostgreSQL connection checkouts",
)

POSTGRES_CONNECTIONS_CHECKED_IN_TOTAL = Counter(
    "postgres_connections_checked_in_total",
    "Total number of PostgreSQL connection check-ins",
)

POSTGRES_CONNECTION_HOLD_DURATION_SECONDS = Histogram(
    "postgres_connection_hold_duration_seconds",
    "Time a PostgreSQL connection remains checked out",
)
