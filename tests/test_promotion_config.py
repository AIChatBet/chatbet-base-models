import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID

from chatbet_base_models.promotion_config import (
    PromotionButton,
    PromotionItem,
    PromotionsConfig,
    PromotionsConfigDB,
)
from chatbet_base_models.message_template import InlineKeyboardButton


class TestPromotionItem:
    """Test individual promotion item model"""

    def test_create_promotion_item(self):
        """Test creating a promotion item"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Summer Sale",
            start_date=now,
            end_date=now + timedelta(days=30),
            details="Get 50% off",
            keywords=["summer", "sale"],
        )
        assert item.title == "Summer Sale"
        assert len(item.keywords) == 2
        assert isinstance(item.promotion_id, str)
        UUID(item.promotion_id)  # Validate UUID format

    def test_create_promotion_item_minimal(self):
        """Test creating promotion item with minimal fields"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Black Friday",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Huge discounts!",
        )
        assert item.title == "Black Friday"
        assert item.keywords == []  # Default empty list

    def test_title_validation_strips_whitespace(self):
        """Test that title whitespace is stripped"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="  Holiday Sale  ",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.title == "Holiday Sale"

    def test_title_validation_empty_raises_error(self):
        """Test that empty title raises validation error"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="Title cannot be empty"):
            PromotionItem(
                title="   ",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
            )

    def test_title_validation_purely_numeric_raises_error(self):
        """Test that purely numeric title raises error"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="purely numeric"):
            PromotionItem(
                title="12345",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
            )

    def test_keywords_validation_normalizes(self):
        """Test keyword normalization (lowercase, trim)"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            keywords=["  SUMMER  ", "Sale", "DISCOUNT"],
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.keywords == ["summer", "sale", "discount"]

    def test_keywords_validation_removes_duplicates(self):
        """Test that duplicate keywords are removed"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            keywords=["summer", "sale", "summer", "discount", "sale"],
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.keywords == ["summer", "sale", "discount"]

    def test_keywords_validation_removes_empty(self):
        """Test that empty keywords are removed"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            keywords=["summer", "", "  ", "sale"],
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.keywords == ["summer", "sale"]

    def test_keywords_validation_max_length(self):
        """Test keyword max length validation"""
        now = datetime.now(timezone.utc)
        long_keyword = "a" * 51
        with pytest.raises(ValueError, match="Keyword too long"):
            PromotionItem(
                title="Sale",
                keywords=[long_keyword],
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
            )

    def test_keywords_validation_max_count(self):
        """Test maximum keywords count"""
        now = datetime.now(timezone.utc)
        keywords = [f"keyword{i}" for i in range(21)]
        with pytest.raises(ValueError, match="Maximum 20 keywords"):
            PromotionItem(
                title="Sale",
                keywords=keywords,
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
            )

    def test_details_validation_empty_raises_error(self):
        """Test that empty details raises error"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="Details cannot be empty"):
            PromotionItem(
                title="Sale",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="   ",
            )

    def test_date_validation_end_before_start_raises_error(self):
        """Test that end_date before start_date raises error"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            PromotionItem(
                title="Sale",
                start_date=now + timedelta(days=10),
                end_date=now,
                details="Details",
            )

    def test_date_validation_end_equals_start_raises_error(self):
        """Test that end_date equal to start_date raises error"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            PromotionItem(
                title="Sale",
                start_date=now,
                end_date=now,
                details="Details",
            )

    def test_priority_defaults_to_zero(self):
        """Test that priority defaults to 0 for legacy promotions"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.priority == 0

    def test_priority_negative_raises_error(self):
        """Test that a negative priority is rejected"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            PromotionItem(
                title="Sale",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
                priority=-1,
            )

    def test_extra_fields_ignored(self):
        """Test that undeclared fields are accepted and silently dropped

        Promotions are written by Backoffice, which ships on its own cycle and
        may add fields before this model declares them (CU-86ak5jhrk).
        """
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
            extra_field="ignored",
        )
        assert item.title == "Sale"
        assert not hasattr(item, "extra_field")
        assert "extra_field" not in item.model_dump()

    def test_buttons_default_empty(self):
        """Test that a promotion with no buttons defaults to an empty list"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        assert item.buttons == []

    def test_buttons_accepts_promotion_target(self):
        """Test a button targeting another promotion (existing behavior)"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
            buttons=[PromotionButton(text="See other promo", promotion_id="promo-2")],
        )
        assert item.buttons[0].promotion_id == "promo-2"
        assert item.buttons[0].fixture_id is None

    def test_buttons_accepts_fixture_target(self):
        """Test a button targeting a specific fixture"""
        now = datetime.now(timezone.utc)
        item = PromotionItem(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
            buttons=[
                PromotionButton(
                    text="Ver partido",
                    fixture_id="fix-1",
                    sport_id="1",
                    tournament_id="10",
                )
            ],
        )
        assert item.buttons[0].fixture_id == "fix-1"
        assert item.buttons[0].promotion_id is None


class TestPromotionButton:
    """Test the promotion button model (CU-86ak0ajez)"""

    def test_requires_a_target(self):
        with pytest.raises(ValueError, match="either promotion_id or fixture_id"):
            PromotionButton(text="No target")

    def test_rejects_both_targets(self):
        with pytest.raises(ValueError, match="not both"):
            PromotionButton(
                text="Ambiguous",
                promotion_id="promo-1",
                fixture_id="fix-1",
                sport_id="1",
                tournament_id="10",
            )

    def test_fixture_target_requires_sport_and_tournament(self):
        with pytest.raises(ValueError, match="requires sport_id and tournament_id"):
            PromotionButton(text="Ver partido", fixture_id="fix-1")

    def test_promotion_target_does_not_require_sport_or_tournament(self):
        button = PromotionButton(text="See other promo", promotion_id="promo-2")
        assert button.sport_id is None
        assert button.tournament_id is None

    def test_extra_fields_ignored(self):
        """Undeclared button fields are accepted and silently dropped

        Buttons come from the same Backoffice-written config as their parent
        promotion, so they need the same tolerance (CU-86ak5jhrk).
        """
        button = PromotionButton(
            text="Bad", promotion_id="promo-2", extra_field="ignored"
        )
        assert button.text == "Bad"
        assert not hasattr(button, "extra_field")
        assert "extra_field" not in button.model_dump()

    def test_to_inline_keyboard_button_fixture_target(self):
        button = PromotionButton(
            text="Ver partido",
            fixture_id="fix-1",
            sport_id="1",
            tournament_id="10",
        )
        assert button.to_inline_keyboard_button() == InlineKeyboardButton(
            text="Ver partido",
            callback_data="oi:S1.T10.Ffix-1",
        )

    def test_to_inline_keyboard_button_promotion_target(self):
        button = PromotionButton(text="See other promo", promotion_id="promo-2")
        assert button.to_inline_keyboard_button() == InlineKeyboardButton(
            text="See other promo",
            callback_data="promo:promo-2",
        )

    def test_rejects_fixture_target_exceeding_telegram_callback_limit(self):
        with pytest.raises(ValueError, match="exceeding Telegram's 64-char callback_data limit"):
            PromotionButton(
                text="Ver partido",
                fixture_id="fixture-id-that-is-way-too-long-for-a-callback",
                sport_id="sr:sport:1",
                tournament_id="sr:tournament:8",
            )

    def test_accepts_fixture_target_at_exactly_64_chars(self):
        # "oi:S" + "T" + "." + "." + "F" = 8 fixed chars; pad ids to land on 64.
        sport_id = "s" * 20
        tournament_id = "t" * 20
        fixture_id = "f" * 16
        button = PromotionButton(
            text="Ver partido",
            fixture_id=fixture_id,
            sport_id=sport_id,
            tournament_id=tournament_id,
        )
        assert len(button.to_inline_keyboard_button().callback_data) == 64


class TestPromotionsConfig:
    """Test promotions configuration with array"""

    def test_create_empty_config(self):
        """Test creating empty config"""
        config = PromotionsConfig.from_minimal()
        assert config.promotions == []
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_add_promotion(self):
        """Test adding promotions to array"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Black Friday",
            start_date=now,
            end_date=now + timedelta(days=3),
            details="Huge discounts!",
            keywords=["black", "friday"],
        )

        assert len(config.promotions) == 1
        assert config.promotions[0] == promo
        assert promo.title == "Black Friday"
        assert len(promo.keywords) == 2

    def test_add_multiple_promotions(self):
        """Test adding multiple promotions"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo1 = config.add_promotion(
            title="First",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="First promo",
        )

        promo2 = config.add_promotion(
            title="Second",
            start_date=now,
            end_date=now + timedelta(days=2),
            details="Second promo",
        )

        assert len(config.promotions) == 2
        assert config.promotions[0] == promo1
        assert config.promotions[1] == promo2

    def test_add_promotion_with_custom_id(self):
        """Test adding promotion with custom ID"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Custom ID",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
            promotion_id="custom-id-123",
        )

        assert promo.promotion_id == "custom-id-123"

    def test_remove_promotion(self):
        """Test removing promotion by ID"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        assert len(config.promotions) == 1
        removed = config.remove_promotion(promo.promotion_id)
        assert removed is True
        assert len(config.promotions) == 0

    def test_remove_promotion_not_found(self):
        """Test removing non-existent promotion returns False"""
        config = PromotionsConfig.from_minimal()
        removed = config.remove_promotion("nonexistent-id")
        assert removed is False

    def test_get_promotion(self):
        """Test getting promotion by ID"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Sale",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        found = config.get_promotion(promo.promotion_id)
        assert found == promo
        assert found.title == "Sale"

    def test_get_promotion_not_found(self):
        """Test getting non-existent promotion returns None"""
        config = PromotionsConfig.from_minimal()
        not_found = config.get_promotion("nonexistent")
        assert not_found is None

    def test_get_active_promotions(self):
        """Test filtering active promotions"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        # Active promotion
        config.add_promotion(
            title="Active",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Active now",
        )

        # Future promotion
        config.add_promotion(
            title="Future",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=10),
            details="Coming soon",
        )

        # Expired promotion
        config.add_promotion(
            title="Expired",
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=5),
            details="Already ended",
        )

        active = config.get_active_promotions()
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_get_active_promotions_empty(self):
        """Test get_active_promotions with no active promotions"""
        config = PromotionsConfig.from_minimal()
        active = config.get_active_promotions()
        assert active == []

    def test_get_active_promotions_orders_by_priority(self):
        """Test that active promotions are ordered by priority ascending (CU-86ak3z2f1)"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Power Play #1",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
            priority=2,
        )
        config.add_promotion(
            title="Power Play #2",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
            priority=1,
        )

        active = config.get_active_promotions()
        assert [p.title for p in active] == ["Power Play #2", "Power Play #1"]

    def test_get_active_promotions_defaults_priority_to_zero(self):
        """Test legacy promotions without priority default to 0 and don't break ordering"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Legacy",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
        )
        config.add_promotion(
            title="New",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
            priority=1,
        )

        active = config.get_active_promotions()
        assert active[0].priority == 0
        assert [p.title for p in active] == ["Legacy", "New"]

    def test_get_active_promotions_same_priority_tiebreaks_by_title(self):
        """Test deterministic tiebreak (title) when priority collides"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Zebra Sale",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
            priority=5,
        )
        config.add_promotion(
            title="Alpha Sale",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Details",
            priority=5,
        )

        active = config.get_active_promotions()
        assert [p.title for p in active] == ["Alpha Sale", "Zebra Sale"]

    def test_duplicate_id_validation(self):
        """Test duplicate promotion_id validation"""
        now = datetime.now(timezone.utc)
        item1 = PromotionItem(
            promotion_id="same-id",
            title="First",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )
        item2 = PromotionItem(
            promotion_id="same-id",
            title="Second",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        with pytest.raises(ValueError, match="Duplicate promotion_id"):
            PromotionsConfig(promotions=[item1, item2])

    def test_max_promotions_validation(self):
        """Test maximum promotions validation"""
        now = datetime.now(timezone.utc)
        promotions = [
            PromotionItem(
                title=f"Promo{i}",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
            )
            for i in range(101)
        ]

        with pytest.raises(ValueError, match="Maximum 100 promotions"):
            PromotionsConfig(promotions=promotions)

    def test_touch_updates_timestamp(self):
        """Test touch() method"""
        config = PromotionsConfig.from_minimal()
        config.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        original = config.updated_at
        config.touch()
        assert config.updated_at > original

    def test_add_promotion_calls_touch(self):
        """Test that add_promotion updates timestamp"""
        config = PromotionsConfig.from_minimal()
        config.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        original = config.updated_at
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        assert config.updated_at > original

    def test_remove_promotion_calls_touch(self):
        """Test that remove_promotion updates timestamp"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        config.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        original = config.updated_at
        config.remove_promotion(promo.promotion_id)
        assert config.updated_at > original

    def test_to_dynamodb_item(self):
        """Test DynamoDB serialization"""
        config = PromotionsConfig.from_minimal()
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
            keywords=["test"],
        )

        item = config.to_dynamodb_item()
        assert isinstance(item, dict)
        assert "promotions" in item
        assert isinstance(item["promotions"], list)
        assert len(item["promotions"]) == 1
        assert isinstance(item["created_at"], str)  # ISO format
        assert isinstance(item["promotions"][0]["start_date"], str)
        assert item["promotions"][0]["keywords"] == ["test"]

    def test_parses_promotion_with_unknown_backoffice_field_cu_86ak5jhrk(self):
        """A promotion carrying an undeclared Backoffice field still parses.

        Regression for CU-86ak5jhrk. A staging QA fixture
        (``company#123456`` / ``promotions_config``) grew a ``banner_url``
        field on one promotion. Because these models forbade extra inputs,
        ``CompanyConfig(**payload)`` raised ``extra_forbidden`` at
        ``promotions.promotions.0.banner_url``. chatbet-channel-services
        builds every company's config at boot, so that single tenant's data
        stopped the process from starting: the container never booted, the
        ECS circuit breaker aborted the deploy, and the rollback failed
        identically because the DATA changed and not the code. The stack sat
        in ``UPDATE_ROLLBACK_FAILED`` for a week (CU-86akf2we9).

        This is the third field to cause it: ``priority`` (CU-86ak4q6qv),
        ``buttons`` (CU-86ak0ajez), then ``banner_url``. Do not restore
        ``extra="forbid"`` here — Backoffice owns this data and deploys
        separately, so a reader that rejects unknown fields turns every
        Backoffice release into an outage.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "promotions": [
                {
                    "promotion_id": "e2f1c0d4-1a2b-4c3d-9e8f-0a1b2c3d4e5f",
                    "title": "Bono de bienvenida",
                    "start_date": now.isoformat(),
                    "end_date": (now + timedelta(days=30)).isoformat(),
                    "details": "Deposita y recibe 100% extra",
                    "keywords": ["bono", "bienvenida"],
                    "priority": 1,
                    "buttons": [],
                    # Written by Backoffice, not declared by this model.
                    "banner_url": "https://cdn.example.com/promos/welcome.png",
                }
            ],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        config = PromotionsConfig(**payload)

        assert len(config.promotions) == 1
        promotion = config.promotions[0]
        assert promotion.title == "Bono de bienvenida"
        assert promotion.priority == 1
        assert not hasattr(promotion, "banner_url")
        assert "banner_url" not in promotion.model_dump()
        assert "banner_url" not in config.to_dynamodb_item()["promotions"][0]


class TestPromotionsConfigDB:
    """Test DynamoDB variant"""

    def test_create_with_keys(self):
        """Test creating DB config with PK/SK"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        assert config.PK == "company#company123"
        assert config.SK == "promotions_config"
        assert config.promotions == []

    def test_missing_keys_raises_error(self):
        """Test that missing PK/SK raises error"""
        with pytest.raises(ValueError, match="PK and SK are required"):
            PromotionsConfigDB(promotions=[])

    def test_inherits_add_promotion(self):
        """Test that DB variant inherits add_promotion method"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        assert len(config.promotions) == 1
        assert config.promotions[0] == promo

    def test_inherits_remove_promotion(self):
        """Test that DB variant inherits remove_promotion method"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        removed = config.remove_promotion(promo.promotion_id)
        assert removed is True
        assert len(config.promotions) == 0

    def test_inherits_get_promotion(self):
        """Test that DB variant inherits get_promotion method"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        now = datetime.now(timezone.utc)

        promo = config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        found = config.get_promotion(promo.promotion_id)
        assert found == promo

    def test_inherits_get_active_promotions(self):
        """Test that DB variant inherits get_active_promotions method"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Active",
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=1),
            details="Active",
        )

        config.add_promotion(
            title="Future",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=10),
            details="Future",
        )

        active = config.get_active_promotions()
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_to_dynamodb_item_includes_keys(self):
        """Test serialization includes PK/SK"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        item = config.to_dynamodb_item()

        assert "PK" in item
        assert "SK" in item
        assert item["PK"] == "company#company123"
        assert item["SK"] == "promotions_config"

    def test_to_dynamodb_item_with_promotions(self):
        """Test serialization with promotions in array"""
        config = PromotionsConfigDB.from_minimal(company_id="company123")
        now = datetime.now(timezone.utc)

        config.add_promotion(
            title="Test",
            start_date=now,
            end_date=now + timedelta(days=1),
            details="Details",
        )

        item = config.to_dynamodb_item()
        assert "promotions" in item
        assert isinstance(item["promotions"], list)
        assert len(item["promotions"]) == 1
