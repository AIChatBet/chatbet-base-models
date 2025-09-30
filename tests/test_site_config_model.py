import pytest
from datetime import datetime
from decimal import Decimal

from chatbet_base_models.site_config_model import (
    OddType,
    ValidationMethod,
    ChatbetVersion,
    MoneyLimits,
    TestConfig,
    WhatsAppProvider,
    MeilisearchIndexPaths,
    MeilisearchConfig,
    TwilioConfig,
    TelegramConfig,
    WhapiConfig,
    WhatsAppConfig,
    WhatsAppIntegration,
    Integrations,
    Identity,
    LocaleConfig,
    FeaturesConfig,
    Meta,
    SiteConfig,
    SiteConfigDB,
)


class TestEnums:
    def test_odd_type_enum(self):
        assert OddType.AMERICAN == "american"
        assert OddType.DECIMAL == "decimal"

    def test_validation_method_enum(self):
        assert ValidationMethod.PHONE == "phone"
        assert ValidationMethod.EMAIL == "email"

    def test_chatbet_version_enum(self):
        assert ChatbetVersion.V1 == "v1"
        assert ChatbetVersion.V2 == "v2"

    def test_whatsapp_provider_enum(self):
        assert WhatsAppProvider.WHAPI == "whapi"
        assert WhatsAppProvider.META == "meta"


class TestMoneyLimits:
    def test_create_money_limits(self):
        limits = MoneyLimits(
            min_bet_amount=Decimal("1.00"), max_bet_amount=Decimal("100.00")
        )
        assert limits.min_bet_amount == Decimal("1.00")
        assert limits.max_bet_amount == Decimal("100.00")

    def test_convert_string_to_decimal(self):
        limits = MoneyLimits(min_bet_amount="1.50", max_bet_amount="50.00")
        assert limits.min_bet_amount == Decimal("1.50")
        assert limits.max_bet_amount == Decimal("50.00")

    def test_convert_int_to_decimal(self):
        limits = MoneyLimits(min_bet_amount=1, max_bet_amount=100)
        assert limits.min_bet_amount == Decimal("1")
        assert limits.max_bet_amount == Decimal("100")

    def test_convert_float_to_decimal(self):
        limits = MoneyLimits(min_bet_amount=1.5, max_bet_amount=100.5)
        assert limits.min_bet_amount == Decimal("1.5")
        assert limits.max_bet_amount == Decimal("100.5")

    def test_invalid_amount_raises_error(self):
        with pytest.raises(ValueError, match="Invalid amount"):
            MoneyLimits(min_bet_amount="invalid", max_bet_amount="100")

    def test_negative_min_bet_raises_error(self):
        with pytest.raises(ValueError):
            MoneyLimits(min_bet_amount=Decimal("-1"), max_bet_amount=Decimal("100"))

    def test_zero_max_bet_raises_error(self):
        with pytest.raises(ValueError):
            MoneyLimits(min_bet_amount=Decimal("0"), max_bet_amount=Decimal("0"))

    def test_max_less_than_min_raises_error(self):
        with pytest.raises(
            ValueError, match="max_bet_amount must be greater than min_bet_amount"
        ):
            MoneyLimits(min_bet_amount=Decimal("100"), max_bet_amount=Decimal("50"))

    def test_max_equal_to_min_raises_error(self):
        with pytest.raises(
            ValueError, match="max_bet_amount must be greater than min_bet_amount"
        ):
            MoneyLimits(min_bet_amount=Decimal("100"), max_bet_amount=Decimal("100"))


class TestTestConfig:
    def test_create_test_config(self):
        config = TestConfig(
            phone_number="+1234567890",
            email="test@example.com",
            otp="123456",
            user_key="testuser",
        )
        assert config.phone_number == "+1234567890"
        assert config.email == "test@example.com"
        assert config.otp == "123456"
        assert config.user_key == "testuser"

    def test_create_empty_test_config(self):
        config = TestConfig()
        assert config.phone_number is None
        assert config.email is None
        assert config.otp is None
        assert config.user_key is None


