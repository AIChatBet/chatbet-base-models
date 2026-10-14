"""What the channel's code can do: implementation facts, never product decisions.

A step's ``requires``/``provides`` and the copy it can display are facts about
what the code does; only the code knows them. Whether a step may be left out of
a client's flow is a decision, and lives in ``policy.FlowPolicy`` instead.
"""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import Field, model_validator

from ._base import FrozenModel

FactScope = Literal["flow", "session"]
RefKind = Literal["step", "capability"]


class FactDef(FrozenModel):
    name: str = Field(min_length=1)
    scope: FactScope


class OutcomeDef(FrozenModel):
    """A result a step or strategy can produce, with every copy id it may display."""

    id: str = Field(min_length=1)
    renders: tuple[str, ...] = ()


class ContractDef(FrozenModel):
    id: str = Field(min_length=1)
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    renders: tuple[str, ...] = ()
    outcomes: tuple[OutcomeDef, ...] = ()


class StepDef(ContractDef):
    pass


class CapabilityDef(ContractDef):
    """A slot in a flow; every strategy filling it honours this contract."""


class StrategyDef(FrozenModel):
    id: str = Field(min_length=1)
    capability: str = Field(min_length=1)
    renders: tuple[str, ...] = ()
    outcomes: tuple[OutcomeDef, ...] = ()


class FlowRef(FrozenModel):
    name: str = Field(min_length=1)
    kind: RefKind


class FlowDef(FrozenModel):
    """A flow the code ships as a starting point; clients store their own whole."""

    id: str = Field(min_length=1)
    steps: tuple[FlowRef, ...] = ()


class FlowCatalog(FrozenModel):
    facts: dict[str, FactDef] = Field(default_factory=dict)
    steps: dict[str, StepDef] = Field(default_factory=dict)
    capabilities: dict[str, CapabilityDef] = Field(default_factory=dict)
    strategies: dict[str, StrategyDef] = Field(default_factory=dict)
    flows: dict[str, FlowDef] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _reject_inconsistent_catalog(self) -> FlowCatalog:
        problems = find_catalog_problems(self)
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def knows(self, name: str) -> bool:
        """Whether a flow may list this name: a step or a capability slot."""
        return name in self.steps or name in self.capabilities

    def contract(self, name: str) -> ContractDef | None:
        step = self.steps.get(name)
        if step is not None:
            return step
        return self.capabilities.get(name)

    @property
    def fingerprint(self) -> str:
        """Short content hash, so a consumer can tell which catalog it holds."""
        canonical = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def find_catalog_problems(catalog: FlowCatalog) -> list[str]:
    """Every way a catalog contradicts itself, as readable sentences."""
    return [
        *_identity_problems(catalog),
        *_namespace_problems(catalog),
        *_fact_problems(catalog),
        *_strategy_problems(catalog),
        *_flow_problems(catalog),
    ]


def _identity_problems(catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    groups = (
        ("facts", catalog.facts),
        ("steps", catalog.steps),
        ("capabilities", catalog.capabilities),
        ("strategies", catalog.strategies),
        ("flows", catalog.flows),
    )
    for kind, items in groups:
        for key, item in items.items():
            item_id = item.name if isinstance(item, FactDef) else item.id
            if key != item_id:
                problems.append(f"{kind}[{key!r}] holds a definition whose id is {item_id!r}")
    return problems


def _namespace_problems(catalog: FlowCatalog) -> list[str]:
    """Step, capability and strategy ids share one namespace, so a flow can hold a flat list of names."""
    problems: list[str] = []
    seen: dict[str, str] = {}
    groups = (
        ("step", catalog.steps),
        ("capability", catalog.capabilities),
        ("strategy", catalog.strategies),
    )
    for kind, items in groups:
        for name in items:
            if name in seen:
                problems.append(f"{name!r} is registered as both a {seen[name]} and a {kind}")
            else:
                seen[name] = kind
    return problems


def _fact_problems(catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    for owner, contract in (*catalog.steps.items(), *catalog.capabilities.items()):
        referenced = set(contract.requires) | set(contract.provides)
        unknown = sorted(referenced - set(catalog.facts))
        if unknown:
            problems.append(f"{owner!r} uses facts that are not declared: {unknown}")
    return problems


def _strategy_problems(catalog: FlowCatalog) -> list[str]:
    return [
        f"strategy {strategy.id!r} implements {strategy.capability!r}, "
        "which is not a declared capability"
        for strategy in catalog.strategies.values()
        if strategy.capability not in catalog.capabilities
    ]


def _flow_problems(catalog: FlowCatalog) -> list[str]:
    problems: list[str] = []
    for flow_id, flow in catalog.flows.items():
        names = [ref.name for ref in flow.steps]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            problems.append(f"flow {flow_id!r} repeats {repeated}")
        for ref in flow.steps:
            declared = catalog.steps if ref.kind == "step" else catalog.capabilities
            if ref.name not in declared:
                problems.append(
                    f"flow {flow_id!r} names {ref.kind} {ref.name!r}, which is not declared"
                )
    return problems
