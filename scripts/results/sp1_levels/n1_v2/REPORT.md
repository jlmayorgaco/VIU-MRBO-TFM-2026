# SP1.N1 — campaña confirmatoria húngara homogénea

- Campaña: `SP1_N1_HUNGARIAN_CONFIRMATORY_v2`.
- Filas RAW: 12,630.
- Mundos de calidad: 4,500.
- Ahorro mediano frente a greedy: 6.53% (IC 95% 6.34–6.71%).
- Escenarios que superan el gate del 5% tras Holm: 3/5.
- Sensibilidad Wilcoxon: misma clasificación que el gate confirmatorio de signo.
- Control de orden del greedy: mediana agregada 3.76% con orden aleatorizado; clasificación inalterada.
- Pendiente log-log balanceada observada: 2.402 (IC 95% 2.365–2.435).
- Concordancia recuperación–frontera cardinal: 100.00% (identidad de implementación, no un hallazgo estadístico).
- Coste óptimo posterior estrictamente mayor en 99.73% de los 3,000 recálculos factibles con retirada.
- Falsos factibles con heterogeneidad extrema: 97.67%.
- MILP entre los falsos factibles: 900 con asignación factible y 897 con óptimo certificado, de 900.
- Certificado de cardinalidad: se cumple en 300 mundos, con 0 falsos factibles.
- Tendencia GEE de falso factible sobre CV: beta1=8.578 (IC 95% 7.463–9.693).

## Alcance

- El Húngaro es exacto únicamente para la reducción homogénea a slots.
- Las regresiones describen el rango medido; no prueban complejidad asintótica.
- El fallo se resuelve mediante un recálculo central estático.
- La comparación con el MILP heterogéneo muestra por qué N2 debe conservar la capacidad individual.
