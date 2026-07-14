# Revisión integral y roadmap de cierre del TFM

**Fecha de auditoría:** 11 de julio de 2026<br>
**Entregable canónico revisado:** `docs/doc-05-final-report/main.pdf`<br>
**Alcance:** organización, escritura, narrativa, estructura, metodología, estadística, matemáticas, claims, teoría de juegos, robótica, código, resultados, referencias, reproducibilidad y maquetación.
**Modo de revisión:** lectura crítica del PDF y contraste selectivo contra LaTeX, código y artefactos. El manuscrito se mantuvo en modo solo lectura.

## 1. Veredicto

**Revisión mayor / reject & resubmit antes de defensa.**

El TFM tiene una idea científica valiosa, una infraestructura reproducible muy superior a la habitual y una presentación formal avanzada. Puede convertirse en un trabajo sobresaliente. Sin embargo, en su estado actual no es todavía “10/10 bulletproof” ni submit-ready: varios resultados centrales no permiten la interpretación que reciben en el texto y H7–H8 contienen bloqueos de validez.

Conviene separar tres planos:

| Plano | Readiness actual | Juicio |
|---|---:|---|
| Entregable formal VIU | 8,4/10 | Muy avanzado en estructura, extensión, presentación y trazabilidad |
| Solidez científica de los claims | 6,2/10 | Hay problemas constructivos e inferenciales que afectan conclusiones centrales |
| Preparación como artículo Q2 | 4,7/10 | Falta foco, validación integrada y comparadores externos fieles |

Estas cifras son un diagnóstico de readiness, no una predicción de la calificación oficial. La guía de VIU sitúa 9,0–10 en Sobresaliente; la Matrícula de Honor requiere al menos 9, pero es discrecional y está sujeta al cupo institucional.

## 2. La tesis que sí puede ser poderosa

La evidencia disponible no sostiene una narrativa de superioridad universal de Smith-QR. Los propios resultados conservan fallos y muestran referencias mejores en distintos SP. La contribución más fuerte es:

> **Este TFM propone una arquitectura de validación escalonada para coaliciones físicas multi-AMR y demuestra que la factibilidad de asignación no implica factibilidad de transporte: deben certificarse separadamente cierre entero, capacidad, wrench, movimiento, pose de carga, recuperación, conectividad y escalabilidad.**

Esta tesis convierte los resultados negativos en conocimiento científico: muestra dónde y por qué se rompe una coalición que sería “válida” bajo una capa más débil.

Si no se ejecuta una campaña integrada, el título debería hablar de **arquitectura modular y validación escalonada**, no de arquitectura “acoplada”. Smith-QR debe quedar como un mecanismo estudiado, no como vencedor general.

## 3. Scorecard exigente

| Dimensión | Nota /10 | Diagnóstico |
|---|---:|---|
| Organización documental | 8,6 | Completa y profesional; el relato se fragmenta entre SP1–SP8 |
| Escritura | 8,2 | Clara y prudente; presenta cadencia formulaica y repeticiones |
| Narrativa científica | 6,4 | Oscila entre algoritmo, familia de controladores, arquitectura y benchmark |
| Originalidad | 7,5 | “Coalición física” y la escalera son prometedoras; la novedad singular está difusa |
| Metodología | 4,8 | Buen pareamiento, pero hay evaluadores circulares y no existe validación integrada |
| Estadística | 4,5 | Unidad inferencial, dependencia, censura, H7.3 y SESOI/potencia sin cerrar |
| Matemáticas | 4,8 | Resultados estándar mezclados con aportes propios incompletamente demostrados |
| Teoría de juegos | 4,3 | Varias implementaciones no corresponden a las dinámicas declaradas |
| Robótica y control | 4,6 | Planta simplificada, proyección posintegración y referencias proxy |
| Claims y evidencia | 4,5 | H7/H8 no son defendibles hoy; otros claims necesitan acotación |
| Reproducibilidad técnica | 7,6 | Buena infraestructura; faltan benchmarks observados y cierre en entorno limpio |
| Presentación y cumplimiento VIU | 9,2 | Muy avanzado; quedan legibilidad, fuentes, fecha y similitud externa |

## 4. Fortalezas que deben conservarse

