"""Exact-byte specification and complete ordered V1 registry identities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import platform

import numpy as np

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .features import GROUPS, NAMES
from .manifests import canonical_json, digest

# Construction descriptions are versioned audit data, never additional inputs.
CONSTRUCTIONS = (
    "asinh(m_1)", "asinh(m_3)", "asinh(m_6)", "asinh(m_12)",
    "asinh(m_24)", "asinh(m_48)", "abs(asinh(m_12))", "abs(asinh(m_48))",
    "sum(sign(r_k),k=0..11)/12;sign(0)=0",
    "sum(sign(r_k),k=0..47)/48;sign(0)=0",
    "sum(1[sign(r_k)*sign(r_(k+1))<0],k=0..10)/11",
    "asinh((ln(C_0)-ln(O_0))/sigma_48)",
    "log1p((ln(H_0)-ln(L_0))/sigma_48)",
    "((ln(C_0)-ln(L_0))-(ln(H_0)-ln(C_0)))/(ln(H_0)-ln(L_0));flat=0",
    "1[raw H_0=raw L_0]",
    "asinh((max(c_0..c_12)-c_0)/(sigma_48*sqrt(12)))",
    "asinh((c_0-min(c_0..c_12))/(sigma_48*sqrt(12)))",
    "asinh((max(c_0..c_48)-c_0)/(sigma_48*sqrt(48)))",
    "asinh((c_0-min(c_0..c_48))/(sigma_48*sqrt(48)))",
    "ln(sigma_48(U))", "sigma_12/sigma_48", "sigma_48/sigma_288",
    "max(r_k^2,k=0..47)/sum(r_k^2,k=0..47)",
    "asinh(m_12(BTC));BTC-own-sigma_48",
    "asinh(m_48(BTC));BTC-own-sigma_48",
    "sigma_12(BTC)/sigma_48(BTC)", "sigma_48(BTC)/sigma_288(BTC)",
    "asinh(m_12(local)-m_12(BTC))", "asinh(m_48(local)-m_48(BTC))",
    "tanh(m_12(local))*tanh(m_12(BTC))",
    "sin(2*pi*UTC_seconds_since_midnight(T)/86400)",
    "cos(2*pi*UTC_seconds_since_midnight(T)/86400)",
    "1[physical_symbol=AVAXUSDT]", "1[physical_symbol=SUIUSDT]",
    "1[physical_symbol=1000PEPEUSDT]",
)


@dataclass(frozen=True)
class SpecificationBytes:
    spec_id: str
    spec_version: str
    file_identity: str
    byte_size: int
    sha256: str
    materialization_ref: str

    @classmethod
    def from_bytes(cls, exact_bytes: bytes, *, file_identity: str,
                   materialization_ref: str) -> SpecificationBytes:
        if not file_identity or not materialization_ref:
            raise ValueError("specification file and materialization provenance required")
        exact_bytes.decode("utf-8", errors="strict")
        return cls(SPEC_ID, SPEC_VERSION, file_identity, len(exact_bytes),
                   sha256(exact_bytes).hexdigest(), materialization_ref)

    def authenticate_bytes(self, exact_bytes: bytes) -> None:
        if (len(exact_bytes) != self.byte_size or
                sha256(exact_bytes).hexdigest() != self.sha256):
            raise ValueError("exact specification bytes differ from declared identity")


@dataclass(frozen=True)
class RegistryDescriptor:
    registry_id: str
    feature_count: int
    ordered_columns: tuple[tuple[int, str, str, str], ...]
    aggregation: str
    numerical_convention: str
    scaling_contract: tuple[str, ...]
    btc_mask_columns: tuple[int, ...]
    constant_contract: tuple[str, ...]
    descriptor_sha256: str

    def body(self) -> dict[str, object]:
        value = asdict(self)
        value.pop("descriptor_sha256")
        return value

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    def verify(self) -> None:
        if (self.registry_id != FEATURE_REGISTRY or self.feature_count != 35 or
                len(self.ordered_columns) != 35 or
                tuple(row[1] for row in self.ordered_columns) != NAMES or
                tuple(row[3] for row in self.ordered_columns) != GROUPS or
                self.descriptor_sha256 != digest(self.body())):
            raise ValueError("registry descriptor identity mismatch")


def frozen_registry() -> RegistryDescriptor:
    if len(CONSTRUCTIONS) != 35 or len(NAMES) != 35 or len(GROUPS) != 35:
        raise ValueError("registry column count mismatch")
    provisional = RegistryDescriptor(
        FEATURE_REGISTRY, 35,
        tuple((i, name, construction, group) for i, (name, construction, group)
              in enumerate(zip(NAMES, CONSTRUCTIONS, GROUPS), 1)),
        "U=T-1m;289 completed 5m aggregates;1445 consecutive 1m intervals [U-1445m,U)",
        "binary64;natural-log;oldest-to-newest window reductions;LDE_V1_ADJ35_U1M_PY_MATH_V1",
        ("P:pooled eligible base rows;mean/population-SD(ddof=0)",
         "S:per-physical-symbol eligible base rows;column20",
         "A:pooled eligible altcoin base rows;columns24-30",
         "I:identity;columns15,31-35"), tuple(range(24, 31)),
        ("exactly constant P/S/A domain stores raw constant and emits zero",
         "nonconstant zero/nonfinite variance is fitting failure;no epsilon or clipping",
         "identity constants retain identity values;whole-state constants freeze slopes",
         "BTC context columns24-30 exactly zero after preprocessing"), "")
    result = RegistryDescriptor(**{**provisional.body(), "descriptor_sha256": digest(provisional.body())})
    result.verify()
    return result


@dataclass(frozen=True)
class EnvironmentIdentity:
    python_version: str
    numpy_version: str
    platform_identity: str
    model_numerical_runtime: str
    comparator_numerical_runtime: str
    source_revision: str
    serializer_version: str
    dependency_lock_ref: str | None
    dependency_lock_sha256: str | None
    dependency_lock_status: str
    identity_sha256: str

    def body(self) -> dict[str, object]:
        value = asdict(self)
        value.pop("identity_sha256")
        return value

    @classmethod
    def build(cls, *, source_revision: str, serializer_version: str,
              model_numerical_runtime: str, comparator_numerical_runtime: str,
              dependency_lock_bytes: bytes | None = None,
              dependency_lock_ref: str | None = None) -> EnvironmentIdentity:
        if not all((source_revision, serializer_version, model_numerical_runtime,
                    comparator_numerical_runtime)):
            raise ValueError("environment identity fields required")
        if (dependency_lock_bytes is None) != (dependency_lock_ref is None):
            raise ValueError("lock bytes and reference must be supplied together")
        provisional = cls(platform.python_version(), np.__version__, platform.platform(),
                          model_numerical_runtime, comparator_numerical_runtime,
                          source_revision, serializer_version, dependency_lock_ref,
                          sha256(dependency_lock_bytes).hexdigest() if dependency_lock_bytes is not None else None,
                          "DECLARED_UNVERIFIED" if dependency_lock_bytes is not None else "NOT_AVAILABLE", "")
        return cls(**{**provisional.body(), "identity_sha256": digest(provisional.body())})
