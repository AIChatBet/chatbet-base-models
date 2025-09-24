from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Any, Union, Annotated, Literal

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


class ChatbetVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"


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


# ==========================="
# Integrations
# ==========================="


# Proveedor para WhatsApp
class WhatsAppProvider(str, Enum):
    WHAPI = "whapi"  # Proveedor WHAPI
    META = "meta"  # Meta/Cloud API oficial


class MeilisearchIndexPaths(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fixtures: str
    sports: str


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
    connection_token: str
    app_id: Optional[str] = None  # Optional for backward compatibility
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


class Integrations(BaseModel):
    model_config = ConfigDict(extra="forbid")
    telegram: Optional[TelegramConfig] = None
    twilio: Optional[TwilioConfig] = None
    meilisearch: Optional[MeilisearchConfig] = None

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
    validation: ValidationMethod
    combos: bool = Field(description="Enable or disable combos in this configuration")
    chatbet_version: ChatbetVersion
    multigames_response: Optional[bool] = Field(description="Enable or disable multi-games response")


class Meta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
        )
    )
    features: FeaturesConfig = Field(
        default_factory=lambda: FeaturesConfig(
            odd_type=OddType.DECIMAL,
            validation=ValidationMethod.EMAIL,
            combos=False,
            chatbet_version=ChatbetVersion.V1,
            multigames_response=False,
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
                index=MeilisearchIndexPaths(
                    fixtures="fixtures_index", sports="sports_index"
                ),
            ),
        )
    )

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
