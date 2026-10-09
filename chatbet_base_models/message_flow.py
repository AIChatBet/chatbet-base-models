"""Flow events and the per-client flow routes.

``EventCatalog`` is global data (published by a super-admin): which events the bot
can report ("the OTP was invalid") and which message each one shows by default.
``ClientFlow`` is the per-client table ``event -> message key`` (and the global
default flow has the same shape). These are only the shared *types*; the data
never lives in this package. Event ids are plain strings, not an enum.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .message_catalog import (
    MESSAGE_KEY_RE,
    MessageCatalog,
    check_placeholder_names,
)
from .message_template import IDENTIFIER_RE


def _check_event_id(event_id: str) -> None:
    if not IDENTIFIER_RE.fullmatch(event_id):
        raise ValueError(f"invalid event id {event_id!r}: expected [a-z0-9_]+")


def _check_message_key(key: str) -> None:
    if not MESSAGE_KEY_RE.fullmatch(key):
        raise ValueError(f"invalid message key {key!r}: expected '<section>.<field>'")


class EventDef(BaseModel):
    """One event: the placeholders its message may use and the message shown by default."""

    model_config = ConfigDict(extra="forbid")

    description_i18n_key: Optional[str] = None
    allowed_placeholders: List[str] = Field(default_factory=list)
    default_message_key: str

    @field_validator("allowed_placeholders")
    @classmethod
    def _valid_unique_placeholders(cls, v: List[str]) -> List[str]:
        return check_placeholder_names(v)

    @field_validator("default_message_key")
    @classmethod
    def _valid_default_message_key(cls, v: str) -> str:
        _check_message_key(v)
        return v


class EventCatalog(BaseModel):
    """A published version of the global event catalog."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    events: Dict[str, EventDef]
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    @field_validator("events")
    @classmethod
    def _valid_ids(cls, v: Dict[str, EventDef]) -> Dict[str, EventDef]:
        for event_id in v:
            _check_event_id(event_id)
        return v


class ClientFlow(BaseModel):
    """A client's flow: which message each event shows. Empty routes use each event's default."""

    model_config = ConfigDict(extra="forbid")

    catalog_version: int = Field(ge=1)
    event_routes: Dict[str, str] = Field(default_factory=dict)

    @field_validator("event_routes")
    @classmethod
    def _valid_routes(cls, v: Dict[str, str]) -> Dict[str, str]:
        for event_id, message_key in v.items():
            _check_event_id(event_id)
            _check_message_key(message_key)
        return v


def find_event_catalog_problems(
    events: EventCatalog, messages: MessageCatalog
) -> List[str]:
    """Events whose default message is not in the message catalog (empty = consistent)."""
    return [
        f"event {event_id!r} defaults to unknown message key {definition.default_message_key!r}"
        for event_id, definition in sorted(events.events.items())
        if definition.default_message_key not in messages.message_keys
    ]


def find_flow_problems(
    flow: ClientFlow, events: EventCatalog, messages: MessageCatalog
) -> List[str]:
    """Routes for unknown events or to unknown message keys, by event id (empty = valid)."""
    problems: List[str] = []
    for event_id, message_key in sorted(flow.event_routes.items()):
        if event_id not in events.events:
            problems.append(f"route for unknown event {event_id!r}")
        elif message_key not in messages.message_keys:
            problems.append(
                f"event {event_id!r} routes to unknown message key {message_key!r}"
            )
    return problems
