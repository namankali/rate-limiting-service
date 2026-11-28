import time

from app.core.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
)
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            return response

        finally:
            duration = time.perf_counter() - start_time

            route = request.scope.get("route")
            endpoint = getattr(route, "path", "unmatched")

            status_code = response.status_code if "response" in locals() else 500

            if endpoint != "/metrics":
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=str(status_code),
                ).inc()

                HTTP_REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(duration)