1. Problema relevante: coordinación distribuida y transporte cooperativo de cargas heterogéneas.
2. Concepto comunicable de **coalición física**, más allá de cardinalidad o asignación.
3. Escalera clara: cierre → capacidad → wrench → movimiento → carga → recuperación → red → escala.
4. Transparencia al conservar resultados negativos y reconocer la falta de validación física.
5. Repositorio, configuraciones, semillas y artefactos con trazabilidad poco común en un TFM.
6. Uso intencional de mundos compartidos, pareamiento, tamaños de efecto y corrección Holm.
7. Capacidad diagnóstica: el trabajo identifica el escalón exacto en que aparece un falso positivo.
8. Estructura VIU completa, prosa profesional y cierre explícito de objetivos e hipótesis.

## 5. Bloqueos científicos críticos

### C1. SP8 contiene circularidad y resultados no observados

- `src/viu_mrob_tfm/sp8/methods.py:79–97` devuelve timeouts declarados antes de ejecutar y asigna `runtime_ms=60000`.
- `src/viu_mrob_tfm/sp8/methods.py:159–175` usa umbrales y fórmulas de memoria, no RSS observado.
- `src/viu_mrob_tfm/sp8/metrics.py:101–113,291–303` aplica un factor de mitigación dependiente de la identidad del método. Este factor entra en ruta, éxito y completitud.

Consecuencia: H8.1 y H8.2 mezclan comportamiento impuesto por código con desempeño observado. La correlación entre tamaño y timeout es circular cuando el tamaño dispara determinísticamente el timeout. Los métodos omitidos reciben además asignaciones nulas, contaminando la comparación física posterior.

**Acción:** suspender H8.1–H8.2; hacer el evaluador ciego al nombre del método; ejecutar con timeout externo idéntico; medir wall-clock y RSS; analizar tiempo-a-solución con censura; separar no ejecutado, timeout, fallo y solución.

### C2. H7.3 no es un resultado nulo: no existe el contraste

El artefacto de H7.3 contiene `n_blocks=0`, `p=1` y efecto no estimable. El perfil intermitente no aparece en la campaña canónica. El código devuelve `p=1` cuando no hay bloques suficientes (`src/viu_mrob_tfm/sp7/runner.py:306–334`).

**Interpretación correcta:** “no evaluable/no estimable”, nunca “no detectó diferencias”.

Además, la correlación de SP7 usa 20.176 filas que repiten mundos por método, perfil y semilla. No son 20.176 observaciones independientes.

**Acción:** añadir el perfil faltante; obtener bloques completos; agrupar por mundo/semilla; usar bootstrap agrupado, GEE o modelo mixto; registrar IC y número efectivo de clusters.

### C3. SP7 no introduce la red degradada dentro del lazo de control

`src/viu_mrob_tfm/sp7/methods.py:55–94` traduce el perfil de comunicación a cambios escalares de ganancia/velocidad/formación. `src/viu_mrob_tfm/sp7/metrics.py:81–157` muestrea pérdida y retardo sobre la trayectoria ya generada.

Consecuencia: la campaña no demuestra que memoria, mensajes retardados o reparación de conectividad mantengan el transporte en lazo cerrado.

**Acción:** implementar colas de mensajes, timestamps, estados vecinos obsoletos, expiración de memoria, pérdida y retardo dentro de cada paso de control. Mantener fijo el controlador y variar solo el canal.

### C4. La seguridad está contaminada por corrección geométrica del estado

SP5 y SP6 proyectan la carga y/o robots fuera de obstáculos después de integrar (`src/viu_mrob_tfm/sp5/methods.py:692–764`; `src/viu_mrob_tfm/sp6/methods.py:663–668`). La simulación evita penetraciones corrigiendo el estado.

Consecuencia: cero colisiones no puede atribuirse causalmente al controlador. La proyección equivale a una intervención de seguridad no contabilizada.

**Acción:** eliminarla de la comparación principal o declararla como operador explícito, registrar activación y desplazamiento, penalizarla como fallo y validar una muestra en simulación de contacto sin teleportación. El QP/HOCBF debe incluir límites de actuador, slack y verificación final de todas las barreras.

