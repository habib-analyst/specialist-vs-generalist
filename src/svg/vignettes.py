"""Vignette loading and validation.

The vignette set is fully synthetic (no real patient data). Gold labels were
fixed before any model run. Validation enforces the documentation contract:
every ESCALATE case documents at least one red flag, every ABSTAIN case
documents what information is missing, ids are unique, and only the `text`
field is ever shown to a model.
"""

from __future__ import annotations

import json
from pathlib import Path

LABELS = ("DISCHARGE", "ESCALATE", "ABSTAIN")
REQUIRED_FIELDS = (
    "id",
    "family",
    "gold",
    "text",
    "red_flags",
    "missing_info",
    "rationale",
)


def load_vignettes(path: str | Path) -> list[dict]:
    """Load and validate the vignette set; raise ValueError on any defect."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    vignettes = data["vignettes"]
    validate_vignettes(vignettes)
    return vignettes


def validate_vignettes(vignettes: list[dict]) -> None:
    if len(vignettes) < 30:
        raise ValueError(f"need at least 30 vignettes, got {len(vignettes)}")
    seen: set[str] = set()
    for v in vignettes:
        for field in REQUIRED_FIELDS:
            if field not in v:
                raise ValueError(f"{v.get('id', '?')}: missing field {field}")
        if v["id"] in seen:
            raise ValueError(f"duplicate vignette id {v['id']}")
        seen.add(v["id"])
        if v["gold"] not in LABELS:
            raise ValueError(f"{v['id']}: bad gold label {v['gold']!r}")
        if not v["text"].strip():
            raise ValueError(f"{v['id']}: empty text")
        if v["gold"] == "ESCALATE" and not v["red_flags"]:
            raise ValueError(f"{v['id']}: ESCALATE case must document red flags")
        if v["gold"] == "ABSTAIN" and not v["missing_info"]:
            raise ValueError(f"{v['id']}: ABSTAIN case must document missing info")
        if v["gold"] == "DISCHARGE" and v["red_flags"]:
            raise ValueError(f"{v['id']}: DISCHARGE case must not list red flags")


def label_counts(vignettes: list[dict]) -> dict[str, int]:
    counts = {label: 0 for label in LABELS}
    for v in vignettes:
        counts[v["gold"]] += 1
    return counts
