"""A button can carry the destination it was generated from."""

import pytest
from pydantic import ValidationError

from chatbet_base_models.message_template import (
    ButtonDestination,
    InlineKeyboardButton,
)


class TestButtonDestination:
    def test_defaults_to_no_params(self):
        assert ButtonDestination(id="menu").params == {}

    def test_keeps_params(self):
        destination = ButtonDestination(id="link", params={"title": "Support"})
        assert destination.params == {"title": "Support"}

    @pytest.mark.parametrize("bad_id", ["Menu", "a.b", "a b", "", "menu\n"])
    def test_rejects_ids_that_are_not_lowercase_identifiers(self, bad_id):
        with pytest.raises(ValidationError):
            ButtonDestination(id=bad_id)

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            ButtonDestination(id="menu", extra="x")


class TestButtonCarriesDestination:
    def test_button_keeps_its_destination_next_to_the_generated_callback(self):
        button = InlineKeyboardButton(
            text="Help",
            callback_data="link:Support",
            destination={"id": "link", "params": {"title": "Support"}},
        )
        assert button.destination.id == "link"
        assert button.callback_data == "link:Support"

    def test_legacy_button_without_destination_is_unchanged(self):
        button = InlineKeyboardButton(text="Bet", callback_data="bet")
        assert button.destination is None
        assert button.model_dump(exclude_none=True) == {
            "text": "Bet",
            "callback_data": "bet",
        }
