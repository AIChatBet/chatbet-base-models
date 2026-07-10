import pytest
from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError

from chatbet_base_models.site_config_model import (
    OddType,
    ValidationMethod,
    TwilioAuthChannel,
    ChatbetVersion,
    AliasProbabilities,
    MoneyLimits,
    TestConfig,
    SessionConfig,
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
    AuthConfig,
    SiteConfig,
    SiteConfigDB,
    PersonalityConfig,
)


class TestEnums:
    def test_odd_type_enum(self):
        assert OddType.AMERICAN == "american"
        assert OddType.DECIMAL == "decimal"

    def test_validation_method_enum(self):
        assert ValidationMethod.PHONE == "phone"
        assert ValidationMethod.EMAIL == "email"

    def test_twilio_auth_channel_enum(self):
        assert TwilioAuthChannel.SMS == "sms"
        assert TwilioAuthChannel.WHATSAPP == "whatsapp"
        assert TwilioAuthChannel.EMAIL == "email"

    def test_chatbet_version_enum(self):
        assert ChatbetVersion.V1 == "v1"
        assert ChatbetVersion.V2 == "v2"

    def test_whatsapp_provider_enum(self):
        assert WhatsAppProvider.WHAPI == "whapi"
        assert WhatsAppProvider.META == "meta"

    def test_alias_probabilities_enum(self):
        assert AliasProbabilities.CUOTA == "cuota"
        assert AliasProbabilities.MOMIO == "momio"
        assert AliasProbabilities.ODD == "odd"


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


class TestSessionConfig:
    def test_create_session_config_with_default(self):
        config = SessionConfig()
        assert config.inactivity_threshold_minutes == 30

    def test_create_session_config_with_custom_value(self):
        config = SessionConfig(inactivity_threshold_minutes=60)
        assert config.inactivity_threshold_minutes == 60

    def test_session_config_with_minimum_value(self):
        config = SessionConfig(inactivity_threshold_minutes=1)
        assert config.inactivity_threshold_minutes == 1

    def test_session_config_with_large_value(self):
        config = SessionConfig(inactivity_threshold_minutes=10080)  # 1 week
        assert config.inactivity_threshold_minutes == 10080

    def test_zero_threshold_raises_error(self):
        with pytest.raises(ValueError):
            SessionConfig(inactivity_threshold_minutes=0)

    def test_negative_threshold_raises_error(self):
        with pytest.raises(ValueError):
            SessionConfig(inactivity_threshold_minutes=-10)

    def test_session_config_serialization(self):
        config = SessionConfig(inactivity_threshold_minutes=45)
        data = config.model_dump()
        assert data["inactivity_threshold_minutes"] == 45


class TestIntegrationConfigs:
    def test_meilisearch_index_paths(self):
        paths = MeilisearchIndexPaths(fixtures="fixture_idx")
        assert paths.fixtures == "fixture_idx"

    def test_meilisearch_config(self):
        config = MeilisearchConfig(
            url="https://search.example.com",
            token="search_token",
            index=MeilisearchIndexPaths(fixtures="fixtures"),
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

    def test_twilio_config_without_authentication_type(self):
        config = TwilioConfig(
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
        )
        assert config.authentication_type is None

    def test_twilio_config_with_authentication_type_sms(self):
        config = TwilioConfig(
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
            authentication_type="sms",
        )
        assert config.authentication_type == TwilioAuthChannel.SMS

    def test_twilio_config_with_authentication_type_whatsapp(self):
        config = TwilioConfig(
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
            authentication_type="whatsapp",
        )
        assert config.authentication_type == TwilioAuthChannel.WHATSAPP

    def test_twilio_config_with_authentication_type_email(self):
        config = TwilioConfig(
            verify_service_sid="VAxxxxxxx",
            auth_token="auth_token",
            account_sid="ACxxxxxxx",
            authentication_type="email",
        )
        assert config.authentication_type == TwilioAuthChannel.EMAIL

    def test_twilio_config_invalid_authentication_type(self):
        with pytest.raises(ValueError):
            TwilioConfig(
                verify_service_sid="VAxxxxxxx",
                auth_token="auth_token",
                account_sid="ACxxxxxxx",
                authentication_type="telegram",
            )

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
            phone_id="phone123", auth_token="auth_token", hub_verify_token="verify_token"
        )
        assert config.provider == "meta"
        assert config.phone_id == "phone123"
        assert config.auth_token == "auth_token"
        assert config.hub_verify_token == "verify_token"
        assert config.waba_id is None
        assert config.webhook_url is None

    def test_whatsapp_config_with_optional_fields(self):
        config = WhatsAppConfig(
            phone_id="phone123",
            auth_token="auth_token",
            hub_verify_token="verify_token",
            waba_id="waba123",
            webhook_url="https://example.com/webhook",
        )
        assert config.hub_verify_token == "verify_token"
        assert config.waba_id == "waba123"
        assert config.webhook_url == "https://example.com/webhook"


