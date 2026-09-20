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

## Stage 2 — adquisición legal de texto completo

**Estado: completado y validado el 2026-09-12.**

Se procesaron 1057 registros de la cola Stage 1C mediante ubicaciones OA de
OpenAlex y enlaces públicos de Crossref. Se verificaron 230 objetos (144 PDF y
86 HTML); 30 quedaron como `abstract_only`, 776 como `unavailable_legally` y
21 como `retrieval_error`. Cada objeto promovido tiene identidad DOI/título,
hash, MIME, tamaño, URL y timestamp. Los binarios locales se excluyen de Git
por tamaño/licencia y se regeneran con el log/manifests.

## Stage 3 — coding científico de texto completo

**Estado: completado y validado el 2026-09-12.**

Los 230 textos verificados fueron leídos por extracción programática y
codificados con un codebook versionado. La matriz cubre problema, arquitectura,
supuestos de información, método, capa física, ejecución, teoría,
experimentos, resultados, limitaciones, rol y localización de evidencia. Los
30 resúmenes conservan un coding limitado; los casos metadata-only/error no
reciben detalle técnico. La matriz se declara primer pase estructural, no
lectura humana final.

## Stage 4 — síntesis, taxonomía, figuras y auditoría de novedad

**Estado: completado y validado el 2026-09-12.**

Se generaron las 16 analíticas requeridas, 20 análisis totales, 23 tablas CSV,
20 figuras PNG, mapa de evidencia SP1–SP3, mapa explícito de gaps y auditoría
adversarial. Todas las salidas se derivan de la matriz congelada; no se
presenta el conteo de registros como impacto científico y se mantiene la
conclusión de novedad sin resolver.

## Stage 5 — paquete académico final

**Estado: completado y validado el 2026-09-12.**

Se generó `academic-review/final/` sin modificar la memoria canónica, con
revisión completa/compacta, plan de integración SP1–SP3, matriz de claims,
triage CORE/ENABLING, exclusiones, limitaciones y manifest de reproducción.
No se generó LaTeX para evitar introducir una variante no compilada de la
memoria oficial.

WoS permanece como `pending_external_export`; su ausencia no bloqueó la
ejecución, pero impide declarar exhaustividad o novedad final.

Las cinco figuras TikZ protegidas no se alteraron.

## Compuerta posterior — lectura cercana y campañas reproducibles

**Estado: ejecutada y validada el 2026-09-12.**

Se creó un ledger de lectura cercana acotada para 16 fuentes priorizadas. Cada
fila queda ligada a la matriz Stage 3 y distingue texto completo local,
abstract/preview del editor y acceso limitado. El ledger registra de forma
simétrica el soporte de la fuente y aquello que no puede transferirse al TFM;
la verificación final del autor permanece obligatoria.

Se ejecutaron las campañas CPU versionadas de SP1, SP2, SP5 (pilot y
confirmatoria), SP6, SP7, SP8 y Cargo E2E integrada. El script de QA agregado
lee sus manifests y auditorías, conserva los estados de las campañas y separa
la evidencia reducida de la validación física. No se añadieron resultados al
manuscrito canónico.

La inspección seca de Coppelia confirmó el gate de autorización y de preflight
hash-bound; la campaña física no se inició. Web of Science continúa pendiente
de una exportación manual desde una sesión institucional autenticada.

Artefactos nuevos:

- `academic-review/scripts/close_read_prior_art.py` y su test.
- `academic-review/data/processed/prior_art_close_reading.csv` y
  `academic-review/reports/prior_art_close_reading.md`.
- `academic-review/scripts/followup_experiment_qa.py` y su test.
- `academic-review/data/processed/experimental_followup_campaigns.csv` y
  `academic-review/reports/experimental_followup_qa.md`.

## Política de commits

El HEAD base observado al cerrar Stage 1A era
`307683ea2eac7d7e5a2dc54190bd22b6d8589b7e` (`chore(repo): confirmar el
traslado de 26.136 ficheros a legacy/`). El árbol tenía cambios preexistentes;
esta tarea solo compromete sus artefactos aislados y no mezcla esos cambios.
El commit aislado de Stage 1A es
`67a1ecbfe6c0c13c0fa507121a2f5f864a2ccfce` (`review: build Stage 1A candidate
corpus pipeline`); el commit aislado de Stage 1B es `3a99e1b8` (`review:
complete Stage 1B screening and recall audit`) y el de Stage 1C es
`1ffe17e6` (`review: complete Stage 1C query repair`). No se hizo ni se hará
push. Stage 2 está en `f0757abd` (`review: complete Stage 2 legal full-text
acquisition`) y Stage 3 en `687d877e0` (`review: complete Stage 3 evidence
coding`); Stage 4 está en `f0ea343ad` (`review: complete Stage 4 synthesis
and gap audit`); Stage 5 está en `2d182e260` (`review: finalize academic
literature review package`).

## Multisource V2 — expansión de fuentes y evidencia

El 2026-09-13 se ejecutó la campaña derivada
`academic-review/multisource-v2/`. La configuración versionada ejecuta 22
consultas F1–F16 con ventanas primaria/fundacional y conserva las respuestas
RAW por fuente. La corrida produjo 1.225 registros normalizados y 3.033
candidatos reconciliados con V1; Crossref, OpenAlex, Semantic Scholar,
OpenAIRE y DOAJ aportaron resultados observables. Unpaywall quedó limitado a
500 DOI y OpenCitations a una comprobación one-hop de 20 anclas.

arXiv terminó `rate_limited`, DBLP `network_blocked` y CORE
`pending_credentials`; estos estados están reflejados en los informes y no se
interpretan como ausencia de trabajos. Google Scholar, WoS, Scopus e IEEE
Xplore no fueron automatizados: sus paquetes manuales permanecen pendientes
de exportación humana. La cola de evidencia contiene 60 textos completos V1
priorizados, pero solo 16 tienen lectura cercana explícita heredada; no se
declara lectura profunda completa, saturación ni novedad.
