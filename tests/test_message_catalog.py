"""Tests for the catalog types and the legacy -> new-shape conversion."""

import pytest
from pydantic import ValidationError

from chatbet_base_models.message_catalog import (
    MAX_BUTTONS_PER_MESSAGE,
    CatalogEntry,
    ClientMessages,
    LegacyConversion,
    MessageCatalog,
    MessageContent,
    legacy_to_client_messages,
)
from chatbet_base_models.message_render import render
from chatbet_base_models.message_template import (
    AdditionalMessageMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageItem,
    MessageTemplates,
)


def _buttons(prefix: str, count: int):
    return [
        InlineKeyboardButton(text=f"{prefix}{i}", callback_data=f"{prefix}{i}")
        for i in range(count)
    ]


def _markup(*rows):
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def _flat_texts(content: MessageContent):
    return [b.text for row in content.reply_markup.inline_keyboard for b in row]


class TestCatalogEntry:
    def test_defaults(self):
        entry = CatalogEntry()
        assert entry.allowed_placeholders == []
        assert entry.legacy_tokens == {}

    def test_accepts_placeholders_and_legacy_tokens(self):
        entry = CatalogEntry(
            allowed_placeholders=["amount", "BALANCE"],
            legacy_tokens={"%1": "amount", "%": "BALANCE", "{{BET_REMOVED}}": "amount"},
        )
        assert entry.legacy_tokens["%1"] == "amount"

    @pytest.mark.parametrize("name", ["", "has space", "a-b", "{a}"])
    def test_rejects_invalid_placeholder_names(self, name):
        with pytest.raises(ValidationError):
            CatalogEntry(allowed_placeholders=[name])

    def test_rejects_duplicate_placeholders(self):
        with pytest.raises(ValidationError):
            CatalogEntry(allowed_placeholders=["a", "a"])

    @pytest.mark.parametrize("literal", ["%a", "1", "{{x y}}", "{x}", "%%"])
    def test_rejects_invalid_legacy_literals(self, literal):
        with pytest.raises(ValidationError):
            CatalogEntry(allowed_placeholders=["a"], legacy_tokens={literal: "a"})

    def test_rejects_legacy_token_mapped_to_a_disallowed_placeholder(self):
        with pytest.raises(ValidationError):
            CatalogEntry(allowed_placeholders=["a"], legacy_tokens={"%1": "b"})

    def test_rejects_unknown_fields(self):
        with pytest.raises(ValidationError):
            CatalogEntry(unexpected=True)

    def test_additional_message_flag_no_longer_exists(self):
        with pytest.raises(ValidationError):
            CatalogEntry(supports_additional_message=True)

    def test_entry_legacy_tokens_plug_into_render(self):
        entry = CatalogEntry(
            allowed_placeholders=["amount"], legacy_tokens={"%1": "amount"}
        )
        text = render(
            "Bet %1 placed",
            {"amount": "10"},
            channel="telegram",
            company="acme",
            key="bets.placed_bet",
            legacy_tokens=entry.legacy_tokens,
        )
        assert text == "Bet 10 placed"


class TestMessageCatalog:
    def _catalog(self, **overrides):
        data = {"version": 1, "message_keys": {"bets.placed_bet": CatalogEntry()}}
        data.update(overrides)
        return MessageCatalog(**data)

    def test_valid_catalog_round_trips_through_json(self):
        catalog = self._catalog(created_by="juan")
        assert MessageCatalog.model_validate(catalog.model_dump(mode="json")) == catalog

    @pytest.mark.parametrize("version", [0, -1])
    def test_rejects_non_positive_version(self, version):
        with pytest.raises(ValidationError):
            self._catalog(version=version)

    @pytest.mark.parametrize(
        "key", ["nodot", "Bets.Upper", "bets.", ".field", "a.b.c", "bets.with space"]
    )
    def test_rejects_malformed_keys(self, key):
        with pytest.raises(ValidationError):
            self._catalog(message_keys={key: CatalogEntry()})


