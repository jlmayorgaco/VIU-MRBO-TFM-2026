# Revision focal: transporte cooperativo distribuido de cargas en sistemas multi-robot

## Alcance

Esta nota focaliza la revision sistematica en el tema exacto del TFM: transporte cooperativo distribuido de cargas por multiples robots moviles, con interes especial en AGVs/AMRs, coaliciones, comunicacion limitada, formacion rigida, restricciones de payload y asignacion distribuida.

La busqueda se hizo sobre la base local `literature.sqlite`, filtrando registros de prioridad alta/media que contienen senales directas de `cooperative transport`, `payload`, `load transport`, `object transport`, `box transport`, `cooperative manipulation`, `multi-robot manipulation`, `carrying` o `transporting`.

## Resultado cuantitativo focal

| Medida | Valor |
|---|---:|
| Registros focales transporte/carga | 91 |
| Alta prioridad | 35 |
| Prioridad media | 56 |
| Categoria dominante | `cs.RO` (66 registros) |
| Periodo con mayor densidad | 2021-2026 |

Terminos mas frecuentes:

| Termino | Registros |
|---|---:|
| payload | 43 |
| cooperative transport | 16 |
| object transport | 13 |
| carrying | 13 |
| transporting | 12 |
| cooperative transportation | 9 |
| object transportation | 8 |
| load transport | 7 |
| cooperative manipulation | 7 |
| collaborative transport | 6 |
| multi-robot manipulation | 5 |

La concentracion reciente es clara: 2024, 2025 y 2026 contienen la mayor parte de los registros relevantes. Esto indica que el tema esta activo y que el TFM no esta atacando un problema agotado.

## Lectura cientifica del subcampo

### 1. El transporte cooperativo de cargas es un problema acoplado

La literatura focal confirma que el transporte cooperativo de cargas no se resuelve solo con asignacion ni solo con control. Los trabajos relevantes combinan, con distinto grado de integracion:

- seleccion de tarea u objeto;
- seleccion de robots o coalicion;
- restricciones de peso, payload, energia o capacidad;
- posicionamiento relativo de robots;
- soporte, empuje, cable, manipulacion o carga compartida;
- planificacion de trayectoria;
- control distribuido o semi-distribuido;
- comunicacion limitada o event-triggered;
- robustez ante incertidumbre, obstaculos o fallos.

Este hallazgo es central para el TFM: el problema real esta entre MRTA y cooperative manipulation. Si el algoritmo solo asigna robots a cargas, queda incompleto; si solo controla una formacion ya dada, tambien queda incompleto.

### 2. Hay tres familias principales

#### A. Transporte cooperativo con control/formacion

Incluye trabajos sobre payload transportation, box transport, cable-suspended payloads, object transportation y cooperative manipulation. Estos trabajos son los mas fisicos: modelan objeto, masa, geometria, fuerzas, restricciones cinematicas o formaciones.

Valor para el TFM: justifican el uso de capacidad efectiva, wrench, formacion rigida y restricciones fisicas de carga.

Limite: muchos presuponen que la coalicion ya esta formada o que el numero de robots participantes esta dado.

#### B. Task allocation / MRTA para cargas

Incluye task allocation para objetos con pesos desconocidos, payload consumption, multi-object transportation, pickup-and-delivery, assembly planning y warehouse/logistics. Estos trabajos son los mas cercanos a la capa de asignacion.

Valor para el TFM: dan baselines y vocabulario para asignacion dinamica, coaliciones, tareas con demanda y restricciones de capacidad.

Limite: con frecuencia no cierran la factibilidad fisica de la carga. Asignan robots, pero no siempre demuestran que la configuracion pueda transportar establemente.

#### C. Aprendizaje y politicas jerarquicas

Incluye MARL, graph reinforcement learning, hierarchical distributed policies y event-triggered communication/control. Estos trabajos buscan adaptabilidad ante numero variable de robots/objetos, incertidumbre y comunicacion.

Valor para el TFM: sirven como comparadores modernos y muestran que la estructura jerarquica importa.

Limite: menor interpretabilidad y mayor dependencia de entrenamiento, escenarios y generalizacion.

## Estudios focales mas relevantes

| arXiv | Ano | Por que importa |
|---|---:|---|
| 2212.02692 | 2022 | Task allocation para transporte cooperativo de multiples objetos con pesos desconocidos; combina prioridad global y politica distribuida. |
| 2404.02362 | 2024 | Politicas jerarquicas distribuidas para transporte cooperativo adaptativo; relevante para capa task/control. |
| 2404.11817 | 2024 | MRTA para transporte multi-objeto con tareas inviables; cercano a quorum/capacidad insuficiente. |
| 2412.10087 | 2024 | Consensus-Based Payload Algorithm; muy cercano a asignacion dinamica con consumo/capacidad de payload. |
| 2303.08933 | 2023 | MRTA-Collective Transport con GNN y descriptores topologicos; fuerte para escalabilidad y topologia. |
| 2311.00192 | 2023 | Planning stack para manufactura multi-robot; integra asignacion, equipos, transporte y configuracion geometrica. |
| 2605.26430 | 2026 | Box transport descentralizado por roles; muy cercano a cargas rectangulares y control local. |
| 2502.13366 | 2025 | Transporte cooperativo de payload para robots no holonomicos con restricciones escalables. |
| 2606.09610 | 2026 | Formacion para transportar objetos arbitrarios con MARL; relevante para geometria y centro de masa. |
| 2306.12331 | 2023 | Transporte/manipulacion descentralizada de payload suspendido por enjambre aereo; relevante como variante fisica. |
| 2503.19135 | 2025 | Quadrotors con payload suspendido, planificacion y NMPC; util como contraste de control avanzado. |
| 1810.00522 | 2018 | Transporte colaborativo descentralizado de telas con micro-UAVs; muestra manipulacion flexible. |
| 2209.05556 | 2022 | Transporte de objeto fragil con control semi-descentralizado y formacion. |
| 2603.06356 | 2026 | Cooperative manipulation con event-triggered CBF; conecta seguridad, consensus y manipulacion. |
| 2008.00679 | 2020 | Stackelberg learning para cooperative object transportation; puente game theory + aprendizaje. |

