# SP1.A2 — separación experimental y rediseño científico de figuras

## Propósito y resultado observable

Reestructurar la salida de `scripts/sp1_a2_milp.py` en dos carpetas
semánticamente independientes:

1. `milp_results/`, dedicada al MILP heterogéneo sin columnas, curvas ni
   afirmaciones de Hungarian;
2. `comparison/`, dedicada a una comparación controlada donde MILP y Hungarian
   resuelven el mismo problema homogéneo reducible a slots.

Ambas carpetas deben contener CSV reproducibles, un reporte interpretativo,
una guía figura por figura, plots PNG de alta resolución y PDF vectoriales, y
un manifiesto con hashes.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: el MILP es un oráculo central y la capacidad escalar
  no certifica factibilidad mecánica.
- `docs/02_RESEARCH_MATRIX.md`: Hungarian solo es un baseline válido en la
  reducción homogénea uno-a-uno por slots.
- `docs/03_EXPERIMENT_PROTOCOL.md`: comparación pareada, semillas idénticas,
  estado/gap y reporte de resultados negativos.
- `docs/04_CLAIMS_EVIDENCE.md`: la evidencia SP1.A2 es piloto y debe conservar
  sus limitaciones.
- `docs/05_NOTATION.md`: la memoria usa `c_i^{pay}` para capacidad; `q_i` está
  reservado para el estado del robot.
- `scripts/sp1_a1_hungarian.py`, `scripts/sp1_a2_milp.py` y
  `tests/test_sp1_a2_milp.py`.
- Dataset quick existente de 3.420 filas en
  `scripts/results/sp1_a2_milp/`, que se conservará como fuente histórica y no
  se sobrescribirá.

## Alcance y no alcance

Incluye separación física de datos, filtrado de columnas, comparación
homogénea pareada, indicadores descriptivos, tendencias log--log, regresiones
OLS descriptivas, intervalos empíricos o de Wilson, estilos accesibles,
resolución mínima de 400 dpi, PDF vectorial y documentación de lectura.

No incluye convertir regresiones descriptivas en evidencia confirmatoria,
comparar control o transporte físico, ni llamar “Nature/IEEE oficial” a un
estilo inspirado en convenciones editoriales.

## Supuestos y preguntas resueltas

- El resultado heterogéneo previo no dice que MILP sea peor o mejor que
  Hungarian: cambia simultáneamente algoritmo y conjunto factible.
- La comparación válida fija `capacity_mode=homogeneous`, conserva mundo,
  semillas y fallos, y excluye el barrido de heterogeneidad.
- El dataset quick heterogéneo completo se reutiliza para evitar repetir una
  campaña costosa. La comparación controlada se ejecuta con perfil smoke y se
  declara expresamente.
- Los indicadores de tendencia son descriptivos. Se reportarán `n`, mediana,
  bandas P05--P95, pendiente y `R²` cuando sean identificables.

## Diseño matemático/técnico

La reducción controlada impone `c_i^{pay}=q_bar` y masas
`m_k=r_k q_bar`. Por tanto, toda solución factible mínima usa exactamente
`r_k` robots por carga y el coste de distancia es equivalente a la expansión
Hungarian en slots. El MILP mantiene sus propias variables binarias y solver;
no se copiará la solución Hungarian.

La identidad visual usa lienzo 3:2, tipografía sans-serif legible en pantalla,
paleta Okabe--Ito, marcadores y tipos de línea redundantes, grid secundario
tenue, una sola señal dominante por figura y márgenes proporcionales. Cada
figura tendrá una anotación de indicador y una explicación externa.

## Plan experimental

### MILP heterogéneo

- Fuente: campaña quick completa, 3.420 filas.
- Estudios: escala, balance, asimetría, capacidad y fallos.
- Métricas: factibilidad, optimalidad, tiempo, memoria, distancia, exceso,
  utilización, equidad, churn y recuperación.

### Comparación controlada

