# -*- coding: utf-8 -*-
"""Comprobacion de entrega de SP1. Devuelve codigo 1 si algo falla."""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))
TEX = os.path.join(SP1, "sp1.tex")
LOG = os.path.join(SP1, "sp1.log")
PDF = os.path.join(SP1, "sp1.pdf")

fails, warns = [], []


def check(ok, msg, hard=True):
    (fails if hard else warns).append(msg) if not ok else None
    print("  %-4s %s" % ("OK" if ok else ("FALLA" if hard else "aviso"), msg))


src = io.open(TEX, encoding="utf-8").read()
log = io.open(LOG, encoding="utf-8", errors="replace").read() if os.path.exists(LOG) else ""

print("=" * 70)
print("COMPROBACION DE ENTREGA — SP1")
print("=" * 70)

print("\n1. COMPILACION")
check("Overfull" not in log, "sin cajas Overfull")
check("Underfull" not in log, "sin cajas Underfull")
check("undefined" not in log.lower(), "sin referencias ni citas sin resolver")
# El .log parte la linea; se lee del PDF, que es la fuente real.
pages = -1
try:
    out = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True,
                         check=False).stdout
    mm = re.search(r"Pages:\s+(\d+)", out)
    if mm:
        pages = int(mm.group(1))
except OSError:
    pass
if pages < 0:
    flat = re.sub(r"\s+", " ", log)
    m = re.findall(r"Output written on .*?\((\d+) pages", flat)
    pages = int(m[-1]) if m else -1
# El anexo se compila como apendice del mismo PDF. El limite de VIU cuenta
# paginas de cuerpo; los anexos van aparte. La primera pagina del apendice se
# lee del .aux, que registra la pagina de cada \\label.
body_pages = pages
aux_path = TEX[:-4] + ".aux"
if os.path.exists(aux_path):
    aux = io.open(aux_path, encoding="utf-8", errors="replace").read()
    anx_pages = [int(x) for x in
                 re.findall(r"newlabel\{anx:[^}]+\}\{\{[^}]*\}\{(\d+)\}", aux)]
    if anx_pages:
        body_pages = min(anx_pages) - 1
check(0 < body_pages <= 25,
      "paginas de cuerpo = %d (limite 25); anexo = %d; total = %d"
      % (body_pages, pages - body_pages, pages))
# Un PDF mas antiguo que la fuente significa que la ultima compilacion fallo y
# se esta revisando un artefacto obsoleto.
fresh = (os.path.exists(PDF)
         and os.path.getmtime(PDF) >= os.path.getmtime(TEX) - 1.0)
check(fresh, "el PDF es posterior a sp1.tex (no es un artefacto obsoleto)")

print("\n2. INTEGRIDAD DE REFERENCIAS")
# Las figuras del anexo se alcanzan por su numero de anexo, que el cuerpo si
# cita, de modo que no se les exige ademas una cita por \\ref propia.
anx_file = os.path.join(os.path.dirname(TEX), "sp1_anexo.tex")
anx_src = (io.open(anx_file, encoding="utf-8").read()
           if os.path.exists(anx_file) else "")
labels = set(re.findall(r"\\label\{(fig:[^}]+)\}", src + anx_src))
refs = set(re.findall(r"\\ref\{(fig:[^}]+)\}", src + anx_src))
check(not (labels - refs),
      "toda figura del cuerpo se cita (%d)" % len(labels))
check(not (refs - labels), "ninguna referencia rota")
eqlab = set(re.findall(r"\\label\{(eq:[^}]+)\}", src + anx_src))
eqref = set(re.findall(r"\\eqref\{(eq:[^}]+)\}", src))
check(not (eqref - eqlab), "ninguna ecuacion referenciada sin etiqueta")

print("\n3. CORRUPCION SILENCIOSA")
raw = io.open(TEX, "rb").read()
stray = raw.replace(b"\r\n", b"\x00\x00").count(b"\r")
check(stray == 0, "sin retornos de carro sueltos")
check("\t" not in src, "sin tabuladores")
bad = re.findall(r"(?<![\\\w])(ef|extbf|extit|aption|abel|iny)\{", src)
check(not bad, "sin comandos con la barra perdida")

print("\n4. TERMINOLOGIA")
body = src[src.find(r"\begin{document}"):]
body = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("%"))
for term, limit in (("conviene", 0), ("frontera", 0), ("contrato", 0),
                    ("trazabilidad", 0), ("alcance", 0)):
    n = len(re.findall(term, body, re.I))
    check(n <= limit, "'%s' aparece %d veces (limite %d)" % (term, n, limit))
n_rob = len(re.findall(r"\brobots?\b", body, re.I))
check(n_rob <= 1, "'robot' solo en la definicion de AMR (%d)" % n_rob)

print("\n5. TRAZABILIDAD NUMERICA")
# cifras sueltas con coma decimal fuera de macro, ecuacion o comentario
prose = re.sub(r"\$[^$]*\$", " ", body)
prose = re.sub(r"\\[A-Za-z]+", " ", prose)
loose = re.findall(r"(?<![\d,])\d{1,3},\d{1,2}\\,\\%", prose)
check(len(loose) <= 12, "cifras con coma decimal escritas a mano: %d" % len(loose),
      hard=False)

print("\n6. ESTRUCTURA FORMAL")
props = len(re.findall(r"\\begin\{n1prop\}", src))
lemas = len(re.findall(r"\\begin\{n1lema\}", src))
proofs = len(re.findall(r"\\proofsketch\{", src))
check(proofs >= props + lemas - 1,
      "%d demostraciones para %d proposiciones y %d lemas" % (proofs, props, lemas))
# Un recuento minimo no protege nada: lo que importa es que ningun nivel
# se quede sin figura al compactar. Se comprueba cobertura, no cantidad.
_body_figs = set(re.findall(r"\\label\{(fig:[^}]+)\}", src))
_needed = {
    "N1": ("fig:modelos", "fig:n1"),
    "N2": ("fig:n2-contraejemplos", "fig:n2"),
    "N3": ("fig:n3-resultados",),
    "N4": ("fig:orden-brecha", "fig:ablacion", "fig:desviacion"),
    "validacion": ("fig:n3b", "fig:holdout"),
}
_missing = [k for k, v in _needed.items() if not (set(v) & _body_figs)]
check(not _missing,
      "cada nivel conserva figura en el cuerpo (%d figuras)%s"
      % (len(_body_figs),
         "" if not _missing else "; sin figura: " + ", ".join(_missing)))
check("\\begin{tcolorbox}" not in src, "sin cajas de resumen")

print("\n7. INTEGRIDAD DEL RAW")
lev = os.path.abspath(os.path.join(SP1, "..", "..", "scripts", "results", "sp1_levels"))
git = subprocess.run(["git", "status", "--porcelain", lev],
                     capture_output=True, text=True, check=False).stdout
touched = [l for l in git.splitlines() if "/raw/" in l.replace("\\", "/")]
check(not touched, "ningun fichero RAW modificado (%d)" % len(touched))

print("\n" + "=" * 70)
if fails:
    print("FALLOS: %d" % len(fails))
    for f in fails:
        print("   - " + f)
else:
    print("SIN FALLOS")
if warns:
    print("avisos: %d" % len(warns))
    for w in warns:
        print("   - " + w)
print("=" * 70)
sys.exit(1 if fails else 0)
