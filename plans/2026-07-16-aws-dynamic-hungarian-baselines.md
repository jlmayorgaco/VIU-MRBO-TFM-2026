# Piloto dinámico Hungarian--greedy--random en almacén AWS

## Propósito y resultado observable

Construir un experimento reproducible de asignación dinámica uno-a-uno sobre el layout industrial AWS existente. En cada periodo de decisión se comparará la asignación húngara centralizada con greedy y random factible, conservando el destino propio de cada carga. El resultado incluirá trazas CSV, figuras y un MP4 comparativo.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` y `docs/02_RESEARCH_MATRIX.md`: el piloto pertenece a SP0 como baseline de asignación uno-a-uno.
- `docs/03_EXPERIMENT_PROTOCOL.md`: semillas pareadas, datos crudos y métricas reproducibles.
- `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py`: geometría y entidades del escenario industrial.
- `tmp/scripts/coppelia/benchmark_sp0_dispatch.py`: motor cinemático y coste de despacho ya existente.

## Alcance y no alcance

Incluye reasignación periódica, factibilidad energética, batería, posiciones de AMR/cargas, destinos fijos, comparación pareada y animación. No modela coaliciones de dos o tres AMR, wrench/contacto, percepción, comunicación imperfecta ni garantía de trayectorias libres de colisión.

## Supuestos y preguntas resueltas

- Cada carga activa se reduce a una tarea indivisible atendida por un AMR; por ello Hungarian es un baseline exacto válido en este piloto.
- Las cargas de cola se excluyen del piloto inicial; la extensión con cardinalidad/capacidad requerirá MILP o set partitioning.
- El algoritmo se ejecuta cada periodo digital de reasignación, no en tiempo continuo.
- El destino de cada carga permanece fijo durante todos sus ciclos.

## Diseño matemático/técnico

Para robot `i` y carga `j`, el coste combina distancia al despacho, trayecto despacho--destino, retorno a base y penalización de batería. Los pares que no conservan la reserva energética son infactibles. Hungarian minimiza la suma con máxima cardinalidad; greedy selecciona iterativamente el par factible de menor coste; random genera un matching factible uniforme condicionado al orden aleatorio.

## Plan experimental

- Escenario: cuatro cargas activas y cuatro destinos fijos del almacén AWS industrial.
- Políticas: Hungarian, greedy y random factible.
- Semillas pareadas: configurables; piloto inicial de humo y campaña corta.
- Métricas: entregas, espera, distancia, energía, ciclos de carga, coste acumulado y regret instantáneo respecto a Hungarian.
- Evidencia visual: trayectorias, batería, objetivo/regret y MP4 sincronizado de las tres políticas.

## Hitos

- [x] Hito 1 — motor admite random factible, objetivos fijos y traza de cargas.
- [x] Hito 2 — runner AWS y configuración versionada generan CSV/PNG/MP4.
- [x] Hito 3 — pruebas y campaña piloto verificadas.
- [x] Hito 4 — variante replicadora usa consenso vecinal muestreado y registra conectividad, desacuerdo y mensajes.
- [x] Hito 5 — comparación de cuatro políticas y MP4 regenerados con semillas pareadas.

## Validación

- Prueba unitaria de cardinalidad, unicidad y factibilidad de los tres matchings.
- Prueba de que `target` no cambia al reaparecer una carga.
- Experimento de humo con dos semillas y horizonte reducido.
- Verificación con `ffprobe` del códec, duración y resolución del MP4.

## Riesgos y mitigaciones

- Riesgo de presentar Hungarian como solución de coaliciones: rotular explícitamente el alcance SP0 uno-a-uno.
- Riesgo de confundir animación cinemática con validación física: conservar limitación en manifiesto y reporte.
- Riesgo de sesgo estocástico: usar semillas pareadas y publicar resultados por semilla.

## Registro de decisiones

- 2026-07-16: se reutiliza el motor de despacho existente y se adapta al layout AWS para evitar duplicar métricas.
- 2026-07-16: se limita a cuatro cargas activas porque la demanda multi-AMR pertenece a SP1--SP3 y requiere otro oráculo.
- 2026-07-17: la extensión replicadora se define como dinámica distribuida dentro de cada componente del grafo por radio; el cierre entero se realiza mediante aceptación local de una propuesta por carga. No se afirmará consenso global si el grafo está desconectado.

## Progreso

Se completó la ampliación. En ocho semillas, Hungarian y greedy entregaron 10 cargas, replicator 9,75 y random 8. Replicator redujo el desacuerdo intracomponente medio de 0,02455 a 0,000906, operó con 3,42 componentes y transmitió 7.612,5 escalares por ejecución. Las tres pruebas pasan; 128/128 grupos carga--política--semilla conservaron un único destino. El MP4 H.264 final contiene cuatro paneles, 161 cuadros y resolución 2520x636. La evidencia sigue siendo descriptiva SP0: no demuestra consenso global, coaliciones ni path planning seguro.
