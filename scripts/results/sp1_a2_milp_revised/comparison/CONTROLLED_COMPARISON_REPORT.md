# SP1.A2 — comparación controlada MILP–Hungarian

Esta comparación reduce el MILP al mismo problema homogéneo que puede resolver Hungarian: `c_i^{pay}=q_bar` y cada carga se expande en su cuota entera de slots. Los mundos, masas, posiciones, semillas y robots fallados son pareados.

## Auditoría del diseño

- Perfil: `smoke`.
- Filas: 126.
- Modelo homogéneo en todas las filas: `True`.
- Pares conjuntamente factibles: 102.
- Desacuerdos de factibilidad: 0.
- Error absoluto máximo de distancia: 0.000e+00 m.
- Ratio mediano de tiempo MILP/Hungarian: 181.60×.

## Conclusión

En esta reducción, ambos métodos deben recuperar el mismo coste de distancia, salvo tolerancia numérica. La comparación relevante es computacional: el MILP resuelve una formulación binaria general, mientras Hungarian explota la estructura especializada de asignación. Por ello, igualdad de calidad no implica igualdad de tiempo.

Este resultado no autoriza extrapolar Hungarian al problema heterogéneo: fuera de la reducción homogénea ya no representa las restricciones de capacidad del MILP.
