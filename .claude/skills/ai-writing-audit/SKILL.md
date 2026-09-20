---
name: ai-writing-audit
description: Auditoría adversarial a escala de documento para detectar patrones de escritura de IA (estilo "Turnitin/AI-detector"), en español y en inglés académico. Úsala cuando el usuario pida "revisar si suena a IA", "pasar un detector de IA", "auditoría Turnitin", o antes de depositar cualquier memoria/artículo redactado o corregido con asistencia de IA. Complementa a `no-ai-slop` (léxico, un archivo) y `tfm-voice` (voz de este TFM): esta habilidad es la capa estructural, a escala de documento completo, con metodología de reparto en paralelo.
---

# Auditoría de escritura de IA, a escala de documento

No existe un plugin de Claude Code equivalente a Turnitin: es un servicio
propietario de terceros, no una habilidad instalable. Lo que sí es replicable
sin depender de él es su función — encontrar texto que lee como generado o
retocado mecánicamente — con una lectura adversarial sistemática. Esta
habilidad es esa réplica: no pasa un detector externo, hace el trabajo que un
detector prometería hacer, y lo hace mejor porque entiende el contenido.

**No se trata de esquivar un detector.** Los detectores de IA son poco
fiables en ambas direcciones (falsos positivos sobre prosa humana muy pulida,
falsos negativos sobre LLM-slop bien parafraseado). El objetivo es que el
texto diga algo con la menor cantidad de palabras que lo permitan, y que cada
frase la firmaría el autor en una defensa oral. Ver la filosofía completa en
`no-ai-slop`.

## 1. Relación con las otras habilidades

| Habilidad | Nivel | Cuándo |
|---|---|---|
| `no-ai-slop` | Léxico, un archivo, con linter ejecutable (`slop_lint.py`) | Antes de dar por bueno cualquier párrafo nuevo o reescrito |
| `tfm-voice` | Voz calibrada de este TFM, con sustituciones canónicas | Siempre que se escriba o reescriba prosa del TFM |
| **`ai-writing-audit`** (esta) | **Estructural, documento completo**: plantillas repetidas entre archivos, ritmo de párrafo, densidad de puntuación, meta-comentario acumulado por varias rondas de edición | Antes de depositar, o cuando el usuario pida explícitamente una auditoría tipo Turnitin/AI-detector |

Ejecuta primero el linter mecánico de `no-ai-slop` sobre cada archivo tocado
(`python ~/.claude/skills/no-ai-slop/scripts/slop_lint.py ARCHIVO.tex`): es
gratis y atrapa la mitad del trabajo. Esta habilidad cubre lo que un linter
por expresiones regulares no puede ver porque exige leer el documento
completo y comparar entre secciones.

## 2. Qué busca esta auditoría (categorías, ES/EN)

1. **Meta-comentario o auto-referencia al propio documento**, en vez de hablar
   del contenido — "esta memoria no verifica si...", "el enunciado se
   restringe a...", "cabe destacar que este anexo conserva..." · EN: "this
   paper does not claim...", "it is worth noting that this document...".
2. **Tríos/listas de tres forzadas** con estructura gramatical y longitud
   casi idéntica, sobre todo si se repiten como muletilla en varios sitios.
3. **Hedging apilado**: dos o más calificadores de incertidumbre encadenados
   sin necesidad ("podría llegar a sugerir que posiblemente...").
