# Plan de implementación de la revisión bibliográfica

Este plan mantiene el alcance del TFM y la estructura canónica autorizada por
el autor: `academic-review/`. Los documentos adjuntos se trataron como
material de entrada y referencia; no sustituyen el contrato del repositorio ni
autorizan acciones fuera de la etapa indicada.

## Principios operativos

- Preservar fuentes crudas, valores originales, provenance y lineage.
- Mantener separado el corpus candidato del ledger/evidencia existente.
- Usar `unclear` cuando la evidencia no permita una clasificación firme.
- No raspar Web of Science ni Google Scholar; WoS entra mediante exportación
  manual y Scholar mediante cola manual futura.
- No convertir presencia de palabras clave, citas o metadatos en evidencia
  científica.
- No afirmar optimalidad, convergencia, robustez, escalabilidad, novedad o
  ausencia universal sin definición y evidencia correspondientes.

## Stage 0 — inspección y diagnóstico

**Estado: completado.** Se inspeccionaron el repositorio y el ZIP de bootstrap,
se registraron sus hashes y se confirmó la ausencia de semillas `academic_*`,
PDF de revisión separado y exportación WoS. No se hicieron llamadas externas
en esta etapa.

## Stage 1A — corpus candidato abierto

**Estado: completado y validado el 2026-09-12.**

Se ejecutó bajo `academic-review/` con el siguiente alcance:

1. importar las 32 semillas legacy sin descartar metadatos incompletos;
2. asignar IDs deterministas y conservar campos originales y `seed_raw`;
3. enriquecer metadatos vía Crossref sin promover semillas a evidencia;
4. ejecutar las familias Q1–Q7 en Crossref y OpenAlex con caché, timeout,
   rate limit, reintentos solo para estados transitorios y logs explícitos;
5. traducir la sintaxis de consulta al formato OpenAlex dejando la consulta
   canónica intacta en `stage1a_search_log.csv`;
6. reconciliar DOI exacto y coincidencias de metadatos de forma conservadora;
7. retener probables duplicados para revisión manual;
8. producir el corpus CSV/JSONL y la QA/provenance solicitadas.

La compuerta se superó: 246 candidatos únicos, 0 fallos terminales de API,
32 semillas preservadas como `unverified_seed`, y WoS explícitamente pendiente.

No se ejecutaron screening, texto completo, snowballing, prior-art final,
novelty/gap analysis ni redacción científica.

## Stage 1B — auditoría de cobertura y screening

**Estado: completado y validado el 2026-09-12.**

Se congelaron los artefactos Stage 1A con un manifest SHA-256 y se ejecutó el
protocolo `screening_protocol_v1` sobre una sola entrada derivada. La etapa
incluyó resolución conservadora de los 9 grupos probables, auditoría de los 5
registros sin DOI, reconciliación de las 32 semillas, matriz de conceptos y
snowballing de una ronda sobre 20 anclas mediante OpenAlex. Se recuperaron 2
DOI únicamente cuando Crossref/OpenAlex coincidieron con título, año y autor.

El corpus final contiene 1218 candidatos, de los cuales 340 quedaron en
`include_fulltext`, 280 en `maybe_fulltext` y 598 en `exclude`. El diagnóstico
de recall observó 463 registros nuevos relevantes o plausibles y, por tanto,
no permite declarar saturación. Se realizó una auditoría manual de 20
incluidos, 20 excluidos y 20 `maybe`; se registraron 0 correcciones en una
revisión de un único auditor, no como acuerdo interevaluador.

Los registros siguen siendo `not_evidence`. La cola de texto completo no se
descargó ni se utilizó para redactar afirmaciones; Web of Science continúa
pendiente como exportación externa.

## Stage 1C — reparación acotada de consultas

**Estado: completado y validado el 2026-09-12.**

El recall de Stage 1B mostró familias relevantes ausentes de Q1–Q7, por lo que
se ejecutó una sola ronda de reparación con ocho familias dirigidas: juegos
poblacionales/evolutivos, seguridad/CBF, contexto industrial, formación/docking,
multi-agent robótico, transporte colectivo, fuerza/wrench y AMR/AGV logístico.
Q1–Q7 no se modificaron. Se hicieron 16 ejecuciones, una por proveedor abierto
para cada familia, y una segunda comprobación one-hop acotada.

La ronda añadió 278 candidatos por consultas y 730 por la comprobación de
recall; 437 fueron relevantes o plausibles. El derivado final contiene 2226
registros, con 515 `include_fulltext`, 542 `maybe_fulltext` y 1169
`exclude`. Como persistió la recuperación de literatura relevante, no se
declara saturación; la expansión automática se detiene después de esta ronda.

Todos los registros permanecen en `not_evidence`. Stage 2 usa la cola Stage 1C
y se limita a adquisición legal/open de texto completo, sin bypass de controles.

## Stage 2 — semillas originales y WoS manual

**Estado: pendiente de entrada externa.**

- Recibir o ubicar los archivos semilla `academic_*.csv` y cualquier export
  WoS auténtico, preferentemente `Full Record and Cited References`.
- Calcular SHA-256 antes/después y registrar manifest de copia.
- Implementar/probar parsers CSV, TSV, TXT, XLSX y BibTeX según el formato
  real recibido.
- Conservar archivos originales y producir una cola explícita para filas
  fallidas; detener si la pérdida supera el umbral documentado.

## Stages posteriores — no iniciados

1. **Stage 3:** cliente HTTP compartido y pilotos documentados de OpenAlex,
   arXiv, Semantic Scholar y Unpaywall según necesidad.
2. **Stage 4:** normalización, version linkage y lineage ampliada.
3. **Stage 5:** texto completo legal, validación PDF y extracción por página.
4. **Stage 6:** coding de texto completo, codebook y claim evidence con decisiones
   auditables.
5. **Stage 7:** descubrimiento masivo controlado y reconciliación de fuentes.
6. **Stage 8:** lectura profunda, snowballing y saturación.
7. **Stage 9:** analítica y figuras derivadas de datasets congelados.
8. **Stage 10:** BibTeX, informe, compilación y auditoría final.

Cada etapa requerirá sus propias pruebas, configuración versionada, resultados
reproducibles, informe de limitaciones y compuerta antes de avanzar. Las cinco
figuras TikZ protegidas de la memoria no forman parte de esta Stage 1B y no se
han alterado.

## Política de commits

El HEAD base observado al cerrar Stage 1A era
`307683ea2eac7d7e5a2dc54190bd22b6d8589b7e` (`chore(repo): confirmar el
traslado de 26.136 ficheros a legacy/`). El árbol tenía cambios preexistentes;
esta tarea solo compromete sus artefactos aislados y no mezcla esos cambios.
El commit aislado de Stage 1A es
`67a1ecbfe6c0c13c0fa507121a2f5f864a2ccfce` (`review: build Stage 1A candidate
corpus pipeline`); el commit aislado de Stage 1B se añadirá después de
revisar el diff final es `3a99e1b8` (`review: complete Stage 1B screening and
recall audit`). No se hizo ni se hará push.
