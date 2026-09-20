# V3 — revisión sistematizada de mapeo y síntesis crítica para el TFM MROB

## Propósito y categoría metodológica

Construir un estado del arte reproducible, crítico y útil para justificar las
decisiones del TFM, con trazabilidad desde cada consulta hasta cada afirmación.
El producto se describirá como una **revisión sistematizada de mapeo y síntesis
crítica**, alineada con PRISMA 2020 y PRISMA-S cuando corresponda. No se llamará
revisión sistemática exhaustiva ni meta-análisis: las fuentes están incompletas
y los escenarios, robots y métricas de los estudios no son homogéneos.

V1/V2 no se modifican ni se reclasifican retrospectivamente como protocolo
prerregistrado. Se conservan como corpus exploratorio, anclas y procedencia.
V3 será un derivado con protocolo, registro de enmiendas, manifiestos y
artefactos propios.

## Pregunta rectora y alcance

**Pregunta rectora.** ¿Qué mecanismos verificables permiten formar coaliciones
heterogéneas de AMR, ejecutar transporte cooperativo físico y coordinar varias
coaliciones con información local, y qué garantías, supuestos, baselines y
límites empíricos están realmente demostrados?

La síntesis seguirá las interfaces canónicas:

1. SP1: asignación, capacidades/roles, juegos, consenso, subastas y cierre.
2. SP2: aproximación, contacto, wrench, pose, seguridad y sustitución. Cargo
   soportado es la modalidad primaria; empuje/caging se analiza por separado.
3. SP3: rutas, reservas, prioridad, congestión y redes imperfectas.
4. Ejes transversales: heterogeneidad, fallos, comunicación, explicabilidad y
   coste de cómputo/comunicación.

Se excluyen como evidencia directa MARL como mecanismo principal, trabajos de
un solo robot sin transferencia demostrable, redes/IoT sin operación robótica y
trabajos que no aporten una decisión, control o baseline aplicable al TFM.

## Estado de partida

- V1/V2 aportan candidatos, anclas, fuentes abiertas, logs y coding inicial.
- WoS aporta 154 registros reconciliados; F01 (50/80) y F02 (50/275) son
  parciales. Faltan 255 resultados para llamar completa esa fuente.
- Crossref, OpenAlex y snowballing son descubrimiento reproducible. arXiv es
  preprint hasta verificar la versión revisada por pares.
- Google Scholar será búsqueda manual de variantes, versiones y citas; no se
  raspa ni alimenta conteos bibliométricos finales.

## Avance operativo al 13 de septiembre de 2026

- **R0 completada:** el protocolo, el ledger V3, el registro de semillas, la
  cola priorizada, manifiestos y QA están generados en
  `academic-review/literature-review-v3/`.
- Se conservaron **2.309** candidatos históricos como descubrimiento, con una
  cola de **244** textos adquiridos legalmente para evaluación de lectura.
- La auditoría conservadora de acceso identificó **168** textos aptos para
  lectura cercana (145 PDF y 23 HTML) y **76** que requieren texto alternativo
  o inspección manual. Una página de vista previa no se cuenta como texto
  completo.
- R3 cuenta con 20 fichas de evidencia con pasajes localizados, cuatro de ellas
  derivadas de manuscritos arXiv y con control de versión. La trazabilidad de avance está en
  `data/close_reading_tracker_v3.csv`; una ficha completada no equivale a
  evidencia generalizable ni a una afirmación final del TFM.
- **R1 iniciada:** Crossref y OpenAlex completaron 44 ejecuciones de las 22
  familias y generaron 1.044 filas de descubrimiento, 898 identidades únicas
  por DOI/título antes de cribado. arXiv quedó `partial/not_available` en esta
  ejecución (21 fallos de red y un límite de tasa), con eventos y consultas
  conservados en el log. Esto no se interpreta como ausencia de preprints.
