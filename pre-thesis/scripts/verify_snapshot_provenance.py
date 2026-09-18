"""Verify the immutable source snapshot plus its explicit derived-file overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceError(ValueError):
    """Raised when snapshot provenance is incomplete or inconsistent."""


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProvenanceError(f"Missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProvenanceError(f"Invalid JSON in {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProvenanceError(f"{label} must be a JSON object: {path}")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_sha256(value: object, *, field: str, snapshot_path: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ProvenanceError(
            f"Invalid {field} for {snapshot_path!r}; expected lowercase SHA-256"
        )
    return value


def _validated_relative_path(root: Path, value: object, *, source: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(f"Missing snapshot_path in {source}")
    relative = Path(value)
    if relative.is_absolute():
        raise ProvenanceError(f"Absolute snapshot path is forbidden in {source}: {value}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ProvenanceError(f"Snapshot path escapes root in {source}: {value}") from exc
    return relative.as_posix(), resolved


def _indexed_base_files(root: Path, data: dict[str, Any]) -> dict[str, tuple[str, Path]]:
    files = data.get("files")
    if not isinstance(files, list):
        raise ProvenanceError("Base manifest field 'files' must be a list")
    indexed: dict[str, tuple[str, Path]] = {}
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise ProvenanceError(f"Base manifest files[{index}] must be an object")
        snapshot_path, resolved = _validated_relative_path(
            root, entry.get("snapshot_path"), source=f"base files[{index}]"
        )
        if snapshot_path in indexed:
            raise ProvenanceError(f"Duplicate base snapshot_path: {snapshot_path}")
        base_sha256 = _validated_sha256(
            entry.get("snapshot_sha256"),
            field="snapshot_sha256",
            snapshot_path=snapshot_path,
        )
        indexed[snapshot_path] = (base_sha256, resolved)
    return indexed


def _indexed_overlay_files(root: Path, data: dict[str, Any]) -> dict[str, tuple[str, str, Path]]:
    files = data.get("files")
    if not isinstance(files, list):
        raise ProvenanceError("Derived overlay field 'files' must be a list")
    indexed: dict[str, tuple[str, str, Path]] = {}
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise ProvenanceError(f"Derived overlay files[{index}] must be an object")
        snapshot_path, resolved = _validated_relative_path(
            root, entry.get("snapshot_path"), source=f"overlay files[{index}]"
        )
        if snapshot_path in indexed:
            raise ProvenanceError(f"Duplicate overlay snapshot_path: {snapshot_path}")
        base_sha256 = _validated_sha256(
            entry.get("base_sha256"),
            field="base_sha256",
            snapshot_path=snapshot_path,
        )
        derived_sha256 = _validated_sha256(
            entry.get("derived_sha256"),
            field="derived_sha256",
            snapshot_path=snapshot_path,
        )
        if base_sha256 == derived_sha256:
            raise ProvenanceError(
                f"Overlay entry is not derived because both hashes match: {snapshot_path}"
            )
        rationale = entry.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ProvenanceError(f"Overlay entry has no rationale: {snapshot_path}")
        indexed[snapshot_path] = (base_sha256, derived_sha256, resolved)
    return indexed


def verify_snapshot_provenance(
    *, root: Path, base_manifest: Path, derived_overlay: Path
) -> dict[str, int]:
    """Return counts after validating every file against base or exact overlay."""

    root = root.resolve()
    base_manifest = base_manifest.resolve()
    base_data = _load_json(base_manifest, label="base manifest")
    overlay_data = _load_json(derived_overlay.resolve(), label="derived overlay")
    if overlay_data.get("base_manifest") != "config/source-snapshot.json":
        raise ProvenanceError(
            "Derived overlay must declare base_manifest='config/source-snapshot.json'"
        )
    declared_manifest_sha256 = _validated_sha256(
        overlay_data.get("base_manifest_sha256"),
        field="base_manifest_sha256",
        snapshot_path="config/source-snapshot.json",
    )
    if declared_manifest_sha256 != _sha256(base_manifest):
        raise ProvenanceError(
            "Immutable base manifest hash does not match derived overlay declaration"
        )
    base_commit = base_data.get("git", {}).get("commit")
    if not isinstance(base_commit, str) or not base_commit:
        raise ProvenanceError("Base manifest has no git.commit")
    if overlay_data.get("base_commit") != base_commit:
        raise ProvenanceError("Derived overlay base_commit does not match base manifest")

    base_files = _indexed_base_files(root, base_data)
    overlay_files = _indexed_overlay_files(root, overlay_data)
    unknown = sorted(set(overlay_files) - set(base_files))
    if unknown:
        raise ProvenanceError(f"Overlay paths are absent from base manifest: {unknown}")

    base_matches = 0
    derived_matches = 0
    for snapshot_path, (base_sha256, resolved) in base_files.items():
        if not resolved.is_file():
            raise ProvenanceError(f"Snapshot file is missing: {snapshot_path}")
        actual_sha256 = _sha256(resolved)
        overlay_entry = overlay_files.get(snapshot_path)
        if actual_sha256 == base_sha256:
            if overlay_entry is not None:
                raise ProvenanceError(
                    f"Stale overlay entry for file that matches base: {snapshot_path}"
                )
            base_matches += 1
            continue
        if overlay_entry is None:
            raise ProvenanceError(
                f"Unrecorded derived snapshot file: {snapshot_path} "
                f"(base={base_sha256}, actual={actual_sha256})"
            )
        overlay_base, overlay_derived, _ = overlay_entry
        if overlay_base != base_sha256:
            raise ProvenanceError(f"Overlay base hash mismatch: {snapshot_path}")
        if overlay_derived != actual_sha256:
            raise ProvenanceError(
                f"Overlay derived hash mismatch: {snapshot_path} "
                f"(declared={overlay_derived}, actual={actual_sha256})"
            )
        derived_matches += 1

    if derived_matches != len(overlay_files):
        raise ProvenanceError("Derived overlay contains an entry that was not validated")
    return {
        "files": len(base_files),
        "base_matches": base_matches,
        "derived_matches": derived_matches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--base-manifest", type=Path)
    parser.add_argument("--derived-overlay", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    base_manifest = args.base_manifest or root / "config" / "source-snapshot.json"
    derived_overlay = (
        args.derived_overlay or root / "config" / "source-snapshot-derived.json"
    )
    try:
        summary = verify_snapshot_provenance(
            root=root,
            base_manifest=base_manifest,
            derived_overlay=derived_overlay,
        )
    except ProvenanceError as exc:
        print(f"snapshot provenance: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "snapshot provenance: PASS "
        f"({summary['files']} files; {summary['base_matches']} base, "
        f"{summary['derived_matches']} derived)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
