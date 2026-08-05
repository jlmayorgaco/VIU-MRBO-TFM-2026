from pathlib import Path

from scripts.check_protected_tikz_figures import active_tex, load_manifest, validate_sources


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_all_protected_tikz_figures_are_active_and_included() -> None:
    assert validate_sources(REPO_ROOT) == []


def test_protected_figure_registry_is_exact() -> None:
    labels = tuple(item["label"] for item in load_manifest()["figures"])
    assert labels == (
        "fig:problema",
        "fig:robot",
        "fig:tf-population-simplex",
        "fig:tf-literature-timeline",
        "fig:tf-methodological-map",
    )


def test_iffalse_content_is_not_treated_as_active() -> None:
    source = (
        "before\\iffalse\\begin{figure}"
        "\\ifcase0 nested\\or branch\\fi"
        "\\label{fig:removed}\\end{figure}\\fi after"
    )
    active = active_tex(source)
    assert "fig:removed" not in active
    assert "before" in active and "after" in active
