"""Fuente canonica unica de las cifras de SP1.

Regla: RAW congelado -> este guion -> macros LaTeX -> texto, tablas y figuras.
Ningun numero del capitulo debe escribirse a mano si existe aqui como metrica.

Cada metrica declara su SOPORTE en el propio nombre de la macro, porque toda la
discrepancia detectada entre el capitulo y el re-analisis procedia de soportes
distintos que el texto no declaraba:

  full     : los 1200 mundos de la campana
  cert     : mundos con optimo MILP certificado
  common   : mundos donde TODOS los metodos comparados entregan salida factible
             y el oraculo certifico el optimo

Emite:
  generated/sp1-final/canonical_metrics.tex   macros LaTeX
  generated/sp1-final/canonical_metrics.csv   tabla de auditoria
"""
from __future__ import annotations

import collections
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from thesis_style import (CSVDIR, boot_ci, fbool, fnum, median, read_raw,  # noqa: E402
                          wilson_ci)

GIT_SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True,
                        check=False).stdout.strip() or "unknown"

AUDIT: list[dict] = []
MACROS: list[tuple[str, str]] = []


def esp(value, decimals=1):
    """Numero en convencion espanola, con coma decimal y separador fino."""
    if value is None:
        return "---"
    txt = ("%%.%df" % decimals) % value
    intpart, _, dec = txt.partition(".")
    neg = intpart.startswith("-")
    intpart = intpart.lstrip("-")
    groups = []
    while len(intpart) > 3:
        groups.insert(0, intpart[-3:])
        intpart = intpart[:-3]
    groups.insert(0, intpart)
    out = "\\,".join(groups)
    if dec:
        out += "{,}" + dec
    return ("-" if neg else "") + out


def emit(name, value, decimals, raw_file, support, definition, where,
         claim_id="", campaign="", metric="", method="",
         n_total="", n_used="", ci_low="", ci_high="", filt=""):
    MACROS.append((name, esp(value, decimals)))
    AUDIT.append({
        "claim_id": claim_id or name,
        "campaign": campaign,
        "metric": metric,
        "method": method,
        "macro": "\\" + name,
        "denominator_definition": support,
        "n_total": n_total,
        "n_used": n_used,
        "estimate": "" if value is None else round(value, 4),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "source_csv": raw_file,
        "filter": filt,
        "definition": definition,
        "appears_in": where,
        "script": "scripts/sp1_final_figs/canonical_metrics.py",
        "git_sha": GIT_SHA,
    })


# ===================================================================== N4 E4
E4 = read_raw("n4_v2/raw/e4_family_runs.csv")
BW = collections.defaultdict(dict)
for r in E4:
    BW[r["world_key"]][r["method"]] = r

ORDER = [("geo_qpg_u", "BR"), ("geo_qpg_p", "TwoBR"), ("geo_qpg_c3", "CThree")]
MAIN = [m for m, _ in ORDER]

full = set(BW)
cert = {w for w in full
        if all(m in BW[w] for m in MAIN)
        and fbool(BW[w][MAIN[0]]["oracle_certified"])}
common = {w for w in sorted(cert) if all(fbool(BW[w][m]["feasible"]) for m in MAIN)}

emit("SPoneCertWorlds", float(len(cert)), 0,
     "n4_v2/e4_family_runs.csv", "cert",
     "mundos con optimo MILP certificado", "N4 texto")
emit("SPoneCommonWorlds", float(len(common)), 0,
     "n4_v2/e4_family_runs.csv", "common",
     "BR, 2BR y C3 factibles y oraculo certificado", "N4 texto, F7")

