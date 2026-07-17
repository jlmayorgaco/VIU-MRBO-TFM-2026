from __future__ import annotations

import json
from pathlib import Path

import yaml

from viu_mrob_tfm.sp3.evidence import execute


def test_sp3_evidence_regenerates_audited_latex(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("experiments/configs/sp3_wrench_evidence.yaml").read_text(encoding="utf-8")
    )
    config["output_dir"] = str(tmp_path / "sp3")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    output = execute(config_path)

    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    table = (output / "tables" / "sp3_results.tex").read_text(encoding="utf-8")
    macros = (output / "tables" / "sp3_numbers.tex").read_text(encoding="utf-8")
    figure = output / "figures" / "fig-sp3-wrench-performance.pdf"
    assert audit["status"] == "passed"
    assert audit["worlds"] == 600
    assert audit["runs"] == 7200
    assert audit["vector_figure_regenerated"] is True
    assert figure.read_bytes().startswith(b"%PDF-")
    assert "PD exacto + guardia" in table
    assert "Cobertura" in table
    assert "Abstención" in table
    assert "\\newcommand{\\SPThreeWorlds}{600}" in macros
    assert "\\newcommand{\\SPThreeRuns}{7200}" in macros
    assert "\\newcommand{\\SPThreeGuardedCoverage}{1.000}" in macros
    assert "\\newcommand{\\SPThreeGuardedAbstention}{0.500}" in macros