class TestWhatsAppIntegration:
    def test_whatsapp_integration_with_whapi(self):
        whapi_config = WhapiConfig(api_url="https://whapi.example.com", token="token")
        integration = WhatsAppIntegration(config=whapi_config)
        assert integration.enabled is True
        assert integration.config.provider == "whapi"

    def test_whatsapp_integration_with_meta(self):
        meta_config = WhatsAppConfig(
            phone_id="phone123", auth_token="auth_token"
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


class TestPersonalityConfig:
    def test_default_bot_name_is_empty(self):
        personality = PersonalityConfig()
        assert personality.bot_name == ""

    def test_accepts_empty_bot_name(self):
        personality = PersonalityConfig(bot_name="")
        assert personality.bot_name == ""

    def test_accepts_single_char_bot_name(self):
        personality = PersonalityConfig(bot_name="X")
        assert personality.bot_name == "X"

    def test_rejects_bot_name_over_max_length(self):
        with pytest.raises(ValidationError):
            PersonalityConfig(bot_name="x" * 21)

    def test_rejects_html_in_bot_name(self):
        with pytest.raises(ValueError):
            PersonalityConfig(bot_name="<script>alert(1)</script>")


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

    def test_features_config_default_alias_probabilities(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
        )
        assert features.alias_probabilities == AliasProbabilities.ODD

    def test_features_config_with_custom_alias_probabilities(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            alias_probabilities=AliasProbabilities.CUOTA,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
        )
        assert features.alias_probabilities == AliasProbabilities.CUOTA

        features_momio = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            alias_probabilities=AliasProbabilities.MOMIO,
            validation=ValidationMethod.EMAIL,
            combos=False,
            chatbet_version=ChatbetVersion.V1,
            multigames_response=False,
            see_in_combo=False,
        )
        assert features_momio.alias_probabilities == AliasProbabilities.MOMIO

    def test_features_config_default_fixture_range_days(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
        )
        assert features.fixture_range_days == 7

    def test_features_config_custom_fixture_range_days(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
            fixture_range_days=30,
        )
        assert features.fixture_range_days == 30

    def test_features_config_invalid_fixture_range_days(self):
        from pydantic import ValidationError

        for invalid in (0, -1, 366, 1000):
            with pytest.raises(ValidationError):
                FeaturesConfig(
                    odd_type=OddType.DECIMAL,
                    validation=ValidationMethod.EMAIL,
                    combos=True,
                    chatbet_version=ChatbetVersion.V2,
                    multigames_response=True,
                    see_in_combo=True,
                    fixture_range_days=invalid,
                )

    def test_features_config_default_whatsapp_detected_login(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
        )
        assert features.whatsapp_detected_login is False

    def test_features_config_whatsapp_detected_login_enabled(self):
        features = FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=True,
            chatbet_version=ChatbetVersion.V2,
            multigames_response=True,
            see_in_combo=True,
            whatsapp_detected_login=True,
        )
        assert features.whatsapp_detected_login is True

    def test_features_config_whatsapp_detected_login_round_trip(self):
        features = FeaturesConfig.model_validate(
            {
                "odd_type": OddType.DECIMAL,
                "validation": ValidationMethod.EMAIL,
                "combos": True,
                "chatbet_version": ChatbetVersion.V2,
                "multigames_response": True,
                "see_in_combo": True,
                "whatsapp_detected_login": True,
            }
        )
        assert features.whatsapp_detected_login is True
        assert features.model_dump()["whatsapp_detected_login"] is True


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
        assert config.session is not None
        assert config.session.inactivity_threshold_minutes == 30
        assert config.integrations is not None

    def test_default_factory(self):
        config = SiteConfig.default_factory("Test Site", "test123")
        assert config.identity.site_name == "Test Site"
        assert config.identity.company_id == "test123"
        assert str(config.identity.site_url) == "https://default.url/"

    def test_site_config_with_custom_session(self):
        identity = Identity(
            site_name="Test Site",
            company_id="test123",
            site_url="https://test.example.com",
        )
        config = SiteConfig(
            identity=identity, session=SessionConfig(inactivity_threshold_minutes=60)
        )
        assert config.session.inactivity_threshold_minutes == 60


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
        assert "session" in item

        # Check serialization
        assert isinstance(item["created_at"], str)  # datetime as ISO string
        assert isinstance(item["identity"]["site_url"], str)  # HttpUrl as string
        assert item["features"]["odd_type"] == "decimal"  # Enum as value
        assert item["locale"]["currency"] == "USD"
        assert item["session"]["inactivity_threshold_minutes"] == 30  # Default value

        # Check nested structures
        assert "integrations" in item
        assert "telegram" in item["integrations"]
        # Decimal is kept as Decimal object in DynamoDB serialization
        # assert isinstance(item["limits"]["min_bet_amount"], str)  # Decimal as string

    def test_to_dynamodb_item_with_authentication_type(self):
        config_db = SiteConfigDB.default_factory("Test Site", "test123")
        config_db.integrations.twilio.authentication_type = TwilioAuthChannel.WHATSAPP
        item = config_db.to_dynamodb_item()

        assert item["integrations"]["twilio"]["authentication_type"] == "whatsapp"

    def test_to_dynamodb_item_without_authentication_type(self):
        config_db = SiteConfigDB.default_factory("Test Site", "test123")
        item = config_db.to_dynamodb_item()

        assert item["integrations"]["twilio"]["authentication_type"] is None


