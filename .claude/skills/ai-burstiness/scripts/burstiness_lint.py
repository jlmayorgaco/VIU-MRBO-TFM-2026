"""Linter de ritmo de prosa para el TFM en español.

Mide lo que un detector de texto generado cuantifica y que ni `no-ai-slop` ni
`tfm-voice` miden: varianza de longitud de frase, uniformidad de parrafo,
densidad de conectores de apertura y plantillas de bloque repetidas.

NO mide lexico (eso es no-ai-slop) ni registro (eso es tfm-voice).
NO propone reescrituras: senala donde mirar.

Uso:
    python burstiness_lint.py fichero.tex [fichero2.tex ...]
    python burstiness_lint.py --census final-hardening/census.json --root pre-thesis
    python burstiness_lint.py --json salida.json fichero.tex
"""
import argparse
import io
import json
import os
import re
import statistics
import sys

BS = chr(92)

# --- umbrales del criterio de aceptacion (SKILL.md §6) ---
MIN_SD = 8.0            # desviacion tipica de longitud de frase, en palabras
MIN_SHORT = 10          # al menos una frase por debajo
MIN_LONG = 35           # al menos una frase por encima
PARA_MIN = 3            # minimo VIU de oraciones por parrafo
PARA_MAX = 10
PARA_MODE_MAX = 0.70    # fraccion maxima de parrafos con el mismo numero de frases
CONN_PER_100 = 6.0
MIN_SENTENCES = 15      # por debajo de esto, la estadistica no dice nada
PROSE_PAR_MIN_WORDS = 30  # menos que esto tras limpiar LaTeX es un fragmento, no un parrafo

# --- conectores de apertura (SKILL.md R4) ---
SUPRIMIR_SIEMPRE = [
    "cabe destacar", "cabe señalar", "cabe mencionar", "cabe recordar",
    "es importante destacar", "es importante señalar", "conviene recordar",
    "conviene señalar", "nótese que", "obsérvese que", "como se puede observar",
    "como puede observarse", "claramente", "evidentemente", "notablemente",
]
LIMITAR = [
    "además", "asimismo", "por otra parte", "en este sentido", "por su parte",
    "por tanto", "por consiguiente", "en consecuencia", "de este modo",
    "en conclusión", "en resumen", "en definitiva",
]

# --- limpieza de LaTeX ---
RE_COMMENT = re.compile(r"(?<!" + BS + BS + r")%.*$", re.M)
RE_DISPLAY = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?\\end\{\1\*?\}",
    re.S)
RE_ENV_SKIP = re.compile(
    r"\\begin\{(table|tabular|tabularx|figure|algorithm|algorithmic|tikzpicture|"
    r"lstlisting|verbatim|description|itemize|enumerate|teorema|theorem|proposicion|"
    r"proposition|lema|lemma|corolario|corollary|definicion|definition|proof|"
    r"contribucion)\*?\}.*?\\end\{\1\*?\}", re.S)
RE_INLINE_MATH = re.compile(r"\$[^$]*\$")
RE_CMD_ARG = re.compile(r"\\(?:label|ref|eqref|cite\w*|parencite\*?|textcite|"
                        r"viusource|viuownsource|zlabel|input|include|caption)"
                        r"\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?")
RE_CMD = re.compile(r"\\[a-zA-Z@]+\*?")
RE_BRACES = re.compile(r"[{}]")


def strip_latex(text):
    """Deja solo prosa continua: fuera math, flotantes, listas y entornos formales."""
    text = RE_COMMENT.sub("", text)
    text = RE_DISPLAY.sub(" ", text)
    for _ in range(3):  # entornos anidados
        text = RE_ENV_SKIP.sub(" ", text)
    text = RE_INLINE_MATH.sub(" NUM ", text)
    text = RE_CMD_ARG.sub(" ", text)
    text = RE_CMD.sub(" ", text)
    text = RE_BRACES.sub(" ", text)
    text = text.replace("~", " ").replace(BS + BS, " ")
    return text


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def sentences(par):
    """Corte por . ! ? seguidos de espacio y mayuscula, evitando abreviaturas obvias."""
    par = re.sub(r"\s+", " ", par)
    par = re.sub(r"\b(Fig|Tab|Ec|Sec|cf|vs|aprox|etc|p\.\s?ej)\.", r"\1<DOT>", par)
    raw = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])", par)
    out = []
    for s in raw:
        s = s.replace("<DOT>", ".").strip()
        if len(s.split()) >= 2:
            out.append(s)
    return out


