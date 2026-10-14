import pytest

from chatbet_base_models.flow_rules.validation import (
    ConfigError,
    FlowConfig,
    required_copy,
    validate_facts,
)
from tests.flow_rules_world import valid_config, world_catalog


@pytest.fixture
def catalog():
    return world_catalog()


# --- the happy path ---------------------------------------------------------


def test_a_well_formed_configuration_is_accepted(catalog) -> None:
    assert validate_facts(valid_config(), catalog) == []


def test_an_empty_configuration_is_accepted(catalog) -> None:
    assert validate_facts(FlowConfig(), catalog) == []


# --- names ------------------------------------------------------------------


def test_an_unknown_name_is_rejected(catalog) -> None:
    """The `chatbet_version` case: a value that saves and does nothing."""
    config = FlowConfig(flows={"bet": ("understand", "chatbet_version", "confirm")})
    errors = validate_facts(config, catalog)

    assert any("chatbet_version" in str(e) for e in errors)
    assert any("not a registered step or capability" in e.message for e in errors)
    assert any(e.field == "flows.bet[1]" for e in errors)


# --- ordering ---------------------------------------------------------------


def test_amount_first_is_a_valid_order(catalog) -> None:
    config = FlowConfig(
        flows={
            "bet": (
                "understand",
                "authenticate",
                "collect_amount",
                "pick_market",
                "confirm",
                "place_bet",
            )
        },
        bindings={"authenticate": "auth.otp"},
    )
    assert validate_facts(config, catalog) == []


def test_an_impossible_order_is_rejected(catalog) -> None:
    config = FlowConfig(
        flows={
            "bet": (
                "understand",
                "authenticate",
                "place_bet",  # before the amount exists
                "collect_amount",
                "confirm",
            )
        },
        bindings={"authenticate": "auth.otp"},
    )
    errors = validate_facts(config, catalog)

    assert any("place_bet" in e.message for e in errors)
    assert any("amount" in e.message for e in errors)


def test_removing_authentication_is_rejected_by_a_dependency(catalog) -> None:
    config = FlowConfig(
        flows={"bet": ("understand", "pick_market", "collect_amount", "confirm", "place_bet")}
    )
    errors = validate_facts(config, catalog)

    assert any("authenticated" in e.message for e in errors)


def test_a_step_nothing_depends_on_may_be_dropped(catalog) -> None:
    config = FlowConfig(
        flows={"bet": ("authenticate", "pick_market", "collect_amount", "confirm", "place_bet")},
        bindings={"authenticate": "auth.otp"},
    )
    assert validate_facts(config, catalog) == []


# --- bindings ---------------------------------------------------------------


def test_binding_an_unregistered_strategy_is_rejected(catalog) -> None:
    config = FlowConfig(flows=valid_config().flows, bindings={"authenticate": "auth.magic_link"})
    errors = validate_facts(config, catalog)

    assert any("not a registered strategy" in e.message for e in errors)


def test_binding_a_strategy_to_the_wrong_slot_is_rejected(catalog) -> None:
    config = FlowConfig(
        flows=valid_config().flows, bindings={"authenticate": "identify.by_phone"}
    )
    errors = validate_facts(config, catalog)

    assert any("implements 'identify', not 'authenticate'" in e.message for e in errors)


def test_an_unbound_capability_is_rejected(catalog) -> None:
    errors = validate_facts(FlowConfig(flows=valid_config().flows), catalog)

    assert any("bound to it" in e.message for e in errors)


def test_binding_a_capability_no_flow_uses_is_rejected(catalog) -> None:
    config = FlowConfig(
        flows=valid_config().flows,
        bindings={"authenticate": "auth.otp", "identify": "identify.by_phone"},
    )
    errors = validate_facts(config, catalog)

    assert any("has no effect" in e.message for e in errors)


def test_all_errors_are_reported_together(catalog) -> None:
    config = FlowConfig(
        flows={"bet": ("understand", "nonsense", "place_bet")},
        bindings={"authenticate": "auth.magic_link"},
    )
    assert len(validate_facts(config, catalog)) >= 3


# --- copy -------------------------------------------------------------------

BET_COPY = {
    "bet.pick_market",
    "bet.ask_amount",
    "bet.confirm",
    "bet.cancelled",
    "bet.placed",
    "bet.insufficient_balance",
    "auth.ask_otp",
    "auth.otp_invalid",
}


def test_required_copy_collects_steps_outcomes_and_the_bound_strategy(catalog) -> None:
    requirements = required_copy(valid_config(), catalog)

    assert requirements.required == frozenset(BET_COPY)
    assert requirements.by_source["place_bet"] == frozenset(
        {"bet.placed", "bet.insufficient_balance"}
    )
    assert requirements.by_source["auth.otp"] == frozenset({"auth.ask_otp", "auth.otp_invalid"})
    assert "auth.password_form" not in requirements.by_source  # not bound, not required


def test_a_strategy_bound_to_a_slot_no_flow_uses_asks_for_no_copy(catalog) -> None:
    config = FlowConfig(flows={"bet": ("understand",)}, bindings={"authenticate": "auth.otp"})

    assert required_copy(config, catalog).required == frozenset()


def test_copy_is_not_checked_when_templates_are_omitted(catalog) -> None:
    assert validate_facts(valid_config(), catalog, templates=None) == []


def test_an_empty_copy_mapping_demands_every_required_id(catalog) -> None:
    """`{}` is a client with no copy yet. It is not the same as `None`."""
    errors = validate_facts(valid_config(), catalog, templates={})

    assert {e.field for e in errors} == {f"message_templates.{t}" for t in BET_COPY}


def test_complete_copy_is_accepted(catalog) -> None:
    templates = {template: "text" for template in BET_COPY}

    assert validate_facts(valid_config(), catalog, templates=templates) == []


def test_a_missing_copy_error_says_who_asked_for_it(catalog) -> None:
    templates = {template: "text" for template in BET_COPY - {"bet.placed"}}
    errors = validate_facts(valid_config(), catalog, templates=templates)

    assert errors == [
        ConfigError(
            field="message_templates.bet.placed",
            message="place_bet can display this, but no copy is set.",
        )
    ]


def test_a_config_error_prints_its_field_and_message() -> None:
    assert str(ConfigError(field="bindings.x", message="boom")) == "bindings.x: boom"
