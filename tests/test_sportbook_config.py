import pytest
from datetime import datetime, timezone

from chatbet_base_models.sportbook_config import (
    Competition,
    Region,
    Tournament,
    Betsw3Config,
    DigitainConfig,
    PhoenixBasicAuth,
    PhoenixConfig,
    PlannatechConfig,
    IsolutionsConfig,
    StakeType,
    SportbookConfig,
    SportbookConfigDB,
    SportsS3Reference,
    _default_tournaments,
    _default_stake_types,
)


class TestCompetition:
    def test_create_competition(self):
        competition = Competition(id="1", name="Champions League")
        assert competition.id == "1"
        assert competition.name == "Champions League"
        assert competition.order == 999_999  # default

    def test_create_competition_with_order(self):
        competition = Competition(id="2", name="Premier League", order=1)
        assert competition.order == 1


class TestRegion:
    def test_create_region(self):
        competitions = [Competition(id="1", name="Champions League")]
        region = Region(id="eu", name="Europe", competitions=competitions)
        assert region.id == "eu"
        assert region.name == "Europe"
        assert len(region.competitions) == 1
        assert region.order == 999_999  # default

    def test_create_region_without_name(self):
        competitions = [Competition(id="1", name="Champions League")]
        region = Region(id="eu", competitions=competitions)
        assert region.name is None

    def test_create_region_with_order(self):
        competitions = [Competition(id="1", name="Champions League")]
        region = Region(id="eu", name="Europe", competitions=competitions, order=5)
        assert region.order == 5


class TestTournament:
    def test_create_tournament(self):
        competitions = [Competition(id="1", name="Champions League")]
        regions = [Region(id="eu", name="Europe", competitions=competitions)]

        tournament = Tournament(
            sport_id="soccer", sport_name="Football", regions=regions
        )

        assert tournament.sport_id == "soccer"
        assert tournament.sport_name == "Football"
        assert tournament.main_market is None
        assert len(tournament.regions) == 1
        assert tournament.order == 999_999  # default
        assert tournament.stake_types is not None  # default factory

    def test_create_tournament_with_all_fields(self):
        stake_types = [StakeType(id="1", name="Result")]
        competitions = [Competition(id="1", name="Champions League")]
        regions = [Region(id="eu", name="Europe", competitions=competitions)]

        tournament = Tournament(
            sport_id="soccer",
            sport_name="Football",
            main_market="result",
            regions=regions,
            stake_types=stake_types,
            order=1,
        )

        assert tournament.main_market == "result"
        assert tournament.order == 1
        assert len(tournament.stake_types) == 1


class TestStakeType:
    def test_create_stake_type(self):
        stake_type = StakeType(id="1", name="Result")
        assert stake_type.id == "1"
        assert stake_type.key is None
        assert stake_type.name == "Result"
        assert stake_type.order == 999_999  # default

    def test_create_stake_type_with_all_fields(self):
        stake_type = StakeType(id="2", key="over_under", name="Over/Under", order=2)
        assert stake_type.key == "over_under"
        assert stake_type.order == 2


