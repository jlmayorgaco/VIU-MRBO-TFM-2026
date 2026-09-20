PYTHON ?= python
PIP ?= $(PYTHON) -m pip
export PYTHONPATH := src

.PHONY: install test check compile smoke-sp0 smoke-sp1 smoke-sp1-canonical smoke-sp1-full smoke-sp1-conference sp1-conference smoke-sp5 cargo-smoke thesis clean

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

compile:
	$(PYTHON) -m compileall -q src tests

check: compile test

smoke-sp0:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp0_theory --smoke

smoke-sp1:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp1_theory --smoke

smoke-sp1-canonical:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp1_canonical --config experiments/configs/sp1_canonical_smoke.yaml

smoke-sp1-full:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp1_full --canonical-smoke

smoke-sp1-conference:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp1_conference --config experiments/configs/sp1_conference_smoke.yaml

sp1-conference:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp1_conference --config experiments/configs/sp1_conference_v1.yaml --resume

smoke-sp5:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp5 experiments/configs/sp5_payload_transport_smoke.yaml

cargo-smoke:
	$(PYTHON) -m viu_mrob_tfm.cli.run_cargo_e2e experiments/configs/cargo_e2e_smoke.yaml

thesis:
	powershell -ExecutionPolicy Bypass -File thesis/build.ps1

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]"
