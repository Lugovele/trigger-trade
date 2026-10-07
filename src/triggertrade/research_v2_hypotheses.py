"""Research V2 hypothesis bridge primitives for immutable batch jobs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import copy
import json
import subprocess
from typing import Any, Mapping

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.research_v2 import (
    RESEARCH_V2_SPEC_DIR,
    ResearchV2JobConfig,
    build_research_v2_execution_profile,
    load_common_profile,
    load_research_v2_jobs,
)


RV2_HB001_BATCH_ID = "RV2-HB001"
RV2_HB001_MANIFEST_PATH = RESEARCH_V2_SPEC_DIR / "hypotheses" / "RV2_HB001.json"
RESOLVED_RESEARCH_SPEC_SCHEMA = "research-v2-resolved-research-spec@1"


class ResearchV2HypothesisError(ValueError):
    pass


@dataclass(frozen=True)
class ResearchV2HypothesisSpec:
    batch_id: str
    hypothesis_id: str
    parent_job_id: str
    parent_hypothesis_id: str | None
    research_direction: str
    direction_mode: str
    signal_family: str
    stop_family: str
    parameters: Mapping[str, Any]
    metadata: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ResearchV2HypothesisSpec":
        return cls(
            batch_id=_required_text(payload, "batch_id"),
            hypothesis_id=_required_text(payload, "hypothesis_id"),
            parent_job_id=_required_text(payload, "parent_job_id"),
            parent_hypothesis_id=_optional_text(payload.get("parent_hypothesis_id")),
            research_direction=_required_text(payload, "research_direction"),
            direction_mode=_required_text(payload, "direction_mode"),
            signal_family=_required_text(payload, "signal_family"),
            stop_family=_required_text(payload, "stop_family"),
            parameters=dict(payload.get("parameters") or {}),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "hypothesis_id": self.hypothesis_id,
            "parent_job_id": self.parent_job_id,
            "parent_hypothesis_id": self.parent_hypothesis_id,
            "research_direction": self.research_direction,
            "direction_mode": self.direction_mode,
            "signal_family": self.signal_family,
            "stop_family": self.stop_family,
            "parameters": _canonicalize(self.parameters),
            "metadata": _canonicalize(self.metadata),
        }

    @property
    def fingerprint(self) -> str:
        return canonical_json_digest({"research_v2_hypothesis_spec": self.to_payload()})


@dataclass(frozen=True)
class ResearchV2HypothesisJob:
    spec: ResearchV2HypothesisSpec
    parent_job: ResearchV2JobConfig
    runtime_profile: Mapping[str, Any]
    code_commit: str | None = None

    @property
    def job_id(self) -> str:
        return self.spec.hypothesis_id

    @property
    def parent_job_id(self) -> str:
        return self.spec.parent_job_id

    @property
    def parent_hypothesis_id(self) -> str | None:
        return self.spec.parent_hypothesis_id

    @property
    def dependencies(self) -> tuple[str, ...]:
        return (self.spec.parent_job_id,)

    @property
    def signal_family(self) -> str:
        return self.spec.signal_family

    @property
    def entry_profile(self) -> str:
        return self.parent_job.entry_profile

    @property
    def stop_family(self) -> str:
        return self.spec.stop_family

    @property
    def sizing_profile(self) -> str:
        return self.parent_job.sizing_profile

    @property
    def leverage(self) -> Decimal:
        return self.parent_job.leverage

    @property
    def margin_fraction(self) -> Decimal:
        return self.parent_job.margin_fraction

    @property
    def symbols(self) -> tuple[str, ...]:
        return self.parent_job.symbols

    @property
    def window_start(self) -> str:
        return self.parent_job.window_start

    @property
    def window_end(self) -> str:
        return self.parent_job.window_end

    @property
    def source(self) -> Mapping[str, Any]:
        return {"hypothesis": self.spec.to_payload(), "parent": self.parent_job.normalized_config()}

    def normalized_config(self) -> dict[str, Any]:
        return {
            "program_id": "RESEARCH_V2_HYPOTHESIS_BRIDGE",
            "batch_id": self.spec.batch_id,
            "hypothesis_id": self.spec.hypothesis_id,
            "parent_job_id": self.spec.parent_job_id,
            "parent_hypothesis_id": self.spec.parent_hypothesis_id,
            "research_direction": self.spec.research_direction,
            "hypothesis_fingerprint": self.spec.fingerprint,
            "code_commit": self.code_commit,
            "parent_job_config_fingerprint": self.parent_job.config_fingerprint,
            "runtime_profile": _canonicalize(self.runtime_profile),
            "symbols": list(self.symbols),
            "window": {"start_inclusive": self.window_start, "end_exclusive": self.window_end},
        }

    @property
    def config_fingerprint(self) -> str:
        return canonical_json_digest(self.normalized_config())

    @property
    def signal_config(self) -> dict[str, Any]:
        return {
            "program_id": "RESEARCH_V2_HYPOTHESIS_BRIDGE",
            "contract": "RESEARCH_V2_HYPOTHESIS_SET_V1",
            "batch_id": self.spec.batch_id,
            "hypothesis_id": self.spec.hypothesis_id,
            "hypothesis_fingerprint": self.spec.fingerprint,
            "parent_job_id": self.spec.parent_job_id,
            "signal": _canonicalize(self.runtime_profile["signal"]),
            "symbols": list(self.symbols),
            "window": {"start_inclusive": self.window_start, "end_exclusive": self.window_end},
        }

    @property
    def signal_config_fingerprint(self) -> str:
        return canonical_json_digest(self.signal_config)

    def identity_payload(self, *, dataset_fingerprint: str | None = None, population_fingerprint: str | None = None) -> dict[str, Any]:
        return {
            "batch_id": self.spec.batch_id,
            "hypothesis_id": self.spec.hypothesis_id,
            "parent_job_id": self.spec.parent_job_id,
            "parent_hypothesis_id": self.spec.parent_hypothesis_id,
            "research_direction": self.spec.research_direction,
            "resolved_config": self.normalized_config(),
            "strategy_fingerprint": self.signal_config_fingerprint,
            "execution_profile_fingerprint": None,
            "dataset_fingerprint": dataset_fingerprint,
            "code_commit": self.code_commit,
            "window": {"start_inclusive": self.window_start, "end_exclusive": self.window_end},
            "warmup": self.runtime_profile.get("warmup_days"),
            "population_fingerprint": population_fingerprint,
        }


def build_resolved_research_spec(
    job: ResearchV2HypothesisJob,
    *,
    dataset_manifest: str | None = None,
    dataset_fingerprint: str | None = None,
    population_fingerprint: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Return the canonical resolved research passport for one hypothesis.

    This is a representation/evidence layer only. It reads the resolved
    Research V2 job/profile state and does not form candidates or replay
    execution.
    """

    execution_profile = build_research_v2_execution_profile(job)
    signal = dict(job.runtime_profile["signal"])
    profile = job.runtime_profile
    return _canonicalize(
        {
            "schema": RESOLVED_RESEARCH_SPEC_SCHEMA,
            "research": _research_section(
                job,
                dataset_manifest=dataset_manifest,
                dataset_fingerprint=dataset_fingerprint,
                population_fingerprint=population_fingerprint,
                execution_profile_fingerprint=execution_profile.config_fingerprint,
                output_path=output_path,
            ),
            "set": _set_section(job, signal),
            "triggers": _trigger_rows(job, signal),
            "position_rules": _position_rules_section(job, execution_profile),
            "portfolio_rules": _portfolio_rules_section(job, profile),
            "delta_from_parent": _delta_from_parent(job),
            "validation": {
                "hidden_material_settings_found": 0,
                "resolved_spec_mismatches": [],
                "material_setting_sections": [
                    "triggers",
                    "set",
                    "position_rules",
                    "portfolio_rules",
                    "research",
                ],
            },
            "source_refs": [
                "docs/research-v2/hypotheses/RV2_HB001.json",
                "docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json",
                "docs/research-v2/jobs/INITIAL_7D_JOBS.json",
                "src/triggertrade/research_v2_hypotheses.py",
                "src/triggertrade/research_v2.py",
                "src/triggertrade/research_v2_execution.py",
                "tools/research_v2/run_7d_screen.py",
            ],
        }
    )


