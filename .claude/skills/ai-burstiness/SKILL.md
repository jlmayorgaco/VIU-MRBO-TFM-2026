---
name: ai-burstiness
description: Capa estructural de la prosa en español académico — varianza de longitud de frase, uniformidad de párrafo, densidad de conectores y posición de la frase temática. Úsala cuando el texto ya pasa `tfm-voice` y `no-ai-slop` pero sigue "sonando a IA", o antes de cualquier depósito. Complementa a `ai-writing-audit` (patrones a escala de documento) y `tfm-voice` (registro y léxico); esta mide el ritmo, que las otras no cuantifican. Incluye linter en `scripts/burstiness_lint.py`.
---

# Ritmo de la prosa: la capa que los detectores miden

## 0. Para qué sirve esto, y para qué no

**Sirve** para que la memoria lea como prosa académica madura escrita por un
investigador, no como salida de plantilla. Eso es calidad de escritura y es
exigible por sí mismo: las Instrucciones VIU piden «sin frases superfluas ni
repeticiones» y ortografía y gramática impecables.

**No sirve** como método para ocultar el uso de asistencia de IA. La
`viu-compliance` §11.10 es explícita: *comprobar si hay que declarar el uso de
IA; si la normativa no lo cubre, preguntar al tutor; declararlo sale más barato
que cualquier alternativa*. Un texto bien escrito y declarado es una posición
sólida. Un texto maquillado y no declarado es un riesgo disciplinario que
ninguna técnica de redacción cubre.

La consecuencia práctica: **no se toca ni una cifra, ni un enunciado formal, ni
una atribución de fuente para mejorar una métrica de estilo.**

## 1. Qué mide realmente un detector

No busca palabras concretas. Mide **uniformidad estadística**:

| señal | qué es | valor humano típico | señal de plantilla |
|---|---|---|---|
| *Burstiness* | desviación típica de la longitud de frase | alta: frases de 6 y de 45 palabras conviven | baja: casi todo entre 15 y 25 |
| Uniformidad de párrafo | dispersión del número de frases por párrafo | irregular | casi todos de 4–5 |
| Densidad de conectores | conectores de apertura por cada 100 frases | baja y variada | alta y repetitiva |
| Posición de la frase temática | dónde vive la idea central | varía; a veces implícita | siempre la primera |
| Plantilla de bloque | secuencia fija enunciado → alcance → límite | no existe | se repite N veces |

El léxico lo cubren `no-ai-slop` y `tfm-voice`. **Aquí se trabaja el ritmo.**

## 2. Las seis reglas, adaptadas a un TFM en español

### R1. Varianza de longitud de frase

Objetivo: desviación típica **≥ 8 palabras**, con al menos una frase por debajo
de 10 y una por encima de 35 en cada sección.

- Parte en dos cada tercera o cuarta frase larga.
- Une dos frases cortas consecutivas en una compuesta.
- Una frase muy corta después de una muy larga marca el cierre de un argumento
  mejor que cualquier conector.

### R2. Longitud de párrafo irregular — con el mínimo VIU

**Aquí la guía original choca con la norma y gana la norma.** La fuente
recomienda párrafos de 2–3 frases; las Instrucciones VIU prohíben **cualquier
párrafo de menos de tres oraciones completas**.

Regla resultante: **entre 3 y 10 frases, con dispersión real**. Si toda una
sección tiene párrafos de 4–5, alargar uno a 8–9 y dejar otro en 3.

### R3. Mover la frase temática

No todos los párrafos abren con su tesis. Alternar:

- tesis primero, desarrollo después (el más común, no el único);
- dato primero, lectura al final;
- tesis implícita, que el párrafo sostiene sin enunciarla.

En un TFM el segundo patrón es además el correcto: **la cifra va antes que su
interpretación** (`tfm-voice` R5).

### R4. Lista negra de conectores de apertura, en español

La lista inglesa no se traduce: hay que sustituirla por la nuestra.

