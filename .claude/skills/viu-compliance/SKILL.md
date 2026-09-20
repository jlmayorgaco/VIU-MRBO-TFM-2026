---
name: viu-compliance
description: Normativa VIU completa del TFM 12MROB y nivel exigible para la máxima nota - formato, tipografía, numeración, extensión, estructura, APA 7, originalidad y Turnitin, calendario de la convocatoria, y la defensa, que pesa el 70 %. Úsala antes de cualquier entrega, predepósito, depósito o defensa, al tocar viu-mrob-thesis.sty, portada, preliminares o geometría, y cuando haya que decidir qué recortar.
---

# Conformidad VIU — 12MROB, edición Octubre 2025–2026

## 1. Cómo se califica

**El documento no es la nota.**

| Peso | Quién | Sobre qué |
|---:|---|---|
| 30 % | Informe del director (Anexo III) | El trabajo y su seguimiento |
| **70 %** | **Tribunal, en la defensa** | Rúbrica sobre la defensa que el estudiante hace del trabajo |

El tribunal valora tres cosas, y en este orden:

1. **Dominio técnico** — comprender decisiones, procedimientos y resultados.
2. **Análisis crítico** — interpretar evidencias, **reconocer limitaciones** y
   justificar alternativas.
3. **Comunicación profesional** — presentar y defender con claridad y precisión.

Un TFM excelente mal defendido saca menos que uno correcto bien defendido. Si
queda poco tiempo, el reparto de esfuerzo se decide con esta tabla, no con el
gusto por seguir escribiendo.

## 2. Calendario (1ª convocatoria)

| Hito | Fecha |
|---|---|
| Tarea 1 — Fundamentación (hasta Metodología) | 29/05/2026 |
| Tarea 2 — **PREDEPÓSITO**, versión definitiva | 17/07/2026 |
| Tarea 3 — **DEPÓSITO** completo + antiplagio | **08/09/2026** |
| **Defensa** | **21–24/09/2026**, 18:00–22:00 CET, videoconferencia pública |

2ª convocatoria: depósito 13/10/2026, defensa 26–30/10/2026.
3ª: depósito 10/11/2026, defensa 23–27/11/2026.

> **Las entregas fuera de plazo no se corrigen ni se evalúan.** Sin excepción.

El depósito incluye, además de la memoria: **Anexo III** (informe del director),
**Anexo IV** (solicitud de defensa firmada), copia del expediente académico y la
prueba antiplagio. Los anexos están en `resources/`.

Requisito para defender: todas las asignaturas superadas salvo un máximo de dos.

## 3. Gate mecánico

```bash
powershell -File thesis/build.ps1
python .claude/skills/viu-compliance/scripts/viu_check.py thesis/build/main.pdf
```

Comprueba sobre el PDF: A4, páginas, Arial incrustada, **sustituciones
silenciosas de fuente**, resumen 200–300 palabras, 3–5 palabras clave, reparto
por capítulo, cuerpo 50–80, anexos ≤ 20 y resultados ≥ 50 % del cuerpo.

Nada se arregla en el PDF: se arregla en la fuente y se recompila.

## 4. Formato — reglas literales de las Instrucciones

| Regla | Valor |
|---|---|
| Página | A4 |
| Tipografía | **Arial 12 pt** |
| Alineación | Justificado |
| Interlineado | **1,5** |
| Márgenes | Superior 2,5 · inferior 2,5 · izquierdo 3 · derecho 3 cm |
| **Encabezado** | **Nombre del estudiante y título abreviado del trabajo** |
| Pie | Numeración consecutiva centrada |
| Portada | Sin numerar |
| Preliminares | Romanos minúsculos: i, ii, iii, iv… |
| Cuerpo | Arábigos desde 1 |
| Cuerpo | **50–80 páginas**, excluidas portada, resúmenes, índices y anexos |
| Anexos | Máximo 20 páginas |
| Entrega | Borradores en Word; **versión definitiva en PDF** |

**No se permite modificar los estilos predefinidos de la plantilla.**

**Portada:** título, autor, tutor(es), fecha en formato *mes y año*
(«septiembre 2026»), nombre del máster y logo VIU.

**Índices, cada uno empezando en página nueva:** Índice de Contenido, Listado de
Figuras, Índice de Tablas, y Símbolos/Acrónimos/Abreviaturas si procede.

