# Auditoría de implementación SP1.N4

## Estado anterior a esta revisión

La rama F-I ya disponía de Geo-QPG, vecindades BR/2BR/C3, revisiones ASR/LLL,
conflict graph, DMIS, transacciones versionadas, DPOP pequeño y campañas E4–E6.
F-II reutilizaba resultados históricos de masa divisible, pero no compartía el
modelo N4 ni producía una asignación física. F-III aparecía como formulación sin
algoritmo ni residuos. F-IV figuraba como extensión futura. La memoria lo decía
de manera explícita; por tanto, no existía aún una comparación de familias.

## Implementación incorporada

### Núcleo continuo y cierre común

`src/viu_mrob_tfm/sp1_n4/continuous.py` contiene:

- normalización única de capacidad y distancia;
- potencial y fitness común de F-II;
- Replicator, Smith, BNN y Logit;
- referencia con agregado exacto y ejecución distribuida con DAC;
- proyección vectorizada al símplex e invariantes numéricos;
- referencia vGNE central regularizada;
- algoritmo primal–dual distribuido con DAC y consenso dual;
- residuos primal, dual, de complementariedad, estacionariedad, consenso y KKT;
- operador `atomic_closure`, compartido por F-II y F-III.

El cierre reutiliza la recuperación aumentante determinista del módulo histórico
de N4. Prioriza las intenciones de `x`, limita longitud, candidatos y nodos
explorados, y devuelve métricas de recuperación. Es heurístico y no sustituye al
MILP.

### Extensión temporal

`src/viu_mrob_tfm/sp1_n4/stochastic.py` define una secuencia canónica de
llegadas, terminaciones y fallos, dos políticas Geo-QPG y un oráculo dinámico
central de horizonte finito para `N` pequeño. El modelo no incluye movimiento,
batería continua ni transición aprendida.

### Cambios de interfaz y pruebas

`run_geo_qpg` acepta una asignación inicial validada para permitir warm start.
Las nuevas pruebas cubren derivada del potencial, símplex, soporte, cierre,
KKT, consenso, reproducibilidad de eventos, factibilidad atómica y cota del
oráculo dinámico. La batería se mantiene separada en:

- `tests/test_sp1_n4_continuous.py`;
- `tests/test_sp1_n4_stochastic.py`.

## Campañas

La configuración `experiments/configs/sp1_n4_cross_family_v3.yaml` congela E7
estática y E8 dinámica. `scripts/sp1_n4_cross_family.py` genera datos RAW,
procesados, figuras PDF/PNG, macros LaTeX y manifiesto. E7 conserva los 1.200
mundos de E4 y E8 usa 30 mundo–semilla nuevos. El detalle estadístico se define
en `docs/reviews/CROSS_FAMILY_PROTOCOL.md`.

## Riesgos no resueltos

1. La integración digital de F-II/F-III es una aproximación del campo continuo.
2. DAC supone un grafo estático, no dirigido y conectado en E7.
3. No existe una prueba aplicada de convergencia global del algoritmo F-III.
4. El cierre puede fallar aunque exista una solución MILP.
5. Los bytes son contadores del modelo de mensajes, no capturas de una red.
6. F-IV usa conocimiento perfecto del futuro solo en el oráculo central.
7. Ninguna de estas campañas valida acoplamiento o transporte de SP2.

## Criterio de aceptación

La ampliación es apta para la memoria cuando: pasan los tests; la campaña
completa produce RAW y hashes; los residuos se reportan aunque fallen; los
gráficos se leen en A4; el texto no convierte evidencia numérica en teoremas; y
F-IV permanece fuera de la tabla estática.
