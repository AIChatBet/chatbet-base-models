from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace

import pytest

from chatbet_base_models.flow_rules.catalog import (
    CapabilityDef,
    FactDef,
    FlowCatalog,
    FlowRef,
    OutcomeDef,
    StepDef,
    StrategyDef,
)
from chatbet_base_models.flow_rules.extract import (
    CATALOG_FLAT_KINDS,
    CATALOG_KINDS,
    catalog_drift,
    catalog_from_registry,
    policy_from_registry,
    render_generated_module,
)
from chatbet_base_models.flow_rules.policy import FlowPolicy


class Scope(Enum):
    FLOW = "flow"
    SESSION = "session"


@dataclass(frozen=True)
class Message:
    templates: frozenset[str]


@dataclass(frozen=True)
class Outcome:
    id: str
    renders: tuple[Message, ...] = ()


@dataclass(frozen=True)
class Ref:
    name: str
    kind: str


def fake_registry() -> SimpleNamespace:
    confirm = SimpleNamespace(
        id="confirm",
        requires=("amount",),
        provides=(),
        omittable=False,
        renders=(Message(frozenset({"bet.confirm", "bet.cancel_label"})),),
        outcomes=(Outcome("cancelled", (Message(frozenset({"bet.cancelled"})),)),),
    )
    amount = SimpleNamespace(
        id="collect_amount",
        requires=(),
        provides=("amount",),
        omittable=True,
        renders=(Message(frozenset({"bet.ask_amount"})), Message(frozenset({"bet.ask_amount"}))),
        # no `outcomes` attribute at all: the real Step protocol does not require one
    )
    authenticate = SimpleNamespace(
        id="authenticate", requires=(), provides=("authenticated",), omittable=False
    )
    strategy = SimpleNamespace(
        id="auth.otp",
        capability="authenticate",
        renders=(Message(frozenset({"auth.ask_otp"})),),
        outcomes=(Outcome("rejected", (Message(frozenset({"auth.otp_invalid"})),)),),
    )
    unused_step = SimpleNamespace(
        id="support", requires=(), provides=(), omittable=False, renders=()
    )
    return SimpleNamespace(
        always_renders=(),
        facts={
            "amount": SimpleNamespace(name="amount", scope=Scope.FLOW),
            "authenticated": SimpleNamespace(name="authenticated", scope=Scope.SESSION),
        },
        steps={"confirm": confirm, "collect_amount": amount, "support": unused_step},
        capabilities_={"authenticate": authenticate},
        strategies={"auth.otp": strategy},
        flows={
            "bet": SimpleNamespace(
                id="bet",
                steps=(
                    Ref("authenticate", "capability"),
                    Ref("collect_amount", "step"),
                    Ref("confirm", "step"),
                ),
            )
        },
    )


def test_a_registry_becomes_a_catalog() -> None:
    catalog = catalog_from_registry(fake_registry())

    assert catalog.facts["authenticated"] == FactDef(name="authenticated", scope="session")
    assert catalog.steps["confirm"] == StepDef(
        id="confirm",
        requires=("amount",),
        renders=("bet.cancel_label", "bet.confirm"),
        outcomes=(OutcomeDef(id="cancelled", renders=("bet.cancelled",)),),
    )
    assert catalog.capabilities["authenticate"] == CapabilityDef(
        id="authenticate", provides=("authenticated",)
    )
    assert catalog.strategies["auth.otp"] == StrategyDef(
        id="auth.otp",
        capability="authenticate",
        renders=("auth.ask_otp",),
        outcomes=(OutcomeDef(id="rejected", renders=("auth.otp_invalid",)),),
    )
    assert catalog.flows["bet"].steps[0] == FlowRef(name="authenticate", kind="capability")


def test_copy_ids_are_sorted_and_deduplicated() -> None:
    catalog = catalog_from_registry(fake_registry())

    assert catalog.steps["collect_amount"].renders == ("bet.ask_amount",)


def test_a_step_without_outcomes_is_accepted() -> None:
    catalog = catalog_from_registry(fake_registry())

    assert catalog.steps["collect_amount"].outcomes == ()


