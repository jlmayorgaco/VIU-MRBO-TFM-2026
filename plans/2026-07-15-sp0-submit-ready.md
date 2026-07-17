# SP0 submit-ready: asignación homogénea, equilibrio y eficiencia

## Propósito y resultado observable

Cerrar SP0 como caso base formal y reproducible del capítulo 6. El resultado observable será una sección compilable con formulación exacta, complejidad, juego potencial, caracterización de Nash, límite de eficiencia, certificado primal--dual, campaña Python pareada, tablas y figuras generadas desde datos.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`. La memoria se edita en `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`; el código canónico se ubicará en `src/viu_mrob_tfm/sp0/`; la configuración, en `experiments/configs/sp0_theory.yaml`; y los artefactos, en `results/sp0/SP0_THEORY_v1/`.

## Alcance y no alcance

Incluye robots homogéneos en capacidad, tareas unitarias, costes espaciales robot--tarea, $N\geq K$, matching uno-a-uno, ejecución asíncrona sin rondas globales, oráculo central, subasta, dinámica potencial y refinamiento por intercambios. No incluye coaliciones de cardinalidad mayor que uno, heterogeneidad de capacidad, movimiento, restricciones físicas ni degradación de red; corresponden a SP1--SP8.

## Supuestos y preguntas resueltas

Los costes son conocidos localmente por cada robot, no negativos y normalizados. Una ocupación por tarea puede propagarse mediante un broker lógico o mensajes vecinales; SP0 no modela pérdida, retardo ni radio. Se distingue entre el juego de penalización, que certifica factibilidad, y el juego de precios, que certifica eficiencia aproximada.

## Diseño matemático/técnico

El oráculo es el problema rectangular de asignación lineal. Se demostrará integralidad de su relajación, complejidad polinómica y cardinalidad del espacio enumerable. Para el juego finito se usará $F_\lambda=C+\lambda(D+E)$ y utilidad de contribución marginal; se demostrará potencial exacto y, para $\lambda>c_{\max}$, que el conjunto de Nash coincide con el conjunto factible. Se probará que la eficiencia en coste del peor Nash no está acotada, pese a precio de estabilidad uno. La subasta se interpretará mediante complementariedad $\varepsilon$ y cota aditiva $N\varepsilon$.

## Plan experimental

Instancias geométricas pareadas con posiciones uniformes y coste euclídeo normalizado. Métodos: Hungarian, auction-$\varepsilon$, greedy, mejor respuesta potencial, potencial con intercambios bilaterales y ablación sin exclusión. Se medirán factibilidad, déficit/exceso, coste, gap al oráculo, bienestar, revisiones/pujas, evaluaciones y tiempo de CPU. Una auditoría exhaustiva enumerará todos los perfiles en tamaños pequeños. Se reportarán medianas, IQR e intervalos bootstrap pareados; el tiempo se calificará como dependiente de implementación.

## Hitos

- [x] Hito 1 — teoremas codificados como invariantes y pruebas unitarias.
- [x] Hito 2 — campaña y auditoría exacta reproducibles desde una configuración versionada.
- [x] Hito 3 — tablas y figuras generadas automáticamente.
- [x] Hito 4 — sección SP0 compilada, trazabilidad actualizada y revisión visual aprobada.
- [x] Hito 5 — fitness cerrada, frontera de NP-dificultad y cota conservadora de revisiones verificadas en código y memoria.
- [x] Hito 6 — diagrama conceptual de SP0 recuperado, coste distancia--prioridad formalizado y PDF revisado visualmente.
- [x] Hito 7 — literatura de dinámicas poblacionales, límites de replicator y ruta primal--dual/entrópica integrados; pruebas extensas trasladadas al anexo SP0.
- [x] Hito 8 — grafos de asignación/comunicación separados, certificado grafo--gap e imposibilidad por desconexión integrados; cuerpo SP0 compactado a un máximo de diez páginas.
- [x] Hito 9 — vista cenital, matriz temporal $4\times4$ y contraste pareado de $H_{0,\mathrm{SP0}}$ generados e integrados al cierre de SP0.
- [x] Hito 10 — SP0 reorganizado como caso de calibración uno-a-uno en seis páginas; teoría y visualizaciones auxiliares trasladadas al anexo; comparación principal reducida a cinco métodos ejecutados.
- [x] Hito 10 — contribución reencuadrada como frontera factibilidad--optimalidad; imposibilidad anónima y presupuesto suficiente de recuperación exacta añadidos sin atribuir novedad a métodos clásicos.

## Validación

Comandos previstos: `python -m pytest tests/test_sp0_theory.py`, `python -m viu_mrob_tfm.cli.run_sp0_theory --config experiments/configs/sp0_theory.yaml`, `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`. Se verificará además que los CSV no contengan NaN indebidos, que todo resultado factible satisfaga exclusión, que la subasta respete su certificado y que las figuras existan en PNG y PDF.

## Riesgos y mitigaciones

El principal riesgo científico es confundir Nash con óptimo; se explicitará el contraejemplo. El riesgo computacional de la enumeración se limita a $N\leq5$. La comparación de runtimes entre SciPy y Python no se usará como prueba de escalabilidad; se acompañará de conteos de operaciones lógicas. Ningún resultado heredado de campañas anteriores se reutilizará como evidencia de esta formulación.

## Registro de decisiones

- 2026-07-15 — SP0 se mantiene polinómico; la NP-dificultad se reserva para extensiones con coaliciones/restricciones acopladas.
- 2026-07-15 — Se separan equilibrio de factibilidad y equilibrio primal--dual para evitar una garantía falsa de optimalidad.
- 2026-07-15 — El refinamiento bilateral se reportará como óptimo local de 2-intercambio, no como óptimo global.
- 2026-07-15 — La cardinalidad fija con costes aditivos se clasifica como $b$-matching polinómico; la NP-dificultad se atribuye a la selección todo-o-nada bajo escasez mediante una reducción explícita desde mochila 0--1.
- 2026-07-15 — En SP0, la prioridad $w_k$ pondera el término dependiente del robot $\bar\delta_{ik}$; una constante aditiva por carga no modificaría el matching cuando todas las cargas son obligatorias.
- 2026-07-15 — Dos adjuntos sobre dinámicas poblacionales son duplicados exactos y se integran una sola vez. El adjunto WISE corresponde a otro manuscrito: solo se trasladan criterios generales de validación, no su formulación espectral ni sus claims.
- 2026-07-15 — PD-Smith y la relajación entrópica se presentan como ruta candidata hacia eficiencia social; no se declaran implementadas ni convergentes en este TFM hasta disponer de código, prueba y campaña específicos.
- 2026-07-15 — SP0 incorpora un grafo de comunicación estático como restricción de información. La campaña existente conserva ocupación y precios compartidos; auction multihop y Graph-Coupled PD--Smith permanecen pendientes, mientras el certificado $N(\varepsilon+2e_\pi^t)$ y la imposibilidad por desconexión se sostienen teóricamente.
- 2026-07-15 — La evolución de desempeño se indexa por evento algorítmico, no por tiempo físico. La instancia cenital $4\times4$ se selecciona por cercanía al regret mediano de mejor respuesta para evitar elegir un caso extremo.
- 2026-07-15 — $H_{0,\mathrm{SP0}}$ contrasta igualdad de factibilidad entre la penalización completa y la ablación $\lambda=0$ mediante McNemar exacto bilateral sobre instancias pareadas.

## Progreso

Ampliación cerrada. Se añadió la fitness cerrada por acción, la equivalencia entre máximos globales del potencial y óptimos de asignación, la cota conservadora de $(K+1)^N-1$ cambios de perfil y la frontera entre $b$-matching polinómico y selección NP-difícil. El diagrama muestra ahora tanto el grafo bipartito de asignación como el grafo robot--robot; el cuerpo incluye imposibilidad por desconexión, certificado $N(\varepsilon+2e_\pi^t)$, contracción espectral, radio crítico y coste de mensajes. La revisión sobre dinámicas poblacionales quedó integrada una sola vez: fallo estructural de replicator, ruta Graph-Coupled PD--Smith, relajación entrópica y cota $\tau N\log N$. La campaña canónica conserva 200 instancias y 1200 ejecuciones, añade trazas por evento, una vista cenital representativa y el contraste exacto de $H_{0,\mathrm{SP0}}$. Ocho pruebas unitarias pasan. PD-Smith y auction multihop permanecen pendientes de código y campaña. Las demostraciones completas están en `thesis/sections/appendices/02-sp0-proofs.tex`. Limitaciones conservadas: 2-intercambio no es óptimo global, los tiempos Python/SciPy no prueban complejidad asintótica, la campaña vigente no simula la red y la relajación entrópica no resuelve por sí sola el cierre entero. La extensión y la inspección visual finales se verifican tras recompilar la memoria.

La compilación final contiene 90 páginas. SP0 ocupa las páginas 40--45 (seis páginas) y SP1 comienza en una página nueva, la 46. El cuerpo contiene dos figuras, dos tablas y una proposición; la vista cenital y la matriz temporal se conservan en las páginas 89--90 del anexo. Nueve pruebas unitarias pasan. Las páginas 40--46 y 81--90 fueron renderizadas e inspeccionadas sin cortes, solapamientos ni texto ilegible; permanece únicamente un overfull preexistente de 1.70 pt fuera de SP0.

El cierre editorial redefine SP0 como referencia diagnóstica, no como mini-contribución teórica. El cuerpo pregunta qué robot atiende cada carga bajo homogeneidad y correspondencia uno-a-uno; SP1 hereda la pregunta de cuántos robots y SP2 la combinación de capacidades. Los resultados de red, regularización y dinámicas poblacionales permanecen como material analítico auxiliar o trabajo de SP8, sin contaminar el relato principal.

### Cierre definitivo del microcapítulo — 2026-07-16

- [x] Hito 11 — SP0 reorganizado en seis apartados: alcance, oráculo, juego potencial, métodos y protocolo, resultados, y transición.
- [x] Se retiró la prioridad de las cargas del caso homogéneo; el coste de SP0 es únicamente distancia euclídea normalizada.
- [x] El bienestar y la brecha por carga quedaron definidos mediante fórmulas exactas, y los conteos se denominan operaciones registradas porque no son una unidad de complejidad común entre algoritmos.
- [x] La comparación principal conserva cinco métodos; la ablación de consistencia se presenta separadamente.
- [x] La figura principal quedó reducida a dos paneles legibles: auditoría Nash frente a factorial y distribución de brechas respecto del oráculo.
- [x] SP0 ocupa las páginas 40--45 y SP1 comienza en la página 46 después de un salto de página explícito.

La lectura inversa del apartado deja una sola función por bloque: delimitar el caso base, fijar el óptimo, caracterizar el juego, declarar la comparación, contrastar la hipótesis y transferir las restricciones a SP1--SP2. Las afirmaciones fuertes quedan vinculadas a evidencia concreta: complejidad e integralidad en el anexo, identidad de potencial y factibilidad en la proposición, auditoría exhaustiva para tamaños pequeños, campaña pareada de 200 instancias para eficiencia y contraste exacto de McNemar para la ablación. No se extrapolan optimalidad global, estabilidad física ni escalabilidad de red desde SP0.

- [x] Hito 12 — auditoría visual de los cuatro diagramas de SP0. El esquema TikZ distingue asociación lógica de trayectoria o mensaje; la figura agregada usa un eje discreto, explicita la dirección de la brecha y conserva los atípicos; la vista cenital evita solapamientos de etiquetas; y la matriz temporal comparte escalas por fila y marca la brecha indefinida antes de factibilidad.
- [x] Hito 13 — Figura 2 rediseñada como grafo bipartito alineado. El matching se codifica mediante aristas azules sólidas sin flechas, las alternativas mediante aristas grises punteadas y el estado inactivo mediante un nodo libre; el pie distingue expresamente decisión, trayectoria y comunicación.
