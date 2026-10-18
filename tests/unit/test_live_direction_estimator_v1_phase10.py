"""Small offline Phase 10 contract checks; no corpus or holdout access."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from math import exp, log

import pytest

from triggertrade.live_direction_estimator_v1.artifact_contract import (
    ArtifactField, DOSSIER_REFERENCES, FINAL_FIELD_NAMES, FIT_FIELD_NAMES,
    build_dossier, build_fit_contract,
)
from triggertrade.live_direction_estimator_v1.calendar import (
    D0, H1_START, ReadinessEvidence, schedule_prospective,
)
from triggertrade.live_direction_estimator_v1.failure_classification import classify_failure
from triggertrade.live_direction_estimator_v1.features import RawFeatureRow
from triggertrade.live_direction_estimator_v1.governance_seal import (
    AuthenticationResult, H1Access, H1GovernanceEvidence, SealCodeIdentities,
    FinalPrimaryIdentity, PreH1Freeze, build_prospective_seal,
)
from triggertrade.live_direction_estimator_v1.evaluation_metrics import ProbabilityState, SealedPrediction
from triggertrade.live_direction_estimator_v1.manifests import RowMetadata, build_manifest, digest
from triggertrade.live_direction_estimator_v1.model import CLASSES
from triggertrade.live_direction_estimator_v1.origin_contract import (
    DiagnosticLinks, FeatureAudit, LaterOutcomeLinkage, OriginIdentity,
    OriginInputs, OriginStatus, OriginTimes, ProbabilityAudit, SourceVersionAudit,
    assert_unique_origin_keys, join_outcome, seal_origin_record,
)
from triggertrade.live_direction_estimator_v1.registry_identity import (
    EnvironmentIdentity, SpecificationBytes, frozen_registry,
)
from triggertrade.live_direction_estimator_v1.source import SYMBOLS
from triggertrade.live_direction_estimator_v1.report_only_status import seal_report_only_status
from triggertrade.live_direction_estimator_v1.stability_diagnostics import (
    VintageComparison, adjacent_origin_report, fit_causal_strata, prospective_windows, reconcile_vintages,
    reflect_raw,
)


def _raw(symbol, t, sigma):
    values = [0.1 + i * 0.01 for i in range(32)]
    values[19] = log(sigma)
    values[14] = 0.0
    values += [float(symbol == s) for s in SYMBOLS[1:]]
    return RawFeatureRow(symbol, t, t-timedelta(minutes=1),
                         f"synthetic:{symbol}:{t.isoformat()}:{sigma}", tuple(values))


def _base(horizon=60):
    rows = []
    for si, symbol in enumerate(SYMBOLS):
        for j, sigma in enumerate((1., 2., 3., 4., 5.)):
            t = D0 + timedelta(days=2, minutes=5*(si*5+j))
            raw = _raw(symbol, t, sigma)
            rows.append(RowMetadata(symbol, t, horizon, "AVAILABLE", "VALID",
                                    CLASSES[j % 3], raw, 1))
    return tuple(rows)


def test_causal_quantiles_equality_and_empty_strata():
    rows = _base()
    manifest = build_manifest(rows, horizon_minutes=60, fit_id="F1", segment_type="BASE")
    strata = fit_causal_strata(manifest, rows)
    btc = strata["BTCUSDT"]
    assert btc.predictor_sigma_48_u_thresholds == tuple(exp(log(v)) for v in (1., 2., 3., 4.))
    assert [btc.assign(exp(log(v))) for v in (1., 2., 3., 4., 5.)] == [0, 1, 2, 3, 4]
    same = tuple(replace(row, feature_row=_raw(row.physical_symbol,
                    row.prediction_origin, 2.)) for row in rows)
    same_manifest = build_manifest(same, horizon_minutes=60, fit_id="F1", segment_type="BASE")
    flat = fit_causal_strata(same_manifest, same)["BTCUSDT"]
    assert flat.predictor_sigma_48_u_thresholds == (2.,)*4
    assert flat.assign(2.) == 0 and flat.assign(3.) == 4
    assert "canonical_rms48" not in fit_causal_strata.__code__.co_names


def test_prospective_windows_independent_and_fixed():
    f = datetime(2026, 10, 1, tzinfo=UTC)
    r = f + timedelta(minutes=1)
    schedule = schedule_prospective(ReadinessEvidence(60, "FINAL_ARTIFACT", f, "f"),
                                    ReadinessEvidence(60, "COLLECTOR", r, "r"))
    thirty, weekly = prospective_windows(schedule)
    assert len(thirty) == 3 and len(weekly) == 13
    assert all((w.end-w.start) == timedelta(days=30) for w in thirty)
    assert all((w.end-w.start) == timedelta(days=7) for w in weekly[:12])
    assert weekly[-1].end-weekly[-1].start == timedelta(days=6)
    assert thirty[0].start == weekly[0].start == schedule.start
    assert thirty[-1].end == weekly[-1].end == schedule.end


def test_reflection_exact_raw_map_and_vintage_immutability():
    raw = _raw("AVAXUSDT", D0+timedelta(days=2), 2.)
    reflected = reflect_raw(raw)
    negate = {1,2,3,4,5,6,9,10,12,14,24,25,28,29}
    swap = {16:17,17:16,18:19,19:18}
    for index in range(1,36):
        expected = raw.values[swap.get(index,index)-1] if index in swap else (
            -raw.values[index-1] if index in negate else raw.values[index-1])
        assert reflected.values[index-1] == expected
    assert raw.values[0] > 0 and reflected.values[0] < 0
    comparison = VintageComparison("AVAXUSDT", raw.prediction_origin, "sealed-snapshot",
                                   (("minute", "v1"),), (("minute", "v2"),), ("momentum",))
    report = reconcile_vintages((comparison,))
    assert report.discrepancies == 1 and report.affected_feature_families == ("momentum",)
    assert comparison.sealed_versions == (("minute", "v1"),)


def test_exact_spec_bytes_and_complete_registry_identity():
    a = SpecificationBytes.from_bytes(b"line\r\n", file_identity="synthetic.md", materialization_ref="fixture")
    b = SpecificationBytes.from_bytes(b"line\n", file_identity="synthetic.md", materialization_ref="fixture")
    assert a.sha256 == sha256(b"line\r\n").hexdigest() and a.sha256 != b.sha256
    registry = frozen_registry()
    assert registry.feature_count == 35 and registry.descriptor_sha256 == digest(registry.body())
    changed = replace(registry, ordered_columns=registry.ordered_columns[::-1])
    assert digest(changed.body()) != registry.descriptor_sha256
    with pytest.raises(ValueError):
        changed.verify()


def test_h1_clean_requires_bound_affirmative_audit():
    initial = H1GovernanceEvidence.create()
    assert initial.cleanliness() == "CLEANLINESS_UNVERIFIED"
    access = H1Access("PRICES", "2026-06-01T00:00:00Z", "audit-row", "NO")
    pre = H1GovernanceEvidence.create((access,), audit_inventory_complete=True,
                                      audit_reference="inventory")
    proof = AuthenticationResult("H1_AUDIT", pre.audit_subject(), "SYNTHETIC_FIXTURE",
                                 "offline-fixture", "2026-06-02T00:00:00Z")
    clean = H1GovernanceEvidence.create((access,), audit_inventory_complete=True,
                                        audit_reference="inventory", audit_authentication=proof)
    assert clean.cleanliness(verifier=lambda p: True, fixture_only=True) == "ESTIMATOR_RESERVED_CLEAN"
    assert clean.cleanliness() == "CLEANLINESS_UNVERIFIED"
    with pytest.raises(ValueError):
        H1GovernanceEvidence.create((replace(access, affected_estimator_choices="YES"),),
            audit_inventory_complete=True, audit_reference="inventory", audit_authentication=proof)


def test_pre_h1_freeze_is_before_authenticated_score_access_not_nominal_start():
    h = "a"*64
    frozen = datetime(2026,7,1,0,10,tzinfo=UTC)
    first = datetime(2026,7,1,0,20,tzinfo=UTC)
    provisional = PreH1Freeze(60,h,h,h,h,(h,h,h),"revision",h,h,h,h,h,h,h,
                              frozen.isoformat().replace("+00:00","Z"),"")
    freeze = replace(provisional,freeze_sha256=digest(provisional.body()))
    assert freeze.structurally_valid() and frozen > H1_START
    proof = AuthenticationResult("PRE_H1_FREEZE",freeze.freeze_sha256,
        "SYNTHETIC_FIXTURE","fixture",(frozen+timedelta(seconds=1)).isoformat().replace("+00:00","Z"))
    access = AuthenticationResult("H1_FIRST_SCORE_ACCESS",digest({
        "horizon":60,"first_score_access_at":"2026-07-01T00:20:00.000000Z"}),
        "SYNTHETIC_FIXTURE","fixture",first.isoformat().replace("+00:00","Z"))
    assert freeze.authenticated_before_score(proof,first,access,
        verifier=lambda p: True,fixture_only=True)
    assert not freeze.authenticated_before_score(proof,first,access,verifier=None)


def _unavailable_record(horizon=60, cohort="fixture"):
    t = D0+timedelta(days=2)
    text = lambda x: x.isoformat().replace("+00:00", "Z")
    identity = OriginIdentity("LIVE_DIRECTION_ESTIMATOR_V1", "1.0.0", "a"*64,
                              "LDE_V1_ADJ35_U1M", "b"*64, cohort, "BTCUSDT", None,
                              horizon, None, None, None)
    times = OriginTimes(text(t), text(t-timedelta(minutes=1)), text(t), None,
                        text(t+timedelta(seconds=10)), None)
    status = OriginStatus("PROSPECTIVE_FORECAST", "UNAVAILABLE", ("MISSING_REQUIRED_MINUTE",),
                          "MISSED_DEADLINE", None)
    inputs = OriginInputs(None, (), (), (), None, None, None, None)
    features = FeatureAudit(None, None, None, None, None, None, None)
    links = DiagnosticLinks((), (), None, None, None, None)
    return seal_origin_record(identity, times, status, inputs, features,
                              ProbabilityAudit.unavailable(), links)


def test_unavailable_origin_key_watermark_and_outcome_separation():
    record = _unavailable_record()
    assert record.times.prediction_timestamp is None
    assert record.times.feature_timestamp == "2024-10-03T23:59:00Z"
    assert record.probabilities == ProbabilityAudit.unavailable()
    assert record.later_outcome == LaterOutcomeLinkage.pending()
    assert record.key != _unavailable_record(120).key
    assert record.key != _unavailable_record(cohort="other").key
    with pytest.raises(ValueError):
        assert_unique_origin_keys((record, record))
    outcome = LaterOutcomeLinkage(("BTCUSDT", record.times.prediction_origin, 60),
                                  "VALID", "c"*64, "vintage", "calc",
                                  record.times.prediction_origin, "d"*64)
    joined = join_outcome(record, outcome, CLASSES[0])
    assert joined.origin_record_sha256 == record.record_sha256
    assert record.later_outcome == LaterOutcomeLinkage.pending()
    with pytest.raises(ValueError,match="immutable origin"):
        join_outcome(replace(record, identity=replace(record.identity,evidence_cohort_id="tampered")),
                     outcome, CLASSES[0])
    with pytest.raises(ValueError,match="complete canonical"):
        join_outcome(record,replace(outcome,target_file_sha256=None),CLASSES[0])
    assert record.validate() == ()
    false_claim = replace(record, status=replace(record.status, provenance_mode="ASOF_VERIFIED"))
    assert "ASOF_UNVERIFIED" in false_claim.validate()


def test_fit_and_dossier_inventories_remain_horizon_specific():
    registry = frozen_registry()
    environment = EnvironmentIdentity.build(source_revision="fixture", serializer_version="1",
        model_numerical_runtime="python", comparator_numerical_runtime="python")
    fields = {name: ArtifactField(None, "NOT_AVAILABLE") for name in FIT_FIELD_NAMES}
    for name in FINAL_FIELD_NAMES:
        fields[name] = ArtifactField(None, "NOT_AVAILABLE")
    assert len(fields) == len(FIT_FIELD_NAMES)+len(FINAL_FIELD_NAMES)
    base = _base()
    bm = build_manifest(base, horizon_minutes=60, fit_id="FINAL", segment_type="BASE")
    cal = tuple(replace(row, prediction_origin=datetime(2026,6,1,2,0,tzinfo=UTC)+
             timedelta(minutes=5*i), feature_row=_raw(row.physical_symbol,
             datetime(2026,6,1,2,0,tzinfo=UTC)+timedelta(minutes=5*i), 2.))
             for i,row in enumerate(base))
    cm = build_manifest(cal, horizon_minutes=60, fit_id="FINAL", segment_type="CALIBRATION")
    fit = build_fit_contract(role="PRIMARY", base=bm, calibration=cm,
                             registry=registry, environment=environment, fields=fields)
    assert fit.validate() == ()
    assert "PROSPECTIVE_FIT_EVIDENCE_INCOMPLETE" in fit.validate(require_prospective_ready=True)
    assert "PROSPECTIVE_FIT_EVIDENCE_UNAUTHENTICATED" in fit.validate(
        require_prospective_ready=True)
    bad_registry = replace(registry, ordered_columns=registry.ordered_columns[::-1])
    with pytest.raises(ValueError, match="FIT_REGISTRY"):
        build_fit_contract(role="PRIMARY", base=bm, calibration=cm,
                           registry=bad_registry, environment=environment, fields=fields)
    bad_environment = replace(environment, source_revision="tampered")
    with pytest.raises(ValueError, match="FIT_ENVIRONMENT"):
        build_fit_contract(role="PRIMARY", base=bm, calibration=cm,
                           registry=registry, environment=bad_environment, fields=fields)
    references = {name: ArtifactField(None,"NOT_AVAILABLE") for name in DOSSIER_REFERENCES}
    folds = {f"F{i}": str(i)*64 for i in range(1,6)}
    d60 = build_dossier(horizon_minutes=60, fit_contract_sha256=fit.contract_sha256,
                        fold_hashes=folds, references=references, fixture_only=True)
    d120 = build_dossier(horizon_minutes=120, fit_contract_sha256=fit.contract_sha256,
                         fold_hashes=folds, references=references, fixture_only=True)
    assert d60.validate() == () and d120.validate() == ()
    assert d60.dossier_sha256 != d120.dossier_sha256
    with pytest.raises(ValueError, match="CONFIRMATORY_VERDICT_WITHOUT_COMPLETE_EVIDENCE"):
        build_dossier(horizon_minutes=60, fit_contract_sha256=fit.contract_sha256,
                      fold_hashes=folds, references=references, fixture_only=True,
                      verdict="ACCEPT")


def test_failure_classes_distinguish_operational_and_statistical():
    assert classify_failure("MISSING_REQUIRED_MINUTE").failure_class == "UNAVAILABLE"
    assert classify_failure("FALSE_ASOF_CLAIM").failure_class == "INVALID"
    assert classify_failure("SYMBOL_CLASS_SUPPORT_ABSENT").failure_class == "MODEL_NOT_ESTIMABLE"
    assert classify_failure("SOLVER_FAILURE").failure_class == "FIT_FAILED"
    assert classify_failure("CALIBRATION_FAILURE").failure_class == "CALIBRATION_FAILED"
    assert classify_failure("UNDEFINED_REQUIRED_BOUND").failure_class == "NOT_ESTIMABLE"
    assert classify_failure("COVERAGE_SHORTFALL").failure_class == "CONTINUE_RESEARCH"
    assert classify_failure("REGISTERED_R1").failure_class == "REJECT"


def _prediction(t, probabilities, *, bundle="a"*64, emitted=True):
    state = ProbabilityState.from_probabilities(probabilities) if emitted else None
    return SealedPrediction(t, "BTCUSDT", 60, "F1", bundle if emitted else None,
                            state, state, None, None, None, None, emitted, None,
                            "EVENT_TIME_ONLY", feature_status="AVAILABLE" if emitted else "UNAVAILABLE")


def test_adjacent_tv_log_odds_flips_and_hard_boundaries():
    t = D0+timedelta(days=2)
    a = _prediction(t, (.6,.2,.2))
    b = _prediction(t+timedelta(minutes=5), (.2,.6,.2))
    missing = _prediction(t+timedelta(minutes=10), (.3,.3,.4), emitted=False)
    c = _prediction(t+timedelta(minutes=15), (.6,.2,.2))
    d = _prediction(t+timedelta(minutes=20), (.2,.6,.2), bundle="b"*64)
    pairs, runs = adjacent_origin_report((a,b,missing,c,d))
    assert len(pairs) == 1 and pairs[0].total_variation == pytest.approx(.4)
    assert pairs[0].hard_class_flip_long_short
    assert pairs[0].side_log_odds_change == pytest.approx(-2*log(3))
    assert sum(run.length for run in runs) == 4


def _seal(*, registered=None):
    h = "a"*64
    final = FinalPrimaryIdentity(60,"FINAL",h,h,h,h,h,h,h,"B2",
                                 "2026-10-01T00:00:00Z","actual-fit-ref")
    f = datetime(2026,10,1,tzinfo=UTC)
    r = f+timedelta(minutes=1)
    schedule = schedule_prospective(ReadinessEvidence(60,"FINAL_ARTIFACT",f,"fit-proof"),
                                    ReadinessEvidence(60,"COLLECTOR",r,"collector-proof"))
    code = SealCodeIdentities(*(h for _ in range(14)), "NumPy 2.2.5 PCG64.random_raw", 20261017)
    comp = seal_report_only_status(role="C1_SHALLOW_RF",horizon_minutes=60,fit_id="FINAL",
            status="NOT_ASSESSED",reason="offline",primary_bundle_sha256=h)
    shadow = seal_report_only_status(role="SIX_MONTH_ROLLING_SHADOW",horizon_minutes=60,
            fit_id="FINAL",status="NOT_ASSESSED",reason="offline",primary_bundle_sha256=h)
    spec = SpecificationBytes.from_bytes(b"synthetic-spec",file_identity="fixture.md",
                                          materialization_ref="offline")
    env = EnvironmentIdentity.build(source_revision="fixture",serializer_version="1",
        model_numerical_runtime="python",comparator_numerical_runtime="python",
        dependency_lock_bytes=b"lock",dependency_lock_ref="fixture-lock")
    return build_prospective_seal(horizon_minutes=60,evidence_cohort_id="P60-fixture",
        specification=spec,registry=frozen_registry(),environment=env,code=code,
        final_primary=final,comparator=comp,shadow=shadow,
        source_manifest_sha256=h,canonical_label_sha256=h,schedule=schedule,
        registered_at=registered or schedule.start-timedelta(minutes=5),
        ledger_anchor_sha256=h)


def test_prospective_seal_default_blocked_timing_and_immutability():
    seal = _seal()
    assert "CLOCK_UNVERIFIED" in seal.validate()
    assert "LEDGER_ANCHOR_UNVERIFIED" in seal.validate()
    assert seal.operationally_ready_without_external_verifier is False
    assert "HORIZON_OR_FINAL_ARTIFACT_MISMATCH" not in seal.validate()
    changed = replace(seal, final_primary=replace(seal.final_primary, model_sha256="b"*64))
    assert digest(changed.body()) != seal.seal_sha256
    late = _seal(registered=datetime.fromisoformat(seal.schedule_start.replace("Z","+00:00")))
    assert "SEAL_NOT_REGISTERED_BEFORE_P0" in late.validate()
    assert "ACTUAL_ARTIFACT_AVAILABILITY_MISSING" in replace(
        seal, final_primary=replace(seal.final_primary,actual_fitted_state_available_at=None)).validate()


def test_synthetic_authentication_binds_exact_claims_and_clock_error():
    seal = _seal()
    start = datetime.fromisoformat(seal.schedule_start.replace("Z","+00:00"))
    close = _seal(registered=start-timedelta(seconds=1))
    when = (start-timedelta(minutes=10)).isoformat().replace("+00:00","Z")
    proofs = tuple(AuthenticationResult(kind, subject, "SYNTHETIC_FIXTURE",
              "fixture-authority", when, 5.0 if kind == "CLOCK" else None)
              for kind,subject in close.authentication_subjects().items())
    provisional = replace(close, authentication=proofs)
    signed = replace(provisional, seal_sha256=digest(provisional.body()))
    assert "REGISTRATION_UTC_BOUND_OVERLAPS_P0" in signed.validate(
        verifier=lambda p: True,fixture_only=True)
    assert "CLOCK_UNVERIFIED" in signed.validate()  # fixture proof never grants production authority
    altered = replace(signed, collector_ready_ref="different")
    assert "CLOCK_UNVERIFIED" in altered.validate(verifier=lambda p: True,fixture_only=True)
    changed_status = replace(signed, comparator=seal_report_only_status(
        role="C1_SHALLOW_RF",horizon_minutes=60,fit_id="FINAL",status="FIT_FAILED",
        reason="later-claim",primary_bundle_sha256="a"*64))
    assert "ARTIFACT_AVAILABILITY_UNVERIFIED" in changed_status.validate(
        verifier=lambda p: True,fixture_only=True)
    assert "LEDGER_ANCHOR_UNVERIFIED" in changed_status.validate(
        verifier=lambda p: True,fixture_only=True)
    changed_code = replace(signed, code=replace(signed.code, feature_code_sha256="b"*64,
                                                gate_code_sha256="c"*64))
    changed_code = replace(changed_code, seal_sha256=digest(changed_code.body()))
    assert "LEDGER_ANCHOR_UNVERIFIED" in changed_code.validate(
        verifier=lambda p: True,fixture_only=True)


def test_fitted_report_only_state_must_exist_by_registration():
    seal = _seal()
    registered = datetime.fromisoformat(seal.registered_at.replace("Z","+00:00"))
    fitted = seal_report_only_status(role="C1_SHALLOW_RF",horizon_minutes=60,
        fit_id="FINAL",status="FITTED",reason="fixture",primary_bundle_sha256="a"*64,
        artifact_sha256="b"*64,artifact_available_at=registered+timedelta(seconds=1),
        evidence_ref="fixture-ref")
    late = replace(seal, comparator=fitted)
    assert "REPORT_ONLY_ARTIFACT_AVAILABLE_AFTER_REGISTRATION" in late.validate()


def _available_origin():
    t = D0 + timedelta(days=2)
    fmt = lambda value: value.isoformat().replace("+00:00","Z")
    raw = _raw("BTCUSDT",t,2.)
    p = (.6,.2,.2)
    lp = tuple(log(v) for v in p)
    identity = OriginIdentity("LIVE_DIRECTION_ESTIMATOR_V1","1.0.0","a"*64,
        "LDE_V1_ADJ35_U1M","b"*64,"fixture","BTCUSDT",None,60,"FINAL","pre","cal")
    times = OriginTimes(fmt(t),fmt(t-timedelta(minutes=1)),fmt(t),
        fmt(t+timedelta(seconds=1)),fmt(t+timedelta(seconds=2)),None)
    status = OriginStatus("HISTORICAL_SIMULATION","AVAILABLE",(),"NOT_APPLICABLE","EVENT_TIME_ONLY")
    source = SourceVersionAudit("BTCUSDT",fmt(t-timedelta(minutes=1446)),
        fmt(t-timedelta(minutes=1445)),"historical-v1","c"*64,None,None)
    inputs = OriginInputs("snapshot",(source,),(),(),None,
        (fmt(t-timedelta(minutes=1446)),fmt(t-timedelta(minutes=1))),None,None)
    transformed = list(raw.values)
    transformed[23:30] = [0.0]*7
    features = FeatureAudit(raw.values,None,tuple(transformed),None,(),tuple(range(24,31)),2.)
    probabilities = ProbabilityAudit(lp,lp,lp,lp,*p,CLASSES[0],.6)
    baseline_links = tuple((name,f"{name}-fixture") for name in ("B0","B1","B2","B3"))
    links = DiagnosticLinks(baseline_links,baseline_links,"d"*64,None,"e"*64,None)
    return identity,times,status,inputs,features,probabilities,links


def test_available_origin_resolves_snapshot_and_probability_identity():
    args = _available_origin()
    with pytest.raises(ValueError,match="SOURCE_SNAPSHOT_UNRESOLVED"):
        seal_origin_record(*args)
    record = seal_origin_record(*args,snapshot_verifier=lambda item: True)
    assert record.validate(snapshot_verifier=lambda item: True) == ()
    raw_tenth = list(args[4].raw_35)
    raw_tenth[19] = log(.1)
    rounded_sigma = replace(args[4],raw_35=tuple(raw_tenth),predictor_sigma_48_u=.1)
    assert seal_origin_record(*args[:4],rounded_sigma,*args[5:],
                              snapshot_verifier=lambda item: True).validate(
                                  snapshot_verifier=lambda item: True) == ()
    wrong_class = replace(args[5],predicted_class=CLASSES[1])
    with pytest.raises(ValueError,match="PROBABILITY_LOGIT_IDENTITY_MISMATCH"):
        seal_origin_record(*args[:5],wrong_class,args[6],snapshot_verifier=lambda item: True)
    wrong_span = replace(args[3],local_support_span=(args[3].local_support_span[0],
                     "2024-10-04T00:00:00Z"))
    with pytest.raises(ValueError,match="SOURCE_SUPPORT_SPAN_INVALID"):
        seal_origin_record(*args[:3],wrong_span,*args[4:],snapshot_verifier=lambda item: True)
    with pytest.raises(ValueError,match="BASELINE_LINKAGE_INCOMPLETE"):
        seal_origin_record(*args[:6],replace(args[6],baseline_outputs=()),
                           snapshot_verifier=lambda item: True)
    with pytest.raises(ValueError,match="FEATURE_AUDIT_FLAGS_INVALID"):
        seal_origin_record(*args[:4],replace(args[4],mask_flags=None),*args[5:],
                           snapshot_verifier=lambda item: True)
