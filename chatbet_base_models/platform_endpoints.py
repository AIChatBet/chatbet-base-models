from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# =========================
# HTTP Method (seguro)
# =========================
class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


# ===============
# Endpoint Model
# ===============
class Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # method es opcional para permitir endpoints legacy sin método; si llega string libre lo normalizamos
    method: Optional[HTTPMethod] = None
    endpoint: HttpUrl
    params: Optional[Dict[str, str | bool | int | float]] = None
    payload: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

    @field_validator("method", mode="before")
    @classmethod
    def _normalize_method(cls, v):
        if v is None:
            return None
        if isinstance(v, HTTPMethod):
            return v
        # normalizar string libre a Enum si coincide
        s = str(v).strip().upper()
        if s in HTTPMethod.__members__:
            return HTTPMethod[s]
        # también aceptar valores como "post", "get", etc
        for m in HTTPMethod:
            if s == m.value:
                return m
        raise ValueError(f"Invalid HTTP method: {v}")


# ==========================
# Endpoint Group Models
# ==========================
class AuthEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    validate_user: Optional[Endpoint] = None
    validate_token: Optional[Endpoint] = None
    generate_token: Optional[Endpoint] = None
    generate_otp: Optional[Endpoint] = None


class UsersEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_user_balance: Optional[Endpoint] = None


class SportsEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_available_sports: Optional[Endpoint] = None
    list_sports: Optional[Endpoint] = None


class FixturesEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_fixtures_by_sport: Optional[Endpoint] = None
    get_fixtures_by_tournament: Optional[Endpoint] = None
    get_special_bets: Optional[Endpoint] = None
    get_recommended_bets: Optional[Endpoint] = None


class TournamentsEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_tournaments: Optional[Endpoint] = None


class OddsEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    get_fixture_odds: Optional[Endpoint] = None
    get_odds_combo: Optional[Endpoint] = None


class BetsEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    place_bet: Optional[Endpoint] = None


class CombosEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    place_combo: Optional[Endpoint] = None
    get_combo_profit: Optional[Endpoint] = None
    delete_bet_combo: Optional[Endpoint] = None
    add_bet_to_combo: Optional[Endpoint] = None
    get_odds_combo: Optional[Endpoint] = None


# ======================
# Unified Endpoints
# ======================
class APIEndpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auth: Optional[AuthEndpoints] = None
    users: Optional[UsersEndpoints] = None
    sports: Optional[SportsEndpoints] = None
    tournaments: Optional[TournamentsEndpoints] = None
    fixtures: Optional[FixturesEndpoints] = None
    odds: Optional[OddsEndpoints] = None
    bets: Optional[BetsEndpoints] = None
    combos: Optional[CombosEndpoints] = None


# =========================================================
# Versión DB con PK/SK + defaults y serialización DynamoDB
# =========================================================
class APIEndpointsDB(APIEndpoints):
    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # --- DEFAULT FACTORY ---
    @classmethod
    def default_factory(cls, company_id: str) -> "APIEndpointsDB":
        """
        Crea una configuración por defecto con endpoints de placeholder.
        No quedan campos NULL en DynamoDB: todas las hojas definen al menos url.
        """
        base_url = "https://placeholder.com/api"
        ws_base = "wss://placeholder.com/ws"

        def ep(url: str, method: HTTPMethod) -> Endpoint:
            return Endpoint(
                method=method,
                endpoint=url,  # HttpUrl
                params={},
                payload={},
                headers={},
            )

        defaults = APIEndpoints(
            auth=AuthEndpoints(
                validate_user=ep(f"{base_url}/auth/validate-user", HTTPMethod.POST),
                validate_token=ep(f"{base_url}/auth/validate-token", HTTPMethod.POST),
                generate_token=ep(f"{base_url}/auth/generate-token", HTTPMethod.POST),
            ),
            users=UsersEndpoints(
                get_user_balance=ep(f"{base_url}/users/get-balance", HTTPMethod.GET),
            ),
            sports=SportsEndpoints(
                get_available_sports=ep(f"{base_url}/sports/available", HTTPMethod.GET),
                list_sports=ep(f"{base_url}/sports/list", HTTPMethod.GET),
            ),
            tournaments=TournamentsEndpoints(
                get_tournaments=ep(f"{base_url}/tournaments", HTTPMethod.GET),
            ),
            fixtures=FixturesEndpoints(
                get_fixtures_by_sport=ep(
                    f"{base_url}/fixtures/by-sport", HTTPMethod.GET
                ),
                get_fixtures_by_tournament=ep(
                    f"{base_url}/fixtures/by-tournament", HTTPMethod.GET
                ),
                get_special_bets=ep(
                    f"{base_url}/fixtures/special-bets", HTTPMethod.GET
                ),
                get_recommended_bets=ep(
                    f"{base_url}/fixtures/recommended", HTTPMethod.GET
                ),
            ),
            odds=OddsEndpoints(
                get_fixture_odds=ep(f"{base_url}/odds/fixture", HTTPMethod.GET),
                get_odds_combo=ep(f"{base_url}/odds/combo", HTTPMethod.POST),
            ),
            bets=BetsEndpoints(
                place_bet=ep(f"{base_url}/bets/place", HTTPMethod.POST),
            ),
            combos=CombosEndpoints(
                place_combo=ep(f"{base_url}/combos/place", HTTPMethod.POST),
                get_combo_profit=ep(f"{base_url}/combos/profit", HTTPMethod.POST),
                delete_bet_combo=ep(f"{base_url}/combos/bet", HTTPMethod.DELETE),
                add_bet_to_combo=ep(f"{base_url}/combos/bet", HTTPMethod.POST),
                get_odds_combo=ep(f"{base_url}/combos/odds", HTTPMethod.POST),
            ),
        )

        return cls(
            **defaults.model_dump(),
            PK=f"company#{company_id}",
            SK="platform_endpoints",
        )

    # --- SERIALIZACIÓN DDB ---
    def to_dynamodb_item(self) -> dict:
        from pydantic import HttpUrl
        from enum import Enum

        def serialize(obj):
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
            return obj

        return serialize(self.model_dump())
