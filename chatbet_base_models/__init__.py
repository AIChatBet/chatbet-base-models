"""
ChatBet Base Models

Reusable Pydantic base models for ChatBet applications.
This package centralizes common data models used across
multiple ChatBet projects.
"""

__version__ = "1.1.0"

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
    LinkItem,
    LinksMessages,
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
    MarketsEndpoints,
    SportCatalogEndpoints,
    APIEndpoints,
    APIEndpointsDB,
)

# Site Configuration
from .site_config_model import (
    OddType,
    ValidationMethod,
    TwilioAuthChannel,
    ChatbetVersion,
    HourFormat,
    AliasProbabilities,
    MoneyLimits,
    TestConfig,
    SessionConfig,
    WhatsAppProvider,
    MeilisearchIndexPaths,
    MeilisearchConfig,
    TwilioConfig,
    TelegramConfig,
    WhapiConfig,
    WhatsAppConfig,
    WhatsAppUnion,
    WhatsAppIntegration,
    WebWidgetKey,
    WebConfig,
    Integrations,
    Identity,
    LocaleConfig,
    FeaturesConfig,
    Meta,
    AuthConfig,
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
    KambiOffering,
    KambiPlayer,
    KambiConfig,
    PlannatechConfig,
    IsolutionsConfig,
    BetbyConfig,
    VelisportsBasicAuth,
    VelisportsConfig,
    ConfigUnion,
    StakeType,
    SportbookConfig,
    SportbookConfigDB,
    SportsS3Reference,
)

# Promotion Configuration
from .promotion_config import (
    PromotionButton,
    PromotionItem,
    PromotionsConfig,
    PromotionsConfigDB,
)

# Tutorial
from .tutorial import (
    TutorialItemDB,
    TutorialsDB,
    TutorialVideo,
    GetTutorialVideosResponse,
    UploadTutorialVideoResponse,
    DeleteTutorialVideoResponse,
)

# Onboarding Questions
from .onboarding_questions import (
    ALLOWED_STORAGE_ROOTS,
    OnboardingPhase,
    OnboardingQuestionItem,
    OnboardingQuestions,
    OnboardingQuestionsDB,
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
    "LinkItem",
    "LinksMessages",
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
    "MarketsEndpoints",
    "SportCatalogEndpoints",
    "APIEndpoints",
    "APIEndpointsDB",
    # Site Configuration
    "OddType",
    "ValidationMethod",
    "TwilioAuthChannel",
    "ChatbetVersion",
    "HourFormat",
    "AliasProbabilities",
    "MoneyLimits",
    "TestConfig",
    "SessionConfig",
    "WhatsAppProvider",
    "MeilisearchIndexPaths",
    "MeilisearchConfig",
    "TwilioConfig",
    "TelegramConfig",
    "WhapiConfig",
    "WhatsAppConfig",
    "WhatsAppUnion",
    "WhatsAppIntegration",
    "WebWidgetKey",
    "WebConfig",
    "Integrations",
    "Identity",
    "LocaleConfig",
    "FeaturesConfig",
    "Meta",
    "AuthConfig",
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
    "KambiOffering",
    "KambiPlayer",
    "KambiConfig",
    "PlannatechConfig",
    "IsolutionsConfig",
    "BetbyConfig",
    "VelisportsBasicAuth",
    "VelisportsConfig",
    "ConfigUnion",
    "StakeType",
    "SportbookConfig",
    "SportbookConfigDB",
    "SportsS3Reference",
    # Promotion Configuration
    "PromotionButton",
    "PromotionItem",
    "PromotionsConfig",
    "PromotionsConfigDB",
    # Tutorial
    "TutorialItemDB",
    "TutorialsDB",
    "TutorialVideo",
    "GetTutorialVideosResponse",
    "UploadTutorialVideoResponse",
    "DeleteTutorialVideoResponse",
    # Onboarding Questions
    "ALLOWED_STORAGE_ROOTS",
    "OnboardingPhase",
    "OnboardingQuestionItem",
    "OnboardingQuestions",
    "OnboardingQuestionsDB",
]
