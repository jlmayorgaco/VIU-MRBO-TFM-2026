"""Create or verify the standalone ``pre-thesis`` release manifest.

The source-corpus generators intentionally read the repository's ``paper``,
``thesis``, ``material`` and ``docs`` trees.  A release build must not need
those live roots: it validates the already audited evidence package instead.
This script therefore seals every non-ephemeral input below ``pre-thesis`` and
checks a small set of cross-artifact invariants without resolving any path
outside that directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "release-manifest.json"
MANIFEST_RELATIVE_PATH = "config/release-manifest.json"
EXCLUDED_PREFIXES = (".qa/", "build/", "monograph/build/")
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
LABELED_KINDS = {
    "latex-observation",
    "latex-figure",
    "latex-table",
    "latex-equation",
}
VALID_DESTINATIONS = {
    "thesis-body",
    "thesis-appendix",
    "monograph",
    "background",
    "archive-only",
}


class ReleaseManifestError(ValueError):
    """Raised when the frozen standalone package is incomplete or stale."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _included(path: Path) -> bool:
    relative = _relative(path)
    if relative == MANIFEST_RELATIVE_PATH:
        return False
    if any(relative.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if any(part in EXCLUDED_PARTS for part in Path(relative).parts):
        return False
    return path.suffix.casefold() not in EXCLUDED_SUFFIXES


def discover_files() -> list[Path]:
    """Return every immutable release input, always confined below ``ROOT``."""

    return sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and _included(path)),
        key=lambda path: _relative(path).casefold(),
    )


def _read_csv(relative: str) -> list[dict[str, str]]:
    path = ROOT / relative
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(relative: str) -> dict[str, Any]:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ReleaseManifestError(f"Expected a JSON object: {relative}")
    return data


