from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pre-thesis" / "evidence"
CLAIMS_LEDGER = ROOT / "docs" / "04_CLAIMS_EVIDENCE.md"

SOURCE_ID_RE = re.compile(r"SRC-[0-9a-f]{16}\Z")
SOURCE_ID_IN_MARKDOWN_RE = re.compile(r"`(SRC-[0-9a-f]{16})`")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
CLAIM_ROW_RE = re.compile(
    r"^\|\s*`?(C[A-Z0-9-]+)`?\s*\|",
    flags=re.MULTILINE,
)


def _read_csv(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _source_path(raw_path: str, corpus: str) -> Path:
    relative = PurePosixPath(raw_path)
    assert not relative.is_absolute()
    assert "\\" not in raw_path
    source_prefixes = {
        "books": ("material", "books"),
        "work": ("material", "compendios"),
    }
    prefix = source_prefixes[corpus]
    assert relative.parts[: len(prefix)] == prefix
    assert ".." not in relative.parts

    path = ROOT.joinpath(*relative.parts).resolve(strict=True)
    assert path.is_relative_to(ROOT.resolve())
    assert path.is_file()
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_canonical_map(
    map_name: str,
    corpus: str,
    expected_count: int,
) -> None:
    manifest = _read_csv("source-manifest.csv")
    rows = _read_csv(map_name)
    canonical = [
        row
        for row in manifest
        if row["corpus"] == corpus and row["is_canonical"] == "yes"
    ]

    assert len(rows) == len(canonical) == expected_count
    assert all(row["media_type"] == "application/pdf" for row in canonical)

    for field in ("unit_id", "path", "sha256"):
        values = [row[field] for row in rows]
        assert len(values) == len(set(values)) == expected_count

    assert all(SOURCE_ID_RE.fullmatch(row["unit_id"]) for row in rows)
    assert all(SHA256_RE.fullmatch(row["sha256"]) for row in rows)

    canonical_by_id = {row["unit_id"]: row for row in canonical}
    assert len(canonical_by_id) == expected_count
    assert set(canonical_by_id) == {row["unit_id"] for row in rows}

    for row in rows:
        manifest_row = canonical_by_id[row["unit_id"]]
        assert row["path"] == manifest_row["path"]
        assert row["sha256"] == manifest_row["sha256"]

        source = _source_path(row["path"], corpus)
        assert source.stat().st_size == int(manifest_row["bytes"])
        assert _sha256(source) == row["sha256"]


def _claim_ids(rows: list[dict[str, str]]) -> set[str]:
    claim_ids: set[str] = set()
    for row in rows:
        raw_claim_ids = row["claim_ids"]
        if not raw_claim_ids:
            continue
        parts = raw_claim_ids.split(";")
        assert all(part and part == part.strip() for part in parts)
        assert len(parts) == len(set(parts))
        claim_ids.update(parts)
    return claim_ids


def _markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    _, separator, tail = text.partition(marker)
    assert separator, f"Missing Markdown section: {marker}"
    return tail.split("\n## ", maxsplit=1)[0]


def _declared_token_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        token = re.search(r"`([^`]+)`", cells[0])
        count = cells[1].strip("*")
        if token and count.isdigit():
            counts[token.group(1)] = int(count)
    return counts


def test_book_consultation_map_covers_37_canonical_sources_with_real_hashes() -> None:
    _assert_canonical_map("book-consultation-map.csv", "books", 37)


def test_work_crosswalk_covers_33_canonical_sources_with_real_hashes() -> None:
    _assert_canonical_map("work-thematic-crosswalk.csv", "work", 33)


def test_book_claims_exist_and_declared_distribution_is_preserved() -> None:
    rows = _read_csv("book-consultation-map.csv")
    claims_text = CLAIMS_LEDGER.read_text(encoding="utf-8")
    registered_claims = set(CLAIM_ROW_RE.findall(claims_text))
    referenced_claims = _claim_ids(rows)

    assert referenced_claims
    assert referenced_claims <= registered_claims
    assert Counter(row["decision"] for row in rows) == {
        "use-now": 10,
        "use-later": 22,
        "out-of-scope": 5,
    }

    scope_counts = Counter(scope for row in rows for scope in row["scope"].split(";"))
    assert scope_counts == {
        "SP1": 12,
        "SP2": 18,
        "SP3": 11,
        "transversal": 32,
    }
    assert (
        sum(row["identity_status"].startswith("verified-ledger") for row in rows) == 10
    )
    assert Counter(
        "ledger"
        if row["identity_status"].startswith("verified-ledger")
        else row["identity_status"]
        for row in rows
    ) == {
        "ledger": 10,
        "verified-publisher": 26,
        "verified-journal-doi": 1,
    }
    assert all(
        row["identity_status"].startswith("verified-ledger")
        for row in rows
        if row["decision"] == "use-now"
    )
    assert all(row["identity_status"].startswith("verified-") for row in rows)
    assert all(row["verification_source"].startswith("https://") for row in rows)
    assert all(row["verification_date"] == "2026-09-09" for row in rows)
    assert all(row["verification_note"].strip() for row in rows)

    markdown = (EVIDENCE / "book-consultation-map.md").read_text(encoding="utf-8")
    declared = _declared_token_counts(markdown)
    assert {
        decision: declared[decision]
        for decision in {
            "use-now",
            "use-later",
            "out-of-scope",
        }
    } == Counter(row["decision"] for row in rows)


def test_book_identity_audit_is_reproducible() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE / "tools" / "verify_book_identities.py"),
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_work_crosswalk_neither_claims_nor_promotes_author_drafts() -> None:
    rows = _read_csv("work-thematic-crosswalk.csv")
    manifest_by_id = {row["unit_id"]: row for row in _read_csv("source-manifest.csv")}

    assert all(not row["claim_ids"].strip() for row in rows)
    assert all(not manifest_by_id[row["unit_id"]]["claim_ids"].strip() for row in rows)
    assert all(not row["destino"].casefold().startswith("thesis") for row in rows)
    assert all(
        not manifest_by_id[row["unit_id"]]["use"].casefold().startswith("thesis")
        for row in rows
    )
    assert Counter(row["destino"] for row in rows) == {
        "monograph": 15,
        "background": 4,
        "archive-only": 14,
    }
    assert Counter(row["decision"] for row in rows) == {
        "candidate": 19,
        "superseded": 9,
        "duplicate": 4,
        "out-of-scope": 1,
    }

    markdown = (EVIDENCE / "work-thematic-crosswalk.md").read_text(encoding="utf-8")
    declared = _declared_token_counts(markdown)
    for field in ("destino", "decision"):
        observed = Counter(row[field] for row in rows)
        assert {token: declared[token] for token in observed} == observed


