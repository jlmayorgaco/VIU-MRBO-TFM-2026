PYTHON ?= python
PIP ?= $(PYTHON) -m pip
EXP ?= experiments/exp-001-baseline-nominal/config.yaml
REPORT_DIR := docs/doc-05-final-report
export PYTHONPATH := src

.PHONY: install test lint report-pdf validate-suite smoke-exp clean-generated clean

install:
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m compileall src tests scripts

report-pdf:
	$(PYTHON) -c "from pathlib import Path; Path('$(REPORT_DIR)/build').mkdir(parents=True, exist_ok=True)"
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(REPORT_DIR) && bibtex build/main
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	$(PYTHON) -c "import shutil; shutil.copyfile('$(REPORT_DIR)/build/main.pdf', '$(REPORT_DIR)/main.pdf')"

validate-suite:
	$(PYTHON) -m viu_mrob_tfm.validation.suite

smoke-exp:
	$(PYTHON) scripts/run_experiment.py --config $(EXP)

clean-generated:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in [Path('docs/doc-05-final-report/build'), Path('results/raw/_pytest_runner_smoke')] if path.exists()]"

clean: clean-generated

