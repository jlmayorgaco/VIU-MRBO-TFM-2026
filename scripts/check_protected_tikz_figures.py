"""Fail when a protected TikZ figure is absent from the active thesis."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
THESIS_ROOT = REPO_ROOT / "thesis"
MANIFEST_PATH = THESIS_ROOT / "config" / "protected-tikz-figures.json"
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
CONDITIONAL_RE = re.compile(
    r"\\(?:iffalse|iftrue|ifcase|ifnum|ifdim|ifodd|ifvmode|ifhmode|"
    r"ifmmode|ifinner|ifvoid|ifhbox|ifvbox|ifx|ifeof|ifdefined|"
    r"ifcsname|iffontchar|if|else|or|fi)(?![A-Za-z@])"
)


def _strip_comments(text: str) -> str:
    """Remove LaTeX comments while preserving escaped percent signs."""

    cleaned: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, character in enumerate(line):
            if character != "%":
                continue
            preceding = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                preceding += 1
                cursor -= 1
            if preceding % 2 == 0:
                cut = index
                break
        cleaned.append(line[:cut])
    return "\n".join(cleaned)


def active_tex(text: str) -> str:
    """Return source outside literal ``\\iffalse`` branches.

    The scan is token based so inline wrappers and nested primitive TeX
    conditionals cannot make a disabled figure look active. Dynamic
    conditionals are preserved because their truth value is build-dependent.
    """

    source = _strip_comments(text)
    active: list[str] = []
    stack: list[bool | None] = []
    cursor = 0

    def visible() -> bool:
        return all(state is not False for state in stack)

    for match in CONDITIONAL_RE.finditer(source):
        if visible():
            active.append(source[cursor : match.start()])
        token = match.group(0)
        if token == r"\iffalse":
            stack.append(False)
        elif token == r"\iftrue":
            stack.append(True)
        elif token == r"\else":
            if stack:
                if stack[-1] is False:
                    stack[-1] = True
                elif stack[-1] is True:
                    stack[-1] = False
                elif visible():
                    active.append(token)
            elif visible():
                active.append(token)
        elif token == r"\fi":
            if stack:
                state = stack.pop()
                if state is None and visible():
                    active.append(token)
            elif visible():
                active.append(token)
        elif token == r"\or":
            if visible():
                active.append(token)
        else:
            stack.append(None)
            if visible():
                active.append(token)
        cursor = match.end()

    if stack:
        raise ValueError("unclosed TeX conditional")
    if visible():
        active.append(source[cursor:])
    return "".join(active)


def _resolve_input(name: str) -> Path:
    candidate = THESIS_ROOT / name
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")
    return candidate.resolve()


def active_input_graph() -> set[Path]:
    """Traverse existing active inputs from ``main.tex``.

    Missing non-protected generated inputs are left to the normal LaTeX build.
    This checker has the narrower responsibility of proving that every
    protected TikZ source is reachable through the active document graph.
    """

    pending = [(THESIS_ROOT / "main.tex").resolve()]
    visited: set[Path] = set()
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        if not source.is_file():
            continue
        visited.add(source)
        content = active_tex(source.read_text(encoding="utf-8"))
        for match in INPUT_RE.finditer(content):
            included = _resolve_input(match.group(1))
            if included not in visited:
                pending.append(included)
    return visited


def load_manifest() -> dict[str, Any]:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("figures"), list):
        raise ValueError(f"invalid protected-figure manifest: {MANIFEST_PATH}")
    return data


def _figure_block(source: str, label: str) -> str:
    label_token = rf"\label{{{label}}}"
    if source.count(label_token) != 1:
        raise ValueError(
            f"{label}: expected one active {label_token}, found {source.count(label_token)}"
        )
    label_index = source.index(label_token)
    start = source.rfind(r"\begin{figure}", 0, label_index)
    end = source.find(r"\end{figure}", label_index)
    if start < 0 or end < 0:
        raise ValueError(f"{label}: active label is not enclosed in a figure")
    return source[start : end + len(r"\end{figure}")]


def validate_sources(repo_root: Path = REPO_ROOT) -> list[str]:
    """Return all source/inclusion violations without stopping at the first one."""

    errors: list[str] = []
    try:
        manifest = load_manifest()
        included_sources = active_input_graph()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    labels: set[str] = set()
    for item in manifest["figures"]:
        label = item.get("label")
        source_value = item.get("source")
        if not isinstance(label, str) or not isinstance(source_value, str):
            errors.append(f"invalid manifest entry: {item!r}")
            continue
        if label in labels:
            errors.append(f"duplicate protected label in manifest: {label}")
        labels.add(label)

        source_path = (repo_root / source_value).resolve()
        if not source_path.is_file():
            errors.append(f"{label}: source does not exist: {source_value}")
            continue
        if source_path not in included_sources:
            errors.append(f"{label}: source is not reachable from thesis/main.tex")

        raw = source_path.read_text(encoding="utf-8")
        try:
            active = active_tex(raw)
            block = _figure_block(active, label)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        for token in (r"\begin{tikzpicture}", r"\caption"):
            if token not in block:
                errors.append(f"{label}: figure block is missing {token}")
        if not re.search(r"\\viu(?:own)?source(?:\{|\b)", block):
            errors.append(f"{label}: figure block is missing a VIU source statement")
        for token in item.get("required_tokens", []):
            # Human-readable protection markers are comments by design, while
            # all substantive TikZ tokens must remain in active TeX.
            haystack = raw if token.startswith("TFM-PROTECTED-TIKZ:") else block
            if token not in haystack:
                errors.append(f"{label}: protected content token is missing: {token}")
    return errors


def validate_aux(aux_path: Path) -> list[str]:
    """Require every protected label in the stabilized LaTeX auxiliary file."""

    if not aux_path.is_file():
        return [f"compiled auxiliary file does not exist: {aux_path}"]
    aux = aux_path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    for item in load_manifest()["figures"]:
        label = item["label"]
        if rf"\newlabel{{{label}}}" not in aux:
            errors.append(f"{label}: label is absent from compiled auxiliary file")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aux",
        type=Path,
        help="also require protected labels in this compiled LaTeX .aux file",
    )
    args = parser.parse_args()

    errors = validate_sources()
    if args.aux is not None:
        errors.extend(validate_aux(args.aux.resolve()))
    if errors:
        print("Protected TikZ figure check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)

    count = len(load_manifest()["figures"])
    suffix = " and compiled auxiliary file" if args.aux is not None else ""
    print(f"Protected TikZ figure check passed for {count} figures{suffix}.")


if __name__ == "__main__":
    main()
