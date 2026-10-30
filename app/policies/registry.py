from typing import Any

from pydantic import BaseModel, model_validator

from app.helpers.formatter import make_policy_identifier
from app.policies.algorithm_config import (
    FixedWindowConfig,
    SlidingWindowConfig,
    TokenBucketConfig,
)
from app.policies.policy import (
    IdentityTypes,
    Policy,
    QuotaScope,
    RateLimitAlgorithms,
    Resources,
)


class PolicyRequest(BaseModel):
    name: str
    algorithm: RateLimitAlgorithms
    algorithm_config: FixedWindowConfig | SlidingWindowConfig | TokenBucketConfig
    identity_type: IdentityTypes
    resource: Resources
    route: str = "*"
    quota_scope: QuotaScope = QuotaScope.PER_IDENTITY

    @model_validator(mode="before")
    @classmethod
    def validate_algorithm_config(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        algorithm = data.get("algorithm")
        config = data.get("algorithm_config")

        if isinstance(algorithm, str):
            try:
                algorithm = RateLimitAlgorithms(algorithm)
            except ValueError:
                return data

        config_models = {
            RateLimitAlgorithms.FIXED_WINDOW: FixedWindowConfig,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: SlidingWindowConfig,
            RateLimitAlgorithms.TOKEN_BUCKET: TokenBucketConfig,
        }

        config_model = config_models.get(algorithm)

        if config_model is not None and isinstance(config, dict):
            data = data.copy()
            data["algorithm_config"] = config_model(**config)
        return data


class Registry:
    def __init__(self) -> None:
        self.policies: dict[str, Policy] = {}

    def register(self, policy_data: PolicyRequest) -> bool:
        policy_identifier = make_policy_identifier(policy_data.resource.value)

        if policy_identifier in self.policies:
            return False
        else:
            self.policies[policy_identifier] = Policy(
                route=policy_data.route,
                identifier=policy_identifier,
                name=policy_data.name,
                algorithm=policy_data.algorithm,
                algorithm_config=policy_data.algorithm_config,
                identity_type=policy_data.identity_type,
                resource=policy_data.resource,
                quota_scope=policy_data.quota_scope,
            )
            return True

    def is_policy_exists(self, identifier: str) -> bool:
        return identifier in self.policies

    def get_policy(self, identifier: str) -> Policy:
        if identifier not in self.policies:
            raise KeyError("Identifier not present")
        else:
            return self.policies[identifier]

    def policy_selection(
        self,
        resource: Resources,
        route: str,
        identity_type: IdentityTypes,
        identity_value: str,
    ) -> Policy | None:
        self._validate_input_policy_selection(
            resource, route, identity_type, identity_value
        )
        matched_keys = self._match_keys(
            keys=list(self.policies.keys()),
            resource=resource,
            identity_type=identity_type,
        )

        if not matched_keys:
            return None
        selected_policy = self._select_policy(matched_keys=matched_keys, route=route)
        return selected_policy

    def _select_policy(self, matched_keys: list[str], route: str) -> Policy | None:
        exact_policy = []
        wildcard_policy = []
        for key in matched_keys:
            policy = self.policies[key]
            if policy.route == route:
                exact_policy.append(policy)
            elif policy.route == "*":
                wildcard_policy.append(policy)
        if len(exact_policy) == 1:
            return exact_policy[0]
        elif len(exact_policy) > 1:
            raise ValueError("Multiple exact-route policies match")
        elif len(wildcard_policy) == 1:
            return wildcard_policy[0]
        elif len(wildcard_policy) > 1:
            raise ValueError("Multiple wildcard policies match")
        else:
            return None

    def _match_keys(
        self, keys: list[str], resource: Resources, identity_type: IdentityTypes
    ) -> list[str]:
        result = []
        for key in keys:
            policy = self.policies[key]
            if resource == policy.resource and policy.identity_type == identity_type:
                result.append(key)
        return result

    def _validate_input_policy_selection(
        self,
        resource: Resources,
        route: str,
        identity_type: IdentityTypes,
        identity_value: str,
    ) -> None:
        if not isinstance(resource, Resources):
            raise ValueError("resource is invalid")
        if not route.strip():
            raise ValueError("route is invalid")
        if not isinstance(identity_type, IdentityTypes):
            raise ValueError("identity type is invalid")
        if not identity_value.strip():
            raise ValueError("identity is not valid")
