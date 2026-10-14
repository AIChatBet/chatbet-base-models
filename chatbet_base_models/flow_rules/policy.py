"""Product decisions about how the flow_config may be used.

The catalog says what the code can do; this says what the product allows. It is
what a super admin edits, so it is plain data with a version, not code.
"""
from __future__ import annotations

from pydantic import Field

from ._base import FrozenModel


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
