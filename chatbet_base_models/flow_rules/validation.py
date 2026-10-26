"""Pure validation of a client's flow_config against the catalog and the policy.

Ported from the channel's ``conversation/flow/validation.py``. The split is the
point: ``validate_facts`` checks what the code cannot run without (names that
exist, dependencies, bindings, copy); ``validate_policy`` (below) checks what the
product decided. The channel calls only the first.
"""
from __future__ import annotations

from collections.abc import Collection

from pydantic import Field

from ._base import FrozenModel
from .catalog import ContractDef, FlowCatalog, StrategyDef
from .policy import FlowPolicy


class ConfigError(FrozenModel):
    """One reason a configuration was rejected.

    ``field`` is the path the UI should highlight; ``message`` is what to say.
    """

    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class FlowConfig(FrozenModel):
    """A client's stored conversation configuration.

    Each flow is held whole: what is stored is what runs, with nothing merged in.
    """

    flows: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    bindings: dict[str, str] = Field(default_factory=dict)


class CopyRequirements(FrozenModel):
    """The exact set of copy ids one client's configuration can display."""

    required: frozenset[str]
    by_source: dict[str, frozenset[str]]
    """Which step, strategy, or unconditional source asked for each group, so an error
    can say why."""

    def missing_from(self, available: Collection[str]) -> frozenset[str]:
        return frozenset(template for template in self.required if template not in available)


def validate_facts(
    config: FlowConfig,
    catalog: FlowCatalog,
    templates: Collection[str] | None = None,
) -> list[ConfigError]:
    """Every reason this configuration cannot run, given what the code can do.

    All checks run; the caller gets the full list rather than the first failure.
    ``templates`` is the set of copy ids that exist (a mapping works: only its keys
    are read). It is optional because flow structure can be checked before copy
    exists. When supplied, even an empty collection, missing copy is an error.
    """
    errors = [
        *_check_names_resolve(config, catalog),
        *_check_dependencies_satisfied(config, catalog),
        *_check_bindings(config, catalog),
    ]
    if templates is not None:
        errors += _check_copy(config, catalog, templates)
    return errors


def validate_policy(config: FlowConfig, policy: FlowPolicy) -> list[ConfigError]:
    """Every way this configuration breaks a product decision."""
    return [
        *_check_required_steps(config, policy),
        *_check_allowed_strategies(config, policy),
    ]


#: How `by_source` names the catalog's unconditional copy. Every other key is a
#: step or strategy id the operator chose; this one is prose because it names the
#: thing they did not choose, and because `_check_copy` reads it aloud: "<source>
#: can display this, but no copy is set." Nothing about a channel belongs here —
#: a tap, a voice turn and a push all reach this copy the same way, by not going
#: through a flow at all.
ALWAYS = "the bot itself"


def required_copy(config: FlowConfig, catalog: FlowCatalog) -> CopyRequirements:
    """Every copy id this client's configuration can display.

    Three sources, and only together are they complete. A step knows what it
    renders and what its outcomes render; it does not know which errors can
    occur, because that depends on the strategy bound to the capability. And
    neither knows the copy a channel displays without consulting the flow at
    all, which is `catalog.always_renders` — configured by nobody, so derived
    from nothing the first two sources can see.
    """
    by_source: dict[str, frozenset[str]] = {}
    _claim(by_source, ALWAYS, frozenset(catalog.always_renders))

    for names in config.flows.values():
        for name in names:
            contract = catalog.contract(name)
            if contract is not None:
                _claim(by_source, name, _copy_of(contract))

    used_slots = _slots_used(config, catalog)
    for slot, strategy_id in config.bindings.items():
        strategy = catalog.strategies.get(strategy_id)
        if strategy is not None and slot in used_slots:
            _claim(by_source, strategy_id, _copy_of(strategy))

    required = frozenset().union(*by_source.values())
    return CopyRequirements(required=required, by_source=by_source)


def _claim(by_source: dict[str, frozenset[str]], source: str, templates: frozenset[str]) -> None:
    if templates:
        by_source[source] = templates


def _copy_of(contract: ContractDef | StrategyDef) -> frozenset[str]:
    from_outcomes = (template for outcome in contract.outcomes for template in outcome.renders)
    return frozenset(contract.renders) | frozenset(from_outcomes)


def _slots_used(config: FlowConfig, catalog: FlowCatalog) -> set[str]:
    return {
        name
        for names in config.flows.values()
        for name in names
        if name in catalog.capabilities
    }


