"""specialist-vs-generalist: discharge-safety harness.

Runs identical synthetic discharge vignettes through a small local model in
two arms that differ ONLY in the safety-policy layer:

  G (generalist) - bare model, minimal instruction.
  S (specialist) - same model + clinic-plugin-pack style discharge-safety
                   policy (mandatory red-flag screen, abstention rule,
                   deterministic enforcement).

The claim under test: the safety layer, not model size, drives discharge
safety. See PREREG.md for the frozen design and bars.
"""

__all__ = ["vignettes", "prompts", "policy", "metrics", "runner"]
