"""Rules for a client's flow_config: what the code can do, and what may be configured.

Two layers. The catalog holds implementation facts and comes from the channel's
code; the policy holds product decisions and is edited in the Backoffice.
``validate_facts`` and ``validate_policy`` are pure.
"""
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
from .defaults import DEFAULT_FLOW_POLICY, FLOW_CATALOG
from .extract import (
    catalog_drift,
    catalog_from_registry,
    policy_from_registry,
    render_generated_module,
)
from .policy import FlowPolicy
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
    "policy_from_registry",
    "render_generated_module",
    "required_copy",
    "validate_facts",
    "validate_policy",
]
