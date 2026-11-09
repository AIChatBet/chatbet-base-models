import pytest
from pydantic import ValidationError

from chatbet_base_models.flow_rules.catalog import (
    CapabilityDef,
    FactDef,
    FlowCatalog,
    FlowDef,
    FlowRef,
    OutcomeDef,
    StepDef,
    StrategyDef,
)


def make_catalog(**overrides: object) -> FlowCatalog:
    data: dict[str, object] = dict(
        facts={
            "authenticated": FactDef(name="authenticated", scope="session"),
            "amount": FactDef(name="amount", scope="flow"),
        },
        steps={
            "collect_amount": StepDef(
                id="collect_amount", provides=("amount",), renders=("bet.ask_amount",)
            )
        },
        capabilities={
            "authenticate": CapabilityDef(id="authenticate", provides=("authenticated",))
        },
        strategies={
            "auth.otp": StrategyDef(
                id="auth.otp",
                capability="authenticate",
                outcomes=(OutcomeDef(id="rejected", renders=("auth.otp_invalid",)),),
            )
        },
        flows={
            "bet": FlowDef(
                id="bet",
                steps=(
                    FlowRef(name="authenticate", kind="capability"),
                    FlowRef(name="collect_amount", kind="step"),
                ),
            )
        },
    )
    data.update(overrides)
    return FlowCatalog(**data)


def test_a_consistent_catalog_builds_and_answers_lookups() -> None:
    catalog = make_catalog()

    assert catalog.knows("collect_amount")
    assert catalog.knows("authenticate")
    assert not catalog.knows("auth.otp")  # a strategy is not something a flow lists
    assert catalog.contract("collect_amount").provides == ("amount",)
    assert catalog.contract("authenticate").id == "authenticate"
    assert catalog.contract("nope") is None


def test_a_step_using_an_undeclared_fact_is_rejected() -> None:
    steps = {"x": StepDef(id="x", requires=("ghost",))}
    with pytest.raises(ValidationError, match="ghost"):
        make_catalog(steps=steps, flows={})


def test_a_strategy_for_an_unknown_capability_is_rejected() -> None:
    strategies = {"s": StrategyDef(id="s", capability="no_such")}
    with pytest.raises(ValidationError, match="no_such"):
        make_catalog(strategies=strategies)


def test_a_flow_naming_something_undeclared_is_rejected() -> None:
    flows = {"f": FlowDef(id="f", steps=(FlowRef(name="collect_amount", kind="capability"),))}
    with pytest.raises(ValidationError, match="collect_amount"):
        make_catalog(flows=flows)


def test_a_flow_repeating_a_name_is_rejected() -> None:
    ref = FlowRef(name="collect_amount", kind="step")
    flows = {"f": FlowDef(id="f", steps=(ref, ref))}
    with pytest.raises(ValidationError, match="repeats"):
        make_catalog(flows=flows)


def test_step_capability_and_strategy_ids_share_one_namespace() -> None:
    steps = {"authenticate": StepDef(id="authenticate")}
    with pytest.raises(ValidationError, match="both"):
        make_catalog(steps=steps, flows={})


def test_a_mapping_key_must_match_the_definition_id() -> None:
    steps = {"a": StepDef(id="b")}
    with pytest.raises(ValidationError, match="holds a definition"):
        make_catalog(steps=steps, flows={})


def test_omittable_is_not_part_of_the_catalog() -> None:
    """It is policy now. Accepting it here would hide the move."""
    with pytest.raises(ValidationError):
        StepDef(id="x", omittable=True)  # type: ignore[call-arg]


def test_the_catalog_is_frozen() -> None:
    catalog = make_catalog()
    with pytest.raises(ValidationError):
        catalog.steps = {}  # type: ignore[misc]


def test_fingerprint_is_stable_and_follows_content() -> None:
    first = make_catalog()
    second = make_catalog()
    changed = make_catalog(
        steps={
            "collect_amount": StepDef(
                id="collect_amount", provides=("amount",), renders=("bet.other",)
            )
        }
    )

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 12
    assert first.fingerprint != changed.fingerprint
