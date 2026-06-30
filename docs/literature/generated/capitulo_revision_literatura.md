# Revision sistematica de literatura: coordinacion distribuida y transporte cooperativo multi-robot

## Resumen ejecutivo

Esta revision analiza un corpus local de 5665 registros arXiv, descargados y organizados por tema y ano, con 5931 enlaces tema/ano y 174 estudios priorizados como altamente relevantes para el problema del TFM. La revision no debe interpretarse todavia como una revision PRISMA final, porque la fuente actual es arXiv-first y aun falta incorporar IEEE Xplore, ACM Digital Library, Scopus/Web of Science y rastreo de citas. Si se interpreta correctamente, el corpus ya permite una revision sistematica de mapeo muy fuerte y una primera revision focalizada sobre coordinacion distribuida, asignacion de tareas, coaliciones, formacion rigida y transporte cooperativo multi-robot.

La lectura sistematica muestra una conclusion central: el transporte cooperativo multi-robot no es un problema de control aislado. Es una arquitectura multicapa en la que asignacion de tareas, cierre de coaliciones, restricciones de carga, comunicacion, planificacion, formacion geometrica y control de bajo nivel deben resolverse de manera coherente. La literatura mas cercana al TFM no es una sola familia de metodos, sino la interseccion entre MRTA, consensus/CBBA, control distribuido, teoria de juegos, teoria de grafos, optimizacion distribuida, formacion rigida y validacion robotica bajo restricciones.

Para Smith-QR, la evidencia sugiere un posicionamiento claro: el aporte no debe presentarse como "usar game theory" o "usar control distribuido" de forma generica. El aporte defendible es integrar una dinamica distribuida de asignacion con cierre entero de coalicion, quorum, restricciones fisicas de transporte y robustez frente a degradacion de comunicacion o disponibilidad robotica.

## Metodo seguido

El flujo seguido en el repositorio separa tres niveles. Primero, se construyo un corpus bibliografico local mediante consultas arXiv sobre multi-agent systems, multi-robot robotics, distributed control, networked systems, graph theory, game theory, cooperative transport, coalitions, formation control y warehouse/AGV. Segundo, se construyo una base SQLite reproducible (`literature.sqlite`) con metadatos, rutas PDF, temas, anos y prioridades. Tercero, se extrajo texto de 173 de los 174 registros de alta prioridad, usando las primeras paginas de cada PDF para inspeccion metodologica inicial.

Los registros se clasificaron con reglas transparentes, no con inclusion definitiva automatica. El archivo `screening_candidates.csv` conserva la decision como `unscreened` para que el screening final mantenga juicio revisor y razon de inclusion/exclusion. Esta decision es importante: una revision sistematica real no puede delegar inclusion final a keywords.

La tabla PRISMA preliminar del snapshot local es:

| Etapa | Registros |
|---|---:|
| Registros identificados en corpus arXiv local | 5665 |
| Registros priorizados para screening titulo/resumen | 174 |
| PDFs recuperados para triage full-text | 173 |
| PDFs no recuperados | 1 |
| Estudios incluidos provisionalmente en sintesis narrativa | 174 |

## Tendencias principales

### Crecimiento reciente

El corpus muestra un crecimiento claro entre 2021 y 2026, con alta presencia de temas de robustez, comunicacion, aprendizaje y control distribuido. En los ultimos anos del snapshot, la literatura se desplaza desde formulaciones puramente teoricas de consensus y distributed optimization hacia arquitecturas mas integradas: task allocation con restricciones, aprendizaje multi-agente, GNNs, comunicacion parcial, seguridad y validacion en escenarios de warehouse, manufactura o transporte.

La tendencia no es que una familia sustituya a otra. Mas bien, las familias se estan acoplando:

- MRTA se combina con restricciones de carga, energia y tiempo.
- Control distribuido se combina con comunicacion limitada y seguridad.
- Graph theory se usa tanto para comunicacion como para formacion y topologia del entorno.
- MARL/GNN se usa para escalar politicas, pero normalmente con estructura previa.
- Cooperative transport aparece cada vez mas como problema conjunto de asignacion, formacion y control.

### Conceptos dominantes en alta prioridad

En los 174 estudios de alta prioridad, los conceptos mas frecuentes fueron:

