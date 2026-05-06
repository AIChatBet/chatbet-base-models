import pytest
from datetime import datetime, timezone

from pydantic import ValidationError

from chatbet_base_models.message_template import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabelMessages,
    MessageItem,
    OnboardingMessages,
    ValidationMessages,
    MenuMessages,
    BetsMessages,
    CombosMessages,
    ErrorMessages,
    MessageTemplates,
    MessageTemplatesDB,
    LinkItem,
    LinksMessages,
    DEFAULT_LINKS,
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
                        [InlineKeyboardButton(text="No", callback_data="account_no")],
                    ]
                ),
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
                        [{"text": "No", "callback_data": "account_no"}],
                    ]
                },
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
                        [
                            InlineKeyboardButton(
                                text="Send OTP", callback_data="send_otp"
                            )
                        ]
                    ]
                ),
            ),
        )
        assert validation.member_validation.text == "Please validate"
        assert validation.send_otp.text == "OTP sent"


# Password-auth POC templates — keys live under `validation.*` alongside OTP
# templates (sibling auth namespace). See SDD change `password-auth-poc`.
PASSWORD_TEMPLATE_KEYS = (
    "password_required",
    "password_form_invalid",
    "password_failed",
    "password_already_registered",
    "password_ok_register",
    "password_ok_login",
)


class TestValidationMessagesPasswordTemplates:
    """Validate the password-auth POC templates added under ValidationMessages."""

    def test_password_templates_default_to_none_on_bare_validation_messages(self):
        validation = ValidationMessages()
        for key in PASSWORD_TEMPLATE_KEYS:
            assert getattr(validation, key) is None, (
                f"{key} must default to None when not provided"
            )

    def test_from_minimal_provides_password_template_defaults(self):
        templates = MessageTemplates.from_minimal()
        assert templates.validation is not None
        assert (
            templates.validation.password_required.text
            == "Para continuar, completá el formulario rápido 👇"
        )
        assert (
            templates.validation.password_form_invalid.text
            == "Faltan datos en el formulario. Volvé a intentar."
        )
        assert (
            templates.validation.password_failed.text
            == "No pudimos validar tus datos. Verificá e intentá de nuevo."
        )
        assert (
            templates.validation.password_already_registered.text
            == "Esta cuenta ya está registrada. Iniciá sesión."
        )
        assert templates.validation.password_ok_register.text == "✅ ¡Cuenta creada!"
        assert templates.validation.password_ok_login.text == "✅ ¡Sesión iniciada!"

    def test_password_templates_override_via_constructor(self):
        validation = ValidationMessages(
            password_required=MessageItem(text="Custom required"),
            password_form_invalid=MessageItem(text="Custom invalid"),
            password_failed=MessageItem(text="Custom failed"),
            password_already_registered=MessageItem(text="Custom already"),
            password_ok_register=MessageItem(text="Custom ok register"),
            password_ok_login=MessageItem(text="Custom ok login"),
        )
        assert validation.password_required.text == "Custom required"
        assert validation.password_form_invalid.text == "Custom invalid"
        assert validation.password_failed.text == "Custom failed"
        assert validation.password_already_registered.text == "Custom already"
        assert validation.password_ok_register.text == "Custom ok register"
        assert validation.password_ok_login.text == "Custom ok login"

    def test_password_templates_override_via_model_validate_string_coercion(self):
        """Plain strings must coerce to MessageItem({"text": ...}) for the new keys
        (matches the existing convention used by every sibling field)."""
        data = {
            "password_required": "Form please",
            "password_form_invalid": "Bad form",
            "password_failed": "Auth failed",
            "password_already_registered": "Already registered",
            "password_ok_register": "Register OK",
            "password_ok_login": "Login OK",
        }
        validation = ValidationMessages.model_validate(data)
        assert validation.password_required.text == "Form please"
        assert validation.password_form_invalid.text == "Bad form"
        assert validation.password_failed.text == "Auth failed"
        assert validation.password_already_registered.text == "Already registered"
        assert validation.password_ok_register.text == "Register OK"
        assert validation.password_ok_login.text == "Login OK"

    def test_password_templates_unknown_key_rejected(self):
        """`extra=forbid` must keep working — typos must be caught at parse time."""
        with pytest.raises(ValidationError):
            ValidationMessages.model_validate(
                {"password_unknown_key": "should not be accepted"}
            )

    def test_password_templates_serialize_in_dynamodb_item(self):
        templates = MessageTemplates.from_minimal()
        item = templates.to_dynamodb_item()
        assert "validation" in item
        for key in PASSWORD_TEMPLATE_KEYS:
            assert key in item["validation"], (
                f"{key} must be present in DynamoDB serialization"
            )
            assert item["validation"][key]["text"], (
                f"{key} must have non-empty text in DynamoDB serialization"
            )


