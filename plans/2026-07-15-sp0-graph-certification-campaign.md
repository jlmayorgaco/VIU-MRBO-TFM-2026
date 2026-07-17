# SP0: campaña de certificación grafo--optimalidad

## Propósito y resultado observable

Validar cuándo y a qué coste una red vecinal puede reproducir el coste del matching Hungarian. El resultado observable será una campaña pareada E0--E6 con GCA implementado, GPG formalizado sin confundirlo con GCA, certificados verificados por instancia y una recomendación de radio o topología condicionada a calidad.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`. La formulación y los límites actuales están en la sección SP0 y su anexo de pruebas. La campaña vigente `SP0_THEORY_v1` cubre factibilidad y calidad con precios compartidos, pero no simula consenso vecinal. La nueva evidencia tendrá un identificador diferente y no sobrescribirá la campaña vigente.

## Alcance y no alcance

Incluye matching homogéneo, grafos estáticos no dirigidos, costes euclídeos, GCA, análisis GPG, conectividad, desacuerdo de precios, rondas, escalares transmitidos, regret y exactitud. No incluye movimiento físico, retardo, pérdida de paquetes, coaliciones de cardinalidad mayor que uno ni una prueba de convergencia de PD--Smith.

## Supuestos y preguntas resueltas

Las matrices de coste permanecen fijas al variar el grafo. Los precios y ganadores solo se intercambian entre vecinos. Se separan mensajes lógicos, transmisiones sobre aristas, escalares y bytes. La condición $N(\varepsilon+2e_\pi^t)<1$ solo certifica exactitud para costes enteros o cuantizados con separación unitaria. La campaña no se usará para afirmar que la dependencia espectral general es nueva.

## Diseño matemático/técnico

Métodos: HUN como oráculo central; GRD como baseline rápido; PBR como juego de factibilidad; PBR-2 como mejora bilateral; GCA como auction-consenso conocido; GPG como marco de juego local con copias de precios, desacuerdo y certificado. La salida de GPG no se considerará algoritmo evaluado hasta disponer de una dinámica completa, cierre entero, prueba de invariancia y criterio de terminación.

Por ronda se registrarán $e_\pi^t$, gap $g_t$, cota $B_t=N(\varepsilon+2e_\pi^t)$, factibilidad, pujas, actualizaciones, aristas activas y tráfico acumulado. Invariantes: una asignación factible no duplica tareas, el certificado nunca se viola, las copias locales son finitas y la ejecución es reproducible.

## Plan experimental

- E0, auditoría exacta: tamaños enumerables, instancias aleatorias y adversariales; Hungarian contra enumeración, Nash contra inyecciones y gap contra certificado. No usa p-valores.
- E1, calidad: $N\in\{8,16,32,64,128\}$, $K/N\in\{0.5,0.75,1\}$, distribuciones uniforme, agrupada, cargas concentradas y greedy adversarial; 30 semillas pareadas por celda. Friedman, Kendall $W$, Wilcoxon--Holm, rank-biserial e IC bootstrap.
- E2, conectividad: grafos de disco por radio y familias cadena, anillo, grid, k-NN, Erdős--Rényi conectado y completo. Métricas $\lambda_2$, diámetro, componentes, exactitud, regret y desacuerdo.
- E3, convergencia espectral: trayectorias de desacuerdo, gap, cota y mensajes; ajuste robusto de rondas frente a $\lambda_2$, $N$, densidad y $K/N$.
- E4, agenda y ablaciones: 100 matrices, 20 agendas; sin precios, sin consenso, sin corrección de desacuerdo, una ronda y grafo completo. Medir terminales distintos, varianza de regret y distancia de Hamming.
- E5, escalado: $N\in\{8,16,32,64,128,256\}$ y estrés en 512/1024 con subconjunto viable. Reportar exponentes empíricos, no complejidad formal, además de memoria y tráfico.
- E6, diseño: estimar $R^\dagger$ que minimiza tráfico sujeto a exactitud o regret fijado antes del análisis. No presuponer una curva en U.

En el cuerpo de SP0 solo entrarán un panel central de certificado/calidad/conectividad y un panel de trabajo/tráfico/Pareto. Diagnósticos, topologías, ablaciones y estrés irán al anexo para conservar el máximo de diez páginas.

## Hitos

- [ ] Hito 1 — especificación y pruebas de GCA vecinal, incluida terminación y resolución determinista de empates.
- [ ] Hito 2 — E0 sin violaciones y con casos adversariales versionados.
- [ ] Hito 3 — E1 confirmatorio con análisis pareado y control de multiplicidad.
- [ ] Hito 4 — E2--E3 con barrido de red y certificado temporal.
- [ ] Hito 5 — E4 con agendas y ablaciones.
- [ ] Hito 6 — E5--E6 con exponentes empíricos y recomendación condicionada de red.
- [ ] Hito 7 — figuras, tablas, trazabilidad, compilación y revisión visual.

## Validación

Se exigirán pruebas unitarias de consenso, conflictos, padding y métricas; experimento de humo; semillas pareadas; ausencia de NaN/Inf; verificación automática $g_t\leq B_t+\xi$; reproducción desde configuración; y revisión visual del PDF. Una topología desconectada puede fallar y ese fallo debe conservarse.

## Riesgos y mitigaciones

El principal riesgo es etiquetar como GCA una aproximación que conserva información global. Se auditará el estado leído por cada robot. Otro riesgo es confundir el certificado suficiente con una condición necesaria o con una tasa empírica; las tres se reportarán por separado. GPG permanecerá pendiente si no se logra una dinámica cerrada y demostrable. El coste de la campaña se controlará mediante humo, confirmación y estrés separados.

## Registro de decisiones

- 2026-07-15 — La contribución de SP0 se centra en información necesaria y coste comunicativo, no en inventar el matching o auction.
- 2026-07-15 — GCA se trata como baseline conocido; GPG como marco analítico hasta completar algoritmo y pruebas.
- 2026-07-15 — La campaña existente no se reetiqueta como experimento de red.
- 2026-07-15 — La prioridad mundial de la frontera y del certificado queda sin afirmar hasta una revisión sistemática específica.

## Progreso

La frontera de implementabilidad anónima, el certificado grafo--gap y la ley suficiente de recuperación exacta están formulados y demostrados. La campaña E0--E6 permanece pendiente; no existe aún evidencia experimental de $R^\dagger$, transición de conectividad o tasa espectral de GCA/GPG.
