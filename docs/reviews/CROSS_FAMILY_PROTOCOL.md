# Protocolo de comparación entre familias SP1.N4

## Pregunta y unidad independiente

El benchmark estático pregunta qué propiedades sobreviven cuando tres objetos
matemáticos distintos producen la misma salida física. La unidad independiente
es el par mundo–semilla. Todos los métodos incluidos en un contraste reciben
las mismas posiciones, capacidades, demandas, distancias y grafo.

## Campaña estática E7

E7 reutiliza los 1.200 mundos congelados de E4 (`N=16`, `K=5`) y su oráculo
MILP/HiGHS. Compara:

- F-I: Geo-QPG BR, 2BR, C3 y DMIS+TX;
- F-II: Replicator, Smith, BNN y Logit, todos seguidos por `R`;
- F-III: referencia vGNE central y primal–dual distribuido, ambos seguidos por
  `R`;
- baselines: CBBA-RB, GRAPE y Pair-GRAPE.

F-II usa un único potencial, fitness, inicialización, DAC, presupuesto de
iteraciones y cierre. F-II y F-III comparten exactamente `R`. Una fila solo se
marca continua como convergente cuando cruza sus umbrales declarados; fallos y
timeouts permanecen en el denominador.

## Endpoints y preguntas

Las métricas continuas —potencial, déficit relajado, residual de punto fijo,
residuos KKT y consenso— describen el estado interno de cada familia. La
comparación física usa exclusivamente la asignación posterior al cierre:
factibilidad, distancia, gap frente al MILP, exceso de capacidad y operaciones
de recuperación.

- **RQ-D:** coincidencia entre el ganador continuo de F-II y el ganador después
  de `R`.
- **RQ-E:** diferencia pareada entre PD-vGNE+R y Smith+R en presión 0,85.
- **RQ-F:** frontera observada entre calidad atómica, bytes por agente y CPU.

La factibilidad usa diferencia de riesgos pareada y McNemar; las continuas usan
mediana pareada, bootstrap de mundos completos y Wilcoxon. La corrección de Holm
se aplica dentro de la familia de hipótesis preespecificada.

## Campaña dinámica E8

E8 es independiente de E7. Ejecuta cinco geometrías por seis semillas con la
misma secuencia de llegadas, finalizaciones y fallos para las tres políticas.
Se registran coste descontado acumulado, tiempo con demanda incumplida,
conmutaciones, factibilidad atómica, mensajes y tiempo de recuperación.

El contraste RQ-G enfrenta el oráculo dinámico central con cada política
miopemente realizable. El oráculo conoce la secuencia futura; por tanto, su
ventaja es un techo de información, no una comparación justa de arquitectura.

## Reproducibilidad y límites

La configuración congelada es
`experiments/configs/sp1_n4_cross_family_v3.yaml`. El script
`scripts/sp1_n4_cross_family.py` genera RAW, procesados, figuras, macros y un
manifiesto con hashes. Los mundos son sintéticos, el grafo es estático durante
E7, los bytes son modelados y la CPU corresponde a una implementación Python en
un equipo. Ninguna conclusión cubre docking, contacto, seguridad o transporte.
