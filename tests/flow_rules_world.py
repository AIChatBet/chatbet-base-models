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
from chatbet_base_models.flow_rules.validation import FlowConfig


def world_catalog() -> FlowCatalog:
    facts = {
        "intent": FactDef(name="intent", scope="flow"),
        "selected_market": FactDef(name="selected_market", scope="flow"),
        "amount": FactDef(name="amount", scope="flow"),
        "bet_placed": FactDef(name="bet_placed", scope="flow"),
        "authenticated": FactDef(name="authenticated", scope="session"),
        "identity": FactDef(name="identity", scope="session"),
    }
    steps = {
        "understand": StepDef(id="understand", provides=("intent",)),
        "collect_amount": StepDef(
            id="collect_amount",
            requires=("authenticated",),  # deliberately NOT the market
            provides=("amount",),
            renders=("bet.ask_amount",),
        ),
        "pick_market": StepDef(
            id="pick_market", provides=("selected_market",), renders=("bet.pick_market",)
        ),
        "confirm": StepDef(
            id="confirm",
            renders=("bet.confirm", "bet.cancelled"),
            outcomes=(OutcomeDef(id="cancelled", renders=("bet.cancelled",)),),
        ),
        "place_bet": StepDef(
            id="place_bet",
            requires=("authenticated", "selected_market", "amount"),
            provides=("bet_placed",),
            renders=("bet.placed",),
            outcomes=(
                OutcomeDef(id="insufficient_balance", renders=("bet.insufficient_balance",)),
            ),
        ),
    }
    capabilities = {
        "authenticate": CapabilityDef(id="authenticate", provides=("authenticated",)),
        "identify": CapabilityDef(id="identify", provides=("identity",)),
    }
    strategies = {
        "auth.otp": StrategyDef(
            id="auth.otp",
            capability="authenticate",
            renders=("auth.ask_otp",),
            outcomes=(OutcomeDef(id="rejected", renders=("auth.otp_invalid",)),),
        ),
        "auth.password_form": StrategyDef(
            id="auth.password_form",
            capability="authenticate",
            renders=("auth.ask_password",),
        ),
        "identify.by_phone": StrategyDef(
            id="identify.by_phone", capability="identify", renders=("identify.ask_phone",)
        ),
    }
    flows = {
        "bet": FlowDef(
            id="bet",
            steps=(
                FlowRef(name="understand", kind="step"),
                FlowRef(name="authenticate", kind="capability"),
                FlowRef(name="pick_market", kind="step"),
                FlowRef(name="collect_amount", kind="step"),
                FlowRef(name="confirm", kind="step"),
                FlowRef(name="place_bet", kind="step"),
            ),
        )
    }
    return FlowCatalog(
        facts=facts, steps=steps, capabilities=capabilities, strategies=strategies, flows=flows
    )


def valid_config() -> FlowConfig:
    return FlowConfig(
        flows={
            "bet": (
                "understand",
                "authenticate",
                "pick_market",
                "collect_amount",
                "confirm",
                "place_bet",
            )
        },
        bindings={"authenticate": "auth.otp"},
    )
