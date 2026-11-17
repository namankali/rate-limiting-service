import base64
import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.algorithms.fixed_window import FixedWindowCounter
from app.algorithms.leaky_bucket import LeakyBucket
from app.algorithms.sliding_window_log import SlidingWindowLog
from app.algorithms.token_bucket import TokenBucket
from app.core.config import Settings
from app.data_access.client_data_access import ClientRepository
from app.data_access.permissions_data_access import PermissionsRepository
from app.data_access.policy_data_access import PolicyRepository
from app.data_access.service_credentials_data_access import ServiceCredentialsRepository
from app.data_access.service_identity_data_access import ServiceIdentityRepository
from app.data_access.service_permissions_data_access import ServicePermissionsRepository
from app.db.postgres.client import AsyncSessionFactory, engine
from app.db.redis.client import create_redis_client
from app.exceptions.base import ApplicationError
from app.routes import (
    client,
    health,
    permissions,
    policy,
    rate_limit,
    service_identity,
    service_permissions,
)
from app.services.authentication import Authentication
from app.services.authorization import AuthorizationService
from app.services.permissions_service import PermissionsService
from app.services.policy_service import PolicyService
from app.services.rate_limiting_service import RateLimitingService
from app.services.service_credential_service import ServiceCredtialsService
from app.services.service_identity_service import ServiceIdentityService
from app.services.service_permissions import ServicePermissionsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = Settings()
    redis_client = create_redis_client(
        host=app.state.settings.redis_host,
        port=app.state.settings.redis_port,
        password=app.state.settings.redis_password,
    )

    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")

        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        logger.info("PostgreSQL connected successfully")

        app.state.redis = redis_client
        app.state.engine = engine
        app.state.db_session_factory = AsyncSessionFactory
        app.state.client_repository = ClientRepository()
        app.state.policy_repository = PolicyRepository()
        app.state.service_identity_repository = ServiceIdentityRepository()
        app.state.service_credentials_repository = ServiceCredentialsRepository()
        app.state.permissions_repository = PermissionsRepository()
        app.state.service_permissions_repository = ServicePermissionsRepository()

        app.state.authentication = Authentication(
            service_credential_data_access=app.state.service_credentials_repository,
            hmac_keys=app.state.settings.decode_hmac_keys,
        )
        app.state.service_permissions_service = ServicePermissionsService(
            service_permissions_data_access=app.state.service_permissions_repository,
            service_identity_data_access=app.state.service_identity_repository,
            permissions_data_access=app.state.permissions_repository,
        )

        app.state.authorization = AuthorizationService(
            service_permission_service=app.state.service_permissions_service
        )
        app.state.permissions_service = PermissionsService(
            permission_data_access=app.state.permissions_repository
        )
        app.state.service_credentials_service = ServiceCredtialsService(
            service_credential_data_access=app.state.service_credentials_repository,
            service_identity_data_access=app.state.service_identity_repository,
            hmac_key_version=app.state.settings.hmac_active_key_version,
            hmac_keys=app.state.settings.decode_hmac_keys,
        )
        app.state.service_identity_service = ServiceIdentityService(
            client=app.state.client_repository,
            service_identity=app.state.service_identity_repository,
        )
        app.state.policy_service = PolicyService(
            policy=app.state.policy_repository, client=app.state.client_repository
        )
        app.state.rate_limiting_service = RateLimitingService(
            leaky_bucket=LeakyBucket(redis_client=redis_client),
            token_bucket=TokenBucket(redis_client=redis_client),
            fixed_window_counter=FixedWindowCounter(redis_client=redis_client),
            sliding_window_counter=SlidingWindowLog(redis_client=redis_client),
            policy_service=app.state.policy_service,
            environment=app.state.settings.environment,
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


@app.exception_handler(ApplicationError)
async def application_exception_handler(request: Request, exec: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=exec.status_code,
        content={"error_code": exec.error_code, "message": exec.message},
    )


app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(permissions.router)
app.include_router(service_permissions.router)
app.include_router(rate_limit.router, prefix="/rate", tags=["Rate Limit"])
app.include_router(client.router, prefix="/client", tags=["Clients"])
app.include_router(service_identity.router, prefix="/service-identity", tags=["Service Identity"])
app.include_router(
    policy.router,
    prefix="/policies",
    tags=["Policies"],
)


def temp_secret() -> None:
    secret_bytes = secrets.token_bytes(32)
    secret_bytes_str = base64.urlsafe_b64encode(secret_bytes).decode("ascii")
    print(secret_bytes_str)


# temp_secret()
