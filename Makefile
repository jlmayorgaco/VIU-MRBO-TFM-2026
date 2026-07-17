PYTHON ?= python
PIP ?= $(PYTHON) -m pip
export PYTHONPATH := src

.PHONY: install test check compile smoke-sp0 smoke-sp1 smoke-sp5 cargo-smoke thesis clean

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

smoke-sp5:
	$(PYTHON) -m viu_mrob_tfm.cli.run_sp5 experiments/configs/sp5_payload_transport_smoke.yaml

cargo-smoke:
	$(PYTHON) -m viu_mrob_tfm.cli.run_cargo_e2e experiments/configs/cargo_e2e_smoke.yaml

thesis:
	powershell -ExecutionPolicy Bypass -File thesis/build.ps1

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]"
