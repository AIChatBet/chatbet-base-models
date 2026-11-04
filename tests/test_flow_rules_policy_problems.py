from chatbet_base_models.flow_rules.defaults import DEFAULT_FLOW_POLICY, FLOW_CATALOG
from chatbet_base_models.flow_rules.policy import FlowPolicy, find_policy_problems


def _problems(**fields: object) -> list[str]:
    return find_policy_problems(FlowPolicy(**fields), FLOW_CATALOG)


def test_the_shipped_policy_has_no_problems() -> None:
    assert find_policy_problems(DEFAULT_FLOW_POLICY, FLOW_CATALOG) == []


def test_an_empty_policy_has_no_problems() -> None:
    assert find_policy_problems(FlowPolicy(), FLOW_CATALOG) == []


def test_a_required_step_the_catalog_does_not_know_is_reported() -> None:
    assert _problems(required_steps={"bet": ("confirm", "ghost")}) == [
        "required_steps['bet'] names 'ghost', which is not a step or capability in the catalog"
    ]


def test_a_journey_the_code_does_not_ship_may_still_require_known_steps() -> None:
    """A client's own journey (`combo`) is not in the code's seed flows; requiring a real step there is legitimate."""
    assert _problems(required_steps={"combo": ("confirm_combo",)}) == []


def test_a_capability_slot_may_be_required() -> None:
    assert _problems(required_steps={"balance": ("authenticate",)}) == []


def test_an_allowed_list_for_a_capability_the_catalog_does_not_have_is_reported() -> None:
    assert _problems(allowed_strategies={"teleport": ("x",)}) == [
        "allowed_strategies names 'teleport', which is not a capability in the catalog"
    ]


def test_an_empty_allowed_list_is_reported() -> None:
    assert _problems(allowed_strategies={"authenticate": ()}) == [
        "allowed_strategies['authenticate'] is empty: no client could use this capability"
    ]


def test_an_allowed_strategy_the_catalog_does_not_have_is_reported() -> None:
    assert _problems(allowed_strategies={"authenticate": ("auth.magic_link",)}) == [
        "allowed_strategies['authenticate'] names strategy 'auth.magic_link', which is not in the catalog"
    ]


def test_an_allowed_strategy_of_another_capability_is_reported() -> None:
    assert _problems(allowed_strategies={"authenticate": ("identify.by_phone",)}) == [
        "allowed_strategies['authenticate'] names 'identify.by_phone', which implements 'identify', not 'authenticate'"
    ]


def test_a_real_restriction_has_no_problems() -> None:
    assert _problems(allowed_strategies={"authenticate": ("auth.otp.platform",)}) == []


def test_a_default_flow_naming_an_unknown_step_or_repeating_one_is_reported() -> None:
    assert _problems(default_flows={"bet": ("understand", "ghost", "understand")}) == [
        "default_flows['bet'] repeats ['understand']",
        "default_flows['bet'] names 'ghost', which is not a step or capability in the catalog",
    ]


def test_a_default_binding_for_an_unknown_capability_is_reported() -> None:
    assert _problems(default_bindings={"teleport": "x"}) == [
        "default_bindings names 'teleport', which is not a capability in the catalog"
    ]


def test_a_default_binding_to_an_unknown_or_foreign_strategy_is_reported() -> None:
    assert _problems(default_bindings={"authenticate": "auth.magic_link"}) == [
        "default_bindings['authenticate'] names strategy 'auth.magic_link', which is not in the catalog"
    ]
    assert _problems(default_bindings={"authenticate": "identify.by_phone"}) == [
        "default_bindings['authenticate'] names 'identify.by_phone', which implements 'identify', not 'authenticate'"
    ]


def test_a_default_binding_the_policy_itself_forbids_is_reported() -> None:
    problems = _problems(
        allowed_strategies={"authenticate": ("auth.otp.platform",)},
        default_bindings={"authenticate": "auth.otp.twilio"},
    )

    assert problems == ["default_bindings['authenticate'] is 'auth.otp.twilio', which allowed_strategies does not allow"]


def test_every_problem_is_reported_together() -> None:
    problems = _problems(
        required_steps={"bet": ("ghost",)},
        allowed_strategies={"authenticate": ()},
        default_bindings={"teleport": "x"},
    )

    assert len(problems) == 3