| evitar al abrir frase | qué hacer |
|---|---|
| *Además*, *Asimismo*, *Por otra parte*, *En este sentido* | suprimir; si la relación no se entiende sin conector, el problema es el orden de las ideas |
| *Por tanto*, *Por consiguiente*, *En consecuencia* | usar como mucho una vez por sección |
| *Cabe destacar*, *Cabe señalar*, *Es importante destacar*, *Conviene recordar* | suprimir siempre: gestionan la lectura |
| *Nótese que*, *Obsérvese que*, *Como se puede observar* | suprimir; el lector ya está mirando |
| *En conclusión*, *En resumen* | solo en Conclusiones, y una vez |
| *Claramente*, *Evidentemente*, *Notablemente* | suprimir: si fuera evidente no haría falta decirlo |

Umbral: **≤ 6 conectores de apertura por cada 100 frases**.

### R5. Romper la plantilla de bloque

El patrón `formulación → recuadro → «Resultado y alcance» → teorema → «no
certifica…»` repetido diez veces es la huella más visible de un TFM generado
por rondas de auditoría.

**No se eliminan los límites: son la fortaleza del documento.** Se condensan:

- una **tabla transversal** con `resultado | supuestos | garantiza | no garantiza`;
- y los teoremas se escriben después como literatura matemática normal, sin
  repetir la advertencia completa en cada bloque.

### R6. Especificidad concreta

Sustituir abstracción por el detalle que solo este trabajo tiene: la cifra con
su unidad, el nombre del escenario, la semilla, el número de mundos. Es lo que
la fuente llama *ungoogleable specifics* y en un TFM técnico es gratis, porque
esos detalles ya existen.

## 3. Lo que NO hay que hacer

De la propia fuente, y vale doble en un texto técnico:

- **No cambiar sinónimos** para despistar. Falla desde el reentrenamiento de
  agosto de 2026 y aquí además destruye precisión terminológica: *wrench*,
  *coalición*, *certificado* y *potencial* son términos fijos.
- **No inyectar palabras de relleno.** Sube la longitud media sin subir la
  varianza, que es lo que se mide.
- **No introducir errores deliberados.** Es la peor idea de todas.

Tres adaptaciones donde la fuente **no** aplica a un TFM VIU:

| la fuente dice | aquí |
|---|---|
| añadir primera persona | **no**: el registro es impersonal (`tfm-voice`) |
| un detalle autobiográfico por sección | **no**: impropio de una memoria técnica |
| incisos e interrupciones | con moderación; VIU pide prosa sin frases superfluas |

## 4. Zonas intocables

Nunca se modifican para mejorar una métrica de estilo:

- ecuaciones, enunciados de teoremas, proposiciones y definiciones;
- cifras, intervalos de confianza, $p$-valores, tamaños muestrales;
- `\viusource` / `\viuownsource` y cualquier atribución de fuente;
- pies de figura en su parte descriptiva;
- macros generadas (`shared/generated-macros/`): se regeneran, no se editan.

## 5. Cómo se usa

```bash
# una sección
python .claude/skills/ai-burstiness/scripts/burstiness_lint.py pre-thesis/sections/v2/sp1-compact.tex

# el cuerpo activo entero, con resumen por fichero
python .claude/skills/ai-burstiness/scripts/burstiness_lint.py --census final-hardening/census.json --root pre-thesis
```

Orden recomendado antes de un depósito:

1. `no-ai-slop` — léxico (ES/EN)
2. `tfm-voice` — registro y las ocho reglas
3. **`ai-burstiness`** — ritmo y estructura
4. `ai-writing-audit` — pasada final a escala de documento

Los tres primeros son mecánicos y se pueden iterar. El cuarto es de lectura.

## 6. Criterio de aceptación

Por sección de prosa continua (≥ 15 frases):

- [ ] desviación típica de longitud de frase ≥ 8 palabras
- [ ] al menos una frase < 10 palabras y una > 35
- [ ] párrafos entre 3 y 10 frases, sin que el 70 % caiga en un solo valor
- [ ] ≤ 6 conectores de apertura por 100 frases
- [ ] ninguna plantilla de bloque repetida más de tres veces seguidas
- [ ] cero ocurrencias de la lista negra de R4 marcadas como «suprimir siempre»
