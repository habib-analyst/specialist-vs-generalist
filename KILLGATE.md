# KILLGATE — specialist-vs-generalist (discharge-safety harness)

Date: 2026-10-28. Gates checked BEFORE build, per foundry rules.

## Gate 1 — $0 / local-model gate
Requirement: a real open-weight model, downloaded for $0, that actually runs
on this VM (2 cores, ~7.9 GB RAM) and produces the eval outputs. Scripted or
hand-written "model outputs" are forbidden.
- Environment already has torch 2.13.0+cpu + transformers 5.19.0 installed.
- Candidate: Qwen/Qwen2.5-0.5B-Instruct (Apache-2.0, ~1 GB fp16 weights),
  fetched file-by-file with curl from huggingface.co (Python HTTP hangs
  through this VM's proxy; curl works). Fallback if 0.5B cannot follow the
  output contract: Qwen2.5-1.5B-Instruct in bf16.
- Verdict: PASSED only when the smoke test in logs/ shows real generations
  from the downloaded weights (see models/ + logs/smoke_test.txt).
- EVIDENCE (2026-10-28): Qwen2.5-0.5B-Instruct model.safetensors downloaded
  by curl, byte-exact (988,097,824 bytes, matches the HF x-linked-size).
  Smoke test (logs/smoke_test.txt): weights load in transformers and produce
  real generations for both arm prompts. One throwaway case exposed a
  format fragility (the model echoed the policy's screen list and looped to
  the token cap), so the PREREG format pilot was run on 6 throwaway
  vignettes: specialist contract parse 6/6, generalist 3/3 — at/above the
  90% bar, so the preregistered 1.5B fallback was NOT triggered and the
  headline run uses the 0.5B in both arms, as frozen. (The 1.5B weights
  were also downloaded — 3,087,467,144 bytes, byte-exact — and are reserved
  for a clearly-labelled exploratory arm only.)

## Gate 2 — novelty / prior-art gate
Searches run 2026-10-28 (web): discharge-safety LLM eval harnesses,
discharge-decision benchmarks, clinical vignette triage/escalation harnesses.
What exists:
- "Discharge Me!" shared task and the discharge-summary/letter generation
  literature (incl. ICU discharge-summary simplification): text GENERATION
  quality (BLEU/ROUGE/factuality of notes). None of it scores the discharge
  DECISION (send home vs escalate vs abstain) for safety.
- Front-door TRIAGE vignette studies (Mount Sinai / Nature Medicine triage
  scenarios; a 48-vignette diagnosis+triage study; a shoulder/elbow red-flag
  vignette study; Amazon PatientAgentBench): different decision point
  (presenting symptoms -> care level, mostly conversational/API models),
  different arms (model vs model, or prompt framing). None isolates a policy
  layer as the sole independent variable.
- Medical safety benchmarks (MedSafetyBench, MedHarm, CARES, DiagSafe,
  SafetyBench): harmful-query refusal / diagnostic safety. Not discharge.
- Lynch-style specialist-vs-generalist clinical comparisons compare
  DIFFERENT models (a specialist system vs a generalist model).
Differentiation of this build (all four required):
  1. Decision point is DISCHARGE (post-admission send-home decision), with
     unsafe-discharge rate on red-flag cases as the primary metric.
  2. The ONLY independent variable is the safety-policy layer: identical
     base model, identical vignettes, identical decoding in both arms.
     Arm S = same model + clinic-plugin-pack escalation policy (prompt
     policy + structured red-flag screen + deterministic enforcement).
  3. Fully local, $0, reproducible: small open-weight model on CPU,
     greedy decoding, all raw outputs published.
  4. Abstention is a scored first-class outcome (pending/missing critical
     information cases), not an error bucket.
Verdict: PASS — no released harness found with this design; build proceeds.

## Honest scope note
This is a harness demonstration on synthetic vignettes with a small local
model. It is not a clinical claim and must never be presented as one.
