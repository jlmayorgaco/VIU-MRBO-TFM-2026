"""Divide GUIDELINES.md en ficheros tematicos sin alterar su contenido.

El corte es por rangos de linea, de modo que cada bloque se copia literalmente:
no se reescribe, resume ni reordena nada. Solo se antepone una cabecera con el
titulo del bloque y el rango de origen, para que cualquier fragmento pueda
localizarse en el fichero original.

Uso:
    python scripts/split_guidelines.py [--dry-run]
"""
import argparse
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "GUIDELINES.md")
OUT = os.path.join(ROOT, "guidelines")

# (fichero, titulo, linea_inicio, linea_fin, descripcion para el indice)
# Rangos 1-indexados e inclusivos, verificados uno a uno sobre el original.
BLOCKS = [
    ("01-auditoria-maestra.md",
     "Auditoria maestra — los 60 frentes de revision",
     1, 984,
     "Indice maestro de auditoria: 60 bloques, de conformidad VIU a readiness final. "
     "Es el mapa del que cuelgan los demas ficheros."),

    ("02-coherencia-y-flujo.md",
     "Coherencia, flujo y «una sola tesis»",
     985, 2715,
     "Secciones A–CB: macroestructura, puentes entre capitulos, reverse outline, unidad de "
     "parrafo, signposting, ritmo visual, tests de lectura y scorecard de fluidez."),

    ("03-figuras-y-calidad-grafica.md",
     "Figuras y calidad grafica",
     2716, 4673,
     "Reglas 1–110: gate visual, tipografia, color, escala de grises, y un estandar por tipo "
     "de figura (barras, scatter, lineas, cajas, heatmaps, trayectorias, diagramas). "
     "Incluye los tests automaticos y el gate final por figura."),

    ("04-literatura-citas-y-referencias.md",
     "Literatura, marco teorico, citas y referencias",
     4674, 7307,
     "Secciones A–DZ: jerarquia de fuentes, citation overreach, verbos de atribucion, APA 7 "
     "campo a campo, auditoria de DOI y metadatos, y los gates de literatura."),

    ("05-checklist-por-fases.md",
     "Checklist maestro por fases (FASE 0–40)",
     7308, 8406,
     "De FASE 0 (requisitos oficiales VIU) a FASE 40 (criterio 10/10), pasando por "
     "trazabilidad, matematica, robotica, estadistica, figuras, originalidad, defensa y "
     "congelacion final."),

    ("06-guia-estrategica-viu.md",
     "Guia estrategica y evaluacion VIU MROB",
     8407, 8928,
     "Secciones 0–24 con las etiquetas `[VIU]` / `[P0]` / `[STRAT]` / `[VERIFICAR]`: como se "
     "evalua realmente el TFM, entregas, deposito, defensa y readiness."),

    ("07-turnitin-y-deteccion-ia.md",
     "Turnitin y deteccion de escritura asistida",
     8929, None,
     "Notas sobre el detector de Turnitin, patrones de escritura a evitar y consideraciones "
     "de integridad academica."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(SRC):
        print("no existe %s" % SRC)
        return 2

    lines = io.open(SRC, encoding="utf8", newline="").read().split("\n")
    total = len(lines)
    print("origen: GUIDELINES.md, %d lineas" % total)

    # comprobar cobertura completa y sin solapes antes de escribir nada
    covered, prev_end = [], 0
    for fn, _t, start, end, _d in BLOCKS:
        end = end if end is not None else total
        if start != prev_end + 1:
            print("AVISO: hueco o solape antes de %s (esperado %d, encontrado %d)"
                  % (fn, prev_end + 1, start))
        covered.append((fn, start, end))
        prev_end = end
    if prev_end < total:
        print("AVISO: quedan %d lineas sin asignar al final" % (total - prev_end))

    if args.dry_run:
        print("\n%-40s %8s %8s %8s" % ("fichero", "desde", "hasta", "lineas"))
        for fn, s, e in covered:
            print("%-40s %8d %8d %8d" % (fn, s, e, e - s + 1))
        return 0

    os.makedirs(OUT, exist_ok=True)
    written = []

    for (fn, title, start, end, desc) in BLOCKS:
        end = end if end is not None else total
        body = "\n".join(lines[start - 1:end])
        header = (
            "# %s\n\n"
            "> Parte de las directrices del TFM. Contenido copiado sin cambios de\n"
            "> `GUIDELINES.md`, lineas %d a %d. Indice en [`00-INDICE.md`](00-INDICE.md).\n\n"
            "---\n\n" % (title, start, end)
        )
        path = os.path.join(OUT, fn)
        io.open(path, "w", encoding="utf8", newline="").write(header + body)
        n = end - start + 1
        written.append((fn, title, desc, n))
        print("  %-42s %5d lineas" % (fn, n))

    idx = ["# Directrices del TFM — indice",
           "",
           "`GUIDELINES.md` se dividio en ficheros tematicos. El contenido es el mismo:",
           "los temas, preguntas y checklists se copiaron literalmente, sin resumir ni",
           "reordenar. Cada fichero indica de que lineas del original procede.",
           "",
           "| # | Fichero | Contenido | Lineas |",
           "|---|---|---|---:|"]
    for i, (fn, title, desc, n) in enumerate(written, 1):
        idx.append("| %d | [%s](%s) | **%s.** %s | %d |" % (i, fn, fn, title, desc, n))
    idx += ["",
            "## Como usarlo",
            "",
            "- **Antes de escribir prosa:** 02 (flujo) y, si toca literatura, 04.",
            "- **Antes de crear o revisar una figura:** 03.",
            "- **Antes de una entrega o del deposito:** 05 y 06.",
            "- **Para planificar una ronda de revision completa:** 01, que es el mapa.",
            "",
            "El original se conserva en [`../GUIDELINES.md`](../GUIDELINES.md).",
            ""]
    io.open(os.path.join(OUT, "00-INDICE.md"), "w", encoding="utf8", newline="").write(
        "\n".join(idx))
    print("  %-42s indice" % "00-INDICE.md")

    suma = sum(n for _f, _t, _d, n in written)
    print("\nlineas repartidas: %d de %d" % (suma, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