- R1 y R2 permanecen parciales por la cobertura WoS/arXiv descrita. Para el
  cierre solicitado, la síntesis usa el corpus adquirido sin representar esa
  parcialidad como ausencia de estudios.
- **R4 completada para el corpus disponible:** se generaron mapas de año,
  método, arquitectura, aplicación, autores, venues, coocurrencias e interfaces.
- **R5 completada a nivel de manuscrito V3:** existe una revisión de 9.000+
  palabras con referencias verificadas, agenda experimental y limitaciones; el
  ledger bibliográfico fue actualizado. La integración en la memoria VIU y una
  revisión humana independiente quedan como pasos editoriales posteriores.

El protocolo V3 se congela antes de nuevas búsquedas. Todo cambio de consulta,
filtro o criterio será una enmienda con fecha, motivo, impacto y decisión sobre
repetir la familia afectada.

## Fuentes y cartera de consultas

| Fuente | Papel | Regla |
|---|---|---|
| Web of Science | Índice principal y cita hacia adelante | No afirmar cobertura completa hasta completar F01/F02 |
| Crossref/OpenAlex | Descubrimiento, DOI y metadatos | No equivalen a indexación selectiva |
| arXiv | Detección temprana y texto abierto | Distinguir preprint de versión final |
| Google Scholar | Citas hacia atrás/adelante y versiones | Manual; sin scraping ni métricas de conteo |
| Editor/repositorio | Texto legal y versión de registro | Confirmar identidad antes de extraer evidencia |
| Scopus/IEEE Xplore | Complemento futuro opcional | Crear enmienda; nunca inferir cobertura |

La cartera F01--F16 existente se conserva y se agrupa así:

| Bloque | Familias | Propósito |
|---|---|---|
| A — SP1 | F01--F04, F15 | coalición y asignación heterogénea |
| B — SP2 estratégico | F05, F06, F09, F10 | transporte cooperativo distribuido |
| C — SP2 físico | F07, F08 | contacto, wrench, caging y factibilidad |
| D — resiliencia/red | F11, F12, F16 | fallo, sustitución y comunicación |
| E — SP3 | F13, F14 | tráfico y congestión multi-coalición |

Antes de ejecutar V3 se generará `query_ledger_v3.csv` a partir de los packs
de `academic-review/multisource-v2/manual-packs/`. Guardará sintaxis exacta por
fuente, fechas, filtros, total mostrado, formato de exportación y hash. Cada
bloque admite solo una consulta base, una sensibilidad por sinónimos y una ronda
de citas por anclas: no se abrirán variantes ilimitadas.

## Selección y ficha de lectura

Tres niveles no intercambiables:

1. **Descubrimiento:** título, resumen, DOI, procedencia y motivo de inclusión.
2. **Verificación bibliográfica:** identidad, versión, venue y estado
   *peer-reviewed/preprint*.
3. **Evidencia científica:** lectura de texto completo con página, sección,
   ecuación, tabla o figura. Solo este nivel respalda método, garantía, modelo
   físico, resultado o limitación.

Cada artículo núcleo se extrae con la misma ficha: problema/SP; tipo de robot,
carga y contacto; información local/global; método y parámetros; supuesto y
garantía; baseline, escenario, réplicas y métricas; resultado cuantitativo con
localizador; límite o resultado negativo; relación concreta con el TFM.

La automatización puede sugerir snippets y apoyar el descubrimiento, pero no
promueve evidencia sin verificación contra la fuente. Si no hay dos revisores
humanos, se reportan correcciones de auditoría, no acuerdo interrevisor.

## Fases y gates

### R0 — protocolo congelado

- Crear `literature-review-v3/` con protocolo, criterios, esquema de datos,
  ledger de consultas, manifiesto de entorno y registro de enmiendas.
- Importar V1/V2/WoS actual únicamente como semillas y procedencia.
- Definir deduplicación DOI--título--versión y taxonomía SP1--SP3.

