from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional, Union, Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    model_validator,
    WebsocketUrl,
)


# ===========================
# Tournament hierarchy
# ===========================
class Competition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    order: int = Field(default=999_999)


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: Optional[str] = None
    competitions: List[Competition]
    order: int = Field(default=999_999)


class Tournament(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sport_id: str
    sport_name: str
    main_market: Optional[str] = None
    regions: List[Region]
    stake_types: Optional[List[StakeType]] = Field(
        default_factory=lambda: _default_stake_types()
    )
    order: int = Field(default=999_999)


# ===========================
# Providers (configs)
# ===========================
class Betsw3Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["betsw3"] = "betsw3"
    userId: str
    siteId: str
    platformId: str
    language: str
    source: str
    currency: str
    access_token: str
    url: HttpUrl


class DigitainConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["digitain"] = "digitain"
    partner_id: str
    client_id: str
    client_secret: str
    token_url: HttpUrl
    websocket_url: WebsocketUrl
    validate_user_url: HttpUrl
    place_bet_url: HttpUrl


class PhoenixBasicAuth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


class PhoenixConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["phoenix"] = "phoenix"
    cluster_api_key: str
    security_protocol: str
    bootstrap_servers: str
    group_id: str
    mechanisms: str
    cluster_api_secret: str
    origin_id: str
    url: HttpUrl = "https://placeholder.com/"
    basic_auth: PhoenixBasicAuth
    last_state_epoch: str | int
    integration_state: str


ConfigUnion = Annotated[
    Union[Betsw3Config, DigitainConfig, PhoenixConfig], Field(discriminator="provider")
]


# ===========================
# Stake Types
# ===========================
class StakeType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    key: Optional[str] = None
    name: str
    order: int = Field(default=999_999)


# ===========================
# SportbookConfig (core)
# ===========================
class SportbookConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # nombre tal y como lo has usado (lo mantengo "sportbook")
    sportbook: str
    config: ConfigUnion
    tournaments: List[Tournament] = Field(
        default_factory=lambda: _default_tournaments()
    )

    # timestamps por consistencia con tu SiteConfigDB (opcionales aquí)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ---------- Constructores con defaults ----------
    @classmethod
    def from_minimal_phoenix(
        cls,
        *,
        cluster_api_key: str = "",
        security_protocol: str = "",
        bootstrap_servers: str = "",
        group_id: str = "",
        mechanisms: str = "",
        cluster_api_secret: str = "",
        origin_id: str = "",
        url: str = "https://placeholder.com/",
        basic_auth: Optional[PhoenixBasicAuth] = None,
        last_state_epoch: str = "",
        integration_state: str = "",
        tournaments: Optional[List[Tournament]] = None,
    ) -> "SportbookConfig":
        cfg = PhoenixConfig(
            cluster_api_key=cluster_api_key,
            security_protocol=security_protocol,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            mechanisms=mechanisms,
            cluster_api_secret=cluster_api_secret,
            origin_id=origin_id,
            url=url,
            basic_auth=basic_auth or PhoenixBasicAuth(username="", password=""),
            last_state_epoch=last_state_epoch,
            integration_state=integration_state,
        )
        now = datetime.now(timezone.utc)
        return cls(
            sportbook="Phoenix",
            config=cfg,
            tournaments=tournaments or _default_tournaments(),
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_minimal_betsw3(
        cls,
        *,
        userId: str = "",
        siteId: str = "",
        platformId: str = "",
        language: str = "en",
        source: str = "web",
        currency: str = "USD",
        access_token: str = "",
        url: str = "https://placeholder.com/",
        tournaments: Optional[List[Tournament]] = None,
    ) -> "SportbookConfig":
        cfg = Betsw3Config(
            userId=userId,
            siteId=siteId,
            platformId=platformId,
            language=language,
            source=source,
            currency=currency,
            access_token=access_token,
            url=url,
        )
        now = datetime.now(timezone.utc)
        return cls(
            sportbook="Betsw3",
            config=cfg,
            tournaments=tournaments or _default_tournaments(),
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_minimal_digitain(
        cls,
        sportbook: str,
        *,
        partner_id: str,
        client_id: str,
        client_secret: str,
        token_url: str = "https://placeholder.com/token",
        websocket_url: str = "wss://placeholder.com/ws",
        validate_user_url: str = "https://placeholder.com/validate-user",
        place_bet_url: str = "https://placeholder.com/place-bet",
        tournaments: Optional[List[Tournament]] = None,
    ) -> "SportbookConfig":
        cfg = DigitainConfig(
            partner_id=partner_id,
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            websocket_url=websocket_url,
            validate_user_url=validate_user_url,
            place_bet_url=place_bet_url,
        )
        now = datetime.now(timezone.utc)
        return cls(
            sportbook="Digitain",
            config=cfg,
            tournaments=tournaments or _default_tournaments(),
            created_at=now,
            updated_at=now,
        )

    # ---------- utilidades ----------
    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """Serializa a un dict DynamoDB-friendly.
        - datetime -> ISO 8601
        - HttpUrl  -> str
        - Enum     -> value
        - Decimal  -> se mantiene (si llegase a existir)
        """
        from decimal import Decimal  # local para aclarar intención

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, HttpUrl):
                return str(x)
            if isinstance(x, Enum):
                return x.value
            if hasattr(x, "model_dump"):
                return ser(x.model_dump())
            if isinstance(x, dict):
                out = {k: ser(v) for k, v in x.items()}
                return {k: v for k, v in out.items() if not (drop_none and v is None)}
            if isinstance(x, list):
                return [ser(v) for v in x]
            # mantener Decimal, str, int, bool, None
            if isinstance(x, Decimal):
                return x
            return x

        return ser(self.model_dump())


# ===========================
# SportbookConfigDB (para DynamoDB)
# ===========================
class SportbookConfigDB(SportbookConfig):
    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal_phoenix(
        cls,
        company_id: str,
        **kwargs,
    ) -> "SportbookConfigDB":
        base = SportbookConfig.from_minimal_phoenix(**kwargs)
        return cls(
            **base.model_dump(), PK=f"company#{company_id}", SK="sportbook_config"
        )

    @classmethod
    def from_minimal_betsw3(
        cls,
        company_id: str,
        **kwargs,
    ) -> "SportbookConfigDB":
        base = SportbookConfig.from_minimal_betsw3(**kwargs)
        return cls(
            **base.model_dump(), PK=f"company#{company_id}", SK="sportbook_config"
        )

    @classmethod
    def from_minimal_digitain(
        cls,
        company_id: str,
        **kwargs,
    ) -> "SportbookConfigDB":
        base = SportbookConfig.from_minimal_digitain(**kwargs)
        return cls(
            **base.model_dump(), PK=f"company#{company_id}", SK="sportbook_config"
        )

    @model_validator(mode="after")
    def _ensure_keys(self) -> "SportbookConfigDB":
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for SportbookConfigDB")
        return self

    # hereda touch() y to_dynamodb_item() tal cual


# ===========================
# Defaults helpers
# ===========================
def _default_tournaments() -> List[Tournament]:
    # Puedes ajustarlo a tus deportes/regiones por defecto reales
    return [
        Tournament(
            sport_id="soccer",
            sport_name="soccer",
            main_market="result",
            regions=[
                Region(
                    id="eu",
                    name="Europe",
                    competitions=[
                        Competition(id="1", name="UEFA Champions League"),
                        Competition(id="2", name="Premier League"),
                    ],
                ),
            ],
            stake_types=_default_stake_types(),
        ),
    ]


def _default_stake_types() -> List[StakeType]:
    return [
        StakeType(id="1", name="Result"),
        StakeType(id="2", name="Over/Under"),
    ]
