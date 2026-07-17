# AGENTS.md — Contrato operativo del TFM MROB

## 1. Misión del repositorio

Este repositorio desarrolla el TFM de Jorge Luis Mayorga Taborda sobre coordinación distribuida de múltiples AMR para formar coaliciones y transportar cargas heterogéneas. El agente debe producir trabajo científicamente trazable, código reproducible y texto compatible con la estructura oficial de la VIU.

El objetivo no es generar texto plausible. El objetivo es construir y validar una contribución técnica verificable.

## 2. Fuentes de verdad y precedencia

Antes de realizar una tarea sustantiva, leer en este orden:

1. `docs/00_TFM_CHARTER.md`: alcance, preguntas, hipótesis y contribución.
2. `docs/01_VIU_REQUIREMENTS.md`: estructura y restricciones académicas.
3. `docs/02_RESEARCH_MATRIX.md`: descomposición SP0–SP8 y nivel de evidencia.
4. `docs/03_EXPERIMENT_PROTOCOL.md`: reglas de comparación y validación.
5. `docs/04_CLAIMS_EVIDENCE.md`: trazabilidad entre afirmaciones y evidencia.
6. `docs/05_NOTATION.md`: notación matemática canónica.
7. `docs/07_SP_SECTION_TEMPLATE.md`: microestructura obligatoria cuando se crea, completa o revisa un SP.
8. Código, configuraciones y resultados existentes.
9. La petición concreta del usuario.

Si dos fuentes se contradicen, detener la propagación del error, documentar la contradicción y aplicar la fuente de mayor precedencia. No modificar el alcance administrativo ni el título oficial sin indicación expresa del autor y aprobación del director.

## 3. Alcance científico canónico

### 3.1 Tema

Diseñar y validar un mecanismo distribuido, explicable y basado en teoría de juegos —preferentemente juegos potenciales/poblacionales y dinámicas evolutivas— para:

- reclutar coaliciones de tamaño y capacidad adecuados;
- asignar robots heterogéneos a cargas heterogéneas;
- acoplar la decisión estratégica con el movimiento físico;
- transportar una carga desde una pose origen a una pose destino;
- recuperar la operación ante fallos;
- cuantificar escalabilidad, coste computacional y coste de comunicación.

### 3.2 Restricciones de la solución propuesta

- Sin aprendizaje por refuerzo multiagente como método principal.
- Arquitectura distribuida: cada robot usa estado propio, percepción local y mensajes vecinales.
- Un optimizador central puede utilizarse únicamente como baseline/oráculo experimental.
- Algoritmo white-box: estados, payoffs, restricciones, parámetros y leyes de control deben ser interpretables.
- Evitar una FSM global de alto nivel. Preferir campos vectoriales, dinámicas continuas, activaciones suaves o mecanismos asíncronos locales.
- Distinguir siempre entre modelo matemático continuo y ejecución digital muestreada. No afirmar “sin reloj” en un sistema implementado digitalmente; formularlo como ausencia de rondas globales síncronas o de planificación por lotes.
- No afirmar optimalidad, convergencia, estabilidad, robustez o escalabilidad sin una definición formal y evidencia correspondiente.

### 3.3 Alcance físico

El transporte cooperativo puede considerar:

1. transporte rígido/prehensil con formación y reparto de wrench; o
2. transporte no prehensil mediante caging/empuje.

Uno de los dos modos debe declararse **modo primario** y validarse completamente. El segundo es extensión opcional, salvo que exista tiempo y evidencia suficientes. No mezclar ambos bajo una única prueba de estabilidad sin modelar explícitamente sus diferencias de contacto y restricciones.

## 4. Descomposición SP0–SP8

Usar los subproblemas como una escalera de capacidades, no como nueve tesis independientes:

- **SP0:** robots y cargas homogéneos; reclutamiento/asignación básica.
- **SP1:** robots homogéneos; cargas heterogéneas y cardinalidad variable.
- **SP2:** robots y cargas heterogéneos; restricciones multidimensionales de capacidad.
- **SP3:** interacción física con la carga; formación rígida o caging/empuje; factibilidad de fuerzas, wrench y torque.
- **SP4:** transporte cooperativo de pose origen a pose destino.
- **SP5:** evitación de obstáculos durante aproximación y transporte.
- **SP6:** fallo o retirada de un robot y re-reclutamiento distribuido durante la ejecución.
- **SP7:** tráfico entre coaliciones, robots libres, cargas y obstáculos dinámicos.
- **SP8:** escalabilidad y robustez de red: número de robots/cargas, energía, complejidad, mensajes, retardos y pérdidas de paquetes.

