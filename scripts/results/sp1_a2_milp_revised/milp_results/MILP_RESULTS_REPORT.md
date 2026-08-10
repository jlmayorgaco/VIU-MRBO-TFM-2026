# SP1.A2 — resultados autónomos del MILP heterogéneo

Este directorio analiza únicamente el oráculo MILP con capacidades individuales escalares. No contiene métricas ni curvas Hungarian.

## Indicadores globales

- Perfil de la fuente: `quick`.
- Ejecuciones: 3,420.
- Misiones factibles: 2,344 (68.5%).
- Optimalidad certificada: 1,531 (44.8%).
- Tiempo de solver mediano: 1687.734 ms; P95: 5088.969 ms.

## Cobertura por estudio

| Estudio | Filas | Factibles | Óptimos certificados |
|---|---:|---:|---:|
| scaling | 1,560 | 57.3% | 44.0% |
| balance | 780 | 54.0% | 44.9% |
| asymmetry | 500 | 100.0% | 40.8% |
| failures | 480 | 89.4% | 46.9% |
| capacity | 100 | 100.0% | 65.0% |

## Interpretación correcta

La factibilidad indica que todas las cargas reciben capacidad escalar suficiente con exclusividad robot--carga. No demuestra soporte mecánico, reparto de wrench, navegación, estabilidad ni transporte físico.

Las pendientes y regresiones mostradas en las figuras son descriptivas del dominio muestreado. No son pruebas de complejidad asintótica ni resultados confirmatorios.

La capacidad solicitada informalmente como `q_i` se reporta en la memoria como `c_i^{pay}`, porque `q_i` ya está reservado para el estado del robot en la notación canónica.
