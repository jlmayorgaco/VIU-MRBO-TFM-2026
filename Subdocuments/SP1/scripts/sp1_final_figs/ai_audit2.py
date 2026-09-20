# -*- coding: utf-8 -*-
"""Segunda capa de la auditoria: patrones que los contadores no ven.

  A. la misma proposicion reformulada N veces a lo largo del capitulo
  B. frases de encuadre antes de cada figura (el tic que sustituyo al metadiscurso)
  C. antitesis enmascarada  "X, pero no Y" / "no A: B"
  D. duplicacion casi literal entre parrafos distantes
  E. autorreferencia al documento
  F. pies de figura: longitud, verbos y contenido interpretativo
  G. rimas estructurales: pares de frases con el mismo esqueleto
"""
from __future__ import annotations

import collections
import difflib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ai_audit as A  # noqa: E402

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "sp1.tex")
PATH = os.path.abspath(PATH)


def norm(t):
    t = t.lower()
    tbl = str.maketrans("áéíóúüñ", "aeiouun")
    t = t.translate(tbl)
    return re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\s+", " ", t)).strip()


def main():
    pars = A.extract_prose(PATH)
    sents = []
    for n, p in pars:
        for s in A.sentences(p):
            sents.append((n, s))
    raw = io.open(PATH, encoding="utf-8").read()

    print("=" * 78)
    print("AUDITORIA — CAPA 2: PATRONES ESTRUCTURALES")
    print("=" * 78)
    print()

    # --- A. la misma idea, N veces --------------------------------------
    print("A. LA MISMA PROPOSICION REFORMULADA")
    idea = re.compile(
        r"(deja de|dejan de|ya no|no basta|basta contar|deja de valer"
        r"|deja de bastar|empieza a aceptar|deja de ser)", re.I)
    hits = [(n, s) for n, s in sents if idea.search(norm(s))]
    print("   'cuando las capacidades difieren, contar deja de funcionar'")
    print("   variantes localizadas: %d" % len(hits))
    for n, s in hits:
        print("     L%-5d %s" % (n, s[:104]))
    print()
    fam = collections.Counter()
    for _, s in sents:
        for m in re.finditer(r"\b(deja de|dejan de|deja n de|ya no|no basta)\b",
                             norm(s)):
            fam[m.group(1)] += 1
    print("   giro       frecuencia")
    for k, v in fam.most_common():
        print("     %-12s x%d" % (k, v))
    print()

    # --- B. encuadre antes de figura ------------------------------------
    print("B. FRASES DE ENCUADRE (el tic que sustituyo al metadiscurso)")
    frame = re.compile(
        r"^(con |cuando |si |ordenar |resolver |un |los dos |las tres |ampliar "
        r"|todas las brechas|el lp puede|la calidad se paga|hasta aqui)", re.I)
    setup = []
    for n, p in pars:
        ss = A.sentences(p)
        if not ss:
            continue
        first = norm(ss[0])
        if frame.match(first) and not re.search(r"\d", ss[0][:40]):
            setup.append((n, ss[0]))
    print("   parrafos que abren encuadrando en lugar de dar el dato: %d de %d"
          % (len(setup), len(pars)))
    for n, s in setup:
        print("     L%-5d %s" % (n, s[:104]))
    print()
    anun = re.compile(
        r"(la pregunta es|la comparacion mide|separan los dos|las tres reglas "
        r"siguientes|queda por saber|dos instancias minimas|tiene que ser fiable"
        r"|pero no cuanto|tiene un precio)", re.I)
    an = [(n, s) for n, s in sents if anun.search(norm(s))]
    print("   de esas, ANUNCIAN explicitamente lo que viene: %d" % len(an))
    for n, s in an:
        print("     L%-5d %s" % (n, s[:104]))
    print()

    # --- C. antitesis enmascarada ---------------------------------------
    print("C. ANTITESIS ENMASCARADA")
    ant = [
        ("X, pero no Y", re.compile(r",\s*pero no\b", re.I)),
        ("A; B (clausulas balanceadas)", re.compile(r"[a-z]{3,};\s*[a-z]{3,}")),
        ("no A, B", re.compile(r"\bno\s+\w+,\s+\w+", re.I)),
        ("puede X, pero", re.compile(r"\bpuede\b[^.;]{3,50}\bpero\b", re.I)),
        ("X o no X", re.compile(r"\b(\w+)\b[^.;]{0,20}\bo no\s+\1?", re.I)),
        ("no A sino/mas bien B", re.compile(r"\bno\b[^.;]{2,60}\b(sino|mas bien)\b", re.I)),
    ]
    tot = 0
    for name, rx in ant:
        h = [(n, s) for n, s in sents if rx.search(norm(s))]
        tot += len(h)
        if h:
            print("   %-30s %d" % (name, len(h)))
            for n, s in h:
                print("       L%-5d %s" % (n, s[:98]))
    print("   total %d en %d frases (%.0f %%)"
          % (tot, len(sents), 100.0 * tot / len(sents)))
    print()

    # --- D. duplicacion entre parrafos distantes ------------------------
    print("D. DUPLICACION CASI LITERAL ENTRE PASAJES DISTANTES")
    seen = []
    for n, s in sents:
        ns = norm(s)
        if len(ns.split()) < 6:
            continue
        for n2, s2, ns2 in seen:
            r = difflib.SequenceMatcher(None, ns, ns2).ratio()
            if r > 0.62 and abs(n - n2) > 20:
                print("   %.0f %% similar" % (100 * r))
                print("     L%-5d %s" % (n2, s2[:96]))
                print("     L%-5d %s" % (n, s[:96]))
        seen.append((n, s, ns))
    print()

    # --- E. autorreferencia ---------------------------------------------
    print("E. AUTORREFERENCIA AL DOCUMENTO")
    selfref = re.compile(r"(este capitulo|del capitulo|el capitulo|aqui\b|mas adelante"
                         r"|se recoge en el anexo|en el anexo)", re.I)
    sr = [(n, s) for n, s in sents if selfref.search(norm(s))]
    print("   %d frases" % len(sr))
    for n, s in sr:
        print("     L%-5d %s" % (n, s[:104]))
    print()

    # --- F. pies de figura ----------------------------------------------
    print("F. PIES DE FIGURA")
    caps = re.findall(r"\\caption\{(.*?)\}\s*\n\s*\\viuownsource", raw, re.S)
    caps += re.findall(r"\\caption\{(.*?)\}\s*\n\s*\\label", raw, re.S)
    print("   pies encontrados: %d" % len(caps))
    interp = re.compile(
        r"(muestra|demuestra|permite|evidencia|confirma|indica que|revela"
        r"|se observa|por tanto|delimita|separa el efecto|respalda)", re.I)
    for c in caps:
        t = A.clean(c)
        nw = len(t.split())
        ns = len([x for x in re.split(r"\.(?:\s|$)", t) if x.strip()])
        flag = "  <-- INTERPRETA" if interp.search(norm(t)) else ""
        warn = "  <-- >2 frases" if ns > 2 else ""
        print("     [%2d palabras, %d frases]%s%s %s" % (nw, ns, flag, warn, t[:86]))
    print()

    # --- G. rimas estructurales -----------------------------------------
    print("G. RIMAS ESTRUCTURALES (frases con el mismo esqueleto)")
    def skeleton(s):
        t = norm(s)
        t = re.sub(r"\b\d[\d ]*\b", "#", t)
        w = t.split()
        return " ".join(w[:3] + ["..."] + w[-3:]) if len(w) > 6 else t
    sk = collections.Counter()
    skmap = collections.defaultdict(list)
    for n, s in sents:
        k = skeleton(s)
        tail = " ".join(norm(s).split()[-3:])
        sk[tail] += 1
        skmap[tail].append((n, s))
    for k, v in sk.most_common():
        if v > 1 and len(k.split()) >= 2:
            print("   cierre repetido '%s' x%d" % (k, v))
            for n, s in skmap[k]:
                print("       L%-5d %s" % (n, s[:98]))
    print()
    print("=" * 78)


if __name__ == "__main__":
    main()