class TestMenuMessages:
    def test_create_menu_messages(self):
        menu = MenuMessages(
            main_menu=MessageItem(
                text="Main Menu",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Bet", callback_data="bet")]
                    ]
                ),
            )
        )
        assert menu.main_menu.text == "Main Menu"


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
            },
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
            },
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

    def test_bet_error_defaults_when_not_provided(self):
        """Test that bet_error gets a default value when not provided."""
        data = {
            "invalid_input": "Invalid input text",
            "error": "An error occurred",
        }
        error_messages = ErrorMessages.model_validate(data)
        assert error_messages.bet_error is not None
        assert (
            error_messages.bet_error.text
            == "Sorry, your bet was rejected, please try again later."
        )

    def test_bet_error_defaults_when_none(self):
        """Test that bet_error gets a default value when explicitly set to None."""
        data = {
            "invalid_input": "Invalid input text",
            "bet_error": None,
        }
        error_messages = ErrorMessages.model_validate(data)
        assert error_messages.bet_error is not None
        assert (
            error_messages.bet_error.text
            == "Sorry, your bet was rejected, please try again later."
        )

    def test_bet_error_preserves_custom_value(self):
        """Test that custom bet_error values are preserved."""
        data = {
            "invalid_input": "Invalid input text",
            "bet_error": {"text": "Custom bet error message"},
        }
        error_messages = ErrorMessages.model_validate(data)
        assert error_messages.bet_error is not None
        assert error_messages.bet_error.text == "Custom bet error message"


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
        templates.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
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


