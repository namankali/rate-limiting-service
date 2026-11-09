from uuid import UUID


def make_redis_key(
    environment: str,
    resource: str,
    policy_identifier: str,
    quota_key: str,
    algorithm: str,
    client_id: UUID,
) -> str:
    values = {
        "environment": environment,
        "resource": resource,
        "policy_identifier": policy_identifier,
        "quota_key": quota_key,
        "algorithm": algorithm,
    }

    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

        if ":" in value and name != "quota_key":
            raise ValueError(f"{name} must not contain ':'")

    return (
        f"rate-limiter:{environment}:{client_id}:{resource}:"
        f"{policy_identifier}:{quota_key}:{algorithm}:state"
    )
