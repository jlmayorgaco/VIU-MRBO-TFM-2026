# Stage 2.5 — auditoría independiente de originalidad y modos de fallo de investigación asistida por IA

**Fecha de corte:** 2026-07-14 (America/Bogota)
**Manuscrito canónico:** `docs/doc-05-final-report/main.tex`
**Revisor:** subauditor independiente de Stage 2.5
**Dictamen:** **PASS — 0 bloqueadores**

## 1. Resumen ejecutivo

No se detectó plagio textual, autoplagio textual, cita inventada, resultado experimental inventado, metodología fabricada ni un defecto de implementación convertido narrativamente en hallazgo. Los siete modos de fallo exigidos terminan en **PASS**.

La comprobación de originalidad se hizo en dos capas:

1. una muestra determinista, estratificada por capítulo, de 42/134 párrafos del snapshot inicial (31,34 %); y
2. una adenda de frescura sobre todos los bloques de prosa que cambiaron durante la ronda: 22 párrafos del cuerpo y 10 bloques adicionales de resumen/abstract, anexos, figuras y tabla A0.

Tras reconstruir el cierre final, el cuerpo contiene 146 párrafos. La unión identificable de la muestra inicial y los párrafos corporales modificados cubre **61/146 párrafos actuales (41,78 %)**, con representación de los siete capítulos. Se ejecutaron búsquedas web literales sobre los 42 fragmentos iniciales, los 32 bloques de la primera adenda y ocho redacciones del cierre definitivo: **82 consultas, 0 coincidencias literales pertinentes, 0 `CLOSE_MATCH` y 0 `VERBATIM`**. La búsqueda semántica suplementaria de la muestra inicial encontró los antecedentes esperables del dominio, con redacción distinta y citas presentes.

El escaneo interno final revisó 1.900 archivos de texto del repositorio. Solo encontró: (a) una copia derivada del propio manuscrito en `output/submit_ready`, excluida como artefacto de renderizado; y (b) reutilización deliberada de la discusión SP8 desde el capítulo fuente no incluido hacia la síntesis canónica. No hay duplicados de 20 palabras entre párrafos del cuerpo. La tesis previa del autor identificada en el repositorio de Uniandes se comparó íntegramente contra el cierre definitivo: **0 coincidencias de 12 o 20 palabras** frente a cualquiera de los 146 párrafos actuales.

## 2. Alcance, clausura y frescura

### 2.1 Clausura final reconstruida

Se siguieron recursivamente las instrucciones `\input{}` y `\include{}` desde `main.tex`. El cierre final contiene 28 archivos:

```text
main.tex
sections/frontmatter/00-cover.tex
sections/frontmatter/01-summary.tex
sections/frontmatter/02-abstract.tex
sections/frontmatter/03-contents.tex
sections/frontmatter/04-nomenclature.tex
sections/mainmatter/01-introduction.tex
sections/mainmatter/02-objectives.tex
sections/mainmatter/03-hypothesis.tex
sections/mainmatter/04-methodology.tex
figures/fig-metodologia-investigacion.tex
sections/mainmatter/05-theoretical-framework/index.tex
figures/fig-sota-transporte-cooperativo.tex
figures/fig-equilibrio-nash-smith.tex
figures/fig-campo-obstaculos.tex
sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex
figures/fig-gap-literatura.tex
sections/mainmatter/06-results-and-analysis/index.tex
sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex
sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex
sections/mainmatter/06-results-and-analysis/sp4-motion.tex
figures/fig-sp4-docking-game-architecture.tex
sections/mainmatter/07-conclusions.tex
sections/anexo-b-reproducibilidad.tex
sections/anexo-c-validacion.tex
sections/a0-full-precision-contrasts.tex
sections/anexo-d-declaracion-ia.tex
sections/anexo-e-declaraciones.tex
```

La huella final adopta la misma convención que el audit empírico. Para cada archivo de la clausura se calcula su SHA-256 y se forma una línea exactamente igual a `"<64hex> <ruta-relativa-al-workspace>"`, con hex en minúsculas y `/` como separador. Las rutas absolutas se ordenan con la semántica de `Sort-Object`; las 28 líneas se unen con un único LF y sin LF final. El payload UTF-8 sin BOM mide 3.716 bytes y su SHA-256 es la huella compuesta.

