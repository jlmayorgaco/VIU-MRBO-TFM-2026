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

El algoritmo húngaro se reserva a la etapa de calibración uno-a-uno de SP1 o a una reducción formalmente equivalente.

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

### SP1 — Formación distribuida de coaliciones

- Calibración homogénea uno-a-uno con solución analítica o enumerable; Hungarian actúa únicamente como oráculo de esta etapa.
- Coaliciones con requisitos `{1, 2, 3, 4}` y demanda total por debajo, igual y por encima de la capacidad disponible.
- Robots y cargas heterogéneos con casos donde la cardinalidad es suficiente pero la contribución operacional o el certificado de rol/contacto no cubre el requisito.
- Decisiones explícitas de esperar/iniciar, abandono y cambio de coalición, con costes de conmutación y tareas de distinta prioridad.
- Comparación entre agregados globales, estimación vecinal y ablación sin intercambio de mensajes; barridos de conectividad, retardo y pérdida.
- Referencias centrales separadas para cobertura parcial, cargas completas y factibilidad de roles/contactos. Batería y distancia no se interpretan como reducción mecánica de fuerza.

La implementación regenerable actual es `src/viu_mrob_tfm/sp1_canonical/`. La configuración `sp1_canonical_smoke.yaml` valida el piloto de roles/contactos. La batería `sp1_canonical/validation/` separa E0 casos manuales, E1 relajación LP, E2 grafo, E3 discretización, E4 cierre entero, E5 escala y E6 llegada uniciclo. `sp1_validation_smoke.yaml` valida el software extremo a extremo; `sp1_validation_confirmatory.yaml` conserva los barridos de 100 mundos de E1--E4 y 30 semillas de E5--E6. Esa campaña solo adquirirá valor confirmatorio después de congelar hipótesis, tolerancias y análisis, ejecutarla completa y registrar resultados —incluidos los negativos— en la matriz de evidencia.

La campaña congelada `sp1_conference_v1.yaml` amplía esa infraestructura sin
sobrescribir el piloto. Predeclara P0, cinco casos deterministas E0, los tamaños
y semillas de E1--E6, tolerancias relativas `10^-3/10^-4/10^-3`, comparabilidad
estricta a `10^-6`, bootstrap agrupado, Wilcoxon pareado, tamaños de efecto,
Holm e intervalos binomiales. Los gaps regularizados, brutos y enteros se
mantienen en columnas distintas; toda exclusión conserva un código de motivo.
Los diez gates de conferencia se calculan desde los CSV y no se suavizan tras
observar resultados.

En E1--E4, LP y MILP reciben información global y actúan como referencias. Rep-D solo intercambia copias locales de multiplicadores por aristas del grafo. El criterio de convergencia debe reportar conjuntamente residuo primal normalizado, desacuerdo de multiplicadores y estacionariedad; alcanzar solo uno de ellos no cuenta como convergencia. El paso de E3 se registra respecto a una escala de operador implementada `alpha_reference`, no se denomina `alpha_max` ni cota teórica hasta disponer de una demostración formal. E6 congela la asignación antes de mover los uniciclos y termina en la pose de aproximación; no es evidencia de SP2.

La comparación de relajaciones separa `J_raw=C^T x` y `J_tau=C^T x/c_scale-tau H([x,idle])`. Rep-C y Rep-D solo se comparan con `LP-tau` cuando usan el mismo `tau`, normalización y conjunto factible. Un gap respecto a LP se reporta únicamente si `primal_residual_normalized<=10^-6`; en caso contrario queda como `NaN` y se conserva `gap_lp_unfiltered` solo para diagnóstico. La aceptación mínima exige `r_prim<=10^-6`, `r_cons<=10^-6` y `r_stat<=10^-5`.

E2 etiqueta cada ejecución como `theorem_connected` o `negative_disconnected`; los controles negativos no entran en una eventual regresión rondas--`lambda_2`. E4 aplica cobertura, poda por ahorro, sustitución `1↔1` y compresión `2↔1`. E5 conserva un testigo constructivo de factibilidad, fuerza conectividad cuando el barrido la presupone y clasifica la etapa de fallo. En E6, el escenario de almacén calcula coste y energía estimada sobre la longitud A*, no sobre distancia euclídea.