for method, tag in ORDER:
    # (a) soporte comun: la comparacion que el texto declara
    g_common = [100 * fnum(BW[w][method]["optimality_gap"]) for w in sorted(common)]
    g_common = [g for g in g_common if g is not None]
    lo, hi = boot_ci(g_common)
    emit("SPone%sGapCommon" % tag, median(g_common), 1,
         "n4_v2/e4_family_runs.csv", "common",
         "mediana de la brecha sobre soporte comun", "N4 texto, F7A",
         campaign="N4.E4", metric="brecha mediana frente al MILP [%]",
         method=tag, n_total=len(full), n_used=len(common),
         ci_low=round(lo, 2) if lo is not None else "",
         ci_high=round(hi, 2) if hi is not None else "",
         filt="oracle_certified AND todos los metodos factibles")
    emit("SPone%sGapCommonLo" % tag, lo, 1, "n4_v2/e4_family_runs.csv",
         "common", "IC 95 % bootstrap, extremo inferior", "N4 texto")
    emit("SPone%sGapCommonHi" % tag, hi, 1, "n4_v2/e4_family_runs.csv",
         "common", "IC 95 % bootstrap, extremo superior", "N4 texto")

    # (b) soporte por metodo: la definicion que uso la campana original
    g_own = [100 * fnum(BW[w][method]["optimality_gap"]) for w in sorted(cert)
             if fnum(BW[w][method]["optimality_gap"]) is not None]
    emit("SPone%sGapOwn" % tag, median(g_own), 1,
         "n4_v2/e4_family_runs.csv", "cert (filas factibles de cada metodo)",
         "mediana per-metodo; definicion de family_summary.csv", "solo auditoria")

    k_inf = sum(1 for w in sorted(cert) if not fbool(BW[w][method]["feasible"]))
    p, plo, phi = wilson_ci(k_inf, len(cert))
    emit("SPone%sInfeasPct" % tag, 100 * p, 2,
         "n4_v2/e4_family_runs.csv", "cert",
         "riesgo de infactibilidad, IC de Wilson", "N4 texto, F7B",
         campaign="N4.E4", metric="P(infactible | oraculo factible)",
         method=tag, n_total=len(full), n_used=len(cert),
         ci_low=round(100 * plo, 2), ci_high=round(100 * phi, 2),
         filt="oracle_certified")
    emit("SPone%sFeasN" % tag, float(len(cert) - k_inf), 0,
         "n4_v2/e4_family_runs.csv", "cert",
         "mundos factibles sobre el soporte certificado", "N4 texto",
         campaign="N4.E4", metric="mundos factibles", method=tag,
         n_total=len(full), n_used=len(cert), filt="oracle_certified")
    emit("SPone%sFeasRound" % tag, 100.0 * (len(cert) - k_inf) / len(cert), 1,
         "n4_v2/e4_family_runs.csv", "cert",
         "P(factible | oraculo factible), una decimal", "N4 texto",
         campaign="N4.E4", metric="P(factible | oraculo factible) [1 dec]",
         method=tag, n_total=len(full), n_used=len(cert),
         filt="oracle_certified")
    kf = len(cert) - k_inf
    pf, pflo, pfhi = wilson_ci(kf, len(cert))
    emit("SPone%sFeasPct" % tag, 100 * pf, 2,
         "n4_v2/e4_family_runs.csv", "cert",
         "P(factible | oraculo factible), IC de Wilson", "N4 texto",
         campaign="N4.E4", metric="P(factible | oraculo factible)",
         method=tag, n_total=len(full), n_used=len(cert),
         ci_low=round(100 * pflo, 2), ci_high=round(100 * pfhi, 2),
         filt="oracle_certified")

# contraste pareado C3 - BR sobre el mismo soporte comun
pair = []
for w in common:
    a = fnum(BW[w]["geo_qpg_c3"]["optimality_gap"])
    b = fnum(BW[w]["geo_qpg_u"]["optimality_gap"])
    if a is not None and b is not None:
        pair.append(100 * (a - b))
plo, phi = boot_ci(pair)
emit("SPoneCThreeMinusBRCommon", median(pair), 1,
     "n4_v2/e4_family_runs.csv", "common",
     "mediana de las diferencias pareadas C3 menos BR", "N4 texto",
     campaign="N4.E4", metric="diferencia pareada de brecha [pp]",
     method="C3-BR", n_total=len(full), n_used=len(common),
     ci_low=round(plo, 2) if plo is not None else "",
     ci_high=round(phi, 2) if phi is not None else "",
     filt="soporte comun")
