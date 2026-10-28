"""Output parsing and the deterministic policy-enforcement layer.

Parsing is shared machinery: a DECISION line is extracted from raw model
output for either arm. Enforcement is the specialist arm's policy layer,
ported from the clinic-plugin-pack escalation semantics (emergency context
-> human-only tier; unresolved information -> confirm tier): it acts on the
model's OWN declared red-flag screen and missing-information list.

  - declared red flags present + DECISION == DISCHARGE -> ESCALATE
  - declared missing info present + DECISION == DISCHARGE -> ABSTAIN

Enforcement never fires in the other direction (it cannot turn an ESCALATE
or ABSTAIN into a DISCHARGE), and every override is counted by the metrics
layer. Known limit, stated in the paper: if the model fails to declare a
red flag that is present in the vignette, no override fires.
"""

from __future__ import annotations

import re

DECISIONS = ("DISCHARGE", "ESCALATE", "ABSTAIN")
_DECISION_RE = re.compile(r"DECISION:\s*(DISCHARGE|ESCALATE|ABSTAIN)", re.IGNORECASE)
_EMPTY_VALUES = {"", "NONE", "NONE.", "N/A", "NA", "-"}


def parse_decision(raw_output: str) -> str | None:
    """Return the last DECISION value in the output, or None if unparseable."""
    matches = _DECISION_RE.findall(raw_output or "")
    if not matches:
        return None
    return matches[-1].upper()


def _field_value(raw_output: str, field: str) -> str | None:
    match = re.search(rf"^{field}:\s*(.+)$", raw_output or "", re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _declared_items(raw_output: str, field: str) -> list[str]:
    """Items the model declared for a field; [] when it declared NONE/absent."""
    value = _field_value(raw_output, field)
    if value is None:
        return []
    if value.strip().upper() in _EMPTY_VALUES:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_specialist_fields(raw_output: str) -> dict:
    """Extract the specialist arm's declared screen from its raw output."""
    return {
        "red_flags": _declared_items(raw_output, "RED_FLAGS"),
        "missing": _declared_items(raw_output, "MISSING"),
        "decision": parse_decision(raw_output),
    }


def enforce_policy(parsed: dict) -> tuple[str | None, bool]:
    """Apply Rules 1-2 to a parsed specialist output.

    Returns (final_decision, overridden). Unparseable decisions pass through
    unchanged (they are scored as invalid by the metrics layer, never
    silently repaired).
    """
    decision = parsed.get("decision")
    if decision != "DISCHARGE":
        return decision, False
    if parsed.get("red_flags"):
        return "ESCALATE", True
    if parsed.get("missing"):
        return "ABSTAIN", True
    return decision, False