| Corte | Archivos | Convención | SHA-256 compuesto | Observación |
|---|---:|---|---|---|
| Snapshot inicial | 27 | `LP-v1` | `0b99600d232bc6db37832783d52a63875be19036aef8dd8d4082315c4d53e5fd` | Base de la selección determinista |
| Corte empírico intermedio | 28 | `FH-v2` | `01161a9afdadc100f187f398f179910ae1a828909165f8f87f188b47ecf7a061` | Válido a las 13:02 UTC; quedó obsoleto por ajustes posteriores |
| Snapshot final congelado | 28 | `FH-v2` | `2fe96009eb6dbf047bc56e86c957410c1057a68da90ee7cedc3b03cc014abee6` | Recalculado sobre el cierre definitivo; `main.tex` conserva `fd05b3c5…fa21` |

La huella `6da9e7d8…` citada en una versión anterior de este informe usaba `LP-v1`: rutas relativas al directorio del documento y bytes con prefijos de longitud. La diferencia frente a `01161a9a…` era de algoritmo, no una colisión ni una lectura distinta del archivo principal. Después se ajustaron varias redacciones de “certificado/comprobación” y se dividieron algunas oraciones; por ello, **ambas huellas intermedias quedaron además obsoletas por contenido**. Este informe queda ligado únicamente a `FH-v2 = 2fe96009…`.

El `HEAD` que sirvió de base al último ajuste fue `4b46455a3c58cd0d82bedbffea44eff336525fdf`. La huella compuesta, no el identificador Git, es la autoridad de frescura de este informe.

### 2.2 Definición de párrafo y denominador final

Para el muestreo se eliminaron comentarios, matemáticas en línea/bloque, comandos de estructura y los entornos de figura, tabla, ecuación, alineación y algoritmo. Se retuvieron bloques separados por línea en blanco con al menos 25 palabras alfabéticas y puntuación oracional.

| Capítulo | Párrafos finales | Párrafos actuales auditados | Cobertura mínima |
|---|---:|---:|---:|
| 1. Introducción | 10 | 5 | 50,00 % |
| 2. Objetivos | 3 | 1 | 33,33 % |
| 3. Hipótesis | 3 | 1 | 33,33 % |
| 4. Metodología | 17 | 8 | 47,06 % |
| 5. Marco teórico | 43 | 16 | 37,21 % |
| 6. Resultados y análisis | 58 | 23 | 39,66 % |
| 7. Conclusiones | 12 | 7 | 58,33 % |
| **Total** | **146** | **61** | **41,78 %** |

### 2.3 Selección determinista inicial

Semilla:

```text
stage2.5-originality-2026-07-14|0b99600d232bc6db37832783d52a63875be19036aef8dd8d4082315c4d53e5fd
```

Para cada capítulo se ordenaron sus párrafos por `SHA256(semilla || ruta || ordinal_del_bloque)` y se tomaron `ceil(0,30*n)`. El resultado inicial fue 3/10, 1/3, 1/3, 5/16, 13/41, 15/49 y 4/12: **42/134 = 31,34 %**.

## 3. Auditoría web de fragmentos

### 3.1 Escala de clasificación

- `O`: `ORIGINAL`, sin redacción fuente cercana localizada.
- `D`: síntesis/paráfrasis de conocimiento del dominio con fuente pertinente o cita en el texto; la idea no es original, pero la redacción sí se distingue.
- `C`: conocimiento común.
- `CM`: `CLOSE_MATCH`.
- `V`: `VERBATIM`.

En todas las consultas de las tablas siguientes, “0 pertinente” significa que el buscador pudo devolver ruido no relacionado, pero ninguna página revisada contenía el fragmento o una coincidencia textual relevante.

### 3.2 Muestra inicial: 42 fragmentos

