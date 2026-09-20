# Implementación de `pre-thesis`, memoria VIU y monografía técnica

## Propósito

Construir un árbol documental nuevo, autocontenido y reproducible que consolide únicamente material trazable del repositorio. El entregable principal será una memoria VIU en español y el secundario una monografía técnica separada; ambos compilarán desde la misma notación y registro de resultados formales sin depender de rutas absolutas ni de enlaces vivos a `thesis/`.

## Contexto y fuentes de verdad

La implementación respeta, en este orden, `docs/00_TFM_CHARTER.md`, `docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md` y `docs/07_SP_SECTION_TEMPLATE.md`. El árbol de trabajo contiene cambios masivos del autor; por ello el trabajo será aditivo y no se ejecutarán operaciones de limpieza, restauración o descarte.

La norma VIU fija 50--80 páginas de cuerpo, un máximo de 20 páginas de anexos y al menos un 50 % del cuerpo para resultados y validación. El máximo total de 98 páginas es una restricción editorial interna. La disponibilidad efectiva de la tercera convocatoria, el cómputo de referencias y la aceptación administrativa de la réplica LaTeX se registran como verificaciones externas pendientes del Aula o del director.

## Alcance

Incluye:

- instantánea autocontenida del formato, configuración y cinco figuras TikZ protegidas;
- memoria VIU y monografía con compilación dual;
- presupuesto de páginas ejecutable y verificaciones de referencias, citas, etiquetas, artefactos y figuras protegidas;
- manifiesto deduplicado de los corpus lógicos `books`, `work`, `paper` y `thesis` —los dos primeros reubicados durante la implementación en `material/books/` y `material/compendios/`—, más el cruce fuente--afirmación--evidencia--destino;
- auditoría de resultados formales y bibliografía antes de promover material candidato;
- infraestructura reproducible para la campaña Cargo con CoppeliaSim/MuJoCo, configuración SI, semillas, telemetría y gates explícitos;
- pruebas unitarias, experimento de humo y documentación de limitaciones.

No incluye:

- modificar el título administrativo;
- convertir el banco de empuje/caging existente en evidencia Cargo;
- afirmar gemelo digital, transferencia a hardware, estabilidad global u optimalidad sin evidencia;
- copiar libros o figuras editoriales a `pre-thesis/`;
- ejecutar una campaña confirmatoria después de congelar hipótesis a partir del piloto.

## Supuestos y riesgos

1. Cargo es el modo físico primario y caging permanece como extensión separada.
2. No existen datos físicos reales; la afirmación máxima se limita al dominio parametrizado de MuJoCo.
3. Los resultados históricos `sp0`--`sp8` se conservarán por reproducibilidad, pero se presentarán bajo SP1--SP3.
4. Las referencias pendientes no respaldarán afirmaciones fuertes.
5. CoppeliaSim 4.10 con MuJoCo está disponible y la escena primaria es estructuralmente válida; permanecen abiertos los gates de transmisión, rueda--twist, desempeño terminal y sensibilidad temporal. La afirmación comparativa sigue pendiente y no se fabrican datos para cerrarla.
6. El ajuste a 98 páginas puede requerir iteraciones editoriales; ninguna de las cinco figuras TikZ protegidas puede eliminarse, rasterizarse o desactivarse.

## Diseño

`pre-thesis/` contendrá fuentes documentales, configuración, manifiestos y artefactos regenerados. El código permanecerá en `src/`, las pruebas en `tests/`, las configuraciones en `experiments/configs/` y los resultados en `results/`. Una única entrada PowerShell aceptará `-Target thesis|monograph -Verify` y hará fallar la compilación si se infringen presupuesto, trazabilidad básica, TikZ protegidos o salud LaTeX.

La memoria seguirá los ocho capítulos VIU. El capítulo 6 agrupará la historia experimental en SP1, SP2 y SP3, con una interfaz transversal y una síntesis final. La monografía recibirá demostraciones ampliadas, derivaciones alternativas, sensibilidad, resultados negativos y candidatos no promovidos.

