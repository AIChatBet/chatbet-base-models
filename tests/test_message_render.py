"""Tests for the single message render engine."""

import logging

import pytest

from chatbet_base_models.message_render import CHANNEL_ESCAPERS, render

LOGGER_NAME = "chatbet_base_models.message_render"


def _render(text, values=None, **overrides):
    kwargs = {"channel": "telegram", "company": "acme", "key": "bets.placed_bet"}
    kwargs.update(overrides)
    return render(text, values, **kwargs)


class TestPlaceholders:
    def test_replaces_known_tokens(self):
        assert _render(
            "Hi {name}, balance {BALANCE}", {"name": "Ana", "BALANCE": "10"}
        ) == ("Hi Ana, balance 10")

    def test_zero_and_empty_string_are_valid_values(self):
        assert _render("[{a}][{b}]", {"a": 0, "b": ""}) == "[0][]"

    def test_non_string_values_are_stringified(self):
        assert _render("{a}", {"a": 2.5}) == "2.5"

    @pytest.mark.parametrize("text", [None, ""])
    def test_empty_text_renders_empty_string(self, text):
        assert _render(text, {"a": 1}) == ""

    def test_missing_values_mapping_is_treated_as_empty(self):
        assert _render("{a}", None) == "{a}"

    def test_unicode_and_emoji_are_preserved(self):
        assert _render("¡Hola {name}! ⚽", {"name": "José"}) == "¡Hola José! ⚽"

    def test_escaped_braces_render_like_str_format(self):
        assert _render("{{literal}} {a}", {"a": "x"}) == "{literal} x"

    @pytest.mark.parametrize("text", ["a { b } c", "{", "}", "{}", "{a b}"])
    def test_malformed_braces_pass_through_unchanged(self, text):
        assert _render(text, {"a": "x"}) == text


class TestUnresolvedTokens:
    def test_unresolved_token_stays_raw_and_is_logged(self, caplog):
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            result = _render("Hi {missing} and {name}", {"name": "Ana"})
        assert result == "Hi {missing} and Ana"
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert (record.msg_company, record.msg_key) == ("acme", "bets.placed_bet")
        assert (record.msg_token, record.msg_channel) == ("{missing}", "telegram")

    def test_none_value_counts_as_unresolved(self, caplog):
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            assert _render("{a}", {"a": None}) == "{a}"
        assert len(caplog.records) == 1

    def test_one_log_record_per_unresolved_occurrence(self, caplog):
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            _render("{x} {y} {x}", {})
        assert [r.msg_token for r in caplog.records] == ["{x}", "{y}", "{x}"]

    def test_resolved_text_logs_nothing(self, caplog):
        with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
            _render("{a}", {"a": "1"})
        assert caplog.records == []


class TestSinglePass:
    def test_values_are_not_rescanned(self):
        assert _render("{a} {b}", {"a": "{b}", "b": "x"}) == "{b} x"

    def test_value_containing_a_legacy_literal_is_not_rescanned(self):
        result = _render(
            "%1 %2", {"a": "%2", "b": "B"}, legacy_tokens={"%1": "a", "%2": "b"}
        )
        assert result == "%2 B"


class TestLegacyTokens:
    def test_positional_literals_are_replaced(self):
        result = _render(
            "Bet %1 on %2",
            {"id": "T1", "match": "A vs B"},
            legacy_tokens={"%1": "id", "%2": "match"},
        )
        assert result == "Bet T1 on A vs B"

    def test_longest_literal_wins_over_bare_percent(self):
        result = _render(
            "%1 and %", {"a": "A", "b": "B"}, legacy_tokens={"%": "b", "%1": "a"}
        )
        assert result == "A and B"

    def test_double_brace_literal_is_replaced_when_declared(self):
        result = _render(
            "Removed {{BET_REMOVED}}",
            {"bet_removed": "Over 2.5"},
            legacy_tokens={"{{BET_REMOVED}}": "bet_removed"},
        )
        assert result == "Removed Over 2.5"

    def test_double_brace_literal_without_declaration_is_an_escape(self, caplog):
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            assert _render("Removed {{BET_REMOVED}}", {}) == "Removed {BET_REMOVED}"
        assert caplog.records == []

    def test_unresolved_legacy_literal_stays_raw_and_is_logged(self, caplog):
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            assert _render("Bet %1", {}, legacy_tokens={"%1": "id"}) == "Bet %1"
        assert caplog.records[0].msg_token == "%1"

    def test_percent_is_untouched_when_not_declared(self):
        assert _render("100% sure %1", {"a": "x"}) == "100% sure %1"


class TestChannelEscaping:
    def test_escaper_applies_to_values_only(self, monkeypatch):
        monkeypatch.setitem(
            CHANNEL_ESCAPERS, "telegram", lambda v: v.replace("_", "\\_")
        )
        assert _render("a_b {x}", {"x": "c_d"}) == "a_b c\\_d"

    def test_default_escapers_change_nothing(self):
        for channel in ("telegram", "whatsapp", "web"):
            assert _render("{x}", {"x": "a_b*c"}, channel=channel) == "a_b*c"

    def test_unknown_channel_falls_back_to_identity(self):
        assert _render("{x}", {"x": "a_b"}, channel="sms") == "a_b"


class TestNeverRaises:
    def test_failing_escaper_returns_the_template_text_and_logs_error(
        self, monkeypatch, caplog
    ):
        def boom(value):
            raise RuntimeError("escaper failed")

        monkeypatch.setitem(CHANNEL_ESCAPERS, "telegram", boom)
        with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
            assert _render("Hi {x}", {"x": "y"}) == "Hi {x}"
        assert caplog.records[0].levelno == logging.ERROR
        assert caplog.records[0].msg_key == "bets.placed_bet"

    def test_unstringifiable_value_does_not_raise(self):
        class Bad:
            def __str__(self):
                raise ValueError("no")

        assert _render("Hi {x}", {"x": Bad()}) == "Hi {x}"
