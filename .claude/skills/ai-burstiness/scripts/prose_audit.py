"""Auditoria de prosa del TFM: localiza QUE parrafos hay que reescribir y POR QUE.

Combina dos niveles:

  1. Reglas deterministas y explicables (no dependen de ningun modelo):
     lexico de IA, calcos del ingles, cadenas de gerundios, puntuacion calcada,
     regla de tres, paralelismo negativo, conectores y ritmo de frase.
  2. `lmscan` si esta instalado: puntuacion estadistica por parrafo, en espanol.

Lo que este guion NO hace, deliberadamente:

  - No reescribe. Senala la ocurrencia; la reescritura es del autor.
  - No persigue bajar una puntuacion. Un numero de detector no es una verdad de
    referencia: Turnitin publica que su indicador produce falsos positivos y no
    debe fundar por si solo una accion adversa, y optimizar contra un detector
    distinto del que evalua es ademas un sinsentido metodologico. La senal util
    aqui es la LOCALIZACION, no el porcentaje.
  - No toca ecuaciones, enunciados formales, cifras ni atribuciones de fuente:
    se excluyen del analisis.

Uso:
    python prose_audit.py --census final-hardening/census.json --root pre-thesis
    python prose_audit.py fichero.tex --top 15
    python prose_audit.py --census ... --no-lmscan --json informe.json
"""
import argparse
import io
import json
import os
import re
import statistics
import sys

BS = chr(92)

# --------------------------------------------------------------- umbrales
MIN_SD = 8.0
MIN_SHORT = 10
MIN_LONG = 35
PARA_MIN = 3          # minimo VIU de oraciones por parrafo
PARA_MAX = 10
PROSE_PAR_MIN_WORDS = 30
DASH_MAX_PER_100 = 2.0    # rayas por 100 frases
COLON_MAX_PER_100 = 12.0

# --------------------------------------------------------------- lexico
VOCAB_IA = {
    "verbo": ["ahondar", "aprovechar", "desbloquear", "fomentar", "revolucionar",
              "subrayar", "facilitar"],
    "adjetivo": ["crucial", "pivotal", "innovador", "transformador", "vibrante",
                 "intrincado", "contundente"],
    "sustantivo": ["panorama", "paisaje", "tapiz", "paradigma", "sinergia",
                   "ecosistema", "testimonio", "catalizador"],
}
# Terminos que en esta tesis SOLO valen con definicion formal cerca.
VOCAB_CONDICIONADO = {
    "robusto": "solo con definicion formal de robustez",
    "significativo": "colisiona con el sentido estadistico; usar el termino exacto",
    "escalable": "solo con curvas por tamano",
    "optimo": "solo con el problema de optimizacion declarado",
}
CALCOS = {
    "cuello de botella": "limitacion, restriccion, punto critico",
    "lider del sector": "empresa puntera, referente del sector",
    "en el panorama de": "en el ambito de, en el campo de",
    "punto de inflexion": "momento clave, cambio decisivo",
    "rol crucial": "papel fundamental, funcion clave",
    "vision de futuro": "perspectiva, proyeccion",
    "hoja de ruta": "plan, calendario",
    "estado del arte de vanguardia": "redundante",
}
APERTURAS = [
    "cabe destacar", "cabe senalar", "cabe senialar", "cabe mencionar",
    "es importante destacar", "es importante senalar", "conviene recordar",
    "notese que", "observese que", "como se puede observar", "claramente",
    "evidentemente", "notablemente", "en el mundo actual", "en la era digital",
    "en resumen", "en conclusion", "en definitiva",
]
CONECTORES = ["ademas", "asimismo", "por otra parte", "en este sentido",
              "por tanto", "por consiguiente", "en consecuencia", "sin embargo",
              "no obstante", "de este modo"]

RE_GERUNDIO = re.compile(r"\b\w+(?:ando|endo|iendo)\b", re.I)
RE_DASH = re.compile("[\u2014\u2013]")
RE_TRICOLON = re.compile(r"\b(\w+),\s+(\w+)\s+y\s+(\w+)\b")
RE_NEG_PAR = re.compile(
    r"no\s+(?:es|se\s+trata\s+de|solo)\s+[^.,;]{3,60}[,;]?\s*(?:sino|es)\b", re.I)
RE_ATRIB_VAGA = re.compile(
    r"\b(?:estudios\s+demuestran|seg[uú]n\s+expertos|la\s+industria\s+sostiene|"
    r"se\s+sabe\s+que)\b", re.I)

