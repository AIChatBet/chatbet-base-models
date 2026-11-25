"""Lottery companies: the company type, the lottery_config row and the lottery endpoints."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from chatbet_base_models import (
    APIEndpoints,
    APIEndpointsDB,
    CompanyType,
    Identity,
    LotteryConfig,
    LotteryConfigDB,
    LotteryEndpoints,
    LotteryRules,
    MockLotteryConfig,
    SiteConfig,
    SiteConfigDB,
)

MOCK_URL = "https://mock.example.com"


def _identity(**extra):
    return {"site_name": "Lotería demo", "company_id": "loteriademo", "site_url": "https://chatbet.gg", **extra}


class TestCompanyType:
    def test_a_stored_company_without_the_field_is_a_sportbook(self):
        # GIVEN an identity stored before company_type existed
        # WHEN it is validated
        identity = Identity(**_identity())
        # THEN it is a sportbook company
        assert identity.company_type is CompanyType.SPORTBOOK

    def test_a_lottery_company(self):
        identity = Identity(**_identity(company_type="lottery"))
        assert identity.company_type is CompanyType.LOTTERY

    def test_an_unknown_type_is_rejected(self):
        with pytest.raises(ValidationError):
            Identity(**_identity(company_type="casino"))

    def test_a_sportbook_company_is_saved_without_the_field(self):
        # GIVEN a sportbook company re-saved the way the back office does it
        stored = SiteConfigDB(identity=_identity(), PK="company#x", SK="site_config")
        # WHEN it is dumped and serialized for DynamoDB
        item = stored.to_dynamodb_item()
        # THEN no company_type is written, so services on an older base-models
        # (extra="forbid") still load the row
        assert "company_type" not in item["identity"]
        assert "company_type" not in stored.model_dump()["identity"]
        assert "company_type" not in stored.model_dump(mode="json")["identity"]

    def test_an_explicit_sportbook_is_not_written_either(self):
        identity = Identity(**_identity(company_type="sportbook"))
        assert "company_type" not in identity.model_dump()

    def test_a_lottery_company_keeps_its_type_through_a_save(self):
        # GIVEN a lottery company
        stored = SiteConfigDB(
            identity=_identity(company_type="lottery"), PK="company#x", SK="site_config"
        )
        # WHEN it is serialized and read back
        item = stored.to_dynamodb_item()
        reread = SiteConfig(**{k: v for k, v in item.items() if k not in ("PK", "SK", "created_at", "updated_at")})
        # THEN it is still a lottery company
        assert item["identity"]["company_type"] == "lottery"
        assert reread.identity.company_type is CompanyType.LOTTERY

    def test_the_json_schema_still_documents_the_field(self):
        schema = SiteConfig.model_json_schema()
        identity = schema["$defs"]["Identity"]["properties"]
        assert "company_type" in identity


class TestLotteryConfig:
    def test_minimal_mock(self):
        config = LotteryConfig.from_minimal_mock(api_url=MOCK_URL)
        assert config.provider == "mock"
        assert str(config.config.api_url).startswith(MOCK_URL)
        assert config.config.timeout_s == 5.0
        assert config.rules.max_quantity_per_purchase == 20
        assert config.rules.max_amount_per_purchase is None

    def test_db_row_keys(self):
        row = LotteryConfigDB.from_minimal_mock("loteriademo", api_url=MOCK_URL)
        assert row.PK == "company#loteriademo"
        assert row.SK == "lottery_config"

    def test_db_row_requires_keys(self):
        with pytest.raises(ValidationError):
            LotteryConfigDB(config={"api_url": MOCK_URL})

    def test_round_trip_through_dynamodb(self):
        # GIVEN a row with a money limit
        row = LotteryConfigDB.from_minimal_mock(
            "loteriademo",
            api_url=MOCK_URL,
            rules=LotteryRules(max_quantity_per_purchase=5, max_amount_per_purchase=Decimal("50.5")),
        )
        # WHEN it is serialized for DynamoDB and validated again
        item = row.to_dynamodb_item()
        reread = LotteryConfigDB(**item)
        # THEN nothing is lost, and no float reaches DynamoDB
        assert item["config"] == {"provider": "mock", "api_url": f"{MOCK_URL}/", "timeout_s": Decimal("5.0")}
        assert item["rules"] == {"max_quantity_per_purchase": 5, "max_amount_per_purchase": Decimal("50.5")}
        assert reread.rules == row.rules
        assert reread.config == row.config

    def test_unknown_fields_are_rejected(self):
        with pytest.raises(ValidationError):
            LotteryConfig(config={"api_url": MOCK_URL}, sports=[])
        with pytest.raises(ValidationError):
            MockLotteryConfig(api_url=MOCK_URL, token="x")

    def test_unknown_provider_is_rejected(self):
        with pytest.raises(ValidationError):
            LotteryConfig(config={"provider": "igt", "api_url": MOCK_URL})

    @pytest.mark.parametrize(
        "rules",
        [
            {"max_quantity_per_purchase": 0},
            {"max_amount_per_purchase": 0},
            {"max_amount_per_purchase": -1},
        ],
    )
    def test_limits_must_be_positive(self, rules):
        with pytest.raises(ValidationError):
            LotteryRules(**rules)

    @pytest.mark.parametrize("timeout", [0, -1, 61])
    def test_timeout_bounds(self, timeout):
        with pytest.raises(ValidationError):
            MockLotteryConfig(api_url=MOCK_URL, timeout_s=timeout)


class TestLotteryEndpoints:
    def test_a_lottery_company_has_auth_users_and_lottery_only(self):
        # GIVEN the platform_endpoints of a lottery company: no sportbook groups
        endpoints = APIEndpoints(
            auth={"validate_user": {"endpoint": f"{MOCK_URL}/auth/validate_user", "method": "GET"}},
            users={"get_user_balance": {"endpoint": f"{MOCK_URL}/auth/get_user_balance", "method": "GET"}},
            lottery={
                "get_draws": {
                    "endpoint": f"{MOCK_URL}/lottery/draws",
                    "method": "GET",
                    "params": {"lotteryId": ""},
                },
                "purchase": {"endpoint": f"{MOCK_URL}/lottery/purchase", "method": "POST"},
            },
        )
        # THEN it validates, with the sportbook groups absent
        assert endpoints.sports is None and endpoints.fixtures is None and endpoints.bets is None
        assert endpoints.lottery.get_draws.params == {"lotteryId": ""}
        assert endpoints.lottery.check_number is None

    def test_unknown_lottery_endpoint_is_rejected(self):
        with pytest.raises(ValidationError):
            LotteryEndpoints(buy_scratch_card={"endpoint": MOCK_URL})

    def test_sportbook_defaults_have_no_lottery_group(self):
        assert APIEndpointsDB.default_factory("x").lottery is None
