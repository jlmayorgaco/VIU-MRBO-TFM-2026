SP1 compactado a 20 páginas — estructura esperada
==================================================

Copiar `sp1.tex` en:
C:\Users\walla\Documents\Github\VIU-MRBO-TFM-2026\Subdocuments\SP1

El documento espera:

- references.bib
- viu-mrob-thesis.sty
- generated/metrics.tex
- opcional: generated/n4_v3_results_macros.tex
- opcional: generated/n4_v4_results_macros.tex

TikZ:
- figures/compact/*.tex   (incluidos en este bundle)
- figures/protocol_pipeline.tex
- figures/n2_model_boundary.tex
- figures/n4/*.tex

PDFs:
- assets/figures/n1/*.pdf
- assets/figures/n2/*.pdf
- assets/figures/n3/*.pdf
- assets/figures/n4/*.pdf

Compilación:
lualatex sp1.tex
biber sp1
lualatex sp1.tex
lualatex sp1.tex

La versión compacta conserva las ecuaciones (1)--(23), las siete tablas,
los cinco algoritmos y el contenido visual de las 42 figuras originales,
pero reorganiza estas últimas como paneles de 20 páginas.
