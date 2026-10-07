"""The catalog types are importable from the package root."""

import chatbet_base_models as models

CATALOG_PUBLIC_NAMES = [
    "CatalogEntry",
    "ClientMessages",
    "LegacyConversion",
    "MessageCatalog",
    "MessageContent",
    "legacy_to_client_messages",
    "DEFAULT_ACCOUNT_STATE",
]


def test_catalog_types_are_exported_from_the_package_root():
    for name in CATALOG_PUBLIC_NAMES:
        assert hasattr(models, name), name
        assert name in models.__all__, name


def test_account_state_defaults_constant_covers_the_localized_fallbacks():
    assert "session_expired" in models.DEFAULT_ACCOUNT_STATE
    assert set(models.DEFAULT_ACCOUNT_STATE["session_expired"]) >= {"es", "en", "pt-br"}
