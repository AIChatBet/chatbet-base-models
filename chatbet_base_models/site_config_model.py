from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Any, Union, Annotated, Literal, List

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

# ==========================="
# Enums and basic types
# ==========================="


class OddType(str, Enum):
    AMERICAN = "american"
    DECIMAL = "decimal"


class ValidationMethod(str, Enum):
    PHONE = "phone"
    EMAIL = "email"


class TwilioAuthChannel(str, Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class ChatbetVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"


class HourFormat(str, Enum):
    H12 = "12h"
    H24 = "24h"


class AliasProbabilities(str, Enum):
    CUOTA = "cuota"
    MOMIO = "momio"
    ODD = "odd"


# ==========================="
# Mixins / Value Objects
# ==========================="


class MoneyLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min_bet_amount: Decimal = Field(ge=0)
    max_bet_amount: Decimal = Field(gt=0)

    @field_validator("min_bet_amount", "max_bet_amount", mode="before")
    @classmethod
    def _to_decimal(cls, v):
        if v is None:
            return v
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid amount: {v}") from e

    @field_validator("max_bet_amount")
    @classmethod
    def _max_gt_min(cls, v, info):
        min_val = info.data.get("min_bet_amount")
        if isinstance(min_val, Decimal) and v <= min_val:
            raise ValueError("max_bet_amount must be greater than min_bet_amount")
        return v


class TestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_number: Optional[str] = None
    email: Optional[str] = None
    otp: Optional[str] = None
    user_key: Optional[str] = None


class SessionConfig(BaseModel):
    """Configuration for user session management"""

    model_config = ConfigDict(extra="forbid")
    inactivity_threshold_minutes: int = Field(
        default=30,
        gt=0,
        description="User inactivity threshold in minutes",
    )


# ==========================="
# Integrations
# ==========================="


# Proveedor para WhatsApp
class WhatsAppProvider(str, Enum):
    WHAPI = "whapi"  # Proveedor WHAPI
    META = "meta"  # Meta/Cloud API oficial


class MeilisearchIndexPaths(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fixtures: str


class MeilisearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: HttpUrl
    token: str
    index: MeilisearchIndexPaths


class TwilioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    verify_service_sid: str
    auth_token: str
    account_sid: str
    authentication_type: Optional[TwilioAuthChannel] = None


class TelegramConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str
    webhook_url: Optional[str] = None


# Configuración WHAPI
class WhapiConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["whapi"] = Field(
        default="whapi", description="Discriminador de proveedor"
    )
    api_url: HttpUrl
    token: str


# Configuración WhatsApp Cloud API (Meta)
class WhatsAppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["meta"] = Field(
        default="meta", description="Discriminador de proveedor"
    )
    phone_id: str
    auth_token: str
    # Legacy fields (pre hub_verify_token migration) — kept Optional so existing
    # DynamoDB configs still validate while backoffice/bot migrate to the new
    # names. Remove once every stored config has been updated.
    connection_token: Optional[str] = None
    app_id: Optional[str] = None
    # Current fields for Meta webhook validation
    hub_verify_token: Optional[str] = None
    waba_id: Optional[str] = None
    webhook_url: Optional[str] = None


# Unión discriminada por el campo `provider`
WhatsAppUnion = Annotated[
    Union[WhapiConfig, WhatsAppConfig], Field(discriminator="provider")
]


# Wrapper con enable/disable + config
class WhatsAppIntegration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    config: WhatsAppUnion


class BitlyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bitly_url: Optional[HttpUrl] = None
    access_token: Optional[str] = None
    phone_number: Optional[str] = None
    initial_message: Optional[str] = None


class Integrations(BaseModel):
    model_config = ConfigDict(extra="forbid")
    telegram: Optional[TelegramConfig] = None
    twilio: Optional[TwilioConfig] = None
    meilisearch: Optional[MeilisearchConfig] = None
    bitly: Optional[BitlyConfig] = None

    # <-- CAMBIO: ahora `whatsapp`, no `whapi`
    whatsapp: Optional[WhatsAppIntegration] = None

    # Compat: si llega "whapi" en payloads viejos, lo mapeamos a "whatsapp"
    @model_validator(mode="before")
    @classmethod
    def _map_legacy_whapi(cls, values: Any) -> Any:
        if isinstance(values, dict) and "whapi" in values and "whatsapp" not in values:
            whapi_val = values.pop("whapi")
            # Aceptamos tanto forma simple como wrapper
            if whapi_val is None:
                values["whatsapp"] = None
            elif isinstance(whapi_val, dict) and (
                "enabled" in whapi_val or "config" in whapi_val
            ):
                # ya viene en formato wrapper
                values["whatsapp"] = whapi_val
            else:
                # lo envolvemos como enabled=True por defecto
                values["whatsapp"] = {"enabled": True, "config": whapi_val}
        return values


# ==========================="
# Personality Config
# ==========================="


class PersonalityArchetype(str, Enum):
    FRIENDLY_EXPERT = "friendly_expert"
    ENTHUSIASTIC_FAN = "enthusiastic_fan"
    COOL_ANALYST = "cool_analyst"
    MOTIVATIONAL_COACH = "motivational_coach"


import re as _re

_HTML_PATTERN = _re.compile(r"<[^>]+>|javascript\s*:|on\w+\s*=", _re.IGNORECASE)


def _reject_html(value: str, field: str) -> str:
    if _HTML_PATTERN.search(value):
        raise ValueError(f"{field} must not contain HTML tags or scripts")
    return value


class PersonalityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bot_name: str = Field(default="ChatBet", min_length=2, max_length=20)
    formality_level: int = Field(default=2, ge=1, le=5)
    emoji_level: int = Field(default=2, ge=1, le=3)
    response_length: int = Field(default=1, ge=1, le=3)
    personality_archetype: PersonalityArchetype = Field(
        default=PersonalityArchetype.FRIENDLY_EXPERT
    )
    welcome_message: Optional[str] = Field(default=None, max_length=500)
    waiting_phrases: Optional[List[str]] = Field(default=None)

    @field_validator("bot_name")
    @classmethod
    def _validate_bot_name(cls, v):
        return _reject_html(v, "bot_name")

    @field_validator("welcome_message")
    @classmethod
    def _validate_welcome_message(cls, v):
        if v is None:
            return v
        return _reject_html(v, "welcome_message")

    @field_validator("waiting_phrases")
    @classmethod
    def _validate_waiting_phrases(cls, v):
        if v is None:
            return v
        if not (3 <= len(v) <= 5):
            raise ValueError("waiting_phrases must have between 3 and 5 items")
        for phrase in v:
            if len(phrase) > 100:
                raise ValueError("Each waiting phrase must be at most 100 characters")
            _reject_html(phrase, "waiting_phrases")
        return v


# ==========================="
# Top-level sections
# ==========================="


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    site_name: str
    company_id: str
    site_url: HttpUrl


class LocaleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: str = Field(min_length=3, max_length=3, description="ISO-4217")
    currency_symbol: str = Field(min_length=1, max_length=3)
    language: str = Field(
        min_length=2, max_length=5, description="IETF BCP 47 e.g., 'en', 'es-MX'"
    )
    country: str = Field(min_length=2, max_length=2, description="ISO-3166-1 alpha-2")
    country_code: str = Field(
        min_length=2, max_length=4, description="Phone prefix e.g., +52"
    )
    time_zone: str
    default_amount: Optional[str] = None
    default_desired_profit: Optional[str] = None
    default_minimum_odds: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def _upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("country")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.upper()

    @field_validator("language")
    @classmethod
    def _lower_lang(cls, v: str) -> str:
        return v.lower()


class FeaturesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    odd_type: OddType
    alias_probabilities: AliasProbabilities = Field(
        default=AliasProbabilities.ODD,
        description="Terminology for displaying odds/probabilities",
    )
    validation: ValidationMethod
    combos: bool = Field(description="Enable or disable combos in this configuration")
    chatbet_version: Optional[ChatbetVersion] = None
    multigames_response: Optional[bool] = Field(
        description="Enable or disable multi-games response"
    )
    see_in_combo: Optional[bool] = Field(description="Enable or disable combos")
    hour_format: HourFormat = Field(
        default=HourFormat.H24,
        description="Hour display format: '12h' or '24h'",
    )
    skip_pre_auth_validation: Optional[bool] = Field(
        default=False,
        description="Skip validate_user calls before OTP flow (for providers that need a token to validate, e.g. Plannatech)",
    )
    live: Optional[bool] = Field(
        default=False,
        description="Enable or disable live in this configuration",
    )
    whatsapp_detected_login: Optional[bool] = Field(
        default=False,
        description="Enable WhatsApp detected-number login confirm screen (per-company rollout). When False, WhatsApp users keep the type-the-number flow.",
    )
    fixture_range_days: Optional[int] = Field(
        default=7,
        ge=1,
        le=365,
        description=(
            "Window in days for DynamoDB fixture listing queries. "
            "Wider values let long-horizon tournaments (e.g. World Cup) "
            "surface earlier; narrower values keep result sets smaller. "
            "Default 7 preserves legacy behavior."
        ),
    )


class Meta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================="
# Auth Config
# ==========================="


class AuthConfig(BaseModel):
    """Operator-level authentication configuration.

    Defaults to OTP for backward compatibility with existing operators.
    When ``method == "password"``, ``flow_id`` is required and the
    operator's WhatsApp provider must be ``meta`` (Cloud API). The
    provider compatibility check lives on ``SiteConfig`` because it
    needs access to the sibling ``integrations`` block.
    """

    model_config = ConfigDict(extra="forbid")

    method: Literal["otp", "password"] = Field(
        default="otp",
        description="Auth method: 'otp' (legacy default) or 'password' (WhatsApp Flow form)",
    )
    flow_id: str | None = Field(
        default=None,
        description="Meta WhatsApp Flow ID (required when method='password')",
    )
    forgot_password_url: HttpUrl | None = Field(
        default=None,
        description="Optional forgot-password URL — reserved for Phase 2 (deferred).",
    )


# ==========================="
# General Config (no core wrapper)
# ==========================="


class SiteConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: Identity
    locale: LocaleConfig = Field(
        default_factory=lambda: LocaleConfig(
            currency="USD",
            currency_symbol="$",
            language="en",
            country="US",
            country_code="+1",
            time_zone="UTC",
            default_amount="",
            default_desired_profit="",
            default_minimum_odds="",
        )
    )
    features: FeaturesConfig = Field(
        default_factory=lambda: FeaturesConfig(
            odd_type=OddType.DECIMAL,
            alias_probabilities=AliasProbabilities.ODD,
            validation=ValidationMethod.EMAIL,
            combos=False,
            chatbet_version=ChatbetVersion.V1,
            multigames_response=False,
            see_in_combo=False,
            hour_format=HourFormat.H24,
            skip_pre_auth_validation=False,
            live=False,
            whatsapp_detected_login=False,
            fixture_range_days=7,
        )
    )
    limits: MoneyLimits = Field(
        default_factory=lambda: MoneyLimits(
            min_bet_amount=Decimal("1.00"), max_bet_amount=Decimal("1000.00")
        )
    )
    test: Optional[TestConfig] = Field(
        default_factory=lambda: TestConfig(
            phone_number="", email="", otp="123456", user_key="testuser"
        )
    )
    session: SessionConfig = Field(
        default_factory=SessionConfig, description="Session configuration settings"
    )
    personality: Optional[PersonalityConfig] = Field(default_factory=PersonalityConfig)
    integrations: Integrations = Field(
        default_factory=lambda: Integrations(
            telegram=TelegramConfig(token=""),
            twilio=TwilioConfig(verify_service_sid="", auth_token="", account_sid=""),
            whatsapp=WhatsAppIntegration(
                enabled=True,
                config=WhapiConfig(api_url="https://placeholder.com", token=""),
            ),
            meilisearch=MeilisearchConfig(
                url="https://placeholder.com",
                token="",
                index=MeilisearchIndexPaths(fixtures="fixtures_index"),
            ),
            bitly=BitlyConfig(
                bitly_url="https://api-ssl.bitly.com/v4",
                access_token="",
                phone_number="",
                initial_message="",
            ),
        )
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for public endpoints"
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description=(
            "Operator-level auth configuration. Default factory ⇒ method='otp' so "
            "operators without an explicit auth block keep the legacy OTP path."
        ),
    )

    @model_validator(mode="after")
    def _validate_auth_compatibility(self) -> "SiteConfig":
        """Cross-field validation between ``auth`` and ``integrations``.

        Two rules:
        1. ``auth.method == 'password'`` requires ``auth.flow_id`` to be set
           (Meta WhatsApp Flows cannot be sent without a published flow id).
        2. ``auth.method == 'password'`` is incompatible with WhatsApp
           provider ``whapi`` — Flow messages (``interactive.type='flow'``)
           require Cloud API (``provider='meta'``). Skipped when no
           WhatsApp integration is configured at all.
        """
        if self.auth.method != "password":
            return self

        if self.auth.flow_id is None:
            raise ValueError(
                "auth.method='password' requires auth.flow_id to be set"
            )

        whatsapp = self.integrations.whatsapp if self.integrations else None
        if whatsapp is None:
            # No WhatsApp configured — nothing to validate against.
            return self

        provider = getattr(whatsapp.config, "provider", None)
        if provider == "whapi":
            raise ValueError(
                "auth.method='password' is incompatible with WhatsApp "
                "provider 'whapi' — Flows require WhatsApp Cloud API "
                "(provider='meta')"
            )

        return self

    @classmethod
    def default_factory(cls, site_name: str, company_id: str) -> SiteConfig:
        identity = Identity(
            site_name=site_name, company_id=company_id, site_url="https://default.url"
        )
        return cls(identity=identity)


class SiteConfigDB(SiteConfig):
    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @classmethod
    def default_factory(cls, site_name: str, company_id: str) -> SiteConfigDB:
        base = SiteConfig.default_factory(site_name, company_id)
        return cls(**base.model_dump(), PK=f"company#{company_id}", SK="site_config")

    def to_dynamodb_item(self) -> dict:
        def serialize(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, HttpUrl):
                return str(obj)
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, "model_dump"):
                return serialize(obj.model_dump())
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize(v) for v in obj]
            return obj  # primitive types

        return serialize(self.model_dump())
