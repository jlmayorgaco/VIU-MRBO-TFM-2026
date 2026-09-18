"""Gate de trazabilidad de cifras: toda macro que el documento usa debe coincidir
con el artefacto de la campana que la produjo.

Una cifra impresa en la memoria que no coincide con el bundle de su campana no es
trazable. Este guion:

  1. descubre que ficheros de shared/generated-macros/ usa realmente main-v2.tex
     y sus secciones;
  2. FALLA si alguno no tiene fuente registrada en REGISTRY;
  3. FALLA si el contenido difiere del artefacto de campana;
  4. informa de que guion regenera cada familia.

Uso:
    python scripts/check_macro_provenance.py [--repo ..]
Salida: 0 si todo es trazable; 1 en cualquier otro caso.
"""
import argparse
import hashlib
import io
import os
import re
import sys

# macro -> (artefacto de campana relativo a la raiz, guion que lo regenera)
# "None" como artefacto = la familia no procede de una campana numerica.
REGISTRY = {
    "sp0_method_summary": (
        "results/pre_thesis/figure_regeneration/sp0/tables/sp0_method_summary.tex",
        "viu_mrob_tfm.sp0.experiment con experiments/configs/pre_thesis_sp0_figures.yaml"),
    "sp1_method_summary": (
        "results/pre_thesis/figure_regeneration/sp1/tables/sp1_method_summary.tex",
        "viu_mrob_tfm.sp1.experiment con experiments/configs/pre_thesis_sp1_figures.yaml"),
    "sp2_numbers": (
        "legacy/results/processed/sp2/SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1/tables/sp2_numbers.tex",
        "viu-run-sp2 (experiments/configs/sp2_effective_capacity.yaml)"),
    "sp2_comparison": (
        "legacy/results/processed/sp2/SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1/tables/sp2_comparison.tex",
        "viu-run-sp2"),
    "sp2_ablation": (
        "legacy/results/processed/sp2/SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1/tables/sp2_ablation.tex",
        "viu-run-sp2"),
    "sp3_numbers": (
        "results/processed/sp3/SP3_WRENCH_EVIDENCE_v1/tables/sp3_numbers.tex",
        "viu-run-sp3-evidence (experiments/configs/sp3_wrench_evidence.yaml)"),
    "sp3_results": (
        "results/processed/sp3/SP3_WRENCH_EVIDENCE_v1/tables/sp3_results.tex",
        "viu-run-sp3-evidence"),
    "sp4_numbers": (
        "results/processed/sp4/SP4_TRANSPORT_EVIDENCE_v1/tables/sp4_numbers.tex",
        "viu-run-sp4-evidence (experiments/configs/sp4_transport_evidence.yaml)"),
    "sp4_docking_results": (
        "results/processed/sp4/SP4_TRANSPORT_EVIDENCE_v1/tables/sp4_docking_results.tex",
        "viu-run-sp4-evidence"),
    "sp4_transport_results": (
        "results/processed/sp4/SP4_TRANSPORT_EVIDENCE_v1/tables/sp4_transport_results.tex",
        "viu-run-sp4-evidence"),
    "sp5_numbers": (
        "legacy/results/processed/sp5/SP5_SAFETY_EVIDENCE_v1/tables/sp5_numbers.tex",
        "campana SP5_SAFETY_EVIDENCE_v1"),
    "sp5_results": (
        "legacy/results/processed/sp5/SP5_SAFETY_EVIDENCE_v1/tables/sp5_results.tex",
        "campana SP5_SAFETY_EVIDENCE_v1"),
    "sp6_numbers": (
        "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/tables/sp6_numbers.tex",
        "viu-run-sp6"),
    "sp6_results": (
        "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/tables/sp6_results.tex",
        "viu-run-sp6"),
    "sp7_numbers": (
        "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/tables/sp7_numbers.tex",
        "viu-run-sp7 (experiments/configs/sp7_traffic_confirmatory.yaml)"),
    "sp7_results": (
        "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/tables/sp7_results.tex",
        "viu-run-sp7"),
    "sp8_numbers": (
        "results/processed/sp8/SP8_NETWORK_CONFIRMATORY_v1/tables/sp8_numbers.tex",
        "campana SP8_NETWORK_CONFIRMATORY_v1 (no citada por el cuerpo activo)"),
    "sp8_results": (
        "results/processed/sp8/SP8_NETWORK_CONFIRMATORY_v1/tables/sp8_results.tex",
        "campana SP8_NETWORK_CONFIRMATORY_v1"),
    "cargo_e2e_numbers": (
        "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables/cargo_e2e_numbers.tex",
        "viu-run-cargo-e2e"),
    "cargo_e2e_results": (
        "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables/cargo_e2e_results.tex",
        "viu-run-cargo-e2e"),
    "cargo_e2e_hypotheses": (
        "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables/cargo_e2e_hypotheses.tex",
        "viu-run-cargo-e2e"),
    "aws-industrial2-results": (
        "thesis/generated/aws-industrial2-results.tex",
        "scripts/export_aws_industrial2_latex.py"),
    "literature-coverage": (
        "thesis/generated/literature-coverage.tex",
        "pre-thesis/scripts/build_review_figure_data.py"),
    "lit-bibliometric": (
        None,
        "pre-thesis/scripts/build_review_figure_data.py (sin bundle de campana: derivado del corpus de revision)"),
    "lit-corpus-activity": (
        None,
        "pre-thesis/scripts/build_review_figure_data.py (sin bundle de campana: derivado del corpus de revision)"),
}

