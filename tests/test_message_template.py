import pytest
from datetime import datetime

from chatbet_base_models.message_template import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageItem,
    OnboardingMessages,
    ValidationMessages,
    MenuMessages,
    BetsMessages,
    CombosMessages,
    ErrorMessages,
    MessageTemplates,
    MessageTemplatesDB,
)


class TestInlineKeyboardButton:
    def test_create_button_with_callback_data(self):
        button = InlineKeyboardButton(text="Test", callback_data="test_callback")
        assert button.text == "Test"
        assert button.callback_data == "test_callback"
        assert button.url is None

    def test_create_button_with_url(self):
        button = InlineKeyboardButton(text="Link", url="https://example.com")
        assert button.text == "Link"
        assert button.url == "https://example.com"
        assert button.callback_data is None

    def test_button_with_both_callback_and_url_raises_error(self):
        with pytest.raises(
            ValueError, match="Button must have either callback_data or url, not both"
        ):
            InlineKeyboardButton(
                text="Test", callback_data="test", url="https://example.com"
            )

    def test_button_with_neither_callback_nor_url_raises_error(self):
        with pytest.raises(
            ValueError, match="Button must define either callback_data or url"
        ):
            InlineKeyboardButton(text="Test")

    def test_callback_data_length_validation(self):
        with pytest.raises(ValueError, match="callback_data must be <= 64 characters"):
            InlineKeyboardButton(text="Test", callback_data="a" * 65)

    def test_empty_text_raises_error(self):
        with pytest.raises(ValueError):
            InlineKeyboardButton(text="", callback_data="test")


class TestInlineKeyboardMarkup:
    def test_create_empty_markup(self):
        markup = InlineKeyboardMarkup()
        assert markup.inline_keyboard == []

    def test_create_markup_with_buttons(self):
        buttons = [[InlineKeyboardButton(text="Test", callback_data="test")]]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        assert len(markup.inline_keyboard) == 1
        assert len(markup.inline_keyboard[0]) == 1
        assert markup.inline_keyboard[0][0].text == "Test"


class TestMessageItem:
    def test_create_message_with_text(self):
        message = MessageItem(text="Hello world")
        assert message.text == "Hello world"
        assert message.reply_markup is None

    def test_create_message_with_reply_markup(self):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Test", callback_data="test")]]
        )
        message = MessageItem(text="Hello", reply_markup=markup)
        assert message.text == "Hello"
        assert message.reply_markup is not None

    def test_coerce_string_to_message_item(self):
        result = MessageItem._coerce("Hello world")
        assert result == {"text": "Hello world"}

    def test_coerce_none_returns_none(self):
        result = MessageItem._coerce(None)
        assert result is None

    def test_coerce_dict_returns_dict(self):
        data = {"text": "Hello"}
        result = MessageItem._coerce(data)
        assert result == data

    def test_coerce_message_item_returns_as_is(self):
        message = MessageItem(text="Hello")
        result = MessageItem._coerce(message)
        assert result == message


class TestOnboardingMessages:
    def test_create_onboarding_messages(self):
        onboarding = OnboardingMessages(
            member_onboarding=MessageItem(
                text="Welcome",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Yes", callback_data="account_yes")],
                        [InlineKeyboardButton(text="No", callback_data="account_no")]
                    ]
                )
            ),
            greeting_message=MessageItem(text="Hello"),
        )
        assert onboarding.member_onboarding.text == "Welcome"
        assert onboarding.greeting_message.text == "Hello"

    def test_model_validate_with_string_coercion(self):
        data = {
            "member_onboarding": {
                "text": "Welcome to ChatBet",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "Yes", "callback_data": "account_yes"}],
                        [{"text": "No", "callback_data": "account_no"}]
                    ]
                }
            },
            "greeting_message": "Hello there!",
        }
        onboarding = OnboardingMessages.model_validate(data)
        assert onboarding.member_onboarding.text == "Welcome to ChatBet"
        assert onboarding.greeting_message.text == "Hello there!"


