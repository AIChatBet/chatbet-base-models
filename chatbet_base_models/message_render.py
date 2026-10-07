"""Single render engine for message-template text.

Used by the Backoffice (preview) and Channel Services (sending), so the operator
sees exactly what the user receives.

Rules (decided with the product owner, 2026-10-07):
- An unresolved token stays RAW in the output, exactly as today, but it is now
  logged with company / key / token / channel instead of being swallowed.
- Rendering never raises and never blocks a send.
- Substituted values are never re-scanned (single pass), so a value that itself
  contains ``{x}`` or ``%1`` is emitted verbatim.
"""

import logging
from typing import Any, Callable, Dict, Mapping, Optional

from .message_tokens import build_scan_pattern

logger = logging.getLogger(__name__)

Escaper = Callable[[str], str]


def _identity(value: str) -> str:
    return value


# Escaping per channel does not exist in production today (verified 2026-10-07),
# so every channel starts as identity: shipping this changes no user-visible
# text. Real rules are added here, per channel, with their own tests.
CHANNEL_ESCAPERS: Dict[str, Escaper] = {
    "telegram": _identity,
    "whatsapp": _identity,
    "web": _identity,
}


def _log_extra(
    company: str, key: str, token: Optional[str], channel: str
) -> Dict[str, Any]:
    return {
        "msg_company": company,
        "msg_key": key,
        "msg_token": token,
        "msg_channel": channel,
    }


def render(
    text: Optional[str],
    values: Optional[Mapping[str, Any]],
    *,
    channel: str,
    company: str,
    key: str,
    legacy_tokens: Optional[Mapping[str, str]] = None,
) -> str:
    """Render ``text`` replacing ``{TOKEN}`` and declared legacy literals.

    ``legacy_tokens`` maps a literal (``%1``, ``%``, ``{{BET_REMOVED}}``) to the
    name of the value that fills it; it comes from the catalog entry of ``key``.
    """
    if not text:
        return ""
    try:
        return _render(text, values or {}, channel, company, key, legacy_tokens or {})
    except Exception:
        logger.error(
            "message render failed; returning the template text unrendered",
            extra=_log_extra(company, key, None, channel),
            exc_info=True,
        )
        return text


def _render(
    text: str,
    values: Mapping[str, Any],
    channel: str,
    company: str,
    key: str,
    legacy_tokens: Mapping[str, str],
) -> str:
    escape = CHANNEL_ESCAPERS.get(channel, _identity)
    pattern = build_scan_pattern(legacy_tokens)

    def substitute(match: Any) -> str:
        groups = match.groupdict()
        if groups.get("open"):
            return "{"
        if groups.get("close"):
            return "}"
        raw = match.group(0)
        name = legacy_tokens[raw] if groups.get("legacy") else groups["name"]
        value = values.get(name)
        if value is None:
            logger.warning(
                "unresolved message token left raw",
                extra=_log_extra(company, key, raw, channel),
            )
            return raw
        return escape(str(value))

    return pattern.sub(substitute, text)
