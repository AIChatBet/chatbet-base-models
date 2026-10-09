"""The flow types are importable from the package root."""

import chatbet_base_models as models

FLOW_PUBLIC_NAMES = [
    "ButtonDestination",
    "ParamDef",
    "DestinationDef",
    "DestinationCatalog",
    "RenderedAction",
    "render_destination",
    "find_destination_problems",
    "EventDef",
    "EventCatalog",
    "ClientFlow",
    "find_event_catalog_problems",
    "find_flow_problems",
]


def test_flow_types_are_exported_from_the_package_root():
    for name in FLOW_PUBLIC_NAMES:
        assert hasattr(models, name), name
        assert name in models.__all__, name