class TestLinkItem:
    """Test individual link item model"""

    def test_create_link_item(self):
        """Test creating a link item with all fields"""
        link = LinkItem(
            title="Help Center",
            message_text="Visit our help center for assistance",
            button_label="Get Help",
            button_url="https://example.com/help",
        )
        assert link.title == "Help Center"
        assert link.message_text == "Visit our help center for assistance"
        assert link.button_label == "Get Help"
        assert link.button_url == "https://example.com/help"

    def test_title_validation_strips_whitespace(self):
        """Test that title whitespace is stripped"""
        link = LinkItem(
            title="  Support  ",
            message_text="Contact support",
            button_label="Contact Us",
            button_url="https://example.com/support",
        )
        assert link.title == "Support"

    def test_title_validation_empty_raises_error(self):
        """Test that empty title raises validation error"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            LinkItem(
                title="   ",
                message_text="Text",
                button_label="Label",
                button_url="https://example.com",
            )

    def test_message_text_validation_empty_raises_error(self):
        """Test that empty message_text raises error"""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            LinkItem(
                title="Title",
                message_text="   ",
                button_label="Label",
                button_url="https://example.com",
            )

    def test_button_label_validation_empty_raises_error(self):
        """Test that empty button_label raises error"""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="   ",
                button_url="https://example.com",
            )

    def test_button_url_validation_requires_protocol(self):
        """Test that button_url must start with http:// or https://"""
        with pytest.raises(ValueError, match="must start with http"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="example.com",
            )

    def test_button_url_validation_accepts_https(self):
        """Test that https:// URLs are valid"""
        link = LinkItem(
            title="Title",
            message_text="Text",
            button_label="Label",
            button_url="https://example.com",
        )
        assert link.button_url == "https://example.com"

    def test_button_url_validation_accepts_http(self):
        """Test that http:// URLs are valid"""
        link = LinkItem(
            title="Title",
            message_text="Text",
            button_label="Label",
            button_url="http://example.com",
        )
        assert link.button_url == "http://example.com"

    def test_button_url_validation_empty_raises_error(self):
        """Test that empty button_url raises error"""
        with pytest.raises(ValueError, match="button_url cannot be empty"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="   ",
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected"""
        with pytest.raises(ValueError):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="https://example.com",
                extra_field="not allowed",
            )

    def test_follow_up_defaults_to_none(self):
        """CU-86ah4m4zy: follow_up is optional and defaults to None so
        operators that haven't configured a follow-up message keep the
        existing single-message redirection behavior."""
        link = LinkItem(
            title="Support",
            message_text="Need help?",
            button_label="Contact Support",
            button_url="https://example.com/support",
        )
        assert link.follow_up is None

    def test_follow_up_accepts_message_item_with_reply_markup(self):
        """CU-86ah4m4zy: follow_up accepts a MessageItem with text and
        an inline_keyboard so the bot can chain a second message after
        the link with operator-defined buttons."""
        link = LinkItem(
            title="Support",
            message_text="Need help?",
            button_label="Contact Support",
            button_url="https://example.com/support",
            follow_up=MessageItem(
                text="Anything else?",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Menu", callback_data="menu"
                            ),
                            InlineKeyboardButton(
                                text="Bet", callback_data="bet"
                            ),
                        ]
                    ]
                ),
            ),
        )
        assert link.follow_up is not None
        assert link.follow_up.text == "Anything else?"
        assert link.follow_up.reply_markup is not None
        rows = link.follow_up.reply_markup.inline_keyboard
        assert len(rows) == 1
        callbacks = sorted(btn.callback_data for btn in rows[0])
        assert callbacks == ["bet", "menu"]

    def test_follow_up_serializes_and_round_trips(self):
        """``model_dump`` preserves follow_up so DynamoDB persistence
        and BO round-tripping work end-to-end."""
        original = LinkItem(
            title="Support",
            message_text="Need help?",
            button_label="Contact Support",
            button_url="https://example.com/support",
            follow_up=MessageItem(text="See you soon!"),
        )
        dumped = original.model_dump()
        assert dumped["follow_up"]["text"] == "See you soon!"
        assert dumped["follow_up"].get("reply_markup") is None
        rebuilt = LinkItem.model_validate(dumped)
        assert rebuilt == original


class TestLinksMessages:
    """Test links messages container"""

    def test_create_empty_links_messages(self):
        """Test creating links messages with defaults"""
        links = LinksMessages()
        # Now includes 6 default links instead of empty array
        assert len(links.links) == 6

    def test_create_links_messages_with_items(self):
        """Test creating links messages with items including required defaults"""
        # Must include all 6 required links
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]

        # Add custom links
        custom_link = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )

        links = LinksMessages(links=required_links + [custom_link])
        assert len(links.links) == 7  # 6 required + 1 custom
        assert any(link.title == "Help" for link in links.links)
        assert any(
            link.title == "Support" for link in links.links
        )  # From required defaults

    def test_duplicate_titles_validation_raises_error(self):
        """Test that duplicate titles raise validation error"""
        link1 = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )
        link2 = LinkItem(
            title="Help",
            message_text="Different message",
            button_label="Different Label",
            button_url="https://example.com/help2",
        )

        with pytest.raises(ValueError, match="Duplicate link titles"):
            LinksMessages(links=[link1, link2])

    def test_duplicate_titles_case_insensitive(self):
        """Test that duplicate title checking is case-insensitive"""
        link1 = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )
        link2 = LinkItem(
            title="HELP",
            message_text="Different message",
            button_label="Different Label",
            button_url="https://example.com/help2",
        )

        with pytest.raises(ValueError, match="Duplicate link titles"):
            LinksMessages(links=[link1, link2])

    def test_max_links_validation(self):
        """Test maximum links validation"""
        links_items = [
            LinkItem(
                title=f"Link{i}",
                message_text=f"Message {i}",
                button_label=f"Label {i}",
                button_url=f"https://example.com/{i}",
            )
            for i in range(101)
        ]

        with pytest.raises(ValueError, match="Maximum 100 links"):
            LinksMessages(links=links_items)

    def test_100_links_is_valid(self):
        """Test that exactly 100 links is valid (6 required + 94 custom)"""
        # Include 6 required links
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]

        # Add 94 custom links (6 + 94 = 100)
        custom_links = [
            LinkItem(
                title=f"Link{i}",
                message_text=f"Message {i}",
                button_label=f"Label {i}",
                button_url=f"https://example.com/{i}",
            )
            for i in range(94)
        ]

        links = LinksMessages(links=required_links + custom_links)
        assert len(links.links) == 100

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected"""
        with pytest.raises(ValueError):
            LinksMessages(links=[], extra_field="not allowed")


class TestLinksMessagesDefaultLinks:
    """Test default links functionality and validation"""

    def test_default_links_present_on_initialization(self):
        """Test that 7 default links are present when LinksMessages is created"""
        links = LinksMessages()
        assert len(links.links) == 6

        # Check all required titles are present
        titles = {link.title.lower() for link in links.links}
        assert titles == {
            "support",
            "main site",
            "sign up",
            "withdrawal",
            "deposit",
            "bet results",
        }

    def test_default_links_have_correct_structure(self):
        """Test that default links have all required fields"""
        links = LinksMessages()

        for link in links.links:
            assert link.title
            assert link.message_text
            assert link.button_label
            assert link.button_url
            assert link.button_url.startswith(("http://", "https://"))

    def test_validation_fails_when_required_link_missing(self):
        """Test that validation fails if any required link is deleted"""
        # Create with defaults then try to create without one
        link1 = LinkItem(
            title="Support",
            message_text="Contact support",
            button_label="Get Support",
            button_url="https://example.com/support",
        )
        link2 = LinkItem(
            title="Main site",
            message_text="Visit site",
            button_label="Go to Site",
            button_url="https://example.com",
        )
        # Missing: Sign up, Withdrawal, Deposit, Bet results

        with pytest.raises(ValueError, match="Missing required link titles"):
            LinksMessages(links=[link1, link2])

    def test_validation_fails_with_clear_error_message(self):
        """Test that error message lists missing required links"""
        link1 = LinkItem(
            title="Support",
            message_text="Contact support",
            button_label="Get Support",
            button_url="https://example.com/support",
        )

        with pytest.raises(ValueError) as exc_info:
            LinksMessages(links=[link1])

        error_message = str(exc_info.value)
        assert "Missing required link titles" in error_message
        assert "bet results" in error_message.lower()
        assert "deposit" in error_message.lower()
        assert "withdrawal" in error_message.lower()

    def test_required_links_case_insensitive(self):
        """Test that required link validation is case-insensitive"""
        # Create links with different casing
        links_data = [
            {
                "title": "SUPPORT",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/support",
            },
            {
                "title": "Main Site",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com",
            },
            {
                "title": "sign up",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/signup",
            },
            {
                "title": "WithDrawal",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/withdrawal",
            },
            {
                "title": "deposit",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/deposit",
            },
            {
                "title": "BET RESULTS",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/results",
            },
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]
        links = LinksMessages(links=links_items)

        # Should not raise error
        assert len(links.links) == 6

    def test_users_can_modify_default_link_content(self):
        """Test that users can modify message_text, button_label, button_url of default links"""
        # Modify content of default links
        modified_links = [
            LinkItem(
                title="Support",
                message_text="Custom support message",
                button_label="Custom Support Button",
                button_url="https://custom.com/support",
            ),
            LinkItem(
                title="Main site",
                message_text="Custom site message",
                button_label="Custom Site Button",
                button_url="https://custom.com",
            ),
            LinkItem(
                title="Sign up",
                message_text="Custom signup message",
                button_label="Custom Signup Button",
                button_url="https://custom.com/signup",
            ),
            LinkItem(
                title="Withdrawal",
                message_text="Custom withdrawal message",
                button_label="Custom Withdrawal Button",
                button_url="https://custom.com/withdrawal",
            ),
            LinkItem(
                title="Deposit",
                message_text="Custom deposit message",
                button_label="Custom Deposit Button",
                button_url="https://custom.com/deposit",
            ),
            LinkItem(
                title="Bet results",
                message_text="Custom results message",
                button_label="Custom Results Button",
                button_url="https://custom.com/results",
            ),
        ]

        links = LinksMessages(links=modified_links)

        # Should not raise error
        assert len(links.links) == 6
        assert links.links[0].message_text == "Custom support message"
        assert links.links[0].button_url == "https://custom.com/support"

    def test_users_can_add_additional_links(self):
        """Test that users can add links beyond the required 6"""
        # Start with default links
        links = LinksMessages()

        # Add additional links
        additional_link = LinkItem(
            title="FAQ",
            message_text="Frequently asked questions",
            button_label="View FAQ",
            button_url="https://example.com/faq",
        )

        all_links = links.links + [additional_link]
        links_with_extra = LinksMessages(links=all_links)

        assert len(links_with_extra.links) == 7
        assert any(link.title == "FAQ" for link in links_with_extra.links)

    def test_validation_allows_required_plus_additional_links(self):
        """Test that validation passes with required + additional links"""
        # Create required links + 3 additional
        links_data = [
            {
                "title": "Support",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/support",
            },
            {
                "title": "Main site",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com",
            },
            {
                "title": "Sign up",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/signup",
            },
            {
                "title": "Withdrawal",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/withdrawal",
            },
            {
                "title": "Deposit",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/deposit",
            },
            {
                "title": "Bet results",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/results",
            },
            {
                "title": "FAQ",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/faq",
            },
            {
                "title": "Terms",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/terms",
            },
            {
                "title": "Privacy",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/privacy",
            },
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]
        links = LinksMessages(links=links_items)

        assert len(links.links) == 9

    def test_duplicate_title_validation_still_works(self):
        """Test that duplicate title validation works with default links"""
        # Try to create links with duplicate in additional links
        links_data = [
            {
                "title": "Support",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/support",
            },
            {
                "title": "Main site",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com",
            },
            {
                "title": "Sign up",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/signup",
            },
            {
                "title": "Withdrawal",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/withdrawal",
            },
            {
                "title": "Deposit",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/deposit",
            },
            {
                "title": "Bet results",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/results",
            },
            {
                "title": "Support",
                "message_text": "Different text",
                "button_label": "Different",
                "button_url": "https://example.com/support2",
            },
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]

        with pytest.raises(ValueError, match="Duplicate link titles"):
            LinksMessages(links=links_items)

    def test_max_100_links_validation_still_works(self):
        """Test that max 100 links validation works with defaults"""
        # Create 6 required + 95 additional = 101 total
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]
        additional_links = [
            LinkItem(
                title=f"Extra{i}",
                message_text=f"Message {i}",
                button_label=f"Label {i}",
                button_url=f"https://example.com/extra{i}",
            )
            for i in range(95)
        ]

        all_links = required_links + additional_links

        with pytest.raises(ValueError, match="Maximum 100 links"):
            LinksMessages(links=all_links)

    def test_default_links_use_placeholder_urls(self):
        """Test that default links use https://example.com placeholder URLs"""
        links = LinksMessages()

        for link in links.links:
            # All default URLs should use example.com domain
            assert "example.com" in link.button_url.lower()

    def test_changing_title_of_required_link_breaks_validation(self):
        """Test that changing title of a required link causes validation failure"""
        # Take default links and change one title
        links_data = [
            {
                "title": "Support",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/support",
            },
            {
                "title": "Main site",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com",
            },
            {
                "title": "Sign up",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/signup",
            },
            {
                "title": "Withdrawal",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/withdrawal",
            },
            {
                "title": "Deposit",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/deposit",
            },
            {
                "title": "Results Page",
                "message_text": "Text",
                "button_label": "Label",
                "button_url": "https://example.com/results",
            },  # Changed from "Bet results"
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]

        with pytest.raises(ValueError, match="Missing required link titles"):
            LinksMessages(links=links_items)


