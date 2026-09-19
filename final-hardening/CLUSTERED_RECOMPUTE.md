# Recomputo de contrastes con la semilla como unidad de remuestreo

Bootstrap percentil pareado, B=10000, semilla de analisis 20260919
(distinta de todas las semillas de simulacion).

- **celdas**: remuestreo sobre (escenario x factor x semilla), como en el
  artefacto publicado. Es el `n` impreso en la memoria.
- **semillas**: la diferencia pareada se promedia dentro de cada semilla y
  el remuestreo es sobre semillas, que es la unidad que declara el
  protocolo.

| Campana | Contraste | n celdas | n semillas | efecto celdas | IC celdas | efecto semillas | IC semillas | ancho rel. | cambia signo | determinista |
|---|---|---:|---:|---:|---|---:|---|---:|---|---|
| E3 | `H-SP3-1-guard-reduces-fp` | 600 | 100 | -0.3333 | [-0.3717; -0.2950] | -0.3333 | [-0.3333; -0.3333] | 0.00 | no | SI |
| E3 | `H-SP3-2-vector-beats-scalar-gap` | 600 | 100 | -0.0933 | [-0.1019; -0.0849] | -0.0933 | [-0.0936; -0.0931] | 0.03 | no | no |
| E3 | `H-SP3-3-pair-beats-cbba-gap` | 600 | 100 | -0.0933 | [-0.1018; -0.0851] | -0.0933 | [-0.0935; -0.0931] | 0.03 | no | no |
| E3 | `H-SP3-4-exact-beats-ring-kkt` | 600 | 100 | -0.0181 | [-0.0201; -0.0161] | -0.0181 | [-0.0191; -0.0171] | 0.49 | no | no |
| E4 | `H4_1_replicator_safe_success_above_cbf` | 108 | 6 | +0.0926 | [+0.0370; +0.1574] | +0.0926 | [+0.0463; +0.1296] | 0.69 | no | no |
| E4 | `H4_2_replicator_collision_below_direct` | 108 | 6 | -0.8333 | [-0.8981; -0.7593] | -0.8333 | [-0.8333; -0.8333] | 0.00 | no | SI |
| E4 | `H4_3_exact_kkt_below_ring` | 108 | 6 | -0.3351 | [-0.3952; -0.2725] | -0.3351 | [-0.3520; -0.3210] | 0.25 | no | no |
| E4 | `H4_4_replicator_safe_success_above_nash_pd` | 108 | 6 | +0.2407 | [+0.1574; +0.3241] | +0.2407 | [+0.2222; +0.2593] | 0.22 | no | no |
| E4 | `H4_5_replicator_position_error_below_central` | 108 | 6 | -1.0436 | [-1.1869; -0.9033] | -1.0436 | [-1.0889; -0.9889] | 0.35 | no | no |
| E2 | `H02_primal_dual_vs_greedy` | 1560 | 40 | -0.1190 | [-0.1274; -0.1106] | -0.1190 | [-0.1271; -0.1113] | 0.95 | no | no |
| E2 | `H03_neural_vs_linear_imitation` | 1560 | 40 | -0.0097 | [-0.0118; -0.0077] | -0.0097 | [-0.0117; -0.0079] | 0.94 | no | no |
| E2 | `H04_local_pd_vs_oracle_messages` | 1560 | 40 | -2.8385 | [-3.2250; -2.4558] | -2.8385 | [-2.9526; -2.7321] | 0.29 | no | no |
| E2 | `H05_smith_vs_neural_runtime` | 1560 | 40 | -0.6627 | [-0.6848; -0.6438] | -0.6627 | [-0.6871; -0.6422] | 1.09 | no | no |

## Lectura

Ningun contraste cambia de signo ni de orden de magnitud al agrupar por
semilla. Lo que cambia es la interpretacion del intervalo: el ancho del
IC por celdas mide sobre todo la dispersion **entre escenarios y factores
de diseno**, que estan fijados por el disenador y no muestreados, no la
variabilidad entre repeticiones aleatorias. Varios contrastes son
deterministas por semilla (la columna final), es decir, el desenlace es
identico en todas las semillas y el intervalo publicado no describe
incertidumbre muestral alguna.

Consecuencia para la memoria: los valores p de estas campanas no se
interpretan como evidencia inferencial y los intervalos por celda no se
leen como error de generalizacion a mundos nuevos.
