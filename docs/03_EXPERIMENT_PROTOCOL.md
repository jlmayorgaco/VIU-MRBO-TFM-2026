# 03 — Protocolo experimental

## 1. Principios

Los experimentos deben poder reconstruirse desde código, configuración, semilla y versión del repositorio. Ninguna figura o tabla es fuente primaria: la fuente primaria son los datos crudos y el script que los procesa.

## 2. Unidad experimental

Una ejecución queda identificada por:

- `experiment_id`;
- SP o bloque;
- algoritmo;
- escenario;
- configuración;
- semilla;
- commit/version;
- fecha;
- estado: éxito, fallo, timeout o inválido;
- motivo de fallo cuando proceda.

## 3. Factores experimentales

### Escala

- número de robots `N`;
- número de cargas `K`;
- relación demanda/capacidad total;
- densidad espacial;
- duración u horizonte.

### Heterogeneidad

- dispersión de carga útil;
- dispersión de fuerza/torque;
- batería inicial y consumo;
- geometría/compatibilidad de contacto;
- distribución de masa, tamaño y requisito de pose de las cargas.
- modalidad física: Cargo soportado o empuje/caging;
- alcance, resolución, ruido y frecuencia de los sensores de proximidad usados para estimar la pose de la carga.

### Comunicación

- radio o topología;
- frecuencia local de actualización;
- retardo;
- jitter;
- pérdida de paquetes;
- particiones temporales;
- límite de bytes o mensajes.

### Entorno y perturbaciones

- densidad de obstáculos;
- anchura de pasillos;
- obstáculos dinámicos;
- fallo de robot;
- fallo de sensor/comunicación;
- ruido y saturaciones.

## 4. Métricas canónicas

### Asignación y coalición

- tasa de cargas factibles;
- déficit de capacidad/cardinalidad;
- sobreasignación;
- tiempo de formación;
- número de cambios de estrategia;
- utilidad social/potencial final;
- gap respecto al oráculo central.

### Transporte

- tasa de entregas;
- makespan;
- throughput;
- tiempo medio y percentiles de entrega;
- error de posición y orientación de la carga;
- longitud de trayectoria;
- energía estimada;
- residual de wrench o violación de restricciones mecánicas.
- Cargo: error de formación rígida, reparto de soporte y margen de wrench.
- Empuje/caging: error de pose estimada, pérdida/recuperación de contacto, deslizamiento y condición de confinamiento cuando proceda.

### Seguridad y resiliencia

- colisiones;
- distancia mínima;
- violaciones de seguridad;
- tiempo de detección de fallo;
- tiempo de re-reclutamiento;
- tiempo de recuperación;
- tareas perdidas o abandonadas.

### Coste

- tiempo de CPU total y por agente;
- memoria;
- iteraciones/evaluaciones;
- mensajes y bytes por robot/segundo;
- sensibilidad a delay y packet loss.

## 5. Baseline central/oráculo

El oráculo central debe resolver exactamente la misma instancia estática cuando sea posible. Para tamaños pequeños:

1. formular MILP/ILP de asignación/coalición;
2. registrar optimalidad o gap del solver;
3. imponer timeout;
4. no llamar “óptimo” a una solución con gap desconocido;
5. separar tiempo de optimización y tiempo de ejecución simulada.

El algoritmo húngaro se reserva al caso uno-a-uno de SP0 o a una reducción formalmente equivalente.

## 6. Comparación justa

- Mismos estados iniciales y semillas.
- Mismos límites de actuador y modelo de robot.
- Mismo mapa y cargas.
- Misma definición de éxito y timeout.
- Declarar qué algoritmo recibe información global.
- Ajustar parámetros en un conjunto de validación y evaluar en escenarios separados.
- No optimizar el método propuesto con conocimiento de cada caso y dejar baselines con parámetros por defecto sin justificación.

## 7. Estadística

