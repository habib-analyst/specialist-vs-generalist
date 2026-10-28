# The Safety Layer, Not the Model: A Discharge-Safety Vignette Harness

**Habib Ur Rehman** — 2026-10-28
Build: `specialist-vs-generalist` (PIPELINE_25). Status: harness paper —
a measured demonstration on synthetic data, not a clinical claim.

## Abstract

Specialist-vs-generalist clinical AI comparisons vary the model. This
harness varies only the *policy layer*: 36 synthetic discharge-decision
vignettes were run through one small local model (Qwen2.5-0.5B-Instruct,
CPU, greedy decoding) in two arms — the bare model (generalist) and the
identical model wrapped in a discharge-safety policy ported from the
clinic-plugin-pack escalation rules (mandatory red-flag screen, abstention
rule for decision-critical missing information, deterministic enforcement
on the model's own declared screen). Design, metrics and bars were
pre-registered (PREREG.md) before any run.

On the frozen bars the specialist system did **not** beat the generalist
(B1–B3 fail; B4 passes): the bare 0.5B model's dominant strategy is to
escalate almost everything (34/36), so its 0% unsafe-discharge rate is
degenerate rather than discriminating, and there was no unsafe behaviour
for the policy to remove. The policy prompt alone made the model *more*
willing to commit — including 3 unsafe discharges the bare model never
made — while the deterministic enforcement layer removed all 3 unsafe
discharges and 4 of 5 premature commitments (11 overrides), at the cost of
also overriding 4 correct discharges. The measured story is therefore
about *which part* of a safety layer does what, not a win for the layer
as a whole.

## 1. Motivation

When a hospital patient is sent home too early, the failure is a decision
failure, not a documentation failure. Yet the existing LLM literature on
discharge is overwhelmingly about *generating discharge text* (the
"Discharge Me!" task; discharge-summary quality studies), and the red-flag
vignette literature is about *front-door triage* of presenting symptoms.
The discharge decision itself — discharge, escalate, or abstain — has no
released evaluation harness that we could find (see KILLGATE.md for the
search record), and no study we found isolates a policy/guardrail layer as
the sole independent variable on a fixed base model. Lynch-style 2026
specialist-vs-generalist head-to-heads compare different models; if a
specialist *system* wins, the win is confounded between model and wrapper.
This harness removes the confound in the cheapest possible setting: one
small open-weight model, run locally for $0, with the policy layer as the
only difference between arms.

## 2. Method

**Vignettes.** 36 synthetic cases written for this harness (no real patient
data), each a discharge-round note ending at the discharge decision. Gold
labels were fixed before any model run: 14 ESCALATE (red-flag
presentations: sepsis ×3 variants, acute coronary syndrome, acute stroke,
ongoing GI bleeding, respiratory failure, severe pre-eclampsia, paediatric
sepsis, unresolved DKA, post-PCI haemorrhage, acute delirium, biphasic
anaphylaxis, necrotising soft-tissue infection, suicide risk), 12
DISCHARGE (including distractors whose alarming presentation was fully
worked up and ruled out, e.g. serial-negative-troponin chest pain), 10
ABSTAIN (decision-critical information pending or contradictory: second
troponin, final blood cultures, repeat haemoglobin, CT report, newborn
bilirubin, allergy-record contradiction, unconfirmed anticoagulation plan,
awaiting psychiatry review, absent observations, unresolved home support).
Every label carries a documented rationale in the data file.

**Arms.** Generalist: minimal instruction + output contract. Specialist:
the same model with the discharge-safety policy as system prompt. The
policy ports the clinic-plugin-pack `escalate` block — emergency context →
human-only tier; unresolved information → confirm tier — into a mandatory
11-item red-flag screen, a decision-critical information checklist, and
three ordered rules (red flag → ESCALATE; missing critical information →
ABSTAIN; only a fully clear screen → DISCHARGE). The model must declare
its screen (`RED_FLAGS:`, `MISSING:`) before its decision, and the harness
then enforces the rules deterministically on that declaration: a DISCHARGE
declared alongside red flags is overridden to ESCALATE; alongside missing
information, to ABSTAIN. Pre-override (prompt-only) and post-override
(full-system) specialist results are reported separately, so the prompt
effect and the enforcement effect are not conflated.

**Protocol.** Greedy decoding, seed fixed, one run per vignette per arm,
token caps 128 (G) / 320 (S). Prompts, vignettes, metrics and bars frozen
in PREREG.md. A format pilot on 6 throwaway vignettes (never scored for
safety) confirmed both arms' output contracts parse at ≥90% on the 0.5B
model (specialist 6/6, generalist 3/3), so the pre-registered 1.5B format
fallback was not triggered. Unparseable outputs are counted, published in
the raw output file, and scored as incorrect — never dropped.

**Metrics.** Primary: unsafe-discharge rate on ESCALATE cases. Secondary:
escalation recall; abstention appropriateness on ABSTAIN cases;
over-caution on DISCHARGE cases; overall accuracy; parse rate. Bars
(frozen): B1 specialist unsafe rate ≤ generalist − 20pp; B2 specialist
escalation recall ≥ generalist; B3 specialist still discharges ≥50% of
safe cases; B4 parse rate ≥90% in both arms.

## 3. Results

| Metric | Generalist | Specialist (prompt only) | Specialist (full system) |
|---|---|---|---|
| Unsafe-discharge rate (ESCALATE cases, lower is safer) | 0.0% | 21.4% | 0.0% |
| Escalation recall (ESCALATE cases) | 100.0% | 42.9% | 57.1% |
| Abstention appropriateness (ABSTAIN cases) | 0.0% | 40.0% | 70.0% |
| Safe cases discharged (DISCHARGE cases) | 16.7% | 50.0% | 16.7% |
| Overall accuracy | 44.4% | 44.4% | 47.2% |
| Decision parse rate | 100.0% | 97.2% | 97.2% |

Unsafe discharges: G 0/14 vs S 0/14; policy overrides: 11. Bars: B1 FAIL,
B2 FAIL, B3 FAIL, B4 PASS. Full confusion matrices and per-case raw outputs
are in the repository's `results/`.

Three observations carry the result.

**1. The baseline's safety is degenerate.** The bare model decided
ESCALATE on 34 of 36 vignettes — all 14 red-flag cases, but also 10 of 12
safe cases and all 10 information-missing cases (abstention
appropriateness 0%). Its perfect unsafe-discharge rate and escalation
recall are what a constant "escalate" classifier would score; it
demonstrates refusal to decide, not discrimination. Any safety comparison
against such a baseline on the unsafe metric alone is vacuous, which is
exactly why B1 was unachievable: 0% cannot be beaten by 20 points.

**2. The policy prompt is double-edged.** Prompt-only, the specialist
became the most *decisive* arm: it discharged 50% of safe cases (vs 16.7%)
and identified 40% of abstain cases — and it also produced the run's only
unsafe discharges (3/14, 21.4%) plus 5 premature commitments on abstain
cases. Structuring the decision (screen first, then decide) increased
willingness to commit in both directions. A prompt is not a guardrail.

**3. The deterministic layer is the guardrail — with a measurable cost.**
Enforcement fired 11 times. It eliminated all 3 unsafe discharges
(21.4% → 0%) and 4 of the 5 premature commitments, lifting abstention
appropriateness to 70% and overall accuracy to the run's best (47.2%).
It also overrode 4 *correct* discharges, because on safe cases the model
often declared red flags or missing items that did not withstand its own
decision — the enforcer trusts the declaration, so declaration noise
becomes decision noise (safe discharges fell back to 16.7%, failing B3).
One premature commitment survived enforcement: a case where the model
discharged with a clean declared screen, an extraction failure the design
explicitly cannot catch.

## 4. Discussion

The pre-registered claim — that the specialist system beats the bare model
on the frozen bars — is **not supported** on this model and vignette set,
and we report it as such. What the harness supports instead is a
decomposition claim: in a small local model, (a) unaided "safety" can be
pure escalation bias, invisible if only the unsafe rate is reported;
(b) policy prompting changes the decision distribution substantially but
unsafely in both directions; (c) deterministic enforcement on a declared
screen is the component that reliably removes the most dangerous errors,
and its cost is bounded by the quality of the model's own declarations.
For builders of clinic-style plugin packs, the practical implication is
that the pack's value sits in its enforceable rules, not in its prompt
text — and that any evaluation of such a pack must report over-caution
metrics alongside unsafe-error metrics, or a constant-escalate baseline
will appear unbeatable.

**Exploratory follow-up (not part of the pre-registered headline).** The
headline's vacuity problem — a baseline that never discharges — motivated
one clearly-labelled exploratory arm: the *generalist only*, run on
Qwen2.5-1.5B-Instruct (bf16), identical vignettes, prompts and decoding.
Tripling model size changed the baseline's character: the 1.5B generalist
discharged 83.3% of safe cases (vs 16.7% at 0.5B) and reached the best
overall accuracy of any arm (55.6%), but its parse rate fell to 75.0%
(9/36 outputs had no usable DECISION line, including 5 of 14 red-flag
cases — in a deployment, an unparseable red-flag response is its own
failure mode), its escalation recall was 64.3%, and it still produced
**zero** unsafe discharges. It did, however, commit prematurely on 4 of 10
missing-information cases (abstention appropriateness 10%), where the
0.5B specialist full system committed only 1. Reading both runs together:
at these scales, model size bought decisiveness on clear cases; the
discipline to *not* decide when information is missing came only from the
policy layer; and no local model we could run actually discharged a
red-flag case unaided, so the headline unsafe-discharge comparison awaits
a baseline that takes that risk. Raw outputs:
`results/exploratory_1p5b_generalist.jsonl`.

Two design notes for whoever extends this harness. First, bars must be
written against a *discriminating* baseline: a pre-flight check that the
generalist discharges at least some safe cases would have flagged B1's
vacuity before the run (our format pilot checked parseability, not
decision distribution — a gap we record here). Second, the obvious next
experiment is a model strong enough to actually discharge unsafe cases
unaided; only then does the unsafe-discharge comparison become the
informative test this harness was built for.

## 5. Limits

- **Small local model.** A 0.5B model is far weaker than frontier clinical
  systems; its absolute error rates say nothing about them. The estimand
  is the *within-model* policy effect.
- **Synthetic vignettes, single author.** Gold labels are documented and
  challengeable, but they are not clinician-adjudicated and may encode the
  author's assumptions — including, unavoidably, assumptions that align
  with the policy's screen. The DISCHARGE distractor cases and the ABSTAIN
  class exist to punish blind policy-following, but an independently
  authored vignette set would be a stronger test.
- **Self-declared screen.** Enforcement consumes the model's own red-flag
  declaration. Extraction failures pass through silently; the pre/post
  override split quantifies how much of the system's safety comes from the
  prompt changing decisions vs the enforcer catching contradictions.
- **One run, greedy.** No sampling variance is estimated; with n=14 in the
  primary subset, percentage-point differences have wide uncertainty and
  should be read as directional.
- **Not a clinical claim.** Nothing here validates any system for real
  discharge decisions.

## 6. Reproducibility

All code, vignettes, the policy file, the pre-registration, raw model
outputs for every vignette and arm, and the summary with model-file
SHA-256 hashes are in the repository. Weights are downloaded for $0 from
Hugging Face (Qwen/Qwen2.5-0.5B-Instruct); the full run is CPU-only.
