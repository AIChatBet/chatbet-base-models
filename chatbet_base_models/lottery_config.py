"""Lottery provider configuration of a lottery company (DynamoDB SK ``lottery_config``).

The counterpart of ``sportbook_config`` for a company whose
``site_config.identity.company_type`` is ``"lottery"``: who sells the tickets and how
to reach them. It does not hold what is sold (the lotteries, their draws and prices, and
which of them a company offers live in the lottery catalog in Postgres), nor how the bot
talks (``site_config``), nor the URLs the bot calls (``platform_endpoints.lottery``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class MockLotteryConfig(BaseModel):
    """ChatBet's lottery mock (chatbet-mock-services, routes ``/lottery/*``).

    It has no credentials: the mock authenticates the user with its own fixed token.
    When the first real provider arrives, ``LotteryConfig.config`` becomes a union
    discriminated by ``provider``, as ``SportbookConfig.config`` is; rows stored with
    ``provider: "mock"`` stay valid.
    """

    model_config = ConfigDict(extra="forbid")

    provider: Literal["mock"] = "mock"
    api_url: HttpUrl
    timeout_s: float = Field(
        default=5.0, gt=0, le=60, description="Timeout of each call, in seconds"
    )


class LotteryRules(BaseModel):
    """Purchase limits of the company, the same for every lottery it sells.

    What belongs to one lottery (its price, its numbers, how many minutes before the
    draw its sales close) is in the lottery catalog, not here.
    """

    model_config = ConfigDict(extra="forbid")

    max_quantity_per_purchase: int = Field(
        default=20, ge=1, description="Most tickets one purchase may buy"
    )
    max_amount_per_purchase: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description=(
            "Most money one purchase may cost, in the company's currency "
            "(site_config.locale.currency). None: no limit beyond the balance"
        ),
    )


class LotteryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config: MockLotteryConfig
    rules: LotteryRules = Field(default_factory=LotteryRules)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def provider(self) -> str:
        """The provider adapter to use (``config.provider``)."""
        return self.config.provider

    @classmethod
    def from_minimal_mock(
        cls, *, api_url: str, rules: Optional[LotteryRules] = None
    ) -> "LotteryConfig":
        now = datetime.now(timezone.utc)
        return cls(
            config=MockLotteryConfig(api_url=api_url),
            rules=rules or LotteryRules(),
            created_at=now,
            updated_at=now,
        )

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """A DynamoDB-friendly dict: datetimes as ISO 8601, URLs as text, enums as
        their value, Decimals kept (DynamoDB numbers); None dropped unless asked."""

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, HttpUrl):
                return str(x)
            if isinstance(x, Enum):
                return x.value
            if isinstance(x, dict):
                out = {k: ser(v) for k, v in x.items()}
                return {k: v for k, v in out.items() if not (drop_none and v is None)}
            if isinstance(x, list):
                return [ser(v) for v in x]
            if isinstance(x, float):
                return Decimal(str(x))  # DynamoDB rejects floats
            return x

        return ser(self.model_dump())


class LotteryConfigDB(LotteryConfig):
    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal_mock(  # type: ignore[override]
        cls, company_id: str, **kwargs: Any
    ) -> "LotteryConfigDB":
        base = LotteryConfig.from_minimal_mock(**kwargs)
        return cls(**base.model_dump(), PK=f"company#{company_id}", SK="lottery_config")

    @model_validator(mode="after")
    def _ensure_keys(self) -> "LotteryConfigDB":
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for LotteryConfigDB")
        return self