| ID | Ubicación | Fragmento exacto consultado | Web literal | Clase |
|---|---|---|---|---|
| P002 | Introducción | “Esa regularidad deja de estar disponible cuando una instalación debe mover” | 0 pertinente | D |
| P003 | Introducción | “Los robots seleccionados necesitan cubrir la demanda, ocupar contactos compatibles” | 0 pertinente | O |
| P009 | Introducción | “aíslan reclutamiento homogéneo, capacidad heterogénea, contactos y wrench, movimiento” | 0 pertinente | O |
| P012 | Objetivos | “La memoria distingue resultados evaluados en campañas, pruebas de consistencia” | 0 pertinente | O |
| P016 | Hipótesis | “La metodología conserva esta jerarquía para evitar que una campaña exploratoria” | 0 pertinente | O |
| P020 | Metodología | “Las semillas confirmatorias permanecen selladas hasta el freeze del protocolo” | 0 pertinente | O |
| P022 | Metodología | “Un horizonte agotado puede coexistir con un cierre válido” | 0 pertinente | O |
| P024 | Metodología | “Un contraste es no estimable si carece de bloques completos” | 0 pertinente | O |
| P028 | Metodología | “La tercera identifica la aceptación que se vuelve inválida al ejecutar” | 0 pertinente | O |
| P031 | Metodología | “CoppeliaSim se usa, cuando corresponde, como inspección cualitativa separada” | 0 pertinente | O |
| P037 | Marco teórico | “aparecen dependencias temporales, capacidades heterogéneas y restricciones de coordinación” | 0 pertinente | D |
| P040 | Marco teórico | “el potencial no representa bienestar abstracto; representa reducción de déficit” | 0 pertinente | O |
| P041 | Marco teórico | “CBBA ofrece una familia descentralizada de subastas con consenso para asignación” | 0 pertinente | D |
| P042 | Marco teórico | “suficientes robots en número, pero mal ubicados, sin torque disponible” | 0 pertinente | O |
| P047 | Marco teórico | “Smith genera presión distribuida; QR/quórum transforma preferencias en coaliciones ejecutables” | 0 pertinente | O |
| P049 | Marco teórico | “las funciones de barrera de control permiten imponer desigualdades de seguridad” | 0 pertinente | D |
| P050 | Marco teórico | “El control reactivo aproxima la dirección deseada, pero el TFM” | 0 pertinente | D |
| P058 | Marco teórico | “Amazon Robotics describe sistemas que transportan inventario hacia zonas de almacenamiento” | 0 pertinente | D |
| P059 | Marco teórico | “KUKA ofrece las plataformas KMP 1500P y KMP 3000P para” | 0 pertinente | D |
| P061 | Marco teórico | “La literatura revisada muestra un desplazamiento desde asignaciones abstractas hacia tareas” | 0 pertinente | O |
| P070 | Marco teórico integrado | “La campaña SP5 v2 verificó en las 864 ejecuciones” | 0 pertinente | O |
| P071 | Marco teórico integrado | “V2 la contrastó por diferencias finitas en 600 estados” | 0 pertinente | O |
| P073 | Marco teórico integrado | “El desarrollo completo de potenciales, PoA, precios y variantes de juego” | 0 pertinente | O |
| P075 | Resultados | “Las referencias centralizadas actúan como cotas internas de la campaña” | 0 pertinente | O |
| P076 | Resultados | “La asignación físicamente factible puede fallar durante el movimiento” | 0 pertinente | O |
| P077 | Resultados | “uniforme+closure supera a las nueve variantes de juego” | 0 pertinente | O |
| P080 | Resultados | “una asignación que cubre cardinalidad o capacidad escalar puede seguir” | 0 pertinente | O |
| P082 | Resultados | “la auditoría por capas de coaliciones físicamente ejecutables” | 0 pertinente | O |
| P084 | A0--FULL | “La extensión 40--60--100 dependió solo de que la anchura máxima” | 0 pertinente | O |
| P087 | A0--FULL | “Dos contactos complementarios generaron un momento que no se deduce” | 0 pertinente | O |
| P090 | Síntesis modular | “SP1--SP8 explican por qué falla cada abstracción cuando se estudia” | 0 pertinente | O |
| P095 | Síntesis modular | “En 480 mundos, los fitness marginales redujeron el regret” | 0 pertinente | O |
| P098 | Síntesis modular | “La campaña v1.1 reunió 600 mundos y 7.200 ejecuciones” | 0 pertinente | O |
| P100 | Síntesis modular | “108 mundos emparejados y 864 ejecuciones exclusivamente CPU” | 0 pertinente | O |
| P102 | Síntesis modular | “separar seguridad comandada y mecánica ejecutada” | 0 pertinente | O |
| P104 | Síntesis modular | “una coalición estáticamente válida todavía puede fallar por trayectoria” | 0 pertinente | O |
| P119 | SP4 | “la secuencia de primitivas importan más que resolver con precisión” | 0 pertinente | O |
| P120 | SP4 | “Son medidas del simulador, no cotas asintóticas ni latencia de red real” | 0 pertinente | O |
| P124 | Conclusiones | “la validez física no es monótona por añadir una prueba” | 0 pertinente | O |
| P126 | Conclusiones | “una solución común de Lyapunov proporciona ISS práctica para cualquier” | 0 pertinente | D |
| P131 | Conclusiones | “la campaña mesoscópica no midió de forma externa timeouts ni memoria residente” | 0 pertinente | O |
| P132 | Conclusiones | “El waypoint del caso de obstáculo es nominal; la seguridad se decide” | 0 pertinente | O |

**Balance inicial:** 34 `O`, 8 `D`, 0 `C`, 0 `CM`, 0 `V`.

