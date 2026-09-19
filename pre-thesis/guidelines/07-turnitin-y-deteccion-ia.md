# Turnitin y deteccion de escritura asistida

> Parte de las directrices del TFM. Contenido copiado sin cambios de
> `GUIDELINES.md`, lineas 8929 a 9005. Indice en [`00-INDICE.md`](00-INDICE.md).

---


La detección de IA es un desafío en constante evolución, especialmente con actualizaciones como la de Turnitin en agosto de 2026. He investigado a fondo para ofrecerte una guía actualizada que combine métodos manuales, ajustes técnicos y herramientas de código abierto para reducir al mínimo la detección, siempre con un enfoque de integridad académica.

### 🔍 Entendiendo el Detector de Turnitin (Actualización 2026)

Turnitin **reentrenó su modelo de detección de IA en inglés el 18 de agosto de 2026**, lo que ha invalidado muchas técnicas que funcionaban antes. Los trucos antiguos como el simple intercambio de sinónimos, añadir palabras de relleno o usar parafraseadores gratuitos **ahora fallan más de lo que funcionan**.

Lo que **sí sigue funcionando** en septiembre de 2026 se basa en tres pilares:
1.  **Reescritura estructural a nivel de párrafo**: Reorganizar el flujo de la argumentación, no solo cambiar palabras.
2.  **Variación en la longitud de las frases**: Mezclar frases muy cortas con otras muy largas.
3.  **Humanización que preserva la voz**: Mantener tu estilo personal mientras se rompen los patrones estadísticos de la IA.

### 🛠️ Métodos Manuales y Técnicos para Reducir la Detección

Aquí tienes una guía paso a paso con las técnicas más efectivas para aplicar manualmente a tu texto.

#### **1. Rompe la Estructura Uniforme (El Método Más Eficaz)**

Los detectores buscan patrones predecibles. La clave es la **"burstiness"** (irregularidad) y la **"perplejidad"** (imprevisibilidad).

*   **Varía la longitud de las frases drásticamente**: Alterna frases de 3-5 palabras con otras de 30 o 40. Evita tener tres frases consecutivas de longitud similar.
    *   *Ejemplo AI*: "La robótica móvil es un campo interdisciplinario. Requiere conocimientos de mecánica, electrónica y programación. Su aplicación es cada vez más común en la industria."
    *   *Ejemplo Humanizado*: "La robótica móvil es un campo interdisciplinario. Sin embargo, su implementación exitosa, que depende de una compleja integración de mecánica, electrónica, control y programación avanzada, sigue siendo un desafío monumental para los ingenieros. Y su aplicación en la industria no deja de crecer."
*   **Rompe el patrón de párrafo "tópico → 3 apoyos → transición"**: La IA tiende a seguir esta estructura de forma casi invariable. Introduce párrafos que comiencen con una pregunta, una cita, un dato sorprendente o una anécdota.
*   **Introduce "ruido" sintáctico**: Usa oraciones subordinadas, incisos, paréntesis, guiones largos (—) y puntos y coma (;) de forma natural. La IA tiende a una sintaxis más plana.

#### **2. Ajusta el Vocabulario y los Conectores**

La IA abusa de ciertos términos y estructuras repetitivas.

*   **Elimina la "jerga de IA"**: Los detectores tienen listas de palabras que son señales de alerta. **Evita o usa con extrema moderación** términos como: *delve, leverage, tapestry, nuanced, foster, robust, pivotal, transformative, landscape, realm, underscore, harness, facilitate, navigate, crucial, paramount, meticulous, seamless*.
*   **Varía los conectores lógicos**: No uses siempre "además", "por lo tanto", "sin embargo". Alterna con: "aun así", "no obstante", "por el contrario", "en consecuencia", "de ahí que", "así pues", "en definitiva".
*   **Usa un lenguaje más coloquial y directo (con moderación académica)**: La IA tiende a un registro demasiado formal y neutral. Introducir alguna expresión más natural, una pregunta retórica o una opinión matizada puede ayudar.
*   **Cuidado con la "voz pasiva" excesiva**: La IA a menudo la usa para sonar objetiva. En español, la pasiva refleja ("se observa que...") es más natural, pero no abuses de ella.

#### **3. Inyecta "Humanidad" con Elementos Personales**