- Para experimentos estocásticos, usar por defecto al menos 30 semillas cuando el coste lo permita; justificar cualquier número menor.
- La unidad independiente es el mundo o bloque escenario--semilla; robots, cargas y muestras temporales son observaciones anidadas.
- Reportar mediana y rango intercuartílico cuando haya colas o fallos; media y desviación solo cuando sea informativo.
- Incluir intervalos de confianza.
- Usar comparaciones pareadas cuando los algoritmos comparten escenarios/semillas.
- Reportar tasa y naturaleza de fallos, no eliminar ejecuciones desfavorables sin regla previa.
- Para tres o más métodos y endpoints continuos/ordinales usar Friedman como contraste global y Kendall W como tamaño de efecto; los pares preespecificados usan Wilcoxon pareado y correlación biserial por rangos.
- Cuando la media de diferencias sea el estimando previsto, reportar además Cohen dz, definido con la desviación de las diferencias pareadas, no el d de grupos independientes.
- Para éxito/factibilidad binarios usar diferencia de riesgos pareada, intervalo y McNemar exacto; para tiempos censurados usar análisis de supervivencia o limitarse a tasa de timeout y tiempo truncado.
- Definir familias de hipótesis antes del confirmatorio y corregirlas con Holm; separar análisis exploratorios añadidos después.
- Remuestrear mundos independientes en los intervalos bootstrap y registrar una semilla de análisis distinta de las semillas del simulador.

## 8. Ablaciones mínimas

Según el SP, retirar o variar:

- término de cardinalidad/capacidad;
- descuento espacial;
- consenso/estimador local;
- penalización de sobreasignación;
- activación suave de compromiso;
- filtro de seguridad;
- mecanismo de re-reclutamiento.

La ablación debe demostrar qué aporta cada componente; no basta comparar únicamente contra métodos externos.

## 9. Escenarios mínimos

### SP0

Casos homogéneos pequeños con solución analítica o enumerable, seguidos de instancias pareadas donde la matriz de costes se conserva al variar únicamente el grafo. La campaña de red debe separar: auditoría exacta; calidad; conectividad; convergencia espectral; agenda y ablaciones; escalado computacional/comunicativo; y selección condicionada de radio. Hungarian es oráculo, GCA es baseline conocido y GPG no se evalúa hasta disponer de dinámica, cierre y prueba completos. Una cota suficiente de exactitud no se reportará como condición necesaria ni como radio óptimo observado.

### SP1

Coaliciones con requisitos `{1, 2, 3, 4}` y demanda total por debajo, igual y por encima de la capacidad disponible.

#### Campaña de dinámicas V3

`SP1_DYNAMICS_BENCHMARK_v3` mantiene idénticos por mundo los costes, la máscara, el estado inicial, el grafo, los duales, el tracker PI, las tolerancias y los presupuestos; el factor primario es la geometría de revisión entre Replicator-D, Smith-D, BNN-D, Logit-D annealed y BestResponse-D relajada. La calibración usa exclusivamente semillas 70000--70019 y congela parámetros antes del preview y la evaluación.

La evaluación usa hasta 3.000 rondas, 60 s y $5\times10^9$ escalares por run. Toda ejecución que agota un presupuesto se conserva como censurada con causa explícita. Un paquete es un vector dirigido transmitido sobre una arista en un intercambio; el payload contabilizado concatena dual y tracker PI en `float64`, excluyendo cabeceras y protocolo físico. La unidad pareada es `world_id`; grafo, origen y semilla deben coincidir entre métodos.

E7.5 solo aplica un evento y ejecuta recuperación cuando el estado previo satisface el gate operacional completo. Si no existe ese origen, el evento queda excluido con razón registrada; los costes auxiliares no se interpretan como tiempo ni calidad de recuperación. Alcanzar un tamaño grande bajo censura no acredita escalabilidad.

#### Benchmark DRD-simple frente a CBBA-1-Capacity

`SP1_DRD_VS_CBBA_SIMPLE_v1` es una campaña independiente y más acotada: un
recurso de capacidad escalar, posiciones congeladas, coste exclusivamente
euclídeo y grafo conectado fijo. Compara `DRD-simple` con la adaptación
`CBBA-1-Capacity` usando el mismo \(\rho\), mundos y grafos emparejados, LP en
todos los tamaños, MILP para \(N\leq50\) y el mismo cierre entero para ambos
generadores. La calibración usa solo semillas 80000--80019; la evaluación usa
920 mundos distintos y conserva por separado `raw` y `recovered`. Una
terminación por `no_positive_bid` se clasifica como bloqueo greedy y no como
falta de iteraciones; `max_rounds` permanece censurado. La convergencia
continua de DRD no se interpreta como factibilidad de su cierre `argmax`.

