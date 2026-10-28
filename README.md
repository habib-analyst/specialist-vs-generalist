# specialist-vs-generalist

**Does a safety layer, not model size, drive discharge safety?**

A discharge-safety vignette harness that runs the *same* safety-critical
clinical vignettes through the *same* small local model in two arms:

- **Generalist (G):** the bare model with a minimal instruction.
- **Specialist (S):** the *identical* model wrapped in a discharge-safety
  policy ported from the clinic-plugin-pack escalation rules — a mandatory
  red-flag screen, an abstention rule for decision-critical missing
  information, and a deterministic enforcement layer that acts on the
  model's own declared screen.

The only independent variable is the policy layer. The claim under test is
that the safety layer, not model size, is what drives discharge safety.
Design, metrics and pass/fail bars were frozen in `PREREG.md` before any
model run.

Motivation: specialist-vs-generalist clinical comparisons (e.g. the 2026
Lynch-style head-to-heads) compare *different models*. This harness asks a
different, cheaper question with a cleaner design: holding the model fixed,
how much safety does a policy layer buy?

## Results (headline run, 2026-10-28)

Model: Qwen/Qwen2.5-0.5B-Instruct, run locally on CPU (greedy decoding).
36 synthetic vignettes: 14 ESCALATE, 12 DISCHARGE, 10 ABSTAIN.

| Metric | Generalist | Specialist (prompt only) | Specialist (full system) |
|---|---|---|---|
| Unsafe-discharge rate (ESCALATE cases, lower is safer) | 0.0% | 21.4% | 0.0% |
| Escalation recall (ESCALATE cases) | 100.0% | 42.9% | 57.1% |
| Abstention appropriateness (ABSTAIN cases) | 0.0% | 40.0% | 70.0% |
| Safe cases discharged (DISCHARGE cases) | 16.7% | 50.0% | 16.7% |
| Overall accuracy | 44.4% | 44.4% | 47.2% |
| Decision parse rate | 100.0% | 97.2% | 97.2% |

Unsafe discharges: G 0/14 vs S 0/14; policy overrides: 11.
Pre-registered bars: **B1 FAIL, B2 FAIL, B3 FAIL, B4 PASS** (see below).

*Exploratory (not pre-registered):* the generalist arm on Qwen2.5-1.5B
(bf16) discharged 83.3% of safe cases with the best accuracy of any arm
(55.6%), but a 75.0% parse rate and 4 premature commitments on
missing-information cases — and still zero unsafe discharges. Details in
`results/exploratory_1p5b_generalist_summary.json` and the paper.

**Read the headline honestly:** the bare model's 0% unsafe rate is
degenerate, not discriminating — it escalated 34 of 36 cases, including 10
of the 12 genuinely safe ones and all 10 abstain cases. The policy *prompt
alone* made the model willing to commit in both directions (safe discharges
rose to 50%, but 3 unsafe discharges appeared). The deterministic
*enforcement* layer removed all 3 unsafe discharges and 4 of 5 premature
commitments (11 overrides) — at the cost of also overriding 4 correct
discharges where the model over-declared flags. Against the frozen bars,
which assumed a discriminating baseline, the specialist system did **not**
win: B1–B3 failed. What the harness actually demonstrates is narrower and,
we think, more useful: at this scale the bare model's "safety" is refusal
to decide, a policy prompt trades that for commitment (good and bad), and
only the deterministic layer reliably separates the two.

Full per-vignette raw outputs: `results/raw_outputs.jsonl`.
Machine-readable summary: `results/summary.json`.

## Method

- **Vignettes** (`data/vignettes.json`): fully synthetic discharge-decision
  cases written for this harness — no real patient data. ESCALATE cases span
  14 red-flag presentations (sepsis, ACS, stroke, GI bleed, respiratory
  failure, severe pre-eclampsia, paediatric sepsis, unresolved DKA,
  post-PCI bleeding, delirium, biphasic anaphylaxis, necrotising infection,
  suicide risk). ABSTAIN cases are built around pending/missing
  decision-critical information (second troponin, final cultures, repeat
  haemoglobin, imaging report, contradictory allergy record, unconfirmed
  anticoagulation plan, ...). DISCHARGE cases include distractors whose
  scary presentation has been fully worked up and ruled out.
- **Specialist policy** (`policy/discharge_safety_policy.md`): the
  clinic-plugin-pack `escalate` semantics ported to discharge — a red flag
  moves the case to a human-only tier (must ESCALATE), missing
  decision-critical information moves it to a confirm tier (must ABSTAIN),
  and only a fully clear screen permits DISCHARGE. The harness enforces
  these rules deterministically on the model's own declared screen and
  reports pre-override (prompt-only) and post-override (full system)
  numbers separately.
- **Metrics** (frozen in PREREG.md): unsafe-discharge rate on ESCALATE
  cases (primary), escalation recall, abstention appropriateness on
  ABSTAIN cases, over-caution on DISCHARGE cases, overall accuracy, parse
  rate. Unparseable outputs are counted and scored as incorrect, never
  dropped.

## Run it

```sh
# 1. Download the weights ($0, ~1 GB) with curl:
mkdir -p models && cd models
BASE=https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/resolve/main
for f in config.json generation_config.json tokenizer.json \
         tokenizer_config.json vocab.json merges.txt model.safetensors; do
  curl -sSL -f -O "$BASE/$f"
done
cd ..

# 2. Run the headline evaluation (CPU, greedy):
./run_eval.sh

# 3. Machinery tests (no model needed):
python3 -m pytest
```

## Honest limits

- **Small local model.** A 0.5B model is far weaker than frontier clinical
  systems; absolute numbers say little about them. The *comparison* (same
  model, policy on/off) is the result.
- **Synthetic vignettes.** 36 hand-written cases with author-assigned gold
  labels, not clinician-adjudicated real cases. Label choices are
  documented per case (`rationale` field) so they can be challenged.
- **Self-declared screen.** Enforcement acts on the red flags the model
  itself declares. If the model misses a red flag in its screen, no
  override fires — the enforcement layer cannot fix extraction failures,
  and the results show exactly how often that happens.
- **Harness demonstration, not a clinical claim.** Nothing here validates
  any system for real discharge decisions.

## Layout

- `data/vignettes.json` — the vignette set (only `text` is shown to models)
- `policy/discharge_safety_policy.md` — the specialist policy + provenance
- `src/svg/` — harness: `vignettes.py` (loading/validation), `prompts.py`
  (frozen arm prompts), `policy.py` (parsing + enforcement), `metrics.py`,
  `runner.py` (local transformers runner), `run_eval.py` (headline run)
- `tests/` — machinery tests (18, no model required)
- `results/` — raw outputs + summary of the headline run
- `PREREG.md` — frozen design, metrics, bars · `KILLGATE.md` — $0 and
  novelty gates

MIT license. Part of a portfolio of measured, kill-gated builds by
Habib Ur Rehman.