class TestIntegrationConfigs:
    def test_meilisearch_index_paths(self):
        paths = MeilisearchIndexPaths(fixtures="fixture_idx", sports="sports_idx")
        assert paths.fixtures == "fixture_idx"
        assert paths.sports == "sports_idx"

    def test_meilisearch_config(self):
        config = MeilisearchConfig(
            url="https://search.example.com",
            token="search_token",
            index=MeilisearchIndexPaths(fixtures="fixtures", sports="sports"),
        )
        assert str(config.url) == "https://search.example.com/"
        assert config.token == "search_token"
        assert config.index.fixtures == "fixtures"

    def test_twilio_config(self):
        config = TwilioConfig(
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
        )
        assert config.enabled is True  # default
        assert config.verify_service_sid == "VAxxxxxxx"
        assert config.auth_token == "auth_token"
        assert config.account_sid == "ACxxxxxxx"

    def test_twilio_config_disabled(self):
        config = TwilioConfig(
            enabled=False,
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
        )
        assert config.enabled is False

    def test_telegram_config(self):
        config = TelegramConfig(token="bot_token")
        assert config.token == "bot_token"
        assert config.webhook_url is None

    def test_telegram_config_with_webhook(self):
        config = TelegramConfig(
            token="bot_token", webhook_url="https://example.com/webhook"
        )
        assert config.token == "bot_token"
        assert config.webhook_url == "https://example.com/webhook"

    def test_whapi_config(self):
        config = WhapiConfig(api_url="https://whapi.example.com", token="whapi_token")
        assert config.provider == "whapi"
        assert str(config.api_url) == "https://whapi.example.com/"
        assert config.token == "whapi_token"

    def test_whatsapp_config(self):
        config = WhatsAppConfig(
            phone_id="phone123", auth_token="auth_token", connection_token="conn_token"
        )
        assert config.provider == "meta"
        assert config.phone_id == "phone123"
        assert config.auth_token == "auth_token"
        assert config.connection_token == "conn_token"
        assert config.app_id is None
        assert config.webhook_url is None

    def test_whatsapp_config_with_optional_fields(self):
        config = WhatsAppConfig(
            phone_id="phone123",
            auth_token="auth_token",
            connection_token="conn_token",
            app_id="app123",
            webhook_url="https://example.com/webhook",
        )
        assert config.app_id == "app123"
        assert config.webhook_url == "https://example.com/webhook"


class TestWhatsAppIntegration:
    def test_whatsapp_integration_with_whapi(self):
        whapi_config = WhapiConfig(api_url="https://whapi.example.com", token="token")
        integration = WhatsAppIntegration(config=whapi_config)
        assert integration.enabled is True
        assert integration.config.provider == "whapi"

    def test_whatsapp_integration_with_meta(self):
        meta_config = WhatsAppConfig(
            phone_id="phone123", auth_token="auth_token", connection_token="conn_token"
        )
        integration = WhatsAppIntegration(enabled=False, config=meta_config)
        assert integration.enabled is False
        assert integration.config.provider == "meta"


class TestIntegrations:
    def test_create_empty_integrations(self):
        integrations = Integrations()
        assert integrations.telegram is None
        assert integrations.twilio is None
        assert integrations.meilisearch is None
        assert integrations.whatsapp is None

    def test_create_integrations_with_configs(self):
        integrations = Integrations(
            telegram=TelegramConfig(token="bot_token"),
            twilio=TwilioConfig(
                verify_service_sid="VAxxxxxxx",
                auth_token="auth_token",
                account_sid="ACxxxxxxx",
            ),
        )
        assert integrations.telegram is not None
        assert integrations.twilio is not None
        assert integrations.telegram.token == "bot_token"

    def test_legacy_whapi_mapping(self):
        # Test legacy "whapi" key gets mapped to "whatsapp"
        data = {
            "whapi": {
                "provider": "whapi",
                "api_url": "https://whapi.example.com/",
                "token": "token",
            }
        }
        integrations = Integrations.model_validate(data)
        assert integrations.whatsapp is not None
        assert integrations.whatsapp.enabled is True
        assert integrations.whatsapp.config.provider == "whapi"

    def test_legacy_whapi_with_wrapper_format(self):
        data = {
            "whapi": {
                "enabled": False,
                "config": {
                    "provider": "whapi",
                    "api_url": "https://whapi.example.com/",
                    "token": "token",
                },
            }
        }
        integrations = Integrations.model_validate(data)
        assert integrations.whatsapp is not None
        assert integrations.whatsapp.enabled is False
        assert integrations.whatsapp.config.provider == "whapi"

    def test_legacy_whapi_none_value(self):
        data = {"whapi": None}
        integrations = Integrations.model_validate(data)
        assert integrations.whatsapp is None


