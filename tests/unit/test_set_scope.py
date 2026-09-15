from __future__ import annotations

import pytest

from triggertrade.set_scope import SetConfigurationBinding, SetScopeError


def test_set_configuration_binding_is_strict_and_digest_stable():
    binding = configuration_binding()
    reordered = SetConfigurationBinding.from_payload(
        {
            "numeric_policy_version": "TT_SET_NUMERIC_V1",
            "core_set_config_digest": "c" * 64,
            "core_set_config_version": "core-v1",
            "core_set_config_id": "core-set-main",
            "trigger_config_digest": "b" * 64,
            "trigger_config_version": "trigger-v1",
            "trigger_config_id": "trigger-pack-main",
            "set_config_digest": "a" * 64,
            "set_config_version": "set-v1",
            "set_config_id": "set-main",
        }
    )

    assert binding.to_payload() == reordered.to_payload()
    assert binding.digest == reordered.digest


def test_set_configuration_binding_rejects_unknown_missing_and_wrong_policy():
    payload = configuration_binding().to_payload()
    with pytest.raises(SetScopeError, match="unknown"):
        SetConfigurationBinding.from_payload({**payload, "extra": "nope"})
    missing = dict(payload)
    missing.pop("set_config_id")
    with pytest.raises(SetScopeError, match="missing"):
        SetConfigurationBinding.from_payload(missing)
    with pytest.raises(SetScopeError, match="TT_SET_NUMERIC_V1"):
        SetConfigurationBinding.from_payload({**payload, "numeric_policy_version": "OTHER"})


def configuration_binding() -> SetConfigurationBinding:
    return SetConfigurationBinding(
        set_config_id="set-main",
        set_config_version="set-v1",
        set_config_digest="a" * 64,
        trigger_config_id="trigger-pack-main",
        trigger_config_version="trigger-v1",
        trigger_config_digest="b" * 64,
        core_set_config_id="core-set-main",
        core_set_config_version="core-v1",
        core_set_config_digest="c" * 64,
    )
