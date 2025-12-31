"""
ChatBet Base Models

Reusable Pydantic base models for ChatBet applications.
This package centralizes common data models used across
multiple ChatBet projects.
"""

__version__ = "1.0.0"

# Message Templates
from .message_template import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MessageItem,
    OnboardingMessages,
    ValidationMessages,
    RegistrationMessages,
    MenuMessages,
    BetsMessages,
    CombosMessages,
    ErrorMessages,
    ConfirmationMessages,
    LabelMessages,
    EndMessages,
    GuidanceMessages,
    MessageTemplates,
    MessageTemplatesDB,
)

# Platform Endpoints
from .platform_endpoints import (
    HTTPMethod,
    Endpoint,
    AuthEndpoints,
    UsersEndpoints,
    SportsEndpoints,
    FixturesEndpoints,
    TournamentsEndpoints,
    OddsEndpoints,
    BetsEndpoints,
    CombosEndpoints,
    APIEndpoints,
    APIEndpointsDB,
)

# Site Configuration
from .site_config_model import (
    OddType,
    ValidationMethod,
    ChatbetVersion,
    HourFormat,
    AliasProbabilities,
    MoneyLimits,
    TestConfig,
    WhatsAppProvider,
    MeilisearchIndexPaths,
    MeilisearchConfig,
    TwilioConfig,
    TelegramConfig,
    WhapiConfig,
    WhatsAppConfig,
    WhatsAppUnion,
    WhatsAppIntegration,
    Integrations,
    Identity,
    LocaleConfig,
    FeaturesConfig,
    Meta,
    SiteConfig,
    SiteConfigDB,
)

# Sportbook Configuration
from .sportbook_config import (
    Competition,
    Region,
    Tournament,
    Betsw3Config,
    DigitainConfig,
    PhoenixBasicAuth,
    PhoenixConfig,
    ConfigUnion,
    StakeType,
    SportbookConfig,
    SportbookConfigDB,
)

# Promotion Configuration
from .promotion_config import (
    PromotionItem,
    PromotionsConfig,
    PromotionsConfigDB,
)

__all__ = [
    # Version
    "__version__",
    # Message Templates
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "MessageItem",
    "OnboardingMessages",
    "ValidationMessages",
    "RegistrationMessages",
    "MenuMessages",
    "BetsMessages",
    "CombosMessages",
    "ErrorMessages",
    "ConfirmationMessages",
    "LabelMessages",
    "EndMessages",
    "GuidanceMessages",
    "MessageTemplates",
    "MessageTemplatesDB",
    # Platform Endpoints
    "HTTPMethod",
    "Endpoint",
    "AuthEndpoints",
    "UsersEndpoints",
    "SportsEndpoints",
    "FixturesEndpoints",
    "TournamentsEndpoints",
    "OddsEndpoints",
    "BetsEndpoints",
    "CombosEndpoints",
    "APIEndpoints",
    "APIEndpointsDB",
    # Site Configuration
    "OddType",
    "ValidationMethod",
    "ChatbetVersion",
    "HourFormat",
    "AliasProbabilities",
    "MoneyLimits",
    "TestConfig",
    "WhatsAppProvider",
    "MeilisearchIndexPaths",
    "MeilisearchConfig",
    "TwilioConfig",
    "TelegramConfig",
    "WhapiConfig",
    "WhatsAppConfig",
    "WhatsAppUnion",
    "WhatsAppIntegration",
    "Integrations",
    "Identity",
    "LocaleConfig",
    "FeaturesConfig",
    "Meta",
    "SiteConfig",
    "SiteConfigDB",
    # Sportbook Configuration
    "Competition",
    "Region",
    "Tournament",
    "Betsw3Config",
    "DigitainConfig",
    "PhoenixBasicAuth",
    "PhoenixConfig",
    "ConfigUnion",
    "StakeType",
    "SportbookConfig",
    "SportbookConfigDB",
    # Promotion Configuration
    "PromotionItem",
    "PromotionsConfig",
    "PromotionsConfigDB",
]