La profundidad no tiene que ser uniforme. Respetar los niveles de evidencia definidos en `docs/02_RESEARCH_MATRIX.md`.

## 5. Reglas de rigor matemático

1. Definir conjuntos, variables, parámetros, supuestos y dominios antes de usarlos.
2. Separar claramente:
   - asignación estratégica;
   - estimación/consenso;
   - cinemática o dinámica del robot;
   - interacción carga–robot;
   - seguridad y evitación;
   - comunicación.
3. Toda función de payoff debe indicar unidades, dependencia, interpretación y efecto de cada término.
4. Toda ley de control debe respetar dimensiones físicas y límites de actuador.
5. Todo resultado formal debe etiquetarse de forma honesta:
   - **Lema/Teorema:** prueba completa y supuestos explícitos;
   - **Proposición:** resultado limitado con demostración suficiente;
   - **Conjetura:** aún no probada;
   - **Observación empírica:** sustentada solo por experimentos.
6. Una simulación no demuestra estabilidad ni convergencia global.
7. Un equilibrio de Nash no implica por sí solo optimalidad social, factibilidad mecánica ni ausencia de colisiones.
8. Si se usa una función potencial, demostrar o verificar la relación entre diferencias de payoff y variación del potencial.
9. Si se usa Lyapunov/passivity, declarar el candidato, calcular su derivada o diferencia y especificar el conjunto invariante.
10. Si la formulación discreta aproxima una ley continua, declarar integrador, paso, error y condiciones numéricas.
11. Registrar toda modificación de notación en `docs/05_NOTATION.md`.

## 6. Reglas bibliográficas

- Nunca inventar artículos, autores, años, DOI, resultados, citas ni páginas.
- Priorizar fuentes primarias: artículos revisados por pares, libros académicos y documentación oficial.
- Mantener cada fuente en `references/LITERATURE_LEDGER.md` con estado `verificada`, `parcial` o `pendiente`.
- Una referencia `pendiente` no puede respaldar una afirmación fuerte en la memoria.
- Diferenciar “método clásico”, “baseline competitivo” y “estado del arte”. No llamar SOTA a un método sin revisión comparativa reciente y verificable.
- No usar “nadie ha propuesto…” salvo que exista una revisión suficientemente amplia y documentada. Preferir “no se identificó en la revisión realizada…”.
- Redactar en paráfrasis propia y aplicar APA 7 en la memoria.

## 7. Baselines y comparaciones

Elegir el baseline según el subproblema:

- El algoritmo húngaro solo es baseline válido para asignación uno-a-uno o una reducción demostrada a dicho caso.
- Para coaliciones, capacidades múltiples y cargas heterogéneas, usar MILP/ILP, set partitioning, generalized assignment o una formulación central equivalente.
- Para asignación distribuida, considerar subastas/consenso o formación de coaliciones verificadas en literatura.
- Para planificación y tráfico, seleccionar métodos adecuados al modelo: A*/Dijkstra, CBS/ECBS, planificación priorizada, ORCA/RVO o CBF-QP, según corresponda.
- Para formación/manipulación, comparar contra leader–follower, virtual structure, consenso/formación o reparto centralizado de fuerzas, según el escenario.

Todos los baselines deben recibir la misma información disponible en el nivel que se compare, o la diferencia debe declararse explícitamente. El oráculo central puede disponer de información global, pero debe presentarse como techo o referencia, no como comparación “justa” de arquitectura.

## 8. Reglas de implementación

