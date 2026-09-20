# -*- coding: utf-8 -*-
"""Calcos del ingles y construcciones que delatan una traduccion.

No busca anglicismos tecnicos aceptados (bootstrap, commit, wrench), sino giros
que en castellano academico suenan importados: gerundio de posterioridad,
"basado en" por "a partir de", "en orden a", pasiva perifrastica donde el
castellano usa la refleja, "el mismo" como pronombre, adverbios en -mente
encadenados, y el articulo omitido a la inglesa.

    python scripts/sp1_final_figs/calcos.py
"""
from __future__ import annotations

import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))

PATTERNS = [
    ("basado en / basada en",
     r"\bbasad[oa]s?\s+en\b",
     "en castellano academico: «a partir de», «que parte de», «apoyado en»"),
    ("en orden a / en aras de",
     r"\ben orden a\b|\ben aras de\b",
     "calco de «in order to»"),
    ("jugar un papel",
     r"\bjueg[ao]n?\s+un\s+papel\b",
     "calco de «play a role»; en castellano «desempenar»"),
    # Solo el uso PRONOMINAL, que la Academia desaconseja: «el mismo» en lugar
    # de «este» o del nombre. El uso adjetivo ---«la misma vecindad», «las
    # mismas semillas»--- es correcto y no se marca.
    ("el mismo / la misma como pronombre",
     r"\b(?:de|a|en|por|con|sobre)\s+l[oa]s?\s+mism[oa]s?\s*(?=[,.;:)]|\s+(?:"
     r"se|es|son|fue|fueron|permite|permiten|queda|quedan|tiene|tienen)\b)",
     "la Academia lo desaconseja; usar el pronombre o repetir el nombre"),
    ("gerundio de posterioridad",
     r",\s+(?:produciendo|resultando|dando lugar|obteniendo|generando|"
     r"consiguiendo|permitiendo)\b",
     "el gerundio no expresa consecuencia en castellano"),
    ("adverbios en -mente encadenados",
     r"\b\w+mente\s+\w+mente\b", ""),
    ("dos adverbios -mente en la misma frase",
     r"\b\w{4,}mente\b[^.]{0,60}\b\w{4,}mente\b", ""),
    ("«asumir» por «suponer»",
     r"\basum(?:e|en|imos|ir|iendo)\b",
     "«assume» es «suponer»; «asumir» es hacerse cargo"),
    ("«adresar» / «direccionar»", r"\bdireccionar\b|\badresar\b", ""),
    ("«soportar» por «admitir»", r"\bsoport(?:a|an|ar)\b", "«support»"),
    ("«performance» / «approach»", r"\bperformance\b|\bapproach\b", ""),
    ("«librería» por «biblioteca»", r"\blibrer[ií]as?\b", ""),
    ("«previo a» por «antes de»", r"\bprevio a\b", ""),
    ("«a través de» instrumental",
     r"\ba trav[eé]s de (?:un|una|el|la|los|las)\b",
     "si es instrumento, «mediante» o «con»"),
    ("«en base a»", r"\ben base a\b", "incorrecto; «con base en» o «segun»"),
    ("«el cual / la cual»", r"\bel cual\b|\bla cual\b|\blos cuales\b", ""),
    ("«dado que» repetido", r"\bdado que\b", ""),
    ("«ser capaz de»", r"\bcapaz(?:es)? de\b", "calco de «able to»; «puede»"),
    ("«tanto ... como» excesivo", r"\btanto\s+\w+\s+como\b", ""),
    ("«significativo» sin test", r"\bsignificativ", "reservar al sentido estadistico"),
    ("«robusto» sin definir", r"\brobust[oa]s?\b", ""),
    ("«optimizar» como verbo vago", r"\boptimiza(?:r|ndo|do)\b", ""),
]


def prose(path):
    s = io.open(path, encoding="utf-8").read()
    s = re.sub(r"(?s)\\begin\{(equation|align|gathered|aligned|algorithmic|"
               r"algorithm|tabular|tabularx)\*?\}.*?\\end\{\1\*?\}", " ", s)
    s = re.sub(r"(?m)^\s*%.*$", " ", s)
    s = re.sub(r"\$[^$]*\$", " MAT ", s)
    return s


def main() -> int:
    total = 0
    for name in ("sp1.tex", "sp1_anexo.tex"):
        path = os.path.join(SP1, name)
        if not os.path.exists(path):
            continue
        text = prose(path)
        lines = text.split("\n")
        hits = []
        for label, pat, why in PATTERNS:
            rx = re.compile(pat, re.I)
            for i, line in enumerate(lines, 1):
                for m in rx.finditer(line):
                    hits.append((label, i, m.group(0).strip(), why,
                                 line.strip()[:78]))
        if hits:
            print("\n== %s ==" % name)
            for label, i, frag, why, ctx in hits:
                print("  L%-5d %-34s %r" % (i, label, frag))
                if why:
                    print("           %s" % why)
                print("           %s" % ctx)
        total += len(hits)
    print("\ncalcos y giros marcados: %d" % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