**Ecuaciones:** centradas en línea separada, numeradas consecutivamente, número
entre paréntesis cerca del margen derecho, y **citadas en el texto por su
número** («como se muestra en la Ecuación (1)»).

**Figuras y tablas:** nítidas, con numeración, título y **procedencia o fuente**.

**Estilo, y esto lo miran:**
- Ningún párrafo de menos de **tres oraciones completas**.
- Párrafo introductorio al empezar cada capítulo o apartado.
- **Nunca dos encabezados consecutivos sin texto intermedio.**
- Ortografía y gramática impecables: corrector automático **más** revisión
  manual.
- Sin frases superfluas ni repeticiones (`tfm-voice`, `no-ai-slop`).

## 5. Estructura obligatoria

Portada · Resumen (200–300 palabras) + 3–5 palabras clave · Índices ·
Introducción · Objetivos (general y específicos) · Hipótesis de partida ·
Metodología · Marco teórico y estado del arte · Resultados y análisis ·
Conclusiones y recomendaciones · Referencias · Anexos.

Contenidos que se olvidan y las Instrucciones exigen por nombre:

- **Introducción:** contexto, justificación y relevancia, planteamiento del
  problema o brecha, **impacto esperado**, y descripción de la estructura por
  capítulos. Sin repetir el resumen.
- **Resultados:** validación y pruebas, **comparación explícita con objetivos e
  hipótesis** declarando el grado de cumplimiento y explicando las desviaciones,
  análisis crítico, y **limitaciones**.
- **Conclusiones:** en presente, ligadas una a una a los objetivos, contrastando
  las hipótesis.
- **Recomendaciones:** concretas, viables y **multidimensionales** (teórica,
  tecnológica, económica, social, líneas futuras).

**≥ 50 % del cuerpo en Resultados, Análisis y Validación.** Cada tabla, figura o
ecuación debe aportar información cuantificable; nada meramente narrativo.

## 6. Word → PDF

La plantilla es DOCX, la entrega es PDF, y esto se escribe en LaTeX. Dos errores
opuestos:

- **De más:** no se declara igualdad píxel a píxel con una exportación de Word.
- **De menos:** sí se demuestra geometría OOXML trasladada, portada y logo
  **idénticos byte a byte** a `word/media/image1.jpg` e `image2.png`, Arial
  incrustada y A4 verificado.

`resources/Plantilla memoria TFM_ MROB.docx` tiene el mismo SHA-256
(`6b213806a83f7baa…`) que la referencia auditada en `docs/06`. La cadena está
cerrada.

Queda **un paso manual**: abrir DOCX y PDF en el mismo equipo y compararlos. La
automatización de Word no responde y no hay LibreOffice.

## 7. Originalidad y Turnitin

El depósito pasa por Turnitin y lo revisa la Coordinación. Cómo se interpreta,
literalmente:

- **El porcentaje de similitud no equivale por sí mismo a plagio.**
- **El contenido ajeno debe estar correctamente citado.**
- **Los casos de plagio pueden implicar calificación de cero**, y el Reglamento
  contempla la anulación del TFM.

Se analizan coincidencias justificadas, usos inadecuados de fuentes, bloques
extensos procedentes de otras fuentes y la corrección de la referenciación.

La consecuencia práctica es la de siempre: cita en la primera aparición técnica,
entrecomilla lo literal, atribuye la paráfrasis, pon la fuente en el pie de cada
figura ajena. Eso deja el informe limpio por la razón correcta. Ver
`citation-hygiene`.

## 8. La defensa — el 70 %

**15 minutos de exposición**, presentación con la plantilla oficial
`resources/P11_06_F12 Plantilla PPT Defensa_v01.pptx`.

**15–20 diapositivas:** portada 1 · problema, justificación y objetivos 3–4 ·
metodología 2–3 · **resultados y discusión 7–9** · conclusiones y líneas futuras
2–3. Más diapositivas de anexo reservadas para responder al tribunal.

**Reparto del tiempo:**

| Bloque | Minutos |
|---|---:|
| Contexto y problema | 1 |
| Objetivos y alcance | 2 |
| Metodología y solución desarrollada | 3 |
| **Resultados y validación** | **6** |
| Conclusiones y limitaciones | 2 |
| Margen de seguridad | 1 |