## Brecha exacta para Smith-QR

La brecha fuerte no es "faltan algoritmos de transporte cooperativo". Si existen. La brecha es mas especifica:

> Faltan arquitecturas distribuidas que unan asignacion por escasez, cierre entero de coaliciones, comunicacion limitada y factibilidad fisica de carga en un mismo bucle reproducible.

La literatura suele partirse asi:

- MRTA decide quien hace que, pero no siempre modela wrench/carga/formacion.
- Formation/control mueve una carga, pero suele asumir que el equipo ya esta elegido.
- Game theory/markets asignan recursos, pero no siempre traducen payoff a capacidad fisica.
- MARL aprende politicas, pero pierde interpretabilidad y requiere entrenamiento.
- Cooperative manipulation controla contacto/fuerzas, pero no siempre escala a warehouse/logistics con muchas tareas.

Smith-QR puede posicionarse justo en esa interseccion.

## Como debe formularse nuestro aporte

Una formulacion defendible:

> Proponemos una arquitectura distribuida para transporte cooperativo multi-AGV en la que una dinamica tipo Smith captura presion de asignacion bajo escasez, mientras un cierre QR/quorum transforma preferencias distribuidas en coaliciones enteras fisicamente factibles. La factibilidad no se define solo por asignacion, sino por capacidad efectiva, geometria/formacion, comunicacion disponible y robustez ante perturbaciones.

Esto conecta cuatro capas:

1. **Capa economico-distribuida:** deficit, precios, fitness, Smith dynamics.
2. **Capa discreta:** cierre entero, quorum, coalicion minima.
3. **Capa grafica:** vecinos, conectividad, comunicacion degradada.
4. **Capa fisica:** carga, masa, centro de masa, wrench, formacion rigida.

## Hipotesis literaria que podemos defender

H1. La literatura de cooperative transport muestra que payload y geometria no pueden tratarse como detalles secundarios.

H2. La literatura MRTA muestra que asignacion distribuida es necesaria para escalabilidad, pero insuficiente sin cierre fisico.

H3. La literatura de graph theory/control distribuido ofrece herramientas para comunicacion y formacion, pero requiere adaptacion a cargas heterogeneas.

H4. La literatura de game theory/market dynamics justifica el uso de dinamicas de seleccion/asignacion, pero necesita una traduccion fisica del payoff.

H5. Los metodos MARL/GNN son baselines relevantes, pero Smith-QR puede defenderse por interpretabilidad, bajo costo y trazabilidad.

## Baselines especificos para nuestro tema

Para transporte cooperativo de cargas, no basta comparar contra un greedy generico. Los baselines adecuados son:

- Greedy nearest / dispatching por distancia.
- Hungarian/min-cost centralizado.
- CBBA o consensus bundle allocation.
- Algoritmo de payload/task allocation tipo CBPA, si se implementa una version simplificada.
- MARL proxy o CTDE para task allocation.
- Formation/control nominal con coalicion fija.
- Oracle de asignacion con conocimiento completo, solo como cota superior.

## Variables que debe extraer la revision manual

Para cada paper focal, conviene extraer:

- tipo de carga: caja, objeto rigido, payload suspendido, objeto fragil, carga generica;
- modo fisico: empuje, soporte superior, cable, manipulacion, transporte por formacion;
- robots: AGV/AMR, UAV, manipuladores, cuadrupedos, equipos heterogeneos;
- decision: task allocation, coalition formation, path planning, control, all-stack;
- comunicacion: centralizada, local, broadcast, event-triggered, limitada, desconocida;
- factibilidad: peso, payload, wrench, geometria, energia, tiempo, colision;
- validacion: simulacion, hardware, benchmark, teorema, codigo;
- escalabilidad: numero de robots, numero de tareas/objetos, runtime;
- relacion con TFM: baseline, marco teorico, gap, evidencia fisica o comparador.

## Conclusion focal

Nuestro tema esta bien respaldado, pero no saturado. Hay literatura suficiente para construir una revision seria y para definir baselines, pero todavia existe una brecha defendible: integrar asignacion distribuida, coaliciones enteras y factibilidad fisica de cargas bajo comunicacion limitada. Esa es exactamente la zona donde Smith-QR puede tener una contribucion clara.

La revision amplia demuestra que multi-agent/distributed control es un campo enorme. La revision focal muestra que el subproblema relevante para el TFM es mas estrecho y mas interesante: **distributed cooperative load transport with coalition closure and physical feasibility**.