def analyse(path):
    raw = io.open(path, encoding="utf8", errors="ignore").read()
    text = strip_latex(raw)
    pars = paragraphs(text)
    # Un parrafo del que solo queda un resto corto tras retirar ecuaciones,
    # tablas y flotantes no es un parrafo de prosa: es un fragmento. Contarlo
    # como parrafo de 1 oracion produce falsos positivos contra el minimo VIU.
    pars = [p for p in pars if len(p.split()) >= PROSE_PAR_MIN_WORDS]
    per_par = [sentences(p) for p in pars]
    per_par = [s for s in per_par if s]
    sents = [s for group in per_par for s in group]
    if len(sents) < MIN_SENTENCES:
        return dict(path=path, skipped=True, n_sentences=len(sents))

    lens = [len(s.split()) for s in sents]
    sd = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    counts = [len(g) for g in per_par]

    mode_frac = 0.0
    if counts:
        top = max(set(counts), key=counts.count)
        mode_frac = counts.count(top) / len(counts)

    low = [s for s, n in zip(sents, lens) if n < MIN_SHORT]
    high = [s for s, n in zip(sents, lens) if n > MIN_LONG]

    conn_always, conn_limit = [], []
    for s in sents:
        head = " ".join(s.split()[:4]).lower().strip(",;:")
        for c in SUPRIMIR_SIEMPRE:
            if head.startswith(c) or s.lower().lstrip().startswith(c):
                conn_always.append((c, s[:70]))
                break
        else:
            for c in LIMITAR:
                if s.lower().lstrip().startswith(c):
                    conn_limit.append((c, s[:70]))
                    break

    conn_rate = 100.0 * (len(conn_always) + len(conn_limit)) / len(sents)

    short_pars = [i for i, n in enumerate(counts, 1) if n < PARA_MIN]
    long_pars = [i for i, n in enumerate(counts, 1) if n > PARA_MAX]

    findings = []
    if sd < MIN_SD:
        findings.append(("R1", "varianza baja: sd=%.1f palabras (min %.0f)" % (sd, MIN_SD)))
    if not low:
        findings.append(("R1", "ninguna frase por debajo de %d palabras" % MIN_SHORT))
    if not high:
        findings.append(("R1", "ninguna frase por encima de %d palabras" % MIN_LONG))
    if short_pars:
        findings.append(("R2", "parrafos con menos de %d oraciones (VIU): %s"
                         % (PARA_MIN, short_pars[:8])))
    if long_pars:
        findings.append(("R2", "parrafos de mas de %d oraciones: %s" % (PARA_MAX, long_pars[:8])))
    if mode_frac > PARA_MODE_MAX:
        findings.append(("R2", "uniformidad de parrafo: %.0f%% tienen el mismo numero de frases"
                         % (100 * mode_frac)))
    if conn_rate > CONN_PER_100:
        findings.append(("R4", "densidad de conectores %.1f por 100 frases (max %.0f)"
                         % (conn_rate, CONN_PER_100)))
    for c, s in conn_always:
        findings.append(("R4", "suprimir siempre: '%s' -> %s" % (c, s)))

    return dict(
        path=path, skipped=False,
        n_sentences=len(sents), n_paragraphs=len(counts),
        sd=round(sd, 2), mean=round(statistics.mean(lens), 1),
        min_len=min(lens), max_len=max(lens),
        n_short=len(low), n_long=len(high),
        para_counts=counts, para_mode_fraction=round(mode_frac, 2),
        conn_rate=round(conn_rate, 1),
        conn_always=conn_always, conn_limit=conn_limit,
        findings=findings,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--census", help="census.json con el cierre activo de \\input")
    ap.add_argument("--root", default=".", help="raiz a la que son relativos los del census")
    ap.add_argument("--json", help="volcar resultados a este fichero")
    args = ap.parse_args()

    targets = list(args.files)
    if args.census:
        c = json.load(io.open(args.census, encoding="utf8"))
        targets += [os.path.join(args.root, f) for f in c["files"]]
    targets = [t for t in targets if os.path.exists(t)]
    if not targets:
        print("sin ficheros que analizar")
        return 2

    results, total_findings, analysed = [], 0, 0
    for p in targets:
        r = analyse(p)
        results.append(r)
        if r["skipped"]:
            continue
        analysed += 1
        total_findings += len(r["findings"])
        if not r["findings"]:
            continue
        print("=== %s ===" % os.path.relpath(p))
        print("  %d frases en %d parrafos | media %.1f  sd %.1f  rango %d-%d | conectores %.1f/100"
              % (r["n_sentences"], r["n_paragraphs"], r["mean"], r["sd"],
                 r["min_len"], r["max_len"], r["conn_rate"]))
        for rule, msg in r["findings"]:
            print("    [%s] %s" % (rule, msg))
        print()

    print("-" * 70)
    print("ficheros analizados: %d (de %d; el resto tiene menos de %d frases)"
          % (analysed, len(targets), MIN_SENTENCES))
    print("hallazgos: %d" % total_findings)

    if analysed:
        allsd = [r["sd"] for r in results if not r["skipped"]]
        allcr = [r["conn_rate"] for r in results if not r["skipped"]]
        print("sd mediana: %.1f palabras | conectores medianos: %.1f por 100 frases"
              % (statistics.median(allsd), statistics.median(allcr)))

    if args.json:
        io.open(args.json, "w", encoding="utf8").write(
            json.dumps(results, ensure_ascii=False, indent=2))
        print("JSON -> %s" % args.json)

    return 1 if total_findings else 0


if __name__ == "__main__":
    sys.exit(main())
