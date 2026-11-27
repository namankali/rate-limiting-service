from typing import Annotated

from app.db.postgres.models.users import UserRole, Users
from app.dependencies.user_authentication import AuthenticatedUser
from fastapi import Depends, HTTPException


async def require_admin(
    user: AuthenticatedUser,
) -> AuthenticatedUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrator permission is required",
        )

    return user


AdminUser = Annotated[
    Users,
    Depends(require_admin),
]
