# Informe — SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1

## Alcance y lectura correcta

La campaña evalúa exclusivamente reclutamiento SP1. Las posiciones solo parametrizan coste de llegada; no se simulan docking, contacto, wrench, transporte, MPC ni tráfico. `rho` es intención continua y `x` es la asignación atómica, conforme a la notación canónica del repositorio.

Los resultados `raw`, `seeded` y `recovered` se conservan por separado. El LP es una cota/referencia fraccionaria, nunca una ejecución física. Capacity-CBBA y Weighted-GRAPE son adaptaciones declaradas. GRAPE-S aparece solo en E10, su dominio discreto de servicios.

## Resultado descriptivo agregado

La tabla siguiente agrupa E1–E7 y calcula distancia/exceso solo sobre salidas recovered factibles; la sección posterior separa E1–E5 por cierre.

| method                |   runs |   feasibility |   distance_median_m |   excess_median |   time_median_s |     bytes_median |
|:----------------------|-------:|--------------:|--------------------:|----------------:|----------------:|-----------------:|
| Weighted-Pair-GRAPE   |   1770 |      0.899435 |            1339.4   |         5.6197  |       2.00236   | 192060           |
| Weighted-GRAPE        |   1770 |      0.894915 |            1742.51  |         6.01803 |       0.290707  | 168300           |
| Atomic-Quota-Logit    |   1770 |      0.886441 |            1338.6   |         5.7357  |       2.06549   |  36512           |
| Capacity-CBBA         |   1770 |      0.884181 |            1411.67  |         5.70619 |       1.14909   |  43428           |
| QPG-Replicator-AR     |   1770 |      0.872881 |             967.926 |         6.04453 |       0.0516293 |      2.10944e+06 |
| QPG-Logit-AR          |   1800 |      0.867222 |             768.639 |         5.93936 |       0.0489598 |      2.0864e+06  |
| DRD-simple-Logit      |   1770 |      0.857627 |            2342.61  |         6.41229 |       0.06145   |      2.15424e+06 |
| DRD-simple-Replicator |   1770 |      0.843503 |            2105.79  |         6.48182 |       0.0639171 |      2.15424e+06 |

## Servicios discretos E10

|    | method                     |   services_per_robot |   runs |   feasibility_rate |   time_median_s |   bytes_median |
|---:|:---------------------------|---------------------:|-------:|-------------------:|----------------:|---------------:|
|  0 | Capacity-CBBA-Services     |                    1 |     40 |              1     |      0.0024908  |          25728 |
|  1 | GRAPE-S                    |                    1 |     40 |              1     |      0.006008   |          48000 |
|  2 | Pair-GRAPE-S               |                    1 |     40 |              1     |      0.00640885 |          48000 |
|  3 | QPG-Multiservice-Extension |                    1 |     40 |              1     |      0.00250155 |          25728 |
|  4 | Pair-GRAPE-S               |                    5 |     40 |              1     |      0.0154159  |          56720 |
|  5 | GRAPE-S                    |                    5 |     40 |              0.975 |      0.0146951  |          56720 |
|  6 | Capacity-CBBA-Services     |                    5 |     40 |              0.725 |      0.0042574  |          28080 |
|  7 | QPG-Multiservice-Extension |                    5 |     40 |              0.725 |      0.00441565 |          28080 |

## Certificados

Se verificaron 2970 certificados válidos de 2970 diagnósticos aplicables.

## Censura y límites

El guard de rondas es censura computacional explícita y nunca se interpreta como convergencia. Las simulaciones no demuestran estabilidad global, optimalidad distribuida, transporte físico ni tasa asintótica.

## Ejecución

- Tasks completadas: 2200/2200.
- Workers: 6.
- Wall time primario del driver: 3161.859 s.
- CPU algorítmica acumulada sin triplicar cierres: 16945.641 s.
- Figuras PNG/PDF: 12.

## Separación raw → seeded → recovered

| method                |    raw |   seeded |   recovered |
|:----------------------|-------:|---------:|------------:|
| Weighted-Pair-GRAPE   | 0.1054 |   0.7986 |      0.8789 |
| Weighted-GRAPE        | 0.0517 |   0.7912 |      0.8735 |
| Atomic-Quota-Logit    | 0.1401 |   0.7551 |      0.8633 |
| Capacity-CBBA         | 0.1265 |   0.7925 |      0.8605 |
| QPG-Replicator-AR     | 0.0293 |   0.7245 |      0.8469 |
| QPG-Logit-AR          | 0.0190 |   0.7075 |      0.8374 |
| DRD-simple-Logit      | 0.0320 |   0.7660 |      0.8286 |
| DRD-simple-Replicator | 0.0395 |   0.6687 |      0.8116 |

