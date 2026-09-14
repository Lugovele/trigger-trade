"""Target backend test taxonomy for implementation traceability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Requirement(StrEnum):
    REQUIRED = "REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"
    LATER = "LATER"


@dataclass(frozen=True)
class TestLayer:
    name: str
    purpose: str
    major_areas: tuple[str, ...]
    introduced_in_wave: str


@dataclass(frozen=True)
class ImplementationTestObligation:
    implementation_id: str
    unit: Requirement
    contract: Requirement
    persistence: Requirement
    state_machine: Requirement
    replay: Requirement
    restart: Requirement
    concurrency: Requirement
    integration: Requirement
    e2e: Requirement

    def as_dict(self) -> dict[str, str]:
        return {
            "unit": self.unit.value,
            "contract": self.contract.value,
            "persistence": self.persistence.value,
            "state_machine": self.state_machine.value,
            "replay": self.replay.value,
            "restart": self.restart.value,
            "concurrency": self.concurrency.value,
            "integration": self.integration.value,
            "e2e": self.e2e.value,
        }


TARGET_TEST_LAYERS: tuple[TestLayer, ...] = (
    TestLayer("unit", "Validate owner-local deterministic functions", ("formulas", "gate predicates", "serialization", "identifier validation"), "Wave 1 - Contract Foundation"),
    TestLayer("contract", "Validate strict message/API schemas", ("business contracts", "API requests/responses", "unknown-field rejection"), "Wave 1 - Contract Foundation"),
    TestLayer("state_machine", "Validate lifecycle transitions", ("Portfolio health/holds", "Set epochs/monitors", "Position two-stage flow", "Lifecycle states"), "Wave 1 - Contract Foundation"),
    TestLayer("formula_golden_vectors", "Prove numeric behavior", ("TT_NUMERIC_V1", "TT_SET_NUMERIC_V1", "Entry/SL/TP/R:R/Net Edge"), "later formula-certified waves"),
    TestLayer("persistence", "Prove durability and hydration", ("pins", "facts", "current state", "checkpoints", "receipts", "tombstones"), "Wave 2 - Durable Persistence"),
    TestLayer("concurrency", "Prove atomic boundaries", ("grants", "holds", "close acquire/join", "child authority", "allocation receipts"), "Wave 2 - Durable Persistence"),
    TestLayer("replay", "Prove duplicate/reordered behavior", ("outbox/inbox dedupe", "delayed messages", "known-content challenges"), "Wave 2 - Durable Persistence"),
    TestLayer("restart", "Prove crash cutpoints", ("before/after commits", "ambiguous dispatch", "resumed reconciliation"), "Wave 2 - Durable Persistence"),
    TestLayer("reconciliation", "Prove source/evidence handling", ("native observations", "protection proof", "financial coverage", "post-final incidents"), "Wave 6 - Lifecycle Core"),
    TestLayer("integration", "Prove components together", ("full contract edges", "persisted worker flows"), "later implementation waves"),
    TestLayer("exchange_adapter", "Prove factual/native profile conformance", ("Bybit mappings", "pagination", "chronology", "acceptance", "hard facts"), "later implementation waves"),
    TestLayer("research_backtest", "Prove isolated deterministic runs", ("version pins", "historical selectors", "metrics", "no live side effects"), "Wave 7 - Research Alignment"),
    TestLayer("end_to_end", "Prove material flows", ("paper/demo/live-disabled submission", "cancel", "close", "final accounting"), "later implementation waves"),
)

WAVE1_IMPLEMENTATION_IDS: tuple[str, ...] = (
    "TT-BE-INFRA-008",
    "TT-BE-SYS-004",
    "TT-BE-SYS-001",
    "TT-BE-SYS-006",
    "TT-BE-SYS-011",
    "TT-BE-SYS-008",
    "TT-BE-SYS-010",
)

IMPLEMENTATION_TEST_OBLIGATIONS = MappingProxyType(
    {
        "TT-BE-INFRA-008": ImplementationTestObligation(
            "TT-BE-INFRA-008",
            unit=Requirement.NOT_REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.NOT_REQUIRED,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.NOT_REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.NOT_REQUIRED,
            e2e=Requirement.NOT_REQUIRED,
        ),
        "TT-BE-SYS-001": ImplementationTestObligation(
            "TT-BE-SYS-001",
            unit=Requirement.REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.LATER,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.NOT_REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.NOT_REQUIRED,
            e2e=Requirement.NOT_REQUIRED,
        ),
        "TT-BE-SYS-004": ImplementationTestObligation(
            "TT-BE-SYS-004",
            unit=Requirement.REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.LATER,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.NOT_REQUIRED,
            e2e=Requirement.NOT_REQUIRED,
        ),
        "TT-BE-SYS-006": ImplementationTestObligation(
            "TT-BE-SYS-006",
            unit=Requirement.REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.NOT_REQUIRED,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.NOT_REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.NOT_REQUIRED,
            e2e=Requirement.LATER,
        ),
        "TT-BE-SYS-008": ImplementationTestObligation(
            "TT-BE-SYS-008",
            unit=Requirement.REQUIRED,
            contract=Requirement.NOT_REQUIRED,
            persistence=Requirement.NOT_REQUIRED,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.NOT_REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.LATER,
            e2e=Requirement.NOT_REQUIRED,
        ),
        "TT-BE-SYS-010": ImplementationTestObligation(
            "TT-BE-SYS-010",
            unit=Requirement.REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.REQUIRED,
            state_machine=Requirement.REQUIRED,
            replay=Requirement.REQUIRED,
            restart=Requirement.REQUIRED,
            concurrency=Requirement.REQUIRED,
            integration=Requirement.REQUIRED,
            e2e=Requirement.REQUIRED,
        ),
        "TT-BE-SYS-011": ImplementationTestObligation(
            "TT-BE-SYS-011",
            unit=Requirement.REQUIRED,
            contract=Requirement.REQUIRED,
            persistence=Requirement.NOT_REQUIRED,
            state_machine=Requirement.NOT_REQUIRED,
            replay=Requirement.NOT_REQUIRED,
            restart=Requirement.NOT_REQUIRED,
            concurrency=Requirement.NOT_REQUIRED,
            integration=Requirement.NOT_REQUIRED,
            e2e=Requirement.LATER,
        ),
    }
)

DEFERRED_TT_BE_SYS_010_EXPANSION: tuple[str, ...] = (
    "formula-specific golden vectors wait for formula certification",
    "durable persistence, restart, replay, and concurrency suites expand after PostgreSQL foundation",
    "integration, exchange-adapter, research/backtest, and end-to-end suites expand in their owning waves",
)


def target_test_layer_names() -> tuple[str, ...]:
    return tuple(layer.name for layer in TARGET_TEST_LAYERS)


def wave1_obligations() -> dict[str, dict[str, str]]:
    return {implementation_id: IMPLEMENTATION_TEST_OBLIGATIONS[implementation_id].as_dict() for implementation_id in WAVE1_IMPLEMENTATION_IDS}
