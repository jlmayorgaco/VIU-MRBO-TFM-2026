# SP4 v4 — trazabilidad de revisión

Ronda: 1
Fecha de cierre: 2026-07-13

| Objeción exigente | Cambio aplicado | Evidencia verificable | Estado |
|---|---|---|---|
| La geometría v3 contenía puertos físicamente inalcanzables. | Auditoría geométrica previa y escenarios v4 reparados para N=4, 8 y 12. | `test_v3_invalid_geometry_is_detected_and_v4_is_repaired`; auditoría JSON confirmatoria. | Cerrado |
| Un residual HOCBF continuo podía confundirse con seguridad discreta. | Se separaron residual ejecutado y clearance barrido; se documentó el contraejemplo de penetración de 5,68 mm del baseline directo. | Sección 9.11 y CSV confirmatorio. | Cerrado como limitación, no como garantía |
| Replicator por Euler violaba simplex/capacidad transitoriamente. | Paso espejo entrópico y proyección local exacta de capacidad después de cada revisión. | Tests de simplex/capacidad; violación máxima confirmatoria 2,22e-16. | Cerrado |
| La factibilidad del juego no garantizaba vivacidad en pasos estrechos. | Dueño persistente, admisión por color, prioridad a puertos de menor holgura y replanificación por fase. | 12/12 éxitos seguros por método propuesto; stress N=12 en seis escenarios. | Cerrado empíricamente |
| Comparar solo con greedy/local era insuficiente. | Cinco métodos pareados: directo, prioridad local, central enumerativo, replicator distribuido y primal-dual distribuido, todos con el mismo HOCBF. | 60 ejecuciones confirmatorias y pruebas exactas pareadas. | Cerrado para simulación N=4 |
| La superioridad podía estar sobrerreclamada. | Se reportan p=0,003906 frente a locales, p=0,125 frente a central y empate PD/replicator. | Sección 9.11 y reporte confirmatorio. | Cerrado |
| Faltaba separar desarrollo de confirmación. | YAML de desarrollo y YAML confirmatorio congelado con dos semillas nuevas. | Carpetas de resultados y auditoría de 60 claves únicas. | Cerrado |
| Faltaba honestidad sobre madurez robótica. | Se ejecutó una escena pareada en el motor real de CoppeliaSim y se delimitó como reproducción cinemática, no como dinámica independiente ni hardware. | Escena `.ttt`, 29 capturas, CSV medido y sección 9.11.1. | Parcialmente cerrado |
| La evidencia multi-semilla y de escala es limitada. | Se separó el stress N=12 del contraste N=4 y se evitó tratarlo como evidencia estadística. | Texto metodológico y resultados. | Abierto |

## Veredicto de la ronda

SP4 v4 queda defendible como contribución teórico-computacional, demostración numérica y validación geométrica visual en CoppeliaSim. No queda certificado como solución robótica general ni como capítulo 10/10 hasta ampliar semillas, implementar un baseline ORCA real y validar un lazo dinámico independiente o hardware.
