#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r academic-review/requirements.txt
python academic-review/scripts/validate_inputs.py
python academic-review/scripts/bootstrap_literature.py --mode open --resume
