"""The catalog and starting policy generated from the channel's code."""
from __future__ import annotations

from ._generated import CATALOG_DATA, POLICY_DATA
from .catalog import FlowCatalog
from .policy import FlowPolicy

FLOW_CATALOG = FlowCatalog.model_validate(CATALOG_DATA)
"""What the channel's code could do when this was generated; see ``fingerprint``."""

DEFAULT_FLOW_POLICY = FlowPolicy.model_validate(POLICY_DATA)
"""Used until a super admin publishes a policy of their own."""