def test_markdown_indexes_register_each_audited_source_once() -> None:
    cases = (
        (
            "book-consultation-map.csv",
            "book-consultation-map.md",
            "Índice 37/37",
            37,
        ),
        (
            "work-thematic-crosswalk.csv",
            "work-thematic-crosswalk.md",
            "Registro 33/33",
            33,
        ),
    )

    for csv_name, markdown_name, heading, expected_count in cases:
        rows = _read_csv(csv_name)
        markdown = (EVIDENCE / markdown_name).read_text(encoding="utf-8")
        section = _markdown_section(markdown, heading)
        documented_ids = SOURCE_ID_IN_MARKDOWN_RE.findall(section)

        assert len(documented_ids) == expected_count
        assert Counter(documented_ids) == Counter(row["unit_id"] for row in rows)


def test_manifest_traceability_applicability_is_total_and_conservative() -> None:
    manifest = _read_csv("source-manifest.csv")
    registered_claims = set(CLAIM_ROW_RE.findall(CLAIMS_LEDGER.read_text(encoding="utf-8")))
    valid_sp_tokens = {"SP1", "SP2", "SP3", "transversal", "out-of-scope"}
    valid_link_statuses = {
        "linked",
        "not-applicable",
        "pending-semantic-review",
        "reviewed-unlinked",
    }
    valid_relations = {
        "candidate-only",
        "canonical-reference",
        "context",
        "future-required",
        "mentions",
        "none",
        "refutes",
        "supports",
    }
    valid_symbol_statuses = {
        "indexed",
        "none-detected",
        "not-applicable",
        "pending-semantic-review",
        "reviewed-local-only",
    }

    assert manifest
    for row in manifest:
        sp_tokens = row["sp_target"].split(";")
        assert sp_tokens
        assert len(sp_tokens) == len(set(sp_tokens))
        assert set(sp_tokens) <= valid_sp_tokens

        claim_ids = row["claim_ids"].split(";") if row["claim_ids"] else []
        assert set(claim_ids) <= registered_claims
        assert row["claim_link_status"] in valid_link_statuses
        assert bool(claim_ids) == (row["claim_link_status"] == "linked")
        assert row["claim_relation"] in valid_relations
        assert row["claim_link_reason"]
        if row["claim_link_status"] == "pending-semantic-review":
            assert row["claim_relation"] == "future-required"
        elif row["claim_link_status"] == "reviewed-unlinked":
            assert row["claim_relation"] == "candidate-only"
        elif row["claim_link_status"] == "not-applicable":
            assert row["claim_relation"] == "none"
        else:
            assert row["claim_relation"] not in {"future-required", "none"}
        if claim_ids:
            expected_locator = "docs/04_CLAIMS_EVIDENCE.md::" + ";".join(claim_ids)
        elif row["claim_link_status"] == "reviewed-unlinked":
            expected_locator = (
                "pre-thesis/evidence/source-claim-review.csv::" + row["unit_id"]
            )
        else:
            expected_locator = ""
        assert row["evidence_locator"] == expected_locator

        assert row["symbol_status"] in valid_symbol_statuses
        assert bool(row["symbols"]) == (row["symbol_status"] == "indexed")
        assert row["symbol_note"]
        assert row["evidence_status_note"]


