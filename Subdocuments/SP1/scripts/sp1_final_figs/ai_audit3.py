# -*- coding: utf-8 -*-
"""Tercera capa: pies con parser de llaves, titulos y ritmo de la cifra."""
from __future__ import annotations

import collections
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_audit as A  # noqa: E402

PATH = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "sp1.tex"))


def balanced(text, start):
    """Devuelve el contenido de {...} que empieza en text[start] == '{'."""
    depth, i = 0, start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return "", start


def norm(t):
    tbl = str.maketrans("áéíóúüñ", "aeiouun")
    return re.sub(r"\s+", " ", t.lower().translate(tbl)).strip()


def main():
    raw = io.open(PATH, encoding="utf-8").read()
    body = raw[raw.find(r"\begin{document}"):]

    print("=" * 78)
    print("AUDITORIA — CAPA 3: PIES, TITULOS Y RITMO")
    print("=" * 78)
    print()

    # --- pies con parser de llaves --------------------------------------
    caps = []
    for m in re.finditer(r"\\caption\s*\{", body):
        c, _ = balanced(body, m.end() - 1)
        caps.append(c)
    print("A. PIES DE FIGURA  (%d)" % len(caps))
    interp = re.compile(
        r"\b(muestra|demuestra|permite|evidencia|revela|se observa|por tanto"
        r"|delimita|respalda|sostiene|indica que|separa el efecto|sugiere)\b")
    long_caps, interp_caps = 0, 0
    for c in caps:
        t = A.clean(c)
        nw = len(t.split())
        ns = len([x for x in re.split(r"\.(?:\s|$)", t) if x.strip()])
        flags = []
        if ns > 2:
            flags.append("MAS DE 2 FRASES")
            long_caps += 1
        if interp.search(norm(t)):
            flags.append("INTERPRETA")
            interp_caps += 1
        tag = ("  <<< " + " / ".join(flags)) if flags else ""
        print("   [%2dp %df]%s" % (nw, ns, tag))
        print("        %s" % t[:100])
    print()
    print("   pies con mas de 2 frases : %d de %d" % (long_caps, len(caps)))
    print("   pies que interpretan     : %d de %d" % (interp_caps, len(caps)))
    ws = [len(A.clean(c).split()) for c in caps]
    print("   palabras: media %.1f  min %d  max %d"
          % (sum(ws) / len(ws), min(ws), max(ws)))
    print()

    # --- titulos ---------------------------------------------------------
    print("B. ENCABEZADOS DE SECCION")
    heads = []
    for m in re.finditer(r"\\spheading\s*\{", body):
        tag, nxt = balanced(body, m.end() - 1)
        j = body.find("{", nxt)
        title, _ = balanced(body, j)
        heads.append((tag, title))
    print("   %d encabezados" % len(heads))
    lens = [len(t.split()) for _, t in heads]
    print("   palabras del titulo: media %.1f  min %d  max %d  CV %.2f"
          % (sum(lens) / len(lens), min(lens), max(lens),
             (sum((x - sum(lens) / len(lens)) ** 2 for x in lens) / len(lens))
             ** 0.5 / (sum(lens) / len(lens))))
    firstw = collections.Counter(norm(t).split()[0] for _, t in heads)
    print("   primera palabra del titulo:")
    for k, v in firstw.most_common():
        print("     %-16s x%d" % (k, v))
    print()
    for tag, title in heads:
        print("     %-46s | %s" % (tag[:46], title[:44]))
    print()

    # --- ritmo de la cifra ----------------------------------------------
    print("C. RITMO: ¿DONDE CAE LA CIFRA EN LA FRASE?")
    pars = A.extract_prose(PATH)
    sents = []
    for n, p in pars:
        sents.extend((n, s) for s in A.sentences(p))
    numeric = [(n, s) for n, s in sents if re.search(r"\d", s)]
    end_num, start_num = 0, 0
    for n, s in numeric:
        w = s.split()
        tail = " ".join(w[-4:])
        head = " ".join(w[:4])
        if re.search(r"\d", tail):
            end_num += 1
        if re.search(r"\d", head):
            start_num += 1
    print("   frases con cifra: %d de %d" % (len(numeric), len(sents)))
    print("   la cifra cae en las 4 ultimas palabras : %d (%.0f %%)"
          % (end_num, 100.0 * end_num / max(1, len(numeric))))
    print("   la cifra cae en las 4 primeras palabras: %d (%.0f %%)"
          % (start_num, 100.0 * start_num / max(1, len(numeric))))
    print("   (una proporcion muy alta al final = cadencia de informe generado)")
    print()

    # --- espejo apertura / cierre ---------------------------------------
    print("D. ESPEJO ENTRE APERTURA Y CIERRE")
    op = [s for n, s in sents if n in (167, 173)]
    cl = [s for n, s in sents if n in (1108, 1112, 1119)]
    print("   APERTURA (L167-L173):")
    for s in op:
        print("     %s" % s[:100])
    print("   CIERRE (L1108-L1119):")
    for s in cl:
        print("     %s" % s[:100])
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