La campaña `SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1` añade un
diseño factorial específico para identificar por separado la señal, el motor
de decisión y el cierre. Usa seis familias F0--F5, tamaños `(12,3)`, `(32,8)`
y `(64,16)`, cinco semillas de preview y cincuenta confirmatorias por celda.
Los bloques preview `910000--910004`, tuning `920000--920009`,
confirmatorio `930000--930049` y análisis `990001` son disjuntos. La unidad
independiente es el mundo; las cargas son observaciones anidadas. Todas las
salidas se conservan en etapas `RAW`, `CERTIFIED` y `RECOVERED`, con el mismo
certificador y el mismo reparador. El ajuste
`min ||G u-w||_2` sujeto a cotas sobre `u` se registra correctamente como
mínimos cuadrados acotados convexos. Hungarian se ejecuta solo en F0; MILP,
LP y la referencia entrópica se declaran centralizados y sus límites de tamaño
se conservan como datos. El análisis confirmatorio no se abre para ajuste y no
publica gaps MILP cuando el solver no acredita optimalidad certificada.

Los scripts `sp1_n1.py`--`sp1_n4.py` producen la capa de evidencia del
artefacto editorial. N1 v2 y N4 v2 se regeneraron desde configuraciones
versionadas; N2 y N3 mantienen sus campañas registradas. Cada paquete conserva
RAW, datos procesados, manifiesto y figuras PDF/PNG.

La campaña `SP1_N4_DISTRIBUTED_FAMILY_v2` mantiene mundo y semilla dentro de
cada contraste. E4 reutiliza 1.200 mundos congelados y ejecuta BR, Geo-ASR,
Geo-LLL, 2BR, C3, CF y DMIS+TX junto con los tres baselines N3. BR--2BR--C3 se
interpreta como una jerarquía anidada por orden local; ASR y LLL solo alteran la
revisión dentro de orden uno. E5
abre 400 mundos pequeños (`N=6,8`) y compara DPOP, MILP, C3 y DMIS+TX. E6
abre 60 mundos de escala con `N=16,32,48,64` y `K=N/4` para BR y DMIS+TX.
El endpoint binario usa McNemar/Newcombe; las variables continuas usan mediana
de diferencias, bootstrap de mundos y Wilcoxon; la familia confirmatoria aplica
Holm. Fallos y timeouts permanecen en el denominador.

El programa N4 se organiza en nueve preguntas. Q1 enumera el menor orden de
escape después de BR; Q2 separa regla de revisión y orden estratégico mediante
E4; Q3 ejecuta las mismas propuestas con perfil completo y agregados afectados;
Q4 compara CF y DMIS+TX; Q5 usa E5 para exactitud distribuida pequeña; Q6 usa E6
para escala; Q7 exige un cierre común para las dinámicas poblacionales; Q8 exige
residuos primal, dual, consenso y KKT antes del cierre F-III; Q9 inyecta retardo,
pérdida, reordenamiento y caída del proponente. E7 ejecuta Q7 y Q8 sobre los
1.200 mundos congelados de E4. E9 ejecuta Q1; Q3 y Q9 permanecen pendientes. Q4 conserva
evidencia nominal, pero aún debe registrar rondas,
identidad final y canal degradado.

La figura temporal de una ejecución requiere RAW por evento con fase, déficit,
distancia, orden aceptado, commits paralelos y bytes acumulados. E4--E6 no
persistieron esa secuencia y no se reconstruyen a partir de agregados. E9 abre
un replay separado, registra cada commit y fija antes de dibujar la regla para
elegir el mundo representativo. Esa traza ilustra una ejecución; no sustituye
la distribución de los 1.200 mundos.

La lectura taxonómica de N4 añade dos condiciones de comparabilidad. Primero,
Replicator, Smith, BNN y Logit operan sobre una relajación poblacional. E7 les
aplica una única regla `\mathcal R(x)=a` y audita factibilidad, calidad y coste
sobre los mundos de E4; E71 queda como antecedente histórico porque usó otro
modelo. Segundo, primal--dual es un mecanismo y vGNE un concepto de solución.
E7 registra los residuos primal, dual, de complementariedad, estacionariedad y
consenso antes de aplicar el mismo cierre de F-II. F-IV permanece fuera del
confirmatorio estático. Consensus/DAC, flooding y registros versionados se
comparan como arquitecturas de información dentro de una formulación, no como
familias rivales.

### N4 v3 — comparación atómica y piloto temporal