def test_crosswalk_preserves_traceability_and_resolves_file_level_backlog() -> None:
    manifest_by_id = {row["unit_id"]: row for row in _read_csv("source-manifest.csv")}
    crosswalk = _read_csv("content-crosswalk.csv")
    shared_fields = (
        "path",
        "corpus",
        "sha256",
        "sp_target",
        "claim_ids",
        "claim_link_status",
        "claim_relation",
        "claim_link_reason",
        "evidence_locator",
        "evidence_status",
        "evidence_status_note",
    )

    assert len(crosswalk) == len(manifest_by_id) == 202
    for row in crosswalk:
        manifest_row = manifest_by_id[row["unit_id"]]
        assert all(row[field] == manifest_row[field] for field in shared_fields)

    monograph_backlog = [row for row in crosswalk if row["destination"] == "monograph"]
    assert len(monograph_backlog) == 45
    reviewed_candidates = [row for row in monograph_backlog if not row["claim_ids"]]
    audited_formal_sources = [row for row in monograph_backlog if row["claim_ids"]]
    assert len(reviewed_candidates) == 41
    assert len(audited_formal_sources) == 4
    assert all(
        row["claim_link_status"] == "reviewed-unlinked"
        and row["claim_relation"] == "candidate-only"
        and row["evidence_locator"].endswith(row["unit_id"])
        for row in reviewed_candidates
    )
    assert all(
        row["claim_link_status"] == "linked"
        and row["claim_relation"] == "mentions"
        for row in audited_formal_sources
    )

    reviewed_context_books = {
        "SRC-7923e0f353c892cb",
        "SRC-0b7ceba994fe5772",
        "SRC-c0cae4da012e4a4e",
        "SRC-fda513c2ae72b910",
    }
    for unit_id in reviewed_context_books:
        row = manifest_by_id[unit_id]
        assert row["corpus"] == "books"
        assert not row["claim_ids"]
        assert row["claim_link_status"] == "not-applicable"
        assert row["claim_relation"] == "none"
        assert row["claim_link_reason"]


