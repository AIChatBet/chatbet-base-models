from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional, Any
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==================
# Reply Markup Models (Telegram-like)
# ==================
class InlineKeyboardButton(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    callback_data: Optional[str] = None
    url: Optional[str] = None

    @model_validator(mode="after")
    def _only_one_action(self) -> "InlineKeyboardButton":
        cd = self.callback_data
        url = self.url
        if cd and url:
            raise ValueError("Button must have either callback_data or url, not both")
        if not cd and not url:
            raise ValueError("Button must define either callback_data or url")
        if cd and len(cd) > 64:
            raise ValueError("callback_data must be <= 64 characters")
        return self


class InlineKeyboardMarkup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inline_keyboard: List[List[InlineKeyboardButton]] = Field(default_factory=list)


# ==================
# Message primitive
# ==================
class MessageItem(BaseModel):
    """Generic message wrapper.
    - Accepts **either** `text` or `caption` (mutually exclusive)
    - Optional `reply_markup` for inline keyboards
    - Backward compatible: a plain string coerces to {"text": str}
    """

    model_config = ConfigDict(extra="forbid")

    text: Optional[str] = None
    reply_markup: Optional[InlineKeyboardMarkup] = None

    @classmethod
    def _coerce(cls, v):
        # Back-compat: wrap plain strings into {"text": v}
        if v is None or isinstance(v, dict) or isinstance(v, MessageItem):
            return v
        if isinstance(v, str):
            return {"text": v}
        return v


# ==================
# Message Group Models
# ==================
class OnboardingMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_onboarding: Optional[MessageItem] = None
    greeting_message: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class ValidationMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_validation: Optional[MessageItem] = None
    member_validation_phone: Optional[MessageItem] = None
    member_validation_email: Optional[MessageItem] = None
    send_otp: Optional[MessageItem] = None
    bad_otp: Optional[MessageItem] = None
    blocked_otp: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class RegistrationMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    not_registered_user: Optional[MessageItem] = None
    not_registered_user_country: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class MenuMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    main_menu: Optional[MessageItem] = None
    support: Optional[MessageItem] = None
    withdrawal: Optional[MessageItem] = None
    balance: Optional[MessageItem] = None
    results: Optional[MessageItem] = None
    deposit: Optional[MessageItem] = None
    show_links: Optional[MessageItem] = None  # renders quick links/buttons

    @classmethod
    def model_validate(cls, obj):
        # Soft aliases for legacy keys
        if isinstance(obj, dict):
            if "support_message" in obj and "support" not in obj:
                obj["support"] = obj.pop("support_message")
            if "withdrawal_message" in obj and "withdrawal" not in obj:
                obj["withdrawal"] = obj.pop("withdrawal_message")
            if "deposit_message" in obj and "deposit" not in obj:
                obj["deposit"] = obj.pop("deposit_message")
            if "show_links_message" in obj and "show_links" not in obj:
                obj["show_links"] = obj.pop("show_links_message")
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class BetsMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    special_bet: Optional[MessageItem] = None
    select_sport: Optional[MessageItem] = None
    select_tournament: Optional[MessageItem] = None
    select_fixture: Optional[MessageItem] = None
    bet_amount: Optional[MessageItem] = None
    invalid_bet_amount: Optional[MessageItem] = None
    fixture_odds: Optional[MessageItem] = None
    special_bets_odds: Optional[MessageItem] = None
    unavailable_odds: Optional[MessageItem] = None
    placed_bet: Optional[MessageItem] = None
    placed_bet_menu: Optional[MessageItem] = None
    without_funds: Optional[MessageItem] = None
    deposit: Optional[MessageItem] = None
    bet_rejected: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class CombosMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    show_all_markets_by_fixtures: Optional[MessageItem] = None
    error_to_add_market: Optional[MessageItem] = None
    error_to_get_odds: Optional[MessageItem] = None
    error_to_place_bet: Optional[MessageItem] = None
    summary_after_add_market: Optional[MessageItem] = None
    summary_after_remove_bet_from_combo: Optional[MessageItem] = None
    remove_market: Optional[MessageItem] = None
    select_amount: Optional[MessageItem] = None
    place_combo_bet: Optional[MessageItem] = None
    summary_after_bet: Optional[MessageItem] = None
    show_my_combo: Optional[MessageItem] = None
    delete_combo: Optional[MessageItem] = None
    combo_odds: Optional[MessageItem] = None
    combos_recommendation: Optional[MessageItem] = None
    combos_confirm_add_recommended: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            # Fix typos like errro_to_place_bet -> error_to_place_bet, sumary -> summary
            if "errro_to_place_bet" in obj and "error_to_place_bet" not in obj:
                obj["error_to_place_bet"] = obj.pop("errro_to_place_bet")
            for k in list(obj.keys()):
                if k.startswith("sumary_") and not k.startswith("summary_"):
                    obj[k.replace("sumary_", "summary_")] = obj.pop(k)
            # Ensure defaults when fields are missing
            if (
                "combos_recommendation" not in obj
                or obj.get("combos_recommendation") is None
            ):
                obj["combos_recommendation"] = {"text": "Recommended combos"}
            if (
                "combos_confirm_add_recommended" not in obj
                or obj.get("combos_confirm_add_recommended") is None
            ):
                obj["combos_confirm_add_recommended"] = {
                    "text": "Do you want to add these recommended combos?",
                }
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class ErrorMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invalid_input: Optional[MessageItem] = None
    error: Optional[MessageItem] = None
    error_2: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class ConfirmationMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm_bet: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class LabelMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    menu_label_text: Optional[MessageItem] = None
    label_text: Optional[MessageItem] = None
    combo_summary_after_add_market_label_text: Optional[MessageItem] = None
    select_tournament_label_text: Optional[MessageItem] = None
    select_fixture_label_text: Optional[MessageItem] = None
    markets_without_combo_label_text: Optional[MessageItem] = None
    select_sport_label_text: Optional[MessageItem] = None
    more_options_text: Optional[MessageItem] = None
    combo_remove_market_label_text: Optional[MessageItem] = None
    selected_other_market_label_text: Optional[MessageItem] = None
    other_markets_label_text: Optional[MessageItem] = None
    combo_odds_label_text: Optional[MessageItem] = None
    fixture_odds_label_text: Optional[MessageItem] = None
    menu_more_options_text: Optional[MessageItem] = None
    list_markets_label_text: Optional[MessageItem] = None
    list_fixtures_label_text: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class EndMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    end_conversation: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


class GuidanceMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valid_input_text: Optional[MessageItem] = None
    invalid_input_text: Optional[MessageItem] = None
    invalid_input_response: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)