4. **Plantillas de frase repetidas mecánicamente** 3+ veces en el documento
   con solo los sustantivos cambiados (p. ej. "Las cifras... se conservan en
   el Anexo X", "Este anexo conserva, sin abreviar..."). Es el hallazgo más
   común y el más fácil de arreglar: variar la redacción en la mayoría de las
   apariciones, dejando como mucho una o dos con la fórmula original.
5. **Conectores de IA típicos** en posición y frecuencia uniformes: ES "sin
   embargo,", "por tanto,", "cabe señalar que,", "no obstante," · EN
   "however,", "furthermore,", "it is important to note that,".
6. **Precisión artificial**: cifras o calificadores que no aportan
   información real, solo apariencia de rigor (distinto de una cifra
   trazable a una macro o a un dato real, que nunca se toca).
7. **Ritmo de frase uniforme**: párrafos donde todas las oraciones comparten
   longitud y estructura sintáctica — el tic más citado en detección de IA en
   español es el binomio "afirmación; matiz contrastivo" repetido con punto y
   coma cada 3-4 líneas.
8. **Vocabulario de "corrección política"/transparencia performativa**:
   "honestidad", "transparencia", "reconocemos que", "es honesto decir",
   "verificación propia, no de un tercero independiente" repetido como
   coletilla en vez de declararse una vez.
9. **Vocabulario inflado** (ver lista completa en `no-ai-slop` §2.D/§3): ES
   "robusto" sin métrica, "holístico", "clave", "fundamental" · EN "delve",
   "leverage", "robust", "seamless", "pivotal", "underscore".

## 3. Cómo escalar la auditoría a un documento grande

Para un documento de decenas de páginas repartidas en muchos archivos `.tex`
(como este TFM), leer todo en una sola pasada agota contexto sin necesidad.
El patrón que funciona es **reparto en paralelo por capítulo/tema, con un
fork por cada bloque independiente**:

1. Agrupa los archivos por unidad temática (p. ej. Marco Teórico, cada SP,
   cada capítulo nuevo, frontmatter/global).
2. Lanza un fork por grupo con instrucciones idénticas: leer los archivos
   completos, aplicar las 9 categorías de la Sección 2, citar archivo:línea
   y frase textual de cada hallazgo, y — para las plantillas repetidas —
   reportar el conteo total con 2-3 ejemplos en vez de cada instancia por
   separado.
3. Pide explícitamente que cada fork distinga **patrón de IA** de
   **convención de diseño deliberada y consistente** (p. ej. un campo de
   estado tipo `demostrado/parcial/pendiente` repetido en todas las cajas de
   resultado no es un tic, es una plantilla estructurada a propósito). Sin
   este filtro, la auditoría genera falsos positivos sobre el propio formato
   del documento.
4. Añade un fork de **barrido global de frecuencia**: grep de las frases
   candidatas a plantilla a través de todo el árbol, para contar cuántas
   veces aparece cada una y decidir si el patrón cruza el umbral de lo
   mecánico (3+ repeticiones casi verbatim en secciones independientes suele
   ser el umbral útil).
5. Consolida los hallazgos de todos los forks en una sola lista priorizada
   antes de tocar el código: arregla primero lo que aparece en más forks a la
   vez (señal de que es un patrón real, no ruido de un solo lector).

## 4. Al corregir

- Varía la redacción en vez de borrar contenido: una plantilla repetida 8
  veces no significa que sobren 7 frases, significa que hay una sola idea
  dicha 8 formas distintas posibles y solo se usó una.
- Nunca toques una demostración, ecuación, enunciado formal o cifra para
  "sonar menos a IA" — eso es trabajo de otra naturaleza y esta habilidad no
  lo autoriza (mismo límite que `no-ai-slop` y `tfm-voice`).
- Recompila y confirma 0 errores / 0 referencias indefinidas después de cada
  tanda de cambios de estilo: un ajuste de prosa nunca debería romper una
  `\ref`, un `\label` o un `\eqref`.
- Si una plantilla resulta ser una convención de diseño (ver punto 3.3), no
  la toques; anótala como verificada y sigue.

## 5. Qué NO hace esta habilidad

No reescribe demostraciones, definiciones ni cifras. No es un sustituto de
una revisión de rigor matemático o de cumplimiento normativo (usa
`math-rigor`, `claims-evidence-guard`, `viu-compliance` para eso). No
persigue "pasar" un detector externo: persigue que el texto sea bueno, que es
lo único que además funciona contra un detector.
