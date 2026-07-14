# 05 — Evidencia

Esta capa une cada afirmación defendible con su artefacto, su estimando y su alcance experimental.

## Registros congelados

- [registro_afirmacion_artefacto.md](registro_afirmacion_artefacto.md), [JSON](registro_afirmacion_artefacto.json) y [CSV](registro_afirmacion_artefacto.csv): relación entre afirmaciones, figuras, tablas y archivos fuente.
- [registro_contraste_estimando.md](registro_contraste_estimando.md), [JSON](registro_contraste_estimando.json) y [CSV](registro_contraste_estimando.csv): población, unidad experimental, contraste, corrección y alcance de inferencia.
- [resultados_canonicos.md](resultados_canonicos.md): inventario de campañas promovidas y exclusión explícita de artefactos exploratorios.

## Cadena teoría–simulación

1. El [núcleo matemático](../../doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex) define capacidad, factibilidad de *wrench*, reparto, estabilidad y límites de interpretación.
2. La [síntesis modular SP0–SP8](../../doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex) separa dinámica de juego, cierre entero, guardia física y ejecución.
3. La [campaña integrada A0–FULL](../../doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex) evalúa la cadena acumulativa sobre una misma planta.
4. El [registro de resultados canónicos](resultados_canonicos.md) determina qué campañas pueden sustentar la memoria.

## Artefactos confirmatorios principales

- [A0–FULL de tamaño fijo](../../../results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/): 400 mundos independientes y 2.400 ejecuciones pareadas sobre una planta Euler–Lagrange.
- [Manifiesto final A0–FULL](../../../results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/FINAL_RUN_MANIFEST.json).
- [Contrastes A0–FULL](../../../results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1_1_FIXEDN/statistics/paired_contrasts_holm.csv).
- [SP4 docking game v3](../../../results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/): 108 instancias pareadas, 18 bloques independientes y 1.188 ejecuciones.
- [Sensibilidad por bloques de SP4](../../../results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/statistics/block_sensitivity.md).

## Alcance de CoppeliaSim

El artefacto [SP4 V4 Coppelia](../../../results/sp4/SP4_V4_COPPELIA_PAIRED_NARROW/) es complementario y no canónico. Reproduce cinemáticamente trayectorias precomputadas; no aporta dinámica independiente, contacto físico validado ni evidencia de hardware. Se conserva para inspección visual y demostración, nunca para ampliar el alcance confirmatorio de SP4 v3 o A0–FULL.

## Regla de lectura

Una cifra solo puede citarse como resultado de la tesis si aparece en `resultados_canonicos.md` y puede rastrearse mediante los dos registros anteriores. Los diagnósticos, campañas sustituidas y visualizaciones de demostración deben permanecer etiquetados como exploratorios o complementarios.