# --------------------------------------------------------------- LaTeX
RE_COMMENT = re.compile(r"(?<!" + BS + BS + r")%.*$", re.M)
RE_DISPLAY = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?\\end\{\1\*?\}", re.S)
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


def strip_latex(text):
    text = RE_COMMENT.sub("", text)
    text = RE_DISPLAY.sub(" ", text)
    for _ in range(3):
        text = RE_ENV_SKIP.sub(" ", text)
    text = RE_INLINE_MATH.sub(" NUM ", text)
    text = RE_CMD_ARG.sub(" ", text)
    text = RE_CMD.sub(" ", text)
    return text.replace("{", " ").replace("}", " ").replace("~", " ")


def paragraphs(text):
    out = []
    for p in re.split(r"\n\s*\n", text):
        p = re.sub(r"\s+", " ", p).strip()
        if len(p.split()) >= PROSE_PAR_MIN_WORDS:
            out.append(p)
    return out


def sentences(par):
    par = re.sub(r"\b(Fig|Tab|Ec|Sec|cf|vs|aprox|etc)\.", r"\1<D>", par)
    out = []
    for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])", par):
        s = s.replace("<D>", ".").strip()
        if len(s.split()) >= 2:
            out.append(s)
    return out


def norm(s):
    tbl = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return s.translate(tbl).lower()


def check_paragraph(par, idx):
    """Devuelve la lista de hallazgos de un parrafo."""
    f = []
    low = norm(par)
    sents = sentences(par)
    lens = [len(s.split()) for s in sents]

    for kind, words in VOCAB_IA.items():
        for w in words:
            n = len(re.findall(r"\b" + w + r"\w*\b", low))
            if n:
                f.append(("lexico", "%s de IA: «%s» x%d" % (kind, w, n)))
    for w, why in VOCAB_CONDICIONADO.items():
        n = len(re.findall(r"\b" + w + r"\w*\b", low))
        if n:
            f.append(("condicionado", "«%s» x%d — %s" % (w, n, why)))
    for c, alt in CALCOS.items():
        if norm(c) in low:
            f.append(("calco", "«%s» → %s" % (c, alt)))
    for a in APERTURAS:
        for s in sents:
            if norm(s).lstrip().startswith(a):
                f.append(("apertura", "«%s…» al abrir frase" % a))
                break
    if RE_ATRIB_VAGA.search(par):
        f.append(("rigor", "atribucion vaga sin cita"))
    m = RE_NEG_PAR.search(par)
    if m:
        f.append(("estructura", "paralelismo negativo: «%s…»" % m.group(0)[:48]))
    for s in sents:
        g = RE_GERUNDIO.findall(s)
        if len(g) > 2:
            f.append(("gerundios", "%d gerundios en una frase: %s" % (len(g), ", ".join(g[:4]))))
    tri = RE_TRICOLON.findall(par)
    if len(tri) >= 2:
        f.append(("regla de tres", "%d enumeraciones ternarias" % len(tri)))
    nd = len(RE_DASH.findall(par))
    if nd >= 2:
        f.append(("puntuacion", "%d rayas (—) en un parrafo" % nd))

    if len(sents) < PARA_MIN:
        f.append(("VIU", "%d oraciones: el minimo VIU es %d" % (len(sents), PARA_MIN)))
    elif len(sents) > PARA_MAX:
        f.append(("ritmo", "%d oraciones: parrafo muy largo" % len(sents)))
    if len(lens) >= 3:
        sd = statistics.pstdev(lens)
        if sd < 5.0:
            f.append(("ritmo", "frases de longitud casi igual (sd=%.1f)" % sd))
    return f


