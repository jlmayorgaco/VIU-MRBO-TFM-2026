# Research Question Brief

## Área temática

Arquitectura escalonada para transporte cooperativo de cargas heterogéneas mediante formación de coaliciones basada en juegos sobre grafos, dinámicas poblacionales y control distribuido con información local.

## Pregunta principal

¿Qué efecto tiene incorporar un mecanismo de formación de coaliciones mediante un juego poblacional sobre el grafo de comunicación en el desempeño extremo a extremo de una arquitectura de control distribuido de AMR para cargas heterogéneas, frente a baselines distribuidos SOTA preespecificados y bajo recursos equivalentes?

## Evaluación FINER

| Criterio | Puntuación | Justificación |
|---|---:|---|
| Feasible | 4/5 | Es abordable mediante análisis formal y simulación reproducible; depende de disponer de comparadores equivalentes |
| Interesting | 5/5 | Conecta la decisión de coalición con la ejecución física |
| Novel | 4/5 provisional | La novedad debe confirmarse mediante búsqueda bibliográfica; no se presume |
| Ethical | 5/5 | No involucra personas ni datos sensibles |
| Relevant | 5/5 | Aporta criterios verificables para coordinación distribuida multi-AMR |
| **Media** | **4,6/5** | Supera el umbral FINER |

## Núcleo teórico

¿Bajo qué condiciones sobre el grafo, las funciones de pago y las restricciones de carga converge la dinámica poblacional propuesta a un equilibrio factible y estable de formación de coaliciones de AMR?

## Hipótesis de superioridad falsable

Bajo una distribución de tareas fijada previamente y con idéntica información local, frecuencia de control y presupuestos de cómputo y comunicación, la arquitectura propuesta mejora la probabilidad de completar correctamente el transporte respecto del baseline distribuido elegible de mejor desempeño, sin exceder los márgenes de no inferioridad preespecificados para tiempo, energía y comunicación.

## Regla de decisión

- Variable primaria: proporción de misiones terminadas dentro del tiempo límite, sin pérdida de estabilidad ni violaciones físicas declaradas.
- Superioridad: el límite inferior del intervalo de confianza del efecto pareado debe superar un margen práctico fijado antes del ensayo final.
- Variables secundarias: tiempo, energía normalizada, error de seguimiento, mensajes y reconfiguraciones.
- No inferioridad: ningún deterioro secundario puede superar su margen preespecificado.
- Comparadores: métodos distribuidos verificables y pertinentes, con información y recursos equivalentes.
- Una referencia centralizada solo actuará como cota; no contará como competidor distribuido.
- Superar un baseline débil, una métrica secundaria o un subconjunto post hoc no constituye victoria.

## Alcance

### Incluido

- Formación y reasignación de coaliciones para cargas heterogéneas.
- Grafo de comunicación como restricción de información local.
- Un concepto principal de equilibrio.
- Existencia o caracterización del equilibrio bajo supuestos declarados.
- Convergencia de la dinámica poblacional.
- Interfaz entre asignación basada en juegos y control distribuido.
- Ablaciones, perturbaciones y comparación reproducible.

### Excluido

- Optimalidad universal.
- Superioridad declarada antes de la evidencia.
- Percepción, SLAM y manipulación general.
- Generalización a hardware a partir de simulación.
- Seguridad funcional.
- Aprendizaje automático salvo como comparador necesario y reproducible.

## Subpreguntas

1. ¿Qué supuestos mínimos garantizan existencia, factibilidad y estabilidad del equilibrio seleccionado?
2. ¿Cómo se implementa el juego con información vecinal y qué garantías existen sobre convergencia, comunicación y estabilidad del lazo cerrado?
3. ¿En qué topologías, cargas y fallos se confirma o refuta la regla de superioridad frente a baselines distribuidos verificados?

## Pendientes para Phase 2

- Confirmar la novedad.
- Seleccionar el concepto de equilibrio.
- Congelar clases de grafos y modelo de carga.
- Verificar y seleccionar comparadores SOTA.
- Fijar márgenes prácticos a partir de literatura o piloto independiente.