- Perfil: smoke, salvo indicación contraria en el reporte.
- Estudios: escala, balance, asimetría y fallos.
- Capacidad: homogénea para ambos métodos.
- Indicadores: acuerdo de factibilidad, diferencia absoluta de distancia,
  ratio de tiempos, número de robots y regresión de escalabilidad.

## Hitos

- [x] Hito 1 — API de publicación separada y CSV sin contaminación cruzada.
- [x] Hito 2 — campaña homogénea controlada y pruebas de identidad del problema.
- [x] Hito 3 — sistema visual editorial y plots MILP autónomos.
- [x] Hito 4 — plots comparativos controlados y guías explicativas.
- [x] Hito 5 — run, render, inspección visual, hashes y trazabilidad.

## Validación

```text
python -m py_compile scripts/sp1_a2_milp.py
python -m pytest tests/test_sp1_a2_milp.py -q
python scripts/sp1_a2_milp.py --mode publish-existing \
  --profile quick --comparison-profile smoke \
  --source-dir scripts/results/sp1_a2_milp \
  --output-dir scripts/results/sp1_a2_milp_revised
```

Criterios: exactamente dos carpetas de resultados; CSV MILP sin campos
`hungarian_*`; comparación con `same_capacity_model=True` en todas las filas;
distancia homogénea coincidente dentro de tolerancia; PNG ≥400 dpi y PDF para
cada figura; textos legibles; hashes válidos; ninguna modificación de los
datos históricos.

## Riesgos y mitigaciones

- Runtime MILP: comparación smoke separada del perfil quick heterogéneo.
- Sobreinterpretación de regresiones: etiqueta “descriptiva”, `n` y `R²`.
- Exceso de indicadores: un mensaje dominante por figura y guía externa.
- Color inaccesible: color más marcador/estilo de línea.
- Salida raster insuficiente: exportación simultánea PNG 450 dpi y PDF.
- Árbol sucio: no eliminar ni sobrescribir resultados históricos.

## Registro de decisiones

- 2026-07-29 — Se crea `sp1_a2_milp_revised/` para no mezclar ni destruir la
  salida histórica combinada.
- 2026-07-29 — “Estilo IEEE/Nature” se operacionaliza como sobriedad editorial,
  alta densidad informativa y salida vectorial; no se atribuye conformidad
  oficial con ninguna revista.
- 2026-07-29 — La comparación controlada excluye `capacity_study`, porque ese
  barrido existe para estudiar heterogeneidad y no pertenece al dominio válido
  de Hungarian.
- 2026-07-29 — Una regresión visual solo se dibuja como tendencia cuando tiene
  pendiente positiva y `R² >= 0,50`. En la comparación smoke, los ajustes
  temporales no superaron este umbral y se etiquetaron como no identificables.
- 2026-07-29 — El dataset quick histórico no contiene Gini/Jain por fila. Se
  descartó esa figura y se usó utilización de flota, que sí está registrada; no
  se reconstruyeron ni inventaron métricas ausentes.

## Progreso

Publicación completada en `scripts/results/sp1_a2_milp_revised/` con exactamente
dos carpetas. `milp_results/` contiene 3.420 filas, nueve figuras PNG a 450 dpi,
nueve PDF vectoriales, reporte, guía y manifiesto de 33 artefactos.
`comparison/` contiene 126 filas homogéneas, cuatro PNG, cuatro PDF, reporte,
guía y manifiesto de 22 artefactos. Hubo 102 pares conjuntamente factibles,
cero desacuerdos de factibilidad y error máximo de distancia de 0 m; el ratio
mediano de tiempo MILP/Hungarian fue 181,60. Las nueve pruebas pasan. Se
inspeccionaron visualmente escalabilidad, heterogeneidad, fallos, paridad y
tiempo; se corrigieron solapamientos tipográficos, etiquetas porcentuales y
regresiones débiles. Todos los hashes y tamaños pasan, la resolución mínima es
2.781 × 2.212 px y la fuente histórica conserva sus hashes.
