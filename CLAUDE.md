# ChatBet Base Models

Python library that centralizes reusable Pydantic models for ChatBet applications. Provides type-safe validation and serialization for a conversational sports betting platform.

## Project Structure

```
chatbet-base-models/
├── chatbet_base_models/          # Main modules
│   ├── __init__.py               # Exports all public models
│   ├── message_template.py       # Message templates and keyboards
│   ├── message_tokens.py         # {TOKEN} scanner shared by validators and renderer
│   ├── message_render.py         # Single render engine (preview + sending)
│   ├── message_catalog.py        # Dynamic catalog types + legacy shape conversion
│   ├── message_destinations.py   # Button destination catalog + callback generator
│   ├── message_flow.py           # Event catalog + client flow (event -> message)
│   ├── platform_endpoints.py     # HTTP endpoint configuration
│   ├── site_config_model.py      # Site configuration
│   ├── sportbook_config.py       # Sportsbook configuration
│   ├── promotion_config.py       # Promotions management
│   ├── tutorial.py               # Tutorial videos management
│   └── onboarding_questions.py   # Operator-configured onboarding questions
├── tests/                        # Test suite (715 tests)
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

### message_tokens.py / message_render.py / message_catalog.py
Dynamic message catalog support (CU-86akn2750):
- `extract_tokens`, `build_scan_pattern`: the one `{TOKEN}` scanner (`{{` / `}}` are escaped braces)
- `render`: single render engine; unresolved tokens stay raw and are logged; never raises
- `CatalogEntry`, `MessageCatalog`, `MessageContent`, `ClientMessages`: shared types of the dynamic catalog (the data lives in DynamoDB, never in this package); a message is single (text + at most 10 buttons, no `additional_message`)
- `legacy_to_client_messages`: legacy 11-section `MessageTemplates` -> `LegacyConversion` (new `ClientMessages` + warnings)
- `DEFAULT_ACCOUNT_STATE` (exported): localized account-state fallbacks; consumers read it directly, it is not stored per client

### message_destinations.py / message_flow.py
Flow structures (CU-86akn2750, stage 1): what a button leads to and which message each event shows:
- `ButtonDestination` (in `message_template.py`): destination id + params; optional `destination` on `InlineKeyboardButton`, stored next to the generated `callback_data`
- `DestinationDef`, `DestinationCatalog`, `ParamDef`: global destination catalog types (data lives in DynamoDB, never in this package); ids are plain strings
- `render_destination`: builds the callback (or URL) of a destination; raises `ValueError`, never truncates (64-byte limit)
- `find_destination_problems`: readable problems of a button's destination (unknown destination, bad params, unknown message key)
- `EventDef`, `EventCatalog`, `ClientFlow`: events the bot reports and the per-client `event -> message key` routes (the global default flow has the same shape)
- `find_event_catalog_problems`, `find_flow_problems`: cross-validation against the message catalog

### platform_endpoints.py
HTTP endpoint configuration for APIs:
- `Endpoint`: Single endpoint config (method, url, headers, payload)
- `AuthEndpoints`, `UsersEndpoints`, `SportsEndpoints`, `FixturesEndpoints`: Endpoint groups
- `SportCatalogEndpoints`: Sport Catalog endpoints (get_sports, get_regions, get_tournaments, get_markets)
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

### onboarding_questions.py
Operator-configured profiling questions the agent weaves into conversation (SK `onboarding_questions`):
- `OnboardingPhase`: `first_encounter` | `getting_to_know` | `window_frame`
- `OnboardingQuestionItem`: one question — `agent_instruction` (an instruction, never a literal script), `storage_key`, `hook_hints`, optional date window
- `OnboardingQuestions` / `OnboardingQuestionsDB`: container with `seed_default()` (the three questions the agent asks today) and `get_active_questions()`

## Key Features

- **Type-Safe Validation**: Pydantic v2 with `ConfigDict(extra="forbid")`, except the
  promotion config chain (`PromotionButton`, `PromotionItem`, `PromotionsConfig`), which
  uses `extra="ignore"` — see the extra-field policy note in `promotion_config.py`
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

- 715 tests total (100% pass rate)
- Coverage >= 80% enforced
- Supports Python 3.10, 3.11, 3.12