def analyse_file(path, use_lmscan):
    raw = io.open(path, encoding="utf8", errors="ignore").read()
    pars = paragraphs(strip_latex(raw))
    if not pars:
        return None
    all_sents = [s for p in pars for s in sentences(p)]
    lens = [len(s.split()) for s in all_sents]
    if len(lens) < 10:
        return None

    sd = statistics.pstdev(lens)
    findings_file = []
    if sd < MIN_SD:
        findings_file.append(("ritmo", "sd de longitud de frase %.1f (min %.0f)" % (sd, MIN_SD)))
    if not any(n < MIN_SHORT for n in lens):
        findings_file.append(("ritmo", "ninguna frase por debajo de %d palabras" % MIN_SHORT))
    if not any(n > MIN_LONG for n in lens):
        findings_file.append(("ritmo", "ninguna frase por encima de %d palabras" % MIN_LONG))

    ncon = sum(1 for s in all_sents
               if any(norm(s).lstrip().startswith(c) for c in CONECTORES))
    rate = 100.0 * ncon / len(all_sents)
    if rate > 6.0:
        findings_file.append(("conectores", "%.1f conectores de apertura por 100 frases" % rate))

    ndash = len(RE_DASH.findall(" ".join(pars)))
    if 100.0 * ndash / len(all_sents) > DASH_MAX_PER_100:
        findings_file.append(("puntuacion", "%d rayas (—) en %d frases" % (ndash, len(all_sents))))

    per_par = []
    for i, p in enumerate(pars, 1):
        f = check_paragraph(p, i)
        score = None
        if use_lmscan:
            try:
                import lmscan
                r = lmscan.scan(p)
                score = getattr(r, "ai_probability", None)
            except Exception:
                score = None
        per_par.append(dict(index=i, words=len(p.split()), findings=f,
                            lmscan=score, head=p[:90]))

    return dict(path=path, n_paragraphs=len(pars), n_sentences=len(all_sents),
                sd=round(sd, 2), mean=round(statistics.mean(lens), 1),
                file_findings=findings_file, paragraphs=per_par)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--census")
    ap.add_argument("--root", default=".")
    ap.add_argument("--top", type=int, default=12, help="parrafos peores a listar")
    ap.add_argument("--no-lmscan", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()

    use_lmscan = not args.no_lmscan
    if use_lmscan:
        try:
            import lmscan  # noqa: F401
            print("lmscan disponible: puntuacion estadistica por parrafo activada.")
        except ImportError:
            use_lmscan = False
            print("lmscan no instalado: solo reglas deterministas (pip install lmscan).")
    print()

    targets = list(args.files)
    if args.census:
        c = json.load(io.open(args.census, encoding="utf8"))
        targets += [os.path.join(args.root, f) for f in c["files"]]
    targets = [t for t in targets if os.path.exists(t)]

    results, worst = [], []
    for p in targets:
        r = analyse_file(p, use_lmscan)
        if r is None:
            continue
        results.append(r)
        for par in r["paragraphs"]:
            n = len(par["findings"])
            if n or (par["lmscan"] or 0) > 0.6:
                worst.append((n, par["lmscan"] or 0.0, r["path"], par))

    if not results:
        print("sin prosa suficiente que analizar")
        return 2

    print("%-44s %5s %5s %6s %s" % ("fichero", "parr", "frases", "sd", "hallazgos de fichero"))
    print("-" * 104)
    tot = 0
    for r in sorted(results, key=lambda x: -len(x["file_findings"])):
        msgs = "; ".join(m for _k, m in r["file_findings"]) or "-"
        tot += len(r["file_findings"])
        print("%-44s %5d %5d %6.1f %s"
              % (os.path.basename(r["path"])[:44], r["n_paragraphs"],
                 r["n_sentences"], r["sd"], msgs[:52]))

    worst.sort(key=lambda x: (-x[0], -x[1]))
    print("\n\nPARRAFOS A REESCRIBIR PRIMERO (%d con hallazgos)" % len(worst))
    print("=" * 104)
    for n, sc, path, par in worst[:args.top]:
        tag = "  lmscan %.0f%%" % (100 * sc) if sc else ""
        print("\n%s  parrafo %d (%d palabras)%s"
              % (os.path.basename(path), par["index"], par["words"], tag))
        print("  «%s…»" % par["head"])
        for k, m in par["findings"]:
            print("    [%-13s] %s" % (k, m))

    npar = sum(len(r["paragraphs"]) for r in results)
    print("\n" + "-" * 104)
    print("ficheros %d | parrafos de prosa %d | con hallazgos %d | hallazgos de fichero %d"
          % (len(results), npar, len(worst), tot))
    print("sd mediana %.1f palabras (objetivo >= %.0f)"
          % (statistics.median([r["sd"] for r in results]), MIN_SD))
    print("\nEste informe localiza donde reescribir. No reescribe, y la puntuacion")
    print("de lmscan es orientativa: no es un objetivo que haya que minimizar.")

    if args.json:
        io.open(args.json, "w", encoding="utf8").write(
            json.dumps(results, ensure_ascii=False, indent=2))
        print("JSON -> %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