# ==========================="
# AuthConfig + SiteConfig auth validators
# ==========================="


def _identity_factory():
    return Identity(
        site_name="Test Site",
        company_id="test123",
        site_url="https://test.example.com",
    )


def _meta_whatsapp_integration():
    """WhatsApp integration with Meta Cloud API provider (compatible with password)."""
    return WhatsAppIntegration(
        enabled=True,
        config=WhatsAppConfig(
            provider="meta",
            phone_id="phone-123",
            auth_token="token-abc",
        ),
    )


def _whapi_whatsapp_integration():
    """WhatsApp integration with WHAPI provider (incompatible with password)."""
    return WhatsAppIntegration(
        enabled=True,
        config=WhapiConfig(
            provider="whapi",
            api_url="https://placeholder.com",
            token="",
        ),
    )


def _site_config_with_integrations(*, whatsapp=None, **overrides) -> SiteConfig:
    """Build a SiteConfig with explicit Integrations (whatsapp can be None or absent)."""
    integrations_kwargs = {}
    if whatsapp is not None:
        integrations_kwargs["whatsapp"] = whatsapp
    integrations = Integrations(**integrations_kwargs)
    return SiteConfig(
        identity=_identity_factory(),
        integrations=integrations,
        **overrides,
    )


class TestAuthConfig:
    """Unit tests for the AuthConfig model itself (no SiteConfig context)."""

    def test_auth_config_defaults_otp_for_backward_compat(self):
        """1) Default AuthConfig() ⇒ method='otp', flow_id=None, forgot_password_url=None."""
        cfg = AuthConfig()
        assert cfg.method == "otp"
        assert cfg.flow_id is None
        assert cfg.forgot_password_url is None

    def test_auth_config_explicit_otp(self):
        cfg = AuthConfig(method="otp")
        assert cfg.method == "otp"
        assert cfg.flow_id is None

    def test_auth_config_password_with_flow_id_parses(self):
        """2) AuthConfig(method='password', flow_id='123456') parses fine."""
        cfg = AuthConfig(method="password", flow_id="123456")
        assert cfg.method == "password"
        assert cfg.flow_id == "123456"
        assert cfg.forgot_password_url is None

    def test_auth_config_invalid_method_rejected(self):
        """3) AuthConfig(method='magic_link') raises ValidationError (Literal violation)."""
        with pytest.raises(ValidationError):
            AuthConfig(method="magic_link")

    def test_auth_config_forgot_password_url_accepts_https(self):
        cfg = AuthConfig(forgot_password_url="https://example.com/forgot")
        assert str(cfg.forgot_password_url) == "https://example.com/forgot"

    def test_auth_config_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AuthConfig(method="otp", unexpected="x")