### C5. La planta ejecutada no corresponde al AMR diferencial prometido

SP4 actualiza posiciones mediante integrador cartesiano simple (`src/viu_mrob_tfm/sp4/methods.py:153–174`). SP5 también mueve centros con velocidades cartesianas (`src/viu_mrob_tfm/sp5/methods.py:172–233`). No hay orientación, ruedas ni restricción no holonómica en esas campañas.

La ley explícita contiene bloques de uniciclo, saturación y reparto, pero la cadena completa no se ejecuta en los SP canónicos. El diagrama del PDF sugiere una integración mayor que la demostrada.

**Acción:** campaña con estado `(x,y,theta,v,omega)`, mando de rueda o fuerza/par, aceleración y saturación dentro del lazo. Registrar la diferencia entre acción HOCBF deseada y acción realmente aplicada.

### C6. La teoría de juegos no coincide con el algoritmo ejecutado

- `SmithQRAllocator` calcula scores, usa `argmax` y cierre voraz.
- Replicator/BNN en SP1 reutilizan `UtilityGreedyAllocator`.
- SP2 hace selección secuencial por `argmax`.
- SP3 transforma scores y selecciona el máximo.

Esto no implementa las dinámicas Smith, replicator o BNN con estado poblacional, flujo en el simplex, integración, criterio de parada y trazas de potencial.

Además, V1–V3 son circulares: V1 contrasta una función con una expresión construida por ella; V2 llama `poa_closed` en ambos lados; V3 fija `stable_numeric=stable_theory`.

**Acción:** implementar fielmente las dinámicas y validarlas de forma independiente o renombrar todos esos métodos como heurísticas “inspiradas en”. Rehacer V1 con QP/VI y KKT, V2 resolviendo numéricamente mejores respuestas y óptimo social, y V3 con autovalores/trayectorias reales.

### C7. La matemática fuerte está incompleta o desconectada

- El ascenso de potencial Smith es correcto bajo `p=grad Phi`, pero esa identidad no se demuestra para los payoffs operativos discretos.
- GNE/vGNE aparece sin juego generalizado, conjuntos dependientes, VI ni multiplicador común completamente definidos.
- La fórmula cerrada vGNE solo vale sin restricciones activas y con centrado ponderado; no cubre contacto unilateral, fricción o saturación.
- La condición `c lambda_2 mu > vartheta^2` carece de sistema elevado y derivación completos.
- La métrica wrench del texto mezcla N y N·m, mientras el código usa normalización `Q`.
- La HOCBF requiere condiciones iniciales y factibilidad conjunta; la proyección secuencial puede reabrir restricciones previas.

El anexo matemático A no está incluido en el PDF canónico. La guía local del repositorio, sin embargo, pide retirarlo por presupuesto de páginas: no debe reincorporarse sin más. La solución es integrar en el cuerpo solo las definiciones/pruebas esenciales y convertir lo demás en material suplementario o retirarlo como claim.

### C8. No existe una arquitectura end-to-end ni evidencia strict-local

SP1–SP8 cambian métodos, plantas y modelos. Las conclusiones favorables proceden de MAPPO, referencias wrench/CBF/MPC, mercado jerárquico u otros mecanismos, no de una única arquitectura.

En SP1, el decodificador MAPPO lee datos globales, enumera subconjuntos y planes, resuelve asignaciones húngaras y selecciona globalmente el mejor candidato (`src/viu_mrob_tfm/sp1/mappo.py:416–475`). El actor aprendido aporta un término de peso 0,05. La cercanía al oráculo puede provenir del decodificador combinatorio central.

**Acción:** actor-only, decoder-only y logits aleatorios; brazo strict-local frente a global upper bound; campaña end-to-end con la misma implementación y ablación acumulativa.

## 6. Problemas metodológicos y estadísticos mayores

### Unidad experimental

La memoria define escenario–semilla–método, pero el método es tratamiento repetido. La unidad independiente es mundo/escenario/variante/semilla; cargas, robots y frames están anidados.

### Endpoint y test

