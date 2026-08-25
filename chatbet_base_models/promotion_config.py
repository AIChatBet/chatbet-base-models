from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from chatbet_base_models.message_template import InlineKeyboardButton


# ===========================
# Nested Model - Promotion Button
# ===========================
class PromotionButton(BaseModel):
    """Button attached to a promotion's copy (CU-86ak0ajez).

    Targets either another promotion (``promotion_id`` — existing
    promo-to-promo behavior) or a specific fixture (``fixture_id`` alongside
    ``sport_id``/``tournament_id``, the same triple consuming apps already
    use to navigate straight to a fixture's odds), never both.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=200)
    promotion_id: Optional[str] = None
    fixture_id: Optional[str] = None
    sport_id: Optional[str] = None
    tournament_id: Optional[str] = None

    @model_validator(mode="after")
    def _only_one_target(self) -> "PromotionButton":
        if self.promotion_id and self.fixture_id:
            raise ValueError("Button must target either promotion_id or fixture_id, not both")
        if not self.promotion_id and not self.fixture_id:
            raise ValueError("Button must define either promotion_id or fixture_id")
        if self.fixture_id and (not self.sport_id or not self.tournament_id):
            raise ValueError("A fixture_id target requires sport_id and tournament_id")
        return self

    @model_validator(mode="after")
    def _callback_data_fits_telegram_limit(self) -> "PromotionButton":
        """Reject at config-save time what ``InlineKeyboardButton`` would
        otherwise reject when a real user taps the button — Telegram caps
        ``callback_data`` at 64 bytes. Catching it here (Backoffice save)
        instead of in ``to_inline_keyboard_button()`` (chat render) means an
        operator gets an actionable error instead of live users hitting a
        broken promo button."""
        callback_data = self._callback_data()
        if len(callback_data) > 64:
            raise ValueError(
                f"Resulting callback_data '{callback_data}' is {len(callback_data)} "
                "chars, exceeding Telegram's 64-char callback_data limit"
            )
        return self

    def _callback_data(self) -> str:
        if self.fixture_id:
            return f"oi:S{self.sport_id}.T{self.tournament_id}.F{self.fixture_id}"
        return f"promo:{self.promotion_id}"

    def to_inline_keyboard_button(self) -> InlineKeyboardButton:
        """Build the canonical ``InlineKeyboardButton`` consuming apps render.

        Every other button in the system (onboarding, validation, menu, bets,
        combos, confirmation) is built from ``InlineKeyboardButton`` — this
        keeps ``PromotionButton``'s typed domain fields for Backoffice
        authoring while producing the same shape everywhere else. A
        ``fixture_id`` target reuses the ``oi:`` self-contained navigation
        (``S{sport}.T{tournament}.F{fixture}``) that fixture-odds screens use
        elsewhere; a ``promotion_id`` target reuses the ``promo:`` routing.
        """
        return InlineKeyboardButton(text=self.text, callback_data=self._callback_data())


# ===========================
# Nested Model - Individual Promotion Item
# ===========================
class PromotionItem(BaseModel):
    """Individual promotion within the PromotionsConfig array"""

    model_config = ConfigDict(extra="forbid")

    promotion_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this promotion",
    )
    title: str = Field(min_length=1, max_length=200)
    start_date: datetime
    end_date: datetime
    details: str = Field(max_length=5000)
    keywords: List[str] = Field(default_factory=list)
    priority: int = Field(
        default=0,
        ge=0,
        description="Display order in the chat list (ascending, lower shows first). "
        "Legacy promotions without an explicit value default to 0.",
    )
    buttons: List[PromotionButton] = Field(
        default_factory=list,
        description="Buttons rendered under this promotion's copy.",
    )

    # Validators
    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str) -> str:
        """Strip whitespace and validate title"""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty or only whitespace")
        if cleaned.isdigit():
            raise ValueError("Title cannot be purely numeric")
        return cleaned

    @field_validator("keywords")
    @classmethod
    def _validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and normalize keywords"""
        if len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")

        cleaned = []
        for keyword in v:
            kw = keyword.strip().lower()
            if not kw:
                continue  # Skip empty keywords
            if len(kw) > 50:
                raise ValueError(f"Keyword too long (max 50 chars): {kw[:50]}...")
            cleaned.append(kw)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for kw in cleaned:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)

        return unique

    @field_validator("details")
    @classmethod
    def _validate_details(cls, v: str) -> str:
        """Validate details content"""
        if not v.strip():
            raise ValueError("Details cannot be empty")
        return v

    @model_validator(mode="after")
    def _validate_dates(self) -> "PromotionItem":
        """Validate that end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


# ===========================
# Main Configuration - Array Container
# ===========================
class PromotionsConfig(BaseModel):
    """Configuration containing an array of promotions"""

    model_config = ConfigDict(extra="forbid")

    promotions: List[PromotionItem] = Field(
        default_factory=list,
        description="List of all promotions",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Array-level validation
    @field_validator("promotions")
    @classmethod
    def _validate_promotions(cls, v: List[PromotionItem]) -> List[PromotionItem]:
        """Validate promotions array"""
        if len(v) > 100:
            raise ValueError("Maximum 100 promotions allowed")

        # Check for duplicate promotion_ids
        ids = [p.promotion_id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate promotion_id found in promotions array")

        return v

    # Factory method
    @classmethod
    def from_minimal(cls) -> "PromotionsConfig":
        """Create an empty promotions config"""
        now = datetime.now(timezone.utc)
        return cls(
            promotions=[],
            created_at=now,
            updated_at=now,
        )

    # Utility methods
    def touch(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)

    def add_promotion(
        self,
        *,
        title: str,
        start_date: datetime,
        end_date: datetime,
        details: str,
        keywords: Optional[List[str]] = None,
        promotion_id: Optional[str] = None,
        priority: int = 0,
    ) -> PromotionItem:
        """Add a new promotion to the array"""
        promotion = PromotionItem(
            promotion_id=promotion_id or str(uuid4()),
            title=title,
            start_date=start_date,
            end_date=end_date,
            details=details,
            keywords=keywords or [],
            priority=priority,
        )
        self.promotions.append(promotion)
        self.touch()
        return promotion

    def remove_promotion(self, promotion_id: str) -> bool:
        """Remove a promotion by ID. Returns True if found and removed."""
        for i, promo in enumerate(self.promotions):
            if promo.promotion_id == promotion_id:
                self.promotions.pop(i)
                self.touch()
                return True
        return False

    def get_promotion(self, promotion_id: str) -> Optional[PromotionItem]:
        """Get a promotion by ID"""
        for promo in self.promotions:
            if promo.promotion_id == promotion_id:
                return promo
        return None

    def get_active_promotions(self) -> List[PromotionItem]:
        """Get all currently active promotions, ordered by ``priority`` ascending.

        Promotions sharing the same ``priority`` (e.g. legacy entries still at
        the default 0) break ties by title so the order is deterministic
        across calls instead of depending on array position.
        """
        now = datetime.now(timezone.utc)
        active = [p for p in self.promotions if p.start_date <= now < p.end_date]
        return sorted(active, key=lambda p: (p.priority, p.title))

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """Serialize to DynamoDB-compatible dict"""
        from enum import Enum

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, Enum):
                return x.value
            if isinstance(x, dict):
                out = {k: ser(v) for k, v in x.items()}
                return {k: v for k, v in out.items() if not (drop_none and v is None)}
            if isinstance(x, list):
                return [ser(v) for v in x]
            if hasattr(x, "model_dump"):
                return ser(x.model_dump())
            return x  # primitives

        return ser(self.model_dump())


# ===========================
# DynamoDB Variant
# ===========================
class PromotionsConfigDB(PromotionsConfig):
    """DynamoDB variant with PK/SK"""

    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal(cls, company_id: str) -> "PromotionsConfigDB":
        """Create an empty promotions config for a company"""
        base = PromotionsConfig.from_minimal()
        return cls(
            **base.model_dump(),
            PK=f"company#{company_id}",
            SK="promotions_config",
        )

    @model_validator(mode="after")
    def _ensure_keys(self) -> "PromotionsConfigDB":
        """Ensure PK and SK are set"""
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for PromotionsConfigDB")
        return self

    # Inherits all utility methods from PromotionsConfig
