"""Button destinations: what a button can lead to, and how its callback is built.

``DestinationCatalog`` is global data (DynamoDB, published by a super-admin): which
destinations exist and which parameters each takes. These are only the shared
*types* and the generator; the data itself never lives in this package. Ids are
plain strings, not an enum, so the list can grow without an incompatible release.
"""

import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .message_catalog import MessageCatalog
from .message_template import IDENTIFIER_RE, ButtonDestination
from .message_tokens import TOKEN_NAME_PATTERN

# Same limit as `InlineKeyboardButton.callback_data`.
CALLBACK_DATA_MAX_LENGTH = 64

ParamKind = Literal[
    "text",
    "sport",
    "tournament",
    "fixture",
    "market",
    "link",
    "promo",
    "tutorial",
    "message_key",
]

_PARAM_NAME_RE = re.compile(TOKEN_NAME_PATTERN)
_TEMPLATE_TOKEN_RE = re.compile(r"\{(" + TOKEN_NAME_PATTERN + r")\}")


class ParamDef(BaseModel):
    """One parameter of a destination; its kind tells the editor which picker to show."""

    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ParamKind
    required: bool = True

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not _PARAM_NAME_RE.fullmatch(v):
            raise ValueError(f"invalid parameter name: {v!r}")
        return v


class DestinationDef(BaseModel):
    """One destination: a callback (or URL) template and the parameters that fill it."""

    model_config = ConfigDict(extra="forbid")

    label_i18n_key: Optional[str] = None
    callback_template: Optional[str] = Field(default=None, min_length=1)
    url_template: Optional[str] = Field(default=None, min_length=1)
    params: List[ParamDef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one_template_matching_the_params(self) -> "DestinationDef":
        if (self.callback_template is None) == (self.url_template is None):
            raise ValueError(
                "a destination needs exactly one of callback_template and url_template"
            )
        template = self.callback_template or self.url_template or ""
        leftovers = _TEMPLATE_TOKEN_RE.sub("", template)
        if "{" in leftovers or "}" in leftovers:
            raise ValueError(f"template {template!r} has braces outside {{param}} tokens")
        declared = [param.name for param in self.params]
        if len(set(declared)) != len(declared):
            raise ValueError("parameter names must be unique")
        used = set(_TEMPLATE_TOKEN_RE.findall(template))
        if used != set(declared):
            raise ValueError(
                f"template tokens {sorted(used)} do not match declared params {sorted(declared)}"
            )
        return self


class DestinationCatalog(BaseModel):
    """A published version of the global destination catalog."""

    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    destinations: Dict[str, DestinationDef]
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    @field_validator("destinations")
    @classmethod
    def _valid_ids(cls, v: Dict[str, DestinationDef]) -> Dict[str, DestinationDef]:
        for destination_id in v:
            if not IDENTIFIER_RE.fullmatch(destination_id):
                raise ValueError(
                    f"invalid destination id {destination_id!r}: expected [a-z0-9_]+"
                )
        return v


class RenderedAction(BaseModel):
    """What a destination turns into on a button: a callback or a URL, never both."""

    model_config = ConfigDict(extra="forbid")

    callback_data: Optional[str] = None
    url: Optional[str] = None


def _fill(template: str, values: Dict[str, str]) -> str:
    # One pass: a value that itself contains `{name}` is inserted as plain text.
    return _TEMPLATE_TOKEN_RE.sub(lambda match: values[match.group(1)], template)


def render_destination(
    catalog: DestinationCatalog, destination: ButtonDestination
) -> RenderedAction:
    """Build the callback (or URL) of a destination; raises ``ValueError`` if it is invalid."""
    definition = catalog.destinations.get(destination.id)
    if definition is None:
        raise ValueError(f"unknown destination {destination.id!r}")
    declared = {param.name: param for param in definition.params}
    unexpected = sorted(set(destination.params) - set(declared))
    if unexpected:
        raise ValueError(
            f"unexpected parameters for destination {destination.id!r}: {unexpected}"
        )
    values: Dict[str, str] = {}
    for name, param in declared.items():
        value = destination.params.get(name, "")
        if param.required and not value:
            raise ValueError(
                f"missing required parameter {name!r} for destination {destination.id!r}"
            )
        values[name] = value
    if definition.callback_template is None:
        return RenderedAction(url=_fill(definition.url_template or "", values))
    callback_data = _fill(definition.callback_template, values)
    if len(callback_data) > CALLBACK_DATA_MAX_LENGTH:
        raise ValueError(
            f"callback_data of destination {destination.id!r} is "
            f"{len(callback_data)} characters, the limit is {CALLBACK_DATA_MAX_LENGTH}"
        )
    return RenderedAction(callback_data=callback_data)


def find_destination_problems(
    destination: ButtonDestination,
    catalog: DestinationCatalog,
    messages: MessageCatalog,
) -> List[str]:
    """Everything wrong with a button's destination, as readable messages (empty = valid)."""
    try:
        render_destination(catalog, destination)
    except ValueError as error:
        return [str(error)]
    definition = catalog.destinations[destination.id]
    problems: List[str] = []
    for param in definition.params:
        value = destination.params.get(param.name, "")
        if param.kind == "message_key" and value and value not in messages.message_keys:
            problems.append(
                f"parameter {param.name!r} points at unknown message key {value!r}"
            )
    return problems
