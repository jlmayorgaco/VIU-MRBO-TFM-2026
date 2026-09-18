"""Censo de resultados formales y ecuaciones numeradas del documento ACTIVO.

Resuelve la lista real de \input de main-v2.tex (recursivamente) y reporta:
  - todo entorno teorema/proposicion/lema/corolario/definicion con su label
  - toda ecuacion con \label{eq:...} y si se cita en el texto por su numero
  - simbolos sobrecargados declarados en varios sitios

Uso: python scripts/census_formal_results.py [--json salida.json]
"""
import io
import json
import os
import re
import sys

BS = chr(92)

RE_INPUT = re.compile(BS + BS + r"(?:input|include)\{([^}]+)\}")
RE_ENV = re.compile(
    BS + BS + r"begin\{(teorema|theorem|proposicion|proposition|lema|lemma|"
    r"corolario|corollary|definicion|definition)\}(\[[^\]]*\])?"
)
RE_LABEL = re.compile(BS + BS + r"label\{([^}]+)\}")
RE_EQLABEL = re.compile(BS + BS + r"label\{(eq:[^}]+)\}")
RE_REF = re.compile(BS + BS + r"(?:eq)?ref\*?\{([^}]+)\}")


def resolve(path, seen):
    """Devuelve la lista ordenada de ficheros .tex realmente incluidos."""
    if path in seen:
        return []
    seen.add(path)
    if not os.path.exists(path):
        return []
    out = [path]
    txt = io.open(path, encoding="utf8", errors="ignore").read()
    base = os.path.dirname(path)
    for rel in RE_INPUT.findall(txt):
        cand = rel if rel.endswith(".tex") else rel + ".tex"
        for probe in (cand, os.path.join(base, cand)):
            probe = probe.replace("\\", "/")
            if os.path.exists(probe):
                out.extend(resolve(probe, seen))
                break
    return out


def main():
    root = "main-v2.tex"
    files = resolve(root, set())
    print("Ficheros .tex activos: %d" % len(files))

    results = []
    eq_labels = {}
    all_refs = set()

    for p in files:
        txt = io.open(p, encoding="utf8", errors="ignore").read()
        for m in RE_ENV.finditer(txt):
            tail = txt[m.end():m.end() + 500]
            lm = RE_LABEL.search(tail)
            results.append(
                {
                    "file": p,
                    "kind": m.group(1),
                    "title": (m.group(2) or "[]")[1:-1],
                    "label": lm.group(1) if lm else "(SIN LABEL)",
                }
            )
        for m in RE_EQLABEL.finditer(txt):
            eq_labels.setdefault(m.group(1), p)
        for m in RE_REF.finditer(txt):
            all_refs.add(m.group(1))

    print("\n=== RESULTADOS FORMALES: %d ===" % len(results))
    for r in results:
        print(
            "  %-34s %-12s %-44s %s"
            % (
                os.path.basename(r["file"])[:34],
                r["kind"],
                r["title"][:44],
                r["label"],
            )
        )

    uncited = sorted(k for k in eq_labels if k not in all_refs)
    print("\n=== ECUACIONES ETIQUETADAS: %d | SIN CITAR: %d ===" % (len(eq_labels), len(uncited)))
    for k in uncited:
        print("  %-42s %s" % (k, eq_labels[k]))

    dup = {}
    for p in files:
        txt = io.open(p, encoding="utf8", errors="ignore").read()
        for m in RE_LABEL.finditer(txt):
            dup.setdefault(m.group(1), []).append(p)
    dups = {k: v for k, v in dup.items() if len(v) > 1}
    print("\n=== LABELS DUPLICADAS: %d ===" % len(dups))
    for k, v in sorted(dups.items()):
        print("  %-42s %s" % (k, " | ".join(os.path.basename(x) for x in v)))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf8").write(
            json.dumps(
                {
                    "files": files,
                    "results": results,
                    "equations": eq_labels,
                    "uncited_equations": uncited,
                    "duplicate_labels": dups,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print("\nJSON -> %s" % out)


if __name__ == "__main__":
    main()