## Diseño experimental Cargo

El banco declara un factorial de 16 celdas: masa 14/28 kg, coalición mínima/redundante, fricción baja/nominal y aceleración 0,10/0,25 m s^-2, con 30 perturbaciones pareadas. Compara capacidad agregada, LSQ planar y certificado soporte--wrench--ruedas bajo una misma ley de control. También declara sensibilidad temporal en `dt={0.005,0.01,0.02}` y registra todas las ejecuciones, incluidas las rechazadas o fallidas.

Los gates son: error de peso <=2 %, error de transmisión <=5 %, error terminal <=0,10 m y <=5 grados sostenido durante 1 s, contacto activo >=95 %, deslizamiento <=0,02 m, cero colisiones, límites de rueda/par, ausencia de NaN/Inf y repetibilidad dentro de tolerancia declarada. La campaña confirmatoria solo se ejecutará si el piloto y los readbacks físicos superan esos gates.

## Hitos

1. **Congelación y arquitectura:** registrar commit, estado, hashes, normativa y presupuesto; crear el árbol autocontenido.
2. **Integridad previa:** deduplicar corpus, auditar bibliografía, claims y resultados formales; clasificar cada unidad por destino.
3. **Build dual:** compilar memoria y monografía, conservar las cinco figuras protegidas y verificar el presupuesto.
4. **Cargo mínimo:** implementar configuración, modelos, gates, telemetría, adaptador Coppelia y pruebas; ejecutar humo seguro.
5. **Síntesis científica:** migrar solo resultados soportados, consolidar SP1--SP3 y mantener candidatos honestamente etiquetados.
6. **Cierre editorial:** regenerar cifras, revisión matemática, auditoría anti-AI, revisión independiente, renderizado página a página y paquete reproducible.

## Validación

- `pytest` sobre modelos, configuración, payoffs, restricciones, métricas, invariantes y manifiestos;
- compilación limpia de ambos objetivos, sin citas/referencias indefinidas, etiquetas duplicadas ni artefactos ausentes;
- verificador de los cinco TikZ en fuente y en el `.aux`/PDF;
- extracción de estructura física del PDF para cuerpo, resultados, referencias, anexos y total;
- renderizado de todas las páginas y revisión visual de floats, recortes, legibilidad y páginas en blanco;
- auditoría de bibliografía con evidencia externa, claims con pasaje soporte y originalidad mediante búsqueda heurística, seguida por el control profesional de antiplagio que realiza la VIU;
- manifiesto de entorno, hashes, configuración y semilla para cada corrida Cargo.

## Decisiones registradas

