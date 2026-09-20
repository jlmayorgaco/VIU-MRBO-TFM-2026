# 02 — Matriz de investigación SP1–SP3

## 1. Arquitectura de los subproblemas

- **SP1 — Formación distribuida de coaliciones:** reclutamiento, cardinalidad, heterogeneidad, roles/contactos, espera, inicio, abandono y cambio mediante información vecinal.
- **SP2 — Ejecución y transporte cooperativo:** aproximación, acoplamiento, estabilización, control de pose, seguridad, reconfiguración, sustitución y desacoplamiento.
- **SP3 — Planificación y tráfico de múltiples coaliciones:** coordinación de robots libres, grupos en reunión y coaliciones en transporte; rutas, cruces, prioridades, bloqueos, congestión, nuevas tareas y replanteamiento.

La formulación general se presenta una sola vez. SP1 entrega una coalición cerrada y certificada a SP2; SP2 entrega a SP3 un cuerpo compuesto ejecutable con huella, estado y límites. Escalabilidad, comunicación, coste y resiliencia son ejes transversales, no subproblemas adicionales.

## 2. Niveles de evidencia

- **Nivel A:** resultado formal completo + validación numérica.
- **Nivel B:** proposición/argumento formal parcial + validación extensa.
- **Nivel C:** evaluación experimental y análisis de sensibilidad; sin garantía general.

## 3. Matriz canónica

| SP | Pregunta local | Decisiones y estado | Método propuesto | Baselines principales | Evidencia objetivo | Prioridad |
|---|---|---|---|---|---|---|
| SP1 | ¿Cómo formar y adaptar coaliciones heterogéneas, asignar roles/contactos y decidir entre esperar, iniciar o cambiar usando únicamente vecinos? | Pertenencia robot--carga, cardinalidad, contribución multidimensional, rol/contacto, utilidad de espera y coste de cambio; salida: coalición cerrada y certificada | Juego potencial/poblacional con déficit, exceso, utilidad marginal, estimación vecinal y cierre ejecutable | MILP/ILP o set partitioning como oráculo; subasta/CBBA multi-ganador verificable; greedy y ablaciones | A para casos delimitados de cobertura/cuota; B para heterogeneidad, rol/contacto y operación vecinal completa | Nuclear |
| SP2 | ¿Cómo ejecutar el transporte desde la aproximación hasta la liberación, preservando estabilidad operacional, contactos, límites y seguridad sin líder físico permanente? | Estado de robots y carga, contactos, wrench, pose, huella, fallo/degradación y geometría de formación; salida: entrega o aborto seguro | Acoplamiento decisión--movimiento, control distribuido de pose/velocidad, guardia mecánica y de seguridad, reconfiguración y re-reclutamiento | Estructura virtual/leader--follower, QP central de fuerzas, PD de pose, LQI, port--Hamiltoniano, NMPC central como techo, CBF--QP/ORCA y reparación central/voraz | B para propiedades locales bajo contactos fijos; C para integración, cambios de geometría, sustitución física y desacoplamiento | Nuclear |
| SP3 | ¿Cómo coordinar simultáneamente robots libres, reuniones y coaliciones de distinto tamaño ante cruces, prioridades, congestión y tareas dinámicas? | Rutas, reservas espaciotemporales, prioridad con envejecimiento, huella, estado de misión, replanteamiento y vistas vecinales imperfectas | Juego potencial de rutas + reserva local de recursos + replanteamiento asíncrono y retransmisión versionada | CBS/ECBS u oráculo restringido, planificación priorizada, ORCA/RVO y variantes con información perfecta | C para tráfico discreto, escala y red imperfecta; seguridad continua y completitud global pendientes | Nuclear, con alcance experimental delimitado |

## 4. Correspondencia con campañas históricas

Los códigos siguientes se conservan en rutas, módulos, configuraciones, manifiestos e IDs de afirmaciones para no romper la reproducibilidad. En la memoria se presentan como **etapas experimentales**, no como subproblemas canónicos.

