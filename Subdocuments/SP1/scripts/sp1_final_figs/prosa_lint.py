# -*- coding: utf-8 -*-
"""Restos de reescritura que un corrector automatico no ve.

Al mover material entre cuerpo y anexo se reescriben remisiones, y ahi se
cuelan defectos que ni LaTeX ni el corrector ortografico detectan: un articulo
duplicado, una minuscula despues de punto, un espacio doble, una remision a
«la Anexo».

    python scripts/sp1_final_figs/prosa_lint.py

Tiene un suelo de falsos positivos irreducible: una etiqueta en negrita
seguida de minuscula, o dos puntos seguidos de minuscula, son correctos en
castellano y el detector no puede distinguirlos sin analizar la frase. Sirve
para comparar entre versiones, no para llegar a cero.
"""
from __future__ import annotations

import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))

CHECKS = [
    ("minuscula despues de punto",
     r"[.:]\s+([a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]{3,})\b"),
    ("articulo duplicado",
     r"\b(el|la|los|las|un|una)\s+(el|la|los|las|un|una)\b"),
    ("genero equivocado en la remision",
     r"\bla\s+Anexo\b|\bel\s+Figura\b|\bla\s+Cuadro\b"),
    ("preposicion duplicada", r"\b(de|en|a|por|con|para)\s+\1\b"),
    ("espacio antes de puntuacion", r"\s+[,;.](?:\s|$)"),
    ("doble espacio en prosa", r"[^\s]  +[^\s]"),
]


def prose(path):
    s = io.open(path, encoding="utf-8").read()
    # Los entornos de figura llevan rutas, medidas y etiquetas que no son
    # prosa; dejarlos dentro llena el informe de falsos positivos.
    s = re.sub(r"(?s)\\begin\{figure\}.*?\\end\{figure\}", " ", s)
    s = re.sub(r"\\anxsection\{[^{}]*\}\{[^{}]*\}", " ", s)
    s = re.sub(r"\\spheading\{[^{}]*\}\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"(?s)\\begin\{(equation|align|gathered|aligned|algorithmic|"
               r"algorithm|tabular|tabularx)\*?\}.*?\\end\{\1\*?\}", " ", s)
    s = re.sub(r"(?m)^\s*%.*$", " ", s)
    # Sin espacios alrededor: si se anaden, la propia sustitucion inventa un
    # «espacio antes de puntuacion» que no esta en el original.
    s = re.sub(r"\$[^$]*\$", "MAT", s)
    s = re.sub(r"\\(cite[pt]|ref|eqref|label)\*?\{[^}]*\}", "CIT", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"\1", s)
    # El nombre del entorno sobrevive a quitar \begin y \end, y aparece
    # despues de un punto como si fuera una palabra en minuscula.
    s = re.sub(r"\\(begin|end)\{[a-zA-Z*]+\}(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)
    return re.sub(r"[{}]", "", s)


def main() -> int:
    total = 0
    for name in ("sp1.tex", "sp1_anexo.tex"):
        path = os.path.join(SP1, name)
        if not os.path.exists(path):
            continue
        text = prose(path)
        flat = " ".join(text.split())
        for label, pat in CHECKS:
            for m in re.finditer(pat, flat):
                frag = flat[max(0, m.start() - 46):m.end() + 34]
                print("  %-32s ...%s..." % (label, frag))
                total += 1
    print("\nrestos de reescritura: %d" % total)
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
