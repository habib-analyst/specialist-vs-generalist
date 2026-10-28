#!/bin/sh
# Headline run (design frozen in PREREG.md). Expects local weights in ./models
# (download instructions in README.md).
set -e
cd "$(dirname "$0")"
PYTHONPATH=src python3 -m svg.run_eval --model-dir models \
  --vignettes data/vignettes.json \
  --policy policy/discharge_safety_policy.md \
  --out-dir results
