# Metodología común SP0--SP8 en nueve páginas

## Propósito y resultado observable

Sustituir el andamiaje provisional del capítulo 4 por una metodología común, no repetida en cada SP, con los apartados 4.1--4.9 y una extensión renderizada de nueve páginas. El capítulo debe enlazar objetivos, hipótesis, subproblemas, métricas y evidencia; definir el modelo reutilizable; fijar métodos, baselines, protocolo, estadística y reproducibilidad; y declarar límites de inferencia antes de presentar resultados.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`, la estructura de `thesis/main.tex`, los objetivos e hipótesis vigentes y la bibliografía verificada de `thesis/references.bib`. Se modifica principalmente `thesis/sections/mainmatter/04-methodology.tex`; cualquier símbolo nuevo se registra en `docs/05_NOTATION.md`.

## Alcance y no alcance

Incluye diseño hipotético-deductivo, modelo unificado, taxonomía de cuatro familias metodológicas, escalera SP0--SP8, fases experimentales, métricas, complejidad, análisis estadístico, arquitectura reproducible y amenazas a la validez. No presenta resultados, no fija hiperparámetros extensos, no promueve artefactos históricos a evidencia canónica y no repite formulaciones particulares que pertenecen al capítulo 6 o al anexo.

## Supuestos y preguntas resueltas

- La solicitud actual autoriza ampliar de 6--7 a nueve páginas el presupuesto editorial del capítulo, sin alterar el rango total VIU.
- Cargo soportado es la rama física primaria; empuje/caging se conserva como extensión secundaria y no comparte automáticamente garantías.
- El modelo cinemático común es el uniciclo muestreado con saturación. La dinámica planar de carga solo se activa en los SP físicos.
- La preferencia continua y la asignación binaria se representan con símbolos distintos; un cierre QR no se denomina distribuido si consulta preferencias globales.
- La unidad experimental es el mundo o bloque de escenario--semilla. Robots, cargas y muestras temporales son observaciones anidadas.
- Friedman/Wilcoxon/Holm se aplican a endpoints compatibles; los binarios usan procedimientos pareados específicos para evitar una prueba inadecuada.

## Diseño matemático/técnico

El capítulo define conjuntos de robots, cargas y obstáculos; estado, entrada, capacidad, requisitos, grafo de comunicación, modos locales de misión, restricciones de exclusividad, capacidad, seguridad, energía y factibilidad física. La metodología separa preferencia, cierre entero, estimación, movimiento, interacción mecánica, seguridad y comunicación. La taxonomía distingue centralización y dependencia de datos, y reserva los métodos aprendidos para baselines diagnósticos.

## Plan experimental

La campaña común atraviesa pruebas unitarias, screening, tuning, confirmatorio, stress testing y generalización con registros de semillas disjuntos. Cada tratamiento recibe el mismo mundo, límites y timeout; los oráculos globales se etiquetan como techo. Se preservan fallos válidos y se preespecifican endpoints, familias de hipótesis, presupuesto computacional y reglas de invalidez.

## Hitos

- [x] Hito 1 -- capítulo 4 redactado con 4.1--4.9, tablas y ecuaciones coherentes.
- [x] Hito 2 -- notación y referencias cruzadas actualizadas sin duplicar metodología en SP.
- [x] Hito 3 -- pruebas del repositorio y compilación LaTeX superadas.
- [x] Hito 4 -- capítulo medido en nueve páginas y revisión visual aprobada.

## Validación

Ejecutar `python -m pytest`, `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`, comprobar citas/referencias y cajas desbordadas en `thesis/build/main.log`, medir el intervalo del capítulo mediante PDF/TOC, renderizar sus páginas con Poppler y revisar tablas, ecuaciones, encabezados, pies y transiciones.

## Riesgos y mitigaciones

El mayor riesgo editorial es comprimir nueve SP en tablas ilegibles; se mitiga con síntesis y prosa común. El principal riesgo científico es atribuir localidad o garantías a cierres y plantas que no las satisfacen; se exige declarar información disponible y alcance. El árbol de trabajo contiene numerosas eliminaciones preexistentes, por lo que no se tocarán ni restaurarán cambios ajenos.

## Registro de decisiones

- 2026-07-15: se acepta el nuevo presupuesto de nueve páginas como instrucción editorial posterior a `docs/01_VIU_REQUIREMENTS.md`.
- 2026-07-15: se adopta análisis por tipo de endpoint; Friedman no se fuerza sobre variables binarias o censuradas.
- 2026-07-15: la complejidad se reportará tanto de forma analítica como observada, sin equiparar tiempo de Python con escalabilidad teórica.

## Progreso

Trabajo completado. El capítulo contiene 4.1--4.9, cinco tablas/ecuaciones numeradas y una matriz SP0--SP8 compacta. Se añadieron las referencias estadísticas verificadas y se sincronizaron el presupuesto VIU, el protocolo, la notación y la nomenclatura. `python -m pytest` supera 5/5 pruebas. La compilación LuaLaTeX/Biber genera un PDF de 79 páginas sin citas o referencias indefinidas. Metodología ocupa exactamente las páginas 19--27 y Marco teórico comienza en la 28. Las nueve páginas se renderizaron con Poppler y se revisaron en una hoja de contacto; no presentan cortes, solapamientos ni tablas fuera de margen. Persisten dos desbordes pequeños preexistentes fuera del capítulo, uno en Marco teórico y otro en SP0, que no se modificaron por quedar fuera del alcance.
