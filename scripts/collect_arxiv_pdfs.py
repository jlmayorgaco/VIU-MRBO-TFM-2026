"""Collect arXiv metadata and PDFs for the TFM literature review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.literature import collect_arxiv_papers, load_topics  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--topics-config",
        type=Path,
        default=ROOT / "configs" / "arxiv_literature_topics.yaml",
        help="YAML file with named arXiv queries.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "output" / "literature" / "arxiv",
        help="Directory for manifest files and the pdfs/ corpus.",
    )
    parser.add_argument(
        "--topic",
        action="append",
        default=None,
        help="Topic name to include. Repeat the flag to select multiple topics.",
    )
    parser.add_argument(
        "--list-topics",
        action="store_true",
        help="List configured topics and exit without contacting arXiv.",
    )
    parser.add_argument(
        "--max-results-per-topic",
        type=int,
        default=None,
        help="Override each topic max_results from the YAML config.",
    )
    parser.add_argument(
        "--max-results-per-topic-year",
        type=int,
        default=None,
        help="When --from-year/--to-year are used, override results per topic/year.",
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=None,
        help="Start year for submittedDate slicing, inclusive.",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=None,
        help="End year for submittedDate slicing, inclusive.",
    )
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument(
        "--api-pause-seconds",
        type=float,
        default=3.1,
        help="Pause between arXiv API pages.",
    )
    parser.add_argument(
        "--download-pause-seconds",
        type=float,
        default=1.0,
        help="Pause between PDF downloads.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--sort-by",
        choices=("relevance", "lastUpdatedDate", "submittedDate"),
        default="relevance",
    )
    parser.add_argument(
        "--sort-order",
        choices=("ascending", "descending"),
        default="descending",
    )
    parser.add_argument("--overwrite", action="store_true", help="Re-download existing PDFs.")
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Only write metadata manifests; do not fetch PDFs.",
    )
    parser.add_argument(
        "--user-agent",
        default="viu-mrob-tfm-literature-collector/0.1",
        help="HTTP User-Agent header.",
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print per-paper progress.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    topics = load_topics(args.topics_config)
    if args.list_topics:
        for topic in topics:
            limit = topic.max_results if topic.max_results is not None else "default"
            print(f"{topic.name}\tmax_results={limit}")
        return 0
    selected_topics = set(args.topic) if args.topic else None
    summary = collect_arxiv_papers(
        topics,
        output_dir=args.output_dir,
        max_results_per_topic=args.max_results_per_topic,
        max_results_per_topic_year=args.max_results_per_topic_year,
        from_year=args.from_year,
        to_year=args.to_year,
        batch_size=args.batch_size,
        api_pause_seconds=args.api_pause_seconds,
        download_pause_seconds=args.download_pause_seconds,
        timeout_seconds=args.timeout_seconds,
        download_pdfs=not args.no_download,
        overwrite=args.overwrite,
        user_agent=args.user_agent,
        selected_topics=selected_topics,
        retries=args.retries,
        sort_by=args.sort_by,
        sort_order=args.sort_order,
        verbose=not args.quiet,
    )
    print(f"Output: {summary['output_dir']}")
    print(f"Unique papers: {summary['unique_papers']}")
    print(f"Manifest CSV: {summary['manifest_csv']}")
    print(f"BibTeX: {summary['bibtex']}")
    print(f"Downloads: {summary['download_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
