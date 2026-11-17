from dataclasses import dataclass
from enum import Enum

from app.policies.algorithm_config import (
    FixedWindowConfig,
    LeakyBucketConfig,
    SlidingWindowConfig,
    TokenBucketConfig,
)


class RateLimitAlgorithms(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_LOG = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class Resources(Enum):
    AI_DEVOPS = "ai-devops"
    CHAT = "chat"
    AUTHENTICATION = "authentication"
    METRICS = "metrics"
    KUBERNETES = "kubernetes"
    GITHUB_INTEGRATION = "github-integration"


class IdentityTypes(Enum):
    USER = "user"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    CLIENT_ID = "client_id"


class QuotaScope(Enum):
    SHARED = "shared"
    PER_IDENTITY = "per_identity"


@dataclass
class Policy:
    identifier: str
    name: str
    algorithm: RateLimitAlgorithms
    algorithm_config: (
        FixedWindowConfig | SlidingWindowConfig | TokenBucketConfig | LeakyBucketConfig
    )
    identity_type: IdentityTypes
    resource: Resources
    route: str
    method: str
    quota_scope: QuotaScope = QuotaScope.PER_IDENTITY

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Identifier is required")
        if not self.name.strip():
            raise ValueError("Name is required")
        if not isinstance(self.algorithm, RateLimitAlgorithms):
            raise ValueError("Invalid algorithm")
        if not isinstance(self.identity_type, IdentityTypes):
            raise ValueError("Invalid identity type")
        if not isinstance(self.resource, Resources):
            raise ValueError("Invalid Resource")
        if not self.route.strip():
            raise ValueError("invalid route")
        if not isinstance(self.quota_scope, QuotaScope):
            raise ValueError("Invalid quota scope")

        expected_configs = {
            RateLimitAlgorithms.FIXED_WINDOW: FixedWindowConfig,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: SlidingWindowConfig,
            RateLimitAlgorithms.TOKEN_BUCKET: TokenBucketConfig,
            RateLimitAlgorithms.LEAKY_BUCKET: LeakyBucketConfig,
        }

        expected_config = expected_configs[self.algorithm]

        if not isinstance(self.algorithm_config, expected_config):
            raise ValueError(
                f"{self.algorithm_config} requires"
                f"{expected_config.__name__}. "
                f"got {type(self.algorithm_config).__name__}"
            )