def _research_section(
    job: ResearchV2HypothesisJob,
    *,
    dataset_manifest: str | None,
    dataset_fingerprint: str | None,
    population_fingerprint: str | None,
    execution_profile_fingerprint: str,
    output_path: str | None,
) -> dict[str, Any]:
    population_status = None if population_fingerprint is not None else "AVAILABLE_AFTER_POPULATION_MATERIALIZATION"
    return {
        "batch_id": job.spec.batch_id,
        "hypothesis_id": job.spec.hypothesis_id,
        "parent_job_id": job.spec.parent_job_id,
        "parent_hypothesis_id": job.spec.parent_hypothesis_id,
        "research_direction": job.spec.research_direction,
        "dataset_manifest": dataset_manifest,
        "dataset_manifest_status": "PROVIDED" if dataset_manifest else "NOT_PROVIDED_FOR_RESOLVE_ONLY",
        "dataset_fingerprint": dataset_fingerprint,
        "dataset_fingerprint_status": "PROVIDED" if dataset_fingerprint else "UNAVAILABLE_WITHOUT_DATASET_MANIFEST",
        "window": {"start_inclusive": job.window_start, "end_exclusive": job.window_end},
        "warmup_days": job.runtime_profile.get("warmup_days"),
        "code_commit": job.code_commit,
        "hypothesis_fingerprint": job.spec.fingerprint,
        "resolved_config_fingerprint": job.config_fingerprint,
        "strategy_fingerprint": job.signal_config_fingerprint,
        "execution_profile_fingerprint": execution_profile_fingerprint,
        "population_fingerprint": population_fingerprint,
        "population_fingerprint_status": population_status,
        "independent_account_key": f"{job.spec.batch_id}:{job.spec.hypothesis_id}:{execution_profile_fingerprint}",
        "output_path": output_path,
        "source_refs": ["ResearchV2HypothesisJob.identity_payload", "tools/research_v2/run_7d_screen._portfolio_book_key"],
    }