# ==================
# Message Template (Core)
# ==================
class MessageTemplates(BaseModel):
    model_config = ConfigDict(extra="forbid")
    onboarding: Optional[OnboardingMessages] = None
    validation: Optional[ValidationMessages] = None
    registration: Optional[RegistrationMessages] = None
    menu: Optional[MenuMessages] = None
    bets: Optional[BetsMessages] = None
    combos: Optional[CombosMessages] = None
    errors: Optional[ErrorMessages] = None
    confirmation: Optional[ConfirmationMessages] = None
    labels: Optional[LabelMessages] = None
    end: Optional[EndMessages] = None
    guidance: Optional[GuidanceMessages] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ---------- Factory con defaults razonables ----------
    @classmethod
    def from_minimal(cls) -> "MessageTemplates":
        return cls(
            onboarding=OnboardingMessages(
                member_onboarding=MessageItem(text="Welcome to our chatbot!"),
                greeting_message=MessageItem(
                    text="Hello! 👋 How can I help you today?"
                ),
            ),
            validation=ValidationMessages(
                member_validation=MessageItem(text="Please validate your account."),
                send_otp=MessageItem(text="We've sent you an OTP."),
                bad_otp=MessageItem(text="Invalid OTP, try again."),
            ),
            registration=RegistrationMessages(
                not_registered_user=MessageItem(text="You are not registered."),
            ),
            menu=MenuMessages(
                main_menu=MessageItem(text="Main menu"),
                show_links=MessageItem(
                    text="Quick links",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Help", url="https://example.com/help"
                                )
                            ]
                        ]
                    ),
                ),
            ),
            bets=BetsMessages(
                select_sport=MessageItem(text="Select a sport"),
                select_tournament=MessageItem(text="Select a tournament"),
                bet_amount=MessageItem(text="Enter your bet amount"),
            ),
            combos=CombosMessages(
                show_all_markets_by_fixtures=MessageItem(text="Showing all markets"),
                combos_recommendation=MessageItem(text="Recommended combos"),
                combos_confirm_add_recommended=MessageItem(
                    text="Do you want to add these recommended combos?",
                ),
            ),
            errors=ErrorMessages(
                invalid_input=MessageItem(text="Invalid input."),
                error=MessageItem(text="An error occurred."),
            ),
            confirmation=ConfirmationMessages(
                confirm_bet=MessageItem(text="Confirm your bet?"),
            ),
            labels=LabelMessages(
                menu_label_text=MessageItem(text="Menu"),
                list_fixtures_label_text=MessageItem(text="Fixtures"),
            ),
            end=EndMessages(
                end_conversation=MessageItem(text="Bye!"),
            ),
            guidance=GuidanceMessages(
                valid_input_text=MessageItem(text="Looks good ✅"),
                invalid_input_text=MessageItem(text="Please check your input ⚠️"),
            ),
        )

    # ---------- utilidades ----------
    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_dynamodb_item(self, *, drop_none: bool = True) -> dict:
        """Serializa a dict compatible con DynamoDB."""

        def ser(x: Any) -> Any:
            if isinstance(x, datetime):
                return x.isoformat()
            if isinstance(x, Enum):
                return x.value
            if hasattr(x, "model_dump"):
                return ser(x.model_dump())
            if isinstance(x, dict):
                out = {k: ser(v) for k, v in x.items()}
                return {k: v for k, v in out.items() if not (drop_none and v is None)}
            if isinstance(x, list):
                return [ser(v) for v in x]
            return x  # primitivos

        return ser(self.model_dump())


# ==================
# MessageTemplatesDB
# ==================
class MessageTemplatesDB(MessageTemplates):
    PK: Optional[str] = Field(default=None, description="Partition key")
    SK: Optional[str] = Field(default=None, description="Sort key")

    @classmethod
    def from_minimal(cls, company_id: str) -> "MessageTemplatesDB":
        base = MessageTemplates.from_minimal()
        return cls(
            **base.model_dump(),
            PK=f"company#{company_id}",
            SK="message_templates",
        )

    @model_validator(mode="after")
    def _ensure_keys(self) -> "MessageTemplatesDB":
        if not self.PK or not self.SK:
            raise ValueError("PK and SK are required for MessageTemplatesDB")
        return self

    # hereda touch() y to_dynamodb_item()
