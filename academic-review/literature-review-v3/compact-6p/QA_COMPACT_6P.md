# QA — revisión V3 compacta de seis páginas

## Entregable

- Fuente: `MROB_literature_review_compact_6p.tex`.
- PDF final: `output/pdf/MROB_literature_review_compact_6p.pdf`.
- SHA-256: `955F4E8F2EB38E51ED70BAEF531031A9045948B3394A4EB883F340EE1CDAB92F`.
- Formato: letter, seis páginas, XeLaTeX.

## Figuras restauradas

La edición conserva y recalcula las cinco familias visuales solicitadas:

1. mapa metodológico descentralizado--centralizado y white-box--data-driven;
2. matriz discriminante de capacidades;
3. diagrama de modalidades físicas;
4. cobertura/intersecciones y presupuesto de autoridad;
5. dashboard temporal de seis paneles.

También incorpora las figuras nuevas de evolución metodológica, madurez de
evidencia y cadena de certificados. `build_v3_compact_review_6p.py` genera las
figuras, macros, el manifiesto, la matriz codificada y el corte legado
congelado.

## Trazabilidad y comparabilidad

- V3: 3.014 identidades descubiertas, 244 documentos analíticos, 168 textos
  adecuados y 20 lecturas cercanas.
- Interfaces: SP1 = 115, SP2 = 15, SP3 = 20; SP1--SP2 = 2, SP1--SP3 = 10,
  SP2--SP3 = 0 y triple = 0.
- Evidencia: simulación = 99, señal industrial = 25, experimento físico = 12 y
  análisis formal = 7.
- Legado: se congelaron únicamente valores impresos en el `.tex` entregado
  (`n=59`, ventana fechada `n=54`, conteos de familias, discriminantes y cinco
  posiciones ordinales).
- No se fabricó una serie anual legado: el archivo crudo del dashboard anterior
  no estaba entre los materiales entregados. Las taxonomías legado y V3 se
  muestran separadas y se advierte que no son intercambiables.

## Comprobaciones ejecutadas

- Generador de figuras y manifiesto: correcto.
- `python -m py_compile academic-review/scripts/build_v3_compact_review_6p.py`:
  correcto.
- `python -m pytest -q academic-review/tests`: 63 pruebas aprobadas; una
  advertencia preexistente de compatibilidad de `requests`.
- XeLaTeX, dos pasadas: seis páginas.
- Log final: cero coincidencias para `Overfull`, `Undefined` o
  `Missing character`.
- `pdftotext -layout`: títulos de las cinco figuras restauradas, cadena de
  certificados y referencias presentes.
- `pdftoppm`: seis páginas renderizadas; todas inspeccionadas visualmente tras
  la compilación final, sin recortes ni solapamientos materiales.

## Limitación mantenida

El documento es una revisión sistematizada de mapeo y síntesis crítica. No se
declara revisión sistemática exhaustiva, prevalencia poblacional ni
meta-análisis porque WoS/arXiv quedaron parciales, el corpus fue enriquecido por
relevancia y solo 20 fuentes recibieron lectura cercana.