class TestValidationMessages:
    def test_create_validation_messages(self):
        validation = ValidationMessages(
            member_validation=MessageItem(text="Please validate"),
            send_otp=MessageItem(
                text="OTP sent",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Send OTP", callback_data="send_otp")]
                    ]
                )
            ),
        )
        assert validation.member_validation.text == "Please validate"
        assert validation.send_otp.text == "OTP sent"


class TestMenuMessages:
    def test_create_menu_messages(self):
        menu = MenuMessages(
            main_menu=MessageItem(
                text="Main Menu",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Bet", callback_data="bet")]
                    ]
                )
            ), 
            support=MessageItem(text="Support")
        )
        assert menu.main_menu.text == "Main Menu"
        assert menu.support.text == "Support"

    def test_legacy_key_aliases(self):
        data = {
            "main_menu": {
                "text": "Main Menu",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "Bet", "callback_data": "bet"}]
                    ]
                }
            },
            "support_message": "Support Help",
            "withdrawal_message": "Withdraw Funds",
            "deposit_message": "Deposit Money",
            "show_links_message": "Quick Links",
        }
        menu = MenuMessages.model_validate(data)
        assert menu.main_menu.text == "Main Menu"
        assert menu.support.text == "Support Help"
        assert menu.withdrawal.text == "Withdraw Funds"
        assert menu.deposit.text == "Deposit Money"
        assert menu.show_links.text == "Quick Links"


class TestBetsMessages:
    def test_create_bets_messages(self):
        bets = BetsMessages(
            select_sport=MessageItem(text="Select sport"),
            bet_amount=MessageItem(text="Enter amount"),
        )
        assert bets.select_sport.text == "Select sport"
        assert bets.bet_amount.text == "Enter amount"


class TestCombosMessages:
    def test_create_combos_messages(self):
        combos = CombosMessages(
            show_all_markets_by_fixtures=MessageItem(text="Markets"),
            select_amount=MessageItem(text="Amount"),
        )
        assert combos.show_all_markets_by_fixtures.text == "Markets"
        assert combos.select_amount.text == "Amount"

    def test_typo_correction_and_defaults(self):
        data = {
            "errro_to_place_bet": "Error placing bet",
            "sumary_after_add_market": "Summary after adding",
        }
        combos = CombosMessages.model_validate(data)
        assert combos.error_to_place_bet.text == "Error placing bet"
        assert combos.summary_after_add_market.text == "Summary after adding"
        # Check defaults are set
        assert combos.combos_recommendation.text == "Recommended combos"
        assert (
            combos.combos_confirm_add_recommended.text
            == "Do you want to add these recommended combos?"
        )


class TestErrorMessages:
    def test_create_error_messages_with_general_errors(self):
        error_messages = ErrorMessages(
            invalid_input=MessageItem(text="Invalid input"),
            general_errors={
                "es": ["Error 1 en español", "Error 2 en español"],
                "en": ["Error 1 in English", "Error 2 in English"],
            }
        )
        assert error_messages.invalid_input.text == "Invalid input"
        assert error_messages.general_errors is not None
        assert len(error_messages.general_errors["es"]) == 2
        assert len(error_messages.general_errors["en"]) == 2
        assert error_messages.general_errors["es"][0] == "Error 1 en español"

    def test_general_errors_from_minimal(self):
        templates = MessageTemplates.from_minimal()
        assert templates.errors is not None
        assert templates.errors.general_errors is not None
        assert "es" in templates.errors.general_errors
        assert "en" in templates.errors.general_errors
        assert "pt-br" in templates.errors.general_errors
        assert len(templates.errors.general_errors["es"]) == 10
        assert len(templates.errors.general_errors["en"]) == 10
        assert len(templates.errors.general_errors["pt-br"]) == 10

    def test_model_validate_with_general_errors(self):
        data = {
            "invalid_input": "Invalid input text",
            "error": "An error occurred",
            "general_errors": {
                "es": ["Error español"],
                "en": ["English error"],
            }
        }
        error_messages = ErrorMessages.model_validate(data)
        assert error_messages.invalid_input.text == "Invalid input text"
        assert error_messages.error.text == "An error occurred"
        assert error_messages.general_errors["es"] == ["Error español"]
        assert error_messages.general_errors["en"] == ["English error"]

    def test_general_errors_in_dynamodb_item(self):
        templates = MessageTemplates.from_minimal()
        item = templates.to_dynamodb_item()
        assert "errors" in item
        assert "general_errors" in item["errors"]
        assert "es" in item["errors"]["general_errors"]
        assert len(item["errors"]["general_errors"]["es"]) == 10

    def test_general_errors_defaults_when_not_provided(self):
        """Test that general_errors gets default values when not provided."""
        data = {
            "invalid_input": "Invalid input text",
            "error": "An error occurred",
        }
        error_messages = ErrorMessages.model_validate(data)
        assert error_messages.general_errors is not None
        assert "es" in error_messages.general_errors
        assert "en" in error_messages.general_errors
        assert "pt-br" in error_messages.general_errors
        assert len(error_messages.general_errors["es"]) == 10
        assert len(error_messages.general_errors["en"]) == 10
        assert len(error_messages.general_errors["pt-br"]) == 10

    def test_general_errors_defaults_with_direct_constructor(self):
        """Test that general_errors gets default values when using direct constructor."""
        error_messages = ErrorMessages()
        assert error_messages.general_errors is not None
        assert "es" in error_messages.general_errors
        assert "en" in error_messages.general_errors
        assert "pt-br" in error_messages.general_errors
        assert len(error_messages.general_errors["es"]) == 10


