# Cierre de observaciones P0/P1 de la revisión de `main(11).pdf`

## Propósito y resultado observable

Resolver el dictamen externo del 17 de julio sin elevar el nivel de evidencia de forma artificial. El resultado observable será una memoria cuya semántica física de SP2 y cadena dimensional de SP5 sean coherentes, cuya arquitectura distribuida se audite por capas, cuyos preliminares y tablas cumplan la presentación VIU, y cuya validación CoppeliaSim se clasifique exclusivamente según la dinámica realmente ejecutada. Cada cambio tendrá prueba, artefacto o limitación explícita.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, la fuente LaTeX en `thesis/`, los módulos actuales en `src/viu_mrob_tfm/`, las configuraciones en `experiments/configs/` y los resultados procesados. El dictamen está en el adjunto `pasted-text.txt`. El título administrativo canónico de `docs/00_TFM_CHARTER.md` usa AMR; el nombre del Anexo I contiene AGV, pero no autoriza por sí solo a sustituir el título registrado.

El árbol de trabajo contiene una migración extensa con borrados y archivos nuevos previos a este pase. No se restaurarán ni revertirán rutas ajenas. Los antiguos scripts y escenas de CoppeliaSim solo se consultarán como antecedente; cualquier recuperación o sustitución quedará limitada al nuevo protocolo de validación.

## Alcance y no alcance

Incluye la auditoría completa del dictamen; corrección editorial y matemática de SP2 y SP5; tabla transversal de arquitectura; PoS/PoA y resultados de red si ya cuentan con prueba; numeración preliminar; nomenclatura; compactación de tablas; trazabilidad; pruebas y compilación.

Incluye una validación cuantitativa CoppeliaSim únicamente si puede ejecutarse con motor dinámico, estado medido y configuración versionada. No se llamará dinámica a una reproducción cinemática. No incluye hardware, contacto 3D validado, soporte vertical realista ni cambio del título administrativo sin autorización.

## Supuestos y preguntas resueltas

- SP2 conserva los datos históricos, pero `e_ik` se interpreta como índice operacional de servicio, no como capacidad mecánica ni kilogramos equivalentes.
- La capacidad física nominal y la factibilidad energética se definen por separado como extensión del modelo; los resultados existentes no se recalculan ni se reinterpretan como evidencia mecánica.
- SP5 debe declarar explícitamente la transformación de velocidad filtrada a aceleración traslacional, el canal angular y el error de realización antes de formular el wrench aplicado.
- La propiedad «distribuida» se descompone en decisión, agregado/estimación, cierre, certificación y planta; una lectura global declarada no se oculta como local.
- La campaña Cargo integrada en Python acredita composición empírica planar, pero no sustituye CoppeliaSim.
- El título administrativo permanece en AMR hasta que el autor aporte una resolución o solicitud aprobada distinta.

## Diseño matemático/técnico

En SP2 se separarán `c_i^pay` (kg, capacidad nominal física), `a_ik=psi_i^b psi_ik^d` (adimensional, disponibilidad operacional) y `e_ik=c_i^pay a_ik/c_ref` (adimensional, índice de servicio normalizado). La demanda histórica se expresará como umbral de servicio `d_k^srv`; la cobertura de SP2 será operacional. SP3 seguirá siendo el primer certificado mecánico.

En SP5 se definirá
`a_{k,tr}^{fil}=sat_A((v_k^{fil}-v_{k,m}^L)/Delta t)`,
`a_k^{fil}=[a_{k,tr}^{fil}; alpha_k^{fil}]` y
`W_k^{fil}=M_k a_k^{fil}+D_k dot(q)_k^L`.
La acción aplicada se evaluará mediante un margen `epsilon_act` que agrupa discretización, saturación, reparto, predicción e iteraciones finitas; no se inferirá invariancia.

La arquitectura transversal añadirá columnas para decisión, agregado/estimación, cierre, certificación y planta, con el estado real de SP0--SP8 y de la campaña integrada.

La validación CoppeliaSim, si supera el gate técnico, utilizará ejecución por pasos, motor físico declarado, estado medido desde la escena y al menos tres escenarios: nominal, obstáculo y fallo. Registrará éxito, tiempos, error de pose, residual de wrench, distancia mínima, contactos/saturaciones y mensajes. Una campaña sin contactos o actuadores dinámicos se conservará como verificación geométrica.

