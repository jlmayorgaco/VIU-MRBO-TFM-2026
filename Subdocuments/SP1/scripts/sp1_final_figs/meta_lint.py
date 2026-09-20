"""Detector de metadiscurso y marcas de auditoria en la prosa de SP1.

Objetivo editorial: el texto debe ser riguroso sin explicar que lo es. Este
guion cuantifica los patrones que producen esa sensacion, para que la poda
final sea medible y no impresionista.

Uso:
    python meta_lint.py [ruta.tex]

Informa: recuento por categoria, densidad por 1000 palabras de prosa y la
localizacion exacta de cada aparicion.
"""
from __future__ import annotations

import io
import os
import re
import sys

# Categorias ordenadas por gravedad editorial.
PATTERNS: list[tuple[str, str, list[str]]] = [
    ("A. Gestion de la lectura", "el narrador dice al lector como interpretar", [
        r"[Cc]onviene (señalar|no leer|leer|precisar|advertir|recordar)",
        r"[Cc]abe (leer|interpretar|señalar)",
        r"[Nn]o cabe (leer|interpretar)",
        r"conviene leerla junto a",
        r"debe leerse",
        r"no debe leerse",
        r"El capítulo responde",
        r"Esta distinción fija la lectura",
    ]),
    ("B. Autoevaluacion del resultado", "el texto califica su propia fuerza", [
        r"más fuerte de lo que parece",
        r"[Ll]a aportación principal",
        r"[Ll]a diferencia decisiva",
        r"evidencia decisiva",
        r"resultado (clave|central|fuerte)",
        r"especialmente (relevante|importante|notable)",
        r"[Ee]s importante (destacar|señalar|notar)",
    ]),
    ("C. Metadiscurso sobre la figura", "habla del panel, no del objeto", [
        r"[Ll]a figura (muestra|permite|ilustra)",
        r"[Ee]l diagrama (muestra|separa|ilustra)",
        r"[Ee]l panel (muestra|describe)",
        r"[Ee]l atlas (fija|muestra)",
        r"[Ll]a síntesis visual",
        r"[Ee]ste panel",
    ]),
    ("D. Cautela repetida en cadena", "una limitacion por oracion, no por resultado", [
        r"y no (mide|constituye|implica|establece|caracteriza)",
        r"[Nn]o constituye",
        r"[Nn]o implica",
        r"[Nn]o establece por sí",
        r"[Nn]o significa que",
        r"[Nn]o debe leerse como",
    ]),
    ("E. Simetria de contraste", "molde 'X hace A; Y hace B' repetido", [
        r"cambia la pregunta",
        r"conserva (este|el mismo) contrato",
        r"resuelve otro problema",
        r"[Ee]l mismo contrato",
    ]),
    ("F. Estructura de checklist", "auditoria visible en el cuerpo", [
        r"Balance teórico",
        r"\\textit\{Demostrado",
        r"\\textit\{Medido",
        r"\\textit\{No afirmado",
    ]),
    ("G. Terminologia pendiente", "AMR y h_c estrella", [
        r"bytes por agente",
        r"bytes/agente",
        r"propuestas físicas",
        r"\brobots?\b(?! móviles)",
    ]),
]

SKIP = re.compile(r"^\s*%")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Lineas de prosa: descarta comentarios y entornos no narrativos."""
    out = []
    depth_env = 0
    for i, line in enumerate(text.splitlines(), 1):
        if SKIP.match(line):
            continue
        if re.search(r"\\begin\{(equation|aligned|gathered|algorithmic|tabularx"
                     r"|tikzpicture)", line):
            depth_env += 1
        if depth_env == 0:
            out.append((i, line))
        if re.search(r"\\end\{(equation|aligned|gathered|algorithmic|tabularx"
                     r"|tikzpicture)", line):
            depth_env = max(0, depth_env - 1)
    return out


def main(path: str) -> int:
    text = io.open(path, encoding="utf-8").read()
    lines = prose_lines(text)
    words = sum(len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", ln))
                for _n, ln in lines)

    total = 0
    print("=" * 72)
    print("Metadiscurso en %s" % os.path.basename(path))
    print("prosa analizada: %d lineas, ~%d palabras" % (len(lines), words))
    print("=" * 72)
    for title, why, pats in PATTERNS:
        hits = []
        for n, ln in lines:
            for p in pats:
                for m in re.finditer(p, ln):
                    hits.append((n, m.group(0).strip()))
        total += len(hits)
        print("\n%-32s %3d  (%s)" % (title, len(hits), why))
        seen = {}
        for n, frag in hits:
            seen.setdefault(frag.lower(), []).append(n)
        for frag, ns in sorted(seen.items(), key=lambda kv: -len(kv[1]))[:6]:
            loc = ", ".join(str(x) for x in ns[:6])
            if len(ns) > 6:
                loc += ", ..."
            print("     %-42s x%-3d  L%s" % (frag[:42], len(ns), loc))

    dens = 1000.0 * total / words if words else 0.0
    print()
    print("=" * 72)
    print("TOTAL %d marcas | densidad %.1f por 1000 palabras" % (total, dens))
    print("Objetivo de la poda final: -30 %% a -35 %% -> <= %d marcas"
          % int(round(total * 0.68)))
    print("=" * 72)
    return total


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "..", "sp1.tex")
    main(os.path.abspath(target))
