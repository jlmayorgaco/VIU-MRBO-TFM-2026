"""Record provenance and SHA-256 for material imported into pre-thesis."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUTPUT = ROOT / "config" / "source-snapshot.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def origin_for(relative: Path) -> Path | None:
    text = relative.as_posix()
    direct = {
        "viu-mrob-thesis.sty": Path("thesis/viu-mrob-thesis.sty"),
        "config/metadata.tex": Path("thesis/config/metadata.tex"),
        "config/math-commands.tex": Path("thesis/config/math-commands.tex"),
        "config/protected-tikz-figures.snapshot.json": Path(
            "thesis/config/protected-tikz-figures.json"
        ),
        "bibliography/references.bib": Path("thesis/references.bib"),
        "shared/generated-macros/aws-industrial2-results.tex": Path(
            "thesis/generated/aws-industrial2-results.tex"
        ),
        "shared/generated-macros/literature-coverage.tex": Path(
            "thesis/generated/literature-coverage.tex"
        ),
        "figures/generated/cargo-e2e-success.pdf": Path(
            "legacy/results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/figures/fig-cargo-e2e-success.pdf"
        ),
        "figures/coppelia/aws-industrial-oblique-camera.png": Path(
            "legacy/results/coppeliasim_validation/aws_industrial_adversarial_industrial2/aws_industrial_oblique_camera.png"
        ),
        "figures/coppelia/aws-industrial-oblique-live.png": Path(
            "legacy/results/coppeliasim_validation/aws_industrial_adversarial_industrial2/aws_industrial_oblique_live.png"
        ),
    }
    if text in direct:
        return direct[text]
    if text.startswith("sections/source-snapshot/"):
        return Path("thesis/sections") / Path(text).relative_to("sections/source-snapshot")
    if text.startswith("figures/protected/"):
        return Path("thesis/figures/protected") / relative.name
    if text.startswith("images/"):
        return Path("thesis/images") / relative.name
    if text.startswith("shared/generated-macros/"):
        name = relative.name
        if name.startswith("cargo_"):
            return Path(
                "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables"
            ) / name
        if name.startswith("sp0_"):
            return Path("legacy/results/sp0/SP0_THEORY_v1/tables") / name
        if name.startswith("sp1_"):
            return Path("legacy/results/sp1/SP1_QUORUM_v1/tables") / name
        if name.startswith("sp3_"):
            return Path(
                "results/processed/sp3/SP3_WRENCH_EVIDENCE_v1/tables"
            ) / name
        if name.startswith("sp4_"):
            return Path(
                "results/processed/sp4/SP4_TRANSPORT_EVIDENCE_v1/tables"
            ) / name
        if name.startswith("sp") and len(name) > 2 and name[2].isdigit():
            number = name[2]
            campaigns = {
                "2": "SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1",
                "3": "SP3_WRENCH_EVIDENCE_v1",
                "4": "SP4_TRANSPORT_EVIDENCE_v1",
                "5": "SP5_SAFETY_EVIDENCE_v1",
                "6": "SP6_RECOVERY_CONFIRMATORY_v1",
                "7": "SP7_TRAFFIC_CONFIRMATORY_v1",
                "8": "SP8_NETWORK_CONFIRMATORY_v1",
            }
            return Path("legacy/results/processed") / f"sp{number}" / campaigns[number] / "tables" / name
    return None


def imported_files() -> list[Path]:
    roots = (
        ROOT / "viu-mrob-thesis.sty",
        ROOT / "config/metadata.tex",
        ROOT / "config/math-commands.tex",
        ROOT / "config/protected-tikz-figures.snapshot.json",
        ROOT / "bibliography/references.bib",
        ROOT / "sections/source-snapshot",
        ROOT / "figures/protected",
        ROOT / "figures/generated/cargo-e2e-success.pdf",
        ROOT / "figures/coppelia",
        ROOT / "images",
        ROOT / "shared/generated-macros",
    )
    files: list[Path] = []
    for candidate in roots:
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(path for path in candidate.rglob("*") if path.is_file())
    return sorted(set(files), key=lambda path: path.as_posix().lower())


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=REPO)


def main() -> None:
    status = git_bytes("status", "--porcelain=v1", "-z")
    entries = [entry for entry in status.split(b"\0") if entry]
    records: list[dict[str, object]] = []
    for snapshot in imported_files():
        relative = snapshot.relative_to(ROOT)
        origin = origin_for(relative)
        source = REPO / origin if origin is not None else None
        source_hash = sha256(source) if source is not None and source.is_file() else None
        snapshot_hash = sha256(snapshot)
        records.append(
            {
                "snapshot_path": relative.as_posix(),
                "snapshot_sha256": snapshot_hash,
                "source_path": origin.as_posix() if origin is not None else None,
                "source_sha256_at_snapshot": source_hash,
                "modified_during_import": source_hash is not None and source_hash != snapshot_hash,
            }
        )

    document = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": {
            "commit": git_bytes("rev-parse", "HEAD").decode().strip(),
            "dirty": bool(entries),
            "status_entry_count": len(entries),
            "status_porcelain_sha256": hashlib.sha256(status).hexdigest(),
        },
        "files": records,
    }
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Registradas {len(records)} fuentes en {OUTPUT}")


if __name__ == "__main__":
    main()