La campaña registra payload lógico sin cabeceras físicas: paquete significa un
envío unidireccional por arista. `all_messages.csv` permite reconstruir
paquetes, escalares y bytes. La comparación primaria es
`DRD-simple/recovered` frente a `CBBA-1-Capacity/recovered`; raw frente a raw
caracteriza el generador. Las inicializaciones sesgadas por distancia y la
aceptación múltiple de candidatos de CBBA son ablaciones secundarias limitadas
a los 15 mundos del preview y no se mezclan con los 920 mundos principales.

#### Campaña final de juego poblacional con cuotas

`SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1` amplía el control anterior con cuotas
inferiores y superiores, compatibilidad, mercados locales y recuperación
atómica. La capacidad escalar indivisible se denota \(\chi_i\), porque \(q_i\)
ya identifica el estado del robot en la notación canónica. La intención
continua es \(\rho_{ik}\) y la ejecución atómica es \(x_{ik}\); el `x/y` del
enunciado externo queda mapeado en la configuración congelada.

Todos los métodos escalares reciben el mismo `world_id`, grafo y presupuesto.
Se conservan `raw`, `seeded` y `recovered`; `AugmentingRecovery` usa para todos
longitud máxima 12, 50.000 nodos por aumento, 30 candidatos y dos pasadas de
intercambio local. El LP es una cota fraccionaria y el MILP solo aporta gap
entero cuando certifica optimalidad. Hungarian se limita al control separado
de capacidades unitarias y slots enteros.

QPG usa una única pareja de precios comunes por carga, encaminada sobre el
grafo, y no copias densas de todos los duales por robot. El guard de evaluación
de 160 rondas/5 s en preview y 40 rondas/2 s en full es una causa explícita de
censura; no satisface el criterio de convergencia, que además exige residual de
estado, cuotas, precios/consenso y `dwell` de 100 rondas. La referencia
entrópica SLSQP se ejecuta en el preview hasta \(N=50\); LP se conserva en
todos los tamaños y MILP hasta \(N=50\).

La calibración usa únicamente semillas 700000--700007. El preview emplea 15
mundos distintos y congela el candidato `balanced` antes de E0--E10. E9
verifica cadenas mínimas 1--12 contra greedy, swap y reparación MILP. E10 es
un dominio secundario de requisitos enteros por servicio: solo allí se usan
las etiquetas `GRAPE-S` y `Pair-GRAPE-S`; `Weighted-GRAPE` permanece
explícitamente como adaptación del dominio escalar.

### SP2

Contribución operacional escalar dependiente del par robot--carga y casos donde la cardinalidad es suficiente pero el índice de servicio ponderado por disponibilidad no cubre el umbral. Comparar por separado cobertura parcial y cargas completas mediante dos referencias centrales. La carga útil nominal se normaliza con una escala explícita; batería y distancia no se interpretan como reducción mecánica. La compatibilidad no puede atribuirse a una campaña que la mantuvo universal; energía de misión, fuerza, torque y geometría de contacto se evalúan por separado desde SP3.

### SP3–SP4

`SP3-C/SP4-C`: una carga ligera y una pesada soportadas por varios robots; diferentes poses objetivo; perturbación de formación y al menos un caso con saturación o restricción de wrench activa.

`SP3-E/SP4-E`: empuje cooperativo con contactos unilaterales; diferentes poses y orientaciones objetivo; pérdida temporal de contacto, ruido de proximidad y al menos un caso donde el empuje alcanza la posición pero no la orientación. Solo los escenarios que verifiquen confinamiento geométrico se etiquetarán como caging.

### SP5

Pasillo, obstáculo aislado, cuello de botella y obstáculo dinámico controlado.

### SP6

Cargo: fallo antes del soporte, durante formación rígida y durante transporte. Empuje/caging: fallo antes del contacto, pérdida de un empujador o apertura del confinamiento durante el transporte.

### SP7

Cruce de dos coaliciones y conflicto de pasillo; solo si el sistema base es estable.

### SP8

Barridos en `N`, `K`, radio, delay y pérdida; oráculo hasta el tamaño que el solver resuelva con gap reportado.

## 10. Salidas reproducibles

Cada experimento debe producir:

- configuración serializada;
- log estructurado;
- datos crudos;
- resumen procesado;
- figura y tabla generadas por script;
- manifest con versión y semilla;
- entrada en `docs/04_CLAIMS_EVIDENCE.md` cuando respalde una afirmación de la tesis.
