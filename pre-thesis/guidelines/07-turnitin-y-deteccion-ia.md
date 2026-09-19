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