- Resultados binarios: McNemar exacto, diferencia de riesgos pareada, odds ratio/IC o modelos binomiales agrupados; no Wilcoxon genérico por defecto.
- Colisiones: `any_collision_per_run`, duración y clearance mínimo; no contar frames como réplicas independientes.
- Tiempo-a-evento: análisis de supervivencia o RMST con censura explícita.
- Repetición por mundo/método: modelo mixto, GEE o bootstrap por cluster.

### Potencia y relevancia práctica

No hay SESOI ni justificación a priori de tamaños de muestra. El número de semillas parece orientado a acumular filas. Definir umbral mínimo de relevancia, potencia/precisión con dependencia y stopping rule antes de rerun.

### Multiplicidad y reporting

Holm parece bien implementado, pero no se definen las familias. Cada tabla confirmatoria debe contener:

`family_id`, endpoint, unidad, n clusters, eventos, exclusiones, estimación, IC95 %, efecto, SESOI, p crudo, p ajustado y decisión.

No reportar `p=0`; usar límites numéricos, por ejemplo `p<1e-...`.

### H3

El 0,5000 surge de un diseño balanceado entre casos factibles y adversariales. Demuestra existencia de un fallo del criterio escalar dentro del generador, no prevalencia externa. El 0,4830 de Smith marginal indica además que el guard/oráculo wrench, no Smith-QR sin guardia, es el mecanismo que evita el falso positivo.

## 7. Claims: conservar, acotar o suspender

| Claim | Estado actual | Formulación segura inmediata |
|---|---|---|
| Arquitectura acoplada implementada y evaluada | Excede evidencia | “Arquitectura escalonada evaluada modularmente; integración end-to-end pendiente” |
| H7 sin diferencias bajo intermitencia | Inválido | “H7.3 no fue estimable: no hubo bloques completos” |
| H8 demuestra timeout de centralizados | Inválido | “SP8 aplicó límites declarados; no midió tiempo-a-solución en esos casos” |
| Cada método resuelve 2.000 instancias | Inexacto | “Cada método fue programado para 2.000 mundos; ejecuciones omitidas se consideran no evaluadas” |
| FPR=0,5000 como prevalencia | Excede diseño | “El conjunto adversarial balanceado demuestra existencia, no prevalencia externa” |
| MAPPO distribuido | No demostrado | “Actor CTDE evaluado con decodificador global de factibilidad” |
| Control garantiza cero colisiones | Contaminado | “Se observaron cero colisiones bajo una simulación con proyección correctiva” |
| Smith/replicator/BNN validados | Etiqueta infiel | “Heurísticas inspiradas en esas familias”, salvo reimplementación |
| SOTA/baseline MPC-CBF/CBF temporal | Proxy | Nombrar “proxy interno inspirado en…” o implementar el algoritmo reconocible |

## 8. Organización, narrativa y escritura

### Organización

La estructura formal es sólida. El problema no es el orden de capítulos, sino que ocho campañas compiten por ser la contribución principal. La reescritura debe reducir el cuerpo a evidencia que sostenga una sola tesis; rankings y campañas secundarias pueden pasar a suplemento.

### Narrativa recomendada

1. El fallo científico: asignación factible no implica transporte factible.
2. Definición de coalición física y escalera de certificados.
3. Qué afirmación falsable se evalúa en cada escalón.
4. Evidencia diagnóstica, incluidos resultados negativos.
5. Campaña integradora y ablaciones.
6. Discusión: cuándo falla cada aproximación, coste de descentralizar y límites.

### Escritura

La prosa es clara, pero las aperturas repetidas “La campaña…”, “El alcance…”, “permite…” y “respalda…” producen cadencia mecánica. Sustituir enumeración por mecanismo causal: qué cambió, por qué cambió y qué no puede inferirse.

Evitar “demuestra”, “prueba”, “confirma” cuando el resultado solo ilustra, reproduce una fórmula o es específico del generador. “Oráculo” cambia de significado entre SP: definir cada uno. La etiqueta SOTA debe aparecer acompañada por “proxy adaptado” en tabla y figura, no solo en una limitación distante.

Falta una discusión transversal que explique:

- por qué Smith-QR pierde frente a greedy en SP2;
- por qué Smith marginal no corrige SP3;
- cómo cambia SP5 al modelar la carga;
- qué se sacrifica al descentralizar;
- qué resultados contradicen la expectativa inicial;
- cómo se posiciona el trabajo ante los vecinos más próximos.

