from app.policies.policy import IdentityTypes, RateLimitAlgorithms, Resources
from app.policies.registry import PolicyRequest, Registry


def test_register_valid_policy() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True
    assert len(registry.policies) == 1


def test_register_same_configuration_twice() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    policy_data_2: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True
    assert registry.register(policy_data=policy_data_2) is True
    assert len(registry.policies) == 2


def test_register_multiple_policies() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    policy_data_2: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.TOKEN_BUCKET,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.USER,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True
    assert registry.register(policy_data=policy_data_2) is True
    assert len(registry.policies) == 2


def test_register_generates_unique_identifiers() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    policy_data_2: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.TOKEN_BUCKET,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.USER,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True
    assert registry.register(policy_data=policy_data_2) is True

    set_ = set(registry.policies.keys())

    assert len(registry.policies.keys()) == len(set_)


def test_is_policy_exists_returns_true() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True

    policy_identifiers = list(registry.policies.keys())
    policy_identifier = policy_identifiers[0]

    assert registry.is_policy_exists(policy_identifier) is True


def test_registered_policy_contains_generated_identifier() -> None:
    policy_data: PolicyRequest = PolicyRequest(
        name="login",
        algorithm=RateLimitAlgorithms.SLIDING_WINDOW_LOG,
        limit=100,
        window_seconds=10,
        identity_type=IdentityTypes.CLIENT_ID,
        resource=Resources.AI_DEVOPS,
    )
    registry = Registry()

    assert registry.register(policy_data=policy_data) is True

    policy_identifiers = list(registry.policies.keys())
    policy_identifier = policy_identifiers[0]

    assert hasattr(registry.policies[policy_identifier], "identifier")


# def
