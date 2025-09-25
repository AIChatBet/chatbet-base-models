import pytest
from datetime import datetime

from chatbet_base_models.platform_endpoints import (
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


class TestHTTPMethod:
    def test_http_method_enum_values(self):
        assert HTTPMethod.GET == "GET"
        assert HTTPMethod.POST == "POST"
        assert HTTPMethod.PUT == "PUT"
        assert HTTPMethod.PATCH == "PATCH"
        assert HTTPMethod.DELETE == "DELETE"


class TestEndpoint:
    def test_create_endpoint_with_required_fields(self):
        endpoint = Endpoint(endpoint="https://api.example.com/test")
        assert str(endpoint.endpoint) == "https://api.example.com/test"
        assert endpoint.method is None
        assert endpoint.params is None
        assert endpoint.payload is None
        assert endpoint.headers is None

    def test_create_endpoint_with_all_fields(self):
        endpoint = Endpoint(
            method=HTTPMethod.POST,
            endpoint="https://api.example.com/test",
            params={"param1": "value1"},
            payload={"key": "value"},
            headers={"Authorization": "Bearer token"},
        )
        assert endpoint.method == HTTPMethod.POST
        assert str(endpoint.endpoint) == "https://api.example.com/test"
        assert endpoint.params == {"param1": "value1"}
        assert endpoint.payload == {"key": "value"}
        assert endpoint.headers == {"Authorization": "Bearer token"}

    def test_normalize_method_from_string(self):
        endpoint = Endpoint(method="post", endpoint="https://api.example.com/test")
        assert endpoint.method == HTTPMethod.POST

    def test_normalize_method_from_uppercase_string(self):
        endpoint = Endpoint(method="GET", endpoint="https://api.example.com/test")
        assert endpoint.method == HTTPMethod.GET

    def test_normalize_method_with_whitespace(self):
        endpoint = Endpoint(method="  PUT  ", endpoint="https://api.example.com/test")
        assert endpoint.method == HTTPMethod.PUT

    def test_invalid_method_raises_error(self):
        with pytest.raises(ValueError, match="Invalid HTTP method: INVALID"):
            Endpoint(method="INVALID", endpoint="https://api.example.com/test")

    def test_method_already_enum(self):
        endpoint = Endpoint(
            method=HTTPMethod.DELETE, endpoint="https://api.example.com/test"
        )
        assert endpoint.method == HTTPMethod.DELETE

    def test_invalid_url_raises_error(self):
        with pytest.raises(ValueError):
            Endpoint(endpoint="not-a-valid-url")

    def test_params_types(self):
        endpoint = Endpoint(
            endpoint="https://api.example.com/test",
            params={
                "string_param": "value",
                "bool_param": True,
                "int_param": 42,
                "float_param": 3.14,
            },
        )
        assert endpoint.params["string_param"] == "value"
        assert endpoint.params["bool_param"] is True
        assert endpoint.params["int_param"] == 42
        assert abs(endpoint.params["float_param"] - 3.14) < 0.001


class TestEndpointGroups:
    def test_auth_endpoints(self):
        auth = AuthEndpoints(
            validate_user=Endpoint(endpoint="https://api.example.com/auth/validate"),
            validate_token=Endpoint(endpoint="https://api.example.com/auth/token"),
        )
        assert auth.validate_user is not None
        assert auth.validate_token is not None
        assert auth.generate_token is None
        assert auth.generate_otp is None

    def test_users_endpoints(self):
        users = UsersEndpoints(
            get_user_balance=Endpoint(endpoint="https://api.example.com/users/balance")
        )
        assert users.get_user_balance is not None

    def test_sports_endpoints(self):
        sports = SportsEndpoints(
            get_available_sports=Endpoint(
                endpoint="https://api.example.com/sports/available"
            ),
            list_sports=Endpoint(endpoint="https://api.example.com/sports/list"),
        )
        assert sports.get_available_sports is not None
        assert sports.list_sports is not None

    def test_fixtures_endpoints(self):
        fixtures = FixturesEndpoints(
            get_fixtures_by_sport=Endpoint(
                endpoint="https://api.example.com/fixtures/sport"
            ),
            get_fixtures_by_tournament=Endpoint(
                endpoint="https://api.example.com/fixtures/tournament"
            ),
        )
        assert fixtures.get_fixtures_by_sport is not None
        assert fixtures.get_fixtures_by_tournament is not None
        assert fixtures.get_special_bets is None
        assert fixtures.get_recommended_bets is None

    def test_tournaments_endpoints(self):
        tournaments = TournamentsEndpoints(
            get_tournaments=Endpoint(endpoint="https://api.example.com/tournaments")
        )
        assert tournaments.get_tournaments is not None

    def test_odds_endpoints(self):
        odds = OddsEndpoints(
            get_fixture_odds=Endpoint(endpoint="https://api.example.com/odds/fixture"),
            get_odds_combo=Endpoint(endpoint="https://api.example.com/odds/combo"),
        )
        assert odds.get_fixture_odds is not None
        assert odds.get_odds_combo is not None

    def test_bets_endpoints(self):
        bets = BetsEndpoints(
            place_bet=Endpoint(endpoint="https://api.example.com/bets/place")
        )
        assert bets.place_bet is not None

    def test_combos_endpoints(self):
        combos = CombosEndpoints(
            place_combo=Endpoint(endpoint="https://api.example.com/combos/place"),
            get_combo_profit=Endpoint(endpoint="https://api.example.com/combos/profit"),
        )
        assert combos.place_combo is not None
        assert combos.get_combo_profit is not None
        assert combos.delete_bet_combo is None
        assert combos.add_bet_to_combo is None
        assert combos.get_odds_combo is None


class TestAPIEndpoints:
    def test_create_empty_api_endpoints(self):
        api = APIEndpoints()
        assert api.auth is None
        assert api.users is None
        assert api.sports is None
        assert api.tournaments is None
        assert api.fixtures is None
        assert api.odds is None
        assert api.bets is None
        assert api.combos is None

    def test_create_api_endpoints_with_groups(self):
        api = APIEndpoints(
            auth=AuthEndpoints(
                validate_user=Endpoint(endpoint="https://api.example.com/auth/validate")
            ),
            users=UsersEndpoints(
                get_user_balance=Endpoint(
                    endpoint="https://api.example.com/users/balance"
                )
            ),
        )
        assert api.auth is not None
        assert api.users is not None
        assert api.auth.validate_user is not None
        assert api.users.get_user_balance is not None


class TestAPIEndpointsDB:
    def test_create_api_endpoints_db(self):
        api_db = APIEndpointsDB(PK="company#123", SK="platform_endpoints")
        assert api_db.PK == "company#123"
        assert api_db.SK == "platform_endpoints"
        assert isinstance(api_db.created_at, datetime)
        assert isinstance(api_db.updated_at, datetime)

    def test_default_factory(self):
        api_db = APIEndpointsDB.default_factory("test_company")

        assert api_db.PK == "company#test_company"
        assert api_db.SK == "platform_endpoints"

        # Check that all endpoint groups are created
        assert api_db.auth is not None
        assert api_db.users is not None
        assert api_db.sports is not None
        assert api_db.tournaments is not None
        assert api_db.fixtures is not None
        assert api_db.odds is not None
        assert api_db.bets is not None
        assert api_db.combos is not None

        # Check some specific endpoints
        assert api_db.auth.validate_user is not None
        assert api_db.auth.validate_token is not None
        assert api_db.users.get_user_balance is not None
        assert api_db.sports.get_available_sports is not None
        assert api_db.sports.list_sports is not None

        # Verify placeholder URLs
        assert "placeholder.com" in str(api_db.auth.validate_user.endpoint)
        assert api_db.auth.validate_user.method == HTTPMethod.POST
        assert api_db.users.get_user_balance.method == HTTPMethod.GET

    def test_default_factory_complete_endpoints(self):
        api_db = APIEndpointsDB.default_factory("test_company")

        # Verify all auth endpoints
        assert api_db.auth.validate_user is not None
        assert api_db.auth.validate_token is not None
        assert api_db.auth.generate_token is not None

        # Verify fixtures endpoints
        assert api_db.fixtures.get_fixtures_by_sport is not None
        assert api_db.fixtures.get_fixtures_by_tournament is not None
        assert api_db.fixtures.get_special_bets is not None
        assert api_db.fixtures.get_recommended_bets is not None

        # Verify combos endpoints
        assert api_db.combos.place_combo is not None
        assert api_db.combos.get_combo_profit is not None
        assert api_db.combos.delete_bet_combo is not None
        assert api_db.combos.add_bet_to_combo is not None
        assert api_db.combos.get_odds_combo is not None

    def test_to_dynamodb_item(self):
        api_db = APIEndpointsDB.default_factory("test_company")
        item = api_db.to_dynamodb_item()

        assert isinstance(item, dict)
        assert "PK" in item
        assert "SK" in item
        assert "created_at" in item
        assert "updated_at" in item
        assert "auth" in item

        # Check that datetime objects are serialized as strings
        assert isinstance(item["created_at"], str)
        assert isinstance(item["updated_at"], str)

        # Check that HttpUrl objects are serialized as strings
        assert isinstance(item["auth"]["validate_user"]["endpoint"], str)

        # Check that enums are serialized as values
        assert item["auth"]["validate_user"]["method"] == "POST"

    def test_serialization_handles_all_types(self):
        # Create an endpoint with all possible data types
        endpoint = Endpoint(
            method=HTTPMethod.POST,
            endpoint="https://api.example.com/test",
            params={"string": "value", "number": 42, "boolean": True, "float": 3.14},
            payload={"key": "value"},
            headers={"Authorization": "Bearer token"},
        )

        api_db = APIEndpointsDB(
            PK="test", SK="test", auth=AuthEndpoints(validate_user=endpoint)
        )

        item = api_db.to_dynamodb_item()

        # Verify complex nested structures are properly serialized
        auth_endpoint = item["auth"]["validate_user"]
        assert auth_endpoint["method"] == "POST"
        assert auth_endpoint["params"]["string"] == "value"
        assert auth_endpoint["params"]["number"] == 42
        assert auth_endpoint["params"]["boolean"] is True
        assert abs(auth_endpoint["params"]["float"] - 3.14) < 0.001
        assert auth_endpoint["payload"]["key"] == "value"
