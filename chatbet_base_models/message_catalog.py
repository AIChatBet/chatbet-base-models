"""Dynamic message catalog and per-client message content.

``MessageCatalog`` is global data (DynamoDB ``PK=message_catalog``): which message
keys exist and which placeholders each one accepts. ``ClientMessages`` is the
per-client content (``PK=company#<id> / SK=message_templates``) in the new shape.
These are only the shared *types*; the data itself never lives in this package.
"""

import re
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .message_template import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinksMessages,
    MessageItem,
    MessageTemplates,
)
from .message_tokens import TOKEN_NAME_PATTERN

MESSAGE_KEY_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
PLACEHOLDER_NAME_RE = re.compile(r"^" + TOKEN_NAME_PATTERN + r"$")
LEGACY_TOKEN_RE = re.compile(r"^(%\d*|\{\{" + TOKEN_NAME_PATTERN + r"\}\})$")

# WhatsApp shows more than 3 buttons as a list, and a list holds at most 10 rows
# (anything beyond is dropped silently by the channel), so authored content is
# capped here instead.
MAX_BUTTONS_PER_MESSAGE = 10

# Legacy sections that are not MessageItem groups and travel next to `messages`.
_NON_CATALOG_SECTIONS = {"links", "created_at", "updated_at"}


def _check_message_keys(keys: List[str]) -> None:
    for key in keys:
        if not MESSAGE_KEY_RE.fullmatch(key):
            raise ValueError(
                f"invalid message key {key!r}: expected '<section>.<field>'"
            )


def check_placeholder_names(names: List[str]) -> List[str]:
    """Placeholder names must be valid tokens and unique; shared by catalog entries and events."""
    for name in names:
        if not PLACEHOLDER_NAME_RE.fullmatch(name):
            raise ValueError(f"invalid placeholder name: {name!r}")
    if len(set(names)) != len(names):
        raise ValueError("allowed_placeholders must not contain duplicates")
    return names


class CatalogEntry(BaseModel):
    """One message key of the catalog: which placeholders its text may use."""

    model_config = ConfigDict(extra="forbid")

    allowed_placeholders: List[str] = Field(default_factory=list)
    # literal used in today's templates (`%1`, `%`, `{{BET_REMOVED}}`) -> name of
    # the value that fills it. The name must also be an allowed placeholder.
    legacy_tokens: Dict[str, str] = Field(default_factory=dict)
    description_i18n_key: Optional[str] = None

    @field_validator("allowed_placeholders")
    @classmethod
    def _valid_unique_placeholders(cls, v: List[str]) -> List[str]:
        return check_placeholder_names(v)

    @model_validator(mode="after")
    def _valid_legacy_tokens(self) -> "CatalogEntry":
        for literal, name in self.legacy_tokens.items():
            if not LEGACY_TOKEN_RE.fullmatch(literal):
                raise ValueError(f"invalid legacy token literal: {literal!r}")
            if name not in self.allowed_placeholders:
                raise ValueError(
                    f"legacy token {literal!r} maps to {name!r}, "
                    "which is not in allowed_placeholders"
                )
        return self