class TestMessageTemplates:
    def test_create_empty_message_templates(self):
        templates = MessageTemplates()
        assert isinstance(templates.created_at, datetime)
        assert isinstance(templates.updated_at, datetime)

    def test_from_minimal_factory(self):
        templates = MessageTemplates.from_minimal()
        assert templates.onboarding is not None
        assert templates.validation is not None
        assert templates.registration is not None
        assert templates.menu is not None
        assert templates.bets is not None
        assert templates.combos is not None
        assert templates.errors is not None
        assert templates.confirmation is not None
        assert templates.labels is not None
        assert templates.end is not None
        assert templates.guidance is not None

        # Check some specific values
        assert templates.onboarding.member_onboarding.text == "Welcome to our chatbot!"
        assert templates.validation.send_otp.text == "We've sent you an OTP."
        assert templates.bets.select_sport.text == "Select a sport"

    def test_touch_method(self):
        templates = MessageTemplates()
        original_time = templates.updated_at
        templates.touch()
        assert templates.updated_at > original_time

    def test_to_dynamodb_item(self):
        templates = MessageTemplates.from_minimal()
        item = templates.to_dynamodb_item()

        assert isinstance(item, dict)
        assert "created_at" in item
        assert "updated_at" in item
        assert "onboarding" in item
        assert isinstance(item["created_at"], str)  # Should be ISO format string

    def test_to_dynamodb_item_drop_none(self):
        templates = MessageTemplates()
        item = templates.to_dynamodb_item(drop_none=True)

        # Should not contain None values
        def check_no_none_values(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    check_no_none_values(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            check_no_none_values(item)
                else:
                    assert value is not None, f"Found None value for key: {key}"

        check_no_none_values(item)


class TestMessageTemplatesDB:
    def test_create_message_templates_db(self):
        templates_db = MessageTemplatesDB(PK="company#123", SK="message_templates")
        assert templates_db.PK == "company#123"
        assert templates_db.SK == "message_templates"

    def test_from_minimal_factory(self):
        templates_db = MessageTemplatesDB.from_minimal("test_company")
        assert templates_db.PK == "company#test_company"
        assert templates_db.SK == "message_templates"
        assert templates_db.onboarding is not None

    def test_validation_requires_pk_sk(self):
        with pytest.raises(ValueError, match="PK and SK are required"):
            MessageTemplatesDB()

    def test_validation_requires_both_keys(self):
        with pytest.raises(ValueError, match="PK and SK are required"):
            MessageTemplatesDB(PK="company#123")

        with pytest.raises(ValueError, match="PK and SK are required"):
            MessageTemplatesDB(SK="message_templates")
