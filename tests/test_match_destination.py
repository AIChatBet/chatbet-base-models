"""Turning a callback back into the destination it came from."""

import pytest

from chatbet_base_models.message_destinations import (
    RAW_DESTINATION_ID,
    DestinationCatalog,
    DestinationDef,
    ParamDef,
    callback_candidates,
    match_destination,
    render_destination,
)
from chatbet_base_models.message_template import ButtonDestination


def _catalog(with_raw: bool = True) -> DestinationCatalog:
    destinations = {
        "menu": DestinationDef(callback_template="menu"),
        "link": DestinationDef(
            callback_template="link:{title}", params=[ParamDef(name="title", kind="link")]
        ),
        "message": DestinationDef(
            callback_template="message:{key}", params=[ParamDef(name="key", kind="message_key")]
        ),
        "offer": DestinationDef(
            callback_template="oi:{path}", params=[ParamDef(name="path", kind="text")]
        ),
        "combo_show": DestinationDef(callback_template="oi:COMBO.show"),
        "combo_place_amount": DestinationDef(
            callback_template="oi:COMBO.A{amount}", params=[ParamDef(name="amount", kind="text")]
        ),
        "more_tournaments": DestinationDef(
            callback_template="more_T_S{sport}_{page}",
            params=[ParamDef(name="sport", kind="sport"), ParamDef(name="page", kind="text")],
        ),
        "market_page": DestinationDef(
            callback_template="mp|{screen}|{direction}|{page}",
            params=[
                ParamDef(name="screen", kind="text"),
                ParamDef(name="direction", kind="text"),
                ParamDef(name="page", kind="text"),
            ],
        ),
        "url": DestinationDef(url_template="{url}", params=[ParamDef(name="url", kind="text")]),
    }
    if with_raw:
        destinations["raw"] = DestinationDef(
            callback_template="{callback_data}",
            params=[ParamDef(name="callback_data", kind="text")],
        )
    return DestinationCatalog(version=1, destinations=destinations)


@pytest.mark.parametrize(
    "callback, destination_id, params",
    [
        ("menu", "menu", {}),
        ("link:support", "link", {"title": "support"}),
        ("message:menu.main_menu", "message", {"key": "menu.main_menu"}),
        ("more_T_S1_2", "more_tournaments", {"sport": "1", "page": "2"}),
    ],
)
def test_a_known_callback_maps_to_its_destination(callback, destination_id, params):
    assert match_destination(callback, _catalog()) == ButtonDestination(
        id=destination_id, params=params
    )


def test_the_most_specific_template_wins():
    catalog = _catalog()
    assert match_destination("oi:COMBO.show", catalog).id == "combo_show"
    assert match_destination("oi:COMBO.A100", catalog) == ButtonDestination(
        id="combo_place_amount", params={"amount": "100"}
    )
    assert match_destination("oi:S1.T2", catalog) == ButtonDestination(
        id="offer", params={"path": "S1.T2"}
    )


def test_a_param_may_contain_colons_dots_and_pipes():
    catalog = _catalog()
    assert match_destination("link:a:b", catalog) == ButtonDestination(
        id="link", params={"title": "a:b"}
    )
    assert match_destination("mp|S1.T2|next|3", catalog) == ButtonDestination(
        id="market_page", params={"screen": "S1.T2", "direction": "next", "page": "3"}
    )


def test_what_fits_nothing_is_raw_so_no_button_is_lost():
    assert match_destination("something_else", _catalog()) == ButtonDestination(
        id=RAW_DESTINATION_ID, params={"callback_data": "something_else"}
    )


def test_without_a_raw_destination_nothing_is_returned_for_an_unknown_callback():
    assert match_destination("something_else", _catalog(with_raw=False)) is None


@pytest.mark.parametrize("empty", ["", None])
def test_an_empty_callback_matches_nothing(empty):
    assert match_destination(empty, _catalog()) is None


def test_a_template_that_cannot_compile_is_skipped_not_fatal():
    catalog = _catalog()
    catalog.destinations["broken"] = DestinationDef(
        callback_template="x:{a}:{a}", params=[ParamDef(name="a", kind="text")]
    )
    assert match_destination("menu", catalog).id == "menu"
    assert match_destination("x:1:1", catalog).id == RAW_DESTINATION_ID


def test_candidates_can_be_computed_once_and_reused():
    catalog = _catalog()
    candidates = callback_candidates(catalog)
    assert all(destination_id != RAW_DESTINATION_ID for destination_id, _ in candidates)
    assert match_destination("link:x", catalog, candidates) == match_destination("link:x", catalog)


@pytest.mark.parametrize(
    "destination",
    [
        ButtonDestination(id="menu"),
        ButtonDestination(id="link", params={"title": "Bet results"}),
        ButtonDestination(id="message", params={"key": "bets.placed_bet"}),
        ButtonDestination(id="combo_place_amount", params={"amount": "250"}),
        ButtonDestination(id="more_tournaments", params={"sport": "7", "page": "4"}),
    ],
)
def test_what_a_destination_renders_is_recognised_as_that_destination(destination):
    catalog = _catalog()
    callback = render_destination(catalog, destination).callback_data
    assert match_destination(callback, catalog) == destination
