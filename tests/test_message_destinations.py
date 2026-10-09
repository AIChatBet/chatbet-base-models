"""Destination catalog types and the callback generator."""

import pytest
from pydantic import ValidationError

from chatbet_base_models.message_catalog import CatalogEntry, MessageCatalog
from chatbet_base_models.message_destinations import (
    CALLBACK_DATA_MAX_LENGTH,
    DestinationCatalog,
    DestinationDef,
    ParamDef,
    RenderedAction,
    find_destination_problems,
    render_destination,
)
from chatbet_base_models.message_template import ButtonDestination


def _catalog() -> DestinationCatalog:
    return DestinationCatalog(
        version=1,
        destinations={
            "menu": DestinationDef(callback_template="menu"),
            "link": DestinationDef(
                callback_template="link:{title}",
                params=[ParamDef(name="title", kind="link")],
            ),
            "message": DestinationDef(
                callback_template="message:{key}",
                params=[ParamDef(name="key", kind="message_key")],
            ),
            "url": DestinationDef(
                url_template="{url}", params=[ParamDef(name="url", kind="text")]
            ),
            "offer": DestinationDef(
                callback_template="oi:S{sport}{tail}",
                params=[
                    ParamDef(name="sport", kind="sport"),
                    ParamDef(name="tail", kind="text", required=False),
                ],
            ),
        },
    )


def _messages() -> MessageCatalog:
    return MessageCatalog(version=1, message_keys={"menu.main_menu": CatalogEntry()})


class TestDestinationDef:
    def test_needs_exactly_one_template(self):
        with pytest.raises(ValidationError):
            DestinationDef()
        with pytest.raises(ValidationError):
            DestinationDef(callback_template="menu", url_template="{url}",
                           params=[ParamDef(name="url", kind="text")])

    def test_every_token_must_be_a_declared_param_and_every_param_used(self):
        with pytest.raises(ValidationError):
            DestinationDef(callback_template="link:{title}")
        with pytest.raises(ValidationError):
            DestinationDef(callback_template="menu",
                           params=[ParamDef(name="title", kind="text")])

    def test_rejects_literal_braces(self):
        with pytest.raises(ValidationError):
            DestinationDef(callback_template="a{{b}}")

    def test_rejects_duplicate_param_names(self):
        with pytest.raises(ValidationError):
            DestinationDef(
                callback_template="x:{a}",
                params=[ParamDef(name="a", kind="text"), ParamDef(name="a", kind="text")],
            )

    def test_param_kind_and_name_are_validated(self):
        with pytest.raises(ValidationError):
            ParamDef(name="a", kind="nonsense")
        with pytest.raises(ValidationError):
            ParamDef(name="a b", kind="text")


class TestDestinationCatalog:
    @pytest.mark.parametrize("bad_id", ["Menu", "a.b", "menu\n", ""])
    def test_rejects_ids_that_are_not_lowercase_identifiers(self, bad_id):
        with pytest.raises(ValidationError):
            DestinationCatalog(
                version=1, destinations={bad_id: DestinationDef(callback_template="x")}
            )

    def test_version_starts_at_one_and_extras_are_forbidden(self):
        with pytest.raises(ValidationError):
            DestinationCatalog(version=0, destinations={})
        with pytest.raises(ValidationError):
            DestinationCatalog(version=1, destinations={}, extra="x")


class TestRenderDestination:
    def test_destination_without_params(self):
        assert render_destination(_catalog(), ButtonDestination(id="menu")) == RenderedAction(
            callback_data="menu"
        )

    def test_destination_with_param(self):
        action = render_destination(
            _catalog(), ButtonDestination(id="link", params={"title": "support"})
        )
        assert action.callback_data == "link:support"
        assert action.url is None

    def test_url_destination_renders_a_url_and_no_callback(self):
        action = render_destination(
            _catalog(), ButtonDestination(id="url", params={"url": "https://x.io/a"})
        )
        assert action == RenderedAction(url="https://x.io/a")

    def test_optional_param_left_out_renders_empty(self):
        action = render_destination(
            _catalog(), ButtonDestination(id="offer", params={"sport": "1"})
        )
        assert action.callback_data == "oi:S1"

    def test_unknown_destination_raises(self):
        with pytest.raises(ValueError, match="unknown destination"):
            render_destination(_catalog(), ButtonDestination(id="refund"))

    def test_missing_required_param_raises(self):
        with pytest.raises(ValueError, match="missing required parameter 'title'"):
            render_destination(_catalog(), ButtonDestination(id="link"))

    def test_empty_required_param_raises(self):
        with pytest.raises(ValueError, match="missing required parameter"):
            render_destination(
                _catalog(), ButtonDestination(id="link", params={"title": ""})
            )

    def test_unexpected_param_raises(self):
        with pytest.raises(ValueError, match="unexpected parameters"):
            render_destination(
                _catalog(), ButtonDestination(id="menu", params={"x": "1"})
            )

    def test_value_containing_braces_is_inserted_as_plain_text(self):
        action = render_destination(
            _catalog(), ButtonDestination(id="link", params={"title": "{key}"})
        )
        assert action.callback_data == "link:{key}"

    def test_callback_limit_counts_utf8_bytes_not_characters(self):
        # 35 characters but 65 UTF-8 bytes: Telegram rejects it.
        with pytest.raises(ValueError, match="64"):
            render_destination(
                _catalog(), ButtonDestination(id="link", params={"title": "é" * 30})
            )

    def test_callback_of_exactly_64_bytes_is_accepted(self):
        action = render_destination(
            _catalog(), ButtonDestination(id="link", params={"title": "x" * 59})
        )
        assert len(action.callback_data.encode("utf-8")) == CALLBACK_DATA_MAX_LENGTH

    def test_callback_longer_than_the_limit_raises_instead_of_truncating(self):
        too_long = "x" * CALLBACK_DATA_MAX_LENGTH
        with pytest.raises(ValueError, match="64"):
            render_destination(
                _catalog(), ButtonDestination(id="link", params={"title": too_long})
            )


class TestFindDestinationProblems:
    def test_valid_destination_has_no_problems(self):
        destination = ButtonDestination(id="message", params={"key": "menu.main_menu"})
        assert find_destination_problems(destination, _catalog(), _messages()) == []

    def test_message_key_param_must_exist_in_the_catalog(self):
        destination = ButtonDestination(id="message", params={"key": "menu.missing"})
        problems = find_destination_problems(destination, _catalog(), _messages())
        assert problems == ["parameter 'key' points at unknown message key 'menu.missing'"]

    def test_render_errors_are_reported_as_problems(self):
        problems = find_destination_problems(
            ButtonDestination(id="refund"), _catalog(), _messages()
        )
        assert problems == ["unknown destination 'refund'"]