class TestSiteConfigAuthBackwardCompat:
    """SiteConfig must default to OTP when no auth block is supplied."""

    def test_site_config_without_auth_defaults_to_otp(self):
        """4) SiteConfig(...without auth...) ⇒ site.auth.method == 'otp'."""
        config = SiteConfig(identity=_identity_factory())
        assert config.auth is not None
        assert config.auth.method == "otp"
        assert config.auth.flow_id is None

    def test_site_config_default_factory_keeps_otp_default(self):
        config = SiteConfig.default_factory("Test Site", "test123")
        assert config.auth.method == "otp"


class TestSiteConfigAuthValidators:
    """SiteConfig.model_validator(after) covering password/whapi/flow_id rules."""

    def test_password_with_meta_provider_parses(self):
        """5) auth.method='password' + flow_id + provider='meta' → parses fine."""
        config = _site_config_with_integrations(
            whatsapp=_meta_whatsapp_integration(),
            auth=AuthConfig(method="password", flow_id="flow-123"),
        )
        assert config.auth.method == "password"
        assert config.auth.flow_id == "flow-123"
        # Confirm sibling integrations is intact (provider visible)
        assert config.integrations.whatsapp.config.provider == "meta"

    def test_password_with_whapi_provider_rejected(self):
        """6) auth.method='password' + provider='whapi' → ValidationError mentioning 'whapi' and 'Cloud API'."""
        with pytest.raises(ValidationError) as exc_info:
            _site_config_with_integrations(
                whatsapp=_whapi_whatsapp_integration(),
                auth=AuthConfig(method="password", flow_id="flow-123"),
            )

        msg = str(exc_info.value)
        assert "whapi" in msg
        assert "Cloud API" in msg

    def test_password_without_flow_id_rejected(self):
        """7) auth.method='password' + no flow_id → ValidationError mentioning 'flow_id'."""
        with pytest.raises(ValidationError) as exc_info:
            _site_config_with_integrations(
                whatsapp=_meta_whatsapp_integration(),
                auth=AuthConfig(method="password"),
            )

        msg = str(exc_info.value)
        assert "flow_id" in msg

    def test_password_without_whatsapp_integration_passes(self):
        """8) No `integrations.whatsapp` block + auth.method='password' + flow_id set → parses (whapi check skipped)."""
        config = _site_config_with_integrations(
            whatsapp=None,
            auth=AuthConfig(method="password", flow_id="flow-123"),
        )
        assert config.auth.method == "password"
        assert config.integrations.whatsapp is None

    def test_otp_method_with_whapi_is_unaffected(self):
        """OTP operators with whapi must remain valid (regression guard)."""
        config = _site_config_with_integrations(
            whatsapp=_whapi_whatsapp_integration(),
            auth=AuthConfig(method="otp"),
        )
        assert config.auth.method == "otp"
        assert config.integrations.whatsapp.config.provider == "whapi"

    def test_legacy_config_without_auth_block_with_whapi_passes(self):
        """Pre-existing operators (no auth block, whapi provider) must keep working."""
        config = _site_config_with_integrations(
            whatsapp=_whapi_whatsapp_integration(),
        )
        assert config.auth.method == "otp"
        assert config.integrations.whatsapp.config.provider == "whapi"