| Concepto | Registros |
|---|---:|
| Graph/network/topology | 169 |
| Robustness/safety/resilience | 156 |
| Communication constraints | 146 |
| Distributed control/consensus | 143 |
| Planning/MAPF/navigation | 135 |
| Optimization/MPC | 134 |
| Learning/MARL/GNN | 92 |
| Warehouse/AGV/logistics | 87 |
| Formation/rigidity/geometry | 81 |
| Task allocation/coalitions | 69 |
| Game theory/markets | 51 |
| Cooperative transport | 45 |

La lectura de esta distribucion es importante. El transporte cooperativo aparece como un subconjunto mas estrecho que la coordinacion distribuida general. Por eso, el TFM debe evitar presentar toda la literatura multi-agent como evidencia directa para transporte de carga. La evidencia directa se concentra en los papers donde aparecen simultaneamente transporte/payload, asignacion/coalicion, control distribuido y restricciones fisicas.

## Taxonomia de la literatura

### 1. Coordinacion distribuida y consensus

La familia mas amplia es la de consensus, control distribuido, optimizacion distribuida y networked systems. Estos trabajos aportan el lenguaje formal para demostrar convergencia, estabilidad, consenso, conectividad y robustez frente a fallos o retardos. Su valor para el TFM es alto como fundamento matematico, pero su transferencia no es automatica.

El patron recurrente es que cada agente actualiza una variable local usando informacion de vecinos. Esto encaja con Smith-QR porque la asignacion puede verse como una dinamica poblacional o de decision local. Sin embargo, muchas formulaciones suponen grafos conectados, actualizaciones sincronas o informacion idealizada. En un warehouse con AGVs, comunicacion degradada y cargas heterogeneas, esas suposiciones deben convertirse en condiciones experimentales explicitas.

Conclusion para el TFM: usar consensus/control distribuido como base, pero demostrar que el mecanismo sigue funcionando cuando la comunicacion se degrada, cuando robots fallan y cuando las coaliciones necesarias no son triviales.

### 2. MRTA, task allocation y coaliciones

La literatura de multi-robot task allocation es la mas cercana a la capa de decision del TFM. Aparecen algoritmos tipo CBBA, bundle methods, subastas, mercados, consenso sobre asignaciones y optimizacion distribuida. Estos trabajos modelan robots escasos, tareas multiples, restricciones locales, objetivos globales y conflicto entre asignaciones.

El limite de esta familia es que frecuentemente termina en "quien hace que tarea", sin cerrar la pregunta fisica de si la coalicion puede transportar la carga. En transporte cooperativo, asignar robots no basta: hay que verificar capacidad, posicion relativa, geometria de contacto, rigidez, wrench disponible, estabilidad de carga y comunicacion suficiente.

Gap: falta una integracion sistematica entre MRTA y factibilidad fisica de transporte. Este gap es central para justificar el cierre quorum/rigid-formation del TFM.

### 3. Transporte cooperativo y manipulacion compartida

Los estudios de cooperative transport, object transportation, cooperative manipulation y payload transportation muestran que la tarea real se descompone en varias capas: seleccion de objeto, seleccion de robots, configuracion de soporte, generacion de trayectoria, control, evitacion de colisiones y compensacion de perturbaciones.

Los trabajos recientes con multi-robot cooperative transport y large-scale assembly planning son especialmente relevantes porque reconocen restricciones de payload, equipos de robots, manipulacion/transporte colaborativo y planificacion a gran escala. Tambien muestran que el problema se vuelve combinatorio cuando se acoplan subensambles, cargas, rutas, prioridades y robots disponibles.

Para el TFM, esta familia aporta el argumento fisico: si la carga no se modela, el algoritmo de asignacion puede producir soluciones numericamente razonables pero fisicamente falsas. La tesis debe insistir en capacidad efectiva, wrench, masa, geometria rectangular, centros de masa y formacion de contacto.

### 4. Teoria de grafos, rigidez y geometria

Graph theory aparece como lenguaje transversal. En comunicacion, el grafo define vecinos e informacion disponible. En formacion, el grafo define distancias, bearing, rigidez y condiciones para conservar forma. En entornos, el grafo representa topologia, caminos, particiones Voronoi o mapas exploratorios.

Esta convergencia es una oportunidad para el TFM: el mismo marco grafico puede conectar red de comunicacion, coalicion de robots y geometria de carga. En particular, las nociones de conectividad, rigidez y particion del espacio ayudan a justificar por que no basta un score economico de asignacion.

Gap: muchos trabajos usan grafos para una sola capa. Pocos articulan simultaneamente grafo de comunicacion, grafo de formacion/contacto y grafo de tareas.

### 5. Game theory, mercados y dinamicas poblacionales