RE_USE = re.compile(r"shared/generated-macros/([A-Za-z0-9_\-]+)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_lines(a, b):
    la = io.open(a, encoding="utf8", errors="ignore").read().splitlines()
    lb = io.open(b, encoding="utf8", errors="ignore").read().splitlines()
    out = []
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "(ausente)"
        y = lb[i] if i < len(lb) else "(ausente)"
        if x != y:
            out.append((i + 1, x, y))
    return out


def discover_used(thesis_root, census=None):
    """Macros usadas. Con `census`, solo las del cierre real de \\input de
    main-v2.tex; sin el, todo .tex del arbol (util para inventario)."""
    used = set()
    if census and os.path.exists(census):
        import json
        files = json.load(io.open(census, encoding="utf8"))["files"]
        for rel in files:
            p = os.path.join(thesis_root, rel)
            if not os.path.exists(p):
                continue
            used.update(RE_USE.findall(io.open(p, encoding="utf8", errors="ignore").read()))
        return sorted(used)
    for base, _dirs, files in os.walk(thesis_root):
        if "build" in base or ".git" in base:
            continue
        for fn in files:
            if not fn.endswith(".tex"):
                continue
            try:
                txt = io.open(os.path.join(base, fn), encoding="utf8", errors="ignore").read()
            except OSError:
                continue
            used.update(RE_USE.findall(txt))
    return sorted(used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="..")
    ap.add_argument("--census", default="../final-hardening/census.json",
                    help="cierre real de \\input; sin el, se escanea todo el arbol")
    ap.add_argument("--all", action="store_true",
                    help="inventariar todo el arbol, no solo el cuerpo activo")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    thesis = os.path.abspath(".")

    census = None if args.all else args.census
    used = discover_used(thesis, census)
    scope = "todo el arbol" if args.all else "cierre activo de main-v2.tex"
    print("Macros en %s: %d" % (scope, len(used)))

    ok, diverged, unregistered, missing, nobundle = [], [], [], [], []

    for name in used:
        shipped = os.path.join(thesis, "shared", "generated-macros", name + ".tex")
        if name not in REGISTRY:
            unregistered.append(name)
            continue
        bundle_rel, generator = REGISTRY[name]
        if not os.path.exists(shipped):
            missing.append((name, "no existe en shared/generated-macros"))
            continue
        if bundle_rel is None:
            nobundle.append((name, generator))
            continue
        bundle = os.path.join(repo, bundle_rel)
        if not os.path.exists(bundle):
            missing.append((name, "bundle ausente: " + bundle_rel))
            continue
        if sha256(shipped) == sha256(bundle):
            ok.append((name, generator))
        else:
            diverged.append((name, bundle_rel, generator, diff_lines(shipped, bundle)))

    print("  trazables      : %d" % len(ok))
    print("  sin bundle     : %d (derivadas, no de campana numerica)" % len(nobundle))
    print("  SIN REGISTRAR  : %d" % len(unregistered))
    print("  ausentes       : %d" % len(missing))
    print("  DIVERGENTES    : %d" % len(diverged))
    print()

    if ok:
        print("Generador por familia trazable:")
        for name, gen in ok:
            print("  %-26s <- %s" % (name, gen))
        print()

    fail = False

    if unregistered:
        fail = True
        print("SIN FUENTE REGISTRADA (el documento las usa y nadie declara de donde salen):")
        for n in unregistered:
            print("  %s" % n)
        print()

    if missing:
        fail = True
        print("ARTEFACTOS AUSENTES:")
        for n, why in missing:
            print("  %-26s %s" % (n, why))
        print()

    if diverged:
        fail = True
        print("DIVERGENTES (la cifra impresa no es la de la campana):")
        for name, bundle_rel, gen, dl in diverged:
            print("\n  %s" % name)
            print("    bundle   : %s" % bundle_rel)
            print("    regenera : %s" % gen)
            for ln, x, y in dl[:10]:
                print("    L%-4d memoria : %s" % (ln, x))
                print("          campana : %s" % y)
        print()

    if nobundle:
        print("Sin bundle de campana (aceptado, se declara su generador):")
        for n, gen in nobundle:
            print("  %-26s <- %s" % (n, gen))
        print()

    if fail:
        print("FALLO: hay cifras activas sin trazabilidad.")
        return 1
    print("OK: toda cifra activa es trazable a su campana.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