**Los diez errores comunes, tal como los enumera la coordinación:**

1. Superar los 15 minutos.
2. Dedicar demasiado tiempo al marco teórico.
3. Leer las diapositivas.
4. Presentar objetivos sin resultados asociados.
5. Mostrar gráficos sin interpretarlos.
6. Confundir resultados y conclusiones.
7. **No reconocer las limitaciones.**
8. Responder algo distinto de lo preguntado.
9. Incorporar datos que no están en el TFM.
10. Usar una presentación distinta de la versión preparada y autorizada.

**El acto, 10 pasos:** acceso a la sala virtual · verificación de identidad ·
presentación del tribunal · apertura formal · exposición (15 min) · preguntas
del tribunal · respuestas · salida temporal para deliberación · comunicación de
la valoración cualitativa cuando proceda · cierre.

## 9. Nivel de máster: qué separa aprobar de un 10

Los tres criterios del tribunal (§1), traducidos a lo que hay que tener hecho:

**Dominio técnico**
- Una contribución nombrable en una frase, situada en una familia concreta del
  estado del arte (`multiagent-lit`).
- Saber por qué cada decisión de diseño es esa y no otra. «Lo probé y funcionó»
  no es dominio técnico.
- Enunciados formales con hipótesis explícitas y usadas (`math-rigor`).

**Análisis crítico**
- Hipótesis falsables, con criterio de refutación escrito antes de medir.
- Baselines que podrían ganar, comparados sobre soporte común.
- **Resultados negativos y casos donde el método pierde: reportados.** Su
  ausencia es la señal más clara de un trabajo débil, y «no reconocer las
  limitaciones» está en la lista oficial de errores de defensa.
- Estadística con n, semillas, intervalos y tamaño de efecto.
- Ninguna afirmación de optimalidad, convergencia, estabilidad, robustez o
  escalabilidad sin definición formal o medida acotada
  (`claims-evidence-guard`, `control-systems`).

**Comunicación profesional**
- Prosa que no gestiona la lectura (`tfm-voice`).
- Figuras legibles impresas y en blanco y negro; pies que describen.
- Cada limitación que el tribunal podría señalar, ya escrita, una vez, en su
  sitio. Si la descubren ellos, cuesta; si la has escrito tú, suma.
- Respuestas preparadas para «¿por qué no aprendizaje por refuerzo?» y «¿qué
  pasa si falla un AMR?».

**Reproducibilidad**, que es lo que convierte un buen trabajo en uno defendible:
semillas y configuraciones versionadas, cadena verificable dato → macro → figura
→ frase, ninguna cifra escrita a mano.

## 10. Las cinco figuras protegidas

`docs/01` §9: `fig:problema`, `fig:robot`, `fig:tf-population-simplex`,
`fig:tf-literature-timeline`, `fig:tf-methodological-map`.

No se eliminan, ni se comentan, ni se meten en `\iffalse`, ni se sustituyen por
una captura. El registro está en `thesis/config/protected-tikz-figures.json` y
la compilación **falla** si alguna deja de estar activa. Una petición posterior
de «recortar» no revoca esta protección.

## 11. Antes del depósito

1. `powershell -File thesis/build.ps1` — exit 0, sin `Overfull`, sin referencias
   indefinidas.
2. `python .claude/skills/viu-compliance/scripts/viu_check.py` — 0 fallos duros.
3. Encabezado: **nombre del estudiante** y título abreviado (§4).
4. Recorrer figuras y tablas: numeración, título y **fuente** en todas.
5. Ecuaciones numeradas y citadas por su número en el texto.
6. `citation-hygiene` sobre la bibliografía completa; APA 7 contra
   `resources/NormasAPA_VIU_7ed.pdf`.
7. Abrir DOCX y PDF en el mismo equipo y compararlos.
8. Rehacer `docs/06_VIU_TEMPLATE_FIDELITY.md` contra el PDF **actual**: la
   auditoría vigente se hizo sobre 65 páginas y el documento tiene 120.
9. Anexo III, Anexo IV, expediente académico.
10. Comprobar si hay que declarar el uso de IA. Si la normativa no lo cubre,
    preguntar al tutor. Declararlo sale más barato que cualquier alternativa.
