# SP1.N1 — campaña confirmatoria húngara homogénea

- Campaña: `SP1_N1_HUNGARIAN_CONFIRMATORY_v2_SMOKE`.
- Filas RAW: 38.
- Mundos de calidad: 10.
- Ahorro mediano frente a greedy: 5.64% (IC 95% 4.87–7.54%).
- Escenarios que superan el gate del 5% tras Holm: 0/5.
- Sensibilidad Wilcoxon: misma clasificación que el gate confirmatorio de signo.
- Control de orden del greedy: mediana agregada 3.75% con orden aleatorizado; clasificación alterada; requiere discusión.
- Pendiente log-log balanceada observada: 1.527 (IC 95% 1.041–2.089).
- Concordancia recuperación–frontera cardinal: 100.00% (identidad de implementación, no un hallazgo estadístico).
- Coste óptimo posterior estrictamente mayor en 50.00% de los 2 recálculos factibles con retirada.
- Falsos factibles con heterogeneidad extrema: 75.00%.
- MILP entre los falsos factibles: 5 con asignación factible y 5 con óptimo certificado, de 5.
- Certificado de cardinalidad: se cumple en 4 mundos, con 0 falsos factibles.
- Tendencia GEE de falso factible sobre CV: beta1=5.195 (IC 95% -0.330–10.719).

## Alcance

- El Húngaro es exacto únicamente para la reducción homogénea a slots.
- Las regresiones describen el rango medido; no prueban complejidad asintótica.
- El fallo se resuelve mediante un recálculo central estático.
- La comparación con el MILP heterogéneo muestra por qué N2 debe conservar la capacidad individual.
