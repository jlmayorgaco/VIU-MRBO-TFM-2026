# SP1 definitivo — N1 a N4

Esta carpeta es la fuente autónoma de trabajo de SP1. El punto de entrada es
`sp1.tex`; al ejecutar `./build.ps1` genera `sp1.pdf` en esta misma carpeta.
La compilación utiliza LuaLaTeX y Biber, no pdfLaTeX.

## Edición

- Editar `sp1.tex` para N1, N2 y N3.
- Editar `n4_v2.tex` para N4.
- No editar `generated/*.tex` ni `assets/figures/`: son artefactos congelados
  obtenidos de campañas ya ejecutadas.
- Los diagramas TikZ editables están en `figures/`.

## Recursos incluidos

- `viu-mrob-thesis.sty` y `references.bib`: estilo y bibliografía locales.
- `assets/figures/`: PDF vectoriales de resultados que necesita el documento.
- `generated/`: macros cuantitativas incluidas por LaTeX.
- `experiments/configs/`, `scripts/` y `provenance/`: configuraciones, scripts
  de origen y manifiestos que trazan los resultados congelados. Reejecutar esas
  campañas requiere el paquete `src/viu_mrob_tfm` del repositorio principal;
  no es necesario para editar ni compilar este subdocumento.

La fuente procede de `thesis/sp1_levels_23p/main.tex` y se ha adaptado para no
depender de rutas externas al directorio `Subdocuments/SP1`.
