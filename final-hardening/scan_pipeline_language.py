"""Cuenta el lenguaje de pipeline (workflow de software/LLM) en el CUERPO ACTIVO.

Solo recorre el cierre real de \\input de main-v2.tex, tomado de census.json, para
no contar ficheros que el documento no compila.

Uso: python final-hardening/scan_pipeline_language.py [--fix-report]
"""
import argparse
import collections
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THESIS = os.path.join(ROOT, "pre-thesis")
CENSUS = os.path.join(ROOT, "final-hardening", "census.json")

# termino -> (patron, sustitucion sugerida)
TERMS = [
    ("claim-ID",            r"claim-?ID",                      "identificador de afirmacion / eliminar"),
    ("claim",               r"\bclaims?\b",                    "afirmacion"),
    ("gate",                r"\bgates?\b",                     "criterio de validacion / umbral de evidencia"),
    ("artefacto",           r"\bartefactos?\b",                "registro experimental / archivo reproducible"),
    ("hipotesis congelada", r"hip[oó]tesis\s+congelad",        "hipotesis preespecificada"),
    ("congelad*",           r"\bcongelad[oa]s?\b",             "preespecificad* / fijad*"),
    ("macro generada",      r"macros?\s+generad",              "solo en Reproducibilidad"),
    ("pipeline",            r"\bpipelines?\b",                 "protocolo / procedimiento"),
    ("commit",              r"\bcommits?\b",                   "compromiso / confirmacion"),
    ("digest",              r"\bdigests?\b",                   "resumen de versiones"),
    ("belief",              r"\bbeliefs?\b",                   "creencia / estado de informacion"),
    ("smoke/humo",          r"humo acotad|smoke\s*test",       "ensayo funcional preliminar"),
    ("PASS/FAIL/LIMITED",   r"\b(PASS|FAIL|LIMITED|DUPLICATE)\b", "estado en castellano"),
    ("Resultado y alcance", r"Resultado y alcance",            "condensar en tabla transversal"),
    ("no certifica",        r"no certifica",                   "conservar, pero condensar repeticion"),
    ("se conserva",         r"se conserva",                    "variar formulacion"),
    ("Elaboracion propia",  r"Elaboraci[oó]n propia",          "obligatorio VIU: no tocar"),
]


def active_files():
    c = json.load(io.open(CENSUS, encoding="utf8"))
    return [os.path.join(THESIS, f) for f in c["files"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="recorrer todo el arbol, no solo el activo")
    args = ap.parse_args()

    if args.all:
        files = []
        for base, _d, fs in os.walk(os.path.join(THESIS, "sections")):
            files.extend(os.path.join(base, f) for f in fs if f.endswith(".tex"))
    else:
        files = active_files()

    counts = collections.Counter()
    where = collections.defaultdict(collections.Counter)

    for p in files:
        if not os.path.exists(p):
            continue
        txt = io.open(p, encoding="utf8", errors="ignore").read()
        # ignorar lineas de comentario
        txt = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("%"))
        for name, pat, _sug in TERMS:
            n = len(re.findall(pat, txt, flags=re.IGNORECASE if name != "PASS/FAIL/LIMITED" else 0))
            if n:
                counts[name] += n
                where[name][os.path.relpath(p, THESIS).replace("\\", "/")] += n

    print("Ficheros recorridos: %d (%s)" % (len(files), "todo el arbol" if args.all else "cierre activo"))
    print()
    print("%-22s %6s  %s" % ("termino", "n", "sustitucion sugerida"))
    print("-" * 88)
    for name, _pat, sug in TERMS:
        if counts[name]:
            print("%-22s %6d  %s" % (name, counts[name], sug))
    print()
    print("Detalle por fichero (los cinco primeros de cada termino):")
    for name, _pat, _s in TERMS:
        if not counts[name]:
            continue
        top = where[name].most_common(5)
        print("  %-22s %s" % (name, ", ".join("%s(%d)" % (f.split("/")[-1], n) for f, n in top)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
