from app.policies.policy import IdentityTypes, Resources


class RateLimitingService:
    def __init__(
        self, fixed_window_counter, sliding_window_counter, token_bucket, registry
    ):
        self.fixed_window_counter = fixed_window_counter
        self.sliding_window_counter = sliding_window_counter
        self.token_bucket = token_bucket
        self.registry = registry

    def evaluate_request(
        self,
        resource: Resources,
        route: str,
        identity_type: IdentityTypes,
        identity_value: str,
    ):
        get_policy = self.registry.policy_selection(
            resource=resource,
            route=route,
            identity_type=identity_type,
            identity_value=identity_value,
        )

        if get_policy is None:
            return {"allowed": False, "policy": None}

        # quota_key = make_quota_key(
        #     policy_identifier=get_policy.identifier,
        #     identity_value=identity_value,
        #     identity_type=get_policy.identity_type,
        #     quota_scope=get_policy.quota_scope,
        # )