class TestLinksMessagesHelperMethods:
    """Test helper methods for accessing default links"""

    def test_get_support_link(self):
        """Test retrieving support link by helper method"""
        links = LinksMessages()
        support = links.get_support_link()

        assert isinstance(support, LinkItem)
        assert support.title == "Support"
        assert support.message_text
        assert support.button_label
        assert support.button_url

    def test_get_main_site_link(self):
        """Test retrieving main site link by helper method"""
        links = LinksMessages()
        main_site = links.get_main_site_link()

        assert isinstance(main_site, LinkItem)
        assert main_site.title == "Main site"
        assert main_site.message_text
        assert main_site.button_label
        assert main_site.button_url

    def test_get_sign_up_link(self):
        """Test retrieving sign up link by helper method"""
        links = LinksMessages()
        sign_up = links.get_sign_up_link()

        assert isinstance(sign_up, LinkItem)
        assert sign_up.title == "Sign up"
        assert sign_up.message_text
        assert sign_up.button_label
        assert sign_up.button_url

    def test_get_withdrawal_link(self):
        """Test retrieving withdrawal link by helper method"""
        links = LinksMessages()
        withdrawal = links.get_withdrawal_link()

        assert isinstance(withdrawal, LinkItem)
        assert withdrawal.title == "Withdrawal"
        assert withdrawal.message_text
        assert withdrawal.button_label
        assert withdrawal.button_url

    def test_get_deposit_link(self):
        """Test retrieving deposit link by helper method"""
        links = LinksMessages()
        deposit = links.get_deposit_link()

        assert isinstance(deposit, LinkItem)
        assert deposit.title == "Deposit"
        assert deposit.message_text
        assert deposit.button_label
        assert deposit.button_url

    def test_get_bet_results_link(self):
        """Test retrieving bet results link by helper method"""
        links = LinksMessages()
        bet_results = links.get_bet_results_link()

        assert isinstance(bet_results, LinkItem)
        assert bet_results.title == "Bet results"
        assert bet_results.message_text
        assert bet_results.button_label
        assert bet_results.button_url

    def test_helper_methods_return_correct_links(self):
        """Test that all helper methods return the correct links"""
        links = LinksMessages()

        assert links.get_support_link().title == "Support"
        assert links.get_main_site_link().title == "Main site"
        assert links.get_sign_up_link().title == "Sign up"
        assert links.get_withdrawal_link().title == "Withdrawal"
        assert links.get_deposit_link().title == "Deposit"
        assert links.get_bet_results_link().title == "Bet results"

    def test_helper_methods_with_modified_content(self):
        """Verify methods work when link content is modified"""
        links = LinksMessages()

        # Modify support link content
        for link in links.links:
            if link.title == "Support":
                link.button_url = "https://custom.com/support"

        support = links.get_support_link()
        assert support.button_url == "https://custom.com/support"

    def test_get_link_by_title_case_insensitive(self):
        """Verify the generic helper is case-insensitive"""
        links = LinksMessages()

        # Should work with different casing
        support1 = links._get_link_by_title("Support")
        support2 = links._get_link_by_title("support")
        support3 = links._get_link_by_title("SUPPORT")

        assert support1.title == support2.title == support3.title

    def test_helper_methods_with_additional_links(self):
        """Verify methods work when additional custom links present"""
        custom_link = LinkItem(
            title="Custom Link",
            message_text="Custom message",
            button_label="Custom",
            button_url="https://custom.com",
        )

        # Create links with default links plus custom
        default_link_items = [LinkItem(**link) for link in DEFAULT_LINKS]
        links = LinksMessages(links=default_link_items + [custom_link])

        # Should still find default links
        assert links.get_support_link().title == "Support"
        assert len(links.links) == 7  # 6 default + 1 custom

    def test_get_link_by_title_not_found_raises_error(self):
        """Verify clear error when link not found"""
        links = LinksMessages()

        with pytest.raises(ValueError, match="Link with title 'Nonexistent' not found"):
            links._get_link_by_title("Nonexistent")


