from decimal import Decimal

import pytest
from pydantic import ValidationError

from chatbet_base_models.site_config_model import (
    MoneyLimits,
    RecommendationStyleConfig,
    SiteConfig,
    SiteConfigDB,
)

# The contract llm-pro reads, as published in CU-17tmdg7mhxc.
CONTRACT = {
    "priority_combo": ["balanced", "high_value", "safe"],
    "priority_single": ["high_value", "balanced", "safe"],
    "styles": {
        "safe": {
            "enabled": True,
            "single": {"odds_min": 1.15, "odds_max": 1.45, "options_min": 2, "options_max": 3, "markets": {}},
            "combo": {
                "leg_odds_min": 1.15,
                "leg_odds_max": 1.40,
                "total_odds_min": 1.5,
                "total_odds_max": 3.0,
                "legs_min": 2,
                "legs_max": 3,
                "markets": {},
            },
        },
        "balanced": {
            "enabled": True,
            "single": {"odds_min": 1.45, "odds_max": 2.00, "options_min": 3, "options_max": 3, "markets": {}},
            "combo": {
                "leg_odds_min": 1.40,
                "leg_odds_max": 1.80,
                "total_odds_min": 3.0,
                "total_odds_max": 8.0,
                "legs_min": 2,
                "legs_max": 4,
                "markets": {},
            },
        },
        "high_value": {
            "enabled": False,
            "single": {"odds_min": 2.00, "odds_max": 4.50, "options_min": 3, "options_max": 4, "markets": {}},
            "combo": {
                "leg_odds_min": 1.80,
                "leg_odds_max": 3.50,
                "total_odds_min": 5.0,
                "total_odds_max": 30.0,
                "legs_min": 3,
                "legs_max": 5,
                "markets": {"1": ["over_under", "btts"]},
            },
        },
    },
}


class TestRecommendationStyleConfig:
    def test_reads_the_contract_of_the_agent(self):
        style = RecommendationStyleConfig(**CONTRACT)

        assert style.priority_combo == ["balanced", "high_value", "safe"]
        assert style.priority_single[0] == "high_value"
        assert style.styles.safe.combo.leg_odds_max == Decimal("1.4")
        assert style.styles.balanced.single.options_max == 3
        assert style.styles.high_value.enabled is False
        assert style.styles.high_value.combo.markets == {"1": ["over_under", "btts"]}

    def test_an_empty_block_means_the_defaults_of_the_agent(self):
        style = RecommendationStyleConfig()

        assert style.priority_combo == []
        assert style.styles.safe.enabled is True
        assert style.styles.safe.combo.leg_odds_min is None
        assert style.styles.safe.single.markets == {}

    def test_rejects_a_style_that_does_not_exist(self):
        with pytest.raises(ValidationError):
            RecommendationStyleConfig(priority_combo=["risky"])

    def test_rejects_an_unknown_field(self):
        with pytest.raises(ValidationError):
            RecommendationStyleConfig(default_style="safe")

    def test_keeps_a_minimum_above_its_maximum(self):
        # The agent falls back to its default for that range; rejecting it here
        # would stop every service from loading the company.
        style = RecommendationStyleConfig(
            styles={"safe": {"combo": {"leg_odds_min": 3, "leg_odds_max": 1.2}}}
        )

        assert style.styles.safe.combo.leg_odds_min == Decimal("3")


class TestSiteConfigRecommendationStyle:
    def test_a_config_without_styles_is_stored_without_the_key(self):
        item = SiteConfigDB.default_factory("Test Site", "test123").to_dynamodb_item()

        assert "recommendation_style" not in item

    def test_the_styles_of_the_operator_are_stored(self):
        config = SiteConfigDB.default_factory("Test Site", "test123")
        config.recommendation_style = RecommendationStyleConfig(**CONTRACT)

        item = config.to_dynamodb_item()

        assert item["recommendation_style"]["priority_combo"] == ["balanced", "high_value", "safe"]
        assert item["recommendation_style"]["styles"]["safe"]["combo"]["legs_max"] == 3

    def test_a_stored_config_with_styles_loads_back(self):
        base = SiteConfig.default_factory("Test Site", "test123").model_dump()

        config = SiteConfig(**{**base, "recommendation_style": CONTRACT})

        assert config.recommendation_style.styles.balanced.combo.total_odds_max == Decimal("8")


class TestRecommendationLimits:
    def test_unset_limits_are_stored_without_their_keys(self):
        data = MoneyLimits(min_bet_amount=1, max_bet_amount=100).model_dump()

        assert "min_recommended_leg_odds" not in data
        assert "min_recommended_total_odds" not in data
        assert "combo_default_legs" not in data
        assert "max_win_multiplier" in data

    def test_limits_of_the_operator_are_stored(self):
        limits = MoneyLimits(
            min_bet_amount=1,
            max_bet_amount=100,
            min_recommended_leg_odds="1.2",
            min_recommended_total_odds=2,
            combo_default_legs=5,
        )

        data = limits.model_dump()

        assert data["min_recommended_leg_odds"] == Decimal("1.2")
        assert data["min_recommended_total_odds"] == Decimal("2")
        assert data["combo_default_legs"] == 5

    def test_a_combo_needs_at_least_one_match(self):
        with pytest.raises(ValidationError):
            MoneyLimits(min_bet_amount=1, max_bet_amount=100, combo_default_legs=0)
