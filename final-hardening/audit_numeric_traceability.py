"""Auditoria de trazabilidad numerica: toda cifra impresa debe venir de una macro
generada, no estar escrita a mano en el .tex.

La regla del proyecto (latex-build-tfm §4) es explicita: «La prosa no contiene
cifras a mano: si un numero del texto no coincide con el PDF, el fallo esta en
la macro o en la campana, no en el texto.» Este guion comprueba si esa regla se
cumple realmente.

Clasifica cada literal numerico del cuerpo activo en:
  MACRO       viene de \\shared/generated-macros (no aparece como literal)
  ESTRUCTURAL parte de una ecuacion, indice, unidad, año, numero de seccion
  LITERAL     cifra escrita a mano en la prosa o en una tabla -> a revisar

Uso: python final-hardening/audit_numeric_traceability.py [--md salida.md]
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
MACRODIR = os.path.join(THESIS, "shared", "generated-macros")

BS = chr(92)

RE_COMMENT = re.compile(r"(?<!" + BS + BS + r")%.*$", re.M)
# entornos cuyos numeros son estructurales, no afirmaciones de resultado
RE_MATH_ENV = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath|tikzpicture|"
    r"algorithmic|algorithm)\*?\}.*?\\end\{\1\*?\}", re.S)
RE_INLINE = re.compile(r"\$[^$]*\$")
RE_NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")

# numeros que nunca son un resultado experimental
ESTRUCTURAL = re.compile(
    r"^(19|20)\d\d$"          # años
    r"|^\d{1,2}$"             # indices, cardinalidades pequeñas, numeros de seccion
)


def macro_values():
    """Valores que SI provienen de campanas, para poder reconocerlos."""
    vals = {}
    if not os.path.isdir(MACRODIR):
        return vals
    for f in os.listdir(MACRODIR):
        if not f.endswith(".tex"):
            continue
        txt = io.open(os.path.join(MACRODIR, f), encoding="utf8", errors="ignore").read()
        for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", txt):
            vals.setdefault(m.group(2).strip(), []).append((f, m.group(1)))
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    args = ap.parse_args()

    mv = macro_values()
    census = json.load(io.open(CENSUS, encoding="utf8"))
    files = [os.path.join(THESIS, f) for f in census["files"]]

    rows = []
    macro_uses = collections.Counter()
    for p in files:
        if not os.path.exists(p):
            continue
        raw = io.open(p, encoding="utf8", errors="ignore").read()
        macro_uses[os.path.basename(p)] = len(re.findall(r"\\[A-Z][A-Za-z]{5,}\{\}", raw))
        txt = RE_COMMENT.sub("", raw)
        txt = RE_MATH_ENV.sub(" ", txt)
        txt = RE_INLINE.sub(" ", txt)
        for ln, line in enumerate(txt.split("\n"), 1):
            s = line.strip()
            if not s or s.startswith("\\label") or s.startswith("\\input"):
                continue
            for m in RE_NUM.finditer(s):
                v = m.group(1)
                if ESTRUCTURAL.match(v):
                    continue
                kind = "MACRO-EQUIV" if v in mv else "LITERAL"
                rows.append(dict(file=os.path.relpath(p, THESIS).replace("\\", "/"),
                                 line=ln, value=v, kind=kind,
                                 ctx=s[max(0, m.start() - 40):m.start() + 30].strip()))

    lit = [r for r in rows if r["kind"] == "LITERAL"]
    eq = [r for r in rows if r["kind"] == "MACRO-EQUIV"]

    out = []
    w = out.append
    w("# Trazabilidad numerica del cuerpo activo\n")
    w("Regla del proyecto: la prosa no contiene cifras a mano. Toda cifra de")
    w("resultado debe venir de `shared/generated-macros/`.\n")
    w("Excluidos del recuento: comentarios, ecuaciones, `tikzpicture`, algoritmos,")
    w("matematica en linea, anos y enteros de una o dos cifras (indices y")
    w("cardinalidades).\n")
    w("| categoria | n |")
    w("|---|---:|")
    w("| literales decimales en prosa o tablas | %d |" % len(lit))
    w("| literales que coinciden con el valor de alguna macro | %d |" % len(eq))
    w("| ficheros activos revisados | %d |" % len(files))
    w("")
    w("Un literal que **coincide** con el valor de una macro es sospechoso: la")
    w("cifra correcta esta disponible como macro y aun asi se escribio a mano, de")
    w("modo que una regeneracion de campana no la actualizaria.\n")

    if eq:
        w("## Literales que duplican el valor de una macro\n")
        w("| fichero | linea | valor | macro disponible | contexto |")
        w("|---|---:|---:|---|---|")
        for r in sorted(eq, key=lambda x: (x["file"], x["line"]))[:60]:
            src = ", ".join("`%s`" % n for _f, n in mv[r["value"]][:2])
            w("| `%s` | %d | %s | %s | %s |"
              % (r["file"], r["line"], r["value"], src, r["ctx"].replace("|", " ")[:60]))
        w("")

    byfile = collections.Counter(r["file"] for r in lit)
    w("## Literales decimales por fichero\n")
    w("| fichero | literales | usos de macro |")
    w("|---|---:|---:|")
    for f, n in byfile.most_common(25):
        w("| `%s` | %d | %d |" % (f, n, macro_uses.get(os.path.basename(f), 0)))
    w("")
    w("## Muestra de literales (los 40 primeros)\n")
    w("| fichero | linea | valor | contexto |")
    w("|---|---:|---:|---|")
    for r in sorted(lit, key=lambda x: (x["file"], x["line"]))[:40]:
        w("| `%s` | %d | %s | %s |"
          % (r["file"], r["line"], r["value"], r["ctx"].replace("|", " ")[:70]))

    text = "\n".join(out)
    if args.md:
        io.open(args.md, "w", encoding="utf8").write(text)
        print("-> %s" % args.md)
    print("literales decimales: %d | coincidentes con macro: %d | ficheros: %d"
          % (len(lit), len(eq), len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
