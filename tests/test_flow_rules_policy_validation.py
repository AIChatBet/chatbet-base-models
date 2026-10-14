from chatbet_base_models.flow_rules.policy import FlowPolicy
from chatbet_base_models.flow_rules.validation import (
    ConfigError,
    FlowConfig,
    validate_policy,
)
from tests.flow_rules_world import valid_config

REQUIRE_CONFIRM = FlowPolicy(required_steps={"bet": ("confirm",)})


def test_a_config_that_keeps_the_required_step_passes() -> None:
    assert validate_policy(valid_config(), REQUIRE_CONFIRM) == []


def test_removing_a_required_step_is_rejected() -> None:
    """Removing the confirmation screen means betting without confirming."""
    config = FlowConfig(
        flows={"bet": ("understand", "authenticate", "pick_market", "collect_amount", "place_bet")},
        bindings={"authenticate": "auth.otp"},
    )

    assert validate_policy(config, REQUIRE_CONFIRM) == [
        ConfigError(
            field="flows.bet",
            message="'confirm' cannot be removed from this flow (required by policy).",
        )
    ]


def test_a_flow_the_policy_never_heard_of_is_not_an_error() -> None:
    """A client's own flow has no policy entry; that must neither crash nor complain."""
    config = FlowConfig(flows={"my_custom_flow": ("understand",)})

    assert validate_policy(config, REQUIRE_CONFIRM) == []


def test_a_required_flow_missing_from_the_config_is_not_reported() -> None:
    """Only flows the client actually stores are checked, as the channel does today."""
    assert validate_policy(FlowConfig(), REQUIRE_CONFIRM) == []


def test_a_policy_requiring_an_unknown_step_makes_the_flow_report_it_missing() -> None:
    """Unsatisfiable, but explicit: no crash, and the message names the step."""
    policy = FlowPolicy(required_steps={"bet": ("ghost_step",)})
    errors = validate_policy(valid_config(), policy)

    assert [e.message for e in errors] == [
        "'ghost_step' cannot be removed from this flow (required by policy)."
    ]


def test_a_strategy_outside_the_allowed_list_is_rejected() -> None:
    policy = FlowPolicy(allowed_strategies={"authenticate": ("auth.password_form",)})
    errors = validate_policy(valid_config(), policy)

    assert errors == [
        ConfigError(
            field="bindings.authenticate",
            message="'auth.otp' is not allowed for 'authenticate' by policy.",
        )
    ]


def test_a_capability_without_an_entry_allows_every_strategy() -> None:
    policy = FlowPolicy(allowed_strategies={"identify": ("identify.by_phone",)})

    assert validate_policy(valid_config(), policy) == []


def test_an_explicit_empty_list_allows_no_strategy() -> None:
    policy = FlowPolicy(allowed_strategies={"authenticate": ()})

    assert [e.field for e in validate_policy(valid_config(), policy)] == ["bindings.authenticate"]


def test_an_empty_policy_accepts_any_config() -> None:
    assert validate_policy(valid_config(), FlowPolicy()) == []
