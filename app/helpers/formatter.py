from uuid import uuid4

from app.policies.policy import IdentityTypes, QuotaScope, Resources


def make_policy_identifier(resource: Resources) -> str:
    if not isinstance(resource, Resources):
        raise ValueError("Resource is invalid")

    return f"{resource}:{uuid4()}"


def make_quota_key(
    policy_identifier: str,
    identity_type: IdentityTypes,
    identity_value: str,
    quota_scope: QuotaScope,
) -> str:
    if quota_scope == QuotaScope.PER_IDENTITY:
        return f"{policy_identifier}:{identity_type.value}:{identity_value}"
    elif quota_scope == QuotaScope.SHARED:
        return f"{policy_identifier}:{quota_scope.value}"
    else:
        raise ValueError("Invalid quota scope")
