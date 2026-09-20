# -*- coding: utf-8 -*-
"""Capa 4: marcadores finos que las capas 1-3 no miden.

Las capas anteriores dan limpio y el texto sigue oliendo. Eso significa que el
problema no esta en el lexico ni en el molde de parrafo, sino en habitos
sintacticos repetidos que se introdujeron al arreglar los anteriores.

Mide:
  A. apertura por sintagma circunstancial ("Con...", "Al...", "Sobre...")
  B. dos puntos como bisagra afirmacion:desarrollo
  C. raya doble ---inciso--- como parentesis culto
  D. punto y coma que une dos clausulas equilibradas
  E. la referencia a figura siempre en la misma posicion y forma
  F. cadenas de relativas "que + verbo"
  G. coordinacion binaria con "y" como esqueleto unico
  H. uniformidad de tiempo verbal en los resultados
  I. ausencia total de conectores argumentativos (juxtaposicion seca)
  J. cierre de parrafo siempre resolutivo
  K. longitud de parrafo demasiado pareja
  L. formulas de cifra siempre identicas
"""
from __future__ import annotations

import collections
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_audit as A  # noqa: E402

PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "sp1.tex"))


def norm(t):
    tbl = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return t.translate(tbl)


def main():
    pars = A.extract_prose(PATH)
    sents, owner = [], []
    for n, p in pars:
        for s in A.sentences(p):
            sents.append(s)
            owner.append(n)
    total = len(sents)
    words = sum(len(s.split()) for s in sents)
    flagged = collections.defaultdict(list)

    def flag(key, idx, why=""):
        flagged[key].append((owner[idx], sents[idx], why))

    print("=" * 78)
    print("CAPA 4 — MARCADORES SINTACTICOS FINOS")
    print("frases: %d | palabras: %d" % (total, words))
    print("=" * 78)

    # A. apertura circunstancial
    CIRC = re.compile(r"^(Con|Al|Sobre|Sin|Bajo|Tras|Dentro|Para|En|Entre|"
                      r"Cuando|Si|Desde|Hasta|Mediante|Segun)\b")
    for i, s in enumerate(sents):
        if CIRC.match(norm(s)):
            flag("A. apertura circunstancial", i)

    # B. dos puntos bisagra (excluye IC y entradas a ecuacion)
    for i, s in enumerate(sents):
        if ":" in s and not s.rstrip().endswith(":"):
            if not re.search(r"IC 95|95\s*%", s):
                flag("B. dos puntos bisagra", i)

    # C. inciso con raya doble
    for i, s in enumerate(sents):
        if s.count("---") >= 2 or "—" in s:
            flag("C. inciso con raya", i)

    # D. punto y coma uniendo clausulas
    for i, s in enumerate(sents):
        if ";" in s:
            flag("D. punto y coma", i)

    # E. referencia a figura siempre igual
    figref = [i for i, s in enumerate(sents) if "Figura" in s or "CIT" in s]
    paren_end = 0
    for i in figref:
        if re.search(r"\(Figura[^)]*\)\s*[.;:]?\s*$", sents[i]):
            paren_end += 1
            flag("E. figura entre parentesis al final", i)

    # F. cadenas de relativas
    for i, s in enumerate(sents):
        if len(re.findall(r"\bque\b", norm(s))) >= 3:
            flag("F. tres o mas 'que'", i)

    # G. coordinacion binaria como esqueleto
    for i, s in enumerate(sents):
        w = s.split()
        if 12 <= len(w) <= 34 and norm(s).count(" y ") == 1 and "," in s:
            flag("G. binaria con 'y'", i)

    # H. tiempo verbal de los resultados
    past = sum(1 for s in sents
               if re.search(r"\b\w+(o|aron|eron|io)\b", norm(s))
               and re.search(r"\d", s))
    numeric = sum(1 for s in sents if re.search(r"\d", s))

    # I. conectores argumentativos
    CONN = re.compile(r"\b(sin embargo|no obstante|en cambio|ahora bien|"
                      r"por el contrario|aun asi|de hecho|es decir|"
                      r"dicho de otro modo|con todo)\b")
    conn = sum(1 for s in sents if CONN.search(norm(s)))

    # J. cierre de parrafo resolutivo
    for n, p in pars:
        ss = A.sentences(p)
        if not ss:
            continue
        last = ss[-1]
        if re.search(r"(no |nunca |tampoco |solo |unicamente )", norm(last)) \
                and len(last.split()) <= 26:
            i = sents.index(last) if last in sents else None
            if i is not None:
                flag("J. cierre con negacion o restriccion", i)

    plens = [len(A.clean(p).split()) for _n, p in pars]

    # L. formulas de cifra
    forms = collections.Counter()
    for s in sents:
        for m in re.finditer(r"(\d[\d.,]*)\s*\\?,?\s*%", s):
            forms["pct"] += 1
        if re.search(r"de los? \d", norm(s)):
            forms["de los N"] += 1
        if re.search(r"\d+ de (los )?\d", norm(s)):
            forms["N de M"] += 1

    order = ["A. apertura circunstancial", "B. dos puntos bisagra",
             "C. inciso con raya", "D. punto y coma",
             "E. figura entre parentesis al final", "F. tres o mas 'que'",
             "G. binaria con 'y'", "J. cierre con negacion o restriccion"]
    print()
    print("%-42s %6s %8s" % ("marcador", "n", "% frases"))
    print("-" * 60)
    for k in order:
        v = flagged.get(k, [])
        print("%-42s %6d %7.1f %%" % (k, len(v), 100.0 * len(v) / total))
    print()
    print("H. frases numericas en preterito : %d de %d" % (past, numeric))
    print("I. conectores argumentativos     : %d en %d frases (%.1f %%)"
          % (conn, total, 100.0 * conn / total))
    print("K. palabras por parrafo          : media %.1f  desv %.1f  CV %.2f"
          % (statistics.mean(plens), statistics.pstdev(plens),
             statistics.pstdev(plens) / statistics.mean(plens)))
    print("L. formulas de cifra             : %s" % dict(forms))
    print()

    union = set()
    for v in flagged.values():
        for n, s, _w in v:
            union.add(s)
    print("FRASES CON AL MENOS UN MARCADOR   : %d de %d (%.0f %%)"
          % (len(union), total, 100.0 * len(union) / total))
    print()

    for k in order:
        v = flagged.get(k, [])
        if not v:
            continue
        print("-" * 78)
        print("%s  (%d)" % (k, len(v)))
        for n, s, _w in v[:14]:
            print("  L%-5d %s" % (n, s[:96]))
        if len(v) > 14:
            print("  ... y %d mas" % (len(v) - 14))
    print("=" * 78)


if __name__ == "__main__":
    main()
