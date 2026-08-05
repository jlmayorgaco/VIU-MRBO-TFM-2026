# Informe SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1

## Alcance

Esta campaña evalúa formación estática de coaliciones en Python. No simula transporte físico sostenido, contacto dinámico ni estabilidad de SP2.

El residual euclídeo de wrench se resuelve como mínimos cuadrados acotados convexos; no se etiqueta como LP. El margen publicado es el margen a la tolerancia del residual, no un certificado robusto frente a un conjunto de incertidumbre.

## Integridad de ejecución

- Mundos independientes: 900.
- Filas método–mundo–cierre: 35100.
- Timeouts o límites del MILP en salida nativa: 4.
- Errores de solver no recuperados en salida nativa: 0.
- Salidas nativas por máximo de iteraciones: 2720.
- RAW, CERTIFIED y RECOVERED se conservan por separado.
- Todos los métodos usan el mismo mundo, bienestar físico de evaluación, certificador y recuperación común.

## Mapa descriptivo

- `F0_easy_separable`: `weighted_grape_scalar` lideró descriptivamente 2/3 tamaños; `physical_cbba_marginal` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.
- `F1_heterogeneous_critical`: `capacity_cbba_scalar` lideró descriptivamente 2/3 tamaños; `geo_qpg_smith_physical` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.
- `F2_scarce_priority`: `capacity_cbba_scalar` lideró descriptivamente 2/3 tamaños; `geo_qpg_smith_physical` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.
- `F3_torque_complementarity`: `geo_qpg_logit_physical` lideró descriptivamente 1/3 tamaños; `geo_qpg_smith_physical` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.
- `F4_mixed_geometry_route`: `capacity_cbba_scalar` lideró descriptivamente 2/3 tamaños; `geo_qpg_smith_physical` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.
- `F5_network_failure`: `capacity_cbba_scalar` lideró descriptivamente 1/3 tamaños; `capacity_cbba_scalar` obtuvo la peor mediana de rango. Son etiquetas descriptivas y no acreditan dominancia.

## Hipótesis predeclaradas

- `H1_theory_kkt_alignment`: efecto 3.88734e-12, p Holm nan; supera el gate numérico predeclarado.
- `H2_closure_needed`: efecto 0.697778, p Holm 1.79553e-188; rechaza la nula tras Holm.
- `H3_physical_signal_qpg_logit`: efecto 0.00400673, p Holm 1; no cumple la reducción RAW predeclarada de 20 pp.
- `H3_physical_signal_capacity_cbba`: efecto -0.0459675, p Holm 0.000139997; no cumple la reducción RAW predeclarada de 20 pp.
- `H3_physical_signal_pair_grape`: efecto 0.00982143, p Holm 0.625107; no cumple la reducción RAW predeclarada de 20 pp.
- `H4_geo_qpg_vs_cbba_quality`: efecto 0.00623635, p Holm 1; no cumple conjuntamente el gate compuesto y el contraste tras Holm.
- `H5_engine_qpg_vs_pair_grape`: efecto -0.0114719, p Holm 1; no es concluyente tras Holm.
- `H5_engine_practical_equivalence_coverage`: efecto -0.00283333, p Holm 1.7329e-85; acredita equivalencia dentro del margen tras Holm.
- `H6_easy_runtime_qpg_minus_hungarian`: efecto 1651.33, p Holm 0.000139997; rechaza la nula tras Holm.
- `H7_failure_recourse_qpg_minus_cbba`: efecto -14.0267, p Holm 0.000139997; cumple el gate del proxy estático tras Holm; no valida recourse dinámico.
- `H_global_factorial_engine_signal`: efecto 0.047986, p Holm 8.81654e-44; rechaza la nula tras Holm.

## Gates compuestos

- H4 se evaluó en 15 combinaciones familia–tamaño; 0 cumplieron simultáneamente factibilidad, cobertura, calidad, gap cuando aplicaba, runtime y bytes.
- H3 se corrigió al endpoint RAW predeclarado en F3–F4. CERTIFIED y RECOVERED no son informativos para falsos positivos porque el certificador común elimina por construcción los compromisos inválidos.
- H7 se informa solo como proxy estático postfallo. Aunque cumpla sus umbrales numéricos, la hipótesis dinámica permanece sin validar.

## Revisión de análisis

- Revisión `sp1_geo_h3_raw_and_composite_gates_v2`: corrige el cierre de H3 y materializa los gates compuestos sin modificar mundos, semillas, asignaciones ni configuración confirmatoria.

## Limitaciones

- Capacity-CBBA, Weighted-GRAPE y Role/Pair-GRAPE-S son adaptaciones implementadas; no heredan automáticamente las garantías de los métodos originales.
- El MILP usa una envolvente lineal de recursos alineados y después pasa el certificador firmado. Su optimalidad no equivale a un oráculo universal del contacto.
- Los gaps a MILP aparecen únicamente cuando el solver y la salida certificada permiten la comparación.
- F5 es una instantánea estática posterior a un fallo. El recourse mide cambios del cierre común respecto de la intención post-fallo; no sustituye una trayectoria dinámica pre/post-fallo.
- La pérdida de paquetes de F5 se representa mediante una realización congelada de caída de aristas no puente; no modela pérdidas temporales independientes en cada ronda.
- El análisis usa el mundo como unidad independiente; las cargas no se tratan como réplicas independientes.
- Los resultados de preview son piloto. La configuración confirmatoria permanece separada y no debe ajustarse tras abrir sus semillas.

## Reproducción

```powershell
python scripts/run_sp1_geo_benchmark.py --config configs/experiments/sp1_geo/SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1.yaml
```