class TestMessageContent:
    def test_text_only_is_valid(self):
        assert MessageContent(text="hi").reply_markup is None

    def test_exactly_the_maximum_number_of_buttons_is_valid(self):
        content = MessageContent(
            text="pick", reply_markup=_markup(_buttons("a", MAX_BUTTONS_PER_MESSAGE))
        )
        assert len(content.reply_markup.inline_keyboard[0]) == MAX_BUTTONS_PER_MESSAGE

    def test_one_button_over_the_maximum_is_rejected(self):
        with pytest.raises(ValidationError):
            MessageContent(
                text="pick",
                reply_markup=_markup(_buttons("a", MAX_BUTTONS_PER_MESSAGE + 1)),
            )

    def test_buttons_are_counted_across_rows(self):
        rows = [_buttons("a", 4), _buttons("b", 4), _buttons("c", 3)]
        with pytest.raises(ValidationError):
            MessageContent(text="pick", reply_markup=_markup(*rows))

    def test_additional_message_is_not_part_of_the_content(self):
        with pytest.raises(ValidationError):
            MessageContent(text="x", additional_message={"text": "y"})


class TestClientMessages:
    def test_valid_content(self):
        content = ClientMessages(
            catalog_version=1, messages={"bets.placed_bet": MessageContent(text="ok")}
        )
        assert content.messages["bets.placed_bet"].text == "ok"

    def test_rejects_catalog_version_zero(self):
        with pytest.raises(ValidationError):
            ClientMessages(catalog_version=0)

    def test_rejects_malformed_message_keys(self):
        with pytest.raises(ValidationError):
            ClientMessages(
                catalog_version=1, messages={"nodot": MessageContent(text="x")}
            )

    @pytest.mark.parametrize("field", ["general_errors", "account_state_defaults"])
    def test_dead_or_constant_fields_are_not_part_of_client_content(self, field):
        with pytest.raises(ValidationError):
            ClientMessages(catalog_version=1, **{field: {}})

    def test_rejects_additional_message_inside_a_message(self):
        with pytest.raises(ValidationError):
            ClientMessages(
                catalog_version=1,
                messages={
                    "bets.placed_bet": {
                        "text": "x",
                        "additional_message": {"text": "y"},
                    }
                },
            )


class TestLegacyToClientMessages:
    @pytest.fixture
    def templates(self):
        return MessageTemplates.from_minimal()

    def test_returns_content_and_warnings(self, templates):
        result = legacy_to_client_messages(templates, catalog_version=1)
        assert isinstance(result, LegacyConversion)
        assert result.content.catalog_version == 1

    def test_every_message_item_becomes_a_dotted_key(self, templates):
        messages = legacy_to_client_messages(templates, 1).content.messages
        assert "bets.placed_bet" in messages
        assert "menu.main_menu" in messages
        assert all(isinstance(item, MessageContent) for item in messages.values())

    def test_text_is_carried_over_unchanged(self, templates):
        messages = legacy_to_client_messages(templates, 1).content.messages
        assert messages["bets.placed_bet"].text == templates.bets.placed_bet.text
        assert "%2" in messages["bets.placed_bet"].text

    def test_empty_fields_are_omitted(self, templates):
        messages = legacy_to_client_messages(templates, 1).content.messages
        none_fields = [
            f"{section}.{field}"
            for section in (
                "onboarding",
                "validation",
                "registration",
                "menu",
                "bets",
                "combos",
                "errors",
                "confirmation",
                "labels",
                "end",
                "guidance",
            )
            for field in type(getattr(templates, section)).model_fields
            if getattr(getattr(templates, section), field) is None
        ]
        assert none_fields, "fixture should contain at least one empty field"
        assert not set(none_fields) & set(messages)

    def test_links_are_preserved(self, templates):
        content = legacy_to_client_messages(templates, 3).content
        assert content.links == templates.links

    def test_missing_sections_do_not_break_the_conversion(self):
        content = legacy_to_client_messages(MessageTemplates(), 1).content
        assert content.messages == {}
        assert content.links is not None

    def test_result_round_trips_through_json(self, templates):
        content = legacy_to_client_messages(templates, 1).content
        assert ClientMessages.model_validate(content.model_dump(mode="json")) == content