Las búsquedas semánticas sin comillas para los 42 fragmentos localizaron los antecedentes normales del campo, entre ellos la taxonomía MRTA, CBBA, CBF, aplicaciones logísticas y Lyapunov/ISS. Ejemplos de fuentes primarias o institucionales revisadas:

- [Gerkey y Matarić, taxonomía MRTA](https://doi.org/10.1177/0278364904045564)
- [Choi et al., CBBA](https://doi.org/10.1109/TRO.2009.2022423)
- [Ames et al., CBF-QP](https://arxiv.org/abs/1609.06408)
- [Amazon Robotics, sistemas de fulfillment](https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center)
- [KUKA, KMP 1500P](https://www.kuka.com/en-us/products/amr-autonomous-mobile-robotics/mobile-platforms/kmp-1500p-diffdrive)
- [Tuci et al., transporte colectivo](https://doi.org/10.3389/frobt.2018.00059)

Esas fuentes apoyan ideas de dominio; ninguna reprodujo la redacción muestreada.

### 3.3 Adenda de frescura: 32 bloques modificados

Se identificaron 32 bloques sustantivos dentro de la clausura que habían cambiado durante la ronda: 22 del cuerpo, cuatro de resumen/abstract, dos de anexos, dos de figuras y dos del nuevo archivo de contrastes A0. Los cambios exclusivamente de tabla o índice sin prosa no se contabilizaron como párrafo, pero la tabla A0 quedó representada por sus dos textos explicativos.

| ID | Zona | Fragmento actual consultado | Web literal | Clase |
|---|---|---|---|---|
| F01 | Figura obstáculos | “La atracción a la carga solo es aceptable si respeta despejes mínimos” | 0 pertinente | O |
| F02 | Figura Nash/Smith | “las desviaciones locales dejan de mejorar utilidad una vez incorporados déficit” | 0 pertinente | O |
| F03 | Anexo B | “el manifiesto registró frozen ready for execution y semillas cerradas” | 0 pertinente | O |
| F04 | Anexo E | “SP6 SP8 conservan alcance modular o descriptivo y no satisfacen íntegramente” | 0 pertinente | O |
| F05 | Resumen | “Sus escalones añaden una utilidad calculada por robot y umbralizada globalmente” | 0 pertinente | O |
| F06 | Resumen | “conservó un 14 % de fallos en el régimen más adverso” | 0 pertinente | O |
| F07 | Abstract | “Its stages add a per-robot utility with a global selection threshold” | 0 pertinente | O |
| F08 | Abstract | “Its selector uses global candidates this is a recovery proxy” | 0 pertinente | O |
| F09 | Introducción | “Esa regularidad deja de estar disponible cuando una instalación debe mover” | 0 pertinente | D |
| F10 | Introducción | “los cierres enteros y las guardias canónicas todavía usan información global” | 0 pertinente | O |
| F11 | Introducción | “Entre ambos bloques queda una brecha operacional MRTA decide quién participa” | 0 pertinente | D |
| F12 | Introducción | “No se reivindican como novedades la dinámica de Smith las dinámicas poblacionales” | 0 pertinente | O |
| F13 | Hipótesis | “Los contrastes de calidad H8.2 H8.3 se conservan únicamente como análisis exploratorios” | 0 pertinente | O |
| F14 | Metodología | “En las campañas confirmatorias con freeze las semillas confirmatorias permanecen selladas” | 0 pertinente | O |
| F15 | Metodología | “La implementación integrada es un instrumento diagnóstico centralizado que evalúa componentes distribuibles” | 0 pertinente | O |
| F16 | Metodología | “Los timeouts permanecen como resultados censurados y nunca se convierten en éxitos” | 0 pertinente | O |
| F17 | Marco teórico | “V2 contrasta la identidad de potencia Hamiltoniana por diferencias finitas” | 0 pertinente | O |
| F18 | Marco teórico | “Smith-QR es una instancia evaluada pero su cierre canónico usa preferencias globales” | 0 pertinente | O |
| F19 | Matriz de originalidad | “La Tabla matriz-originalidad separa herencia y aporte” | 0 pertinente | D |
| F20 | Síntesis SP8 | “Las afirmaciones de escalado de recursos basadas en timeout declarado y memoria analítica” | 0 pertinente | O |
| F21 | A0--FULL | “complementariedad de contactos mediante búsqueda global acotada” | 0 pertinente | O |
| F22 | A0--FULL | “El tope no garantizaba de antemano alcanzar el objetivo en el resultado observado” | 0 pertinente | O |
| F23 | A0--FULL | “la seguridad se decide por el despeje no por la mera salida del filtro” | 0 pertinente | O |
| F24 | A0--FULL | “La validez de estas tasas está condicionada a una calibración puntual” | 0 pertinente | O |
| F25 | A0--FULL | “cerrar una restricción puede degradar otra al retirar margen físico” | 0 pertinente | O |
| F26 | SP4 | “Los cinco contrastes congelados sobrevivieron Holm” | 0 pertinente | O |
| F27 | SP4 | “La equivalencia QP KKT se limita a instantáneas convexas” | 0 pertinente | O |
| F28 | Conclusiones | “componentes distribuidos y cierres globales auditados para formar coaliciones multi-AMR” | 0 pertinente | O |
| F29 | Conclusiones | “A0 usa un umbral global A1 A4 ejecutan ranking capacidad búsqueda de contactos” | 0 pertinente | O |
| F30 | Conclusiones | “Aunque el tope no lo garantizaba las veinte anchuras finales observadas” | 0 pertinente | O |
| F31 | Tabla A0 | “La tabla siguiente se deriva sin selección de statistics paired contrasts holm” | 0 pertinente | O |
| F32 | Tabla A0 | “Nulo inconcl agrupa ausencia de discordancias o un contraste cuyo intervalo” | 0 pertinente | O |

**Balance de frescura:** 29 `O`, 3 `D`, 0 `CM`, 0 `V`. Los cambios puramente numéricos de SP4 también se conservaron en el alcance; la originalidad textual del párrafo no cambió y los valores se verificaron por separado contra el CSV canónico.

### 3.4 Segunda adenda de frescura: cierre definitivo

Después de la primera adenda se fusionó la tabla A0, se aplicó maquetación local al anexo y se armonizó la terminología “certificado/comprobación”. La fusión y la maquetación no cambiaron texto ni valores. Sí se revalidaron ocho fragmentos cuya redacción o puntuación cambió; dos de ellos son párrafos corporales que no pertenecían a la unión previa, por lo que la cobertura actual sube de 59 a 61 párrafos.

| ID | Zona | Fragmento actual consultado | Web literal | Clase |
|---|---|---|---|---|
| R01 | Anexo B | “La evidencia se organiza en tres niveles El primer nivel corresponde a métricas tabulares como” | 0 pertinente | O |
| R02 | Anexo B | “SP4 usa SP4_DOCKING_GAME_CONFIRMATORY_v3 que comprende 108 mundos” | 0 pertinente | O |
| R03 | Metodología | “SAFE es la orden después del filtro de barrera EXEC es el wrench” | 0 pertinente | O |
| R04 | Síntesis SP5 | “El CBF local alcanzó 0,593 de éxito seguro sin colisiones El proxy VO” | 0 pertinente | O |
| R05 | A0--FULL | “Nominal se detuvo en 60 mundos Las otras familias alcanzaron el tope preespecificado” | 0 pertinente | O |
| R06 | Introducción | “la semántica que separa preferencia cierre comprobación física y ejecución” | 0 pertinente | O |
| R07 | Matriz de originalidad | “definición válida en simulación planar sin validación de hardware” | 0 pertinente | O |
| R08 | Presupuesto de centralización | “Comprobación global de capacidad no mercado local cerrado” | 0 pertinente | O |

**Balance de la segunda adenda:** 8 `O`, 0 `D`, 0 `CM`, 0 `V`. El escaneo interno completo y la comparación con la tesis previa se repitieron después de estas redacciones y conservaron sus resultados negativos.

## 4. Reutilización interna y autoplagio

### 4.1 Reutilización dentro del repositorio

Procedimiento:

- normalización a minúsculas, sin diacríticos;
- ventanas exactas de 12 y 20 palabras;
- 1.900 archivos `.tex`, `.md`, `.rst`, `.txt`, `.yaml`, `.yml`, `.json`, `.py`, `.toml`, `.ini`, `.cfg` y `.csv` de hasta 2 MB;
- exclusión de `.git`, `.aris`, `tmp`, `build`, cachés y los 28 archivos de la clausura actual.

Resultados:

| Hallazgo | 20 palabras | 12 palabras | Clasificación |
|---|---:|---:|---|
| Cuerpo vs `output/submit_ready/tfm_round_1/*` | 1 párrafo | 1 párrafo | Derivado del propio documento; excluido |
| Síntesis canónica SP8 vs `sp8-scalability.tex` no incluido | 12 ventanas | 24 ventanas | Reutilización interna del capítulo fuente hacia la síntesis; no es publicación previa |
| Duplicados entre párrafos incluidos del cuerpo | 0 pares | no aplicable | Sin duplicación extensa interna |

La segunda coincidencia corresponde al párrafo que suspende las afirmaciones de recursos de SP8 y clasifica H8.2--H8.3 como exploratorias. El archivo fuente no forma parte de `main.tex`; la síntesis canónica incorpora su conclusión auditada. No se presenta como texto de otro autor ni como resultado independiente adicional.

### 4.2 Trabajo previo del autor

El autor declarado es Jorge Luis Mayorga Taborda. La búsqueda por autor/título localizó como trabajo previo directamente relacionado:

- [*Dinámicas Poblacionales Distribuidas Aplicadas al Control de Tráfico Urbano* (Universidad de los Andes, 2014)](https://repositorio.uniandes.edu.co/server/api/core/bitstreams/f2d97b2c-2dab-4a00-be25-798636ee21c6/content).

El PDF completo (56 páginas; 17.437 tokens extraídos) se comparó con los 146 párrafos del cuerpo final:

| Ventana | Párrafos actuales con coincidencia |
|---|---:|
| 20 palabras | 0 |
| 12 palabras | 0 |

También apareció el artículo [*Development of real-time control emulator in FPGA using HiLeS methodology*](https://doi.org/10.1109/IECON.2015.7392735), cuyo tema no coincide con el TFM y fue descartado tras la criba de título/resumen.

**Dictamen de autoplagio:** no hay señal textual. La continuidad intelectual en dinámicas poblacionales existe como línea temática, pero no se encontró copia de prosa ni un resultado previo reetiquetado. Si la normativa VIU exige declarar cualquier antecedente académico propio aunque no haya reutilización textual, puede añadirse como transparencia institucional; no es un defecto de integridad detectado.

### 4.3 Límite de la comprobación

Esta es una búsqueda reproducible por web abierta y por corpus local, no un sustituto de Turnitin/iThenticate ni de bases cerradas. Un “PASS” significa que no se encontró señal con las fuentes accesibles, los fragmentos y los umbrales declarados; no afirma imposibilidad matemática de coincidencia en un corpus privado.

## 5. Indicadores estilísticos asociados a IA

Esta sección es informativa y no intenta inferir autoría a partir del estilo.

| Indicador | Resultado | Lectura |
|---|---|---|
| Transiciones formulaicas | Leve | Enumeraciones “primero/segundo/tercero” ligadas a capas del método |
| Estructura oracional repetitiva | No significativa | La muestra alterna definición, evidencia, límite e interpretación |
| Generalidades sin anclaje | No | Predominan nombres de campañas, tamaños, intervalos y supuestos |
| Léxico impropio o artificial | No | Terminología consistente con MRTA, juegos, wrench, CBF e ISS |
| Paralelismo excesivo | Leve | Tablas/matrices usan paralelismo deliberado para comparabilidad |
| Citas decorativas o desconectadas | No | El audit de contexto terminó en PASS |

Hay dos señales leves explicables por la arquitectura académica del texto. No constituyen evidencia de generación automática ni afectan el dictamen.

## 6. Auditoría de los siete modos de fallo

| Modo | Estado | Evidencia principal |
|---|---|---|
| 1. Defecto de implementación | **PASS** | 37 pruebas focalizadas; auditorías canónicas; separación explícita de campañas fallidas/no canónicas |
| 2. Alucinación de citas | **PASS** | 107/107 entradas existentes; revalidación poscorrección y contextos PASS |
| 3. Resultado experimental alucinado | **PASS** | 146/146 unidades del audit empírico clasificadas; 142 verificadas localmente y 4 externas cerradas por citas |
| 4. Dependencia de atajo | **PASS** | Baselines fuertes, RAW/CLOSED, RAW/SAFE/EXEC, mundos adversos y resultados negativos |
| 5. Bug reformulado como insight | **PASS** | SP5 v1 no canónico revelado; efecto negativo A3 preespecificado y conservado |
| 6. Metodología fabricada | **PASS** | Configuraciones, semillas, hashes, freeze, scripts, tablas y manifiestos trazables |
| 7. Bloqueo de marco | **PASS** | Pregunta condicional, presupuesto de centralización, matriz de originalidad y límites explícitos |

### 6.1 Modo 1 — defecto de implementación

Evidencia independiente:

- `python -m pytest -q --disable-warnings tests/test_physical_coalition.py tests/test_sp4_docking_game.py tests/test_sp5_payload_transport.py tests/test_sp6_pipeline.py tests/test_wrench_market_games_integration.py`
- resultado: **37 passed in 45.11 s**.

Dos intentos del conjunto completo no finalizaron dentro de 120 s y 300 s, respectivamente; no produjeron fallo ni salida utilizable y se registran como **inconclusos**, no como PASS. La decisión no depende de ocultarlos: las pruebas focalizadas cubren las rutas críticas de A0/SP4/SP5/SP6 y el audit empírico independiente verificó las salidas canónicas.

Controles adicionales:

- `results/README.md` y los `STATUS.md` separan campañas smoke/debug o v1 fallidas de las canónicas.
- SP5 conserva las 20.040 filas históricas como **no canónicas** por reparación/proyección posterior a la integración; v2 elimina esa operación y pasa la auditoría.
- SP1--SP3 conservan explícitamente sus versiones fallidas y las campañas corregidas, sin mezclar denominadores.
- A0--FULL contiene 2.160 identificadores únicos, cero errores numéricos y gates canónicos en verde.

No apareció un error activo que invalide los resultados presentados.

### 6.2 Modo 2 — alucinación de citas

La auditoría fresca se dividió en tres lotes independientes:

| Lote | Entradas | Existencia | Contextos iniciales |
|---|---:|---:|---:|
| A | 36 | 36 YES | 21 SUPPORTS, 2 WEAK, 0 WRONG |
| B | 36 | 36 YES | 24 SUPPORTS, 0 WEAK, 0 WRONG |
| C | 35 | 35 YES | 30 SUPPORTS, 0 WEAK, 0 WRONG |
| **Total** | **107** | **107 YES** | **75 SUPPORTS, 2 WEAK, 0 WRONG** |

Los ajustes de metadatos y los dos usos débiles de la introducción se corrigieron. La revalidación posterior comprobó 13/13 correcciones bibliográficas, los dos contextos y la matriz de originalidad. El cierre ampliado termina en **PASS**, sin DOI, título, autor, venue o fuente inventados.

Trazas: `batch_a.md`, `batch_b.md`, `batch_c.md` y `postfix_recheck.md` en `.aris/traces/citation-audit/2026-07-14_stage2_5_fresh/`.

### 6.3 Modo 3 — resultado experimental alucinado

El informe hermano `empirical_claim_audit.md` clasificó el 100 % de 146 unidades de afirmación:

- 142 afirmaciones contrastables con artefactos locales: **142 VERIFIED**;
- cuatro hechos externos de mercado/producto: `UNVERIFIABLE_LOCAL`, pero verificados por la auditoría de citas;
- cero `MISMATCH` y cero afirmaciones internas sin artefacto.

Comprobaciones representativas:

- A0--FULL: 960 ejecuciones base, 2.160 finales, 20 contrastes completos, cero errores numéricos.
- V1: error L2 máximo `2,8477e-14`; V2: 600 estados y error de identidad `1,35817e-8`; HOCBF vs QP `6,9084e-14`; V3: `lambda_min=0,277956`, residual `9,042e-16`.
- SP4: 108 mundos, 1.188 ejecuciones; los tres IC corregidos coinciden con el CSV.
- SP5: 108 mundos, 864 ejecuciones; residual mecánico máximo `1,139e-13`; cero reparaciones de pose.
- SP6: 20.000 ejecuciones; el efecto de pérdida de carga es `-0,0227`, mientras completitud frente a Smith queda inconcluyente.

La prosa conserva efectos favorables, nulos, negativos y no estimables. No hay selección narrativa exclusiva de resultados positivos.

### 6.4 Modo 4 — dependencia de atajo

La contribución central no es un modelo de aprendizaje que pueda resolver la tarea mediante una correlación espuria. Aun así, se buscaron atajos de evaluación:

- comparadores uniforme, voraz, húngaro, subasta/CBBA, APF/VO, QP/PD central y variantes de juego;
- separaciones `RAW/CLOSED` y `RAW/SAFE/EXEC`;
- familias emparejadas nominal, escasez, torque y obstáculo/red;
- controles uniformes que en SP2 y SP3 superan o igualan variantes de juego;
- A3 mejora torque pero empeora escasez; FULL mantiene fallos en el régimen adverso.

Los resultados dependen del simulador planar y de su calibración, límite que el texto declara. Dentro de ese dominio no se detecta un atajo que sustituya la capacidad, contacto, wrench, dinámica o seguridad que se afirma medir.

### 6.5 Modo 5 — bug reformulado como insight

Se buscaron expresiones de sorpresa retrospectiva y cambios de hipótesis posteriores. No aparece una narrativa “el bug era en realidad la contribución”. Dos casos merecían atención:

1. **SP5 histórico:** la proyección posterior a integrar podía reparar la pose. El trabajo no la reinterpreta como estabilización novedosa; marca la campaña de 20.040 filas como no canónica y ejecuta v2 sin reparación.
2. **A3 en escasez:** el efecto `-0,18` estaba cubierto por la hipótesis congelada sobre autoridad/capacidad dinámica. Se conserva como resultado negativo y se explica por pérdida de reserva de tracción. La explicación está apoyada por los artefactos y no transforma un error de código en descubrimiento.

La bandera heredada `frozen_before_confirmatory_seed_opening: false` tampoco se usa como hallazgo. Se revela como defecto de metadato inmutable y se resuelve con la cadena hashada de tiempo.

### 6.6 Modo 6 — metodología fabricada

Los elementos metodológicos principales tienen correspondencia en artefactos:

- SP1: semillas 330000--330899 y 900 mundos en el manifiesto.
- A0--FULL: 40 mundos base por familia, regla 40--60--100, objetivo de anchura 0,20, 4.000 bootstraps, cuatro workers y 20 contrastes.
- SP4/SP5/SP6: tamaños, semillas, configuraciones, tablas de corridas, auditorías teóricas e informes.
- Entorno A0: Python 3.13.9, NumPy 2.3.5, CPU lógica 22 y un hilo OMP.

La cronología A0 es verificable:

- `frozen_manifest.json`: `frozen_ready_for_execution`, semillas cerradas, `2026-07-12T19:04:06Z`;
- `seed_opening.json`: `after_freeze: true`, mismo SHA-256, `2026-07-12T19:04:21Z`.

La bandera contradictoria del YAML está documentada en `INTEGRITY_ADDENDUM_2026-07-14.md` y en el Anexo B sin reescribir el archivo congelado. Es un defecto menor de metadato, no una fabricación de la secuencia experimental.

### 6.7 Modo 7 — bloqueo de marco

El manuscrito no fija como única pregunta “qué dinámica de juego gana”. La pregunta se formula en términos de condiciones e interfaces para pasar de preferencia a ejecución física. La ronda refuerza esta apertura mediante:

- presupuesto de centralización por etapa;
- matriz de originalidad que separa herencia y aporte;
- reconocimiento de que los cierres canónicos y el selector FULL usan información global;
- controles uniformes que impiden atribuir automáticamente la mejora al juego;
- suspensión de H7.3/H8.1 y tratamiento exploratorio de H8.2--H8.3;
- declaración de que CoppeliaSim, cuando aparece, es inspección cualitativa separada y no validación física de A0--FULL/SP1--SP8;
- límites sobre planta planar, agarre rígido, calibración, red sintética, sensibilidad y hardware.

Los resultados negativos provocan una interpretación más precisa de las interfaces, no una reducción oportunista del problema para proteger la tesis.

## 7. Hallazgos no bloqueantes y límites residuales

1. **Suite completa inconclusa:** dos ejecuciones de `pytest` excedieron 120 s y 300 s. Las 37 pruebas focalizadas y los audits de artefactos sí pasan. No debe citarse este subaudit como prueba de que toda la suite terminó.
2. **Bandera A0 heredada:** queda en `false` dentro del YAML congelado; el addendum y los timestamps hashados resuelven la cronología. Conviene conservar ambos en el paquete de entrega.
3. **Reutilización SP8 interna:** un párrafo de la síntesis replica el capítulo fuente no incluido. Es legítimo dentro del mismo proyecto, pero no debe contarse dos veces como evidencia independiente.
4. **Cobertura de originalidad:** la búsqueda web abierta no reemplaza una base comercial cerrada.
5. **Trabajo previo del autor:** no hay copia textual. Una declaración voluntaria de continuidad temática puede mejorar transparencia si la norma institucional la pide.

## 8. Dictamen final

### Originalidad

**PASS.** No se encontró `CLOSE_MATCH`, `VERBATIM`, copia interna presentada como evidencia nueva ni autoplagio textual del trabajo previo localizado. Las paráfrasis identificadas corresponden a conocimiento del dominio, están redactadas de forma distinta y disponen de citas o atribución institucional.

### Modos de fallo de investigación asistida por IA

**7/7 PASS.** No hay estado `SUSPECTED`. No hay evidencia insuficiente en los modos críticos 1, 3, 5 o 6. Las limitaciones de herramienta y runtime están declaradas y no cambian el resultado.

### Decisión de Stage 2.5 para este subalcance

**PASS — sin bloqueadores para continuar la canalización académica.** Este dictamen queda ligado a la huella de clausura `2fe96009eb6dbf047bc56e86c957410c1057a68da90ee7cedc3b03cc014abee6` calculada con la convención `FH-v2` descrita arriba. Cualquier cambio posterior de prosa, bibliografía, tablas de resultados o artefactos canónicos exige revalidar la parte afectada y emitir una nueva huella.