def _set_section(job: ResearchV2HypothesisJob, signal: Mapping[str, Any]) -> dict[str, Any]:
    family = str(signal["family"])
    return {
        "set_config_id": f"RESEARCH-V2-{family}",
        "set_config_version": str(signal.get("version", "LEGACY-SET")),
        "parent_set_or_job": job.parent_job_id,
        "signal_family": family,
        "direction_resolution": "GENERIC_FIXED",
        "boolean_composition": _boolean_composition(family),
        "timeframe_inputs": _timeframe_inputs(family),
        "set_fingerprint_inputs": {
            "batch_id": job.spec.batch_id,
            "hypothesis_id": job.spec.hypothesis_id,
            "hypothesis_fingerprint": job.spec.fingerprint,
            "signal": _canonicalize(signal),
            "symbols": list(job.symbols),
            "window": {"start_inclusive": job.window_start, "end_exclusive": job.window_end},
        },
        "implementation_notes": [
            "Research V2 resolves this through the generic Set result contract at runtime.",
            "direction_mode is displayed under position_rules and applied before account admission.",
        ],
        "source_refs": ["triggertrade.research_v2.resolve_research_v2_set_resolution", "triggertrade.research_v2._research_v2_set_result_request"],
    }


def _trigger_rows(job: ResearchV2HypothesisJob, signal: Mapping[str, Any]) -> list[dict[str, Any]]:
    family = str(signal["family"])
    if family == "MOMENTUM_CONTINUATION":
        rows = _continuation_trigger_rows(origin="INHERITED")
        if signal.get("g0_eligibility_only"):
            rows.append(_g0_eligibility_row())
        return rows
    if family == "RET_OR_TREND_ONLY":
        return _ret_or_rows(origin="INHERITED") + _trend_rows(origin="HYPOTHESIS_OVERRIDE")
    if family == "RET_OR_RVOL_ONLY":
        return _ret_or_rows(origin="INHERITED") + [_rvol_row(value=str(signal.get("rvol5_min", "1.2")), origin="HYPOTHESIS_OVERRIDE")]
    if family == "MOMENTUM_CONTINUATION_SHORT_DE":
        return _continuation_trigger_rows(origin="INHERITED") + [
            {
                "name": "SHORT_DIRECTIONAL_EFFICIENCY",
                "type": "SCALAR_PREDICATE",
                "metric": "directional_efficiency_5m",
                "operator": "GTE",
                "value": str(signal.get("short_directional_efficiency_min", "0.30")),
                "direction_scope": "SHORT",
                "origin": "HYPOTHESIS_OVERRIDE",
                "composition_group": "SHORT_DE_GATE",
                "timeframe": "5m",
                "completed_close_count": 9,
                "source": "tools.research_v2.run_7d_screen._directional_efficiency5_from_timeline",
            }
        ]
    if family == "MOMENTUM_CONTINUATION_TURNOVER":
        return _continuation_trigger_rows(origin="INHERITED") + [
            {
                "name": "TURNOVER_ACCELERATION",
                "type": "SCALAR_PREDICATE",
                "metric": "turnover_acceleration",
                "operator": "GTE",
                "value": str(signal.get("turnover_acceleration_min", "1.2")),
                "direction_scope": "BOTH",
                "origin": "HYPOTHESIS_OVERRIDE",
                "composition_group": "TURNOVER_GATE",
                "source": "tools.research_v2.run_7d_screen._evaluate_job_signal_from_timeline",
            }
        ]
    if family == "COMPRESSION_BREAKOUT":
        return _compression_rows(signal)
    if family == "EXHAUSTION_REVERSAL":
        return _reversal_rows()
    return []


