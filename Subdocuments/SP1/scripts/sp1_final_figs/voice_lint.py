"""Auditoria de voz: mide regularidad, no vocabulario.

El metadiscurso lexico es la parte visible y menor. Lo que produce sensacion de
texto generado es la REGULARIDAD: el mismo molde de parrafo repetido, aperturas
de frase monotonas, simetria sintactica y cautela en cadena.

Mide cinco cosas:
  1. molde de parrafo   declarativa -> interpretacion -> descargo
  2. aperturas de frase  cuantas empiezan con el mismo patron
  3. densidad de punto y coma
  4. vocabulario evaluativo
  5. cadenas de descargos sobre un mismo resultado
"""
from __future__ import annotations

import io
import os
import re
import sys
import collections

INTERP = re.compile(
    r"\b(indica|significa|muestra|sugiere|es consistente con|coherente con"
    r"|refleja|implica|por tanto|por ello|de este modo|en este sentido"
    r"|sostien\w+|respald\w+|confirma)\b", re.I)
DISCLAIM = re.compile(
    r"\b(no (mide|implica|significa|constituye|establece|caracteriza|garantiza"
    r"|demuestra|prueba|describe|cabe)|sin establecer|sin que ello"
    r"|no debe leerse|dentro de est\w+ dominio|en el banco (evaluado|estudiado)"
    r"|dentro de est\w+ alcance)\b", re.I)
EVAL = re.compile(
    r"\b(decisiv\w+|clave|central|principal|fundamental|crucial|importante"
    r"|notable|destacad\w+|relevante|fuerte|robust\w+|excelente|clarament\w+"
    r"|precisament\w+|aportaci\w+)\b", re.I)
META = re.compile(
    r"\b(conviene|cabe (destacar|señalar|notar)|es importante|resulta útil"
    r"|debe interpretarse|debe leerse|el capítulo|este capítulo|la figura"
    r"|el diagrama|el panel|la observación|la evidencia)\b", re.I)
HEDGE_FAMILY = re.compile(
    r"\b(frontera|delimit\w+|alcance|contrato|trazabilidad|dominio)\b", re.I)

SKIP_ENV = re.compile(
    r"\\(begin|end)\{(equation|aligned|gathered|algorithmic|tabularx|tikzpicture"
    r"|figure|tcolorbox|center|minipage|n1prop|n1lema|n1obs)")
CMD_ONLY = re.compile(r"^\s*\\[a-zA-Z@]+")


def paragraphs(text: str):
    body = text[text.find(r"\begin{document}"):]
    depth = 0
    buf, out = [], []
    for line in body.splitlines():
        if line.lstrip().startswith("%"):
            continue
        m = SKIP_ENV.search(line)
        if m:
            depth += 1 if m.group(1) == "begin" else -1
            depth = max(0, depth)
            continue
        if depth > 0:
            continue
        if not line.strip():
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        if CMD_ONLY.match(line) and "\\," not in line and "\\emph" not in line:
            continue
        buf.append(line.strip())
    if buf:
        out.append(" ".join(buf))
    # solo parrafos con prosa real
    return [p for p in out
            if len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}", p)) >= 12]


def sentences(par: str):
    par = re.sub(r"\$[^$]*\$", "M", par)
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+", par) if s.strip()]


def main(path):
    text = io.open(path, encoding="utf-8").read()
    pars = paragraphs(text)
    words = sum(len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", p)) for p in pars)

    mould = 0
    multi_disclaim = 0
    openings = collections.Counter()
    semis = 0
    n_sent = 0
    counts = collections.Counter()

    for p in pars:
        ss = sentences(p)
        n_sent += len(ss)
        semis += p.count(";")
        has_i = any(INTERP.search(s) for s in ss)
        n_d = sum(1 for s in ss if DISCLAIM.search(s))
        if has_i and n_d >= 1 and len(ss) >= 3:
            mould += 1
        if n_d >= 2:
            multi_disclaim += 1
        first = re.sub(r"^\W+", "", p)
        openings[" ".join(first.split()[:2]).lower()] += 1
        for name, rx in (("evaluativo", EVAL), ("metadiscurso", META),
                         ("familia frontera/contrato", HEDGE_FAMILY)):
            counts[name] += len(rx.findall(p))

    print("=" * 70)
    print("Auditoria de voz — %s" % os.path.basename(path))
    print("parrafos de prosa: %d | frases: %d | palabras: %d"
          % (len(pars), n_sent, words))
    print("=" * 70)
    print()
    print("1. MOLDE  declarativa -> interpretacion -> descargo")
    print("   parrafos con el molde completo : %3d de %d  (%.0f %%)"
          % (mould, len(pars), 100.0 * mould / max(1, len(pars))))
    print("   parrafos con 2+ descargos      : %3d        (%.0f %%)"
          % (multi_disclaim, 100.0 * multi_disclaim / max(1, len(pars))))
    print("   objetivo: molde <= 25 %, cadenas <= 5 %")
    print()
    print("2. APERTURAS DE PARRAFO repetidas")
    for k, v in openings.most_common(8):
        if v > 1:
            print("   %-28s x%d" % (k, v))
    uniq = sum(1 for v in openings.values() if v == 1)
    print("   aperturas unicas: %d de %d (%.0f %%)"
          % (uniq, len(pars), 100.0 * uniq / max(1, len(pars))))
    print()
    print("3. PUNTO Y COMA")
    print("   %d en %d frases = %.2f por frase   (objetivo <= 0.15)"
          % (semis, n_sent, semis / max(1, n_sent)))
    print()
    print("4. VOCABULARIO por 1000 palabras")
    for name in ("evaluativo", "metadiscurso", "familia frontera/contrato"):
        print("   %-28s %3d  (%.1f)"
              % (name, counts[name], 1000.0 * counts[name] / max(1, words)))
    print()
    print("=" * 70)
    return mould, len(pars)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "..", "sp1.tex")
    main(os.path.abspath(target))