*   **Incluye anécdotas o ejemplos concretos**: La IA generaliza. Tú puedes particularizar. "En mi experiencia al implementar el algoritmo en el simulador Gazebo, me encontré con que..."
*   **Expresa opiniones y matices**: "Si bien los resultados son prometedores, personalmente considero que la metodología presenta una limitación crucial que no debe pasarse por alto."
*   **Referencias a tu propio proceso**: "Durante el desarrollo de este TFM, una decisión de diseño clave fue la de priorizar la eficiencia computacional sobre la precisión absoluta, debido a las restricciones de hardware."

### 📚 Lista de Palabras y Frases a Evitar (o Usar con Cautela)

Los detectores buscan estas "señales" de IA. **No se trata de prohibirlas, sino de no abusar de ellas y, sobre todo, de no usarlas en patrones repetitivos.**

| Categoría | Palabras y Frases a Evitar / Moderar |
| :--- | :--- |
| **Verbos de "IA"** | *Delve into, leverage, harness, underscore, facilitate, navigate, foster, embody, exemplify, encompass, illuminate, elucidate.* |
| **Adjetivos "inflados"** | *Pivotal, crucial, paramount, robust, nuanced, transformative, meticulous, seamless, comprehensive, multifaceted, intricate, profound, compelling.* |
| **Sustantivos "abstractos"** | *Tapestry, landscape, realm, paradigm, synergy, nexus, interplay, framework (en exceso), implication.* |
| **Conectores "fórmula"** | *Moreover, furthermore, in conclusion, additionally, consequently, notably, importantly, it is worth noting that, it is important to note that.* |
| **Estructuras "cliché"** | *"In today's fast-paced world...", "In the realm of...", "A testament to...", "Shed light on...", "Pave the way for..."* |
| **Frases de "relleno"** | *"It goes without saying that...", "Needless to say...", "In order to..."* |

### 💻 Repositorios de GitHub y Herramientas de Código Abierto (2026)

Existen varias herramientas de código abierto que aplican estas técnicas de forma automatizada. Úsalas como **apoyo a tu propia reescritura**, no como sustituto.

