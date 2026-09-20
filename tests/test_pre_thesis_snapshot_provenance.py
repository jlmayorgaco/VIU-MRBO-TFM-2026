from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path("pre-thesis/scripts/verify_snapshot_provenance.py")
SPEC = importlib.util.spec_from_file_location("snapshot_provenance", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
snapshot_provenance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot_provenance)


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _write_manifests(
    root: Path,
    *,
    base_content: str,
    current_content: str,
    overlay_files: list[dict[str, str]],
) -> tuple[Path, Path]:
    snapshot_path = root / "sections" / "chapter.tex"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_text(current_content, encoding="utf-8")
    base = {
        "schema_version": 1,
        "git": {"commit": "abc123"},
        "files": [
            {
                "snapshot_path": "sections/chapter.tex",
                "snapshot_sha256": _sha256(base_content),
            }
        ],
    }
    overlay = {
        "schema_version": 1,
        "base_manifest": "config/source-snapshot.json",
        "base_commit": "abc123",
        "files": overlay_files,
    }
    config = root / "config"
    config.mkdir()
    base_path = config / "source-snapshot.json"
    overlay_path = config / "source-snapshot-derived.json"
    base_text = json.dumps(base)
    base_path.write_text(base_text, encoding="utf-8")
    overlay["base_manifest_sha256"] = _sha256(base_text)
    overlay_path.write_text(json.dumps(overlay), encoding="utf-8")
    return base_path, overlay_path


def _verify(root: Path, base_path: Path, overlay_path: Path) -> dict[str, int]:
    return snapshot_provenance.verify_snapshot_provenance(
        root=root,
        base_manifest=base_path,
        derived_overlay=overlay_path,
    )


def test_base_snapshot_without_overlay_passes(tmp_path: Path) -> None:
    base_path, overlay_path = _write_manifests(
        tmp_path, base_content="base", current_content="base", overlay_files=[]
    )

    assert _verify(tmp_path, base_path, overlay_path) == {
        "files": 1,
        "base_matches": 1,
        "derived_matches": 0,
    }


def test_exact_derived_overlay_passes(tmp_path: Path) -> None:
    overlay_entry = {
        "snapshot_path": "sections/chapter.tex",
        "base_sha256": _sha256("base"),
        "derived_sha256": _sha256("derived"),
        "rationale": "Audited editorial derivation.",
    }
    base_path, overlay_path = _write_manifests(
        tmp_path,
        base_content="base",
        current_content="derived",
        overlay_files=[overlay_entry],
    )

    assert _verify(tmp_path, base_path, overlay_path)["derived_matches"] == 1


def test_unrecorded_derivation_fails(tmp_path: Path) -> None:
    base_path, overlay_path = _write_manifests(
        tmp_path, base_content="base", current_content="derived", overlay_files=[]
    )

    with pytest.raises(snapshot_provenance.ProvenanceError, match="Unrecorded"):
        _verify(tmp_path, base_path, overlay_path)


def test_overlay_must_preserve_base_hash_and_match_current_file(tmp_path: Path) -> None:
    entry = {
        "snapshot_path": "sections/chapter.tex",
        "base_sha256": _sha256("wrong base"),
        "derived_sha256": _sha256("derived"),
        "rationale": "Audited editorial derivation.",
    }
    base_path, overlay_path = _write_manifests(
        tmp_path, base_content="base", current_content="derived", overlay_files=[entry]
    )

    with pytest.raises(snapshot_provenance.ProvenanceError, match="base hash mismatch"):
        _verify(tmp_path, base_path, overlay_path)


def test_overlay_pins_immutable_base_manifest(tmp_path: Path) -> None:
    base_path, overlay_path = _write_manifests(
        tmp_path, base_content="base", current_content="base", overlay_files=[]
    )
    base_data = json.loads(base_path.read_text(encoding="utf-8"))
    base_data["schema_version"] = 2
    base_path.write_text(json.dumps(base_data), encoding="utf-8")

    with pytest.raises(snapshot_provenance.ProvenanceError, match="base manifest hash"):
        _verify(tmp_path, base_path, overlay_path)


def test_stale_overlay_for_base_identical_file_fails(tmp_path: Path) -> None:
    entry = {
        "snapshot_path": "sections/chapter.tex",
        "base_sha256": _sha256("base"),
        "derived_sha256": _sha256("old derived"),
        "rationale": "Audited editorial derivation.",
    }
    base_path, overlay_path = _write_manifests(
        tmp_path, base_content="base", current_content="base", overlay_files=[entry]
    )

    with pytest.raises(snapshot_provenance.ProvenanceError, match="Stale overlay"):
        _verify(tmp_path, base_path, overlay_path)


def test_build_verify_invokes_snapshot_provenance_gate() -> None:
    build_script = Path("pre-thesis/build.ps1").read_text(encoding="utf-8")

    assert '"scripts/verify_snapshot_provenance.py"' in build_script
