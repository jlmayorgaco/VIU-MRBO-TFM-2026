# Revisión editorial y metodológica de SP1.N1

## Propósito y resultado observable

Elevar las cuatro páginas experimentales de SP1.N1 a un estándar editorial
próximo a una figura de revista, sin cambiar a posteriori las hipótesis, las
semillas ni los resultados confirmatorios. El resultado observable será un PDF
de diez páginas con figuras vectoriales legibles al ancho final, incertidumbre y
denominadores explícitos, acompañado por una auditoría de riesgos y artefactos
reproducibles actualizados.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md` y
  `docs/07_SP_SECTION_TEMPLATE.md` fijan alcance, protocolo, evidencia y
  lenguaje admisible.
- `experiments/configs/sp1_n1_confirmatory_v2.yaml` es el protocolo congelado.
- `scripts/sp1_n1.py` genera RAW, resúmenes, estadística y figuras.
- `scripts/sp1_levels_common.py` fija el estilo y la exportación.
- `thesis/sp1_levels_23p/main.tex` compone la vista activa de diez páginas.
- `tests/test_sp1_levels.py` protege conteos, invariantes, alcance y PDF.

## Alcance y no alcance

Incluye E1--E4 de N1: presentación de distribuciones, IC, corrección múltiple,
coste temporal/memoria, retirada estática y auditoría MILP de la frontera
heterogénea. Incluye revisión visual del PDF y verificación de los artefactos.

No reabre la campaña confirmatoria, no selecciona nuevas semillas, no cambia el
umbral práctico del 5 %, no convierte diagnósticos en hipótesis confirmatorias y
no atribuye escalabilidad, resiliencia operacional ni validez física a N1.

## Supuestos y preguntas resueltas

- La configuración y los RAW existentes son la fuente de verdad; se regenerará
  el postproceso con `--reuse-raw`.
- Las guías de IEEE y Nature se usan como referencia de legibilidad,
  accesibilidad y reproducibilidad, no como una afirmación de cumplimiento de
  una revista concreta.
- El Wilcoxon preespecificado se describirá como contraste de desplazamiento
  pareado. La afirmación sobre la mediana conservará su IC bootstrap y el gate
  práctico; no se reinterpretará Wilcoxon como prueba exacta de la mediana.
- Las fracciones de retirada son tratamientos anidados en un mismo mundo; cada
  celda conserva mundos independientes y los tratamientos no se contarán como
  nuevas réplicas independientes.

## Diseño matemático/técnico

- Exportar las figuras a 183 mm de ancho nominal, PDF vectorial con fuentes
  embebidas y PNG de 600 dpi.
- Usar una paleta apta para deficiencia de visión cromática y redundancia por
  marcador, trazo y relleno.
- E1: estimado + IC para el efecto primario y distribución visible del coste
  espacial, sin ocultar la cola mediante un boxplot sin outliers.
- E2: P50 [P05, P95], ajuste balanceado identificado como descriptivo, número de
  tamaños/réplicas y memoria exacta `8NM`.
- E3: frontera cardinal, denominador por celda y bootstrap del aumento mediano
  de coste solo en ejecuciones factibles.
- E4: IC de Wilson para falsos factibles, certificación y rescate, con
  denominadores distintos claramente indicados.

## Plan experimental

Se reutilizan 4.500 filas de E1, 630 de E2, 6.000 de E3 y 1.500 de E4. No se
crean nuevos mundos. El postproceso mantendrá los cinco escenarios espaciales,
las tres razones `M/N`, la cuadrícula reserva--retirada y los cinco niveles de
heterogeneidad. Los criterios confirmatorios siguen siendo los congelados; los
nuevos intervalos de E3/E4 son estimación y transparencia, no nuevos gates.

## Hitos

- [x] Hito 1 -- auditoría separada de riesgos estadísticos, gráficos y de
  reproducibilidad.
- [x] Hito 2 -- generador y pruebas actualizados sin alterar RAW ni hipótesis.
- [x] Hito 3 -- figuras, manifiesto y texto/captions regenerados.
- [x] Hito 4 -- PDF de diez páginas validado visualmente y batería de pruebas
  aprobada.

## Validación

- `python scripts/sp1_n1.py --reuse-raw`
- `python scripts/build_sp1_levels_pdf.py`
- `python -m pytest -q tests/test_sp1_levels.py tests/test_sp1_a1_hungarian.py tests/test_protected_tikz_figures.py`
- `pdfinfo`, `pdffonts` y render Poppler del PDF y de las figuras cuantitativas.
- Inspección visual de las páginas 6--10 a resolución suficiente para detectar
  solapes, texto menor al objetivo, leyendas ambiguas o clipping.

## Riesgos y mitigaciones

- **Doble uso de los datos:** no modificar hipótesis ni umbrales; etiquetar toda
  comprobación nueva como diagnóstica.
- **Pseudorreplicación:** mostrar mundo--semilla como unidad y denominadores por
  celda; no usar robots o tratamientos anidados como réplicas.
- **Sobreafirmación de complejidad:** conservar el ajuste log--log como
  descriptivo del intervalo y separar memoria determinista de tiempo medido.
- **Comparación injusta:** MILP solo audita validez externa de N1 en E4.
- **Maquetación:** verificar el PDF renderizado, no solo la compilación.

## Registro de decisiones

- 2026-08-06: se adopta una revisión en dos fases: auditoría de objeciones y
  corrección editorial/reproducible.
- 2026-08-06: no se promete un resultado "100 % inmune"; el criterio es que
  cada afirmación tenga evidencia, denominador, incertidumbre y límite visibles.

## Progreso

Revisión cerrada. Se conservaron los RAW y el protocolo congelado; se
regeneraron postproceso, manifiesto, seis figuras y PDF. Las páginas 6--10 se
inspeccionaron a resolución completa y la batería final terminó con 21 pruebas
aprobadas. El dictamen y las limitaciones residuales constan en
`reports/2026-08-06-sp1-n1-journal-readiness-audit.md`.
