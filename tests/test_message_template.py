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


class TestLinkItem:
    """Test individual link item model"""

    def test_create_link_item(self):
        """Test creating a link item with all fields"""
        link = LinkItem(
            title="Help Center",
            message_text="Visit our help center for assistance",
            button_label="Get Help",
            button_url="https://example.com/help"
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
            button_url="https://example.com/support"
        )
        assert link.title == "Support"

    def test_title_validation_empty_raises_error(self):
        """Test that empty title raises validation error"""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            LinkItem(
                title="   ",
                message_text="Text",
                button_label="Label",
                button_url="https://example.com"
            )

    def test_message_text_validation_empty_raises_error(self):
        """Test that empty message_text raises error"""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            LinkItem(
                title="Title",
                message_text="   ",
                button_label="Label",
                button_url="https://example.com"
            )

    def test_button_label_validation_empty_raises_error(self):
        """Test that empty button_label raises error"""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="   ",
                button_url="https://example.com"
            )

    def test_button_url_validation_requires_protocol(self):
        """Test that button_url must start with http:// or https://"""
        with pytest.raises(ValueError, match="must start with http"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="example.com"
            )

    def test_button_url_validation_accepts_https(self):
        """Test that https:// URLs are valid"""
        link = LinkItem(
            title="Title",
            message_text="Text",
            button_label="Label",
            button_url="https://example.com"
        )
        assert link.button_url == "https://example.com"

    def test_button_url_validation_accepts_http(self):
        """Test that http:// URLs are valid"""
        link = LinkItem(
            title="Title",
            message_text="Text",
            button_label="Label",
            button_url="http://example.com"
        )
        assert link.button_url == "http://example.com"

    def test_button_url_validation_empty_raises_error(self):
        """Test that empty button_url raises error"""
        with pytest.raises(ValueError, match="button_url cannot be empty"):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="   "
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected"""
        with pytest.raises(ValueError):
            LinkItem(
                title="Title",
                message_text="Text",
                button_label="Label",
                button_url="https://example.com",
                extra_field="not allowed"
            )


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
            button_url="https://example.com/help"
        )

        links = LinksMessages(links=required_links + [custom_link])
        assert len(links.links) == 7  # 6 required + 1 custom
        assert any(link.title == "Help" for link in links.links)
        assert any(link.title == "Support" for link in links.links)  # From required defaults

    def test_duplicate_titles_validation_raises_error(self):
        """Test that duplicate titles raise validation error"""
        link1 = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help"
        )
        link2 = LinkItem(
            title="Help",
            message_text="Different message",
            button_label="Different Label",
            button_url="https://example.com/help2"
        )

        with pytest.raises(ValueError, match="Duplicate link titles"):
            LinksMessages(links=[link1, link2])

    def test_duplicate_titles_case_insensitive(self):
        """Test that duplicate title checking is case-insensitive"""
        link1 = LinkItem(
            title="Help",
            message_text="Get help",
            button_label="Help Center",
            button_url="https://example.com/help"
        )
        link2 = LinkItem(
            title="HELP",
            message_text="Different message",
            button_label="Different Label",
            button_url="https://example.com/help2"
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
                button_url=f"https://example.com/{i}"
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
                button_url=f"https://example.com/{i}"
            )
            for i in range(94)
        ]

        links = LinksMessages(links=required_links + custom_links)
        assert len(links.links) == 100

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected"""
        with pytest.raises(ValueError):
            LinksMessages(
                links=[],
                extra_field="not allowed"
            )


