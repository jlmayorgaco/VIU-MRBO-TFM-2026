PYTHON ?= python
PIP ?= $(PYTHON) -m pip
EXP ?= experiments/exp-001-baseline-nominal/config.yaml
PROPOSAL_DIR  := docs/doc-01-proposal
MIDREPORT_DIR := docs/doc-02-mid-report

.PHONY: install test lint clean proposal-pdf proposal-methodology-pdf mid-report-pdf figures run-exp

install:
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m compileall src tests scripts

clean:
	$(PYTHON) scripts/clean_results.py --all
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in [Path('.pytest_cache'), Path('docs/doc-01-proposal/build'), Path('docs/doc-02-mid-report/build'), Path('docs/doc-03-advance-report/build'), Path('docs/thesis-final/build')] if path.exists()]"
	$(PYTHON) -c "from pathlib import Path; [path.mkdir(parents=True, exist_ok=True) for path in [Path('docs/doc-01-proposal/build'), Path('docs/doc-02-mid-report/build'), Path('docs/doc-03-advance-report/build'), Path('docs/thesis-final/build')]]; [Path(path, '.gitkeep').touch() for path in [Path('docs/doc-01-proposal/build'), Path('docs/doc-02-mid-report/build'), Path('docs/doc-03-advance-report/build'), Path('docs/thesis-final/build')]]"

proposal-pdf:
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(PROPOSAL_DIR) && bibtex build/main
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex

proposal-methodology-pdf:
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main_hasta_metodologia.tex
	cd $(PROPOSAL_DIR) && bibtex build/main_hasta_metodologia
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main_hasta_metodologia.tex
	cd $(PROPOSAL_DIR) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main_hasta_metodologia.tex

mid-report-pdf:
	cd $(MIDREPORT_DIR) && lualatex -interaction=nonstopmode -output-directory=build main.tex
	cd $(MIDREPORT_DIR) && bibtex build/main
	cd $(MIDREPORT_DIR) && lualatex -interaction=nonstopmode -output-directory=build main.tex
	cd $(MIDREPORT_DIR) && lualatex -interaction=nonstopmode -output-directory=build main.tex

figures:
	$(PYTHON) scripts/generate_figures.py

run-exp:
	$(PYTHON) scripts/run_experiment.py --config $(EXP)