## 9. Bibliografía y novedad

La bibliografía impresa contiene 65 referencias únicas y el `.bib` 99 entradas. La auditoría de metadatos y un muestreo de fuentes recientes encontraron una base razonable, pero no equivalen todavía a una auditoría cero-contexto de cada cita.

Correcciones confirmadas en entradas no citadas actualmente:

- `benaim2003deterministic`: DOI correcto `10.1111/1468-0262.00429`, no `...00421`.
- `verginis2018communication`: DOI correcto `10.23919/ECC.2018.8550305`, no `...8550339`.

La cita Mordor/VDA 5050 usada para la dicotomía “sobredimensionar o excluir” no respalda de forma directa ese razonamiento técnico. Sustituir por fuente MRTA/transporte cooperativo o presentarlo como motivación de diseño.

La portada indica 30 de junio de 2026, pero varias fechas de consulta son 2 de julio de 2026. Actualizar fecha de entrega o verificar fechas sin fabricar información.

La novedad debe defenderse con una matriz de 6–10 trabajos próximos que compare: coalición, asignación, contacto/wrench, planificación, control distribuido, red local, recuperación, hardware y diferencia exacta del TFM. Deben añadirse o reforzarse referencias fundacionales de GNE/vGNE, Smith, Nash seeking y grasp/wrench.

## 10. Maquetación y presentación

El PDF tiene 82 páginas físicas: 67 de cuerpo y 5 de anexos según el gate local; 14.743 palabras, 24 figuras y 20 tablas. La composición general es coherente y profesional.

Problemas visibles:

- páginas físicas 40 y 55 muy vacías;
- gran espacio superior en p. 49;
- plots de pp. 50, 57, 60, 64 y 67 con etiquetas pequeñas al 100 %;
- algunas tablas cerca del límite de legibilidad;
- sustituciones de forma Arial/OT1 y varios `underfull hbox` en el log;
- redondeo SP5 0,9760/0,9761 inconsistente.

No añadir páginas solo para rellenar. Reorganizar flotantes, simplificar gráficos, dividir paneles o usar figuras a ancho completo. Eliminar warnings tipográficos relevantes y comprobar accesibilidad/etiquetado si el pipeline lo permite.

## 11. Roadmap de cierre

### Fase 0 — Contención de claims (1–2 días)

1. Crear ledger `claim → método → código → datos → test → limitación`.
2. Marcar H7.3 **NO EVALUABLE**.
3. Suspender H8.1–H8.2 y dejar H8.3 como exploratoria.
4. Separar hipótesis competitivas, validaciones de constructo y análisis exploratorios.
5. Retirar temporalmente del resumen y conclusiones todo claim inválido.

**Gate:** ninguna conclusión favorable depende de `n_blocks=0`, timeout declarado, valor fijado por diseño o factor dependiente del nombre del método.

### Fase 1 — Reparación metodológica (1–2 semanas)

1. Evaluador SP8 ciego; wall-clock/RSS reales; timeout externo; censura.
2. SP7 con red dentro del lazo y perfil intermitente real.
3. Redefinir unidad experimental y rerun cluster-aware.
4. Tests apropiados por endpoint, IC95 %, SESOI y familias Holm explícitas.
5. Actor-only/decoder-only/random-logits para MAPPO.
6. Relabelar inmediatamente métodos proxy que no vayan a reimplementarse.

**Gate:** todo contraste confirmatorio tiene bloques válidos, efecto con IC, unidad inferencial, eventos y prueba compatible con el endpoint.

### Fase 2 — Experimento decisivo robótico (2–4 semanas)

Ejecutar una campaña preregistrada con:

- un único pipeline desde reclutamiento hasta recuperación;
- strict-local y global upper bound;
- ablaciones acumulativas `+QR`, `+capacity`, `+wrench`, `+HOCBF`, `+recovery`, `+network memory`;
- AMR diferencial, límites de rueda/par, carga heterogénea y extendida;
- contacto/fricción coherentes entre SP3, SP5 y SP6;
- obstáculo, giro, pérdida de un robot y canal degradado;
- sin corrección silenciosa de posiciones;
- medición de misión válida, residual wrench, contacto, slip, barreras, slack, saturación, colisión, clearance, mensajes, tiempo y RSS;
- muestra replicada en CoppeliaSim dinámico o motor independiente.

