from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import List, Literal, Optional, Any, Sequence
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


# ==================
# Reply Markup Models (Telegram-like)
# ==================
class InlineKeyboardButton(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    callback_data: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None

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


MatchMode = Literal["exact", "substring", "prefix", "suffix", "regex"]


def _normalize(s: str, *, case_sensitive: bool) -> str:
    return s if case_sensitive else s.lower()


def _collect_callbacks(msg) -> list[str]:
    kb = getattr(msg, "reply_markup", None)
    if not kb or not kb.inline_keyboard:
        return []
    out: list[str] = []
    for row in kb.inline_keyboard:
        for btn in row:
            cd = getattr(btn, "callback_data", None)
            if isinstance(cd, str):
                out.append(cd)
    return out


def require_callbacks(
    msg: Optional["MessageItem"],
    needles: Sequence[str],
    mode: Literal["all", "any"] = "all",  # AND / OR over the needles
    match_mode: MatchMode = "exact",  # <-- changed default to exact
    case_sensitive: bool = True,
) -> Optional["MessageItem"]:
    if msg is None:
        return msg  # allow None if field is Optional

    callbacks = _collect_callbacks(msg)
    if not callbacks:
        raise ValueError(
            f"Must include an inline keyboard with callbacks {needles!r} (mode={mode}, match={match_mode})"
        )

    # Prepare comparators
    if not case_sensitive:
        callbacks_norm = [_normalize(c, case_sensitive=False) for c in callbacks]
        needles_norm = [_normalize(n, case_sensitive=False) for n in needles]
    else:
        callbacks_norm = callbacks
        needles_norm = list(needles)

    def any_match(needle: str) -> bool:
        if match_mode == "exact":
            return any(cd == needle for cd in callbacks_norm)
        if match_mode == "substring":
            return any(needle in cd for cd in callbacks_norm)
        if match_mode == "prefix":
            return any(cd.startswith(needle) for cd in callbacks_norm)
        if match_mode == "suffix":
            return any(cd.endswith(needle) for cd in callbacks_norm)
        if match_mode == "regex":
            pat = re.compile(needle)
            return any(pat.search(cd) for cd in callbacks_norm)
        raise ValueError(f"Unknown match_mode: {match_mode!r}")

    ok = (
        all(any_match(n) for n in needles_norm)
        if mode == "all"
        else any(any_match(n) for n in needles_norm)
    )
    if not ok:
        details = f"present={callbacks!r}, required({mode},{match_mode})={needles!r}"
        raise ValueError(f"Inline keyboard callbacks do not satisfy rule: {details}")
    return msg


def extract(item):
    if not item or not item.reply_markup:
        return set()
    cbs = []
    for row in item.reply_markup.inline_keyboard or []:
        for btn in row:
            if btn.callback_data:
                cbs.append(btn.callback_data)
    return set(cbs)


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

    @field_validator("member_onboarding")
    @classmethod
    def _member_rules(cls, v):
        return require_callbacks(v, ["account_yes", "account_no"])

    @model_validator(mode="after")
    def _require_callbacks(self):
        need = {"account_yes", "account_no"}
        got = extract(self.member_onboarding)
        missing = need - got
        if missing:
            raise ValueError(f"member_onboarding missing callbacks: {sorted(missing)}")

        return self


class ValidationMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_validation: Optional[MessageItem] = None
    member_validation_phone: Optional[MessageItem] = None
    member_validation_email: Optional[MessageItem] = None
    send_otp: Optional[MessageItem] = None
    bad_otp: Optional[MessageItem] = None
    blocked_otp: Optional[MessageItem] = None
    blocked_user: Optional[MessageItem] = None

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)

    @field_validator("send_otp")
    @classmethod
    def _send_otp_rules(cls, v):
        return require_callbacks(v, ["send_otp"])

    @field_validator("bad_otp")
    @classmethod
    def _bad_otp_rules(cls, v):
        return require_callbacks(v, ["send_otp"])

    @model_validator(mode="after")
    def _require_callbacks(self):
        need = {"send_otp"}
        for field, item in {
            "send_otp": self.send_otp,
            "bad_otp": self.bad_otp,
        }.items():
            if item is None:
                continue
            got = extract(item)
            missing = need - got
            if missing:
                raise ValueError(f"{field} missing callbacks: {sorted(missing)}")
        return self


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

    @field_validator("main_menu")
    @classmethod
    def _main_menu_rules(cls, v):
        return require_callbacks(v, ["bet"])

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

    @model_validator(mode="after")
    def _require_callbacks(self):
        if self.main_menu is None:
            return self
        need = {"bet"}
        got = extract(self.main_menu)
        missing = need - got
        if missing:
            raise ValueError(f"main_menu missing callbacks: {sorted(missing)}")
        return self


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
    select_type_of_bet: Optional[MessageItem] = None

    @field_validator("select_type_of_bet")
    @classmethod
    def _type_of_bet_rules(cls, v):
        return require_callbacks(
            v, ["bet_simple&{FIXTURE_ID}", "add_market_to_combo&{FIXTURE_ID}"]
        )

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)

    @model_validator(mode="after")
    def _require_callbacks(self):
        if self.select_type_of_bet is None:
            return self
        need = {"bet_simple&{FIXTURE_ID}", "add_market_to_combo&{FIXTURE_ID}"}
        got = extract(self.select_type_of_bet)
        missing = need - got
        if missing:
            raise ValueError(f"select_type_of_bet missing callbacks: {sorted(missing)}")
        return self


