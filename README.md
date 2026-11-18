# ChatBet Base Models

[![Tests](https://github.com/chatbet/chatbet-base-models/workflows/Tests/badge.svg)](https://github.com/chatbet/chatbet-base-models/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Pydantic Version](https://img.shields.io/badge/pydantic-2.x-green.svg)](https://pydantic.dev)
[![Code Coverage](https://codecov.io/gh/chatbet/chatbet-base-models/branch/main/graph/badge.svg)](https://codecov.io/gh/chatbet/chatbet-base-models)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Reusable Pydantic base models for ChatBet applications. This package centralizes common data models used across multiple ChatBet projects, providing type-safe and validated data structures for messaging, configuration, and API endpoints.

## 🚀 Features

- **Message Templates**: Comprehensive models for bot messages with Telegram-like inline keyboards
- **Platform Endpoints**: HTTP API endpoint configurations with method validation
- **Site Configuration**: Complete site and application configuration models
- **Sportsbook Configuration**: Models for sportsbook integrations (Betsw3, Digitain, Phoenix, Kambi, Plannatech, Isolutions)
- **Type Safety**: Full Pydantic v2 validation and type hints
- **Database Ready**: DynamoDB-compatible serialization methods
- **Fully Tested**: 295 comprehensive tests covering all models and edge cases
- **CI/CD Ready**: Automated testing across Python 3.10-3.12 with coverage enforcement

## 📦 Installation

```
pip install git+https://github.com/chatbet/chatbet-base-models.git@main
```

### Branch Installation

Different branches contain different versions and features:

- **main**: Stable production releases
- **develop**: Latest development features
- **staging**: Pre-release testing

```bash
# Install from specific branch
pip install git+https://github.com/chatbet/chatbet-base-models.git@develop

# Or with specific tag
pip install git+https://github.com/chatbet/chatbet-base-models.git@v1.0.0
```

## 🏗️ Project Structure

```
chatbet-base-models/
├── chatbet_base_models/
│   ├── __init__.py              # Main exports and version
│   ├── message_template.py      # Bot message templates
│   ├── platform_endpoints.py    # API endpoint configurations
│   ├── site_config_model.py     # Site configuration models
│   ├── sportbook_config.py      # Sportsbook configuration models
│   ├── lottery_config.py        # Lottery provider configuration models
│   ├── promotion_config.py      # Promotions management
│   └── tutorial.py              # Tutorial videos management
├── tests/
│   ├── test_message_template.py      # Message template tests
│   ├── test_platform_endpoints.py    # API endpoint tests
│   ├── test_site_config_model.py     # Site configuration tests
│   ├── test_sportbook_config.py      # Sportsbook config tests (55 tests)
│   ├── test_promotion_config.py      # Promotion tests
│   └── test_tutorial.py              # Tutorial tests
├── pytest.ini                  # Test configuration
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## 🛠️ Usage

### Message Templates

Create and manage bot message templates with inline keyboards:

```python
from chatbet_base_models import MessageTemplates, MessageItem, InlineKeyboardButton, InlineKeyboardMarkup

# Create a message with inline keyboard
welcome_message = MessageItem(
    text="Welcome to ChatBet! 🎯",
    reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Start Betting", callback_data="start_bet"),
                InlineKeyboardButton(text="Help", url="https://help.chatbet.gg")
            ]
        ]
    )
)

# Create complete message templates
templates = MessageTemplates.from_minimal()
templates.onboarding.greeting_message = welcome_message
```

### Platform Endpoints

Define and validate API endpoint configurations:

```python
from chatbet_base_models import APIEndpoints, Endpoint, HTTPMethod

# Create endpoint configuration
endpoints = APIEndpoints(
    auth=AuthEndpoints(
        login=Endpoint(
            method=HTTPMethod.POST,
            endpoint="https://api.chatbet.gg/auth/login",
            headers={"Content-Type": "application/json"}
        )
    )
)
```

### Site Configuration

Manage comprehensive site settings:

```python
from chatbet_base_models import SiteConfig, MoneyLimits, OddType

config = SiteConfig(
    identity=Identity(
        company_name="ChatBet",
        site_name="ChatBet Gaming"
    ),
    features=FeaturesConfig(
        odd_type=OddType.DECIMAL,
        money_limits=MoneyLimits(
            min_bet_amount=1.0,
            max_bet_amount=10000.0
        )
    )
)
```

### Database Integration

Models include DynamoDB-compatible serialization:

```python
# Convert to DynamoDB item format
db_item = templates.to_dynamodb_item()

# Use DB-ready models with partition/sort keys
from chatbet_base_models import MessageTemplatesDB

db_templates = MessageTemplatesDB.from_minimal("company_123")
print(db_templates.PK)  # "company#company_123"
print(db_templates.SK)  # "message_templates"
```

## 🧪 Development

### Requirements

- Python 3.10+
- Pydantic 2.x

### Development Setup

```bash
# Clone and install development dependencies
git clone https://github.com/chatbet/chatbet-base-models.git
cd chatbet-base-models
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_message_template.py
pytest tests/test_platform_endpoints.py
pytest tests/test_site_config_model.py
pytest tests/test_sportbook_config.py

# Run with coverage report
pytest --cov=chatbet_base_models --cov-report=html

# Run tests for specific functionality
pytest tests/test_message_template.py::TestMessageTemplates
pytest -k "test_create_button"
```

**Test Coverage:**
- ✅ **Message Templates**: Tests covering inline keyboards, serialization, factory methods
- ✅ **Platform Endpoints**: Tests for HTTP methods, endpoint validation, DynamoDB serialization
- ✅ **Site Configuration**: Tests for integrations, locale, limits, legacy compatibility
- ✅ **Sportsbook Configuration**: 47 tests for providers (Betsw3, Digitain, Phoenix, Kambi, Plannatech, Isolutions), tournaments, competitions
- ✅ **Promotions**: Tests for promotion management and active promotions
- ✅ **Tutorials**: Tests for tutorial video management

**What's Tested:**
- Pydantic model validation and constraints
- Factory methods with sensible defaults
- DynamoDB serialization (datetime, HttpUrl, Enum, Decimal)
- Legacy field mapping and backward compatibility
- Error handling for invalid inputs
- Edge cases and boundary conditions

**Additional Development Tools:**
```bash
# Type checking
mypy chatbet_base_models/

# Code formatting
black chatbet_base_models/
isort chatbet_base_models/
```

## 📚 Available Models

### Message Templates
- `MessageItem` - Individual message with optional keyboard
- `OnboardingMessages` - Welcome and greeting messages
- `ValidationMessages` - User validation prompts
- `BetsMessages` - Betting flow messages
- `MenuMessages` - Navigation and menu messages
- `ErrorMessages` - Error handling messages

### Configuration Models
- `SiteConfig` - Complete site configuration
- `SportbookConfig` - Sportsbook integration settings
- `LotteryConfig` - Lottery provider settings of a lottery company (`site_config.identity.company_type = "lottery"`)
- `APIEndpoints` - API endpoint configurations
- `MoneyLimits` - Betting limits and constraints
- `PromotionsConfig` - Promotions management

### Sportsbook Providers
- `Betsw3Config` - Betsw3 provider configuration
- `DigitainConfig` - Digitain provider configuration
- `PhoenixConfig` - Phoenix provider configuration
- `KambiConfig` - Kambi provider configuration
- `PlannatechConfig` - Plannatech provider configuration
- `IsolutionsConfig` - Isolutions provider configuration

### Platform Integration
- `WhatsAppConfig` - WhatsApp integration settings
- `TelegramConfig` - Telegram bot configuration
- `MeilisearchConfig` - Search engine configuration

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. **Add comprehensive tests** for new functionality
5. Ensure all tests pass (`pytest`)
6. Verify test coverage remains high (`pytest --cov=chatbet_base_models`)
7. Run code formatting (`black . && isort .`)
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

**Testing Requirements:**
- All new models must include corresponding tests
- Tests should cover validation, serialization, and edge cases
- Maintain the existing test coverage standards
- Use descriptive test names and clear assertions

## 📋 Version History

- **v1.0.0** - Initial release with core models and comprehensive test suite
- **develop** - Latest development features
- **staging** - Pre-release testing

## 🧪 Quality Assurance

This project maintains high quality standards through:

- **295 comprehensive tests** with 100% pass rate
- **Type safety** with Pydantic v2 models
- **Input validation** for all model fields
- **Serialization testing** for DynamoDB compatibility
- **Legacy compatibility** testing for backward compatibility
- **Edge case coverage** for robust error handling
- **80%+ code coverage** enforced automatically

**CI/CD Ready**: All tests run automatically on GitHub Actions:
- ✅ **Tests must pass** across Python 3.10-3.12
- ✅ **Coverage must be ≥80%** or merge is blocked
- ✅ **295 comprehensive tests** executed automatically

## 🔒 Quality Gates

This repository enforces quality standards through automated testing:

### 🚫 **Merge is BLOCKED if:**
- Any test fails (295 tests must pass)
- Code coverage drops below 80%

### 🎯 **Branch Protection Rules:**
- **Main branch**: Requires PR approval + all tests passing
- **No direct pushes** to protected branches

See [Branch Protection Setup](.github/BRANCH_PROTECTION.md) for configuration details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About ChatBet

ChatBet is a modern sports betting platform that provides conversational betting experiences through popular messaging platforms.

For more information, visit [chatbet.gg](https://chatbet.gg) or contact us at [tech@chatbet.gg](mailto:tech@chatbet.gg).

---

Made with ❤️ by the ChatBet Team