def _ret_or_rows(*, origin: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "RET_OR_LONG",
            "type": "COMPOSITE_OR",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "LONG",
            "origin": origin,
            "composition_group": "RET_OR",
            "conditions": [
                {"metric": "return5_pct_points", "operator": "GTE", "value": "0.30"},
                {"metric": "return15_pct_points", "operator": "GTE", "value": "0.50"},
            ],
            "source": "triggertrade.research_v2.ret5_ret15_or_signal",
        },
        {
            "name": "RET_OR_SHORT",
            "type": "COMPOSITE_OR",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "SHORT",
            "origin": origin,
            "composition_group": "RET_OR",
            "conditions": [
                {"metric": "return5_pct_points", "operator": "LTE", "value": "-0.30"},
                {"metric": "return15_pct_points", "operator": "LTE", "value": "-0.50"},
            ],
            "source": "triggertrade.research_v2.ret5_ret15_or_signal",
        },
    ]


def _trend_rows(*, origin: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "J4_LONG_TREND",
            "type": "COMPOSITE_AND",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "LONG",
            "origin": origin,
            "composition_group": "TREND_GATE",
            "conditions": [
                {"metric": "EMA20_15m", "operator": "GT", "value_ref": "EMA50_15m"},
                {"metric": "return15_pct_points", "operator": "GT", "value": "0"},
            ],
            "source": "triggertrade.research_v2.continuation_signal",
        },
        {
            "name": "J4_SHORT_TREND",
            "type": "COMPOSITE_AND",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "SHORT",
            "origin": origin,
            "composition_group": "TREND_GATE",
            "conditions": [
                {"metric": "EMA20_15m", "operator": "LT", "value_ref": "EMA50_15m"},
                {"metric": "return15_pct_points", "operator": "LT", "value": "0"},
            ],
            "source": "triggertrade.research_v2.continuation_signal",
        },
    ]


def _rvol_row(*, value: str, origin: str) -> dict[str, Any]:
    return {
        "name": "RVOL5_MIN",
        "type": "SCALAR_PREDICATE",
        "metric": "RVOL5",
        "operator": "GTE",
        "value": value,
        "direction_scope": "BOTH",
        "origin": origin,
        "composition_group": "RVOL_GATE",
        "source": "triggertrade.research_v2.continuation_signal",
    }


def _continuation_trigger_rows(*, origin: str) -> list[dict[str, Any]]:
    return _ret_or_rows(origin=origin) + [_rvol_row(value="1.2", origin=origin)] + _trend_rows(origin=origin)


