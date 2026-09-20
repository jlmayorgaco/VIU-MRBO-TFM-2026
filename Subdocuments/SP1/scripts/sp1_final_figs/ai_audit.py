# -*- coding: utf-8 -*-
"""Auditoria profunda de patrones de escritura asistida sobre sp1.tex.

No mide vocabulario "sospechoso": mide ESTRUCTURA. La sensacion de texto
generado procede sobre todo de la regularidad, no del lexico.

Dimensiones:
  1. rafaga (burstiness): varianza de la longitud de frase
  2. uniformidad de parrafo
  3. diversidad de aperturas de frase
  4. estructuras triadicas ("A, B y C")
  5. simetrias sintacticas ("no X sino Y", "tanto X como Y", "ni X ni Y")
  6. densidad de conectores logicos
  7. nominalizaciones
  8. impersonal con "se"
  9. cobertura lexica (TTR) y palabras favoritas
 10. cierres de parrafo evaluativos
 11. subordinacion (comas por frase)
 12. densidad de guiones largos, punto y coma, dos puntos
 13. hedging / matizacion
 14. frases que anuncian, evaluan o guian la lectura
"""
from __future__ import annotations

import collections
import io
import math
import os
import re
import statistics
import sys

# ---------------------------------------------------------------- extraccion

SKIP_BEGIN = re.compile(
    r"\\begin\{(equation|aligned|gathered|align|algorithmic|algorithm|tabularx"
    r"|tabular|tikzpicture|figure|tcolorbox|center|minipage|n1prop|n1lema"
    r"|n1obs|itemize|enumerate)\b")
SKIP_END = re.compile(
    r"\\end\{(equation|aligned|gathered|align|algorithmic|algorithm|tabularx"
    r"|tabular|tikzpicture|figure|tcolorbox|center|minipage|n1prop|n1lema"
    r"|n1obs|itemize|enumerate)\b")
CMD_LINE = re.compile(
    r"^\s*\\(spheading|leveltag|caption|viuownsource|pdfpanel|tikzpanel"
    r"|tikzpanelfit|newpage|vspace|setlength|input|InputIfFileExists|par"
    r"|renewcommand|newcommand|hypersetup|addbibresource|usepackage"
    r"|documentclass|PassOptionsToPackage|floatname|algrenewcommand|algtext"
    r"|makeatletter|makeatother|captionsetup|proofsketch|nopagebreak"
    r"|toprule|midrule|bottomrule|hline|centering|label|tag|item)")


def extract_prose(path):
    """Devuelve [(linea_inicial, parrafo)] con solo prosa corrida del cuerpo."""
    raw = io.open(path, encoding="utf-8").read()
    start = raw.find(r"\begin{document}")
    lines = raw[start:].splitlines()
    offset = raw[:start].count("\n") + 1

    depth = 0
    out, buf, buf_start = [], [], None
    for idx, line in enumerate(lines):
        n = offset + idx
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        opens = len(SKIP_BEGIN.findall(line))
        closes = len(SKIP_END.findall(line))
        if opens or closes:
            depth += opens - closes
            depth = max(0, depth)
            continue
        if depth > 0:
            continue
        if not stripped:
            if buf:
                out.append((buf_start, " ".join(buf)))
                buf, buf_start = [], None
            continue
        if CMD_LINE.match(line):
            continue
        if stripped.startswith("{\\") or stripped in ("}", "{"):
            continue
        if buf_start is None:
            buf_start = n
        buf.append(stripped)
    if buf:
        out.append((buf_start, " ".join(buf)))

    keep = []
    for n, p in out:
        words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}", p)
        if len(words) >= 12:
            keep.append((n, p))
    return keep


