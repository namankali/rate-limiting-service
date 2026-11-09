from fastapi import APIRouter, HTTPException, Request

from app.helpers.custom_types import DataBaseSession
from app.schemas.rate_limit import RateLimitRequest, RateLimitResponse

router = APIRouter()


@router.post("/v1/check", response_model=RateLimitResponse)
async def evaluate_request(
    request: Request, payload: RateLimitRequest, session: DataBaseSession
):
    service = request.app.state.rate_limiting_service
    try:
        result = await service.evaluate_request(
            resource=payload.resource,
            route=payload.route,
            identity_type=payload.identity_type,
            identity_value=payload.identity_value,
            client_id=payload.client_id,
            session=session,
        )

        return result
    except ValueError as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail={"message": "Rate-limiting configuration error"}
        ) from e
