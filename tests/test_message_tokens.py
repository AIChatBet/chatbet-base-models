"""Tests for the shared ``{TOKEN}`` scanner."""

import pytest

from chatbet_base_models.message_tokens import build_scan_pattern, extract_tokens


class TestExtractTokens:
    def test_extracts_plain_tokens(self):
        assert extract_tokens("Hi {name}, you have {BALANCE}") == {"name", "BALANCE"}

    def test_token_names_are_case_sensitive(self):
        assert extract_tokens("{balance} {BALANCE}") == {"balance", "BALANCE"}

    def test_repeated_token_counts_once(self):
        assert extract_tokens("{a} {a} {a}") == {"a"}

    @pytest.mark.parametrize("text", [None, ""])
    def test_empty_input_has_no_tokens(self, text):
        assert extract_tokens(text) == set()

    def test_escaped_braces_are_not_tokens(self):
        assert extract_tokens("{{BET_REMOVED}}") == set()

    def test_triple_braces_keep_the_inner_token(self):
        assert extract_tokens("{{{X}}}") == {"X"}

    @pytest.mark.parametrize("text", ["{", "}", "{}", "{ }", "{a b}", "{a-b}", "a } {"])
    def test_malformed_braces_are_not_tokens_and_do_not_raise(self, text):
        assert extract_tokens(text) == set()

    def test_percent_style_literals_are_not_tokens(self):
        assert extract_tokens("%1 and % and %8") == set()


class TestBuildScanPattern:
    def test_longest_legacy_literal_wins(self):
        pattern = build_scan_pattern(["%", "%1"])
        assert pattern.search("x %1").group("legacy") == "%1"

    def test_legacy_group_absent_without_literals(self):
        assert "legacy" not in build_scan_pattern().groupindex
