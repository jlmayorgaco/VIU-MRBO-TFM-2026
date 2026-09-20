# Codebook V4 para la matriz técnica

Este codebook aplica solo a la revisión técnica anidada. Las señales de título,
resumen, palabras clave o citas sirven para descubrimiento y mapeo, pero no
para rellenar estas columnas.

## Estados comunes

| Estado | Regla |
|---|---|
| `yes` | Hay evidencia explícita que satisface el criterio de la variable bajo supuestos identificados. |
| `partial` | Hay un componente pertinente, pero falta una condición, fase, garantía o alcance material del criterio. |
| `no` | El propio texto afirma explícitamente una exclusión o el método especificado contradice el criterio. La ausencia de mención no basta. |
| `unclear` | No hay texto suficiente, el pasaje es ambiguo, la versión no es accesible o la evidencia no permite decidir. |

Toda fila debe incluir `evidence_id`, `page_or_section`, `excerpt_or_equation`,
`evidence_type` (`full_text`, `appendix`, `supplement`, `author_clarification`),
`confidence` (`high`, `medium`, `low`) y fecha de decisión.

## Variables

| Variable | `yes` | `partial` | Evidencia no admisible |
|---|---|---|---|
| `heterogeneity` | El método modela al menos una capacidad o restricción robot-específica que cambia la selección/ejecución. | Se declaran tipos distintos sin que la decisión dependa de ellos. | Una lista de plataformas o una palabra “heterogeneous” sin mecanismo. |
| `variable_coalition` | El número o composición de miembros se decide o se adapta para una tarea. | El tamaño se parametriza, pero no se selecciona/adapta. | Ejecutar siempre con dos robots o usar “team” como sinónimo de flota. |
| `local_recruitment` | Los miembros se seleccionan mediante estado propio y mensajes/observaciones locales, sin cierre central de la coalición en ejecución. | Negociación entre pares con una precondición o árbitro global material. | Control local posterior a una asignación global. |
| `shared_load_transport` | Dos o más robots aplican de forma cooperativa acciones de soporte, tracción, empuje o manipulación sobre la misma carga. | La carga es una tarea o recurso abstracto, o los robots no comparten la acción física. | Movimiento simultáneo sin objeto compartido. |
| `physical_feasibility_certificate` | Una prueba o restricción explícita de geometría, contacto, `wrench`, fricción, actuación o confinamiento puede aceptar/rechazar una coalición. | Hay límites físicos o simulación, pero no un certificado que condicione la decisión. | Suma nominal de capacidades, masa declarada o éxito visual sin prueba. |
| `local_execution_authority` | La ley de ejecución usa estado propio y vecinos y no requiere autoridad global en tiempo de ejecución. | Hay líder, maestro, referencia global, planificador remoto o fases local/global mezcladas. | Describir la planta como multi-robot sin declarar autoridad. |
| `failure_recovery` | El método detecta/gestiona una perturbación o fallo y define una acción de recuperación o aborto seguro. | Se discute robustez, replanificación o tolerancia sin ciclo de recuperación demostrado. | Mencionar “fault tolerant” sin mecanismo verificable. |
| `member_replacement` | Un miembro fallido puede ser sustituido mediante selección, llegada y revalidación documentadas. | Se permite reconfiguración o reasignación sin sustitución operacional completa. | Abandonar la misión, volver a ejecutar un algoritmo sin miembro de reemplazo o ausencia de mención. |

## Regla de evidencia y agregación

La agregación “un trabajo cubre X” usa solo celdas `yes` o `partial` con el
denominador de celdas realmente evaluadas. `unclear` y acceso no disponible se
reportan por separado. Ninguna figura suma automáticamente `partial` como
`yes`: una variante de sensibilidad puede hacerlo, pero debe etiquetarse como
tal. La evidencia de un trabajo no se transfiere a sus coautores, a una familia
de métodos ni a una versión distinta sin verificar continuidad.
