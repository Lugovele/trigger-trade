"""UI-only fixture values mirroring the attached TriggerTrade v6 reference.

These values are not production rule definitions, trades, positions, P&L, or
API health facts. They exist only for dashboard DOM/fidelity tests.
"""

VISUAL_TRIGGER_SETS = (
    {"version": "v4", "status": "ACTIVE", "purpose": "Current live execution set", "rules": 5},
    {"version": "v5", "status": "TESTING", "purpose": "v4 + momentum confirmation", "rules": 6},
    {"version": "v3", "status": "ARCHIVE", "purpose": "Previous live configuration", "rules": 4},
)

VISUAL_RULE_NAMES = (
    "Price drop",
    "RSI threshold",
    "Volume confirmation",
    "Trend filter",
    "Allocation limit",
    "Momentum confirmation",
)