def clean(par):
    """Neutraliza matematicas y comandos para contar palabras de prosa."""
    t = re.sub(r"\$[^$]*\$", " MAT ", par)
    t = re.sub(r"\\(cite[a-z]*|ref|eqref)\{[^}]*\}", " CIT ", t)
    t = re.sub(r"\\[a-zA-Z]+\s*", " ", t)
    t = re.sub(r"[{}]", " ", t)
    t = re.sub(r"\\,", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def sentences(par):
    t = clean(par)
    parts = re.split(r"(?<=[.:;])\s+(?=[A-ZÁÉÍÓÚÑ¿«])", t)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def words(t):
    return re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", t.lower())


# ---------------------------------------------------------------- detectores

TRIADA = re.compile(
    r"\b([\wáéíóúñ]+(?:\s+[\wáéíóúñ]+){0,3}),\s+([\wáéíóúñ]+(?:\s+[\wáéíóúñ]+){0,3})"
    r"\s+y\s+([\wáéíóúñ]+(?:\s+[\wáéíóúñ]+){0,3})\b", re.I)
SIMETRIA = [
    ("no X sino Y", re.compile(r"\bno\b[^.;]{2,60}?\bsino\b", re.I)),
    ("no X: Y", re.compile(r"\bno\s+[\wáéíóúñ]+[^.;]{0,40}:\s", re.I)),
    ("tanto X como Y", re.compile(r"\btanto\b[^.;]{2,60}?\bcomo\b", re.I)),
    ("ni X ni Y", re.compile(r"\bni\b[^.;]{2,50}?\bni\b", re.I)),
    ("mientras que", re.compile(r"\bmientras\s+que\b", re.I)),
    ("por un lado / por otro", re.compile(r"\bpor\s+(un|otro)\s+lado\b", re.I)),
    ("X, no Y", re.compile(r",\s*no\s+[\wáéíóúñ]+\.", re.I)),
]
CONECTORES = re.compile(
    r"\b(por tanto|por ello|por eso|de este modo|de esta forma|en consecuencia"
    r"|asi que|de modo que|sin embargo|no obstante|ademas|asimismo|en cambio"
    r"|es decir|en particular|en concreto|dicho de otro modo|en resumen"
    r"|finalmente|en definitiva|por su parte|a su vez|en este sentido)\b", re.I)
NOMINAL = re.compile(
    r"\b\w+(ción|ciones|miento|mientos|encia|encias|idad|idades|anza|anzas)\b",
    re.I)
IMPERSONAL = re.compile(r"\bse\s+[\wáéíóúñ]+(?:a|e|ó|an|en|aron|eron)\b", re.I)
HEDGE = re.compile(
    r"\b(puede|pueden|podria|podrian|suele|suelen|tiende|tienden|parece"
    r"|parecen|en general|no necesariamente|aproximadamente|practicamente"
    r"|casi|quiza|posiblemente|probablemente|hasta cierto punto)\b", re.I)
GUIA = re.compile(
    r"\b(conviene|cabe (destacar|senalar|notar)|es importante|es fundamental"
    r"|resulta (util|necesario)|debe (interpretarse|leerse|entenderse)"
    r"|permite observar|permite ver|como puede|a continuacion|la figura muestra"
    r"|el capitulo|este capitulo|en este punto|la pregunta que surge"
    r"|vale la pena|merece la pena|hay que subrayar)\b", re.I)
EVALUA = re.compile(
    r"\b(principal|fundamental|decisiv\w+|crucial|clave|central|notable"
    r"|destacad\w+|relevante|importante|significativ\w+|contundente"
    r"|aportacion|contribucion|novedos\w+)\b", re.I)
MORALEJA = re.compile(
    r"^(esto|ello|este resultado|esta diferencia|ambas|el resultado|la evidencia"
    r"|el patron|en conjunto|tomad\w+)\b", re.I)


def strip_accents(t):
    tbl = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return t.translate(tbl)


# ---------------------------------------------------------------- informe

def main(path):
    pars = extract_prose(path)
    all_sents, sent_par = [], []
    for n, p in pars:
        ss = sentences(p)
        all_sents.extend(ss)
        sent_par.extend([n] * len(ss))

    lens = [len(s.split()) for s in all_sents]
    plens = [len(clean(p).split()) for _, p in pars]
    nsent_per_par = [len(sentences(p)) for _, p in pars]
    total_words = sum(lens)

    def per1000(n):
        return 1000.0 * n / max(1, total_words)

    print("=" * 78)
    print("AUDITORIA DE PATRONES DE ESCRITURA ASISTIDA — %s"
          % os.path.basename(path))
    print("=" * 78)
    print("parrafos de prosa : %d" % len(pars))
    print("frases            : %d" % len(all_sents))
    print("palabras de prosa : %d" % total_words)
    print()

    # --- 1. rafaga -------------------------------------------------------
    mean_l = statistics.mean(lens)
    sd_l = statistics.pstdev(lens)
    cv_l = sd_l / mean_l
    print("1. RAFAGA (longitud de frase)")
    print("   media %.1f  desv %.1f  CV %.2f" % (mean_l, sd_l, cv_l))
    print("   min %d  P25 %d  mediana %d  P75 %d  max %d"
          % (min(lens), sorted(lens)[len(lens) // 4], statistics.median(lens),
             sorted(lens)[3 * len(lens) // 4], max(lens)))
    hist = collections.Counter((l // 5) * 5 for l in lens)
    print("   histograma (bloques de 5 palabras):")
    for k in sorted(hist):
        print("     %2d-%2d  %s (%d)" % (k, k + 4, "#" * hist[k], hist[k]))
    print("   referencia: prosa humana tecnica CV ~0.55-0.75; LLM sin editar ~0.30-0.45")
    print("   VEREDICTO: %s" % ("OK" if cv_l >= 0.50 else "REVISAR — demasiado uniforme"))
    print()

    # --- 2. parrafos -----------------------------------------------------
    print("2. UNIFORMIDAD DE PARRAFO")
    print("   palabras/parrafo: media %.1f  desv %.1f  CV %.2f"
          % (statistics.mean(plens), statistics.pstdev(plens),
             statistics.pstdev(plens) / statistics.mean(plens)))
    c = collections.Counter(nsent_per_par)
    print("   frases por parrafo: %s"
          % "  ".join("%d frases x%d" % (k, v) for k, v in sorted(c.items())))
    dom = c.most_common(1)[0]
    print("   moda: %d frases en %d de %d parrafos (%.0f %%)"
          % (dom[0], dom[1], len(pars), 100.0 * dom[1] / len(pars)))
    print("   VEREDICTO: %s"
          % ("OK" if dom[1] / len(pars) < 0.40 else "REVISAR — molde dominante"))
    print()

    # --- 3. aperturas ----------------------------------------------------
    print("3. APERTURAS DE FRASE")
    first1 = collections.Counter(strip_accents(s.split()[0].lower()) for s in all_sents)
    first2 = collections.Counter(
        strip_accents(" ".join(s.split()[:2]).lower()) for s in all_sents)
    rep1 = [(k, v) for k, v in first1.most_common(10) if v > 2]
    print("   primera palabra repetida (>2):")
    for k, v in rep1:
        print("     %-14s x%d" % (k, v))
    if not rep1:
        print("     ninguna")
    rep2 = [(k, v) for k, v in first2.most_common(8) if v > 1]
    print("   bigrama inicial repetido:")
    for k, v in rep2:
        print("     %-24s x%d" % (k, v))
    if not rep2:
        print("     ninguno")
    uniq = sum(1 for v in first2.values() if v == 1)
    print("   bigramas iniciales unicos: %d de %d (%.0f %%)"
          % (uniq, len(all_sents), 100.0 * uniq / len(all_sents)))
    art = sum(1 for s in all_sents
              if strip_accents(s.split()[0].lower()) in
              ("el", "la", "los", "las", "un", "una", "este", "esta", "esto",
               "estos", "estas", "ese", "esa", "eso"))
    print("   frases que abren con articulo/demostrativo: %d (%.0f %%)"
          % (art, 100.0 * art / len(all_sents)))
    print("   VEREDICTO: %s"
          % ("OK" if uniq / len(all_sents) > 0.80 else "REVISAR"))
    print()

    # --- 4. triadas ------------------------------------------------------
    print("4. ESTRUCTURAS TRIADICAS  'A, B y C'")
    tri = [(sent_par[i], s) for i, s in enumerate(all_sents) if TRIADA.search(s)]
    print("   %d frases (%.1f por 1000 palabras)" % (len(tri), per1000(len(tri))))
    for n, s in tri:
        print("     L%-5d %s" % (n, s[:96]))
    print("   VEREDICTO: %s"
          % ("OK" if per1000(len(tri)) < 8 else "REVISAR — triada frecuente"))
    print()

    # --- 5. simetrias ----------------------------------------------------
    print("5. SIMETRIAS SINTACTICAS")
    tot_sim = 0
    for name, rx in SIMETRIA:
        hits = [(sent_par[i], s) for i, s in enumerate(all_sents) if rx.search(s)]
        tot_sim += len(hits)
        if hits:
            print("   %-22s %d" % (name, len(hits)))
            for n, s in hits:
                print("       L%-5d %s" % (n, s[:92]))
    print("   total %d (%.1f por 1000 palabras)" % (tot_sim, per1000(tot_sim)))
    print("   VEREDICTO: %s"
          % ("OK" if per1000(tot_sim) < 12 else "REVISAR — paralelismo alto"))
    print()

    # --- 6. conectores ---------------------------------------------------
    print("6. CONECTORES LOGICOS EXPLICITOS")
    con = collections.Counter()
    for s in all_sents:
        for m in CONECTORES.finditer(strip_accents(s)):
            con[m.group(0).lower()] += 1
    print("   total %d (%.1f por 1000 palabras)"
          % (sum(con.values()), per1000(sum(con.values()))))
    for k, v in con.most_common():
        print("     %-18s x%d" % (k, v))
    print("   VEREDICTO: %s"
          % ("OK" if per1000(sum(con.values())) < 15 else "REVISAR"))
    print()

    # --- 7-8. nominalizacion e impersonal --------------------------------
    nom = sum(len(NOMINAL.findall(s)) for s in all_sents)
    imp = sum(len(IMPERSONAL.findall(s)) for s in all_sents)
    print("7. NOMINALIZACIONES  %d  (%.1f/1000)" % (nom, per1000(nom)))
    nomc = collections.Counter()
    for s in all_sents:
        for m in NOMINAL.finditer(s):
            nomc[m.group(0).lower()] += 1
    for k, v in nomc.most_common(12):
        print("     %-18s x%d" % (k, v))
    print("   referencia: prosa tecnica espanola ~35-55/1000")
    print()
    print("8. IMPERSONAL CON 'SE'  %d  (%.1f/1000)" % (imp, per1000(imp)))
    print("   referencia: informe cientifico espanol ~15-30/1000")
    print()

    # --- 9. lexico -------------------------------------------------------
    ws = words(" ".join(all_sents))
    ttr = len(set(ws)) / len(ws)
    print("9. COBERTURA LEXICA")
    print("   tipos %d / ocurrencias %d  TTR %.3f" % (len(set(ws)), len(ws), ttr))
    stop = set("""el la los las un una unos unas de del a al en y o u que se es son
        no por con para su sus lo le les como mas mas si ya pero cada este esta
        estos estas ese esa eso entre sobre sin hasta desde cuando donde cual
        cuales fue fueron ser han ha he tras solo aun aunque tambien""".split())
    cont = [w for w in ws if strip_accents(w) not in stop and len(w) > 3]
    print("   palabras de contenido mas repetidas:")
    for k, v in collections.Counter(cont).most_common(18):
        print("     %-16s x%d" % (k, v))
    print()

    # --- 10. moralejas ---------------------------------------------------
    print("10. CIERRES DE PARRAFO EVALUATIVOS")
    mor = []
    for n, p in pars:
        ss = sentences(p)
        if ss and MORALEJA.search(strip_accents(ss[-1])):
            mor.append((n, ss[-1]))
    print("   %d parrafos cierran con demostrativo resumidor" % len(mor))
    for n, s in mor:
        print("     L%-5d %s" % (n, s[:92]))
    print()

    # --- 11-12. puntuacion -----------------------------------------------
    txt = " ".join(all_sents)
    print("11. SUBORDINACION Y PUNTUACION")
    print("   comas por frase        %.2f" % (txt.count(",") / len(all_sents)))
    print("   punto y coma por frase %.2f" % (txt.count(";") / len(all_sents)))
    print("   dos puntos por frase   %.2f" % (txt.count(":") / len(all_sents)))
    print("   guion largo (---)      %d" % txt.count("---"))
    print("   parentesis             %d" % txt.count("("))
    print("   referencia: punto y coma <=0.15, dos puntos <=0.12")
    print()

    # --- 13. hedging -----------------------------------------------------
    hed = sum(len(HEDGE.findall(strip_accents(s))) for s in all_sents)
    print("12. MATIZACION (hedging)  %d  (%.1f/1000)" % (hed, per1000(hed)))
    nh = sum(1 for s in all_sents if len(HEDGE.findall(strip_accents(s))) >= 2)
    print("   frases con 2+ matizadores: %d" % nh)
    for i, s in enumerate(all_sents):
        if len(HEDGE.findall(strip_accents(s))) >= 2:
            print("     L%-5d %s" % (sent_par[i], s[:92]))
    print()

    # --- 14. guia y autoevaluacion ---------------------------------------
    print("13. FRASES QUE GUIAN LA LECTURA O AUTOEVALUAN")
    g = [(sent_par[i], s) for i, s in enumerate(all_sents)
         if GUIA.search(strip_accents(s))]
    e = [(sent_par[i], s) for i, s in enumerate(all_sents)
         if EVALUA.search(strip_accents(s))]
    print("   guia lectura   : %d" % len(g))
    for n, s in g:
        print("     L%-5d %s" % (n, s[:92]))
    print("   autoevaluacion : %d" % len(e))
    for n, s in e:
        print("     L%-5d %s" % (n, s[:92]))
    print()

    # --- 15. frases largas y muy cortas ----------------------------------
    print("14. EXTREMOS DE LONGITUD (para comprobar que hay variedad real)")
    order = sorted(range(len(all_sents)), key=lambda i: len(all_sents[i].split()))
    print("   MAS CORTAS:")
    for i in order[:5]:
        print("     [%2d] L%-5d %s" % (len(all_sents[i].split()), sent_par[i], all_sents[i][:88]))
    print("   MAS LARGAS:")
    for i in order[-5:]:
        print("     [%2d] L%-5d %s" % (len(all_sents[i].split()), sent_par[i], all_sents[i][:88]))
    print()
    print("=" * 78)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "sp1.tex")
    main(os.path.abspath(target))
