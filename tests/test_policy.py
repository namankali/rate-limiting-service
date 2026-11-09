import pytest
from app.policies.policy import IdentityTypes, Policy, RateLimitAlgorithms, Resources


def test_valid_policy() -> None:
    policy = Policy(
        identifier=f"{Resources.AI_DEVOPS}:123",
        name="login",
        identity_type=IdentityTypes.USER,
        window_seconds=100.0,
        algorithm=RateLimitAlgorithms.FIXED_WINDOW,
        limit=100,
        resource=Resources.AI_DEVOPS,
    )

    assert policy.name == "login"
    assert policy.identity_type == IdentityTypes.USER
    assert policy.window_seconds == 100.0
    assert policy.algorithm == RateLimitAlgorithms.FIXED_WINDOW
    assert policy.limit == 100
    assert policy.resource == Resources.AI_DEVOPS


def test_invalid_policy_name() -> None:
    with pytest.raises(ValueError, match="Name is required"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "",
            RateLimitAlgorithms.FIXED_WINDOW,
            10,
            60.0,
            IdentityTypes.USER,
            Resources.AI_DEVOPS,
        )


def test_invalid_algorithm() -> None:
    with pytest.raises(ValueError, match="Invalid algorithm"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "login",
            "leaky_bucket",  # type: ignore[arg-type]
            10,
            60.0,
            IdentityTypes.USER,
            Resources.AI_DEVOPS,
        )


def test_invalid_limit() -> None:
    with pytest.raises(ValueError, match="Limit should be positive"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "login",
            RateLimitAlgorithms.FIXED_WINDOW,
            0,
            60.0,
            IdentityTypes.USER,
            Resources.AI_DEVOPS,
        )


def test_invalid_window_seconds() -> None:
    with pytest.raises(ValueError, match="window seconds should be positive"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "login",
            RateLimitAlgorithms.FIXED_WINDOW,
            10,
            0.0,
            IdentityTypes.USER,
            Resources.AI_DEVOPS,
        )


def test_invalid_identity_type() -> None:
    with pytest.raises(ValueError, match="Invalid identity type"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "login",
            RateLimitAlgorithms.FIXED_WINDOW,
            10,
            60.0,
            "",  # type: ignore[arg-type]
            Resources.AI_DEVOPS,
        )


def test_invalid_resource() -> None:
    with pytest.raises(ValueError, match="Invalid Resource"):
        Policy(
            f"{Resources.AI_DEVOPS}:123",
            "login",
            RateLimitAlgorithms.FIXED_WINDOW,
            10,
            60.0,
            IdentityTypes.USER,
            "dcms",  # type: ignore[arg-type]
        )


def test_valid_policy_with_fractional_window() -> None:
    policy = Policy(
        identity_type=IdentityTypes.API_KEY,
        identifier=f"{Resources.AI_DEVOPS}:123",
        name="login",
        algorithm=RateLimitAlgorithms.FIXED_WINDOW,
        limit=100,
        window_seconds=0.15,
        resource=Resources.AI_DEVOPS,
    )

    assert policy.identifier == f"{Resources.AI_DEVOPS}:123"


def test_negative_limit() -> None:
    with pytest.raises(ValueError, match="Limit should be positive"):
        Policy(
            identity_type=IdentityTypes.API_KEY,
            identifier=f"{Resources.AI_DEVOPS}:123",
            name="login",
            algorithm=RateLimitAlgorithms.FIXED_WINDOW,
            limit=-100,
            window_seconds=0.15,
            resource=Resources.AI_DEVOPS,
        )


def test_negative_window_seconds() -> None:
    with pytest.raises(ValueError, match="window seconds should be positive"):
        Policy(
            identity_type=IdentityTypes.API_KEY,
            identifier=f"{Resources.AI_DEVOPS}:123",
            name="login",
            algorithm=RateLimitAlgorithms.FIXED_WINDOW,
            limit=100,
            window_seconds=-0.15,
            resource=Resources.AI_DEVOPS,
        )


def test_window_seconds_infinity() -> None:
    with pytest.raises(ValueError, match="window seconds should be positive"):
        Policy(
            identity_type=IdentityTypes.API_KEY,
            identifier=f"{Resources.AI_DEVOPS}:123",
            name="login",
            algorithm=RateLimitAlgorithms.FIXED_WINDOW,
            limit=100,
            window_seconds=float("inf"),
            resource=Resources.AI_DEVOPS,
        )
