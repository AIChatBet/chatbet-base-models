"""Product decisions about how the flow_config may be used.

The catalog says what the code can do; this says what the product allows. It is
what a super admin edits, so it is plain data with a version, not code.
"""
from __future__ import annotations

from pydantic import Field

from ._base import FrozenModel
from .catalog import FlowCatalog


class FlowPolicy(FrozenModel):
    version: int = Field(default=1, ge=1)

    required_steps: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    """Flow id -> names that cannot be removed from that flow.

    Dependencies do not protect everything: ``confirm`` provides nothing, so no
    ``requires`` keeps it in place, yet dropping it lets users bet without
    confirming. That is a decision, so it is stated here.
    """

    allowed_strategies: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    """Capability id -> strategy ids a client may bind to it.

    No entry for a capability means every registered strategy is allowed. An
    explicit empty tuple means none is.
    """

    default_flows: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    """Flow id -> ordered names a new client starts from."""

    default_bindings: dict[str, str] = Field(default_factory=dict)
    """Capability id -> strategy id a new client starts with."""


def find_policy_problems(policy: FlowPolicy, catalog: FlowCatalog) -> list[str]:
    """Every way a policy contradicts the catalog it governs, as readable sentences.

    Flow ids are NOT checked: a client's own journeys are not the code's seed flows, and
    requiring a real step in one of them is legitimate.
    """
    return [
        *_required_step_problems(policy, catalog),
        *_allowed_strategy_problems(policy, catalog),
        *_default_flow_problems(policy, catalog),
        *_default_binding_problems(policy, catalog),
    ]


def _unknown_name_message(owner: str, name: str) -> str:
    return f"{owner} names {name!r}, which is not a step or capability in the catalog"


def _strategy_problem(owner: str, capability: str, strategy_id: str, catalog: FlowCatalog) -> str | None:
    strategy = catalog.strategies.get(strategy_id)
    if strategy is None:
        return f"{owner} names strategy {strategy_id!r}, which is not in the catalog"
    if strategy.capability != capability:
        return f"{owner} names {strategy_id!r}, which implements {strategy.capability!r}, not {capability!r}"
    return None


def _required_step_problems(policy: FlowPolicy, catalog: FlowCatalog) -> list[str]:
    return [
        _unknown_name_message(f"required_steps[{flow_id!r}]", name)
        for flow_id, names in policy.required_steps.items()
        for name in names
        if not catalog.knows(name)
    ]


def _allowed_strategy_problems(policy: FlowPolicy, catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    for capability, strategy_ids in policy.allowed_strategies.items():
        if capability not in catalog.capabilities:
            problems.append(f"allowed_strategies names {capability!r}, which is not a capability in the catalog")
            continue
        if not strategy_ids:
            problems.append(f"allowed_strategies[{capability!r}] is empty: no client could use this capability")
        for strategy_id in strategy_ids:
            problem = _strategy_problem(f"allowed_strategies[{capability!r}]", capability, strategy_id, catalog)
            if problem is not None:
                problems.append(problem)
    return problems


def _default_flow_problems(policy: FlowPolicy, catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    for flow_id, names in policy.default_flows.items():
        owner = f"default_flows[{flow_id!r}]"
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            problems.append(f"{owner} repeats {repeated}")
        problems += [_unknown_name_message(owner, name) for name in names if not catalog.knows(name)]
    return problems


def _default_binding_problems(policy: FlowPolicy, catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    for capability, strategy_id in policy.default_bindings.items():
        if capability not in catalog.capabilities:
            problems.append(f"default_bindings names {capability!r}, which is not a capability in the catalog")
            continue
        owner = f"default_bindings[{capability!r}]"
        problem = _strategy_problem(owner, capability, strategy_id, catalog)
        if problem is not None:
            problems.append(problem)
            continue
        allowed = policy.allowed_strategies.get(capability)
        if allowed is not None and strategy_id not in allowed:
            problems.append(f"{owner} is {strategy_id!r}, which allowed_strategies does not allow")
    return problems
