"""Events, the per-client flow and their cross-validation."""

import pytest
from pydantic import ValidationError

from chatbet_base_models.message_catalog import CatalogEntry, MessageCatalog
from chatbet_base_models.message_flow import (
    ClientFlow,
    EventCatalog,
    EventDef,
    find_event_catalog_problems,
    find_flow_problems,
)


def _messages() -> MessageCatalog:
    return MessageCatalog(
        version=1,
        message_keys={
            "menu.main_menu": CatalogEntry(),
            "validation.bad_otp": CatalogEntry(),
        },
    )


def _events() -> EventCatalog:
    return EventCatalog(
        version=1,
        events={
            "otp_valid": EventDef(default_message_key="menu.main_menu"),
            "otp_invalid": EventDef(
                default_message_key="validation.bad_otp",
                allowed_placeholders=["attempts"],
            ),
        },
    )


class TestEventDef:
    def test_placeholders_default_to_none(self):
        assert EventDef(default_message_key="menu.main_menu").allowed_placeholders == []

    def test_rejects_invalid_or_duplicate_placeholders(self):
        with pytest.raises(ValidationError):
            EventDef(default_message_key="menu.main_menu", allowed_placeholders=["a b"])
        with pytest.raises(ValidationError):
            EventDef(default_message_key="menu.main_menu", allowed_placeholders=["a", "a"])

    @pytest.mark.parametrize("bad_key", ["main_menu", "Menu.x", "menu.x\n", ""])
    def test_default_message_key_must_look_like_a_message_key(self, bad_key):
        with pytest.raises(ValidationError):
            EventDef(default_message_key=bad_key)


class TestEventCatalog:
    @pytest.mark.parametrize("bad_id", ["OtpValid", "otp.valid", "otp_valid\n", ""])
    def test_rejects_ids_that_are_not_lowercase_identifiers(self, bad_id):
        with pytest.raises(ValidationError):
            EventCatalog(
                version=1,
                events={bad_id: EventDef(default_message_key="menu.main_menu")},
            )

    def test_version_starts_at_one_and_extras_are_forbidden(self):
        with pytest.raises(ValidationError):
            EventCatalog(version=0, events={})
        with pytest.raises(ValidationError):
            EventCatalog(version=1, events={}, extra="x")


class TestClientFlow:
    def test_routes_default_to_empty(self):
        assert ClientFlow(catalog_version=1).event_routes == {}

    def test_rejects_bad_event_ids_and_message_keys(self):
        with pytest.raises(ValidationError):
            ClientFlow(catalog_version=1, event_routes={"OtpValid": "menu.main_menu"})
        with pytest.raises(ValidationError):
            ClientFlow(catalog_version=1, event_routes={"otp_valid": "main_menu"})
        with pytest.raises(ValidationError):
            ClientFlow(catalog_version=1, event_routes={"otp_valid": "menu.main_menu\n"})

    def test_rejects_extra_fields_and_version_zero(self):
        with pytest.raises(ValidationError):
            ClientFlow(catalog_version=0)
        with pytest.raises(ValidationError):
            ClientFlow(catalog_version=1, extra="x")


class TestFindEventCatalogProblems:
    def test_consistent_catalog_has_no_problems(self):
        assert find_event_catalog_problems(_events(), _messages()) == []

    def test_default_message_key_must_exist_in_the_message_catalog(self):
        events = EventCatalog(
            version=1,
            events={"otp_valid": EventDef(default_message_key="menu.missing")},
        )
        assert find_event_catalog_problems(events, _messages()) == [
            "event 'otp_valid' defaults to unknown message key 'menu.missing'"
        ]


class TestFindFlowProblems:
    def test_valid_flow_has_no_problems(self):
        flow = ClientFlow(
            catalog_version=1, event_routes={"otp_invalid": "menu.main_menu"}
        )
        assert find_flow_problems(flow, _events(), _messages()) == []

    def test_route_for_an_event_the_catalog_does_not_define(self):
        flow = ClientFlow(
            catalog_version=1, event_routes={"otp_expired": "menu.main_menu"}
        )
        assert find_flow_problems(flow, _events(), _messages()) == [
            "route for unknown event 'otp_expired'"
        ]

    def test_route_to_a_message_key_the_catalog_does_not_define(self):
        flow = ClientFlow(
            catalog_version=1, event_routes={"otp_valid": "menu.missing"}
        )
        assert find_flow_problems(flow, _events(), _messages()) == [
            "event 'otp_valid' routes to unknown message key 'menu.missing'"
        ]

    def test_reports_every_problem_in_event_id_order(self):
        flow = ClientFlow(
            catalog_version=1,
            event_routes={"b_event": "menu.main_menu", "a_event": "menu.missing"},
        )
        assert find_flow_problems(flow, _events(), _messages()) == [
            "route for unknown event 'a_event'",
            "route for unknown event 'b_event'",
        ]
