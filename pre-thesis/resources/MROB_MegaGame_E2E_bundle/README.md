# MegaGame E2E — escenario sintético reproducible

Escenario con 15 AMR heterogéneos, 3 cargas y 12 robots reclutados: A Cargo, B Caging y C Cargo.

## Qué se ejecuta
- subasta distribuida para reclutamiento;
- formación inicial con uniciclo;
- ruta inicial recta y deformación suave local frente a obstáculos;
- negociación distribuida de precedencia sobre un recurso espacio-tiempo de capacidad uno;
- revisión pairwise con ampliación adaptativa CFRD si fuera necesaria;
- time-scaling cooperativo sin parada;
- cinemática diferencial por apoyo, velocidades de rueda y torque;
- reparto de wrench Cargo mínimo-cuadrático;
- QP convexo unilateral para Caging con chequeo KKT;
- batería proxy torque-velocidad + pérdidas de cobre + auxiliares;
- comparación con stop-go seguro usando el mismo orden/slots.

## Resultados principales
- Reclutamiento: coste distribuido 62.827769, oráculo 62.827769.
- Orden distribuido: ['A', 'B', 'C'], igual al oráculo del catálogo 3!; FCFS: ['C', 'A', 'B'].
- Mejora de fin frente a FCFS: 1.290 s (1.49%).
- Ejecución cooperativa vs stop-go con el mismo horario: 0 vs 3 paradas, 1.97% menos energía proxy, 77.6% menos coste de aceleración, 59.1% menos torque pico.
- Clearance mínimo entre coaliciones: 0.655 m.
- Clearance mínimo a obstáculos: 0.212 m.
- Residual KKT máximo del QP Caging: 1.396e-11.

## Alcance
No es una réplica de R10 ni una validación de hardware. La ruta espacial es una solución local del optimizador de spline/potencial; no se certifica su optimalidad global. La optimalidad sí se comprueba para la asignación de reclutamiento y para el orden del catálogo de 3 coaliciones. El QP de Caging es convexo en la geometría fija de cada muestra y se acompaña de residual KKT.
