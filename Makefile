PYTHON ?= python
PIP ?= $(PYTHON) -m pip
EXP ?= experiments/exp-001-baseline-nominal/config.yaml
REPORT_DIR := docs/doc-05-final-report
FILE ?= $(REPORT_DIR)/main.tex
SIMILARITY_REPORT ?=
REQUIRE_SIMILARITY ?= 0
REQUIRE_AI_DECLARATION ?= 1
STRICT ?= 0
export PYTHONPATH := src

SUBMIT_READY_ARGS = --file "$(FILE)"
ifneq ($(strip $(SIMILARITY_REPORT)),)
SUBMIT_READY_ARGS += --similarity-report "$(SIMILARITY_REPORT)"
endif
ifeq ($(REQUIRE_SIMILARITY),1)
SUBMIT_READY_ARGS += --require-similarity-report
endif
ifeq ($(REQUIRE_AI_DECLARATION),0)
SUBMIT_READY_ARGS += --no-require-ai-declaration
endif
ifeq ($(STRICT),1)
SUBMIT_READY_ARGS += --strict
endif

.PHONY: install test test-fast test-smoke test-full lint report-pdf build-report validate-suite smoke-exp run-canonical method-matrix regime-map theory-validation stats-annex figures-paper video-catalog sp9 thesis reproduce-figures submit-ready submit-check clean-generated clean

install:
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest -q

test-fast:
	$(PYTHON) -m pytest tests/test_sp1_pipeline.py tests/test_sp2_pipeline.py tests/test_sp3_pipeline.py tests/test_sp4_pipeline.py tests/test_sp5_pipeline.py tests/test_sp6_pipeline.py tests/test_sp7_pipeline.py tests/test_sp8_pipeline.py -q

test-smoke:
	$(PYTHON) scripts/run_sp1_experiment.py configs/experiments/sp1/SP1_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp2_experiment.py configs/experiments/sp2/SP2_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp3_experiment.py configs/experiments/sp3/SP3_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp4_experiment.py configs/experiments/sp4/SP4_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp5_experiment.py configs/experiments/sp5/SP5_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp6_experiment.py configs/experiments/sp6/SP6_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp7_experiment.py configs/experiments/sp7/SP7_DEBUG_smoke.yaml
	$(PYTHON) scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_DEBUG_smoke.yaml

test-full: test-fast
	$(PYTHON) -m viu_mrob_tfm.validation.suite

lint:
	$(PYTHON) -m compileall src tests scripts

report-pdf:
	$(PYTHON) -c "from pathlib import Path; Path('$(REPORT_DIR)/build').mkdir(parents=True, exist_ok=True)"
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(REPORT_DIR) && biber build/main
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	cd $(REPORT_DIR) && lualatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
	$(PYTHON) -c "import shutil; shutil.copyfile('$(REPORT_DIR)/build/main.pdf', '$(REPORT_DIR)/main.pdf')"

build-report: report-pdf
	$(PYTHON) scripts/generate_pipeline_pdfs.py

method-matrix:
	$(PYTHON) scripts/generate_method_matrix.py

regime-map:
	$(PYTHON) scripts/generate_regime_map.py

theory-validation:
	$(PYTHON) scripts/validate_theory_vgne_share.py
	$(PYTHON) scripts/validate_theory_poa.py
	$(PYTHON) scripts/validate_theory_stability.py
	$(PYTHON) scripts/build_theory_validation_report.py

stats-annex:
	$(PYTHON) scripts/build_stats_annex.py

figures-paper:
	$(PYTHON) scripts/generate_paper_figures.py
	$(PYTHON) scripts/build_figure_manifest.py

video-catalog:
	$(PYTHON) scripts/build_video_catalog.py

sp9:
	$(PYTHON) scripts/run_sp9_experiment.py --config configs/experiments/sp9/SP9_COPPELIA_gap_study.yaml
	$(PYTHON) scripts/postprocess_sp9_gap_study.py
	$(PYTHON) scripts/build_sp9_video_catalog.py

thesis: report-pdf

reproduce-figures: method-matrix regime-map theory-validation stats-annex figures-paper video-catalog

submit-ready:
	$(PYTHON) scripts/submit_ready_gate.py $(SUBMIT_READY_ARGS)

submit-check:
	$(MAKE) submit-ready
	$(PYTHON) scripts/preflight_repo_audit.py
	$(MAKE) reproduce-figures
	$(MAKE) sp9
	$(PYTHON) scripts/check_claims.py
	$(MAKE) test
	$(MAKE) thesis

validate-suite:
	$(PYTHON) -m viu_mrob_tfm.validation.suite

smoke-exp:
	$(PYTHON) scripts/run_experiment.py --config $(EXP)

run-canonical:
	$(PYTHON) scripts/run_sp1_homogeneous.py configs/experiments/sp1/SP1_HOMOGENEOUS_v1_1.yaml
	$(PYTHON) scripts/run_sp2_heterogeneous.py configs/experiments/sp2/SP2_HETEROGENEOUS_GAME_v1_2.yaml
	$(PYTHON) scripts/run_sp3_wrench_nash.py configs/experiments/sp3/SP3_WRENCH_NASH_GAME_v1_1.yaml
	$(PYTHON) scripts/run_sp4_docking_game.py configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml
	$(PYTHON) scripts/run_sp5_payload_transport.py configs/experiments/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2.yaml
	$(PYTHON) scripts/run_sp6_experiment.py configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml
	$(PYTHON) scripts/run_sp7_experiment.py configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml
	$(PYTHON) scripts/run_sp8_experiment.py configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml

clean-generated:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in [Path('docs/doc-05-final-report/build'), Path('results/raw/_pytest_runner_smoke')] if path.exists()]"

clean: clean-generated

