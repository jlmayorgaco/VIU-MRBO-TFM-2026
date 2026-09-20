from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "pre-thesis" / "scripts" / "verify_release_manifest.py"
SPEC = importlib.util.spec_from_file_location("release_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_manifest)


def test_current_release_manifest_is_complete_and_valid() -> None:
    result = release_manifest.verify_manifest()

    assert result["files"] > 250
    assert result["metrics"]["source_units"] == 202
    assert result["metrics"]["canonical_source_units"] == 187
    assert result["metrics"]["formal_results"] == 166
    assert result["metrics"]["idea_units"] == 13_019
    assert result["metrics"]["labeled_idea_units"] == 477
    assert result["metrics"]["labeled_pending_units"] == 0
    assert result["metrics"]["audited_citation_inputs"] > 50
    assert result["metrics"]["citation_trace_artifacts"] == 4
    assert result["metrics"]["protected_tikz_labels"] == [
        "fig:problema",
        "fig:robot",
        "fig:tf-population-simplex",
        "fig:tf-literature-timeline",
        "fig:tf-methodological-map",
    ]


def test_current_release_pdfs_match_the_approved_hashes() -> None:
    thesis = release_manifest.verify_release_pdf("thesis")
    monograph = release_manifest.verify_release_pdf("monograph")

    assert thesis["sha256"] == (
        "07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8"
    )
    assert monograph["sha256"] == (
        "d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f"
    )


def test_release_manifest_paths_are_relative_and_confined() -> None:
    payload = json.loads(release_manifest.MANIFEST_PATH.read_text(encoding="utf-8"))

    declared = {entry["path"] for entry in payload["files"]}
    discovered = {
        release_manifest._relative(path) for path in release_manifest.discover_files()
    }
    assert declared == discovered
    assert release_manifest.MANIFEST_RELATIVE_PATH not in declared
    for relative in declared:
        path = Path(relative)
        assert not path.is_absolute()
        assert ".." not in path.parts
        assert not any(
            relative.startswith(prefix)
            for prefix in release_manifest.EXCLUDED_PREFIXES
        )


def test_standalone_verifier_never_resolves_repository_parents() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "parents[3]" not in source
    assert 'ROOT = Path(__file__).resolve().parents[1]' in source


def test_invalid_source_audit_mode_does_not_mutate_process_environment() -> None:
    build = ROOT / "pre-thesis" / "build.ps1"
    command = (
        "$env:SOURCE_DATE_EPOCH='sentinel-epoch'; "
        "$env:FORCE_SOURCE_DATE='sentinel-force'; "
        f"try {{ & '{build}' -AuditSources }} catch {{ }}; "
        "Write-Output ($env:SOURCE_DATE_EPOCH + '|' + $env:FORCE_SOURCE_DATE)"
    )

    process = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    assert process.stdout.strip() == "sentinel-epoch|sentinel-force"