class TestIdentity:
    def test_create_identity(self):
        identity = Identity(
            site_name="ChatBet", company_id="chatbet123", site_url="https://chatbet.gg"
        )
        assert identity.site_name == "ChatBet"
        assert identity.company_id == "chatbet123"
        assert str(identity.site_url) == "https://chatbet.gg/"

    def test_invalid_url_raises_error(self):
        with pytest.raises(ValueError):
            Identity(site_name="ChatBet", company_id="chatbet123", site_url="not-a-url")


class TestLocaleConfig:
    def test_create_locale_config(self):
        locale = LocaleConfig(
            currency="usd",
            currency_symbol="$",
            language="EN-US",
            country="us",
            country_code="+1",
            time_zone="America/New_York",
        )
        assert locale.currency == "USD"  # Should be uppercase
        assert locale.currency_symbol == "$"
        assert locale.language == "en-us"  # Should be lowercase
        assert locale.country == "US"  # Should be uppercase
        assert locale.country_code == "+1"
        assert locale.time_zone == "America/New_York"

    def test_currency_validation(self):
        with pytest.raises(ValueError):
            LocaleConfig(
                currency="US",  # Too short
                currency_symbol="$",
                language="en",
                country="US",
                country_code="+1",
                time_zone="UTC",
            )

    def test_country_validation(self):
        with pytest.raises(ValueError):
            LocaleConfig(
                currency="USD",
                currency_symbol="$",
                language="en",
                country="USA",  # Too long
                country_code="+1",
                time_zone="UTC",
            )


class TestFeaturesConfig:
    def test_create_features_config(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
        )
        assert features.odd_type == OddType.DECIMAL
        assert features.validation == ValidationMethod.EMAIL
        assert features.combos is True
        assert features.chatbet_version == ChatbetVersion.V2
        assert features.multigames_response is True
        assert features.see_in_combo is True


class TestMeta:
    def test_create_meta_with_defaults(self):
        meta = Meta()
        assert meta.schema_version == "1.0.0"
        assert isinstance(meta.created_at, datetime)

    def test_create_meta_with_custom_values(self):
        custom_time = datetime.now()
        meta = Meta(schema_version="2.0.0", created_at=custom_time)
        assert meta.schema_version == "2.0.0"
        assert meta.created_at == custom_time


class TestSiteConfig:
    def test_create_site_config(self):
        identity = Identity(
            site_name="Test Site",
            company_id="test123",
            site_url="https://test.example.com",
        )
        config = SiteConfig(identity=identity)

        assert config.identity.site_name == "Test Site"
        # Check defaults are set
        assert config.locale.currency == "USD"
        assert config.features.odd_type == OddType.DECIMAL
        assert config.limits.min_bet_amount == Decimal("1.00")
        assert config.test is not None
        assert config.integrations is not None

    def test_default_factory(self):
        config = SiteConfig.default_factory("Test Site", "test123")
        assert config.identity.site_name == "Test Site"
        assert config.identity.company_id == "test123"
        assert str(config.identity.site_url) == "https://default.url/"


class TestSiteConfigDB:
    def test_create_site_config_db(self):
        identity = Identity(
            site_name="Test Site",
            company_id="test123",
            site_url="https://test.example.com",
        )
        config_db = SiteConfigDB(
            identity=identity, PK="company#test123", SK="site_config"
        )

        assert config_db.PK == "company#test123"
        assert config_db.SK == "site_config"
        assert isinstance(config_db.created_at, datetime)
        assert isinstance(config_db.updated_at, datetime)

    def test_default_factory(self):
        config_db = SiteConfigDB.default_factory("Test Site", "test123")
        assert config_db.PK == "company#test123"
        assert config_db.SK == "site_config"
        assert config_db.identity.site_name == "Test Site"
        assert config_db.identity.company_id == "test123"

    def test_to_dynamodb_item(self):
        config_db = SiteConfigDB.default_factory("Test Site", "test123")
        item = config_db.to_dynamodb_item()

        assert isinstance(item, dict)
        assert "PK" in item
        assert "SK" in item
        assert "identity" in item
        assert "locale" in item
        assert "features" in item

        # Check serialization
        assert isinstance(item["created_at"], str)  # datetime as ISO string
        assert isinstance(item["identity"]["site_url"], str)  # HttpUrl as string
        assert item["features"]["odd_type"] == "decimal"  # Enum as value
        assert item["locale"]["currency"] == "USD"

        # Check nested structures
        assert "integrations" in item
        assert "telegram" in item["integrations"]
        # Decimal is kept as Decimal object in DynamoDB serialization
        # assert isinstance(item["limits"]["min_bet_amount"], str)  # Decimal as string