emit("SPoneCThreeMinusBRCommonLo", plo, 1, "n4_v2/e4_family_runs.csv",
     "common", "IC 95 % bootstrap pareado", "N4 texto")
emit("SPoneCThreeMinusBRCommonHi", phi, 1, "n4_v2/e4_family_runs.csv",
     "common", "IC 95 % bootstrap pareado", "N4 texto")

# --------------------------------------------------------------- DMIS vs CF
arch = {w for w in full if "geo_qpg_cf" in BW[w] and "geo_qpg_d" in BW[w]}
arch_cert = {w for w in arch if fbool(BW[w]["geo_qpg_cf"]["oracle_certified"])}

for label, sup_set in (("Full", arch), ("Cert", arch_cert)):
    delta = []
    for w in sorted(sup_set):
        a = fnum(BW[w]["geo_qpg_d"]["bytes_per_agent"])
        b = fnum(BW[w]["geo_qpg_cf"]["bytes_per_agent"])
        if a is not None and b is not None:
            delta.append(a - b)
    lo, hi = boot_ci(delta)
    sup = "full" if label == "Full" else "cert"
    emit("SPoneDmisBytesDelta%s" % label, median(delta), 0,
         "n4_v2/e4_family_runs.csv", sup,
         "mediana de las diferencias pareadas DMIS+TX menos CF",
         "N4 texto" if label == "Cert" else "solo auditoria")
    emit("SPoneDmisBytesDelta%sLo" % label, lo, 0,
         "n4_v2/e4_family_runs.csv", sup, "IC 95 % bootstrap", "N4 texto")
    emit("SPoneDmisBytesDelta%sHi" % label, hi, 0,
         "n4_v2/e4_family_runs.csv", sup, "IC 95 % bootstrap", "N4 texto")
    emit("SPoneDmisWorlds%s" % label, float(len(sup_set)), 0,
         "n4_v2/e4_family_runs.csv", sup, "pares comparados", "N4 texto")

# --------------------------------------- DMIS+TX frente a CF, mundo a mundo
#
# La igualdad de medianas no basta para afirmar que la arquitectura no altera el
# resultado: podrian compensarse mundos distintos. Se comprueba la identidad
# pareada del objetivo.
same, worst, both = 0, 0.0, 0
for w in sorted(arch):
    a = fnum(BW[w]["geo_qpg_d"]["distance_cost"])
    b = fnum(BW[w]["geo_qpg_cf"]["distance_cost"])
    if a is None or b is None:
        continue
    both += 1
    delta = abs(a - b)
    worst = max(worst, delta)
    if delta <= 1e-9:
        same += 1
emit("SPoneDmisSameObjN", float(same), 0, "n4_v2/e4_family_runs.csv", "full",
     "mundos con objetivo identico entre DMIS+TX y CF", "N4 texto",
     campaign="N4.E4", metric="mundos con J identico", method="DMIS+TX vs CF",
     n_total=len(full), n_used=both, filt="ambos metodos presentes")
emit("SPoneDmisPairedN", float(both), 0, "n4_v2/e4_family_runs.csv", "full",
     "pares comparados", "N4 texto")
MACROS.append(("SPoneDmisMaxObjDelta", "%.1e" % worst if worst else "0"))

# ===================================================================== N4 E9
E9 = read_raw("n4_v4/raw/e9_hstar_runs.csv")
MAINBLOCK = [r for r in E9 if r["block"] == "frozen_main"]
counts = collections.Counter(r["hstar_category"] for r in MAINBLOCK)
emit("SPoneHstarWorlds", float(len(MAINBLOCK)), 0,
     "n4_v4/e9_hstar_runs.csv", "bloque confirmatorio",
     "mundos del bloque frozen_main", "N4 texto, F7C")
