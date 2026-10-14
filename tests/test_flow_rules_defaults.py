import subprocess
import sys
from pathlib import Path

import pytest

import chatbet_base_models.flow_rules as flow_rules
from chatbet_base_models import (
    DEFAULT_FLOW_POLICY as root_policy,
    FLOW_CATALOG as root_catalog,
    validate_facts as root_validate_facts,
    validate_policy as root_validate_policy,
)
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


def test_the_public_api_is_importable_from_the_package_root() -> None:
    assert root_catalog is FLOW_CATALOG
    assert root_policy is DEFAULT_FLOW_POLICY
    assert root_validate_facts is validate_facts
    assert root_validate_policy is validate_policy


def test_the_extractor_imports_without_building_the_shipped_defaults() -> None:
    """A broken generated module must not stop the script that regenerates it."""
    repo_root = Path(__file__).resolve().parent.parent
    code = (
        "import sys; import chatbet_base_models.flow_rules.extract; "
        "assert 'chatbet_base_models.flow_rules.defaults' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=repo_root, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr


def test_an_unknown_flow_rules_name_raises_attribute_error() -> None:
    with pytest.raises(AttributeError):
        flow_rules.does_not_exist


def test_the_lazy_exports_are_the_same_objects_as_the_defaults() -> None:
    assert flow_rules.FLOW_CATALOG is FLOW_CATALOG
    assert root_catalog is FLOW_CATALOG