| SP canónico | Etapa histórica | Función dentro del SP |
|---|---|---|
| SP1 | `sp1_canonical` | Campaña regenerable integrada de reclutamiento heterogéneo, roles/contactos, start/wait, cambio y gossip vecinal |
| SP1 | `sp1_canonical/validation` | Batería E0--E6 de recursos agregados: LP/MILP, dinámica poblacional vecinal, conectividad, discretización, cierre entero, escala y aproximación uniciclo |
| SP1 | `sp0` | Calibración uno-a-uno, exclusividad y referencia Hungarian |
| SP1 | `sp1` | Cardinalidad variable, cuórum y cierre entero |
| SP1 | `sp2` | Heterogeneidad y contribución operacional robot--carga |
| SP1 | `sp3` | Asignación de slots/contactos y certificado planar de wrench |
| SP2 | `sp2_canonical/SP2_HONORS_v3` | Cadena N1--N4 para cinemática de pivotes, soporte 2.5D, red local, control, revalidación conjunta y modos de frenado/pérdida de autoridad sobre mundos pareados |
| SP2 | `sp4` | Aproximación, docking y transporte de pose |
| SP2 | `sp5` | Seguridad de la huella compuesta frente a obstáculos |
| SP2 | `sp6` | Fallo, re-reclutamiento y viaje del reemplazo |
| SP2 | `cargo-e2e` | Demostrador híbrido de selección, llegada posicional, transporte, obstáculo y sustitución hasta pose de entrega; no ejecuta liberación física ni descentralización completa |
| SP3 | `sp7` | Rutas y reserva local entre coaliciones |
| SP3 | `sp8` | Escala, retardo, pérdida y coste de comunicación |
| SP3 | `aws-industrial2` | Piloto cinemático de congestión y replanteamiento |

`sp1_canonical` es el módulo vigente y `sp1_canonical/validation` es su batería de validación por capas; las demás filas son etapas históricas. Un resultado conserva exactamente su modelo, información y alcance. La agrupación no permite transferir automáticamente una garantía al SP canónico completo. En particular, E6 finaliza al llegar a poses de aproximación y no valida contacto ni transporte.

La vista editorial `sp1_levels_23p` organiza evidencia existente sin crear
subproblemas nuevos: N1 pregunta cuándo la cardinalidad representa exactamente
la capacidad; N2 introduce atomicidad; N3 estudia la localidad informativa; y
N4, la localidad estratégica. La secuencia queda congelada como una cadena
causal, no como cuatro campañas independientes. F-I reúne los juegos potenciales
atómicos y contiene la contribución principal, Geo-QPG y la localidad de orden
$h$. F-II es el contraste estructural entre estado continuo y cierre entero;
F-III es una formulación alternativa primal--dual de un vGNE con restricciones
compartidas; F-IV queda delimitada como extensión dinámica piloto. Consensus/DAC y los registros
versionados son infraestructura de información transversal, no una quinta
familia. La campaña N4 v3 implementa F-II y F-III sobre los mismos mundos de
F-I y aplica un cierre atómico común; F-IV se evalúa en una campaña temporal
separada.