**Gate:** ninguna nueva búsqueda entra al corpus V3 sin protocolo versionado.

### R1 — búsqueda y trazabilidad

- Ejecutar consultas abiertas con caché, límite de tasa y logs.
- Incorporar los seis tramos WoS faltantes si se obtienen.
- Hacer consulta manual de Scholar solo desde anclas, registrando fecha y
  decisiones; no exportación masiva ni scraping.
- Recuperar solo textos legalmente abiertos/accesibles y enlazar preprint con
  versión editorial.

**Gate:** cada fuente queda `complete`, `partial`, `not_available` o
`not_queried`; nunca se infiere una cobertura inexistente.

### R2 — deduplicación y cribado auditado

- Reconciliar DOI, título, autores, año, versión y procedencia conservando
  aliases.
- Aplicar criterios predefinidos y conservar causa de cada exclusión.
- Auditar una muestra estratificada de decisiones y registrar correcciones.

**Gate:** flujo de selección reproducible antes de síntesis o bibliometría.

### R3 — lectura profunda y evidencia

- Priorizar por hueco cubierto, relevancia para un claim/baseline, calidad y
  contraevidencia, no por número de citas solamente.
- Leer artículos núcleo y contraejemplos; extraer la ficha con localizadores.
- Mantener los inaccesibles como resumen/metadato, sin inferir detalles.

**Gate:** cada afirmación de borrador tiene fuente verificada y localizador, o
se elimina/reformula como pregunta abierta.

### R4 — síntesis y bibliometría limitada

- Generar tablas SP1/SP2/SP3 con arquitectura, información, modelo, garantías,
  baselines, métricas y límites.
- Construir mapas descriptivos de año, venue, método, arquitectura y huecos.
- Hacer una ronda de snowballing desde anclas y artículos núcleo; registrar el
  rendimiento marginal sin afirmar saturación universal.

**Gate:** contradicciones, resultados negativos y amenazas a la validez deben
aparecer en la síntesis. No hay meta-análisis por falta de población y medida de
efecto comunes.

### R5 — integración y auditoría adversarial

- Actualizar `references/LITERATURE_LEDGER.md` con `verificada`, `parcial` o
  `pendiente`.
- Enlazar los claims del capítulo 5 y tablas de métodos de SP1--SP3 a fichas
  verificadas.
- Auditar DOI, versión, atribución, contexto, alcance, evidencia contraria y
  afirmaciones de novedad.

**Gate:** la revisión está lista para memoria solo si los conteos reproducen los
raw, cada claim externo tiene localizador y las limitaciones son explícitas.

## Entregables

1. Protocolo V3 y registro de enmiendas.
2. Ledger de consultas, raw hasheados y flujo de selección tipo PRISMA adaptado.
3. Corpus deduplicado con procedencia y política de versiones.
4. Fichas verificadas y matriz fuente--afirmación--evidencia.
5. Tablas críticas SP1--SP3, baselines y mapa de huecos.
6. Síntesis narrativa para capítulo 5, separada de los resultados del TFM.
7. Informe de cobertura, limitaciones, contraevidencia y reproducibilidad.

## Aporte necesario del autor

No hacen falta claves ni descargas masivas. La única acción que mejoraría
materialmente la cobertura ahora es aportar seis exportaciones WoS: F01
registros 51--80 y F02 registros 51--100, 101--150, 151--200, 201--250 y
251--275, en formato `Plain Text`, `Full Record and Cited References`.

Scopus o IEEE Xplore, si se habilitan después, entrarán mediante enmienda y no
se mezclarán silenciosamente. La interpretación final de los claims fuertes y
la versión entregable permanece bajo revisión del autor.

## Criterio de terminado

V3 termina con los siete entregables existentes, hashes desde raw hasta
síntesis, estados explícitos de fuente, cero citas inventadas, claims limitados
a evidencia localizada y limitaciones de cobertura/heterogeneidad declaradas.
