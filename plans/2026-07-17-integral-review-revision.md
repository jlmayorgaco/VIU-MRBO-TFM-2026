# Revisión integral posterior al dictamen de 124 páginas

## Propósito y resultado observable

Contrastar el dictamen integral recibido el 17 de julio con la versión vigente de la memoria y corregir las observaciones que sigan siendo válidas. El resultado observable será una memoria matemáticamente consistente, estadísticamente trazable y libre de residuos editoriales, acompañada de una matriz que distinga observaciones resueltas, limitaciones deliberadas y desacuerdos sustentados.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, la fuente LaTeX en `thesis/`, el código en `src/viu_mrob_tfm/`, las configuraciones versionadas y los resultados procesados. El nuevo dictamen se conserva fuera del repositorio como adjunto de la tarea. `docs/12_REVIEWER_REVISION_TRACKING.md` registra una ronda anterior y se ampliará sin borrar decisiones históricas.

El árbol de trabajo contiene una migración amplia previa a esta revisión. No se restaurarán ni revertirán borrados o modificaciones ajenos. Las ediciones se limitarán a la memoria, pruebas focalizadas, trazabilidad y este plan.

## Alcance y no alcance

Incluye la revisión de los P0 matemáticos y lógicos de SP2, SP3, SP4 y SP8; coherencia de Cargo; inferencia estadística; terminología; citas LaTeX visibles; resumen, hipótesis y conclusiones cuando dependan de esas correcciones; compilación e inspección del PDF.

No incluye fabricar una campaña dinámica en CoppeliaSim, reconstruir generadores históricos ausentes ni elevar evidencia experimental sin nuevos datos. La solicitud vigente del autor prioriza completitud científica sobre una poda arbitraria; cualquier conflicto con el límite administrativo se registrará como riesgo formal, no se resolverá suprimiendo contribuciones sin autorización.

## Supuestos y preguntas resueltas

- El dictamen describe una versión de 124 páginas; cada observación debe verificarse en la fuente actual antes de editar.
- El título administrativo permanece en AMR por precedencia del `Charter`.
- La paginación seguirá la plantilla oficial auditada en `docs/06_VIU_TEMPLATE_FIDELITY.md`; no se aplicará numeración romana si contradice esa fuente.
- CoppeliaSim solo se presenta como evidencia dinámica si existen actuadores, contacto, estado medido, configuración y resultados reproducibles.
- Una observación estadística que requiera reanalizar datos existentes puede corregirse; una que requiera nueva evidencia se clasifica como trabajo pendiente o limitación.

## Diseño matemático/técnico

La auditoría verificará: (i) que el gradiente del potencial SP2 coincida con el incentivo marginal; (ii) que la imposibilidad SP8 use instancias localmente indistinguibles bajo una interacción remota no observable; (iii) que SP4 defina o elimine toda variación total y no confunda potencial diferencial con potencial exacto; (iv) que SP3 reporte cobertura/abstención o limite explícitamente el alcance de su precisión; y (v) que Cargo y las conclusiones distingan composición planar de validación física.

Las correcciones estadísticas respetarán la instancia base como unidad independiente, conservarán emparejamiento y multiplicidad, y sustituirán «refutada» por «no sustentada» cuando un contraste no rechace la hipótesis nula sin demostrar equivalencia.

## Plan experimental

No se ejecutará una nueva campaña salvo que un artefacto existente permita regenerar de forma exacta una tabla o figura. Se usarán pruebas unitarias, diferencias finitas, enumeración exhaustiva y reprocesamiento de CSV/JSON ya versionados. Toda cifra incorporada a LaTeX se contrastará con datos procesados.

## Hitos

- [x] Matriz completa del nuevo dictamen con estados y evidencia actual.
- [x] P0 matemáticos/lógicos vigentes corregidos y probados.
- [x] Métricas e inferencia SP3/Cargo/H3 corregidas o delimitadas.
- [x] Residuos editoriales, terminología y citas auditados.
- [x] Trazabilidad sincronizada, suite completa superada y PDF revisado.

## Validación

- `python -m pytest -q`
- pruebas focalizadas de SP2, SP3, SP4, SP8 y Cargo;
- búsqueda en fuentes y PDF de `parencite`, `textcite`, `??`, `TODO`, `FIXME`, `passed`, `v4` y terminología prioritaria;
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`;
- inspección del log LaTeX, texto extraído y páginas modificadas.

## Riesgos y mitigaciones

- **Dictamen desactualizado:** verificar fuente y artefactos antes de modificar.
- **Árbol de trabajo ajeno:** aplicar parches focalizados y revisar el diff por ruta.
- **Sobreafirmación física:** mantener CoppeliaSim y Cargo en su nivel real de evidencia.
- **Reanálisis estadístico incorrecto:** identificar explícitamente la unidad independiente y agrupar por instancia.
- **Poda destructiva:** no eliminar contenido formal solo para alcanzar una cifra de páginas sin reconciliar primero el contrato VIU y la instrucción del autor.

## Registro de decisiones

- 2026-07-17: se adopta el modo de revisión académica con trazabilidad punto por punto; no se aceptan comentarios del revisor de forma automática.
- 2026-07-17: las auditorías paralelas son de solo lectura y las ediciones permanecen centralizadas.
- 2026-07-17: el pase prioriza P0 verificables; CoppeliaSim dinámico y reconstrucción histórica no se simulan ni se inventan.
- 2026-07-17: la objeción al factor del potencial SP2 no se confirmó; se conserva la formulación y se añade una prueba en los tres regímenes de saturación.
- 2026-07-17: Cargo se clasifica como simulación planar reducida con registro global y reconstrucción de poses tras el acoplamiento; no se presenta como validación de contacto rueda--suelo.
- 2026-07-17: la unidad inferencial de Cargo y SP8 pasa de escenario/régimen a instancia independiente agrupada.
- 2026-07-17: se mantiene abierta la campaña dinámica CoppeliaSim porque el artefacto disponible terminó en error y el runner histórico no reproduce el modelo físico declarado.

## Progreso

Revisión cerrada. Se regeneraron Cargo (360 mundos, 2160 ejecuciones), SP8 (900 mundos, 4500 ejecuciones) y las métricas SP3; `python -m pytest -q` superó 72 pruebas. El PDF final contiene 129 páginas, con resumen/abstract de 283/271 palabras, sin referencias ni citas indefinidas y con inspección visual de las páginas modificadas. La validación dinámica independiente en CoppeliaSim permanece como limitación abierta y no se sustituye por evidencia narrativa.
