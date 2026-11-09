from hashlib import sha256
from uuid import uuid4

from app.policies.policy import IdentityTypes, QuotaScope, Resources


def make_policy_identifier(resource: Resources) -> str:
    if not isinstance(resource, Resources):
        raise ValueError("Resource is invalid")

    return f"{resource.value}:{uuid4()}"


def make_quota_key(
    identity_type: IdentityTypes,
    identity_value: str,
    quota_scope: QuotaScope,
) -> str:
    if not isinstance(quota_scope, QuotaScope):
        raise ValueError("Invalid quota scope")

    if quota_scope == QuotaScope.PER_IDENTITY:
        if not isinstance(identity_type, IdentityTypes):
            raise ValueError("Invalid identity type")

        if not isinstance(identity_value, str) or not identity_value.strip():
            raise ValueError("Identity value must be a non-empty string")

        identity_hash = sha256(identity_value.encode("utf-8")).hexdigest()

        return f"per-identity:{identity_type.value}:{identity_hash}"

    return "shared:shared"