class TestAdditionalMessageFolding:
    @pytest.fixture
    def templates(self):
        return MessageTemplates.from_minimal()

    def _convert(self, templates, item):
        templates.bets.placed_bet = item
        result = legacy_to_client_messages(templates, 1)
        return result.content.messages["bets.placed_bet"], result.warnings

    def test_additional_message_buttons_move_to_the_main_keyboard(self, templates):
        item = MessageItem(
            text="Pick one",
            reply_markup=_markup(_buttons("a", 2)),
            additional_message=AdditionalMessageMarkup(
                reply_markup=_markup(_buttons("b", 2))
            ),
        )
        content, warnings = self._convert(templates, item)
        assert _flat_texts(content) == ["a0", "a1", "b0", "b1"]
        assert content.text == "Pick one"
        assert [w for w in warnings if "bets.placed_bet" in w] == []

    def test_a_message_without_buttons_can_receive_the_extra_ones(self, templates):
        item = MessageItem(
            text="Pick one",
            additional_message=AdditionalMessageMarkup(
                reply_markup=_markup(_buttons("b", 2))
            ),
        )
        content, _ = self._convert(templates, item)
        assert _flat_texts(content) == ["b0", "b1"]

    def test_additional_text_is_reported_not_dropped_silently(self, templates):
        item = MessageItem(
            text="Pick one",
            additional_message=AdditionalMessageMarkup(text="More options below"),
        )
        content, warnings = self._convert(templates, item)
        assert content.text == "Pick one"
        assert any(
            "bets.placed_bet" in w and "More options below" in w for w in warnings
        )

    def test_blank_additional_text_raises_no_warning(self, templates):
        item = MessageItem(
            text="Pick one",
            additional_message=AdditionalMessageMarkup(
                text="   ", reply_markup=_markup(_buttons("b", 1))
            ),
        )
        _, warnings = self._convert(templates, item)
        assert [w for w in warnings if "bets.placed_bet" in w] == []

    def test_more_than_the_limit_is_capped_and_reported(self, templates):
        item = MessageItem(
            text="Pick one",
            reply_markup=_markup(_buttons("a", 8)),
            additional_message=AdditionalMessageMarkup(
                reply_markup=_markup(_buttons("b", 5))
            ),
        )
        content, warnings = self._convert(templates, item)
        texts = _flat_texts(content)
        assert len(texts) == MAX_BUTTONS_PER_MESSAGE
        assert texts[:8] == [f"a{i}" for i in range(8)]
        assert texts[8:] == ["b0", "b1"]
        assert any("bets.placed_bet" in w and "13 buttons" in w for w in warnings)

    def test_rows_that_fill_the_limit_exactly_drop_whole_extra_rows(self, templates):
        item = MessageItem(
            text="Pick",
            reply_markup=_markup(_buttons("a", 5), _buttons("b", 5), _buttons("c", 2)),
        )
        content, warnings = self._convert(templates, item)
        assert len(content.reply_markup.inline_keyboard) == 2
        assert len(_flat_texts(content)) == MAX_BUTTONS_PER_MESSAGE
        assert any("12 buttons" in w for w in warnings)

    def test_legacy_keyboard_over_the_limit_without_extra_is_capped_too(
        self, templates
    ):
        item = MessageItem(text="Pick", reply_markup=_markup(_buttons("a", 12)))
        content, warnings = self._convert(templates, item)
        assert len(_flat_texts(content)) == MAX_BUTTONS_PER_MESSAGE
        assert any("12 buttons" in w for w in warnings)