- Fecha: 2026-09-08. Decisión: apuntar a tercera convocatoria (predepósito 2026-11-01, depósito 2026-11-10), sujeta a disponibilidad en el expediente. Motivo: petición expresa del autor y calendario oficial local.
- Fecha: 2026-09-08. Decisión: fijar 97 páginas como objetivo y 98 como máximo físico. Motivo: límite editorial del autor más estricto que la norma.
- Fecha: 2026-09-08. Decisión: `pre-thesis/` será una instantánea, no un conjunto de enlaces a `thesis/`. Motivo: reproducibilidad y aislamiento del árbol en edición.
- Fecha: 2026-09-08. Decisión: no promover material de `paper/` o `work/` por mera procedencia. Motivo: el nivel de evidencia prima sobre la prosa existente.
- Fecha: 2026-09-08. Decisión: no llamar gemelo digital al banco Cargo. Motivo: no hay calibración con datos físicos reales.
- Fecha: 2026-09-08. Decisión: conservar la afirmación comparativa Cargo en estado `PENDIENTE`. Motivo: la escena y el preflight acotado prueban infraestructura, lectura estática, actuación por ruedas y trazabilidad, pero no ejecutan transmisión de fuerza ni rueda--twist, no estudian varios pasos temporales y no alcanzan el criterio terminal; no se reutilizó el banco de caging.
- Fecha: 2026-09-08. Decisión: bloquear toda campaña Cargo confirmatoria hasta recibir simultáneamente autorización explícita y un preflight aprobado ligado por hashes a sus artefactos, gates, configuración, escena, auditoría e implementación. Motivo: impedir que una bandera manual o evidencia histórica incompatible cree siquiera un directorio de salida; la elegibilidad posterior exige además éxito físico y gates operacionales en todas las corridas.
- Fecha: 2026-09-08. Decisión: aceptar como inventario observado 145 resultados formales en `paper/` y 21 en `thesis/`, frente a la línea base de planificación de 104. Motivo: el manifiesto final detecta deriva del corpus y debe registrar el material real, no forzar el recuento previsto.
- Fecha: 2026-09-09. Decisión: cerrar la memoria en 97 páginas físicas, con 12 preliminares, 69 de cuerpo, 39 de resultados, 8 de referencias y 8 de anexos. Motivo: cumple exactamente el objetivo editorial, el intervalo VIU del cuerpo y una fracción de resultados de 39/69 = 56,52 %.
- Fecha: 2026-09-08. Decisión: no restaurar los artefactos históricos SP1 ausentes para poner verde la suite global. Motivo: los 10 fallos históricos identificados dependen de eliminaciones preexistentes en `thesis/sp1_levels_23p/` y de dos artefactos no disponibles; restaurarlos contradiría el alcance aditivo aprobado.
- Fecha: 2026-09-08. Decisión: detener el flujo académico al terminar la etapa 2.5 y solicitar autorización antes de convocar cinco revisores. Motivo: punto de control obligatorio del pipeline académico.
- Fecha: 2026-09-08. Decisión: verificar el presupuesto bajo dos interpretaciones del cuerpo: sin referencias y contándolas. Motivo: la norma excluye expresamente preliminares y anexos, pero no resuelve de forma inequívoca el tratamiento de las referencias; ambas lecturas cumplen 50--80 páginas y Resultados conserva más del 50 %.
- Fecha: 2026-09-09. Decisión: separar el gate portátil `-Verify` de la auditoría `-AuditSources` contra los corpus vivos. Motivo: el build autocontenido debe validar un release congelado sin depender de `material/`, `paper/`, `thesis/` o `docs/`, mientras que la detección de deriva sigue disponible de forma explícita en el repositorio completo.

## Progreso

