from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parents[1]
REPO = Path.cwd()
LOG_DIR = BASE / "logs"
INPUT_DIR = BASE / "inputs"
ENV_FILE = BASE / ".env.literature"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_encoding(path: Path) -> str:
    if path.suffix.lower() in {".pdf", ".docx", ".zip", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}:
        return "binary"
    raw = path.read_bytes()[:65536]
    for enc in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "unknown"


def count_records(path: Path, encoding: str) -> str:
    ext = path.suffix.lower()
    if ext not in {".csv", ".tsv", ".txt"}:
        return ""
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        return str(max(0, len(lines) - 1))
    except Exception:
        return ""


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    manifest = LOG_DIR / "stage0_input_manifest.csv"
    rows = []
    for path in sorted(p for p in INPUT_DIR.rglob("*") if p.is_file()):
        enc = detect_encoding(path)
        rows.append({
            "path": str(path.relative_to(BASE)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "encoding": enc,
            "record_count_estimate": count_records(path, enc),
            "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "audited_utc": now,
        })
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["path"])
        w.writeheader()
        w.writerows(rows)

    env = parse_env(ENV_FILE)
    wos_files = [p for p in (INPUT_DIR / "wos").glob("*") if p.is_file() and not p.name.lower().startswith("readme")]
    seed = INPUT_DIR / "legacy" / "legacy_seed_references.csv"
    seed_rows = 0
    if seed.exists():
        with seed.open("r", encoding="utf-8-sig", newline="") as f:
            seed_rows = sum(1 for _ in csv.DictReader(f))

    print(f"Stage 0 input audit: {len(rows)} input files")
    print(f"Legacy seed rows: {seed_rows}")
    print(f"CONTACT_EMAIL configured: {bool(env.get('CONTACT_EMAIL'))}")
    print(f"WoS raw exports present: {len(wos_files)}")
    print(f"Manifest: {manifest}")

    hard_fail = False
    if not seed.exists() or seed_rows == 0:
        print("ERROR: missing/non-empty legacy_seed_references.csv")
        hard_fail = True
    if not env.get("CONTACT_EMAIL"):
        print("ERROR: CONTACT_EMAIL missing in literature_review/.env.literature")
        hard_fail = True

    return 2 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
