"""Regenerate chatbet_base_models/flow_rules/_generated.py from the channel.

Run from the repo root:

    python -m scripts.extract_flow_catalog --channel-src ../chatbet-channel/src
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from chatbet_base_models.flow_rules.extract import (
    catalog_from_registry,
    policy_from_registry,
    render_generated_module,
)

GENERATED_PATH = (
    Path(__file__).resolve().parent.parent / "chatbet_base_models" / "flow_rules" / "_generated.py"
)
REGISTRY_MODULE = "channel_services.composition.root"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel-src", required=True, type=Path, help="chatbet-channel/src")
    args = parser.parse_args()

    sys.path.insert(0, str(args.channel_src.resolve()))
    registry = importlib.import_module(REGISTRY_MODULE).build_registry()

    GENERATED_PATH.write_text(
        render_generated_module(catalog_from_registry(registry), policy_from_registry(registry)),
        encoding="utf-8",
    )
    print(f"wrote {GENERATED_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