class MessageCatalog(BaseModel):
    """A published version of the global catalog."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    message_keys: Dict[str, CatalogEntry]
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    @field_validator("message_keys")
    @classmethod
    def _valid_keys(cls, v: Dict[str, CatalogEntry]) -> Dict[str, CatalogEntry]:
        _check_message_keys(list(v))
        return v


class MessageContent(BaseModel):
    """One authored message: text plus at most ``MAX_BUTTONS_PER_MESSAGE`` buttons.

    There is deliberately no ``additional_message``: WhatsApp bills every message
    sent, so a second message carrying the buttons that did not fit is wasted
    spend. More than 3 buttons are shown by the channel as a list instead.
    """

    model_config = ConfigDict(extra="forbid")

    text: Optional[str] = None
    reply_markup: Optional[InlineKeyboardMarkup] = None

    @field_validator("reply_markup")
    @classmethod
    def _within_button_limit(
        cls, v: Optional[InlineKeyboardMarkup]
    ) -> Optional[InlineKeyboardMarkup]:
        count = sum(len(row) for row in v.inline_keyboard) if v else 0
        if count > MAX_BUTTONS_PER_MESSAGE:
            raise ValueError(
                f"a message holds at most {MAX_BUTTONS_PER_MESSAGE} buttons, got {count}"
            )
        return v


class ClientMessages(BaseModel):
    """Per-client content in the new shape (replaces the 11 fixed sections)."""

    model_config = ConfigDict(extra="forbid")

    catalog_version: int = Field(ge=1)
    messages: Dict[str, MessageContent] = Field(default_factory=dict)
    # The client's named links. Not messages, so not catalog keys, but real
    # operator content: a button points at one by title (`link:<title>`).
    # `general_errors` (dead data, no reader and no editor) and
    # `account_state_defaults` (a code constant, `DEFAULT_ACCOUNT_STATE`) are
    # deliberately NOT carried per client.
    links: Optional[LinksMessages] = None

    @field_validator("messages")
    @classmethod
    def _valid_keys(cls, v: Dict[str, MessageContent]) -> Dict[str, MessageContent]:
        _check_message_keys(list(v))
        return v


class LegacyConversion(BaseModel):
    """Result of converting legacy templates: the content plus what needs review."""

    model_config = ConfigDict(extra="forbid")

    content: ClientMessages
    warnings: List[str] = Field(default_factory=list)


def _cap_buttons(
    key: str, rows: List[List[InlineKeyboardButton]], warnings: List[str]
) -> List[List[InlineKeyboardButton]]:
    """Keep the first ``MAX_BUTTONS_PER_MESSAGE`` buttons, reporting what is cut."""
    total = sum(len(row) for row in rows)
    if total <= MAX_BUTTONS_PER_MESSAGE:
        return rows
    warnings.append(
        f"{key}: {total} buttons exceed the {MAX_BUTTONS_PER_MESSAGE}-button limit; "
        f"kept the first {MAX_BUTTONS_PER_MESSAGE}"
    )
    kept: List[List[InlineKeyboardButton]] = []
    room = MAX_BUTTONS_PER_MESSAGE
    for row in rows:
        if room <= 0:
            break
        kept.append(row[:room])
        room -= len(row)
    return kept


def _to_content(key: str, item: MessageItem, warnings: List[str]) -> MessageContent:
    """Fold a legacy item into a single message.

    The buttons of the old ``additional_message`` move to the main keyboard (the
    channel shows more than 3 buttons as a list). Its own text has nowhere to go,
    so it is reported instead of being dropped silently.
    """
    rows = list(item.reply_markup.inline_keyboard) if item.reply_markup else []
    extra = item.additional_message
    if extra is not None:
        if extra.text and extra.text.strip():
            warnings.append(f"{key}: additional_message text dropped: {extra.text!r}")
        if extra.reply_markup:
            rows.extend(extra.reply_markup.inline_keyboard)
    rows = _cap_buttons(key, rows, warnings)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
    return MessageContent(text=item.text, reply_markup=reply_markup)


def legacy_to_client_messages(
    templates: MessageTemplates, catalog_version: int
) -> LegacyConversion:
    """Convert the legacy 11-section ``MessageTemplates`` into ``ClientMessages``.

    Every non-empty ``MessageItem`` field becomes ``"<section>.<field>"``. This is
    the single implementation shared by the Backoffice migration script and the
    Channel Services loader (which must accept both shapes during the window).
    The returned ``warnings`` list what could not be carried over as is.
    """
    warnings: List[str] = []
    messages: Dict[str, MessageContent] = {}
    for section in MessageTemplates.model_fields:
        if section in _NON_CATALOG_SECTIONS:
            continue
        group = getattr(templates, section)
        if group is None:
            continue
        for field in type(group).model_fields:
            value = getattr(group, field)
            if isinstance(value, MessageItem):
                key = f"{section}.{field}"
                messages[key] = _to_content(key, value, warnings)

    content = ClientMessages(
        catalog_version=catalog_version,
        messages=messages,
        links=templates.links,
    )
    return LegacyConversion(content=content, warnings=warnings)