## Plan experimental

- Mantener las campañas Python existentes como referencia y ejecutar únicamente procesadores reproducibles.
- Diseñar un humo CoppeliaSim antes de la campaña: una semilla por escenario, estado medido, sin teletransporte cinemático, artefactos finitos y manifiesto.
- Si el humo pasa, congelar al menos diez semillas por condición y comparar mecanismo vecinal, baseline local y referencia global con instancias pareadas.
- Generar tablas y figuras desde CSV: montaje, trayectorias, error/residual y comparación Python--CoppeliaSim.
- Conservar fallos y timeouts en el denominador; no codificar cifras manualmente en LaTeX.

## Hitos

- [x] Hito 1 — Matriz completa del dictamen y estado actual documentados sin comentarios omitidos.
- [x] Hito 2 — SP2 usa semántica operacional dimensionalmente honesta; código, notación y claims quedan sincronizados.
- [x] Hito 3 — SP5 explicita velocidad--aceleración--wrench y prueba sus transformaciones e invariantes.
- [x] Hito 4 — Arquitectura distribuida, título administrativo, preliminares, nomenclatura y tablas quedan corregidos.
- [x] Hito 5 — Resultados P1 ya demostrables (NE/PoS/PoA y certificado de precios locales) se elevan al cuerpo sin duplicar pruebas.
- [x] Hito 6 — Humo CoppeliaSim clasificado como dinámico o geométrico mediante gates verificables.
- [x] Hito 7 — Campaña CoppeliaSim cuantitativa final o limitación defensiva queda trazada en resumen, discusión y conclusiones.
- [x] Hito 8 — Suite, regeneración de evidencia, compilación, revisión visual y diff final completados.

## Validación

- `python -m pytest -q`
- Procesadores focalizados de SP2, SP5 y Cargo integrados.
- Gate CoppeliaSim: proceso real, stepping, motor/paso registrados, estado medido, ausencia de teletransporte, artefactos y semillas.
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- búsqueda de referencias/citas indefinidas, símbolos ausentes, `kg_eq`, claims de hardware y tablas por debajo de 7 pt;
- revisión visual del PDF completo, con atención a preliminares, tablas SP0--SP8 y nueva sección transversal.

## Riesgos y mitigaciones

- **Sobreafirmar CoppeliaSim:** separar `kinematic_replay`, `dynamic_simulation` y hardware en campos de manifiesto y lenguaje de la memoria.
- **Romper comparabilidad de SP2:** conservar datos y scores; cambiar la semántica y normalización documentada, no las cifras históricas.
- **Ocultar centralización:** registrar cada lectura global y cada guardia central en la tabla de arquitectura.
- **Exceder páginas VIU:** compactar tablas y redundancias antes de añadir la validación transversal.
- **Alterar cambios previos:** editar solo rutas enumeradas y revisar el diff focalizado; no restaurar eliminaciones masivas.
- **CoppeliaSim no reproducible:** si el motor o la escena no satisfacen el gate, registrar el bloqueo y usar la opción defensiva; no publicar métricas sintéticas como si fueran medidas.

## Registro de decisiones

- 2026-07-17 — El título administrativo permanece en AMR por precedencia de `docs/00_TFM_CHARTER.md`; la discrepancia con el nombre del Anexo I se documenta, no se resuelve por inferencia.
- 2026-07-17 — Se adopta la reinterpretación operacional de SP2 para preservar evidencia sin mezclar disponibilidad con capacidad mecánica.
- 2026-07-17 — La campaña Cargo integrada en Python y CoppeliaSim se mantienen como dos niveles de validación distintos.
- 2026-07-17 — Los replays previos de SP4 siguen clasificados como cinemáticos.

## Progreso

Revisión científica cerrada en `docs/12_REVIEWER_REVISION_TRACKING.md`. SP2 quedó reinterpretado como servicio operacional; SP5 cierra la cadena dimensional; SP6 contiene caracterización exacta, PoS y PoA; y SP0 eleva la cota de precios locales con dependencia espectral. El PDF compila en 116 páginas y la suite pasa 69 pruebas. CoppeliaSim 4.10.0 superó el gate de stepping y dinámica medida, pero el runner histórico no representa Pioneer 3-DX ni contacto rueda--suelo/carga; por tanto, no se incorporó una campaña cuantitativa artificial y la validación dinámica independiente permanece abierta.