# --- facts: checks ------------------------------------------------------------


def _check_names_resolve(config: FlowConfig, catalog: FlowCatalog) -> list[ConfigError]:
    """Every name must be a registered step or a known capability slot."""
    return [
        ConfigError(
            field=f"flows.{flow_id}[{position}]",
            message=(
                f"{name!r} is not a registered step or capability. "
                "Nothing in the code answers to this name."
            ),
        )
        for flow_id, names in config.flows.items()
        for position, name in enumerate(names)
        if not catalog.knows(name)
    ]


def _check_dependencies_satisfied(config: FlowConfig, catalog: FlowCatalog) -> list[ConfigError]:
    """Each step's ``requires`` must be produced by a step before it.

    This is what makes reordering safe as configuration: an order is valid when
    every step finds its requirements produced earlier.
    """
    errors: list[ConfigError] = []
    for flow_id, names in config.flows.items():
        produced: set[str] = set()
        for position, name in enumerate(names):
            contract = catalog.contract(name)
            if contract is None:
                continue  # unknown name, already reported
            missing = [fact for fact in contract.requires if fact not in produced]
            if missing:
                errors.append(
                    ConfigError(
                        field=f"flows.{flow_id}[{position}]",
                        message=(
                            f"{name!r} needs {missing} but no earlier step provides "
                            f"{'them' if len(missing) > 1 else 'it'}."
                        ),
                    )
                )
            produced |= set(contract.provides)
    return errors


def _check_bindings(config: FlowConfig, catalog: FlowCatalog) -> list[ConfigError]:
    """Bindings must name real slots and real strategies, and match."""
    errors: list[ConfigError] = []
    declared_slots = _slots_used(config, catalog)

    for slot, strategy_id in config.bindings.items():
        if slot not in declared_slots:
            errors.append(
                ConfigError(
                    field=f"bindings.{slot}",
                    message=(
                        f"no stored flow uses the capability {slot!r}, "
                        "so binding it has no effect."
                    ),
                )
            )
        strategy = catalog.strategies.get(strategy_id)
        if strategy is None:
            errors.append(
                ConfigError(
                    field=f"bindings.{slot}",
                    message=f"{strategy_id!r} is not a registered strategy.",
                )
            )
        elif strategy.capability != slot:
            errors.append(
                ConfigError(
                    field=f"bindings.{slot}",
                    message=(
                        f"{strategy_id!r} implements {strategy.capability!r}, not {slot!r}."
                    ),
                )
            )

    for slot in sorted(declared_slots - set(config.bindings)):
        errors.append(
            ConfigError(
                field=f"bindings.{slot}",
                message=(
                    f"a stored flow uses the capability {slot!r} but nothing is bound to it."
                ),
            )
        )
    return errors


def _check_copy(
    config: FlowConfig, catalog: FlowCatalog, templates: Collection[str]
) -> list[ConfigError]:
    """Copy a stored flow needs but nobody has written."""
    requirements = required_copy(config, catalog)
    errors: list[ConfigError] = []
    for template in sorted(requirements.missing_from(templates)):
        asked_by = sorted(
            source for source, group in requirements.by_source.items() if template in group
        )
        errors.append(
            ConfigError(
                field=f"message_templates.{template}",
                message=f"{', '.join(asked_by)} can display this, but no copy is set.",
            )
        )
    return errors


# --- policy: checks -----------------------------------------------------------


def _check_required_steps(config: FlowConfig, policy: FlowPolicy) -> list[ConfigError]:
    errors: list[ConfigError] = []
    for flow_id, names in config.flows.items():
        present = set(names)
        for required in policy.required_steps.get(flow_id, ()):
            if required not in present:
                errors.append(
                    ConfigError(
                        field=f"flows.{flow_id}",
                        message=f"{required!r} cannot be removed from this flow (required by policy).",
                    )
                )
    return errors


def _check_allowed_strategies(config: FlowConfig, policy: FlowPolicy) -> list[ConfigError]:
    errors: list[ConfigError] = []
    for slot, strategy_id in config.bindings.items():
        allowed = policy.allowed_strategies.get(slot)
        if allowed is not None and strategy_id not in allowed:
            errors.append(
                ConfigError(
                    field=f"bindings.{slot}",
                    message=f"{strategy_id!r} is not allowed for {slot!r} by policy.",
                )
            )
    return errors