class TestLinksMessagesDefaultLinks:
    """Test default links functionality and validation"""

    def test_default_links_present_on_initialization(self):
        """Test that 6 default links are present when LinksMessages is created"""
        links = LinksMessages()
        assert len(links.links) == 6

        # Check all required titles are present
        titles = {link.title.lower() for link in links.links}
        assert titles == {"support", "main site", "sign up", "withdrawal", "deposit", "bet results"}

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
            button_url="https://example.com/support"
        )
        link2 = LinkItem(
            title="Main site",
            message_text="Visit site",
            button_label="Go to Site",
            button_url="https://example.com"
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
            button_url="https://example.com/support"
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
            {"title": "SUPPORT", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/support"},
            {"title": "Main Site", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com"},
            {"title": "sign up", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/signup"},
            {"title": "WithDrawal", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/withdrawal"},
            {"title": "deposit", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/deposit"},
            {"title": "BET RESULTS", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/results"}
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
                button_url="https://custom.com/support"
            ),
            LinkItem(
                title="Main site",
                message_text="Custom site message",
                button_label="Custom Site Button",
                button_url="https://custom.com"
            ),
            LinkItem(
                title="Sign up",
                message_text="Custom signup message",
                button_label="Custom Signup Button",
                button_url="https://custom.com/signup"
            ),
            LinkItem(
                title="Withdrawal",
                message_text="Custom withdrawal message",
                button_label="Custom Withdrawal Button",
                button_url="https://custom.com/withdrawal"
            ),
            LinkItem(
                title="Deposit",
                message_text="Custom deposit message",
                button_label="Custom Deposit Button",
                button_url="https://custom.com/deposit"
            ),
            LinkItem(
                title="Bet results",
                message_text="Custom results message",
                button_label="Custom Results Button",
                button_url="https://custom.com/results"
            )
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
            button_url="https://example.com/faq"
        )

        all_links = links.links + [additional_link]
        links_with_extra = LinksMessages(links=all_links)

        assert len(links_with_extra.links) == 7
        assert any(link.title == "FAQ" for link in links_with_extra.links)

    def test_validation_allows_required_plus_additional_links(self):
        """Test that validation passes with required + additional links"""
        # Create required links + 3 additional
        links_data = [
            {"title": "Support", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/support"},
            {"title": "Main site", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com"},
            {"title": "Sign up", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/signup"},
            {"title": "Withdrawal", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/withdrawal"},
            {"title": "Deposit", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/deposit"},
            {"title": "Bet results", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/results"},
            {"title": "FAQ", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/faq"},
            {"title": "Terms", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/terms"},
            {"title": "Privacy", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/privacy"}
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]
        links = LinksMessages(links=links_items)

        assert len(links.links) == 9

    def test_duplicate_title_validation_still_works(self):
        """Test that duplicate title validation works with default links"""
        # Try to create links with duplicate in additional links
        links_data = [
            {"title": "Support", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/support"},
            {"title": "Main site", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com"},
            {"title": "Sign up", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/signup"},
            {"title": "Withdrawal", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/withdrawal"},
            {"title": "Deposit", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/deposit"},
            {"title": "Bet results", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/results"},
            {"title": "Support", "message_text": "Different text", "button_label": "Different", "button_url": "https://example.com/support2"}
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
                button_url=f"https://example.com/extra{i}"
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
            {"title": "Support", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/support"},
            {"title": "Main site", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com"},
            {"title": "Sign up", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/signup"},
            {"title": "Withdrawal", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/withdrawal"},
            {"title": "Deposit", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/deposit"},
            {"title": "Results Page", "message_text": "Text", "button_label": "Label", "button_url": "https://example.com/results"}  # Changed from "Bet results"
        ]

        links_items = [LinkItem(**link_data) for link_data in links_data]

        with pytest.raises(ValueError, match="Missing required link titles"):
            LinksMessages(links=links_items)


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
            button_url="https://example.com/help"
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
            button_url="https://example.com/help"
        )

        templates_db = MessageTemplatesDB(
            PK="company#123",
            SK="message_templates",
            links=LinksMessages(links=required_links + [custom_link])
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
        original_time = templates.updated_at
        templates.touch()
        assert templates.updated_at > original_time

    def test_links_field_has_default(self):
        """Test that links field defaults to 6 required links"""
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
            button_url="https://example.com/help"
        )
        link2 = LinkItem(
            title="FAQ",
            message_text="Frequently asked questions",
            button_label="View FAQ",
            button_url="https://example.com/faq"
        )

        templates = MessageTemplates(
            links=LinksMessages(links=required_links + [link1, link2])
        )

        assert len(templates.links.links) == 8  # 6 required + 2 custom
        assert any(link.title == "Help" for link in templates.links.links)
        assert any(link.title == "Support" for link in templates.links.links)  # From required defaults
        assert any(link.title == "FAQ" for link in templates.links.links)
