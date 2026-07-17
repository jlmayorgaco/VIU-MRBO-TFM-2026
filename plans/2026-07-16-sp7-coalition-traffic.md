# SP7: tráfico multicoalición sobre recursos compartidos

## Propósito y resultado observable

Convertir SP7 de propuesta futura en un estudio exploratorio reproducible de nivel C. El resultado observable es una formulación limitada de juego potencial para selección de rutas, una política local de reserva con prioridad y envejecimiento, una campaña pareada de tráfico, tablas y figuras generadas, y una sección de memoria que separa equilibrio estratégico, ejecución discreta y seguridad física.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`. SP7 hereda de SP5 la huella rígida conservadora y de SP6 la condición de coalición recuperada, pero no reabre contacto, wrench ni rereclutamiento. El material histórico `results/sp7/SP7_MC_communication_robustness_*` estudia red, no tráfico, y queda excluido de la evidencia canónica.

## Alcance y no alcance

Incluye cruces, pasillo bidireccional y cuello de botella dinámico para dos a cuatro cuerpos compuestos; rutas discretas precomputadas; reserva vecinal de una zona de conflicto; oráculo exhaustivo restringido; planificación priorizada; dos ablaciones y semillas pareadas. No incluye CBS/ECBS u ORCA ejecutados, dinámica continua de contacto, percepción, paquetes perdidos, múltiples cargas por coalición ni una prueba general de ausencia de colisiones o deadlock industrial.

## Diseño matemático y técnico

El jugador es una coalición y su acción es una ruta de un catálogo finito. El potencial es el negativo del coste base más una penalización por pares de rutas que usan el mismo recurso: `Phi_7=-sum b_ar-lambda_7 sum_e binom(n_e,2)`. La utilidad individual carga su coste base y sus pares de congestión; por ello cada desviación unilateral reproduce exactamente la variación de `Phi_7`. La mejor respuesta estricta termina en Nash por finitud. La ausencia de conflictos en todo Nash solo se enuncia bajo una condición adicional de accesibilidad y dominancia de la penalización.

La ejecución usa un token local por zona, prioridad con envejecimiento, exclusión de vértice y prohibición de intercambio de aristas. La salida estratégica es el número de pares de rutas en conflicto; la salida ejecutiva es entrega, espera y bloqueo. La reserva no sustituye el filtro físico de SP5.

## Plan experimental ejecutado

Escenarios: cruce, pasillo bidireccional y cuello de botella con ocupación dinámica. Factores: 2, 3 y 4 coaliciones, 40 semillas. Métodos: juego y reserva local; ablación sin penalización de congestión; ablación sin reserva de zona; planificación priorizada y oráculo exhaustivo restringido. Se generaron 360 mundos y 1800 ejecuciones pareadas.

## Hitos

- [x] Hito 1 — fuentes canónicas, SP7 heredado y literatura auditados.
- [x] Hito 2 — teoría y pruebas unitarias implementadas.
- [x] Hito 3 — simulador, baselines y experimento de humo verificados.
- [x] Hito 4 — campaña confirmatoria y auditoría reproducible completadas.
- [x] Hito 5 — memoria, anexo, notación y trazabilidad sincronizados.
- [x] Hito 6 — PDF compilado y revisado visualmente.

## Validación final

- `python -m pytest tests/test_sp7_traffic.py -q`: 8 pruebas superadas.
- Continuidad SP5--SP7: 15 pruebas superadas.
- Campaña `SP7_TRAFFIC_CONFIRMATORY_v1`: auditoría aprobada, 360 hashes de mundo y cinco métodos por mundo.
- Compilación integral: `thesis/build/main.pdf`, 145 páginas; SP7 ocupa las páginas 103--108 y sus pruebas las páginas 144--145.
- Inspección visual: final de SP7 y transición a SP8 sin página residual; tablas y figuras legibles.

## Resultados y límites

La política local entregó 360/360 mundos y redujo el makespan truncado en 4 pasos frente a la ablación sin penalización de congestión. Retirar la reserva redujo la entrega en 26,1 puntos porcentuales y produjo deadlock en pasillos opuestos. El oráculo restringido fue 1,153 pasos más rápido en makespan. La condición suficiente de Nash sin conflictos se cumplió solo en los 120 mundos de cruce: el resultado negativo se conserva y limita el alcance del teorema.

Los cero conflictos lógicos observados proceden del ejecutor discreto y no demuestran seguridad física continua. El oráculo es exacto únicamente dentro del catálogo de rutas y prioridades. La red es perfecta; retardo, pérdida, bytes y escalabilidad pertenecen a SP8.

## Registro de decisiones

- 2026-07-16: usar un juego de rutas con penalización por pares, porque conserva potencial exacto sin asumir jugadores ponderados.
- 2026-07-16: ejecutar un oráculo exhaustivo restringido en vez de llamarlo CBS; CBS/ECBS y ORCA quedan como contexto verificado pero no reproducido.
- 2026-07-16: representar la huella mediante inflación del grafo e intervalo de despeje, documentando que es una abstracción cinemática.
- 2026-07-16: mantener como resultado negativo los escenarios donde la condición suficiente no se satisface y usar la reserva como segunda capa ejecutiva.

## Progreso

Plan completado. La evidencia, el código, las pruebas, la memoria, el anexo matemático y el PDF están sincronizados. El siguiente riesgo ya no es SP7, sino el exceso de extensión global de la memoria y la validación de red imperfecta de SP8.
