from uuid import UUID

from app.services.service_permissions import ServicePermissionsService
from sqlalchemy.ext.asyncio import AsyncSession


class AuthorizationService:
    def __init__(self, service_permission_service: ServicePermissionsService):
        self.service_permission_service = service_permission_service

    async def has_permission(self, service_identity_id: UUID, session: AsyncSession):
        is_allowed = await self.service_permission_service.check_permission(
            session=session,
            service_identity_id=service_identity_id,
            permission_name="ratelimit:check",
        )

        return is_allowed
