from __future__ import annotations

import json
from pathlib import Path

import yaml

from viu_mrob_tfm.sp5.evidence import execute


def test_sp5_evidence_regenerates_audited_artifacts(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("experiments/configs/sp5_safety_evidence.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["output_dir"] = str(tmp_path / "sp5")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    output = execute(config_path)
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    macros = (output / "tables" / "sp5_numbers.tex").read_text(encoding="utf-8")
    assert audit["status"] == "passed"
    assert audit["evidence_level"] == "C"
    assert audit["push_caging_branch_validated"] is False
    assert "\\newcommand{\\SPFiveWorlds}{108}" in macros
    assert "\\newcommand{\\SPFiveRuns}{864}" in macros
    assert (output / "figures" / "fig-sp5-safety-progress.pdf").is_file()
    assert (output / "figures" / "fig-sp5-collision-matrix.pdf").is_file()