class TestMessageTemplatesDefaultLinks:
    """Test MessageTemplates integration with default links"""

    def test_from_minimal_includes_default_links(self):
        """Test that from_minimal includes 6 default links"""
        templates = MessageTemplates.from_minimal()

        assert templates.links is not None
        assert len(templates.links.links) == 6

        # Check required titles are present
        titles = {link.title.lower() for link in templates.links.links}
        assert "support" in titles
        assert "main site" in titles
        assert "sign up" in titles
        assert "withdrawal" in titles
        assert "deposit" in titles
        assert "bet results" in titles

    def test_message_templates_db_from_minimal_includes_default_links(self):
        """Test that MessageTemplatesDB.from_minimal includes default links"""
        templates_db = MessageTemplatesDB.from_minimal("test_company")

        assert templates_db.links is not None
        assert len(templates_db.links.links) == 6
        assert templates_db.PK == "company#test_company"
        assert templates_db.SK == "message_templates"

    def test_to_dynamodb_item_includes_default_links(self):
        """Test that DynamoDB serialization includes default links"""
        templates = MessageTemplates.from_minimal()
        item = templates.to_dynamodb_item()

        assert "links" in item
        assert "links" in item["links"]
        assert isinstance(item["links"]["links"], list)
        assert len(item["links"]["links"]) == 6

        # Check structure of first link
        first_link = item["links"]["links"][0]
        assert "title" in first_link
        assert "message_text" in first_link
        assert "button_label" in first_link
        assert "button_url" in first_link