def test_source_claim_review_is_hash_bound_and_matches_fragment_ledgers() -> None:
    review = _read_csv("source-claim-review.csv")
    manifest = {row["unit_id"]: row for row in _read_csv("source-manifest.csv")}
    crosswalk = _read_csv("content-crosswalk.csv")
    ideas = _read_csv("idea-ledger.csv")
    formal = _read_csv("formal-results-audit.csv")

    expected_ids = {
        row["unit_id"]
        for row in crosswalk
        if row["is_exact_duplicate"] == "no"
        and row["destination"] == "monograph"
        and not row["claim_ids"]
    }
    assert len(review) == 41
    assert len({row["unit_id"] for row in review}) == 41
    assert {row["unit_id"] for row in review} == expected_ids
    assert Counter(row["corpus"] for row in review) == {"paper": 26, "work": 15}
    assert Counter(row["review_category"] for row in review) == {
        "author-draft-candidate": 15,
        "paper-formal-candidate": 17,
        "paper-empirical-candidate": 7,
        "paper-context-candidate": 2,
    }

    idea_counts: dict[str, Counter[str]] = {}
    for unit_id in expected_ids:
        idea_counts[unit_id] = Counter(
            row["kind"] for row in ideas if row["source_unit_id"] == unit_id
        )
    formal_counts = Counter(row["path"] for row in formal)
    for row in review:
        source = manifest[row["unit_id"]]
        assert row["path"] == source["path"]
        assert row["source_sha256"] == source["sha256"]
        assert row["corpus"] == source["corpus"]
        assert not row["claim_ids"]
        assert row["claim_link_status"] == "reviewed-unlinked"
        assert row["claim_relation"] == "candidate-only"
        assert row["evidence_locator"] == (
            "pre-thesis/evidence/source-claim-review.csv::" + row["unit_id"]
        )
        counts = idea_counts[row["unit_id"]]
        assert int(row["heading_count"]) == sum(
            counts[kind]
            for kind in ("latex-heading", "pdf-bookmark", "pdf-heading-candidate")
        )
        assert int(row["labeled_unit_count"]) == sum(
            counts[kind]
            for kind in (
                "latex-observation",
                "latex-figure",
                "latex-table",
                "latex-equation",
            )
        )
        assert int(row["formal_result_count"]) == formal_counts[row["path"]]
        assert row["review_basis"] and row["rationale"] and row["limitation"]


def test_build_verify_seals_release_and_keeps_live_source_audit_opt_in() -> None:
    build_script = (ROOT / "pre-thesis" / "build.ps1").read_text(encoding="utf-8")
    release_offset = build_script.index('"scripts/verify_release_manifest.py"')
    release_block_end = build_script.index(")", release_offset)
    assert '"--check"' in build_script[release_offset:release_block_end]

    audit_sources_offset = build_script.index("if ($AuditSources)")
    required_commands = {
        '"evidence/tools/build_inventory.py"': '"--check"',
        '"evidence/tools/build_source_claim_review.py"': '"--check"',
        '"evidence/tools/merge_formal_semantic_audits.py"': '"--check"',
        '"evidence/tools/build_idea_ledger.py"': '"--check-index"',
        '"evidence/tools/verify_book_identities.py"': '"--check"',
    }
    for script, mode in required_commands.items():
        script_offset = build_script.index(script)
        assert script_offset > audit_sources_offset
        block_end = build_script.index(")", script_offset)
        assert mode in build_script[script_offset:block_end]