Game theory aparece en potencial games, Stackelberg games, differential games, mean-field/game dynamics, resource allocation y market-based coordination. Su aporte es permitir que decisiones locales se interpreten como respuestas a payoffs, costos, precios o fitness. Esta familia es especialmente compatible con Smith dynamics.

La evidencia directa para transporte fisico es menor que para asignacion abstracta. Por eso, en el TFM conviene usar game theory como capa de decision y no como explicacion completa del sistema. Los payoffs deben conectarse con magnitudes fisicas: deficit de contacto, distancia, energia, congestion, disponibilidad, riesgo de no completar quorum o insuficiencia de wrench.

Gap: falta una traduccion robusta entre payoff economico y factibilidad fisico-geometrica del transporte.

### 6. MARL, GNN y aprendizaje estructurado

La literatura reciente muestra un crecimiento fuerte de multi-agent reinforcement learning, graph neural networks y politicas descentralizadas aprendidas. Los mejores trabajos no son puramente end-to-end. Usan estructura: prioridades dinamicas, grafos, message passing, entrenamiento centralizado con ejecucion descentralizada, jerarquias de tarea/control o features topologicas.

Esto es relevante para la tesis por dos razones. Primero, MARL/GNN es un baseline competitivo para coordinacion adaptativa. Segundo, refuerza la idea de que la estructura importa: incluso los metodos aprendidos necesitan representaciones de tareas, grafos, comunicacion y restricciones.

Para Smith-QR, MARL no debe ser el nucleo del argumento, pero si un comparador o extension. La ventaja de Smith-QR seria interpretabilidad, bajo costo computacional y trazabilidad de decisiones bajo escenarios de escasez.

### 7. Robustez, seguridad y comunicacion limitada

La robustez aparece como resiliencia frente a fallos, ataques, retardos, ruido, perdida de paquetes, comunicacion intermitente, incertidumbre y seguridad de colision. En el corpus, estos temas son frecuentes, pero suelen tratarse de forma separada respecto al transporte cooperativo.

El TFM tiene una oportunidad fuerte aqui: evaluar comunicacion degradada, fallos de robots, perturbaciones de carga y cambios de centro de masa dentro de una misma arquitectura. Esta integracion hace que la contribucion sea mas solida que un algoritmo que solo funciona en condiciones nominales.

## Estudios clave para citar y revisar manualmente

Los siguientes estudios aparecen como candidatos de alta prioridad por su proximidad al nucleo del TFM. Deben revisarse manualmente antes de inclusion final:

| arXiv | Ano | Relevancia |
|---|---:|---|
| 2311.00192 | 2023 | Multi-robot assembly planning; combina task allocation, transporte, configuracion geometrica y ejecucion distribuida. |
| 2212.02692 | 2022 | MARL para task allocation en transporte cooperativo con objetos de pesos desconocidos. |
| 2412.10087 | 2024 | Consensus-based dynamic task allocation con payload consumption; muy cercano a coaliciones con demanda de carga. |
| 2404.02362 | 2024 | Politicas jerarquicas distribuidas para cooperative transport adaptativo. |
| 2303.08933 | 2023 | MRTA-collective transport con GNN y topological descriptors. |
| 2605.26430 | 2026 | Box transport descentralizado con roles y validacion fisica. |
| 2502.13366 | 2025 | Cooperative payload transportation de baja complejidad para robots no holonomicos. |
| 1810.00522 | 2018 | Transporte colaborativo descentralizado con micro-UAVs. |
| 2008.00679 | 2020 | Cooperative control con Stackelberg learning para transporte de objeto bi-robot. |
| 2309.04257 | 2023 | Tutorial de distributed optimization para cooperative robotics; util para marco teorico. |
| 1803.05505 | 2018 | Bearing rigidity y aplicaciones a control/estimacion de sistemas en red. |
| 1911.07266 | 2019 | Formation control robusto con prescribed performance y rigid graph theory. |
| 2105.00389 | 2021 | Survey de coordinacion multi-robot en incertidumbre y entornos adversarios. |
| 1402.2871 | 2014 | Dec-POMDP/macros para control descentralizado multi-robot en warehouse tasks. |
| 2604.11954 | 2026 | Dynamic MRTA con incertidumbre y restricciones de comunicacion desde enfoque game-theoretic. |

## Autores y comunidades recurrentes

La tabla de productividad no debe leerse como ranking de impacto, porque depende de arXiv y de las queries. Si sirve para identificar comunidades:

- Dimos V. Dimarogonas, Karl H. Johansson, Manuel Mazo, Sandra Hirche y Daniel E. Quevedo aparecen asociados a control distribuido, networked systems, comunicacion y optimizacion.
- George J. Pappas y Vijay Kumar aparecen como nodos relevantes entre control, robotics, seguridad y sistemas en red.
- Sven Koenig y Jiaoyang Li aparecen en MAPF, planning y warehouse/logistics.
- Amanda Prorok, Pratap Tokekar y Ramviyas Parasuraman aparecen vinculados a coordinacion, comunicacion, exploracion y multi-robot systems.
- Mac Schwager, Mykel Kochenderfer y colaboradores aparecen en trabajos de planning/assembly/manufacturing de alta relevancia para transporte y coordinacion.

Para una version final, estos nombres deben usarse como punto de partida para backward/forward citation chasing, no como evidencia en si misma.

## Brechas cientificas identificadas

### Brecha 1: asignacion sin factibilidad fisica

MRTA y auction/market methods asignan robots a tareas, pero muchas veces no prueban que la coalicion resultante pueda ejercer el wrench requerido, mantener una formacion rigida o compensar un centro de masa desplazado.

### Brecha 2: control sin decision discreta

Formation control y cooperative manipulation resuelven estabilidad, tracking o geometria local, pero a menudo presuponen que el equipo de robots ya esta elegido. En escenarios logisticos dinamicos, esa seleccion es parte del problema.

### Brecha 3: teoria de juegos sin carga fisica

Game theory y market dynamics dan mecanismos elegantes de asignacion distribuida, pero sus payoffs rara vez codifican explicitamente restricciones de transporte fisico, quorum o capacidad efectiva.

### Brecha 4: robustez fragmentada

Comunicacion degradada, fallos de robots, incertidumbre de masa, congestion y seguridad se estudian en subliteraturas separadas. Faltan arquitecturas que integren esas perturbaciones en una validacion comun.

### Brecha 5: aprendizaje con baja interpretabilidad

MARL/GNN escala y adapta, pero muchas soluciones son dificiles de auditar. Para un TFM orientado a control distribuido y validacion fisica, un mecanismo interpretable puede ser mas defendible que una politica puramente aprendida.

## Posicionamiento recomendado para la tesis

La tesis puede posicionarse asi:

> El problema de transporte cooperativo multi-AGV requiere cerrar la brecha entre asignacion distribuida y factibilidad fisica. La literatura ofrece componentes parciales: MRTA para asignacion, consensus/control distribuido para coordinacion local, graph theory para conectividad/formacion, game dynamics para decision bajo escasez, y cooperative transport para restricciones fisicas. Sin embargo, pocos enfoques integran esas capas en una arquitectura reproducible que cierre coaliciones enteras, respete capacidad efectiva de carga y evalue robustez bajo degradacion de comunicacion y perturbaciones de carga.

En ese marco, Smith-QR debe presentarse como una arquitectura de integracion:

1. Smith dynamics como mecanismo distribuido de presion/asignacion.
2. QR/quorum como cierre entero de coaliciones.
3. Grafo de comunicacion como restriccion operacional.
4. Formacion rigida/capacidad wrench como factibilidad fisica.
5. Validacion por escenarios: nominal, escasez, comunicacion degradada, fallo robotico, perturbacion de masa/centro de masa.

## Baselines recomendados

Para que la contribucion sea defendible, la comparacion debe incluir:

- greedy nearest/task dispatching
- centralized min-cost or Hungarian assignment
- CBBA/consensus bundle family
- market/auction allocation if implementable
- MARL proxy or CTDE policy
- nominal consensus/formation control without Smith-QR closure
- oracle/clairvoyant upper bound for context, not as deployable baseline

## Conclusiones

La literatura revisada confirma que el TFM se ubica en una interseccion cientificamente rica y no trivial. Hay suficiente evidencia para justificar una arquitectura distribuida basada en dinamicas de asignacion, pero tambien suficientes brechas para sostener una contribucion propia. La clave argumental es no competir contra toda la literatura de multi-agent systems, sino contra el subproblema especifico: coordinacion distribuida de coaliciones roboticas para transporte de carga bajo restricciones fisicas y comunicacionales.

El siguiente paso metodologico debe ser screening manual de los 174 estudios de alta prioridad, con decision `include`, `exclude` o `mapping_only`, usando los codigos de `screening_criteria.yaml`. Despues de eso, la revision puede convertirse en una matriz final de evidencia y en una seccion LaTeX directamente integrable en la memoria.