**Gate:** el mismo artefacto ejecutable completa la cadena y las ablaciones muestran qué mecanismo causa cada mejora o fallo.

### Fase 3 — Cierre matemático y posicionamiento (5–8 días)

1. Clasificar resultado conocido, lema, derivación y teorema nuevo.
2. Demostrar o retirar estabilidad y convergencia práctica.
3. Definir juego, costes, restricciones, VI/vGNE y potencial.
4. Alinear residual wrench, unidades y normalización texto–código.
5. Rehacer V1–V3 con validación independiente.
6. Integrar solo matemáticas indispensables dentro del presupuesto de páginas.
7. Construir matriz de novedad y discusión transversal.

**Gate:** ningún término fuerte aparece sin definición, algoritmo correspondiente y evidencia independiente.

### Fase 4 — Reescritura y submission lock (4–7 días)

1. Alinear título, resumen, pregunta, contribuciones y conclusión.
2. Añadir tabla maestra de evidencia.
3. Reducir rankings y mover detalle secundario a suplemento.
4. Corregir figuras, flotantes, tipografía, fecha y redondeos.
5. Auditoría completa de citas y revisión externa de similitud.
6. Ejecutar suite completa desde checkout/entorno limpio.
7. Preparar una defensa de 12 diapositivas y las preguntas hostiles.

**Gate:** PDF legible, reproducible y semánticamente idéntico entre resumen, resultados y conclusiones.

## 12. Definition of done — submit-ready

No cerrar el TFM hasta cumplir todos los puntos:

- [ ] Cero ramas por identidad del método en evaluadores.
- [ ] Cero timeouts declarados presentados como mediciones.
- [ ] `n_blocks>0` en todo contraste; si no, “no estimable”.
- [ ] Todo endpoint primario tiene efecto, IC95 %, unidad y familia de multiplicidad.
- [ ] SP7 introduce pérdida y retardo dentro del lazo.
- [ ] SP8 usa tiempo y memoria observados.
- [ ] La seguridad no se atribuye al controlador si depende de proyección.
- [ ] Existe una campaña end-to-end o se elimina “acoplada”.
- [ ] Actor-only/decoder-only identifica la contribución real de MAPPO.
- [ ] Smith, replicator, BNN, MPC, CBF y vGNE son implementaciones fieles o proxies bien nombrados.
- [ ] El ledger enlaza claims, código, datos, hashes y resultados.
- [ ] Suite completa aprobada en entorno limpio.
- [ ] Auditoría bibliográfica por entrada y similitud externa cerradas.
- [ ] Todas las figuras son legibles al 100 %.
- [ ] PDF sin sustituciones tipográficas ni warnings de maquetación relevantes.

## 13. Verificación técnica realizada durante esta revisión

- Gate submit-ready existente: `PASS_WITH_WARNINGS`; el warning pendiente es el informe externo de similitud.
- Gate estricto: falla por ese warning, no por estructura/extensión.
- Tests focalizados ejecutados: `tests/test_submit_ready_gate.py`, `tests/test_experiment_stats.py`, `tests/test_explicit_amr_control_law.py`, `tests/test_wrench_market_games_integration.py`: **21 passed**.
- Suite completa: se intentó dos veces, pero no finalizó dentro de cinco minutos. No se considera validada.

Los tests focalizados verifican contratos de software; no corrigen los problemas de validez científica descritos.

## 14. Decisión de cierre

El TFM no necesita más amplitud ni más filas de Monte Carlo. Necesita equivalencia exacta entre cuatro objetos:

> **claim ↔ formulación matemática ↔ algoritmo ejecutado ↔ evidencia inferencial**

La ruta más fuerte consiste en contener primero los claims inválidos, reparar SP7/SP8 y la estadística, ejecutar una única campaña física end-to-end y reescribir el manuscrito alrededor de la coalición física y su escalera de certificación. Si esos gates se cumplen, el trabajo puede pasar de un repositorio ambicioso y fragmentado a una contribución científica clara, falsable y difícil de atacar.