def test_results_sources_have_canonical_sp_targets_and_precise_claim_links() -> None:
    by_path = {row["path"]: row for row in _read_csv("source-manifest.csv")}

    assert by_path[
        "thesis/sections/mainmatter/06-results-and-analysis/index.tex"
    ]["sp_target"] == "SP1;SP2;SP3;transversal"
    assert by_path[
        "thesis/sections/mainmatter/06-results-and-analysis/aws-industrial2.tex"
    ]["sp_target"] == "SP3"
    assert by_path[
        "thesis/sections/mainmatter/06-results-and-analysis/cargo-e2e.tex"
    ]["claim_ids"] == "C4E-SP2-6"
    assert set(
        by_path["thesis/sections/mainmatter/06-results-and-analysis/sp7.tex"][
            "claim_ids"
        ].split(";")
    ) == {"C7A-SP7", "C7B-SP7", "C7C-SP7", "C7D-SP7"}

    aws_macros = by_path["thesis/generated/aws-industrial2-results.tex"]
    assert aws_macros["sp_target"] == "SP3"
    assert set(aws_macros["claim_ids"].split(";")) == {
        "C15-SP0",
        "C16-SP1SP2",
        "C17-SP1SP2",
        "C18-SP1SP5",
        "C19-SP1SP5SP7",
    }
    assert aws_macros["claim_link_status"] == "linked"
    assert aws_macros["claim_relation"] == "mentions"

    reviewed_non_evidence = {
        "thesis/generated/literature-coverage.tex",
        "thesis/sections/frontmatter/01-summary.tex",
        "thesis/sections/frontmatter/02-abstract.tex",
        "thesis/sections/mainmatter/01-introduction.tex",
        "thesis/sections/mainmatter/04-methodology.tex",
        "thesis/sections/mainmatter/06-results-and-analysis/index.tex",
        "thesis/sections/mainmatter/07-conclusions.tex",
    }
    for path in reviewed_non_evidence:
        row = by_path[path]
        assert row["claim_link_status"] == "not-applicable"
        assert row["claim_relation"] == "none"
        assert not row["claim_ids"]

    audited_paper_links = {
        "paper/megajuego.tex": {"C-SP2-EL-CONTACT-MODEL", "C1B-SP1"},
        "paper/sec_cfrd.tex": {"C-SP1-N4-DMIS-TX"},
        "paper/sec_clusters.tex": {"C-SP2-CROSS-MONO-FORMAL"},
        "paper/sec_modelo_fisico.tex": {"C-SP2-N1-KIN-FORMAL"},
    }
    for path, expected_claims in audited_paper_links.items():
        row = by_path[path]
        assert set(row["claim_ids"].split(";")) == expected_claims
        assert row["claim_link_status"] == "linked"
        assert row["claim_relation"] == "mentions"
        assert "NONE_IN_DOCS_04" not in row["claim_ids"]


def test_symbol_index_resolves_false_negatives_without_hiding_overloads() -> None:
    by_path = {row["path"]: row for row in _read_csv("source-manifest.csv")}

    unicycle = by_path["thesis/figures/protected/02-unicycle-geometry.tex"]
    assert unicycle["symbol_status"] == "indexed"
    assert {"q_i", "p_i", "v_i", "theta", "omega", "h_i", "ell"} <= set(
        unicycle["symbols"].split(";")
    )

    for path in (
        "thesis/sections/frontmatter/01-summary.tex",
        "thesis/sections/frontmatter/02-abstract.tex",
    ):
        assert "N" in by_path[path]["symbols"].split(";")

    results_index = by_path[
        "thesis/sections/mainmatter/06-results-and-analysis/index.tex"
    ]
    conclusions = by_path["thesis/sections/mainmatter/07-conclusions.tex"]
    assert "p_Holm" in results_index["symbols"].split(";")
    assert {"W", "p_Holm"} <= set(conclusions["symbols"].split(";"))

    plan = by_path["paper/sec_ensayo_cierre_plan.tex"]
    experiments = by_path["paper/sec_ensayos.tex"]
    assert plan["symbol_status"] == "reviewed-local-only"
    assert "Sobrecarga detectada" in plan["symbol_note"]
    assert "N=30" in experiments["symbol_note"]
    assert "N" not in experiments["symbols"].split(";")

    reviewed_local = {
        row["path"]
        for row in by_path.values()
        if row["symbol_status"] == "reviewed-local-only"
    }
    assert reviewed_local == {
        "paper/sec_auditoria.tex",
        "paper/sec_ensayo_cierre_figs.tex",
        "paper/sec_ensayo_cierre_interp.tex",
        "paper/sec_ensayo_cierre_plan.tex",
        "paper/sec_ensayo_cierre_resultados.tex",
    }
    assert not any(
        row["symbol_status"] == "pending-semantic-review"
        for row in by_path.values()
    )
