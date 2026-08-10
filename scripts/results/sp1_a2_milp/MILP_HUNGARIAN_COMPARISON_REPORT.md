# SP1.A2 — MILP heterogéneo frente a Hungarian homogéneo

- Perfil: `quick`.
- Filas método--mundo/tratamiento: 3420.
- Factibilidad MILP heterogéneo: 0.685.
- Factibilidad Hungarian homogéneo: 0.637.
- Optimalidad MILP certificada: 0.448.
- Mediana de distancia MILP/Hungarian entre casos factibles: 0.8256.
- Error máximo de la reducción homogénea MILP--Hungarian: 0.000e+00 m.

## Interpretación

Hungarian resuelve el caso homogéneo expandido en slots. El MILP resuelve cargas obligatorias con capacidades individuales escalares. Cuando las capacidades son distintas, el ratio de distancia no mide por sí solo superioridad del algoritmo: también cambia el conjunto factible y el número de robots reclutados.

La capacidad escalar representa carga útil nominal en kg. No certifica soporte, fuerza, wrench, contacto, navegación ni transporte físico.
