# Correcciones finales tras la revisión integral de 117 páginas

## Propósito y resultado observable

Resolver los defectos residuales señalados en la revisión integral del manuscrito de 117 páginas y regenerar `thesis/build/main.pdf`. El resultado observable será una memoria con folios romanos legibles en el índice, etiquetas metodológicas consistentes, notación y bibliografía corregidas, explicaciones completas de la evidencia integrada y trazabilidad estadística verificable.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, las fuentes reproducibles en `src/`, `scripts/` y `results/`, y el árbol LaTeX de `thesis/`. La petición procede del adjunto `pasted-text.txt`. El árbol ya contiene cambios extensos del autor; este pase conserva esas modificaciones y aplica parches focalizados.

## Alcance y no alcance

Incluye los puntos 1--4 de la revisión: índice, nombres de métodos, notación SP8, títulos bibliográficos, erratas, formato de tablas, definiciones de SP0, explicación de Industrial 2 y Cargo integrada, verificación del contraste de seguridad y limpieza estilística dirigida.

No incluye crear tag, release, DOI, commit o instantánea final; tampoco cambia el título administrativo ni la cabecera sin confirmación del director. La revisión visual de la Figura 14 y del índice sí forma parte de la validación local.

## Supuestos y preguntas resueltas

- Las etiquetas de métodos conservarán nombres identificables en inglés (`Greedy`, `Greedy-Q`, `Hungarian`) cuando ya aparecen así en figuras no regeneradas; la prosa usará “método voraz” y “algoritmo húngaro” como descriptores.
- La complejidad de SP8 se expresará con `A`, número de coaliciones en SP7, y con `K`, número de coaliciones/cargas en la campaña SP8, solo donde cada símbolo esté definido. La fila H5a debe coincidir con la notación local de su tabla.
- El valor y el test de la ablación de seguridad solo se modificarán si el script o los datos procesados contradicen el manuscrito.
- La limpieza estilística será dirigida: reducirá construcciones contrastivas mecánicas y arranques telegráficos sin alterar cautelas científicas necesarias.

## Diseño matemático/técnico

La definición de `\mathcal D_0`, la matriz `\kappa^{\mathrm{pad}}`, la brecha normalizada de SP8 y la complejidad H5a se contrastarán con las pruebas anexas y el registro de notación. Las tablas generadas se corregirán en su script productor y se regenerarán o sincronizarán; no se editará únicamente el artefacto derivado cuando exista fuente.

## Plan experimental

No se generan campañas nuevas. Se reconstruirá el contraste de la ablación integrada desde las tablas procesadas y el script de análisis, se ejecutarán pruebas focalizadas, se recompilará el PDF y se renderizarán las páginas del índice, Tabla 30, Figura 14, bibliografía y anexos afectados.

## Hitos

- [x] Hito 1 — Todas las incidencias textuales y de notación están localizadas y vinculadas a su fuente.
- [x] Hito 2 — Fuentes, generadores y artefactos derivados quedan sincronizados.
- [x] Hito 3 — El contraste de seguridad queda reproducido y su test se nombra explícitamente.
- [x] Hito 4 — Pruebas, compilación, auditoría del log y revisión visual del PDF pasan.

## Validación

- búsquedas dirigidas de etiquetas, erratas, símbolos y tics estilísticos;
- ejecución del análisis estadístico o reconstrucción desde datos procesados;
- pruebas unitarias focalizadas de SP0, SP3, SP6, SP8 e integración cuando los archivos afectados lo exijan;
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`;
- `pdfinfo`, extracción de texto y render PNG de páginas críticas;
- revisión del diff por archivo y comprobación de que no se pisan cambios ajenos.

## Riesgos y mitigaciones

- **Árbol de trabajo muy modificado:** usar parches mínimos y comparar cada archivo contra su diff previo.
- **Inconsistencia entre LaTeX y tablas generadas:** cambiar primero el generador y reconstruir el artefacto.
- **Cambio estadístico injustificado:** conservar cifra y lenguaje hasta reproducir el test exacto.
- **Corrección del índice dependiente de fuente:** validar visualmente con el PDF, no solo mediante extracción de texto.
- **Sobreedición estilística:** preservar negaciones que delimitan evidencia y modificar solo construcciones repetitivas equivalentes.

## Registro de decisiones

- 2026-07-17 — Mantener fuera de alcance tag/release/DOI y la decisión de cabecera, reservados al autor/director.
- 2026-07-17 — Usar etiquetas `Greedy`/`Greedy-Q` para coincidir con figuras existentes y español descriptivo en prosa.
- 2026-07-17 — Aplicar `manuscript-writing-review` en modo dirigido y `avoid-ai-writing` en modo de reescritura focalizada, con perfil técnico-académico.
- 2026-07-17 — Validar el PDF mediante renderizado conforme a la habilidad `pdf`.
- 2026-07-17 — Ajustar la voz del autor eliminando el punto y coma de la prosa narrativa. Se conservan únicamente separadores técnicos en tablas, notación, TikZ y citas APA.

## Progreso

Correcciones aplicadas en fuentes LaTeX, generadores y artefactos derivados. H2 se reprodujo con Wilcoxon unilateral sobre 90 medias por instancia (`p_Holm = 5.794818526828786e-21`) y H3 con McNemar exacto (`p_Holm = 6.462348535570529e-27`). Pasaron 35 pruebas focalizadas. La última pasada estilística dejó en cero las construcciones `; no` y los puntos y coma de los párrafos narrativos. `thesis/build/main.pdf` se regeneró con 117 páginas; el cuerpo termina en la página 80 y las referencias empiezan en la 81. La inspección renderizada confirmó folios romanos con punto visible, Figura 14 íntegra, Tabla 30 legible y las páginas reescritas sin defectos de maquetación. El log no contiene referencias/citas indefinidas, cajas desbordadas ni errores fatales.