| Repositorio / Herramienta | Enfoque Principal y Técnica | Enlace |
| :--- | :--- | :--- |
| **text-humanizer** | **Cadena de traducción multilingüe**. Pasa el texto por un LLM, luego lo traduce al turco (y opcionalmente al japonés) y finalmente lo reconstruye al español. Esto introduce variaciones estructurales profundas. | [https://github.com/korcarc/text-humanizer](https://github.com/korcarc/text-humanizer) |
| **humanize-text** | **Pipeline estándar de 5 pasos**. Combina reescritura con LLM (DeepSeek) a alta temperatura y múltiples saltos de traducción (chino → japonés → finlandés → inglés) para romper las huellas estadísticas de la IA. | [https://github.com/the-coding-freak/humanize-text](https://github.com/the-coding-freak/humanize-text) |
| **unmask-ai** | **Pipeline de 3 pasadas con Claude Sonnet 4**. Se enfoca en inyectar **perplejidad** (elecciones de palabras inesperadas) y **burstiness** (variación drástica de longitud de frases). También elimina activamente 30+ palabras de vocabulario de IA. | [https://github.com/imsv1301/unmask-ai](https://github.com/imsv1301/unmask-ai) |
| **StealthHumanizer** | **Reescritura multipaso y consciente del estilo**. Utiliza diferentes modelos (BART para textos cortos, Gemma para largos) y ofrece 4 niveles de reescritura y 6 estilos de escritura para preservar la voz del autor. | [https://github.com/rudra496/StealthHumanizer](https://github.com/rudra496/StealthHumanizer) |
| **texthumanizer** | **Humanizador offline (PyPI)**. Usa un modelo T5 local para reescribir texto preservando citas, abreviaturas y terminología técnica. Ideal para documentos `.docx` con referencias. | [https://pypi.org/project/texthumanizer/](https://pypi.org/project/texthumanizer/) |

### ⚠️ Consideraciones Éticas y de Integridad Académica

Es fundamental que uses estas técnicas de forma **responsable y transparente**.

*   **Declara siempre el uso de IA**: La normativa de la VIU y de la mayoría de las revistas científicas exigen que declares si has utilizado herramientas de IA para **cualquier** parte del proceso, incluyendo la corrección gramatical o la traducción. Ocultarlo es una falta grave.
*   **El objetivo no es "engañar", sino "mejorar"**: La meta no es hacer pasar un texto 100% generado por IA como humano, sino **utilizar la IA como un asistente** para superar el "bloqueo del folio en blanco", generar ideas o mejorar tu redacción, y luego **reescribir y aportar tu propio valor** de forma sustancial.
*   **El detector puede dar "falsos positivos"**: La propia Turnitin advierte que su detector puede marcar erróneamente textos escritos por humanos, especialmente si son muy formales o siguen estructuras muy rígidas. Tu mejor defensa es tener **evidencia de tu proceso de escritura** (borradores, notas, historial de versiones).

En resumen, la estrategia más robusta para 2026 es **combinar una reescritura estructural profunda (manual o asistida) con una declaración honesta del uso de IA**. Esto no solo reduce el riesgo de detección, sino que también mejora la calidad y originalidad de tu TFM.

Si necesitas que profundice en alguna de estas técnicas o herramientas, no dudes en preguntar.

---
---

# Ampliación — Patrones de escritura de IA en español (2026)

> Esta parte **no** procede de `GUIDELINES.md`: se añadió después, con material
> aportado por el autor. Cubre tres niveles de detección: **léxico** (palabras),
> **estructural** (frases y párrafos) y **estadístico** (cadencia y simetría).
>
> Lo medible de esta guía está implementado en
> `.claude/skills/ai-burstiness/scripts/burstiness_lint.py`, que marca la
> ocurrencia concreta en el `.tex`. Lo no medible —tiempos verbales, sentencias
> filosóficas, calidad de una reescritura— requiere lectura.

## Nota de encuadre

El objetivo aquí es **calidad de redacción**, no enmascaramiento. Las tres
razones, en orden de peso práctico:

1. **Los trucos superficiales ya no funcionan.** El propio material lo dice: tras
   el reentrenamiento de agosto de 2026, el intercambio de sinónimos, las
   palabras de relleno y los parafraseadores fallan más de lo que funcionan.
2. **En un texto técnico, el intercambio de sinónimos destruye precisión.**
   *wrench*, *coalición*, *certificado*, *potencial* y *margen* son términos
   fijos. No admiten variación estilística.
3. **La normativa pide lo contrario.** `viu-compliance` §11.10: comprobar si hay
   que declarar el uso de IA y, si la normativa no lo cubre, preguntar al tutor.
   Un texto bien escrito y declarado es una posición sólida.

La defensa real ante una revisión de autoría no es un porcentaje bajo: es poder
reconstruir cómo se escribió cada sección —borradores, commits, datos crudos,
resultados negativos, decisiones argumentadas—. Este repositorio ya tiene eso.

---

## Nivel 1 — Léxico

### A. Verbos delatores

| Evitar | Por qué | Alternativa |
|---|---|---|
| ahondar / profundizar | forma rebuscada de «analizar» | analizar, examinar, estudiar, revisar |
| aprovechar (*leverage*) | jerga empresarial trasladada a todo | usar, emplear, aplicar, valerse de |
| desbloquear (*unlock*) | cliché de «desbloquear el potencial» | permitir, habilitar, abrir |
| fomentar (*foster*) | lenguaje corporativo vacío | impulsar, promover, apoyar |
| impulsar (*harness*) | palabra de moda tecnológica | usar, aprovechar con moderación |
| navegar (*navigate*) | casi siempre en «navegar por el panorama» | gestionar, manejar, lidiar con |
| revolucionar | hipérbole vacía | cambiar, transformar, con datos |
| subrayar (*underscore*) | demasiado enfático para lo que dice | destacar, señalar, recalcar |
| facilitar | sobreusado en registro académico | ayudar, permitir, posibilitar |

### B. Adjetivos inflados

| Evitar | Por qué | Alternativa |
|---|---|---|
| crucial / pivotal | marcador de importancia sobreusado | importante, clave, fundamental |
| **robusto** | jerga de ingeniería aplicada a todo | sólido, fiable — y en esta tesis, **solo si hay definición formal** |
| innovador | marketing vacío | nuevo, original, o ser específico |
| transformador | *buzzword* sin sustancia | que cambia, que afecta a |
| vibrante | descriptor vacío | activo, dinámico |
| intrincado | complejidad sin especificidad | detallado, complejo |
| significativo | diluido de tanto uso; además **colisiona con «significativo» estadístico** | notable, relevante — o el término estadístico exacto |
| contundente | adjetivo de moda | claro, directo, decisivo |

### C. Sustantivos grandilocuentes

| Evitar | Alternativa |
|---|---|
| panorama / paisaje (*landscape*) | campo, área, sector, ámbito |
| tapiz (*tapestry*) | conjunto, mezcla, combinación |
| paradigma | modelo, enfoque, marco |
| sinergia | colaboración, cooperación |
| ecosistema | sistema, entorno, conjunto |
| testimonio («es un testimonio de…») | prueba, señal, muestra |
| catalizador | desencadenante, motor |

### D. Fórmulas de apertura y cierre

- **Abrir párrafo:** «En el mundo actual…», «En la era digital…», «En el panorama de…», «Es importante señalar que…», «Cabe destacar que…».
- **Cerrar:** «En resumen…», «En conclusión…», «En definitiva…», «Como se ha podido observar…».
- **Enfatizar:** «No solo… sino también…», «No se trata de X, se trata de Y», «La clave está en…».
- **Atribuir sin fuente:** «Según expertos…», «Estudios demuestran que…», «La industria sostiene que…».

La última categoría es la más grave aquí: en un TFM, una atribución vaga sin
cita es un defecto de rigor antes que de estilo.

---

## Nivel 2 — Estructura

### E. Paralelismo negativo

Afirmar negando el opuesto, para crear dramatismo falso.

- **IA:** «No es solo una herramienta de simulación; es un catalizador para la transformación del paradigma robótico.»
- **Humano:** «La herramienta simula entornos con contacto, lo que permite validar el controlador antes de llevarlo a la planta física.»

### F. Pregunta retórica con respuesta inmediata

- **IA:** «¿Cuál es el verdadero desafío de la robótica cooperativa? La respuesta reside en la comunicación.»
- **Humano:** «El principal desafío es mantener una comunicación fiable y de baja latencia entre los agentes.»

### G. Regla de tres

La IA convierte cualquier argumento en un trío perfecto. Es la simetría más
fácil de detectar.

- **IA:** «El sistema ofrece velocidad, precisión y robustez.»
- **Humano:** «El sistema mantiene la precisión en entornos dinámicos, aunque a costa de un mayor tiempo de cómputo.»

Corrección: desarrolla un elemento en dos frases, suprime el que no aporta y
cierra de forma abrupta.

### H. Cadena de gerundios

Calco del inglés, donde el *-ing* encadena con naturalidad que el español no tiene.

- **IA:** «Siendo una plataforma innovadora, priorizando la escalabilidad y manteniendo un enfoque robusto…»
- **Humano:** «La plataforma prioriza la escalabilidad. Para ello mantiene un diseño modular.»

Regla: **más de dos gerundios en una frase, se parte en oraciones independientes.**

### I. Simetría de párrafo

Señal: todos los párrafos con 4–5 frases y la misma altura visual en la página;
cada sección cerrada con un mini-resumen.

Corrección: varía la extensión de forma drástica. **Un párrafo de una sola frase
contundente entre dos largos** rompe la métrica de uniformidad.

> Atención al límite VIU: **ningún párrafo por debajo de tres oraciones
> completas**. La variación va entre 3 y 10, no entre 1 y 10.

### J. Transiciones anunciadas

«Lo que esto significa en la práctica es…», «A continuación, veamos…». Haz la
transición sin anunciarla.

### K. Cierres con imperativos encadenados

«Empieza X. Deja de Y. Invierte en Z.» Termina con una observación, una
limitación o una pregunta abierta.

---

## Nivel 3 — Calcos del inglés

Específico del español generado por LLM, cuyo entrenamiento es mayoritariamente
en inglés.

### L. Calcos de estilo

- **Calco:** «La implementación de un sistema de control **que es** capaz de…»
- **Español:** «La implementación de un sistema de control capaz de…»

### M. Omisión de artículo

- **Calco:** «Robots son esenciales para automatización.»
- **Español:** «**Los** robots son esenciales para **la** automatización.»

### N. Vocabulario traducido

| Calco | Origen | Alternativa |
|---|---|---|
| cuello de botella | *bottleneck* | limitación, restricción, punto crítico |
| líder del sector | *industry leader* | empresa puntera, referente del sector |
| en el panorama de | *in the landscape of* | en el ámbito de, en el campo de |
| punto de inflexión | *tipping point* | momento clave, cambio decisivo |
| rol crucial | *crucial role* | papel fundamental, función clave |
| visión de futuro | *vision* | perspectiva, proyección |

### O. Tiempos verbales

Hallazgo específico del español: los LLM abusan del **imperfecto y
pluscuamperfecto** y olvidan el **pretérito perfecto simple**, que es el pasado
narrativo natural para relatar un proceso experimental.

- **IA:** «Se estaba ejecutando la campaña mientras se habían registrado los residuales.»
- **Humano:** «**Ejecuté** la campaña con 30 semillas y **registré** el residual de cada corrida.»

En una memoria con registro impersonal: «**se ejecutó**», «**se registró**»,
«**se observó**» — perfecto simple, no imperfecto.

### P. Puntuación calcada

| Signo | Problema | Acción |
|---|---|---|
| raya (—) | comodín para incisos, calcado del inglés | en español, paréntesis o coma; **reducir drásticamente** |
| dos puntos (:) | usados para introducir cualquier explicación | reservarlos para anunciar lista, cita o ejemplo |
| negrita | poco habitual en prosa académica española | reservarla a títulos; si un concepto importa, explícalo |

---

## Nivel 4 — Firma estadística

Los detectores miden **perplejidad** (imprevisibilidad del vocabulario) y
**burstiness** (variación de longitud de frase). La IA tiende a perplejidad y
burstiness bajas: ritmo monótono.

- **Señal:** tres frases seguidas de longitud parecida; todo el párrafo entre 15 y 25 palabras.
- **Corrección:** tras una frase larga, una de 5–8 palabras. Ejemplo: *«El control predictivo se apoya en un modelo dinámico y resuelve una optimización en cada paso, lo que lo encarece. Aun así, funciona.»*

Umbrales operativos del proyecto (§6 de la *skill* `ai-burstiness`): desviación
típica de longitud de frase **≥ 8 palabras**, al menos una frase **< 10** y una
**> 35** por sección.

### Q. La zona gris

La prosa técnica muy estandarizada y el texto híbrido son cada vez menos
distinguibles, y eso corta en ambos sentidos: **la perfección uniforme también
es sospechosa**. La variabilidad debe ser intencionada, no un descuido.

---

## Herramientas: diagnóstico, no generación

| Herramienta | Qué hace | Uso admisible aquí |
|---|---|---|
| `burstiness_lint.py` (este repositorio) | mide varianza de frase, uniformidad de párrafo, conectores, calcos, gerundios y puntuación, y señala la ocurrencia | **el que se usa**: diagnóstico sobre el `.tex`, la reescritura es del autor |
| SignsofAI | *linter* de patrones en español con explicación por hallazgo | aceptable como segundo diagnóstico |
| UnMask.AI | inyecta perplejidad y burstiness automáticamente | **solo la función de detección**; la reescritura automática no |
| Cadenas de traducción (es→zh→tr→ja→es) | rompe la firma estadística traduciendo en círculo | **no se usa.** Degrada la precisión terminológica y su único propósito es enmascarar |

La distinción es la de siempre: una herramienta que **señala dónde mirar** es
legítima; una que **reescribe para que un clasificador falle** no mejora el
texto y no se emplea en este trabajo.

---

## Checklist de auditoría por sección

**Léxico**

- [ ] ¿Aparecen «crucial», «robusto», «transformador», «panorama», «ahondar» más de una vez?
- [ ] ¿«Robusto» y «significativo» se usan sin definición formal ni sentido estadístico?
- [ ] ¿Hay atribuciones vagas —«estudios demuestran»— sin cita?

**Estructura**

- [ ] ¿Algún párrafo abre con «Es importante señalar…», «Cabe destacar…», «En el mundo actual…»?
- [ ] ¿Aparece «No solo… sino también…» o «No se trata de X, sino de Y»?
- [ ] ¿Hay listas de exactamente tres elementos que puedan ser dos, cuatro o desarrollarse?
- [ ] ¿Alguna frase encadena más de dos gerundios?
- [ ] ¿Se anuncian las transiciones en vez de hacerlas?
- [ ] ¿Todos los párrafos tienen extensión parecida? (variar entre 3 y 10 oraciones, nunca menos de 3)

**Calcos**

- [ ] ¿«cuello de botella», «líder del sector», «rol crucial», «punto de inflexión»?
- [ ] ¿Falta algún artículo donde el español lo exige?
- [ ] ¿«que es / que son» innecesarios delante de un adjetivo?
- [ ] ¿El relato experimental usa perfecto simple o todo está en imperfecto?

**Puntuación**

- [ ] ¿Más de dos rayas (—) en la sección?
- [ ] ¿Cada dos puntos anuncia lista, cita o ejemplo?
- [ ] ¿Negrita fuera de títulos?

**Cadencia**

- [ ] ¿Tres frases seguidas de longitud similar? Escribe una de menos de ocho palabras.
- [ ] Léelo en voz alta: ¿suena monótono?

**Cierre**

- [ ] ¿El párrafo termina con una frase demasiado redonda? Cerrar con una limitación o un dato concreto es más creíble.

**Lo que no se toca por estilo:** ecuaciones, enunciados de teoremas,
definiciones, cifras, intervalos, $p$-valores, `\viusource`, y la parte
descriptiva de los pies de figura.