- Lenguaje principal: Python 3.11 o la versión fijada por el entorno reproducible.
- Identificadores y comentarios técnicos en inglés; documentación académica en español.
- Código fuente en `src/`; notebooks solo para exploración, nunca como única implementación.
- Configuraciones de experimentos versionadas en `experiments/configs/`.
- Semillas aleatorias explícitas y registradas.
- Separar datos crudos, datos procesados, figuras y tablas.
- No codificar resultados manualmente en figuras o texto.
- Cada métrica debe tener una función única, probada y documentada.
- Añadir pruebas unitarias para modelos, restricciones, payoffs, integradores y métricas.
- Añadir pruebas de invariantes: límites de velocidad, conservación de población cuando aplique, factibilidad de asignación, ausencia de NaN/Inf y reproducibilidad.
- Antes de añadir una dependencia, justificarla y comprobar si el repositorio ya resuelve esa función.
- No editar archivos generados si existe una fuente reproducible que los produce.

## 9. Protocolo experimental mínimo

Para cada SP trabajado:

1. Definir pregunta e hipótesis local.
2. Declarar escenario, parámetros fijos y factores variables.
3. Elegir baseline(s) pertinentes.
4. Ejecutar casos idénticos y, cuando sea estocástico, semillas pareadas.
5. Reportar distribución, intervalo de confianza y número de ejecuciones, no solo promedios.
6. Incluir al menos una ablación de componentes críticos del método propuesto.
7. Registrar fallos, casos no convergentes y resultados negativos.
8. Generar automáticamente tabla y figura desde los datos procesados.
9. Actualizar la matriz de evidencia antes de redactar conclusiones.

Métricas candidatas: factibilidad, utilidad social, gap de optimalidad, tiempo de formación, makespan, throughput, energía, error de pose, residual de wrench, colisiones/distancia mínima, tiempo de recuperación, mensajes/bytes, tiempo de CPU y memoria.

## 10. Estructura de la memoria VIU

Conservar los capítulos de nivel superior exigidos por la plantilla:

1. Introducción.
2. Objetivos.
3. Hipótesis de partida.
4. Metodología.
5. Marco teórico y estado del arte.
6. Resultados y análisis.
7. Conclusiones y recomendaciones.
8. Referencias bibliográficas.

SP0–SP8 se desarrollan principalmente dentro del capítulo 6 y se agrupan en bloques para evitar repetición. Al menos el 50 % del cuerpo principal debe corresponder a resultados, análisis y validación. El cuerpo debe mantenerse entre 50 y 80 páginas, sin contar preliminares ni anexos; anexos, máximo 20 páginas.

Cada capítulo o apartado debe empezar con un párrafo introductorio. No dejar dos encabezados consecutivos sin texto. Toda figura, tabla y ecuación debe numerarse, citarse en el texto y tener fuente o indicación de elaboración propia.

La microestructura canónica de `sp0.tex`--`sp8.tex` se define en `docs/07_SP_SECTION_TEMPLATE.md`. Debe conservarse la secuencia título e introducción, diagrama TikZ, problema de optimización, tabla crítica de métodos/literatura, juego distribuido, problema de control o delimitación explícita, simulaciones, comparaciones y conclusión. La plantilla fija contenido, no una extensión uniforme.

## 11. Flujo de trabajo del agente

Para tareas complejas:

1. Leer las fuentes de verdad aplicables.
2. Inspeccionar el repositorio y resultados existentes.
3. Crear o actualizar un plan en `plans/` usando `plans/PLANS.md`.
4. Identificar supuestos y riesgos antes de implementar.
5. Ejecutar el cambio mínimo coherente.
6. Ejecutar pruebas y experimento de humo.
7. Revisar el diff y buscar regresiones.
8. Actualizar documentación, matriz de evidencia y registro de decisiones.
9. Entregar un resumen que distinga: hecho, evidencia, limitación y siguiente riesgo.

No pedir al usuario que confirme cada decisión menor. Resolver ambigüedades conservadoramente y documentar el supuesto. Pedir aclaración solo cuando una decisión cambie materialmente la hipótesis, el alcance administrativo o la interpretación de resultados.

## 12. Definición de terminado

Una tarea no está terminada hasta que:

- el entregable existe en la ruta acordada;
- las pruebas pertinentes pasan;
- los resultados son reproducibles desde una configuración versionada;
- no se introducen citas ni números no verificados;
- las afirmaciones están clasificadas por nivel de evidencia;
- se actualizan los documentos de trazabilidad afectados;
- se declaran limitaciones y supuestos relevantes.
