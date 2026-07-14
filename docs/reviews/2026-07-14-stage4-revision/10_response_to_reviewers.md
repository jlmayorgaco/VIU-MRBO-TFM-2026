# Response to Editor and Reviewers — Stage 4

Estimado editor y revisores:

Gracias por una revisión precisa y constructiva. La revisión se abordó como una corrección
de integridad claim–evidencia, no como una ampliación retórica. Se sustituyó el diseño
adaptativo integrado por una campaña nueva de tamaño fijo, se hizo explícita la contribución
híbrida de la arquitectura, se bloqueó cualquier sobrelectura del comparador aprendido y se
centralizó la trazabilidad de afirmaciones y contrastes.

## R1 — Contribución, causalidad y localidad

**Respuesta.** A0 es una política diagnóstica de utilidad más umbral global, no un juego
formal. El título, Summary, Abstract, posicionamiento y conclusiones dicen ahora
“arquitectura escalonada con componentes basados en juegos”. Ningún incremento A0--FULL se
atribuye a un componente cuando el tratamiento incorpora un paquete; FULL se interpreta
como memoria–comunicación–reemplazo. Los controles uniforme+QR y uniforme+guardia se
mantienen como explicación rival central.

**Cambios.** Tablas `presupuesto-centralizacion` y `mecanismo-por-experimento` en
Metodología; matriz de originalidad y posicionamiento en Marco teórico; semántica de paquete
en Resultados y Conclusiones. **Estado solicitado:** `addressed`.

## R2 — O5 y MARL-CTDE

**Respuesta.** Se añadió el protocolo reproducible de MAPPO--GNN cfg03: actor GNN local de
3 capas/64 unidades, crítico global solo en entrenamiento, tres semillas 15001--15003,
200.000 transiciones conjuntas por semilla y hashes de los tres checkpoints. La auditoría
obtiene éxito RAW cero tanto para controles como para checkpoints y éxito uno después de
reparación. El gate de sensibilidad falla; por ello O5 se declara cubierto para comparadores
clásicos/model-based y solo documentado, no validado favorablemente, para MARL.

**Cambios.** Tabla `protocolo-marl`; Alcance de O5; `claim_artifact_registry` C-SP0.
**Estado solicitado:** `addressed`.

## R3 — Regla 40–60–100

**Respuesta.** La regla adaptativa fue retirada de la evidencia canónica. Se ejecutó un
protocolo distinto con ID, semillas y freeze nuevos: 100 mundos fijos en cada una de cuatro
familias y seis tratamientos por mundo, 2.400 filas. No existe parada opcional. Los veinte
contrastes, seeds de bootstrap, McNemar, IC y Holm se fijaron antes de abrir test.

**Cambios/evidencia.** `PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN.yaml`, contrato de
hipótesis, registro de semillas, `FINAL_RUN_MANIFEST.json` y Resultados integrados. La v1
adaptativa está marcada `superseded_noncanonical`. **Estado solicitado:** `addressed`.

## R4 — Estimando, prueba e intervalo

**Respuesta.** A0--FULL estima diferencia de riesgos pareada; usa McNemar exacto bilateral,
IC bootstrap pareado y Holm. Para SP4 se reconoció que los seis escenarios comparten cada
bloque semilla--flota. Las 108 estimaciones se conservan como descripción y la inferencia
se repite sobre 18 bloques mediante test de signos exacto con Holm. Las cinco direcciones
permanecen respaldadas.

**Cambios/evidencia.** `contrast_estimand_registry.csv/json/md`, tabla completa A0--FULL,
tabla `sp4-block-sensitivity` y `statistics/block_sensitivity.*`. **Estado solicitado:**
`addressed`.

## R5 — Sensibilidad y robustez paramétrica

**Respuesta.** La palabra robustez se restringe a variación dentro de las cuatro familias.
Se añadió una tabla con residual, masa/inercia, paso, horizonte, radio, ganancias HOCBF,
capacidad/fuerza/salud, demanda, red, contacto/fricción y riesgo de inversión. Los valores
sin barrido aparecen como “sensibilidad no estimada”.

**Cambios.** Tabla `parametros-integrados` y Limitaciones. **Estado solicitado:**
`addressed`.

## R6 — Modalidad y evidencia física

**Respuesta.** Python A0--FULL y SP4 v3 son simulaciones reducidas. SP4 v4/Coppelia es un
replay cinemático de trayectorias, sin controlador o dinámica independiente. HIL y hardware
no se realizaron. Cero colisiones observadas nunca se equipara a invariancia continua ni a
seguridad funcional.

**Cambios.** Tablas `identidad-evidencia` y `modalidades-validacion`; claims de SP4/SP5 y
Limitaciones. **Estado solicitado:** `addressed`.

## R7 — Registro claim–artefacto

**Respuesta.** Se publicó un registro único C-INT/C-SP0…C-SP8 con estado, claim autorizado,
configuración, registro de semillas, comando, manifiesto, evidencia, tres hashes y límite.
Las ausencias SP7/SP8 se marcan `NO_DISPONIBLE`; SP4 v3/v4 y la campaña integrada v1/v1.1
quedan inequívocamente separadas.

**Cambios/evidencia.** `docs/generated/claim_artifact_registry.csv/json/md`, tabla compilada
y `docs/CANONICAL_RESULTS.md`. **Estado solicitado:** `addressed`.

## R8 — Sensibilidad confirmatoria acotada

**Respuesta.** No se adoptó un barrido post-hoc. Elegir después de observar resultados qué
parámetros y rangos variar no habría reparado la regla adaptativa ni producido evidencia
confirmatoria. La revisión priorizó una campaña correctiva de tamaño fijo y semillas nuevas.
Una sensibilidad multidimensional queda como protocolo separado futuro; R5 conserva todos
los límites y riesgos de inversión.

**Cambios.** Justificación tras la Tabla `parametros-integrados` y Limitaciones.
**Estado solicitado:** `justified` (`DELIBERATE_LIMITATION`).

## R9 — Puente dinámico, contacto y despliegue

**Respuesta.** Se añadió una progresión verificable: G1 motor dinámico cerrado con
fricción/slip/saturación/abstención; G2 HIL con latencia, sensores, actuadores, watchdog y
E-stop; G3 piloto AMR con zona segregada, criterios de aborto y rescate. Cada gate contiene
entrada, salida, peligros y responsables. Se rotula como plan futuro, no como evidencia.

**Cambios.** Tabla `gates-validacion-futura`. **Estado solicitado:** `addressed`.

## R10 — Derivación y edición

**Respuesta.** El compilado contiene ahora la equivalencia KKT/v-GNE de SP3 y su frontera
con el cierre entero. Se cualificaron las figuras de gap, Nash/Smith y estado del arte; se
añadió Sontag (1989) como referencia ISS fundacional; se amplió la nomenclatura y se corrigió
“Tampoco”. La progresión del Marco teórico se reordenó a fundamentos → familias/estado del
arte → brecha/posicionamiento → comprobaciones V1--V3.

**Cambios.** Modular Evidence SP3, Theory ISS, figuras, Nomenclatura y bibliografía.
**Estado solicitado:** `addressed`.

## Síntesis

Se responden 10/10 observaciones: nueve resueltas mediante cambios y una preservada como
límite deliberado metodológicamente justificado. La revisión no reclama aceptación ni nota
automática; solicita re-evaluación sobre el manuscrito y los artefactos verificados.

Atentamente,

**El autor**
