# ChatBet Base Models

Python library that centralizes reusable Pydantic models for ChatBet applications. Provides type-safe validation and serialization for a conversational sports betting platform.

## Project Structure

```
chatbet-base-models/
├── chatbet_base_models/          # Main modules
│   ├── __init__.py               # Exports all public models
│   ├── message_template.py       # Message templates and keyboards
│   ├── platform_endpoints.py     # HTTP endpoint configuration
│   ├── site_config_model.py      # Site configuration
│   ├── sportbook_config.py       # Sportsbook configuration
│   ├── promotion_config.py       # Promotions management
│   └── tutorial.py               # Tutorial videos management
├── tests/                        # Test suite (291 tests)
├── pyproject.toml                # Project configuration
└── pytest.ini                    # Pytest configuration
```

## Main Modules

### message_template.py
Models for bot messages with Telegram-like interactive keyboards:
- `InlineKeyboardButton`, `InlineKeyboardMarkup`: Buttons and keyboards
- `MessageItem`: Message with text and optional keyboard
- `OnboardingMessages`, `ValidationMessages`, `RegistrationMessages`: User flows
- `BetsMessages`, `CombosMessages`: Betting flow
- `MessageTemplates`: Container for all templates
- `MessageTemplatesDB`: DynamoDB variant

### platform_endpoints.py
HTTP endpoint configuration for APIs:
- `Endpoint`: Single endpoint config (method, url, headers, payload)
- `AuthEndpoints`, `UsersEndpoints`, `SportsEndpoints`, `FixturesEndpoints`: Endpoint groups
- `APIEndpoints`: Unified container
- `APIEndpointsDB`: DynamoDB variant with factory method

### site_config_model.py
Complete site configuration:
- `Identity`: Company and site name
- `MoneyLimits`: Betting limits (min/max)
- `Integrations`: Meilisearch, Twilio, Telegram, WhatsApp, Bitly
- `FeaturesConfig`: odd_type, validation_method, etc.
- `SiteConfig` / `SiteConfigDB`: Complete configuration

### sportbook_config.py
Sportsbook provider configuration:
- Providers: `Betsw3Config`, `DigitainConfig`, `PhoenixConfig`, `KambiConfig`, `PlannatechConfig`, `IsolutionsConfig`
- `SportsS3Reference`: Reference to sports hierarchy in S3
- `SportbookConfig` / `SportbookConfigDB`: Main container

### promotion_config.py
Promotions management:
- `PromotionItem`: Individual promotion with dates, title, keywords
- `PromotionsConfig`: Array with add/remove/get_active_promotions methods
- `PromotionsConfigDB`: DynamoDB variant

### tutorial.py
Tutorial videos management:
- `TutorialItemDB`: Tutorial item with s3_key, title, metadata
- `TutorialsDB`: Array with add/remove/get methods

## Key Features

- **Type-Safe Validation**: Pydantic v2 with `ConfigDict(extra="forbid")`
- **DynamoDB-Ready**: "DB" models with PK/SK and `.to_dynamodb_item()`
- **Factory Methods**: `from_minimal()`, `default_factory()` for quick instantiation
- **Backward Compatibility**: String coercion, legacy field mapping, typo correction

## Commands

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=chatbet_base_models --cov-report=html

# Format code
black chatbet_base_models tests
isort chatbet_base_models tests

# Type checking
mypy chatbet_base_models
```

## Usage in Other Projects

```bash
# Install from main (stable)
pip install git+https://github.com/chatbet/chatbet-base-models.git@main

# Install from develop
pip install git+https://github.com/chatbet/chatbet-base-models.git@develop
```

```python
from chatbet_base_models import (
    MessageTemplates,
    APIEndpointsDB,
    SiteConfig,
    SportbookConfig,
    SportbookConfigDB,
    IsolutionsConfig,
    PromotionsConfig,
)

# Create templates with defaults
templates = MessageTemplates.from_minimal()

# Create endpoints with placeholders
endpoints = APIEndpointsDB.default_factory("company_123")

# Create Isolutions sportsbook config
config = SportbookConfigDB.from_minimal_isolutions(
    company_id="your_company",
    api_url="https://api-stg.bolabet.co.zm",
    api_account="ChatBet",
    api_password="secret",
    events_program_code="your_code",
)

# Serialize for DynamoDB
db_item = config.to_dynamodb_item()
```

## Dependencies

- Python 3.10+
- pydantic>=2.0.0,<3.0.0

## Testing

- 291 tests total (100% pass rate)
- Coverage >= 80% enforced
- Supports Python 3.10, 3.11, 3.12
