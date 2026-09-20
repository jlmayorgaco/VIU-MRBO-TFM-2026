"""Verificador mecanico de conformidad VIU sobre el PDF compilado.

Comprueba lo que una maquina puede comprobar sin abrir Word: tamano de pagina,
fuentes incrustadas y sustituciones silenciosas, extension total y por capitulo,
reparto del cuerpo, resumen y palabras clave.

No sustituye a docs/01_VIU_REQUIREMENTS.md ni a docs/06_VIU_TEMPLATE_FIDELITY.md,
que conservan la autoridad. Esto solo dice si el PDF de hoy sigue cumpliendo.

Uso:
    python viu_check.py [ruta/main.pdf]

Codigo de salida: 0 si no hay fallos duros, 1 si los hay.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

A4_PT = (595.276, 841.890)
A4_TOL = 1.0

# docs/01_VIU_REQUIREMENTS.md secciones 2 y 6
CUERPO_MIN, CUERPO_MAX = 50, 80
ANEXOS_MAX = 20
RESUMEN_MIN, RESUMEN_MAX = 200, 300
KEYWORDS_MIN, KEYWORDS_MAX = 3, 5
CAP6_MIN_FRAC = 0.50

# Fuentes que delatan una sustitucion: la plantilla exige Arial.
SUSTITUTOS = ("TeXGyreHeros", "NimbusSans", "Helvetica", "LMSans", "cmss")

OK, WARN, FAIL = "OK", "AVISO", "FALLO"
_estado: list[tuple[str, str, str]] = []


def anota(nivel: str, prueba: str, detalle: str) -> None:
    _estado.append((nivel, prueba, detalle))


def run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=120)
        return out.stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return ""


def check_geometria(pdf: Path) -> int:
    txt = run(["pdfinfo", str(pdf)])
    if not txt:
        anota(WARN, "Geometria", "pdfinfo no disponible; comprobar a mano")
        return 0
    paginas = 0
    m = re.search(r"^Pages:\s+(\d+)", txt, re.M)
    if m:
        paginas = int(m.group(1))
    ms = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+)", txt, re.M)
    if ms:
        w, h = float(ms.group(1)), float(ms.group(2))
        if abs(w - A4_PT[0]) < A4_TOL and abs(h - A4_PT[1]) < A4_TOL:
            anota(OK, "Tamano de pagina", "A4 vertical (%.0f x %.0f pt)" % (w, h))
        else:
            anota(FAIL, "Tamano de pagina", "%.1f x %.1f pt, no es A4" % (w, h))
    anota(OK, "Paginas totales", "%d" % paginas)
    return paginas


def check_fuentes(pdf: Path) -> None:
    txt = run(["pdffonts", str(pdf)])
    if not txt:
        anota(WARN, "Fuentes", "pdffonts no disponible; comprobar a mano")
        return
    lineas = [l for l in txt.splitlines()[2:] if l.strip()]
    nombres = [l.split()[0] for l in lineas if l.split()]
    arial = [n for n in nombres if "Arial" in n]
    # Columnas de pdffonts: name type encoding emb sub uni object ID
    # 'object ID' son dos tokens finales, asi que 'emb' es tokens[-5].
    no_emb = []
    for l in lineas:
        t = l.split()
        if len(t) >= 6 and t[-5] == "no":
            no_emb.append(t[0])

    if arial:
        anota(OK, "Arial incrustada", ", ".join(sorted({n.split("+")[-1] for n in arial})))
    else:
        anota(FAIL, "Arial incrustada", "no se encontro ninguna variante de Arial")

    sustituidas = sorted({n.split("+")[-1] for n in nombres
                          if any(s.lower() in n.lower() for s in SUSTITUTOS)})
    if sustituidas:
        anota(FAIL, "Sustitucion de fuente",
              "%s presente(s): LaTeX sustituyo Arial en alguna forma. "
              "Buscar 'Font shape' + 'undefined' en el .log" % ", ".join(sustituidas))
    else:
        anota(OK, "Sustitucion de fuente", "ninguna fuente sustituta detectada")

    if no_emb:
        anota(FAIL, "Incrustacion", "sin incrustar: %s" % ", ".join(no_emb[:5]))


def texto_pdf(pdf: Path) -> str:
    if shutil.which("pdftotext"):
        return run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"])
    try:
        import pypdf
        r = pypdf.PdfReader(str(pdf))
        return "\n".join((p.extract_text() or "") for p in r.pages[:12])
    except Exception:
        return ""


def check_resumen(pdf: Path) -> None:
    txt = texto_pdf(pdf)
    if not txt:
        anota(WARN, "Resumen", "no se pudo extraer texto; comprobar a mano")
        return
    m = re.search(r"Resumen\s*(.{200,4000}?)(?:Palabras\s+clave|Abstract|Keywords)",
                  txt, re.S | re.I)
    if not m:
        anota(WARN, "Resumen", "no localizado automaticamente; comprobar a mano")
    else:
        n = len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", m.group(1)))
        nivel = OK if RESUMEN_MIN <= n <= RESUMEN_MAX else FAIL
        anota(nivel, "Resumen 200-300 palabras", "%d palabras" % n)

    mk = re.search(r"Palabras\s+clave\s*:?\s*(.{0,300}?)(?:\n\s*\n|Abstract)", txt, re.S | re.I)
    if not mk:
        anota(WARN, "Palabras clave", "no localizadas; comprobar a mano")
    else:
        partes = [p.strip() for p in re.split(r"[;,•]", mk.group(1)) if p.strip()]
        nivel = OK if KEYWORDS_MIN <= len(partes) <= KEYWORDS_MAX else FAIL
        anota(nivel, "Palabras clave 3-5", "%d: %s" % (len(partes), "; ".join(partes[:6])))


def check_encabezado(pdf: Path) -> None:
    """Instrucciones §1.1: encabezado con nombre del estudiante y titulo abreviado."""
    info = run(["pdfinfo", str(pdf)])
    autor = ""
    m = re.search(r"^Author:\s+(.+)$", info, re.M)
    if m:
        autor = m.group(1).strip()
    if not autor:
        anota(WARN, "Encabezado", "sin metadato de autor; comprobar a mano")
        return

    # Encabezado de una pagina de cuerpo: las primeras lineas de texto.
    cabeceras = []
    for pag in (20, 40, 60):
        t = run(["pdftotext", "-enc", "UTF-8", "-f", str(pag), "-l", str(pag),
                 str(pdf), "-"])
        cabeceras.append(" ".join(t.splitlines()[:6]))
    cabecera = " ".join(cabeceras)

    apellidos = [p for p in autor.split() if len(p) > 3]
    if any(a.lower() in cabecera.lower() for a in apellidos):
        anota(OK, "Encabezado con el estudiante", "'%s' aparece en el encabezado" % autor)
    else:
        anota(FAIL, "Encabezado con el estudiante",
              "las Instrucciones exigen 'nombre del estudiante y titulo abreviado'; "
              "no se encontro '%s' en el encabezado" % autor)


def check_estructura(pdf: Path, paginas: int) -> None:
    """Reparto por capitulo a partir del indice del PDF."""
    try:
        import pypdf
    except ImportError:
        anota(WARN, "Estructura", "pypdf no instalado; reparto por capitulo sin comprobar")
        return
    try:
        r = pypdf.PdfReader(str(pdf))
        outline = r.outline
    except Exception as exc:
        anota(WARN, "Estructura", "no se pudo leer el indice (%s)" % exc.__class__.__name__)
        return

    capitulos: list[tuple[str, int]] = []

    def recorre(nodo, nivel=0):
        if isinstance(nodo, list):
            for hijo in nodo:
                recorre(hijo, nivel)
            return
        try:
            titulo = str(nodo.title).strip()
            pag = r.get_destination_page_number(nodo) + 1
        except Exception:
            return
        if nivel == 0:
            capitulos.append((titulo, pag))

    if isinstance(outline, list):
        for item in outline:
            if isinstance(item, list):
                continue
            recorre(item, 0)

    if not capitulos:
        anota(WARN, "Estructura", "el PDF no expone marcadores de capitulo")
        return

    filas = []
    for i, (t, p) in enumerate(capitulos):
        fin = capitulos[i + 1][1] - 1 if i + 1 < len(capitulos) else paginas
        filas.append((t, p, max(0, fin - p + 1)))

    anota(OK, "Capitulos detectados", "%d" % len(filas))
    print("\n  Reparto por capitulo (desde los marcadores del PDF)")
    print("  " + "-" * 66)
    for t, p, n in filas:
        print("  p.%-5d %-46s %3d pag." % (p, t[:46], n))
    print("  " + "-" * 66)

    def busca(*claves):
        for t, p, n in filas:
            tl = t.lower()
            if any(k in tl for k in claves):
                return n
        return None

    resultados = busca("resultado", "analisis", "análisis")

    # Cuerpo principal = capitulos numerados 1..7 (Introduccion..Conclusiones).
    # Fuera: preliminares (Resumen, Abstract, Nomenclatura), Referencias y anexos.
    numerado = re.compile(r"^\d+\s")
    excluir = ("bibliograf", "referencia")
    cuerpo = sum(n for t, p, n in filas
                 if numerado.match(t) and not any(k in t.lower() for k in excluir))
    anexos = sum(n for t, p, n in filas
                 if re.match(r"^[A-Z]\s", t) and not numerado.match(t))
    prelim = sum(n for t, p, n in filas if not numerado.match(t)
                 and not re.match(r"^[A-Z]\s", t))
    if prelim:
        anota(OK, "Preliminares", "%d paginas (fuera del computo del cuerpo)" % prelim)

    if cuerpo:
        nivel = OK if CUERPO_MIN <= cuerpo <= CUERPO_MAX else FAIL
        anota(nivel, "Cuerpo 50-80 paginas", "%d paginas" % cuerpo)
    if anexos:
        nivel = OK if anexos <= ANEXOS_MAX else FAIL
        anota(nivel, "Anexos <= 20 paginas", "%d paginas" % anexos)
    if resultados and cuerpo:
        frac = resultados / cuerpo
        nivel = OK if frac >= CAP6_MIN_FRAC else FAIL
        anota(nivel, "Resultados >= 50 % del cuerpo",
              "%d de %d paginas (%.0f %%)" % (resultados, cuerpo, 100 * frac))


def main(pdf: Path) -> int:
    if not pdf.exists():
        print("No existe %s. Compila primero: powershell -File thesis/build.ps1" % pdf)
        return 1

    print("=" * 72)
    print("Conformidad VIU  ·  %s" % pdf)
    print("=" * 72)

    paginas = check_geometria(pdf)
    check_fuentes(pdf)
    check_resumen(pdf)
    check_encabezado(pdf)
    check_estructura(pdf, paginas)

    print()
    print("=" * 72)
    fallos = 0
    for nivel, prueba, detalle in _estado:
        marca = {OK: "  ok  ", WARN: " aviso", FAIL: " FALLO"}[nivel]
        print("[%s] %-32s %s" % (marca, prueba, detalle))
        if nivel == FAIL:
            fallos += 1
    print("=" * 72)
    print("%d fallo(s) duro(s)." % fallos)
    if fallos:
        print("Nada de esto se arregla en el PDF: se arregla en la fuente y se recompila.")
    print("Lo que este guion NO comprueba: margenes reales, interlineado, color y")
    print("tamano de los titulos, portada, APA 7 y la apertura manual en Word.")
    print("Para eso, la seccion 3 de la habilidad viu-compliance.")
    return 1 if fallos else 0


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("thesis/build/main.pdf")
    sys.exit(main(destino))
