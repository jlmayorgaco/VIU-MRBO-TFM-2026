# Protocolo V4: mapeo sistematizado, revisión técnica anidada y auditoría adversarial

**Versión:** V4.0  
**Fecha de corte operacional:** 2026-09-16  
**Unidad de análisis:** `canonical_work`, no una copia individual de PDF.

## Propósito y preguntas

V4 no pretende demostrar que ningún antecedente exista. Busca delimitar, con
un registro reconstruible, qué afirma cada capa de literatura acerca de las
interfaces entre formación de coalición, factibilidad física, ejecución y
tráfico.

### Mapeo del corpus recuperado

- **RQ-M1.** ¿Qué volumen y composición tiene el corpus recuperado por fuente,
  periodo y familia temática?
- **RQ-M2.** ¿Cómo se distribuyen las señales SP1, SP2, SP3 y sus
  intersecciones en el corpus recuperado?
- **RQ-M3.** ¿Qué familias metodológicas, arquitecturas y tipos generales de
  validación están representados?

### Revisión técnica anidada

- **RQ-T1.** ¿Cómo se reclutan miembros y roles de coalición?
- **RQ-T2.** ¿Qué evidencia explícita existe de factibilidad física,
  contacto o `wrench`?
- **RQ-T3.** ¿Dónde reside la autoridad de decisión en cada etapa?
- **RQ-T4.** ¿Qué información no local, supuestos de red y mecanismos de cierre
  exige cada método?
- **RQ-T5.** ¿Qué evidencia hay de transporte de carga compartida, recuperación
  y sustitución?
- **RQ-T6.** ¿Qué componentes se demostraron conjuntamente en una misma cadena
  operativa?

### Auditoría adversarial

- **RQ-A1.** ¿Qué antecedentes amenazan cada componente de la contribución del
  TFM y qué condición concreta satisfacen o no satisfacen?

La respuesta a RQ-A1 se redacta como “no identificado bajo este protocolo”
cuando proceda; nunca como una prueba de inexistencia universal.

## Unidad canónica y versiones

Una línea científica puede contener preprint, conferencia y extensión de
revista. El registro debe mantener `canonical_work_id`, versiones vinculadas,
versión usada como evidencia y una bandera `substantial_extension`. Una nueva
versión se trata como evidencia adicional solo cuando cambia el método,
supuesto, resultado o garantía pertinente. La deduplicación por DOI por sí sola
no basta.

## Fuentes, fecha y estado

Las fuentes abiertas y los rastreos V3 se conservan con su procedencia y
consulta. Web of Science F01/F02 y la cartera arXiv son **parciales** a este
corte. Google Scholar, Scopus e IEEE Xplore no se usan como conteo automático
ni se presentan como exhaustivamente ejecutados. Cualquier exportación posterior
debe entrar mediante una ejecución nueva, con query, filtro, fecha, hash y
motivo de cambio registrados antes de modificar el corpus congelado.

## Validación prospectiva de la búsqueda

`data/gold_set_v4.csv` define un conjunto de anclas obligatorias que cubre MRTA,
coaliciones, transporte, factibilidad física, coordinación local, sustitución y
tráfico. Antes de aceptar una búsqueda nueva se calcula

\[
R_G=\frac{|G\cap S|}{|G|},
\]

donde \(G\) es el gold set y \(S\) el resultado deduplicado. El objetivo
operacional propuesto es \(R_G\geq0.95\); toda pérdida debe explicarse. Este
umbral es una regla de control futura, no un resultado alcanzado por V3.

## Selección y evidencia

El primer pase usa título/resumen y favorece recall: ante duda se conserva el
registro para revisión manual. El segundo pase exige texto completo para una
propiedad técnica. Cada exclusión conserva código y razón. Falta de acceso no
significa exclusión temática y no permite concluir ausencia de capacidad.

La cadena obligatoria es:

\[
\text{trabajo} \rightarrow \text{pasaje localizado} \rightarrow
\text{valor del codebook} \rightarrow \text{síntesis}.
\]

Cada celda técnica incorpora identificador canónico, versión, página/sección,
pasaje o ecuación, variable del codebook, valor, confianza, revisor y fecha.
Una celda sin evidencia admisible se registra como `unclear`, no como `no`.

## Confiabilidad y control de sesgo

La decisión inicial V3 fue de un revisor asistido y no tiene acuerdo
interrevisor. V4 fija para una continuación: doble codificación independiente
de al menos el 20 % aleatorio del núcleo técnico y del 100 % del registro
adversarial; resolución de desacuerdos; y reporte por campo de acuerdo nominal,
porcentaje de acuerdos y, cuando sea interpretable, kappa de Cohen. La
recodificación diferida por la misma persona es una mitigación menor y debe
declararse como tal.

## Síntesis y sensibilidad

El mapeo admite conteos y tendencias del **corpus recuperado**. La revisión
técnica admite comparación por mecanismo, supuesto y fallo; no mezcla métricas
incompatibles en meta-análisis. La bibliometría se considera descriptiva y
secundaria: proximidad documental, coautoría o Louvain no demuestran cobertura
técnica, calidad ni novedad.

El resultado de la auditoría se recalculará para los escenarios de
`data/sensitivity_plan_v4.csv`. Hasta que esos escenarios estén ejecutados,
no se califica la brecha como robusta al protocolo.

## Congelación y reproducción

Una liberación V4 contiene los CSV de entrada, consultas, screenings,
version-lineage, pasajes, codebook, resultados de sensibilidad, red-team y un
manifiesto SHA-256. La herramienta de derivación produce `generated/` y falla
si los denominadores de este corte no coinciden con los invariantes declarados.
Cambiar un número, una celda o una fuente exige una nueva versión de corpus y
una nueva ejecución del generador.
