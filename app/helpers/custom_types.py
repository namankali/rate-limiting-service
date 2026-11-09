from typing import Annotated

from app.db.postgres.dependencies import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DataBaseSession = Annotated[AsyncSession, Depends(get_db)]