class TestMessageTemplatesWithLinks:
    """Test MessageTemplates integration with links"""

    def test_from_minimal_includes_default_links_legacy(self):
        """Test that from_minimal includes default links (legacy test updated)"""
        templates = MessageTemplates.from_minimal()
        assert templates.links is not None
        # Now includes 6 default links instead of empty array
        assert len(templates.links.links) == 6

    def test_create_message_templates_with_links(self):
        """Test creating MessageTemplates with links including required defaults"""
        # Must include all 6 required links
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]

        # Add custom link
        custom_link = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )

        templates = MessageTemplates(
            links=LinksMessages(links=required_links + [custom_link])
        )

        assert templates.links is not None
        assert len(templates.links.links) == 7  # 6 required + 1 custom
        assert any(link.title == "Help" for link in templates.links.links)

    def test_to_dynamodb_item_includes_links(self):
        """Test DynamoDB serialization includes links"""
        # Use default links (6 required)
        templates = MessageTemplates()

        item = templates.to_dynamodb_item()
        assert "links" in item
        assert "links" in item["links"]
        assert isinstance(item["links"]["links"], list)
        assert len(item["links"]["links"]) == 6  # 6 required default links
        assert item["links"]["links"][0]["title"] == "Support"  # First default link
        assert "example.com" in item["links"]["links"][0]["button_url"]

    def test_to_dynamodb_item_empty_links(self):
        """Test DynamoDB serialization with default links"""
        templates = MessageTemplates.from_minimal()
        item = templates.to_dynamodb_item()

        assert "links" in item
        # Now includes 6 default links instead of empty array
        assert len(item["links"]["links"]) == 6

    def test_message_templates_db_with_links(self):
        """Test MessageTemplatesDB with links including required defaults"""
        # Must include all 6 required links
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]

        # Add custom link
        custom_link = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )

        templates_db = MessageTemplatesDB(
            PK="company#123",
            SK="message_templates",
            links=LinksMessages(links=required_links + [custom_link]),
        )

        assert templates_db.links is not None
        assert len(templates_db.links.links) == 7  # 6 required + 1 custom
        assert any(link.title == "Help" for link in templates_db.links.links)

    def test_message_templates_db_from_minimal_includes_links(self):
        """Test MessageTemplatesDB.from_minimal includes default links"""
        templates_db = MessageTemplatesDB.from_minimal("test_company")

        assert templates_db.links is not None
        # Now includes 6 default links instead of empty array
        assert len(templates_db.links.links) == 6
        assert templates_db.PK == "company#test_company"
        assert templates_db.SK == "message_templates"

    def test_touch_method_works_with_links(self):
        """Test that touch() method works with links present"""
        templates = MessageTemplates.from_minimal()
        templates.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        original_time = templates.updated_at
        templates.touch()
        assert templates.updated_at > original_time

    def test_links_field_has_default(self):
        """Test that links field defaults to 7 required links"""
        templates = MessageTemplates()
        assert templates.links is not None
        assert isinstance(templates.links, LinksMessages)
        # Now includes 6 default links instead of empty array
        assert len(templates.links.links) == 6

    def test_multiple_links_different_urls(self):
        """Test creating multiple links with different URLs including required defaults"""
        # Must include all 6 required links
        required_links = [LinkItem(**link) for link in DEFAULT_LINKS]

        # Add custom links
        link1 = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help",
        )
        link2 = LinkItem(
            title="FAQ",
            message_text="Frequently asked questions",
            button_label="View FAQ",
            button_url="https://example.com/faq",
        )

        templates = MessageTemplates(
            links=LinksMessages(links=required_links + [link1, link2])
        )

        assert len(templates.links.links) == 8  # 6 required + 2 custom
        assert any(link.title == "Help" for link in templates.links.links)
        assert any(
            link.title == "Support" for link in templates.links.links
        )  # From required defaults
        assert any(link.title == "FAQ" for link in templates.links.links)


