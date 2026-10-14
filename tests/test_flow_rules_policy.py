import pytest
from pydantic import ValidationError

from chatbet_base_models.flow_rules.policy import FlowPolicy


def test_an_empty_policy_restricts_nothing() -> None:
    policy = FlowPolicy()

    assert policy.version == 1
    assert policy.required_steps == {}
    assert policy.allowed_strategies == {}
    assert policy.default_flows == {}
    assert policy.default_bindings == {}


def test_a_policy_round_trips_through_plain_data() -> None:
    policy = FlowPolicy(
        version=3,
        required_steps={"bet": ("confirm",)},
        allowed_strategies={"authenticate": ("auth.otp.platform",)},
        default_flows={"bet": ("understand", "confirm")},
        default_bindings={"authenticate": "auth.otp.platform"},
    )

    assert FlowPolicy.model_validate(policy.model_dump(mode="json")) == policy


def test_the_version_starts_at_one() -> None:
    with pytest.raises(ValidationError):
        FlowPolicy(version=0)


def test_unknown_keys_are_rejected() -> None:
    with pytest.raises(ValidationError):
        FlowPolicy(omittable=False)  # type: ignore[call-arg]


def test_a_policy_is_frozen() -> None:
    policy = FlowPolicy()
    with pytest.raises(ValidationError):
        policy.version = 2  # type: ignore[misc]
