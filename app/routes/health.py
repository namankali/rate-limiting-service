from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/live")
async def liveliness() -> dict[str, str]:
    return {"status": "alive", "message": "Application process is running"}


@router.get("/ready")
async def readiness() -> dict[str, str]:
    # will add external dependencies
    is_ready = True
    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "message": "Application is not ready to accept request",
            },
        )
    return {
        "status": "ready",
        "message": "Application is ready to accept requests",
    }
