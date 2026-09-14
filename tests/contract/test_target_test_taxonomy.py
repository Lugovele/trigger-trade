from triggertrade.test_taxonomy import (
    DEFERRED_TT_BE_SYS_010_EXPANSION,
    IMPLEMENTATION_TEST_OBLIGATIONS,
    Requirement,
    TARGET_TEST_LAYERS,
    WAVE1_IMPLEMENTATION_IDS,
    target_test_layer_names,
    wave1_obligations,
)


def test_target_testing_model_layers_are_scaffolded_in_order():
    assert target_test_layer_names() == (
        "unit",
        "contract",
        "state_machine",
        "formula_golden_vectors",
        "persistence",
        "concurrency",
        "replay",
        "restart",
        "reconciliation",
        "integration",
        "exchange_adapter",
        "research_backtest",
        "end_to_end",
    )
    assert TARGET_TEST_LAYERS[0].purpose == "Validate owner-local deterministic functions"
    assert TARGET_TEST_LAYERS[1].purpose == "Validate strict message/API schemas"


def test_wave1_implementation_ids_are_all_present_in_test_taxonomy():
    assert WAVE1_IMPLEMENTATION_IDS == (
        "TT-BE-INFRA-008",
        "TT-BE-SYS-004",
        "TT-BE-SYS-001",
        "TT-BE-SYS-006",
        "TT-BE-SYS-011",
        "TT-BE-SYS-008",
        "TT-BE-SYS-010",
    )
    assert set(wave1_obligations()) == set(WAVE1_IMPLEMENTATION_IDS)


def test_wave1_obligations_match_traceability_for_completed_foundation_tasks():
    obligations = wave1_obligations()

    assert obligations["TT-BE-INFRA-008"] == {
        "unit": "NOT_REQUIRED",
        "contract": "REQUIRED",
        "persistence": "NOT_REQUIRED",
        "state_machine": "NOT_REQUIRED",
        "replay": "NOT_REQUIRED",
        "restart": "NOT_REQUIRED",
        "concurrency": "NOT_REQUIRED",
        "integration": "NOT_REQUIRED",
        "e2e": "NOT_REQUIRED",
    }
    assert obligations["TT-BE-SYS-001"]["unit"] == "REQUIRED"
    assert obligations["TT-BE-SYS-001"]["contract"] == "REQUIRED"
    assert obligations["TT-BE-SYS-004"]["replay"] == "REQUIRED"
    assert obligations["TT-BE-SYS-006"]["contract"] == "REQUIRED"
    assert obligations["TT-BE-SYS-008"]["unit"] == "REQUIRED"
    assert obligations["TT-BE-SYS-011"]["contract"] == "REQUIRED"


def test_tt_be_sys_010_records_full_target_test_categories_without_implementing_later_layers():
    obligation = IMPLEMENTATION_TEST_OBLIGATIONS["TT-BE-SYS-010"]

    assert all(value is Requirement.REQUIRED for value in obligation.__dict__.values() if isinstance(value, Requirement))
    assert DEFERRED_TT_BE_SYS_010_EXPANSION == (
        "formula-specific golden vectors wait for formula certification",
        "durable persistence, restart, replay, and concurrency suites expand after PostgreSQL foundation",
        "integration, exchange-adapter, research/backtest, and end-to-end suites expand in their owning waves",
    )