def test_the_catalog_never_carries_omittable() -> None:
    dumped = catalog_from_registry(fake_registry()).model_dump(mode="json")

    assert "omittable" not in repr(dumped)


def test_a_non_omittable_step_in_a_flow_becomes_a_required_step() -> None:
    policy = policy_from_registry(fake_registry())

    assert policy.required_steps == {"bet": ("authenticate", "confirm")}


def test_a_non_omittable_step_in_no_flow_is_not_required_anywhere() -> None:
    """`support` is not omittable but no seed flow lists it; the channel never enforced it."""
    policy = policy_from_registry(fake_registry())

    assert all("support" not in names for names in policy.required_steps.values())


def test_the_policy_starts_from_the_code_seed_flows_and_restricts_no_strategy() -> None:
    policy = policy_from_registry(fake_registry())

    assert policy.default_flows == {"bet": ("authenticate", "collect_amount", "confirm")}
    assert policy.allowed_strategies == {}
    assert policy.default_bindings == {}


def test_drift_is_empty_when_catalog_and_code_agree() -> None:
    catalog = catalog_from_registry(fake_registry())

    assert catalog_drift(catalog, catalog_from_registry(fake_registry())) == []


def test_every_catalog_field_is_compared_by_drift() -> None:
    """The structural prompt. A field in neither tuple is a field drift cannot see.

    `catalog_drift` walks two tuples, not `FlowCatalog` itself, so adding a field
    and forgetting to list it is a silent hole rather than an error — which for
    copy nothing configures means the Backoffice never learns to ask for it. This
    fails on the field, at the edit, instead of months later in a company record.
    """
    compared = set(CATALOG_KINDS) | set(CATALOG_FLAT_KINDS)

    assert set(FlowCatalog.model_fields) == compared


def test_a_registry_that_never_declared_unconditional_copy_fails_loudly() -> None:
    """Silence here would be the original defect, one layer up and unobservable."""
    registry = fake_registry()
    del registry.always_renders

    with pytest.raises(AttributeError, match="always_renders"):
        catalog_from_registry(registry)


def test_drift_notices_unconditional_copy_the_catalog_has_not_got() -> None:
    """Without this the Backoffice silently keeps not asking for it.

    `always_renders` is a flat set, not one of the named collections the loop
    above walks, so a template added in the code and never regenerated would
    drift undetected — which is the exact failure this copy exists to close.
    """
    expected = catalog_from_registry(fake_registry())
    registry = fake_registry()
    registry.always_renders = ("labels.expired_button",)

    assert catalog_drift(expected, catalog_from_registry(registry)) == [
        "always_renders: 'labels.expired_button' exists in the code but not in the catalog"
    ]


def test_drift_notices_unconditional_copy_the_code_has_dropped() -> None:
    registry = fake_registry()
    registry.always_renders = ("labels.expired_button",)
    expected = catalog_from_registry(registry)

    assert catalog_drift(expected, catalog_from_registry(fake_registry())) == [
        "always_renders: 'labels.expired_button' is in the catalog but not in the code"
    ]


def test_drift_names_what_the_code_added_removed_and_changed() -> None:
    expected = catalog_from_registry(fake_registry())
    registry = fake_registry()
    del registry.steps["support"]
    registry.steps["new_step"] = SimpleNamespace(
        id="new_step", requires=(), provides=(), omittable=True, renders=()
    )
    registry.steps["confirm"].renders = ()
    actual = catalog_from_registry(registry)

    assert catalog_drift(expected, actual) == [
        "steps: 'new_step' exists in the code but not in the catalog",
        "steps: 'support' is in the catalog but not in the code",
        "steps: 'confirm' differs between code and catalog (renders)",
    ]


def test_the_generated_module_round_trips() -> None:
    catalog = catalog_from_registry(fake_registry())
    policy = policy_from_registry(fake_registry())

    namespace: dict[str, object] = {}
    exec(render_generated_module(catalog, policy), namespace)

    assert FlowCatalog.model_validate(namespace["CATALOG_DATA"]) == catalog
    assert FlowPolicy.model_validate(namespace["POLICY_DATA"]) == policy