class TestLabelMessagesNewFields:
    """Tests for the 18 new fields added to LabelMessages."""

    NEW_FIELDS = [
        "back_option",
        "home_page_text",
        "profit_text",
        "remove_bet_label",
        "add_another_bet_label",
        "confirm_bet_label",
        "remove_another_bet_label",
        "session_expired",
        "still_processing",
        "authenticated",
        "expired_button",
        "you_selected_prefix",
        "my_combos_label",
        "select_link_label",
        "select_tutorial_label",
        "no_tutorials_label",
        "combo_no_bets_added",
        "combo_partial_bets_warning",
        "post_bet_menu_text",
        "select_sport_fallback",
        "greeting_menu_fallback",
        "more_options_label",
        "account_locked_text",
        "invalid_otp_text",
    ]

    def test_each_new_field_accepts_message_item(self):
        """Each new field should accept a MessageItem value."""
        for field_name in self.NEW_FIELDS:
            labels = LabelMessages(**{field_name: MessageItem(text="test")})
            value = getattr(labels, field_name)
            assert value is not None
            assert value.text == "test"

    def test_each_new_field_accepts_none(self):
        """Each new field should accept None (default)."""
        labels = LabelMessages()
        for field_name in self.NEW_FIELDS:
            assert getattr(labels, field_name) is None

    def test_model_validate_coerces_plain_string_to_message_item(self):
        """model_validate should coerce a plain string to MessageItem.text."""
        for field_name in self.NEW_FIELDS:
            labels = LabelMessages.model_validate({field_name: "hello"})
            value = getattr(labels, field_name)
            assert isinstance(value, MessageItem)
            assert value.text == "hello"

    def test_extra_fields_raise_validation_error(self):
        """Extra fields not in the model should raise ValidationError."""
        with pytest.raises(ValidationError):
            LabelMessages(nonexistent_field=MessageItem(text="x"))

    def test_from_minimal_labels_is_not_none(self):
        """from_minimal() should return non-None labels (regression guard)."""
        templates = MessageTemplates.from_minimal()
        assert templates.labels is not None

    def test_from_minimal_session_expired_text(self):
        """from_minimal().labels.session_expired.text should match the English default."""
        templates = MessageTemplates.from_minimal()
        expected = (
            "Welcome back! \U0001f44b We've cleared your current betslip "
            "so you can start fresh. Your account and chat history are still saved."
        )
        assert templates.labels.session_expired.text == expected

    def test_from_minimal_all_new_fields_populated(self):
        """from_minimal() should populate every new label field."""
        templates = MessageTemplates.from_minimal()
        for field_name in self.NEW_FIELDS:
            value = getattr(templates.labels, field_name)
            assert value is not None, f"from_minimal() labels.{field_name} is None"
            assert isinstance(value, MessageItem)
            assert value.text, f"from_minimal() labels.{field_name}.text is empty"

    def test_from_minimal_specific_defaults(self):
        """Spot-check a few specific default values from from_minimal()."""
        labels = MessageTemplates.from_minimal().labels
        assert labels.back_option.text == "<< Back"
        assert labels.home_page_text.text == "Go to website \U0001f310"
        assert labels.profit_text.text == "Bet \U0001f911"
        assert labels.confirm_bet_label.text == "Confirm bet"
        assert labels.authenticated.text == "You're now authenticated \u2705"
        assert labels.my_combos_label.text == "My Combos"
        assert labels.no_tutorials_label.text == "No tutorials available at the moment."
        assert labels.edit_bet_label_text.text == "Edit bet"
        assert labels.combo_no_bets_added.text == "Could not add any bet from the combo."
        assert labels.combo_partial_bets_warning.text.startswith(
            "\u26a0\ufe0f"
        )
        assert labels.post_bet_menu_text.text == "What would you like to do?"
        assert labels.select_sport_fallback.text == "Select a sport"
        assert labels.greeting_menu_fallback.text == "Menu"
        assert labels.more_options_label.text == "More options"
        assert labels.account_locked_text.text == "Account locked"
        assert labels.invalid_otp_text.text == "Invalid OTP"
