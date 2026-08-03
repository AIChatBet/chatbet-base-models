from __future__ import annotations

import re
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# Profile namespaces an answer may be written to. Validated at save time so a typo in
# `storage_key` fails loudly in the back office instead of silently discarding the answer
# the user gave (the agent could not route it anywhere). Extend when a new namespace exists.
ALLOWED_STORAGE_ROOTS = ("memory_structured", "outreach_log")

_KEY_RE = re.compile(r"^[a-z0-9_]+$")
_STORAGE_KEY_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")


class OnboardingPhase(str, Enum):
    """When the agent should try to weave a question into the conversation."""

    FIRST_ENCOUNTER = "first_encounter"  # the essentials, earliest interactions
    GETTING_TO_KNOW = "getting_to_know"  # deeper detail, once the essentials are resolved
    WINDOW_FRAME = "window_frame"  # bound to a date window (World Cup, finals); auto-retires


# ===========================
# Nested Model - Individual Question
# ===========================
class OnboardingQuestionItem(BaseModel):
    """One profiling question an operator wants the agent to ask.

    `agent_instruction` is an INSTRUCTION, never a literal script: the agent phrases it in the
    company's configured language, tone and personality, and only when the moment feels natural.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=40, description="Stable identifier, snake_case")
    label: str = Field(min_length=1, max_length=80, description="Internal name, shown in the back office")
    agent_instruction: str = Field(min_length=1, max_length=1000)
    phase: OnboardingPhase
    storage_key: str = Field(min_length=1, max_length=120, description="Dotted profile path the answer lands on")
    hook_hints: List[str] = Field(
        default_factory=list,
        description="Conversational cues that make the question feel natural",
    )
    required_for_personalization: bool = False
    cooldown_override: Optional[int] = Field(
        default=None, gt=0, description="Hours between asks for this question; None uses the global default"
    )
    protected: bool = Field(
        default=False,
        description="System-owned question (marketing consent): cannot be deleted nor have its storage_key changed",
    )
    enabled: bool = True
    window_active_from: Optional[date] = None
    window_active_to: Optional[date] = None

    # Validators
    @field_validator("key")
    @classmethod
    def _validate_key(cls, v: str) -> str:
        """Keys are stable identifiers, so they must be slug-safe and case-insensitive-unique."""
        cleaned = v.strip().lower()
        if not _KEY_RE.match(cleaned):
            raise ValueError(f"key must be snake_case (a-z, 0-9, _): {v!r}")
        return cleaned

    @field_validator("label", "agent_instruction")
    @classmethod
    def _validate_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty or only whitespace")
        return cleaned

    @field_validator("storage_key")
    @classmethod
    def _validate_storage_key(cls, v: str) -> str:
        """A dotted path under a known profile namespace — see ALLOWED_STORAGE_ROOTS."""
        cleaned = v.strip()
        if not _STORAGE_KEY_RE.match(cleaned):
            raise ValueError(f"storage_key must be a dotted snake_case path (e.g. memory_structured.name): {v!r}")
        if cleaned.split(".", 1)[0] not in ALLOWED_STORAGE_ROOTS:
            raise ValueError(f"storage_key must start with one of {ALLOWED_STORAGE_ROOTS}: {v!r}")
        return cleaned

    @field_validator("hook_hints")
    @classmethod
    def _validate_hook_hints(cls, v: List[str]) -> List[str]:
        """Strip, drop empties, dedupe (order preserved) and bound size."""
        if len(v) > 20:
            raise ValueError("Maximum 20 hook_hints allowed")
        seen: set[str] = set()
        unique: List[str] = []
        for hint in v:
            h = hint.strip()
            if not h:
                continue
            if len(h) > 200:
                raise ValueError(f"hook_hint too long (max 200 chars): {h[:50]}...")
            if h.lower() not in seen:
                seen.add(h.lower())
                unique.append(h)
        return unique

    @model_validator(mode="after")
    def _validate_window(self) -> "OnboardingQuestionItem":
        """The date window belongs to WINDOW_FRAME questions and only to them."""
        if self.phase is OnboardingPhase.WINDOW_FRAME:
            if not self.window_active_from or not self.window_active_to:
                raise ValueError("window_active_from and window_active_to are required when phase is window_frame")
            if self.window_active_to < self.window_active_from:
                raise ValueError("window_active_to must be on or after window_active_from")
        elif self.window_active_from or self.window_active_to:
            raise ValueError("window_active_from/window_active_to are only valid when phase is window_frame")
        return self

    # Utility
    def is_active_on(self, day: Optional[date] = None) -> bool:
        """Whether this question may be asked on `day` — False once a window has closed."""
        if not self.enabled:
            return False
        if self.phase is not OnboardingPhase.WINDOW_FRAME:
            return True
        today = day or datetime.now(timezone.utc).date()
        return self.window_active_from <= today <= self.window_active_to


# ===========================
# Main Configuration - Array Container
# ===========================
class OnboardingQuestions(BaseModel):
    """The set of profiling questions configured for a company."""

    model_config = ConfigDict(extra="forbid")

    questions: List[OnboardingQuestionItem] = Field(
        default_factory=list,
        description="All configured questions, any phase",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Array-level validation
    @field_validator("questions")
    @classmethod
    def _validate_questions(cls, v: List[OnboardingQuestionItem]) -> List[OnboardingQuestionItem]:
        """Sanity bound plus uniqueness of both identifiers.

        Duplicate `storage_key` would make two questions overwrite each other's answer, so it is
        rejected here rather than debugged later. The soft operator guidance (warn above 5
        first-encounter / 15 required) is a back-office concern, not a validation error.
        """
        if len(v) > 50:
            raise ValueError("Maximum 50 questions allowed")
        keys = [q.key for q in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate key found in questions array")
        storage_keys = [q.storage_key for q in v]
        if len(storage_keys) != len(set(storage_keys)):
            raise ValueError("Duplicate storage_key found in questions array")
        return v

    # Factory methods
    @classmethod
    def from_minimal(cls) -> "OnboardingQuestions":
        """Create an empty question set."""
        now = datetime.now(timezone.utc)
        return cls(questions=[], created_at=now, updated_at=now)

    @classmethod
    def seed_default(cls) -> "OnboardingQuestions":
        """The three questions the agent asks today, as configuration.

        Used to bootstrap a company that has no record yet, so behaviour is unchanged from the
        hardcoded flow. `consent` is protected: it is the opt-in that legally enables proactive
        messaging, so an operator must not be able to delete it or repoint its storage_key.
        """
        return cls(
            questions=[
                OnboardingQuestionItem(
                    key="name",
                    label="Preferred name",
                    agent_instruction=(
                        "Ask the USER what their name is — how you should address them personally. "
                        "It is strictly about the USER's own name; never your own."
                    ),
                    phase=OnboardingPhase.FIRST_ENCOUNTER,
                    storage_key="memory_structured.name",
                    required_for_personalization=True,
                ),
                OnboardingQuestionItem(
                    key="consent",
                    label="Marketing consent",
                    agent_instruction=(
                        "Ask whether the USER authorizes receiving offers and promotions through this channel."
                    ),
                    phase=OnboardingPhase.FIRST_ENCOUNTER,
                    storage_key="outreach_log.promo_consent",
                    required_for_personalization=True,
                    protected=True,
                ),
                OnboardingQuestionItem(
                    key="tournament",
                    label="Favorite tournament",
                    agent_instruction="Ask which tournament or league is the USER's favorite.",
                    phase=OnboardingPhase.FIRST_ENCOUNTER,
                    storage_key="memory_structured.favorite_tournaments",
                    hook_hints=["the user mentions a team", "the user asks odds on a specific match"],
                ),
            ]
        )

    # Utility methods
    def touch(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)

    def get_question(self, key: str) -> Optional[OnboardingQuestionItem]:
        """Get a question by key"""
        for question in self.questions:
            if question.key == key:
                return question
        return None

    def remove_question(self, key: str) -> bool:
        """Remove a question by key. Returns True if found and removed.

        A `protected` question is never removed — it is system-owned.
        """
        for i, question in enumerate(self.questions):
            if question.key == key:
                if question.protected:
                    raise ValueError(f"Question {key!r} is protected and cannot be removed")
                self.questions.pop(i)
                self.touch()
                return True
        return False

    def get_active_questions(
        self, *, phase: Optional[OnboardingPhase] = None, day: Optional[date] = None
    ) -> List[OnboardingQuestionItem]:
        """Questions askable on `day`: enabled, and inside their window when time-bound."""
        return [
            q
            for q in self.questions
            if q.is_active_on(day) and (phase is None or q.phase is phase)
        ]

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """Serialize to DynamoDB-compatible dict"""

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, date):
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
class OnboardingQuestionsDB(OnboardingQuestions):
    """DynamoDB variant with PK/SK"""

    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal(cls, company_id: str) -> "OnboardingQuestionsDB":
        """Create an empty question set for a company"""
        base = OnboardingQuestions.from_minimal()
        return cls(
            **base.model_dump(),
            PK=f"company#{company_id}",
            SK="onboarding_questions",
        )

    @classmethod
    def seed_default(cls, company_id: str) -> "OnboardingQuestionsDB":
        """Seed a company with the three questions the agent asks today"""
        base = OnboardingQuestions.seed_default()
        return cls(
            **base.model_dump(),
            PK=f"company#{company_id}",
            SK="onboarding_questions",
        )

    @model_validator(mode="after")
    def _ensure_keys(self) -> "OnboardingQuestionsDB":
        """Ensure PK and SK are set"""
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for OnboardingQuestionsDB")
        return self

    # Inherits all utility methods from OnboardingQuestions