def _compression_rows(signal: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": "COMPRESSION_ATR15_MEDIAN96",
            "type": "SCALAR_PREDICATE",
            "metric": "ATR15 / median96_ATR15",
            "operator": "LTE",
            "value": str(signal.get("compression_ratio_max", "0.80")),
            "direction_scope": "BOTH",
            "origin": "HYPOTHESIS_OVERRIDE" if str(signal.get("compression_ratio_max", "0.80")) != "0.80" else "INHERITED",
            "composition_group": "COMPRESSION_GATE",
            "source": "triggertrade.research_v2.compression_breakout_signal",
        },
        {
            "name": "COMPRESSION_RVOL5",
            "type": "SCALAR_PREDICATE",
            "metric": "RVOL5",
            "operator": "GTE",
            "value": str(signal.get("rvol5_min", "1.5")),
            "direction_scope": "BOTH",
            "origin": "INHERITED",
            "composition_group": "RVOL_GATE",
            "source": "triggertrade.research_v2.compression_breakout_signal",
        },
        {
            "name": "COMPRESSION_TURNOVER_ACCELERATION",
            "type": "SCALAR_PREDICATE",
            "metric": "turnover_acceleration",
            "operator": "GTE",
            "value": str(signal.get("turnover_acceleration_min", "1.2")),
            "direction_scope": "BOTH",
            "origin": "INHERITED",
            "composition_group": "TURNOVER_GATE",
            "source": "triggertrade.research_v2.compression_breakout_signal",
        },
        {
            "name": "COMPRESSION_BREAKOUT_BUFFER",
            "type": "COMPOSITE_OR",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "BOTH",
            "origin": "INHERITED",
            "composition_group": "BREAKOUT_GATE",
            "conditions": [
                {"direction_scope": "LONG", "metric": "close", "operator": "GT", "value_ref": "prior_12x5m_high + 0.10*ATR15"},
                {"direction_scope": "SHORT", "metric": "close", "operator": "LT", "value_ref": "prior_12x5m_low - 0.10*ATR15"},
            ],
            "source": "triggertrade.research_v2.compression_breakout_signal",
        },
    ]


def _reversal_rows() -> list[dict[str, Any]]:
    return [
        {
            "name": "EXHAUSTION_REVERSAL_SHORT",
            "type": "COMPOSITE_AND",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "SHORT",
            "origin": "INHERITED",
            "composition_group": "REVERSAL_SIGNAL",
            "conditions": [
                {"metric": "return15_pct_points", "operator": "GTE", "value": "1.0"},
                {"metric": "latest_close", "operator": "LTE", "value_ref": "high_15m - 0.5*ATR15"},
                {"metric": "last_two_closes", "operator": "EQ", "value": "falling"},
                {"metric": "turnover_acceleration", "operator": "LTE", "value": "1.0"},
            ],
            "source": "triggertrade.research_v2.reversal_signal",
        },
        {
            "name": "EXHAUSTION_REVERSAL_LONG",
            "type": "COMPOSITE_AND",
            "metric": None,
            "operator": None,
            "value": None,
            "direction_scope": "LONG",
            "origin": "INHERITED",
            "composition_group": "REVERSAL_SIGNAL",
            "conditions": [
                {"metric": "return15_pct_points", "operator": "LTE", "value": "-1.0"},
                {"metric": "latest_close", "operator": "GTE", "value_ref": "low_15m + 0.5*ATR15"},
                {"metric": "last_two_closes", "operator": "EQ", "value": "rising"},
                {"metric": "turnover_acceleration", "operator": "LTE", "value": "1.0"},
            ],
            "source": "triggertrade.research_v2.reversal_signal",
        },
    ]


def _g0_eligibility_row() -> dict[str, Any]:
    return {
        "name": "G0_STRUCTURAL_ELIGIBILITY",
        "type": "COMPOSITE_ELIGIBILITY",
        "metric": "G0 structural reference geometry",
        "operator": "PASS",
        "value": "canonical G0 geometry",
        "direction_scope": "LONG",
        "origin": "HYPOTHESIS_OVERRIDE",
        "composition_group": "ENTRY_ELIGIBILITY",
        "role": "ENTRY_ELIGIBILITY_ONLY",
        "conditions": [
            {"metric": "structural_reference_price", "operator": "EQ", "value": "available and protective"},
            {"metric": "G0 stop distance", "operator": "GTE", "value_ref": "max(0.5*ATR15, 0.0025*entry)"},
            {"metric": "G0 stop distance", "operator": "LTE", "value_ref": "min(1.5*ATR15, 0.0125*entry)"},
        ],
        "source": "triggertrade.research_v2_execution.evaluate_research_v2_g0_structural_eligibility",
    }