La factibilidad final no puede atribuirse a la dinámica continua. En E1–E5, QPG-Logit pasó de 1.90% raw a 70.75% seeded y 83.74% recovered. El mismo recovery acotado también elevó sustancialmente a todos los baselines; por tanto, es el principal responsable de la factibilidad.

## Respuesta a las diez preguntas obligatorias

1. **Régimen fácil.** No existe un dominador único. En E4 (heterogeneidad baja, utilización 0,60, banda amplia), todos los métodos fueron factibles: QPG-Replicator obtuvo la menor distancia mediana (634.4 m), QPG-Logit quedó en 646.4 m, Weighted-GRAPE tuvo el menor exceso (5.75) y Atomic-Quota-Logit fue mucho más barato en comunicación (49056 bytes).

2. **Alta heterogeneidad y alta utilización.** Tampoco hubo dominador. En E4 alta/0,95/estrecha, Capacity-CBBA tuvo la mayor factibilidad (33.3%), seguido por Weighted-GRAPE (26.7%); QPG-Logit alcanzó solo 16.7%. Entre sus escasas salidas factibles, QPG-Logit sí obtuvo menor distancia (1172.4 m), lo que no compensa el sesgo de selección inducido por la baja factibilidad.

3. **Cuotas superiores.** Las bandas estrechas eliminaron violaciones superiores en las salidas declaradas factibles, pero no redujeron el exceso respecto de la cuota inferior: las medianas E4 fueron 6.156 (amplia), 6.277 (media) y 6.280 (estrecha). Su efecto principal fue reducir la región factible.

4. **Calidad frente a coste.** QPG compra una mejora descriptiva de distancia (781.4 m de mediana estática), pero no justifica su coste como ganador general: tuvo menor factibilidad que los métodos hedónicos, censura del 100 % y una mediana de 1896960 bytes. En el régimen difícil incumplió los gates de factibilidad, gap MILP, recursos y recourse.

5. **Estado continuo o recovery.** La ventaja de factibilidad provino principalmente del recovery común, no del estado continuo; la tabla raw/seeded/recovered lo hace auditable.

6. **Logit frente a Replicator.** En QPG, Logit redujo distancia (781.4 frente a 816.6 m) y exceso (5.03 frente a 5.42), pero perdió 0.95% de factibilidad. En DRD, Logit mejoró ligeramente factibilidad pero empeoró distancia (2207.7 m). No hay mejora universal por cambiar el protocolo.

7. **Mercados locales y cuello de botella V3.** La arquitectura evita estructuralmente copias densas globales de todos los duales, pero no redujo el tráfico medido: QPG-Logit usó aproximadamente un 21 % más bytes que DRD-Logit en E1–E5. No se acredita la eliminación del cuello de botella de comunicación.

8. **Certificado extremo a extremo.** Fue válido en 1500/1500 casos QPG-Logit aplicables, pero su gap relativo mediano (781.3) fue demasiado holgado para ser operativo. La cota Bernstein fue válida pero vacua: mediana 1,0 frente a una frecuencia empírica de fallo también cercana a 1,0.

9. **Dónde GRAPE/CBBA son mejores.** Capacity-CBBA fue más factible en el régimen difícil y mucho más barato en bytes; Weighted-GRAPE y Weighted-Pair-GRAPE lograron la mayor factibilidad estática agregada. En E10 discreto, Pair-GRAPE-S alcanzó 100 % y GRAPE-S 97,5 % con cinco servicios por robot, frente a 72,5 % de las extensiones Capacity-CBBA y QPG.

10. **Claim final defendible.** Se implementó y auditó una interfaz trazable de intención continua, compromiso atómico y recuperación común con precios locales y certificados válidos. La evidencia identifica un intercambio entre distancia, factibilidad y comunicación; no soporta superioridad general, convergencia ni optimalidad entera distribuida.

## Gates científicos y resultados negativos

- QPG-Logit obtuvo 16.7% de factibilidad en el régimen difícil predeclarado, lejos del 95 % exigido.
- Su gap MILP mediano fue 0.235, por encima del 0,05 exigido.
- El recourse dinámico mediano fue 97 robots frente al mejor valor 42; la razón 2.31 incumple el máximo 0,70.
- Todas las salidas pos-evento fueron reparadas, pero la fracción mediana de coaliciones no afectadas intactas fue 0.0; el cierre fue global, no local.
- En E9, augmenting paths y MILP repair resolvieron 100.0% y 100.0%; greedy y swap resolvieron 7.7% y 15.4%. Esto valida el generador de cadenas 1–12 dentro del dominio ensayado, no completitud general.

## Conclusión científica

La interpretación final se basa en el mapa de regímenes y en pruebas emparejadas; no se presupone un ganador. Cuando QPG no satisface un gate, se registra como resultado negativo. La contribución defendible es el pipeline trazable continuo→semilla→recovery con precios comunes por mercado local y certificados computables, no una afirmación de optimalidad entera distribuida general.