class CombosMessages(BaseModel):
    model_config = ConfigDict(extra="forbid")
    show_all_markets_by_fixtures: Optional[MessageItem] = None
    error_to_add_market: Optional[MessageItem] = None
    error_to_get_odds: Optional[MessageItem] = None
    error_to_place_bet: Optional[MessageItem] = None
    empty_combo: Optional[MessageItem] = MessageItem(
        text="Sorry, there isn't any combo yet"
    )
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

    @field_validator("combos_recommendation")
    @classmethod
    def _combos_recommendation_rules(cls, v):
        return require_callbacks(v, ["combo_select_amount_recommended"])

    @field_validator("delete_combo")
    @classmethod
    def _delete_combo_rules(cls, v):
        return require_callbacks(v, ["combo_confirm_delete_combo"])

    @field_validator("place_combo_bet")
    @classmethod
    def _place_combo_bet_rules(cls, v):
        return require_callbacks(v, ["combo_summary_after_bet"])

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
                obj["combos_recommendation"] = {
                    "text": "Recommended combos",
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "Select Amount",
                                    "callback_data": "combo_select_amount_recommended",
                                }
                            ]
                        ]
                    },
                }
            if (
                "combos_confirm_add_recommended" not in obj
                or obj.get("combos_confirm_add_recommended") is None
            ):
                obj["combos_confirm_add_recommended"] = {
                    "text": "Do you want to add these recommended combos?",
                }
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)

    @model_validator(mode="after")
    def _require_callbacks(self):
        checks = {
            "combos_recommendation": {"combo_select_amount_recommended"},
            "delete_combo": {"combo_confirm_delete_combo"},
            "place_combo_bet": {"combo_summary_after_bet"},
        }
        for field, need in checks.items():
            item = getattr(self, field)
            if item is None:
                continue
            got = extract(item)
            missing = need - got
            if missing:
                raise ValueError(f"{field} missing callbacks: {sorted(missing)}")
        return self


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

    @field_validator("confirm_bet")
    @classmethod
    def _confirm_bet_rules(cls, v):
        return require_callbacks(v, ["confirm_bet"])

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = {k: MessageItem._coerce(v) for k, v in obj.items()}
        return super().model_validate(obj)

    @model_validator(mode="after")
    def _require_callbacks(self):
        if self.confirm_bet is None:
            return self
        need = {"confirm_bet"}
        got = extract(self.confirm_bet)
        missing = need - got
        if missing:
            raise ValueError(f"confirm_bet missing callbacks: {sorted(missing)}")
        return self


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
                member_onboarding=MessageItem(
                    text="Welcome to our chatbot!",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Yes", callback_data="account_yes"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="No", callback_data="account_no"
                                )
                            ],
                        ]
                    ),
                ),
                greeting_message=MessageItem(
                    text="Hello! 👋 How can I help you today?",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Place a Bet", callback_data="bet"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="More Options", callback_data="show_links"
                                )
                            ],
                        ]
                    ),
                ),
            ),
            validation=ValidationMessages(
                member_validation=MessageItem(text="Please validate your account."),
                member_validation_phone=MessageItem(
                    text="Please provide your phone number."
                ),
                member_validation_email=MessageItem(
                    text="Please provide your email address."
                ),
                send_otp=MessageItem(
                    text="We've sent you an OTP.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Resend OTP", callback_data="send_otp"
                                )
                            ],
                        ]
                    ),
                ),
                bad_otp=MessageItem(
                    text="Invalid OTP, try again.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Resend OTP", callback_data="send_otp"
                                )
                            ],
                        ]
                    ),
                ),
                blocked_otp=MessageItem(
                    text="Too many failed attempts. OTP blocked.",
                ),
                blocked_user=MessageItem(
                    text="Sorry, I can't help you, you are blocked",
                ),
            ),
            registration=RegistrationMessages(
                not_registered_user=MessageItem(text="You are not registered."),
                not_registered_user_country=MessageItem(
                    text="You are in the wrong country."
                ),
            ),
            menu=MenuMessages(
                main_menu=MessageItem(
                    text="Main menu",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="Bet", callback_data="bet")],
                            [
                                InlineKeyboardButton(
                                    text="Show links", callback_data="show_links"
                                )
                            ],
                        ]
                    ),
                ),
                support=MessageItem(text="Support options"),
                withdrawal=MessageItem(text="Withdrawal options"),
                balance=MessageItem(text="Your balance"),
                results=MessageItem(text="Latest results"),
                deposit=MessageItem(text="Deposit options"),
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
                select_fixture=MessageItem(text="Select a fixture"),
                invalid_bet_amount=MessageItem(
                    text="Invalid amount, Enter your bet amount",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="5", callback_data="5"),
                                InlineKeyboardButton(text="10", callback_data="10"),
                            ]
                        ]
                    ),
                ),
                bet_amount=MessageItem(
                    text="Enter your bet amount",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="5", callback_data="5"),
                                InlineKeyboardButton(text="10", callback_data="10"),
                            ]
                        ]
                    ),
                ),
                select_type_of_bet=MessageItem(
                    text="Select type of bet",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Simple",
                                    callback_data="bet_simple&{FIXTURE_ID}",
                                ),
                                InlineKeyboardButton(
                                    text="Combo",
                                    callback_data="add_market_to_combo&{FIXTURE_ID}",
                                ),
                            ]
                        ]
                    ),
                ),
                fixture_odds=MessageItem(text="Here are the odds for the fixture."),
                unavailable_odds=MessageItem(text="Some odds are unavailable."),
                placed_bet=MessageItem(
                    text="Your bet has been placed successfully! 🤑 • Match: %1 • Bet Amount: %2 • Selection: %3 • Potential Win: %4 • Balance: %5"
                ),
                placed_bet_menu=MessageItem(
                    text="Your bet has been placed! What would you like to do next?"
                ),
                without_funds=MessageItem(
                    text="Insufficient funds. Please deposit to continue."
                ),
                deposit=MessageItem(
                    text="To deposit funds, please visit: https://example.com/deposit"
                ),
                bet_rejected=MessageItem(
                    text="Your bet was rejected. Please try again."
                ),
            ),
            combos=CombosMessages(
                show_all_markets_by_fixtures=MessageItem(text="Showing all markets"),
                error_to_add_market=MessageItem(text="Error adding market."),
                error_to_get_odds=MessageItem(text="Error retrieving odds."),
                error_to_place_bet=MessageItem(text="Error placing combo bet."),
                empty_combo=MessageItem(text="Sorry, there isn't any combo yet"),
                summary_after_add_market=MessageItem(
                    text="I’ve added that pick to your combo ✅ Your combo: {PICKS} Total odds: {TOTAL_ODDS}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="My Combo",
                                    callback_data="combo_show_my_combo",
                                ),
                            ]
                        ]
                    ),
                ),
                summary_after_remove_bet_from_combo=MessageItem(
                    text="I have eliminated the match {BET_REMOVED} This is your combo now {COMBO} • What would you like to do now?",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="My Combo",
                                    callback_data="combo_show_my_combo",
                                ),
                            ]
                        ]
                    ),
                ),
                remove_market=MessageItem(text="Remove a market from your combo"),
                select_amount=MessageItem(
                    text="Enter the amount for your combo bet",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(text="5", callback_data="5"),
                                InlineKeyboardButton(text="10", callback_data="10"),
                            ]
                        ]
                    ),
                ),
                place_combo_bet=MessageItem(
                    text="Do you want to confirm this combo with the following details? 👇 {COMBO} ∙ Amount {AMOUNT} ∙ Total Odds: {TOTAL_ODDS} ∙ Potential Win: {PROFIT}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Confirm Combo Bet",
                                    callback_data="combo_summary_after_bet",
                                )
                            ]
                        ]
                    ),
                ),
                summary_after_bet=MessageItem(
                    text="Your combo bet was placed successfully! 🤑 ∙ Combo: {COMBO} ∙ Amount: {AMOUNT} ∙ Potential Win: {PROFIT} ∙ Balance: {BALANCE}"
                ),
                show_my_combo=MessageItem(
                    text="You are currently viewing the following combo bet: ∙{SUMMARY_COMBO} ∙ Total Odds: {TOTAL_ODDS}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Confirm Combo Bet",
                                    callback_data="combo_select_amount",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="Delete Bet",
                                    callback_data="combo_delete_combo",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="Add Other Market",
                                    callback_data="combo_add_market",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="Remove Market",
                                    callback_data="combo_remove_market",
                                )
                            ],
                        ]
                    ),
                ),
                delete_combo=MessageItem(
                    text="Are you sure? Do you want to delete your combo bet?",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Yes Delete",
                                    callback_data="combo_confirm_delete_combo",
                                )
                            ]
                        ]
                    ),
                ),
                combo_odds=MessageItem(text="Here are the odds for your combo."),
                combos_recommendation=MessageItem(
                    text="Recommended combo: {PICKS} ∙ If you bet {AMOUNT} you can potentially win: {PROFIT}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Add Combo",
                                    callback_data="combo_select_amount_recommended",
                                )
                            ]
                        ]
                    ),
                ),
                combos_confirm_add_recommended=MessageItem(
                    text="Done! Your Combo has been successfully created ∙ {COMBO}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="View Combo",
                                    callback_data="combo_show_my_combo",
                                )
                            ]
                        ]
                    ),
                ),
            ),
            errors=ErrorMessages(
                invalid_input=MessageItem(text="Invalid input."),
                error=MessageItem(text="An error occurred."),
                error_2=MessageItem(text="Another error occurred."),
            ),
            confirmation=ConfirmationMessages(
                confirm_bet=MessageItem(
                    text="Bet Summary: ∙ Match: {DESCRIPTION_GAME} ∙ Bet Amount: {AMOUNT} ∙ Selection: {BET_NAME} ∙ Potential Win: {PROFIT}",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Place Combo",
                                    callback_data="confirm_bet",
                                )
                            ]
                        ]
                    ),
                )
            ),
            labels=LabelMessages(
                menu_label_text=MessageItem(text="Menu"),
                label_text=MessageItem(text="Label"),
                combo_summary_after_add_market_label_text=MessageItem(
                    text="Your combo"
                ),
                select_tournament_label_text=MessageItem(text="Tournaments"),
                select_fixture_label_text=MessageItem(text="Fixtures"),
                markets_without_combo_label_text=MessageItem(text="Markets"),
                select_sport_label_text=MessageItem(text="Sports"),
                more_options_text=MessageItem(text="More options"),
                combo_remove_market_label_text=MessageItem(text="Remove market"),
                selected_other_market_label_text=MessageItem(text="Selected"),
                other_markets_label_text=MessageItem(text="Other markets"),
                combo_odds_label_text=MessageItem(text="Combo odds"),
                fixture_odds_label_text=MessageItem(text="Fixture odds"),
                menu_more_options_text=MessageItem(text="More options"),
                list_markets_label_text=MessageItem(text="Markets"),
                list_fixtures_label_text=MessageItem(text="Fixtures"),
            ),
            end=EndMessages(
                end_conversation=MessageItem(text="Bye!"),
            ),
            guidance=GuidanceMessages(
                valid_input_text=MessageItem(text="Looks good ✅"),
                invalid_input_text=MessageItem(text="Please check your input ⚠️"),
                invalid_input_response=MessageItem(text="Invalid input, try again."),
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
