import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID

from chatbet_base_models.promotion_config import (
    PromotionItem,
    PromotionsConfig,
    PromotionsConfigDB,
)


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

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError):
            PromotionItem(
                title="Sale",
                start_date=now,
                end_date=now + timedelta(days=1),
                details="Details",
                extra_field="not allowed",
            )


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
        original = config.updated_at
        config.touch()
        assert config.updated_at > original

    def test_add_promotion_calls_touch(self):
        """Test that add_promotion updates timestamp"""
        config = PromotionsConfig.from_minimal()
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
