# QA — revisión V3 compacta de cuatro páginas

## Entregable

- Fuente: `MROB_literature_review_compact_4p.tex`
- PDF: `output/pdf/MROB_literature_review_compact_4p.pdf`
- SHA-256: `6B8D11783A12F4412752BF708F4E564130CD07C31E1360E21C327460D002AB0B`
- Formato: letter, cuatro páginas, XeLaTeX.

## Trazabilidad numérica

`academic-review/scripts/build_v3_compact_review.py` lee los derivados V3,
comprueba invariantes y genera `compact_metrics.tex`, tres figuras PDF y
`build_manifest.json`. Los valores comprobados fueron:

- 3.014 identidades de descubrimiento;
- 244 documentos en el corpus analítico;
- 168 textos adecuados y 20 fichas de lectura cercana;
- SP1 = 115, SP2 = 15, SP3 = 20;
- SP1--SP2 = 2, SP1--SP3 = 10, SP2--SP3 = 0 y triple interfaz = 0;
- simulación = 99, señal industrial = 25, experimento físico = 12 y análisis
  formal = 7.

## Comprobaciones ejecutadas

- `python academic-review/scripts/build_v3_compact_review.py`: correcto.
- `python -m py_compile academic-review/scripts/build_v3_compact_review.py`:
  correcto.
- `python -m pytest -q academic-review/tests`: 63 aprobadas; una advertencia
  preexistente de compatibilidad de dependencias de `requests`.
- XeLaTeX, dos pasadas: cuatro páginas; sin `Overfull`, `Undefined` ni
  `Missing character` en el log final.
- `pdftotext -layout`: secciones, brecha, agenda y declaraciones presentes.
- `pdftoppm` + inspección visual: cuatro páginas revisadas; figuras, tablas,
  cabeceras, enlaces y numeración legibles y sin recortes visibles.

## Limitación mantenida

El documento se denomina revisión sistematizada de mapeo y síntesis crítica.
No afirma exhaustividad, prevalencia poblacional ni meta-análisis porque WoS y
arXiv quedaron parciales y solo 20 fuentes recibieron lectura cercana.

