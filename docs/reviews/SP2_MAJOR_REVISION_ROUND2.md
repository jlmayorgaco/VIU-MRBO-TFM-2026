# SP2 — respuesta a la revisión multidisciplinar, ronda 2

Fecha: 2026-08-20  
Entregable: `output/pdf/SP2_HONORS_VIU.pdf`

## Dictamen

Las objeciones que podían resolverse sin inventar evidencia quedaron
incorporadas. SP2 conserva un núcleo Cargo cuantitativo y auditable, reduce la
arquitectura no ejecutada a transferencia instrumentable y explicita los
resultados negativos. No se declara una calificación garantizada, autoría sin
asistencia ni un resultado Turnitin.

## Matriz de respuesta

| Observación | Estado | Respuesta aplicada |
|---|---|---|
| Dependencia entre siete escenarios N4 | Resuelta | Bootstrap de 5.000 remuestras sobre 30 bloques de semilla completos; los escenarios no se tratan como réplicas independientes. |
| Procedencia de tuning | Resuelta con limitación | Selección de ingeniería no optimizada, fijada antes de las semillas; se declara la ausencia de conjunto disjunto, log de búsqueda y optimización independiente. |
| Claim universal de literatura | Resuelta | El alcance se limita a los enfoques resumidos en la Tabla 1. |
| “LP polinómico” frente a SLSQP | Resuelta | La Tabla 1 distingue optimización vertical restringida y LP tangencial; el texto explica por qué la implementación reutiliza SLSQP sin reclamar ventaja algorítmica. |
| Coste del reparto normal secuencial | Resuelta | Se advierte que otro reparto normal factible podría admitir un wrench rechazado por la sección secuencial. |
| Monotonías y dispersión | Resuelta | La geometría se presenta como tensión análoga, no como validación experimental de retirar miembros. |
| Inflación de lemas/proposiciones | Resuelta | Se eliminó el lema trivial y la capacidad escalar quedó como contraejemplo en prosa. |
| RBPF/pose graph dentro de resultados | Resuelta de forma conservadora | Se eliminaron las ecuaciones no ejecutadas; se conserva media página larga con Figura 5 y protocolo de transferencia, porque el extracto SP2 debe ser autónomo y el autor pidió explícitamente explicar SLAM. |
| Caging sobredimensionado | Resuelta | Una sola página comparte certificado discreto, figura y límite dinámico; se eliminó la ecuación dinámica unilateral. |
| Cita Lee/Rosenfelder/DMPC | Resuelta | Lee respalda conmutación MILP--QP, Rosenfelder medida/control de fuerzas y DMPC queda como posible extensión no ejecutada. |
| Atribución inmediata de ecuaciones estándar | Resuelta | Matriz de agarre, RBPF, grafo relativo, LQR, MPC, CBF y caging se vinculan a fuentes en su primera aparición técnica. |
| Explicación para no especialista | Resuelta | Se añadieron `Resultado N1`--`Resultado N4`, definición de wrench y una explicación operativa SP1→SP2. |
| Originalidad poco explícita | Resuelta | El inicio separa herramientas conocidas de la contribución propia: composición de capas y cuantificación de falsos positivos. |
| Por qué cuatro AMR | Resuelta | Cuatro apoyos en las esquinas permiten conservar tres contactos tras una pérdida; no se interpreta como estudio de escalado. |
| Por qué 30 semillas | Resuelta con limitación | Presupuesto computacional fijado antes del análisis, sin cálculo prospectivo de potencia; la precisión se informa mediante IC por bloques. |
| Figura 10 pequeña | Resuelta | Dos bandas horizontales separan misión nominal y recuperación; `LIBERAR` permanece discontinuo y pendiente. |
| Párrafos breves y AI-smell | Resuelta parcialmente | Se fusionaron fragmentos, se eliminaron muletillas defensivas y se variaron las transiciones. No se rellenó para imponer tres oraciones: esa supuesta regla literal no aparece en los requisitos VIU locales consultados. |
| Referencias APA/software | Verificadas localmente; revisión independiente pendiente | Las 21 citas pasaron resolución DOI/arXiv/manual, metadatos y contexto. El revisor fresco no emitió dictamen y el artefacto conserva `ERROR` procedimental en vez de simular un `PASS`. |

## Verificación

- Batería conjunta: **34 passed**.
- Compilación autónoma: **PASS**, 20 páginas.
- Búsqueda textual: sin claims antiguos, metarreferencias de IA ni avisos de
  citas/referencias indefinidas o cajas `Overfull`.
- Render Poppler: 20 páginas inspeccionadas; sin solapes. Las Figuras 1, 5, 8,
  10, 11 y 12 son legibles y las páginas 11--13 no contienen líneas viudas.

## Limitaciones residuales

No se ejecutaron SLAM multi-AMR, calibración de fuerzas, docking físico,
liberación, contacto 3D ni hardware. Tampoco existe una campaña de ajuste
disjunto, cálculo prospectivo de potencia, sensibilidad temporal ni una huella
versionada que reconstruya con certeza el código que produjo los datos crudos
N4. Los hashes añadidos sirven para detectar cambios posteriores, no para
resolver retrospectivamente esa trazabilidad.