Dentro de F-I, BR, 2BR y C3 forman un refinamiento anidado de estabilidad local
de orden $h=1,2,3$; Geo-ASR y Geo-LLL son ablaciones de la regla de revisión
dentro de $h=1$. Las propuestas calculadas sobre las mismas versiones forman un
grafo de conflictos: CF conserva un orden global como ablación y DMIS+TX
selecciona un lote independiente mediante arbitraje vecinal y commit por cargas.
DPOP se usa únicamente como oráculo distribuido exacto en instancias pequeñas.
F-II y F-III entran en el ranking E7 únicamente después de compartir cierre
entero, instancias, oráculo y endpoints. Sus residuos continuos se conservan
como diagnósticos de familia y no sustituyen la comparación física.
N1--N2 solo se comparan
bajo el mismo problema homogéneo; N2--N4 conservan la diferencia entre oráculo
global y negociación vecinal. Una guía previa define N1--N4 y las ramas N3.1 y
N3.2 sin confundirlas con nuevos SP ni con niveles de evidencia. Antes de N1
presenta dos páginas comunes: escenarios y métricas/estadística.
N1 ocupa después seis páginas cerradas: modelo, diseño de cuatro experimentos y
una página independiente para cada contraste E1--E4. La última página establece
la transición motivada a N2. N4 conserva el problema heterogéneo y el contrato
de información de N3; el MILP se usa como techo experimental y no como
arquitectura candidata. La campaña N4 v2 separa la comparación de calidad E4,
la exactitud pequeña de DPOP E5 y el escalado observado E6. El programa por
preguntas registra Q1--Q9: Q2 usa E4, Q5 usa E5 y Q6 usa E6; Q4 dispone solo del
control nominal CF--DMIS+TX de E4. E7 responde Q7 mediante cuatro dinámicas
poblacionales y un cierre común, y Q8 mediante una referencia central y un
algoritmo primal--dual distribuido con residuos conjuntos. E8 añade el piloto
temporal F-IV sin mezclarlo con el ranking estático. E9 responde Q1: reproduce
el terminal BR desde reposo y enumera exactamente las desviaciones conectadas
de dos y tres robots sobre 1.200 mundos, con un barrido independiente de
$N/K$. Quedan pendientes Q3 (estado completo frente a agregados) y Q9 (canal
degradado). Ninguna campaña valida
todavía contacto o transporte.

El resultado central de N4 es la medición del primer orden de escape del terminal
BR. En E9, la gran mayoría de los escapes observados fue bilateral; esta
observación enlaza la estructura local, el refinamiento BR--2BR--C3 y la mejora
de calidad. Su alcance se limita a la inicialización, los mundos sintéticos y la
búsqueda conectada hasta $h=3$. No se interpreta `>3` como optimalidad.

## 5. Dependencias

```text
SP1: reclutamiento -> cierre -> rol/contacto -> certificado previo
                                      |
                                      v
SP2: aproximación -> acoplamiento -> transporte seguro -> sustitución -> liberación
                                      |
                                      v
SP3: ruta/reserva -> prioridad/cruce -> congestión -> replanteamiento -> red/escala

Escala, comunicación, coste y resiliencia --------------------------> SP1..SP3
```

No se evalúa tráfico multi-coalición como sistema físico continuo antes de disponer de una interfaz SP2 estable y métricas verificadas. La evaluación de escala comienza en SP1 y culmina en SP3.

## 6. Capítulo de Resultados y análisis

> **Enmienda 2026-09-02.** La formulación general y el protocolo común dejan de
> ser secciones del capítulo 6 y pasan al capítulo 4, Metodología. Motivos: (a)
> las Instrucciones VIU asignan a Metodología el diseño de investigación, las
> variables, los instrumentos, el análisis de datos y las fases, que es
> exactamente este material; (b) estaban duplicados con
> `\subsection{Escenarios, variables y métricas}` y
> `\subsection{Validación estadística y CoppeliaSim}` del capítulo 4; (c)
> Metodología estaba en 5 páginas contra un presupuesto de 9 y el capítulo 6 en
> 62 contra 34–39. El capítulo 6 empieza ahora en SP1. Ningún contenido se
> elimina: se traslada, y la versión que sobrevive de cada duplicado es la más
> completa.

### 6.1 SP1 — Formación distribuida de coaliciones

Integra las etapas históricas de asignación, cuotas, heterogeneidad y certificado de roles/contactos. Aquí se concentra la aportación estratégica principal.

### 6.2 SP2 — Ejecución y transporte cooperativo

Integra docking, transporte de pose, seguridad, recuperación y demostración Cargo. Cargo es el modo primario; empuje/caging es una extensión secundaria con modelo de contacto propio.

### 6.3 SP3 — Planificación y tráfico de múltiples coaliciones

Integra rutas, reservas, prioridad, escala, red imperfecta y el piloto de congestión. Las garantías discretas no se presentan como seguridad continua ni completitud MAPF.

### 6.4 Discusión transversal

- respuesta a RQ1–RQ5;
- comparación entre garantías y resultados;
- coste de descentralización;
- regiones de fallo;
- amenazas a la validez;
- límites de generalización.
