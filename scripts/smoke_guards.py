"""Shared guards for manual, noncanonical smoke harnesses."""

from __future__ import annotations

MANUAL_NONCANONICAL_SMOKE = "manual_opt_in_noncanonical_smoke"


def require_manual_smoke_opt_in(env: dict[str, str], flag: str, name: str) -> None:
    if env.get(flag) != "1":
        raise RuntimeError(f"{name} is manual/noncanonical; set {flag}=1 to run")


def smoke_metadata(flag: str) -> dict[str, str]:
    return {
        "classification": MANUAL_NONCANONICAL_SMOKE,
        "opt_in_flag": flag,
    }
