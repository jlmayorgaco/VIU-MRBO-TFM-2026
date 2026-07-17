# Comparación multiescenario AWS Industrial 2

## Propósito y resultado observable

Crear una variante visual `Industrial 2` del hangar y una campaña separada que compare familias centralizadas y distribuidas sobre cargas heterogéneas cooperativas. La campaña debe revelar throughput, tiempo de formación, deadlock, energía, colisiones muestreadas, comunicación y coste computacional en varios regímenes de congestión.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: el método propuesto es distribuido, interpretable y acoplado a movimiento continuo.
- `docs/02_RESEARCH_MATRIX.md`: SP1--SP2 forman coaliciones; SP4--SP5 gobiernan vivacidad y seguridad; SP7--SP8 cubren tráfico y red.
- `docs/03_EXPERIMENT_PROTOCOL.md`: semillas pareadas, fallos visibles, intervalos y ablaciones.
- `tmp/scripts/coppelia/benchmark_aws_heterogeneous_coalitions.py`: simulador cinemático AWS vigente.
- `tmp/scripts/coppelia/build_aws_industrial_adversarial_scene.py`: constructor visual industrial vigente.
- `src/viu_mrob_tfm/sp5/local_navigation.py`: ley Replicator--CBF muestreada.

## Alcance y no alcance

Incluye una campaña piloto con métodos claramente rotulados según su fidelidad: oráculo MILP de asignación, subasta de coaliciones tipo CBBA, navegación recíproca local, control predictivo distribuido y método Replicator--CBF. Incluye varios layouts y tráfico controlado, y una escena `Industrial 2` con infraestructura adicional fuera de los corredores útiles.

No se llamará CBBA, ORCA o NMPC exacto a una aproximación que no reproduzca sus ecuaciones y supuestos. El primer piloto puede usar proxies explícitos para integrar y depurar la interfaz; estos no sustituyen la campaña confirmatoria. No se afirmará optimalidad global del oráculo si no integra rutas, tiempo y mecánica en una única formulación certificada.

## Supuestos y preguntas resueltas

- Hungarian queda fuera porque las tareas requieren coaliciones heterogéneas todo-o-nada.
- El oráculo central dispone de información global y se presenta como techo, no como comparación arquitectónicamente justa.
- Todos los métodos reciben los mismos mundos, destinos, baterías y actores por semilla.
- La ley continua se ejecuta digitalmente con paso declarado; las auditorías de colisión son muestreadas.
- El transporte físico continúa siendo un acoplamiento cinemático; wrench/contacto se evalúan en SP3--SP5, no se inventan aquí.

## Diseño matemático/técnico

La asignación central usa variables binarias de robot--carga y activación todo-o-nada con cuotas/capacidades. La subasta distribuida usa pujas marginales locales y cierre de cuota por componentes de comunicación. Los controladores comparten límites de velocidad, aceleración y huella. Las variantes predictivas minimizan coste finito de progreso, proximidad y esfuerzo antes del filtro CBF; la variante TFM mantiene preferencias poblacionales y consenso.

## Plan experimental

- Escenarios: centro abierto, cuello industrial, tráfico cruzado controlado y backlog alto.
- Métodos piloto: `central_milp_global_preview`, `cbba_reciprocal_proxy`, `distributed_predictive_cbf_proxy` y `replicator_cbf_tfm`.
- Semillas pareadas: dos para humo; ocho para confirmación después de cerrar invariantes.
- Métricas: entregas, formación, espera, makespan, distancia, energía, deadlock, residual RAW/SAFE/EXEC, guardias, colisiones, mensajes y CPU.
- Comparación justa: misma información dentro de cada clase o ventaja central declarada explícitamente.

## Hitos

- [x] H1 — contratos y nombres de métodos sin sobreafirmaciones.
- [x] H2 — escenarios pareados y actores dinámicos reproducibles.
- [x] H3 — escena `Industrial 2` exportada y auditada.
- [x] H4 — experimento de humo y visualizaciones.
- [x] H5 — decisión documentada sobre qué proxies merecen reproducción completa.

## Validación

- Pruebas de cuotas, exclusividad, simplex y ausencia de NaN/Inf.
- Auditoría de geometría Industrial 2 y objetos flotantes.
- Cero solapamientos muestreados o fallos explícitos por método.
- Trazas de deadlock y tiempo de CPU por ejecución.
- MP4 y screenshots inspeccionados.

## Riesgos y mitigaciones

- Proxies demasiado débiles: rotularlos y no usarlos para afirmaciones confirmatorias.
- El oráculo de asignación no es oráculo temporal: separar ambos conceptos en tablas.
- Seguridad por detención: reportar deadlock junto a colisión.
- Escena visual más densa: colocar nueva infraestructura fuera de la huella navegable y auditarla.

## Registro de decisiones

- 2026-07-17: se crea una campaña independiente; no se sobrescriben C16--C18.
- 2026-07-17: se adopta `Industrial 2` como nivel visual, no como nueva afirmación física.
- 2026-07-17: el intento con actores no reactivos se conserva como resultado negativo; la versión principal aplica una parada muestreada antes de invadir una huella ocupada.
- 2026-07-17: el siguiente baseline central debe integrar asignación y espacio--tiempo; `central_milp_global_preview` no se eleva a oráculo temporal. El siguiente baseline distribuido debe reproducir una subasta de coaliciones y un controlador publicado, no renombrar los proxies actuales.

## Progreso

Completado el piloto de 32 ejecuciones (cuatro escenarios, cuatro métodos y dos semillas). La versión corregida registró cero solapamientos muestreados, cuotas completas y destinos pareados. Solo el centro abierto produjo entregas: 0 para el central y 1 por ejecución para los tres métodos distribuidos. En los tres escenarios congestionados todos obtuvieron cero entregas en 60 s. `distributed_predictive_cbf_proxy` tuvo la menor fracción de deadlock (0,008--0,010), mientras `replicator_cbf_tfm` quedó entre 0,467 y 0,646. Es evidencia piloto negativa y no una clasificación confirmatoria.

La escena `Industrial 2` se exportó con 2.964 objetos; la auditoría declarativa informa cero colisiones de layout y cero violaciones de soporte. El MP4 3D validado cubre 56 s simulados, dos entregas, los cuatro estados de prioridad y el fallo previsto. Algunas cámaras quedan visualmente dominadas por los discos de radio; se conserva como limitación de presentación.