def _position_rules_section(job: ResearchV2HypothesisJob, execution_profile: Any) -> dict[str, Any]:
    signal = job.runtime_profile["signal"]
    direction_mode = str(signal.get("direction_mode", "LONG_SHORT"))
    stop_origin = "HYPOTHESIS_OVERRIDE" if job.stop_family != job.parent_job.stop_family else "PARENT_JOB"
    parent_direction_mode = str(job.parent_job.runtime_profile.get("signal", {}).get("direction_mode", "LONG_SHORT"))
    direction_origin = "HYPOTHESIS_OVERRIDE" if "direction_mode" in signal else "PARENT_JOB"
    return {
        "direction_mode": {
            "value": direction_mode,
            "origin": direction_origin,
            "changed_by_hypothesis": direction_mode != parent_direction_mode,
            "runtime_application_stage": "PRE_ADMISSION_SIGNAL_FILTER",
            "source_refs": ["tools.research_v2.run_7d_screen._apply_direction_mode"],
        },
        "entry": {
            "type": {"value": "LIMIT_POST_ONLY", "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "post_only": {"value": True, "origin": "HARDCODED_FROZEN", "changed_by_hypothesis": False},
            "pullback_atr15": {"value": str(execution_profile.entry_profile.get("pullback_ATR15")), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "ttl_minutes": {"value": execution_profile.entry_profile.get("TTL_minutes"), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "chase": {"value": False, "origin": "HARDCODED_FROZEN", "changed_by_hypothesis": False},
            "reprice": {"value": False, "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "market_fallback": {"value": False, "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "source_refs": ["docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json", "triggertrade.research_v2_execution.construct_research_v2_order_spec"],
        },
        "stop": {
            "family": {"value": job.stop_family, "origin": stop_origin, "changed_by_hypothesis": job.stop_family != job.parent_job.stop_family},
            "type": {"value": execution_profile.stop_profile.get("type"), "origin": stop_origin, "changed_by_hypothesis": job.stop_family != job.parent_job.stop_family},
            "parameters": _canonicalize(dict(execution_profile.stop_profile)),
            "source_refs": ["docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json", "triggertrade.research_v2_execution._stop_price"],
        },
        "take_profit": {
            "mode": {"value": execution_profile.take_profit_profile.get("type"), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "gross_r": {"value": str(execution_profile.take_profit_profile.get("gross_R")), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "scope": {"value": "FULL_POSITION", "origin": "HARDCODED_FROZEN", "changed_by_hypothesis": False},
            "partial_profit_taking": {"value": execution_profile.take_profit_profile.get("partial_profit_taking"), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "net_tp_fraction_of_notional_min": {"value": str(execution_profile.take_profit_profile.get("net_TP_fraction_of_notional_min")), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
            "source_refs": ["docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json", "triggertrade.research_v2_execution._tp_price"],
        },
        "leverage": {"value": str(job.leverage), "origin": "PARENT_JOB", "changed_by_hypothesis": False},
        "cooldown_minutes": {
            "value": execution_profile.sizing_profile.get("cooldown_minutes", 15),
            "origin": "COMMON_PROFILE",
            "changed_by_hypothesis": False,
            "source_refs": ["tools.research_v2.run_7d_screen._profile_cooldown_minutes"],
        },
    }


def _portfolio_rules_section(job: ResearchV2HypothesisJob, profile: Mapping[str, Any]) -> dict[str, Any]:
    sizing = dict(profile["sizing"])
    return {
        "capital_usdt": {"value": "1000", "origin": "FROZEN_CODE", "changed_by_hypothesis": False},
        "compounding": {"value": False, "origin": "COMMON_PROFILE", "changed_by_hypothesis": False},
        "nominal_margin_fraction": _portfolio_value(sizing, "nominal_margin_fraction"),
        "total_margin_fraction_max": _portfolio_value(sizing, "total_margin_fraction_max"),
        "per_coin_margin_fraction_cap": _portfolio_value(sizing, "per_coin_margin_fraction_cap"),
        "gross_notional_fraction_max": _portfolio_value(sizing, "gross_notional_fraction_max"),
        "risk_per_trade_fraction_max": _portfolio_value(sizing, "risk_per_trade_fraction_max"),
        "portfolio_open_and_pending_stop_risk_fraction_max": _portfolio_value(sizing, "portfolio_open_and_pending_stop_risk_fraction_max"),
        "max_open_and_pending_orders": _portfolio_value(sizing, "max_open_and_pending_orders"),
        "max_positions_per_coin": _portfolio_value(sizing, "max_positions_per_coin"),
        "daily_loss_fraction_max": _portfolio_value(sizing, "daily_loss_fraction_max"),
        "minimum_tranche_usdt": _portfolio_value(sizing, "minimum_tranche_usdt"),
        "cooldown_minutes": _portfolio_value(sizing, "cooldown_minutes"),
        "coins": [
            {
                "logical_symbol": symbol,
                "enabled": True,
                "allocation_or_cap": None,
                "physical_symbol": "1000PEPEUSDT" if symbol == "PEPEUSDT" else symbol,
                "source": "ResearchV2JobConfig.symbols + common_profile.physical_binding",
            }
            for symbol in job.symbols
        ],
        "shared_per_coin_margin_fraction_cap": str(sizing.get("per_coin_margin_fraction_cap")),
        "source_refs": [
            "docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json",
            "triggertrade.research_v2.physical_symbol_for_research_v2",
            "triggertrade.research_v2_execution.evaluate_research_v2_portfolio_grant",
        ],
    }


def _portfolio_value(sizing: Mapping[str, Any], key: str) -> dict[str, Any]:
    return {"value": _canonicalize(sizing.get(key)), "origin": "COMMON_PROFILE", "changed_by_hypothesis": False}


def _delta_from_parent(job: ResearchV2HypothesisJob) -> dict[str, list[str]]:
    changed: list[str] = []
    unchanged: list[str] = []
    parent_signal = dict(job.parent_job.runtime_profile.get("signal", {}))
    signal = dict(job.runtime_profile.get("signal", {}))
    for path, before, after in _diff_dicts(parent_signal, signal, prefix="set.signal"):
        changed.append(f"{path}: {before} -> {after}")
    if not any(item.startswith("set.signal") for item in changed):
        unchanged.append("set signal predicates")
    if job.parent_job.stop_family != job.stop_family:
        changed.append(f"position_rules.stop.family: {job.parent_job.stop_family} -> {job.stop_family}")
    else:
        unchanged.append(f"position_rules.stop.family {job.stop_family}")
    if job.parent_job.entry_profile == job.entry_profile:
        unchanged.append("position_rules.entry")
    if job.parent_job.leverage == job.leverage:
        unchanged.append(f"position_rules.leverage {job.leverage}")
    if job.parent_job.margin_fraction == job.margin_fraction:
        unchanged.append(f"position_rules.margin_fraction {job.margin_fraction}")
    if job.parent_job.symbols == job.symbols:
        unchanged.append("portfolio_rules.coins")
    unchanged.extend(
        [
            "portfolio_rules.capital_and_risk_limits",
            "position_rules.take_profit",
            "position_rules.cooldown",
        ]
    )
    return {"changed": changed, "unchanged": unchanged}


def _diff_dicts(before: Mapping[str, Any], after: Mapping[str, Any], *, prefix: str) -> list[tuple[str, Any, Any]]:
    rows: list[tuple[str, Any, Any]] = []
    keys = sorted(set(before) | set(after))
    for key in keys:
        path = f"{prefix}.{key}"
        left = before.get(key)
        right = after.get(key)
        if isinstance(left, Mapping) and isinstance(right, Mapping):
            rows.extend(_diff_dicts(left, right, prefix=path))
        elif _canonicalize(left) != _canonicalize(right):
            rows.append((path, _canonicalize(left), _canonicalize(right)))
    return rows


def _boolean_composition(family: str) -> str:
    if family == "MOMENTUM_CONTINUATION":
        return "RET_OR AND RVOL5>=1.2 AND direction-specific J4 trend"
    if family == "RET_OR_TREND_ONLY":
        return "RET_OR AND direction-specific J4 trend; RVOL disabled"
    if family == "RET_OR_RVOL_ONLY":
        return "RET_OR AND RVOL5>=1.2; trend disabled"
    if family == "MOMENTUM_CONTINUATION_SHORT_DE":
        return "LONG: J4 continuation; SHORT: J4 continuation AND directional_efficiency_5m>=0.30"
    if family == "MOMENTUM_CONTINUATION_TURNOVER":
        return "J4 continuation AND turnover_acceleration>=1.2"
    if family == "COMPRESSION_BREAKOUT":
        return "compression AND RVOL5>=1.5 AND turnover_acceleration>=1.2 AND breakout buffer"
    if family == "EXHAUSTION_REVERSAL":
        return "impulse AND retrace-from-15m-extreme AND two-close confirmation AND turnover_acceleration<=1.0"
    return family


def _timeframe_inputs(family: str) -> list[str]:
    base = ["1m source candles", "5m completed bars", "15m completed bars"]
    if family == "MOMENTUM_CONTINUATION_SHORT_DE":
        return base + ["9 completed 5m closes"]
    if family == "COMPRESSION_BREAKOUT":
        return base + ["96 prior ATR15 observations", "prior 12 completed 5m bars"]
    return base


def load_rv2_hb001_hypothesis_jobs(
    manifest_path: Path = RV2_HB001_MANIFEST_PATH,
) -> dict[str, ResearchV2HypothesisJob]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    common = load_common_profile()
    parent_jobs = load_research_v2_jobs()
    code_commit = _git_commit_or_none()
    jobs: dict[str, ResearchV2HypothesisJob] = {}
    for row in manifest.get("hypotheses", ()):
        spec = ResearchV2HypothesisSpec.from_payload(row)
        if spec.batch_id != RV2_HB001_BATCH_ID:
            raise ResearchV2HypothesisError(f"unsupported batch_id: {spec.batch_id}")
        parent = parent_jobs.get(spec.parent_job_id)
        if parent is None:
            raise ResearchV2HypothesisError(f"unknown parent_job_id: {spec.parent_job_id}")
        jobs[spec.hypothesis_id] = ResearchV2HypothesisJob(
            spec=spec,
            parent_job=parent,
            runtime_profile=_runtime_profile_for_hypothesis(spec, parent, common),
            code_commit=code_commit,
        )
    return jobs


def _runtime_profile_for_hypothesis(
    spec: ResearchV2HypothesisSpec,
    parent: ResearchV2JobConfig,
    common: Mapping[str, Any],
) -> dict[str, Any]:
    profile = copy.deepcopy(parent.runtime_profile)
    profile["hypothesis"] = {
        **spec.to_payload(),
        "hypothesis_fingerprint": spec.fingerprint,
    }
    profile["signal"] = _signal_profile(spec, profile.get("signal", {}))
    profile["stop"] = common["stop_G1"] if spec.stop_family == "G1" else common["stop_G0"]
    profile["take_profit"] = common["take_profit"]
    profile["sizing"] = common["capital_risk"]
    profile["costs"] = common["costs"]
    profile["units_policy"] = common["units_policy"]
    profile["features"] = common["features"]
    profile["warmup_days"] = common.get("warmup_days")
    return profile


def _signal_profile(spec: ResearchV2HypothesisSpec, parent_signal: Mapping[str, Any]) -> dict[str, Any]:
    params = dict(spec.parameters)
    family = spec.signal_family
    signal = dict(parent_signal)
    signal["family"] = family
    signal["direction_mode"] = spec.direction_mode
    if family == "RET_OR_TREND_ONLY":
        signal.update({"base": "V2-SIGNAL-RET5-RET15-OR-V1", "trend_gate": "J4_ONLY", "rvol_gate": "DISABLED"})
    elif family == "RET_OR_RVOL_ONLY":
        signal.update({"base": "V2-SIGNAL-RET5-RET15-OR-V1", "trend_gate": "DISABLED", "rvol5_min": str(params["rvol5_min"])})
    elif family == "MOMENTUM_CONTINUATION_SHORT_DE":
        signal.update({"base": "V2-SIGNAL-CONTINUATION-V1", "short_directional_efficiency_min": str(params["short_directional_efficiency_min"])})
    elif family == "MOMENTUM_CONTINUATION_TURNOVER":
        signal.update({"base": "V2-SIGNAL-CONTINUATION-V1", "turnover_acceleration_min": str(params["turnover_acceleration_min"])})
    elif family == "COMPRESSION_BREAKOUT":
        signal["compression_ratio_max"] = str(params.get("compression_ratio_max", signal.get("compression_ratio_max", "0.80")))
    elif family in {"MOMENTUM_CONTINUATION", "EXHAUSTION_REVERSAL"}:
        pass
    else:
        raise ResearchV2HypothesisError(f"unsupported hypothesis signal family: {family}")
    if params.get("g0_eligibility_only"):
        signal["g0_eligibility_only"] = True
    return signal


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ResearchV2HypothesisError(f"{key} is required")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _git_commit_or_none() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    commit = result.stdout.strip()
    return commit or None
