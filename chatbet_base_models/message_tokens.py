"""Shared scanner for ``{TOKEN}`` placeholders in message templates.

The Backoffice validators and the render engine both import this module, so a
token that validates when a template is saved is a token that renders when the
message is sent. ``{{`` and ``}}`` are escaped braces (same as ``str.format``)
and never count as tokens.
"""

import re
from typing import Iterable, Optional, Pattern, Set

TOKEN_NAME_PATTERN = r"[A-Za-z0-9_]+"


def build_scan_pattern(legacy_literals: Iterable[str] = ()) -> Pattern[str]:
    """Compile the single-pass scanner used by ``extract_tokens`` and ``render``.

    Named groups: ``legacy`` (a declared legacy literal such as ``%1``), ``open``
    (``{{``), ``close`` (``}}``) and ``name`` (a ``{TOKEN}`` name). Legacy
    literals are tried longest-first so ``%1`` wins over ``%``.
    """
    parts = []
    literals = sorted(set(legacy_literals), key=len, reverse=True)
    if literals:
        alternatives = "|".join(re.escape(literal) for literal in literals)
        parts.append(f"(?P<legacy>{alternatives})")
    parts.append(r"(?P<open>\{\{)")
    parts.append(r"(?P<close>\}\})")
    parts.append(r"\{(?P<name>" + TOKEN_NAME_PATTERN + r")\}")
    return re.compile("|".join(parts))


_PLAIN_PATTERN = build_scan_pattern()


def extract_tokens(text: Optional[str]) -> Set[str]:
    """Return the ``{TOKEN}`` names used in ``text`` (escaped braces ignored)."""
    if not text:
        return set()
    return {m.group("name") for m in _PLAIN_PATTERN.finditer(text) if m.group("name")}