La campaña `SP1_N4_CROSS_FAMILY_v3` tiene dos bloques. E7 reutiliza los 1.200
mundos de E4 (`N=16`, `K=5`) y produce 16.800 filas: siete métodos/baselines
históricos, cuatro dinámicas F-II, dos soluciones F-III y el oráculo MILP. Los
40 mundos declarados infactibles por el oráculo permanecen en RAW y en el
denominador de fallos; el gap solo se calcula en soporte certificado. F-II usa
un potencial squared-hinge común y DAC; F-III usa regularización `ε=0,02`, una
referencia central y un predictor--corrector distribuido. F-II y F-III terminan
con el mismo cierre determinista acotado.

E8 abre 30 mundo--semilla pequeños (`N=5`, `K=3`) con secuencias pareadas de
llegadas, finalizaciones y fallos. Compara re-solving, warm start activado por
evento y un oráculo dinámico central de horizonte finito. F-IV se clasifica como
juego potencial repetido con eventos exógenos; no se afirma que sea un juego
potencial de Markov. La configuración, RAW, procesados, figuras y hashes viven
en `scripts/results/sp1_levels/n4_v3/`.

### N4 v4 — orden mínimo de coordinación

La campaña `SP1_N4_HSTAR_v4` audita el estado en el que termina BR cuando parte
del perfil inactivo. Para cada mundo enumera todas las desviaciones conectadas
en las que cambian exactamente dos robots; si ninguna mejora el criterio,
repite la enumeración con tres. Por tanto, las etiquetas 2 y 3 son exactas
dentro de esas vecindades. La etiqueta `>3` solo dice que el corte no encontró
una mejora: no distingue una desviación de orden superior de un mínimo global.

El bloque principal reutiliza los 1.200 mundos congelados de E4 (`N=16`,
`K=5`). Un segundo bloque, independiente y no combinado con el principal,
varía `N/K` en 2, 3 y 4 sobre otros 1.200 mundos. Se publican el conteo y el IC
de Wilson de cada categoría, el coste medido de la búsqueda, el vínculo con la
reducción posterior del gap y una traza F-I por commit. Configuración, RAW,
procesados, figuras y hashes se guardan en
`scripts/results/sp1_levels/n4_v4/`.

El directorio fuente histórico `sp1_levels_23p` compila el artefacto vigente de
48 páginas: 2 de apertura, 4 de protocolo común, 6 de N1, 6 de N2, 8 de N3 y
22 de N4. La validación exige exactamente 48 páginas, hashes RAW intactos y
render completo con Poppler.

### SP2 — Ejecución y transporte cooperativo

- Cargo ligero y pesado soportado por varios robots; aproximación, docking, estabilización y diferentes poses objetivo.
- Perturbación de formación, cambio de geometría y al menos un caso con saturación o restricción de wrench activa.
- Pasillo, obstáculo aislado, cuello de botella y obstáculo dinámico controlado.
- Fallo antes del soporte, durante formación rígida y durante transporte; sustitución, reanudación y abandono seguro cuando no existe reserva factible.
- Finalización con liberación de la carga y separación de los robots, registrando contacto, error de pose y tiempo de misión.
- En la extensión empuje/caging: contactos unilaterales, pérdida temporal de contacto, ruido de proximidad y casos que separen posición de orientación. Solo se usa el término caging cuando se verifica confinamiento geométrico.

### SP3 — Planificación y tráfico de múltiples coaliciones

- Cruce de dos o más coaliciones, conflicto de pasillo, intersección con prioridades y cargas de huellas diferentes.
- Convivencia de robots libres, robots en reunión y coaliciones en transporte.
- Bloqueo, envejecimiento de prioridad, congestión, aparición de nuevas tareas y replanteamiento durante la ejecución.
- Barridos en `N`, `K`, radio, retardo y pérdida; oráculo hasta el tamaño que el solver resuelva con gap reportado.
- Evaluación separada de exclusión lógica discreta, seguridad geométrica continua y vivacidad; ninguna se usa como sustituto de las otras.

## 10. Salidas reproducibles

Cada experimento debe producir:

- configuración serializada;
- log estructurado;
- datos crudos;
- resumen procesado;
- figura y tabla generadas por script;
- manifest con versión y semilla;
- entrada en `docs/04_CLAIMS_EVIDENCE.md` cuando respalde una afirmación de la tesis.