- [x] Auditoría normativa y calendario local: tercera convocatoria verificada en las páginas físicas 6--7 de la guía; confirmación del expediente en Aula pendiente.
- [x] Lectura de fuentes canónicas y selección del punto de entrada de integridad.
- [x] Instantánea e inventario estructural: 202 unidades, 187 canónicas y deduplicación por SHA-256 validadas.
- [x] Cruce documental de primer nivel: 37/37 libros y 33/33 borradores canónicos auditados; 202/202 unidades tienen SP y estado de aplicabilidad. Las 37 identidades bibliográficas de libros quedaron contrastadas el 2026-09-09 con fuente autorizada: 10 también están en el ledger y 27 requieren aún revisión contextual antes de citarse. El generador distingue 57 enlaces a claims, 104 casos no aplicables y 41 fuentes `reviewed-unlinked`, sin pendientes a nivel archivo ni `sp_target=unassigned`; las 26 fuentes `paper` y 15 `work` quedan ligadas por hash a su revisión conservadora. Sus 91 resultados formales y 266 unidades LaTeX etiquetadas conservan el estado individual y no adquieren soporte por procedencia. Las ocho fuentes activas de `thesis/` antes ambiguas quedaron adjudicadas como una macro AWS que menciona cinco claims exactos y siete documentos derivados o estructurales sin valor de evidencia independiente. Cuatro libros sin claim activo se clasificaron como contexto o consulta auxiliar. Cuatro fuentes de `paper/` importan claim-ID exactos de la auditoría formal con relación conservadora `mentions`. La notación canónica está indexada en 53 unidades, 5 se adjudican como `reviewed-local-only` y no queda ninguna revisión simbólica pendiente, conservando dos sobrecargas de `N`. La reubicación física a `material/books/` y `material/compendios/` conserva los 70 identificadores estables y todos los hashes.
- [x] Auditoría bibliográfica: 116/116 referencias verificadas.
- [x] Auditoría formal de la columna activa: 18/18 resultados usados por la memoria tienen veredicto `PASS`.
- [x] Auditoría formal exhaustiva del corpus candidato: 166/166 clasificados en 18 `PASS`, 87 `LIMITED`, 43 `FAIL`, 16 `DUPLICATE` y 2 `CONJECTURE`; el inventario formal canónico y el ledger de ideas reflejan estos veredictos y sus claim-ID exactos, con cero promociones automáticas.
- [x] Indexación editorial ampliada: el ledger reproducible registra 13.019 unidades. Las 477 unidades LaTeX añadidas —246 observaciones, 37 figuras, 48 tablas y 146 ecuaciones etiquetadas— quedan localizadas y cerradas individualmente: 21 caen dentro de un resultado formal auditado y conservan su ID, veredicto y claim-ID únicamente como contexto; las otras 456 poseen decisión semántica explícita ligada al hash, con cero etiquetas pendientes. Los veinte bindings de `thesis/` reúnen 137 decisiones y tres contextos formales; sus 140 destinos son 72 al cuerpo, 48 a la monografía y 20 `archive-only`. Dos bindings cubren las quince piezas del ensayo exploratorio `megajuego`: catorce candidatas monográficas y una síntesis excluida. Veinticinco bindings técnicos cubren las 304 decisiones restantes: 214 candidatas monográficas y 90 exclusiones por ausencia de artefactos, fallo formal, duplicación, conflicto arquitectónico, ley física inconsistente o sobregiro. Globalmente, las 456 decisiones se distribuyen en 116 definiciones, 123 límites, 169 contextos, doce protocolos y 36 resúmenes de evidencia; sus destinos son 69 `thesis-body`, 276 `monograph` y 111 `archive-only`. Sumados los 21 contextos formales, las 477 etiquetas quedan en 72 `thesis-body`, 294 `monograph` y 111 `archive-only`. Ninguna asociación se infiere por proximidad y solo las decisiones explícitas pueblan `claim_ids`.
- [x] Gate de trazabilidad integrado en el build: ambas variantes con `-Verify` validan el sello autocontenido de todos los insumos no efímeros y la consistencia interna del inventario, revisión claim--archivo, auditoría formal, ledger de ideas, citas e identidades bibliográficas. `-AuditSources` mantiene separada la comparación reproducible contra los corpus vivos.
- [x] Build de memoria: 97 páginas, presupuesto por capítulo y cinco TikZ protegidos verificados.
- [x] Build final de monografía con atlas formal: 110 páginas, dos compilaciones `-Verify` idénticas y hash congelado.
- [x] Reproducibilidad portátil: una exportación de 291 insumos sellados más `release-manifest.json`, sin raíces externas, compiló ambos objetivos y reprodujo byte a byte sus SHA-256; el `/ID` del trailer se fija por identidad lógica del documento. El único límite restante es que el árbol todavía no está versionado.
- [x] Escena Cargo estructuralmente válida y preflight MuJoCo acotado 6/6 con paquete hash-bound; transmisión, rueda--twist, terminal y sensibilidad multirrate pendientes; campaña confirmatoria no autorizada.
- [x] Refresco final de integridad de etapa 2.5 y auditoría visual de 207/207 páginas: 76 citas activas verificadas, 202/202 consultas heurísticas de originalidad sin coincidencia exacta y cero defectos visuales pendientes.
- [ ] Etapa 3: revisión independiente de cinco revisores, pendiente de autorización del autor.
- [ ] Confirmación externa en Aula de tercera convocatoria y aceptación administrativa de la réplica LaTeX, pendiente de inicio de sesión del autor/director.