def _confined_file(relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ReleaseManifestError(f"Unsafe package-relative path: {relative}")
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ReleaseManifestError(f"Path escapes package: {relative}") from exc
    if not resolved.is_file():
        raise ReleaseManifestError(f"Missing sealed file: {relative}")
    return resolved


def _verify_declared_hashes(mapping: object, *, label: str) -> int:
    if not isinstance(mapping, dict) or not mapping:
        raise ReleaseManifestError(f"Citation audit has no {label}")
    for relative, declared in mapping.items():
        if not isinstance(relative, str) or not isinstance(declared, str):
            raise ReleaseManifestError(f"Invalid {label} entry")
        actual = _sha256(_confined_file(relative))
        if actual != declared:
            raise ReleaseManifestError(
                f"Citation-audit {label} drift: {relative} "
                f"(declared={declared}, actual={actual})"
            )
    return len(mapping)


def _duplicates(values: Iterable[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def compute_metrics() -> dict[str, Any]:
    """Validate and summarize the frozen evidence tables using local files only."""

    source = _read_csv("evidence/source-manifest.csv")
    crosswalk = _read_csv("evidence/content-crosswalk.csv")
    formal = _read_csv("evidence/formal-results-audit.csv")
    semantic = _read_csv("evidence/integrity/formal-audit/semantic-all.csv")
    ideas = _read_csv("evidence/idea-ledger.csv")
    idea_summary = _read_json("evidence/idea-ledger-summary.json")
    source_review = _read_csv("evidence/source-claim-review.csv")
    books = _read_csv("evidence/book-consultation-map.csv")
    work = _read_csv("evidence/work-thematic-crosswalk.csv")
    claims = _read_csv("evidence/integrity/context-claims/claim-registry.csv")
    quantitative = _read_csv(
        "evidence/integrity/context-claims/quantitative-claims.csv"
    )
    citation_audit = _read_json("CITATION_AUDIT.json")
    protected = _read_json("config/protected-tikz-figures.snapshot.json")

    source_ids = [row["unit_id"] for row in source]
    crosswalk_ids = [row["unit_id"] for row in crosswalk]
    if duplicates := _duplicates(source_ids):
        raise ReleaseManifestError(f"Duplicate source unit IDs: {duplicates[:5]}")
    if duplicates := _duplicates(crosswalk_ids):
        raise ReleaseManifestError(f"Duplicate crosswalk unit IDs: {duplicates[:5]}")
    if set(source_ids) != set(crosswalk_ids):
        raise ReleaseManifestError("Source manifest and crosswalk unit sets differ")

    source_by_id = {row["unit_id"]: row for row in source}
    for row in crosswalk:
        source_row = source_by_id[row["unit_id"]]
        if row["path"] != source_row["path"] or row["sha256"] != source_row["sha256"]:
            raise ReleaseManifestError(
                f"Crosswalk provenance mismatch for {row['unit_id']}"
            )
        if row["destination"] not in VALID_DESTINATIONS:
            raise ReleaseManifestError(
                f"Unknown destination for {row['unit_id']}: {row['destination']}"
            )

    formal_ids = [row["result_id"] for row in formal]
    semantic_ids = [row["result_id"] for row in semantic]
    if duplicates := _duplicates(formal_ids):
        raise ReleaseManifestError(f"Duplicate formal result IDs: {duplicates[:5]}")
    if duplicates := _duplicates(semantic_ids):
        raise ReleaseManifestError(f"Duplicate semantic result IDs: {duplicates[:5]}")
    if set(formal_ids) != set(semantic_ids):
        raise ReleaseManifestError("Formal inventory and semantic audit result sets differ")

    source_hashes_by_path = {row["path"]: row["sha256"] for row in source}
    for row in formal:
        if source_hashes_by_path.get(row["path"]) != row["source_sha256"]:
            raise ReleaseManifestError(
                f"Formal-result source hash mismatch for {row['result_id']}"
            )

    idea_ids = [row["idea_id"] for row in ideas]
    if duplicates := _duplicates(idea_ids):
        raise ReleaseManifestError(f"Duplicate idea IDs: {duplicates[:5]}")
    for row in ideas:
        source_row = source_by_id.get(row["source_unit_id"])
        if source_row is None:
            raise ReleaseManifestError(
                f"Idea references unknown source unit: {row['idea_id']}"
            )
        if row["path"] != source_row["path"] or row["source_sha256"] != source_row["sha256"]:
            raise ReleaseManifestError(f"Idea provenance mismatch: {row['idea_id']}")

    labeled = [row for row in ideas if row["kind"] in LABELED_KINDS]
    labeled_pending = sum(
        row["semantic_review_status"] == "pending-semantic-review" for row in labeled
    )
    if idea_summary.get("row_count") != len(ideas):
        raise ReleaseManifestError("Idea-ledger summary row count is stale")
    if idea_summary.get("labeled_unit_count") != len(labeled):
        raise ReleaseManifestError("Idea-ledger labeled-unit count is stale")
    if idea_summary.get("labeled_pending_count") != labeled_pending:
        raise ReleaseManifestError("Idea-ledger pending-label count is stale")

    for row in source_review:
        source_row = source_by_id.get(row["unit_id"])
        if source_row is None or row["source_sha256"] != source_row["sha256"]:
            raise ReleaseManifestError(
                f"Source-review provenance mismatch for {row['unit_id']}"
            )

    if citation_audit.get("verdict") != "PASS":
        raise ReleaseManifestError("Frozen citation audit is not PASS")
    audited_citation_inputs = _verify_declared_hashes(
        citation_audit.get("audited_input_hashes"), label="audited_input_hashes"
    )
    citation_trace_artifacts = _verify_declared_hashes(
        citation_audit.get("audit_artifact_hashes"), label="audit_artifact_hashes"
    )
    figures = protected.get("figures")
    if not isinstance(figures, list):
        raise ReleaseManifestError("Protected-TikZ manifest has no figure list")
    protected_labels = [str(item.get("label", "")) for item in figures]
    if any(not label for label in protected_labels) or _duplicates(protected_labels):
        raise ReleaseManifestError("Protected-TikZ labels are missing or duplicated")

    return {
        "source_units": len(source),
        "canonical_source_units": sum(row["is_canonical"] == "yes" for row in source),
        "crosswalk_units": len(crosswalk),
        "crosswalk_destinations": dict(
            sorted(Counter(row["destination"] for row in crosswalk).items())
        ),
        "formal_results": len(formal),
        "formal_verdicts": dict(
            sorted(Counter(row["audit_status"] for row in formal).items())
        ),
        "semantic_results": len(semantic),
        "semantic_verdicts": dict(
            sorted(Counter(row["normalized_verdict"] for row in semantic).items())
        ),
        "idea_units": len(ideas),
        "labeled_idea_units": len(labeled),
        "labeled_pending_units": labeled_pending,
        "source_claim_reviews": len(source_review),
        "book_sources": len(books),
        "work_sources": len(work),
        "claim_registry_rows": len(claims),
        "quantitative_claim_rows": len(quantitative),
        "citation_audit_verdict": citation_audit["verdict"],
        "audited_citation_inputs": audited_citation_inputs,
        "citation_trace_artifacts": citation_trace_artifacts,
        "protected_tikz_labels": protected_labels,
    }


def verify_release_pdf(target: str) -> dict[str, str]:
    """Check the built PDF against the hash approved by the citation audit."""

    paths = {
        "thesis": "build/main.pdf",
        "monograph": "monograph/build/monograph.pdf",
    }
    try:
        relative = paths[target]
    except KeyError as exc:
        raise ReleaseManifestError(f"Unknown PDF target: {target}") from exc
    citation_audit = _read_json("CITATION_AUDIT.json")
    try:
        record = citation_audit["details"]["refresh_verification"][
            "final_pdf_hashes"
        ][relative]
    except (KeyError, TypeError) as exc:
        raise ReleaseManifestError(
            f"Citation audit has no final PDF record for {relative}"
        ) from exc
    declared = record.get("expected")
    if (
        not isinstance(declared, str)
        or record.get("actual") != declared
        or record.get("matches") is not True
    ):
        raise ReleaseManifestError(f"Citation-audit PDF record is not sealed: {relative}")
    actual = _sha256(_confined_file(relative))
    if actual != declared:
        raise ReleaseManifestError(
            f"Built PDF hash drift: {relative} (declared={declared}, actual={actual})"
        )
    return {"target": target, "path": relative, "sha256": actual}


def build_manifest() -> dict[str, Any]:
    files = discover_files()
    entries = [
        {
            "path": _relative(path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in files
    ]
    snapshot = _read_json("config/source-snapshot.json")
    base_commit = snapshot.get("git", {}).get("commit")
    if not isinstance(base_commit, str) or not base_commit:
        raise ReleaseManifestError("Source snapshot does not declare git.commit")
    return {
        "schema_version": 1,
        "package_root": ".",
        "hash_algorithm": "sha256",
        "base_commit": base_commit,
        "excluded_prefixes": list(EXCLUDED_PREFIXES),
        "excluded_parts": sorted(EXCLUDED_PARTS),
        "excluded_suffixes": sorted(EXCLUDED_SUFFIXES),
        "metrics": compute_metrics(),
        "files": entries,
    }


def write_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    payload = build_manifest()
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def verify_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseManifestError(f"Missing release manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseManifestError(f"Invalid release manifest: {exc}") from exc
    if payload.get("schema_version") != 1:
        raise ReleaseManifestError("Unsupported release-manifest schema")
    if payload.get("package_root") != "." or payload.get("hash_algorithm") != "sha256":
        raise ReleaseManifestError("Unexpected release-manifest root or hash algorithm")
    if payload.get("excluded_prefixes") != list(EXCLUDED_PREFIXES):
        raise ReleaseManifestError("Release-manifest excluded prefixes changed")
    if payload.get("excluded_parts") != sorted(EXCLUDED_PARTS):
        raise ReleaseManifestError("Release-manifest excluded parts changed")
    if payload.get("excluded_suffixes") != sorted(EXCLUDED_SUFFIXES):
        raise ReleaseManifestError("Release-manifest excluded suffixes changed")

    entries = payload.get("files")
    if not isinstance(entries, list):
        raise ReleaseManifestError("Release-manifest files must be a list")
    declared: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ReleaseManifestError(f"files[{index}] must be an object")
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative:
            raise ReleaseManifestError(f"files[{index}] has no path")
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ReleaseManifestError(f"Unsafe release path: {relative}")
        resolved = (ROOT / candidate).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ReleaseManifestError(f"Release path escapes package: {relative}") from exc
        normalized = candidate.as_posix()
        if normalized in declared:
            raise ReleaseManifestError(f"Duplicate release path: {normalized}")
        declared[normalized] = entry

    actual_paths = {_relative(file): file for file in discover_files()}
    if set(declared) != set(actual_paths):
        missing = sorted(set(declared) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(declared))
        raise ReleaseManifestError(
            f"Release file set changed: missing={missing[:5]}, extra={extra[:5]}"
        )
    for relative, file in actual_paths.items():
        entry = declared[relative]
        size = file.stat().st_size
        digest = _sha256(file)
        if entry.get("bytes") != size or entry.get("sha256") != digest:
            raise ReleaseManifestError(
                f"Release file drift: {relative} "
                f"(declared bytes/hash={entry.get('bytes')}/{entry.get('sha256')}, "
                f"actual={size}/{digest})"
            )

    metrics = compute_metrics()
    if payload.get("metrics") != metrics:
        raise ReleaseManifestError("Frozen evidence metrics are stale")
    return {
        "files": len(actual_paths),
        "bytes": sum(path.stat().st_size for path in actual_paths.values()),
        "metrics": metrics,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite the release seal")
    mode.add_argument("--check", action="store_true", help="Verify the release seal")
    parser.add_argument(
        "--pdf-target",
        choices=("thesis", "monograph"),
        help="With --check, also verify the built PDF's approved hash",
    )
    args = parser.parse_args(argv)
    if args.write and args.pdf_target:
        parser.error("--pdf-target is only valid with --check")
    try:
        if args.write:
            payload = write_manifest()
            print(
                "release manifest: WRITTEN "
                f"({len(payload['files'])} files; {payload['metrics']['idea_units']} ideas)"
            )
        else:
            result = verify_manifest()
            pdf_result = verify_release_pdf(args.pdf_target) if args.pdf_target else None
            print(
                "release manifest: PASS "
                f"({result['files']} files; {result['bytes']} bytes; "
                f"{result['metrics']['idea_units']} ideas; "
                f"{result['metrics']['formal_results']} formal results"
                + (
                    f"; {pdf_result['target']}={pdf_result['sha256']}"
                    if pdf_result
                    else ""
                )
                + ")"
            )
    except (OSError, KeyError, ReleaseManifestError, ValueError) as exc:
        print(f"release manifest: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
