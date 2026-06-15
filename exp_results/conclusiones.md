# Conclusiones del protocolo minimo

Fecha de ejecucion: 2026-06-13

## Cordura del motor

- Configuracion: r=[1,.8,.6,.5], n=[3,4,2,5], N=30.
- z*=[4.4722, 5.3540, 3.1989, 6.0986]
- z_obs=[4.4722, 5.3540, 3.1989, 6.0986]
- max|err|=1.96316e-08
- Veredicto: PASS

## H1 - Smith converge al water-filling

- H0: Smith no converge a z*.
- Criterio preregistrado: slope in [0.97,1.03], R2 > 0.99, max err < 0.05 for all configs.
- Resultado: slope=1.000000, R2=1.000000, max|err|=3.34744e-07, fallos=0.
- Veredicto: H0 RECHAZADA.

## H2 - Clearing entero reduce desperdicio bajo escasez

- H0: el clearing entero no cambia la cobertura bajo escasez.
- Criterio preregistrado: sin-entero >= con-entero in 100% of configs and strictly greater in >=50%.
- Resultado: desperdicio medio 8.758 -> 5.958 robots (-32.0%).
- Delta pareado: 2.800, IC95 [1.976, 3.624].
- No-peor: 100.0%; estricto mejor: 100.0%.
- Nota de medicion: integer mode uses post-burn-in mean floor(z) waste; fractional post-burn-in waste is also recorded.
- Veredicto: H0 RECHAZADA.

## H3-A - Precio en equilibrio estatico

- H0 operativa: el precio no debe reclamarse como mecanismo estatico.
- Criterio: report negative or neutral static effect; do not validate H3 in static equilibrium.
- Abundancia: delta valor=0.0000, IC95 [0.0000, 0.0000].
- Escasez: delta valor=-0.1180, IC95 [-0.1689, -0.0671].
- Tarea mas valiosa en escasez: delta z=-1.670, IC95 [-1.878, -1.462].
- Veredicto: NEGATIVO ESTATICO CONFIRMADO.

## H3-B - Precio temporal con llegadas y deadlines

- H0: el precio no cambia el valor entregado a tiempo bajo llegadas.
- Criterio preregistrado: scarcity paired delta CI95 above 0; abundance effect approximately 0 or non-positive.
- Abundancia: sin precio=0.9983, con precio=0.9983, delta=0.0000, IC95 [0.0000, 0.0000], veredicto=EFECTO NULO.
- Escasez: sin precio=0.6236, con precio=0.9021, delta=0.2785, IC95 [0.2234, 0.3337], veredicto=H0 RECHAZADA.

## Veredicto integrado

H1 y H2 pasan sus criterios preregistrados. H3-A confirma que el precio no debe defenderse como mecanismo de asignacion estatica: en abundancia no agrega valor y en escasez perturba el equilibrio. H3-B si muestra el cruce temporal esperado: efecto nulo en abundancia y mejora positiva, con IC95 disjunto de cero, bajo escasez con llegadas y deadlines.
