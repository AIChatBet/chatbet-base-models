"""Rules for a client's flow_config: what the code can do, and what may be configured.

Two layers. The catalog holds implementation facts and comes from the channel's
code; the policy holds product decisions and is edited in the Backoffice.
``validate_facts`` and ``validate_policy`` are pure.
"""
import importlib
from typing import Any

from .catalog import (
    CapabilityDef,
    FactDef,
    FlowCatalog,
    FlowDef,
    FlowRef,
    OutcomeDef,
    StepDef,
    StrategyDef,
    find_catalog_problems,
)
from .extract import (
    catalog_drift,
    catalog_from_registry,
    policy_from_registry,
    render_generated_module,
)
from .policy import FlowPolicy, find_policy_problems
from .validation import (
    ConfigError,
    CopyRequirements,
    FlowConfig,
    required_copy,
    validate_facts,
    validate_policy,
)

__all__ = [
    "CapabilityDef",
    "ConfigError",
    "CopyRequirements",
    "DEFAULT_FLOW_POLICY",
    "FLOW_CATALOG",
    "FactDef",
    "FlowCatalog",
    "FlowConfig",
    "FlowDef",
    "FlowPolicy",
    "FlowRef",
    "OutcomeDef",
    "StepDef",
    "StrategyDef",
    "catalog_drift",
    "catalog_from_registry",
    "find_catalog_problems",
    "find_policy_problems",
    "policy_from_registry",
    "render_generated_module",
    "required_copy",
    "validate_facts",
    "validate_policy",
]


_LAZY_DEFAULTS = ("DEFAULT_FLOW_POLICY", "FLOW_CATALOG")


def __getattr__(name: str) -> Any:
    """Build the shipped defaults on first use, so a broken generated module does
    not stop the package (or the script that regenerates it) from importing."""
    if name in _LAZY_DEFAULTS:
        return getattr(importlib.import_module(".defaults", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
