"""Auditoria de referencias cruzadas del cuerpo activo.

VIU exige que toda figura, tabla y ecuacion este numerada, titulada, con fuente
**y citada en el texto por su numero**. Un flotante que nadie cita es un
incumplimiento, y ademas suele indicar que el argumento no lo necesita.

Este guion recorre el cierre real de \\input de main-v2.tex y reporta:
  - etiquetas definidas y nunca referenciadas, por tipo
  - flotantes (figura/tabla) nunca citados  -> incumplimiento VIU
  - ecuaciones etiquetadas y nunca citadas  -> incumplimiento VIU
  - etiquetas referenciadas que no existen  (biber/LaTeX ya las detecta, se
    comprueba por si algo se resuelve por otro fichero)

Uso: python final-hardening/audit_crossrefs.py [--md salida.md]
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
BS = chr(92)

RE_COMMENT = re.compile(r"(?<!" + BS + BS + r")%.*$", re.M)
RE_LBL = re.compile(BS + BS + r"label\{([^}]+)\}")
RE_REF = re.compile(BS + BS + r"(?:eq)?ref\*?\{([^}]+)\}")
RE_CAPTION = re.compile(BS + BS + r"caption(?:\[[^\]]*\])?\{([^}]{0,80})")

# tipos cuya falta de cita incumple la norma VIU
OBLIGATORIOS = {"fig": "figura", "tab": "tabla", "eq": "ecuacion"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    args = ap.parse_args()

    census = json.load(io.open(CENSUS, encoding="utf8"))
    files = [f for f in census["files"] if os.path.exists(os.path.join(THESIS, f))]

    defs, refs, captions = {}, set(), {}
    for rel in files:
        p = os.path.join(THESIS, rel)
        txt = RE_COMMENT.sub("", io.open(p, encoding="utf8", errors="ignore").read())
        for m in RE_LBL.finditer(txt):
            defs.setdefault(m.group(1), rel)
            # caption mas cercano hacia atras
            head = txt[max(0, m.start() - 600):m.start()]
            caps = RE_CAPTION.findall(head)
            if caps:
                captions[m.group(1)] = caps[-1].strip()
        refs.update(RE_REF.findall(txt))

    orphan = sorted(k for k in defs if k not in refs)
    dangling = sorted(r for r in refs if r not in defs)

    by_kind = collections.defaultdict(list)
    for k in orphan:
        by_kind[k.split(":")[0] if ":" in k else "otro"].append(k)

    out = []
    w = out.append
    w("# Referencias cruzadas del cuerpo activo\n")
    w("Criterio VIU: toda figura, tabla y ecuacion numerada debe citarse en el")
    w("texto por su numero.\n")
    w("| metrica | n |")
    w("|---|---:|")
    w("| ficheros activos | %d |" % len(files))
    w("| etiquetas definidas | %d |" % len(defs))
    w("| etiquetas referenciadas | %d |" % len(refs & set(defs)))
    w("| etiquetas huerfanas | %d |" % len(orphan))
    w("| referencias sin destino | %d |" % len(dangling))
    w("")

    total_viu = sum(len(by_kind.get(k, [])) for k in OBLIGATORIOS)
    w("## Incumplimientos VIU: flotantes y ecuaciones sin citar\n")
    if total_viu == 0:
        w("Ninguno.\n")
    else:
        w("**%d elementos numerados no se citan en ninguna parte del texto.**\n" % total_viu)
        w("| tipo | etiqueta | fichero | titulo |")
        w("|---|---|---|---|")
        for kind, nombre in OBLIGATORIOS.items():
            for k in by_kind.get(kind, []):
                w("| %s | `%s` | `%s` | %s |"
                  % (nombre, k, defs[k], captions.get(k, "")[:56].replace("|", " ")))
        w("")
        w("Cada uno admite una de tres salidas: citarlo en el texto, fundirlo con")
        w("otro elemento, o retirarlo. Un flotante que el argumento no necesita")
        w("ocupa presupuesto de paginas sin sostener nada.\n")

    w("## Resto de etiquetas huerfanas, por tipo\n")
    w("No incumplen la norma: un teorema o una seccion pueden leerse en su sitio")
    w("sin cita cruzada. Se listan porque una etiqueta que nadie usa suele")
    w("sobrar.\n")
    w("| tipo | n | ejemplos |")
    w("|---|---:|---|")
    for kind in sorted(by_kind):
        if kind in OBLIGATORIOS:
            continue
        ks = by_kind[kind]
        w("| `%s` | %d | %s |" % (kind, len(ks), ", ".join("`%s`" % x for x in ks[:3])))
    w("")

    if dangling:
        w("## Referencias sin destino\n")
        for r in dangling:
            w("- `%s`" % r)
        w("")

    text = "\n".join(out)
    if args.md:
        io.open(args.md, "w", encoding="utf8").write(text)
        print("-> %s" % args.md)
    print("definidas %d | huerfanas %d | incumplimientos VIU %d | sin destino %d"
          % (len(defs), len(orphan), total_viu, len(dangling)))
    return 1 if total_viu else 0


if __name__ == "__main__":
    sys.exit(main())
