from chatbet_base_models.flow_rules.defaults import DEFAULT_FLOW_POLICY, FLOW_CATALOG
from chatbet_base_models.flow_rules.validation import (
    FlowConfig,
    required_copy,
    validate_facts,
    validate_policy,
)

SEED_BINDINGS = {"identify": "identify.by_phone", "authenticate": "auth.otp.platform"}


def test_the_shipped_catalog_knows_the_betting_steps() -> None:
    assert {"understand", "pick_market", "collect_amount", "confirm", "place_bet"} <= set(
        FLOW_CATALOG.steps
    )
    assert {"identify", "authenticate"} == set(FLOW_CATALOG.capabilities)
    assert "auth.otp.platform" in FLOW_CATALOG.strategies


def test_the_shipped_policy_keeps_what_the_code_enforced() -> None:
    assert DEFAULT_FLOW_POLICY.required_steps["bet"] == ("authenticate", "confirm")
    assert DEFAULT_FLOW_POLICY.required_steps["balance"] == ("authenticate",)
    assert DEFAULT_FLOW_POLICY.allowed_strategies == {}


def test_the_code_seed_flows_are_a_valid_configuration_in_both_layers() -> None:
    """If this fails, a client created from the defaults could not be saved."""
    config = FlowConfig(flows=DEFAULT_FLOW_POLICY.default_flows, bindings=SEED_BINDINGS)

    assert validate_facts(config, FLOW_CATALOG) == []
    assert validate_policy(config, DEFAULT_FLOW_POLICY) == []


def test_the_seed_flows_ask_for_some_copy() -> None:
    config = FlowConfig(flows=DEFAULT_FLOW_POLICY.default_flows, bindings=SEED_BINDINGS)

    assert "bet.placed" in required_copy(config, FLOW_CATALOG).required


def test_the_fingerprint_is_available_for_consumers() -> None:
    assert len(FLOW_CATALOG.fingerprint) == 12