class TestBetsw3Config:
    def test_create_betsw3_config(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        assert config.provider == "betsw3"
        assert config.userId == "user123"
        assert config.siteId == "site456"
        assert config.platformId == "platform789"
        assert config.language == "en"
        assert config.source == "web"
        assert config.currency == "USD"
        assert config.access_token == "token123"
        assert str(config.url) == "https://api.betsw3.com/"

    def test_invalid_url_raises_error(self):
        with pytest.raises(ValueError):
            Betsw3Config(
                userId="user123",
                siteId="site456",
                platformId="platform789",
                language="en",
                source="web",
                currency="USD",
                access_token="token123",
                url="not-a-valid-url",
            )


class TestDigitainConfig:
    def test_create_digitain_config(self):
        config = DigitainConfig(
            partner_id="partner123",
            client_id="client456",
            client_secret="secret789",
            token_url="https://digitain.com/token",
            websocket_url="wss://digitain.com/ws",
            validate_user_url="https://digitain.com/validate",
            place_bet_url="https://digitain.com/bet",
        )

        assert config.provider == "digitain"
        assert config.partner_id == "partner123"
        assert config.client_id == "client456"
        assert config.client_secret == "secret789"
        assert str(config.token_url) == "https://digitain.com/token"
        assert str(config.websocket_url) == "wss://digitain.com/ws"
        assert str(config.validate_user_url) == "https://digitain.com/validate"
        assert str(config.place_bet_url) == "https://digitain.com/bet"

    def test_invalid_websocket_url_raises_error(self):
        with pytest.raises(ValueError):
            DigitainConfig(
                partner_id="partner123",
                client_id="client456",
                client_secret="secret789",
                token_url="https://digitain.com/token",
                websocket_url=1,
                validate_user_url="https://digitain.com/validate",
                place_bet_url="https://digitain.com/bet",
            )


class TestPhoenixConfig:
    def test_create_phoenix_basic_auth(self):
        auth = PhoenixBasicAuth(username="admin", password="secret")
        assert auth.username == "admin"
        assert auth.password == "secret"

    def test_create_phoenix_config(self):
        basic_auth = PhoenixBasicAuth(username="admin", password="secret")

        config = PhoenixConfig(
            cluster_api_key="cluster_key",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1,server2",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="cluster_secret",
            origin_id="origin123",
            url="https://phoenix.example.com",
            basic_auth=basic_auth,
            last_state_epoch="1234567890",
            integration_state="active",
        )

        assert config.provider == "phoenix"
        assert config.cluster_api_key == "cluster_key"
        assert config.security_protocol == "SASL_SSL"
        assert config.bootstrap_servers == "server1,server2"
        assert config.group_id == "group1"
        assert config.mechanisms == "PLAIN"
        assert config.cluster_api_secret == "cluster_secret"
        assert config.origin_id == "origin123"
        assert str(config.url) == "https://phoenix.example.com/"
        assert config.basic_auth.username == "admin"
        assert config.last_state_epoch == "1234567890"
        assert config.integration_state == "active"

    def test_phoenix_config_with_int_epoch(self):
        basic_auth = PhoenixBasicAuth(username="admin", password="secret")

        config = PhoenixConfig(
            cluster_api_key="cluster_key",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1,server2",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="cluster_secret",
            origin_id="origin123",
            basic_auth=basic_auth,
            last_state_epoch=1234567890,
            integration_state="active",
        )

        assert config.last_state_epoch == 1234567890

    def test_phoenix_config_default_url(self):
        basic_auth = PhoenixBasicAuth(username="admin", password="secret")

        config = PhoenixConfig(
            cluster_api_key="cluster_key",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1,server2",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="cluster_secret",
            origin_id="origin123",
            basic_auth=basic_auth,
            last_state_epoch="1234567890",
            integration_state="active",
        )

        assert str(config.url) == "https://placeholder.com/"


class TestIsolutionsConfig:
    def test_create_isolutions_config(self):
        config = IsolutionsConfig(
            api_url="https://api-stg.bolabet.co.zm",
            api_account="ChatBet",
            api_password="secret123",
            events_program_code="mefvdituytybd",
        )

        assert config.provider == "isolutions"
        assert str(config.api_url) == "https://api-stg.bolabet.co.zm/"
        assert config.api_account == "ChatBet"
        assert config.api_password == "secret123"
        assert config.bookmaker_id == 1  # default
        assert config.events_program_code == "mefvdituytybd"
        assert config.language_id == 2  # default (English)
        assert config.fetch_interval_seconds == 60  # default
        assert config.check_fixture_availability is False  # default

    def test_create_isolutions_config_with_all_fields(self):
        config = IsolutionsConfig(
            api_url="https://api.bolabet.co.zm",
            api_account="TestAccount",
            api_password="TestPassword",
            bookmaker_id=5,
            events_program_code="custom_code",
            language_id=1,  # Spanish
            fetch_interval_seconds=30,
            check_fixture_availability=True,
        )

        assert config.provider == "isolutions"
        assert config.bookmaker_id == 5
        assert config.language_id == 1
        assert config.fetch_interval_seconds == 30
        assert config.check_fixture_availability is True

    def test_isolutions_config_invalid_url_raises_error(self):
        with pytest.raises(ValueError):
            IsolutionsConfig(
                api_url="not-a-valid-url",
                api_account="ChatBet",
                api_password="secret123",
                events_program_code="mefvdituytybd",
            )

    def test_isolutions_config_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            IsolutionsConfig(
                api_url="https://api-stg.bolabet.co.zm",
                api_account="ChatBet",
                api_password="secret123",
                events_program_code="mefvdituytybd",
                extra_field="not_allowed",
            )


class TestPlannatechConfig:
    def test_create_plannatech_config(self):
        config = PlannatechConfig(
            url="https://api.plannatech.com",
        )

        assert config.provider == "plannatech"
        assert str(config.url) == "https://api.plannatech.com/"
        assert config.grpc_url is None  # default
        assert config.check_fixture_availability is False  # default

    def test_create_plannatech_config_with_all_fields(self):
        config = PlannatechConfig(
            url="https://api.plannatech.com",
            grpc_url="grpc://grpc.plannatech.com:443",
            check_fixture_availability=True,
        )

        assert config.provider == "plannatech"
        assert str(config.url) == "https://api.plannatech.com/"
        assert config.grpc_url == "grpc://grpc.plannatech.com:443"
        assert config.check_fixture_availability is True

    def test_plannatech_config_invalid_url_raises_error(self):
        with pytest.raises(ValueError):
            PlannatechConfig(
                url="not-a-valid-url",
            )

    def test_plannatech_config_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            PlannatechConfig(
                url="https://api.plannatech.com",
                extra_field="not_allowed",
            )


class TestSportbookConfig:
    def test_create_sportbook_config(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sportbook = SportbookConfig(sportbook="Betsw3", config=config)

        assert sportbook.sportbook == "Betsw3"
        assert sportbook.config.provider == "betsw3"
        assert isinstance(sportbook.created_at, datetime)
        assert isinstance(sportbook.updated_at, datetime)
        assert len(sportbook.tournaments) > 0  # default tournaments

    def test_from_minimal_phoenix(self):
        sportbook = SportbookConfig.from_minimal_phoenix(
            cluster_api_key="key123",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="secret123",
            origin_id="origin123",
        )

        assert sportbook.sportbook == "Phoenix"
        assert sportbook.config.provider == "phoenix"
        assert sportbook.config.cluster_api_key == "key123"
        assert sportbook.config.basic_auth.username == ""  # default empty
        assert sportbook.config.basic_auth.password == ""  # default empty

    def test_from_minimal_phoenix_with_basic_auth(self):
        basic_auth = PhoenixBasicAuth(username="admin", password="secret")

        sportbook = SportbookConfig.from_minimal_phoenix(
            cluster_api_key="key123",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="secret123",
            origin_id="origin123",
            basic_auth=basic_auth,
        )

        assert sportbook.config.basic_auth.username == "admin"
        assert sportbook.config.basic_auth.password == "secret"

    def test_from_minimal_betsw3(self):
        sportbook = SportbookConfig.from_minimal_betsw3(
            userId="user123", siteId="site456", platformId="platform789"
        )

        assert sportbook.sportbook == "Betsw3"
        assert sportbook.config.provider == "betsw3"
        assert sportbook.config.userId == "user123"
        assert sportbook.config.language == "en"  # default
        assert sportbook.config.source == "web"  # default
        assert sportbook.config.currency == "USD"  # default

    def test_from_minimal_digitain(self):
        sportbook = SportbookConfig.from_minimal_digitain(
            "Custom Digitain",
            partner_id="partner123",
            client_id="client456",
            client_secret="secret789",
        )

        assert sportbook.sportbook == "Digitain"
        assert sportbook.config.provider == "digitain"
        assert sportbook.config.partner_id == "partner123"
        assert "placeholder.com" in str(sportbook.config.token_url)  # default

    def test_from_minimal_plannatech(self):
        sportbook = SportbookConfig.from_minimal_plannatech(
            url="https://api.plannatech.com",
        )

        assert sportbook.sportbook == "Plannatech"
        assert sportbook.config.provider == "plannatech"
        assert "plannatech.com" in str(sportbook.config.url)
        assert sportbook.config.grpc_url is None  # default
        assert sportbook.config.check_fixture_availability is False  # default

    def test_from_minimal_plannatech_with_all_params(self):
        sportbook = SportbookConfig.from_minimal_plannatech(
            url="https://api.plannatech.com",
            grpc_url="grpc://grpc.plannatech.com:443",
            check_fixture_availability=True,
        )

        assert sportbook.sportbook == "Plannatech"
        assert sportbook.config.provider == "plannatech"
        assert sportbook.config.grpc_url == "grpc://grpc.plannatech.com:443"
        assert sportbook.config.check_fixture_availability is True

    def test_from_minimal_isolutions(self):
        sportbook = SportbookConfig.from_minimal_isolutions(
            api_url="https://api-stg.bolabet.co.zm",
            api_account="ChatBet",
            api_password="secret123",
            events_program_code="mefvdituytybd",
        )

        assert sportbook.sportbook == "Isolutions"
        assert sportbook.config.provider == "isolutions"
        assert sportbook.config.api_account == "ChatBet"
        assert sportbook.config.bookmaker_id == 1  # default
        assert sportbook.config.language_id == 2  # default
        assert sportbook.config.fetch_interval_seconds == 60  # default

    def test_from_minimal_isolutions_with_all_params(self):
        sportbook = SportbookConfig.from_minimal_isolutions(
            api_url="https://api.bolabet.co.zm",
            api_account="TestAccount",
            api_password="TestPassword",
            bookmaker_id=5,
            events_program_code="custom_code",
            language_id=1,
            fetch_interval_seconds=30,
            check_fixture_availability=True,
        )

        assert sportbook.sportbook == "Isolutions"
        assert sportbook.config.provider == "isolutions"
        assert sportbook.config.bookmaker_id == 5
        assert sportbook.config.language_id == 1
        assert sportbook.config.fetch_interval_seconds == 30
        assert sportbook.config.check_fixture_availability is True

    def test_touch_method(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sportbook = SportbookConfig(sportbook="Betsw3", config=config)
        original_time = sportbook.updated_at

        sportbook.touch()
        assert sportbook.updated_at > original_time

    def test_to_dynamodb_item(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sportbook = SportbookConfig(sportbook="Betsw3", config=config)
        item = sportbook.to_dynamodb_item()

        assert isinstance(item, dict)
        assert "sportbook" in item
        assert "config" in item
        assert "tournaments" in item
        assert "created_at" in item
        assert "updated_at" in item

        # Check serialization
        assert isinstance(item["created_at"], str)  # datetime as ISO string
        assert isinstance(item["config"]["url"], str)  # HttpUrl as string
        assert item["config"]["provider"] == "betsw3"


class TestSportbookConfigDB:
    def test_create_sportbook_config_db(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sportbook_db = SportbookConfigDB(
            sportbook="Betsw3",
            config=config,
            PK="company#test123",
            SK="sportbook_config",
        )

        assert sportbook_db.PK == "company#test123"
        assert sportbook_db.SK == "sportbook_config"

    def test_from_minimal_phoenix_db(self):
        sportbook_db = SportbookConfigDB.from_minimal_phoenix(
            "test_company",
            cluster_api_key="key123",
            security_protocol="SASL_SSL",
            bootstrap_servers="server1",
            group_id="group1",
            mechanisms="PLAIN",
            cluster_api_secret="secret123",
            origin_id="origin123",
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.config.provider == "phoenix"

    def test_from_minimal_betsw3_db(self):
        sportbook_db = SportbookConfigDB.from_minimal_betsw3(
            "test_company", userId="user123", siteId="site456", platformId="platform789"
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.config.provider == "betsw3"

    def test_from_minimal_digitain_db(self):
        sportbook_db = SportbookConfigDB.from_minimal_digitain(
            "test_company",
            sportbook="Custom Digitain",
            partner_id="partner123",
            client_id="client456",
            client_secret="secret789",
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.config.provider == "digitain"

    def test_from_minimal_plannatech_db(self):
        sportbook_db = SportbookConfigDB.from_minimal_plannatech(
            "test_company",
            url="https://api.plannatech.com",
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.sportbook == "Plannatech"
        assert sportbook_db.config.provider == "plannatech"

    def test_from_minimal_plannatech_db_with_grpc(self):
        sportbook_db = SportbookConfigDB.from_minimal_plannatech(
            "test_company",
            url="https://api.plannatech.com",
            grpc_url="grpc://grpc.plannatech.com:443",
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.config.grpc_url == "grpc://grpc.plannatech.com:443"

    def test_from_minimal_isolutions_db(self):
        sportbook_db = SportbookConfigDB.from_minimal_isolutions(
            "test_company",
            api_url="https://api-stg.bolabet.co.zm",
            api_account="ChatBet",
            api_password="secret123",
            events_program_code="mefvdituytybd",
        )

        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"
        assert sportbook_db.sportbook == "Isolutions"
        assert sportbook_db.config.provider == "isolutions"
        assert sportbook_db.config.api_account == "ChatBet"

    def test_from_minimal_isolutions_db_to_dynamodb_item(self):
        sportbook_db = SportbookConfigDB.from_minimal_isolutions(
            "test_company",
            api_url="https://api-stg.bolabet.co.zm",
            api_account="ChatBet",
            api_password="secret123",
            events_program_code="mefvdituytybd",
            bookmaker_id=1,
            language_id=2,
        )

        item = sportbook_db.to_dynamodb_item()

        assert item["PK"] == "company#test_company"
        assert item["SK"] == "sportbook_config"
        assert item["sportbook"] == "Isolutions"
        assert item["config"]["provider"] == "isolutions"
        assert item["config"]["api_account"] == "ChatBet"
        assert item["config"]["bookmaker_id"] == 1
        assert item["config"]["language_id"] == 2
        assert isinstance(item["config"]["api_url"], str)

    def test_validation_requires_pk_sk(self):
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        with pytest.raises(ValueError, match="PK and SK are required"):
            SportbookConfigDB(sportbook="Betsw3", config=config)


class TestSportsS3Reference:
    def test_create_sports_s3_reference(self):
        """Test creating a sports S3 reference with all required fields."""
        ref = SportsS3Reference(
            bucket="my-bucket",
            key="company_id/sports_catalog.json",
            path="s3://my-bucket/company_id/sports_catalog.json"
        )

        assert ref.type == "s3_reference"
        assert ref.bucket == "my-bucket"
        assert ref.key == "company_id/sports_catalog.json"
        assert ref.path == "s3://my-bucket/company_id/sports_catalog.json"

    def test_sports_s3_reference_type_is_literal(self):
        """Test that type is automatically set to 's3_reference'."""
        ref = SportsS3Reference(
            bucket="test-bucket",
            key="test.json",
            path="s3://test-bucket/test.json"
        )

        assert ref.type == "s3_reference"

    def test_sports_s3_reference_missing_fields_raises_error(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValueError):
            SportsS3Reference(
                bucket="my-bucket",
                key="company_id/sports_catalog.json"
                # Missing path
            )

    def test_sports_s3_reference_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValueError):
            SportsS3Reference(
                bucket="my-bucket",
                key="company_id/sports_catalog.json",
                path="s3://my-bucket/company_id/sports_catalog.json",
                extra_field="not_allowed"
            )

    def test_sportbook_config_with_sports_s3_reference(self):
        """Test SportbookConfig with sports as S3 reference."""
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sports_ref = SportsS3Reference(
            bucket="my-bucket",
            key="test_company/sports_catalog.json",
            path="s3://my-bucket/test_company/sports_catalog.json"
        )

        sportbook = SportbookConfig(
            sportbook="Betsw3",
            config=config,
            sports=sports_ref
        )

        assert sportbook.sports is not None
        assert isinstance(sportbook.sports, SportsS3Reference)
        assert sportbook.sports.bucket == "my-bucket"
        assert sportbook.sports.key == "test_company/sports_catalog.json"

    def test_sportbook_config_sports_is_optional(self):
        """Test that sports field is optional (can be None)."""
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sportbook = SportbookConfig(sportbook="Betsw3", config=config)

        assert sportbook.sports is None

    def test_sportbook_config_db_with_sports_s3_reference(self):
        """Test SportbookConfigDB with sports as S3 reference."""
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sports_ref = SportsS3Reference(
            bucket="my-bucket",
            key="test_company/sports_catalog.json",
            path="s3://my-bucket/test_company/sports_catalog.json"
        )

        sportbook_db = SportbookConfigDB(
            sportbook="Betsw3",
            config=config,
            sports=sports_ref,
            PK="company#test_company",
            SK="sportbook_config"
        )

        assert sportbook_db.sports is not None
        assert sportbook_db.sports.type == "s3_reference"
        assert sportbook_db.PK == "company#test_company"
        assert sportbook_db.SK == "sportbook_config"

    def test_to_dynamodb_item_with_sports_s3_reference(self):
        """Test serialization to DynamoDB item includes S3 reference."""
        config = Betsw3Config(
            userId="user123",
            siteId="site456",
            platformId="platform789",
            language="en",
            source="web",
            currency="USD",
            access_token="token123",
            url="https://api.betsw3.com",
        )

        sports_ref = SportsS3Reference(
            bucket="my-bucket",
            key="test_company/sports_catalog.json",
            path="s3://my-bucket/test_company/sports_catalog.json"
        )

        sportbook = SportbookConfig(
            sportbook="Betsw3",
            config=config,
            sports=sports_ref
        )

        item = sportbook.to_dynamodb_item()

        assert "sports" in item
        assert item["sports"]["type"] == "s3_reference"
        assert item["sports"]["bucket"] == "my-bucket"
        assert item["sports"]["key"] == "test_company/sports_catalog.json"
        assert item["sports"]["path"] == "s3://my-bucket/test_company/sports_catalog.json"


class TestDefaultHelpers:
    def test_default_stake_types(self):
        stake_types = _default_stake_types()
        assert len(stake_types) == 2
        assert stake_types[0].name == "Result"
        assert stake_types[1].name == "Over/Under"

    def test_default_tournaments(self):
        tournaments = _default_tournaments()
        assert len(tournaments) == 1

        tournament = tournaments[0]
        assert tournament.sport_id == "soccer"
        assert tournament.sport_name == "soccer"
        assert tournament.main_market == "result"
        assert len(tournament.regions) == 1

        region = tournament.regions[0]
        assert region.id == "eu"
        assert region.name == "Europe"
        assert len(region.competitions) == 2

        competitions = region.competitions
        assert competitions[0].name == "UEFA Champions League"
        assert competitions[1].name == "Premier League"
