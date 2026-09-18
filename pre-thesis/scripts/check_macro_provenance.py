"""Comprueba que cada fichero de macros generadas que usa la memoria coincide,
byte a byte, con el fichero equivalente del bundle de su campana.

Una cifra impresa en la memoria que no coincide con el bundle de la campana no
es trazable: o se regenera, o se documenta por que difiere. Este guion detecta
esa divergencia, que de otro modo solo aparece comparando a mano.

Uso: python scripts/check_macro_provenance.py [--repo RAIZ]
Salida: 0 si todo es trazable; 1 si hay divergencias o bundles ausentes.
"""
import argparse
import hashlib
import io
import os
import sys

# shipped (relativo a pre-thesis/) -> bundle de campana (relativo a la raiz)
PAIRS = {
    "shared/generated-macros/sp3_numbers.tex":
        "results/processed/sp3/SP3_WRENCH_EVIDENCE_v1/tables/sp3_numbers.tex",
    "shared/generated-macros/sp6_numbers.tex":
        "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/tables/sp6_numbers.tex",
    "shared/generated-macros/sp7_numbers.tex":
        "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/tables/sp7_numbers.tex",
    "shared/generated-macros/sp8_numbers.tex":
        "results/processed/sp8/SP8_NETWORK_CONFIRMATORY_v1/tables/sp8_numbers.tex",
    "shared/generated-macros/cargo_e2e_numbers.tex":
        "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables/cargo_e2e_numbers.tex",
    "shared/generated-macros/sp6_results.tex":
        "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/tables/sp6_results.tex",
    "shared/generated-macros/sp7_results.tex":
        "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/tables/sp7_results.tex",
    "shared/generated-macros/cargo_e2e_results.tex":
        "results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/tables/cargo_e2e_results.tex",
}


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="..")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)

    ok, diverged, missing = 0, [], []
    for shipped_rel, bundle_rel in sorted(PAIRS.items()):
        shipped = os.path.join(os.path.abspath("."), shipped_rel)
        bundle = os.path.join(repo, bundle_rel)
        if not os.path.exists(shipped):
            missing.append((shipped_rel, "shipped ausente"))
            continue
        if not os.path.exists(bundle):
            missing.append((shipped_rel, "bundle ausente: " + bundle_rel))
            continue
        if sha(shipped) == sha(bundle):
            ok += 1
        else:
            diverged.append((shipped_rel, bundle_rel, diff_lines(shipped, bundle)))

    print("Trazables (identicos al bundle): %d" % ok)

    if missing:
        print("\nSin bundle comparable: %d" % len(missing))
        for rel, why in missing:
            print("  %-46s %s" % (rel, why))

    if diverged:
        print("\nDIVERGENTES: %d" % len(diverged))
        for shipped_rel, bundle_rel, dl in diverged:
            print("\n  %s" % shipped_rel)
            print("    bundle: %s" % bundle_rel)
            for ln, x, y in dl[:12]:
                print("    L%-4d memoria : %s" % (ln, x))
                print("          campana : %s" % y)
        print("\nUna cifra que no coincide con su campana no es trazable.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