for cat, tag in (("2", "Two"), ("3", "Three"), (">3", "NotFound")):
    emit("SPoneHstar%sCount" % tag, float(counts.get(cat, 0)), 0,
         "n4_v4/e9_hstar_runs.csv", "bloque confirmatorio",
         "recuento de la categoria de h_c*", "N4 texto, F7C")
    emit("SPoneHstar%sPct" % tag, 100.0 * counts.get(cat, 0) / len(MAINBLOCK), 1,
         "n4_v4/e9_hstar_runs.csv", "bloque confirmatorio",
         "porcentaje de la categoria de h_c*", "N4 texto, F7C")

# ===================================================================== N3
E2 = read_raw("n3_v2/raw/e2_runs.csv")
BW3 = collections.defaultdict(dict)
for r in E2:
    BW3[r["world_key"]][r["method"]] = r
M3 = ["capacity_cbba_rb", "weighted_grape", "weighted_pair_grape"]
T3 = {"capacity_cbba_rb": "Cbba", "weighted_grape": "Grape",
      "weighted_pair_grape": "PairGrape"}


def feas3(row):
    return row.get("raw_certificate", "").upper() == "FEASIBLE"


cert3 = {w for w, d in BW3.items() if all(m in d for m in M3)
         and fbool(d[M3[0]]["oracle_certified"])}
common3 = {w for w in sorted(cert3) if all(feas3(BW3[w][m]) for m in M3)}
emit("SPoneNThreeCommonWorlds", float(len(common3)), 0,
     "n3_v2/e2_runs.csv", "common", "los tres metodos factibles y certificado",
     "N3 texto, F5")
for m in M3:
    g = [100 * fnum(BW3[w][m]["optimality_gap"]) for w in common3]
    g = [x for x in g if x is not None]
    emit("SPoneNThree%sGap" % T3[m], median(g), 1, "n3_v2/e2_runs.csv",
         "common", "mediana de la brecha sobre soporte comun", "N3 texto, F5")
    b = [fnum(BW3[w][m]["bytes_per_agent"]) for w in sorted(cert3)]
    emit("SPoneNThree%sBytes" % T3[m], median(b), 0, "n3_v2/e2_runs.csv",
         "cert", "mediana de bytes/AMR", "N3 texto, F5")
    k = sum(1 for w in sorted(cert3) if feas3(BW3[w][m]))
    p, _lo, _hi = wilson_ci(k, len(cert3))
    emit("SPoneNThree%sFeas" % T3[m], 100 * p, 1, "n3_v2/e2_runs.csv",
         "cert", "factibilidad condicionada al oraculo", "N3 texto, F5")

# ===================================================================== salida
os.makedirs(CSVDIR, exist_ok=True)
tex = os.path.join(CSVDIR, "canonical_metrics.tex")
with open(tex, "w", encoding="utf-8") as fh:
    fh.write("% Generado por scripts/sp1_final_figs/canonical_metrics.py\n")
    fh.write("% NO EDITAR A MANO. Fuente: RAW congelado en sp1_levels.\n")
    for name, value in MACROS:
        fh.write("\\newcommand{\\%s}{%s}\n" % (name, value))

aud = os.path.join(CSVDIR, "canonical_metrics.csv")
with open(aud, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=[
        "claim_id", "campaign", "metric", "method", "macro",
        "denominator_definition", "n_total", "n_used",
        "estimate", "ci_low", "ci_high",
        "source_csv", "filter", "definition", "appears_in",
        "script", "git_sha"])
    w.writeheader()
    w.writerows(AUDIT)

print("macros emitidas : %d -> %s" % (len(MACROS), os.path.relpath(tex)))
print("tabla auditoria : %s" % os.path.relpath(aud))
print()
print("=== CIFRAS EN DISPUTA ===")
look = {n: v for n, v in MACROS}
for n in ("SPoneTwoBRGapCommon", "SPoneTwoBRGapOwn",
          "SPoneCThreeGapCommon", "SPoneCThreeGapOwn",
          "SPoneDmisBytesDeltaFull", "SPoneDmisBytesDeltaCert",
          "SPoneCommonWorlds", "SPoneCertWorlds"):
    print("  %-28s %s" % (n, look.get(n)))
