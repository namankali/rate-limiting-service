import asyncio
from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

DB_SEMAPHORE_TIMEOUT = 1.0


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    semaphore = request.app.state.db_semaphore
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=DB_SEMAPHORE_TIMEOUT)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database capacity temporarily unavailable",
        ) from exc

    try:
        session_factory = request.app.state.db_session_factory
        async with session_factory() as session:
            yield session
    finally:
        semaphore.release()
