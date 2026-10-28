"""Headline evaluation run. Design and bars are frozen in PREREG.md.

Usage:
    python -m svg.run_eval --model-dir <local weights dir> \
        --vignettes data/vignettes.json --policy policy/discharge_safety_policy.md \
        --out-dir results

Writes results/raw_outputs.jsonl (every raw generation, both arms) and
results/summary.json (metrics, bars, model hashes, prompt hashes).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from . import prompts as prompts_mod
from .metrics import arm_metrics, check_bars
from .policy import enforce_policy, parse_decision, parse_specialist_fields
from .runner import LocalModel, model_file_hashes
from .vignettes import label_counts, load_vignettes

GENERALIST_MAX_TOKENS = 128
SPECIALIST_MAX_TOKENS = 320


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def run_eval(model_dir: Path, vignettes_path: Path, policy_path: Path, out_dir: Path) -> dict:
    vignettes = load_vignettes(vignettes_path)
    policy_text = policy_path.read_text(encoding="utf-8")
    model = LocalModel(model_dir)

    raw_rows: list[dict] = []
    g_records, s_pre_records, s_post_records = [], [], []
    overrides = 0

    for v in vignettes:
        g_raw = model.generate(
            prompts_mod.generalist_messages(v["text"]), GENERALIST_MAX_TOKENS
        )
        g_decision = parse_decision(g_raw)
        g_records.append({"gold": v["gold"], "decision": g_decision})
        raw_rows.append(
            {"id": v["id"], "gold": v["gold"], "arm": "generalist", "raw": g_raw,
             "decision": g_decision}
        )

        s_raw = model.generate(
            prompts_mod.specialist_messages(v["text"], policy_text), SPECIALIST_MAX_TOKENS
        )
        fields = parse_specialist_fields(s_raw)
        s_final, overridden = enforce_policy(fields)
        overrides += int(overridden)
        s_pre_records.append({"gold": v["gold"], "decision": fields["decision"]})
        s_post_records.append({"gold": v["gold"], "decision": s_final})
        raw_rows.append(
            {"id": v["id"], "gold": v["gold"], "arm": "specialist", "raw": s_raw,
             "declared_red_flags": fields["red_flags"],
             "declared_missing": fields["missing"],
             "decision_pre_override": fields["decision"],
             "decision": s_final, "overridden": overridden}
        )
        print(f"{v['id']} gold={v['gold']:<9} G={g_decision} "
              f"S_pre={fields['decision']} S={s_final} override={overridden}", flush=True)

    g_metrics = arm_metrics(g_records)
    s_pre_metrics = arm_metrics(s_pre_records)
    s_metrics = arm_metrics(s_post_records)
    bars = check_bars(g_metrics, s_metrics)

    summary = {
        "model_dir": str(model_dir),
        "model_files": model_file_hashes(model_dir),
        "decoding": {"do_sample": False, "seed": 0,
                     "generalist_max_new_tokens": GENERALIST_MAX_TOKENS,
                     "specialist_max_new_tokens": SPECIALIST_MAX_TOKENS},
        "prompt_hashes": {
            "generalist_system": _hash(prompts_mod.GENERALIST_SYSTEM),
            "generalist_user_template": _hash(prompts_mod.GENERALIST_USER_TEMPLATE),
            "specialist_system_template": _hash(prompts_mod.SPECIALIST_SYSTEM_TEMPLATE),
            "specialist_user_template": _hash(prompts_mod.SPECIALIST_USER_TEMPLATE),
            "policy_file": _hash(policy_text),
        },
        "label_counts": label_counts(vignettes),
        "generalist": g_metrics,
        "specialist_pre_override": s_pre_metrics,
        "specialist": s_metrics,
        "specialist_overrides": overrides,
        "bars": bars,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "raw_outputs.jsonl", "w", encoding="utf-8") as fh:
        for row in raw_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--vignettes", default="data/vignettes.json")
    parser.add_argument("--policy", default="policy/discharge_safety_policy.md")
    parser.add_argument("--out-dir", default="results")
    args = parser.parse_args()
    start = time.time()
    summary = run_eval(
        Path(args.model_dir), Path(args.vignettes), Path(args.policy), Path(args.out_dir)
    )
    print(f"\nElapsed: {time.time() - start:.0f}s")
    print(json.dumps(summary["bars"], indent=2))
    print("G unsafe:", summary["generalist"]["unsafe_discharge_rate"],
          "| S unsafe:", summary["specialist"]["unsafe_discharge_rate"])


if __name__ == "__main__":
    main()
