# SP1.A1 Hungarian con campañas Monte Carlo

## Propósito y resultado observable

Convertir `scripts/sp1_a1_hungarian.py` en un único ejecutable que conserve la
demostración gráfica original y genere campañas Monte Carlo reproducibles de
escala, balance casi completo, asimetría y fallos. El resultado observable
incluye configuración, CSV crudos, resúmenes, exponentes, baselines de calidad
y figuras dentro del directorio indicado por CLI.

## Contexto y archivos canónicos

- `scripts/sp1_a1_hungarian.py`: implementación única del baseline.
- `tests/test_sp1_a1_hungarian.py`: invariantes y contrato de salidas.
- `docs/03_EXPERIMENT_PROTOCOL.md`: comparación, métricas y reproducibilidad.
- `docs/04_CLAIMS_EVIDENCE.md`: Hungarian se limita a la calibración homogénea.
- `docs/05_NOTATION.md`: símbolos de SP1 y métricas de asignación.
- `scripts/results/sp1_a1_hungarin/`: destino solicitado para la validación.

## Alcance y no alcance

Incluye demo, perfiles `smoke/quick/full`, generadores pareados, asignación
parcial solo como diagnóstico de cobertura, balance interior `[-0.95,0.95]`,
cinco escenarios de cuota, cinco geometrías, ocho tratamientos de fallo,
baseline greedy, calidad de asignación, tiempos, memoria, comunicación, CSV,
resúmenes y gráficos. No incluye formación distribuida, consenso vecinal,
roles/contactos, certificación mecánica, wrench ni planta física.

## Supuestos y preguntas resueltas

- Todos los robots son homogéneos y tienen capacidad nominal `q_bar=5 kg`.
- Las cuotas son enteras positivas y suman exactamente el total de slots `M`.
- En escasez, `linear_sum_assignment` se usa para medir cobertura parcial, pero
  `mission_feasible` permanece falso.
- El coordinador central recibe un estado por robot activo y devuelve una
  decisión por robot activo; los fallidos consumen reintentos configurados.
- Las semillas se derivan de forma estable desde una semilla base y la celda.
- `δ=-1` y `δ=+1` se tratan como límites matemáticos, no como instancias
  finitas; el barrido usa paso `0.05` entre `-0.95` y `+0.95`.

## Diseño matemático/técnico

La carga `k` genera `n_k=ceil(m_k/q_bar)` slots. Hungarian resuelve la matriz
rectangular euclídea `C[i,s]`. La escala usa
`delta=(N-M)/(N+M)`; la asimetría usa coeficientes de variación de cuotas y
costes; los fallos vuelven a resolver sobre robots supervivientes y calculan
incremento relativo de coste y churn respecto a la asignación base.

Los tiempos se separan en construcción de slots, matriz, solver y postproceso.
La memoria primaria es `cost_matrix.nbytes=8NM` para `float64`.

## Plan experimental

- `smoke`: dos semillas por celda y tamaños pequeños.
- `quick`: diez semillas, 3,300 runs y 18 figuras.
- `full`: sesenta semillas por celda, 28,140 runs.
- Escala: 13 tamaños y 13 balances moderados hasta `M=640`.
- Balance: 39 valores con paso `0.05` y cuatro tamaños hasta `M=160`.
- Estudios: escala, balance extremo, cuota×geometría y fallos.
- Validación funcional con `smoke`; la campaña `full` se ejecuta para generar
  el paquete estadístico solicitado.

## Hitos

- [x] Auditar la implementación presente y su CLI.
- [x] Añadir pruebas de invariantes y contrato de artefactos.
- [x] Ejecutar el perfil `smoke`.
- [x] Verificar CSV, resúmenes, figuras, configuración y recuento de runs.
- [x] Registrar resultados y limitaciones sin sobreafirmar.

## Validación

```powershell
python -m py_compile scripts/sp1_a1_hungarian.py
python scripts/sp1_a1_hungarian.py --help
pytest -q tests/test_sp1_a1_hungarian.py
python scripts/sp1_a1_hungarian.py `
  --mode all `
  --profile smoke `
  --output-dir scripts/results/sp1_a1_hungarin `
  --no-show
```

Aceptación: salida `0`, pruebas verdes, demo PNG válido, CSV con claves únicas,
cuotas conservadas, cobertura coherente, parciales no factibles, memoria
`8NM`, artefactos esperados y ausencia de NaN/Inf donde la métrica sea
estimable.

## Riesgos y mitigaciones

- Tiempo/memoria de `full`: ejecutarlo de forma monitorizada y conservar el log.
- Tiempos ruidosos: reportarlos como mediciones empíricas, no complejidad
  teórica universal.
- Fallo sin robot libre: conservar la no factibilidad como resultado.
- Árbol de trabajo ya sucio: limitar la revisión y entrega a los archivos de
  esta tarea; no restaurar ni incluir cambios ajenos.

## Registro de decisiones

- 2026-07-28: conservar el script único solicitado y no trasladar la lógica a
  `src/`.
- 2026-07-28: tratar Hungarian como baseline central homogéneo y no como método
  distribuido.
- 2026-07-28: usar `smoke` para validación y reservar `full` para una ejecución
  confirmatoria posterior.
- 2026-07-28: elevar `full` a 60 semillas por celda y densificar los barridos
  numéricos a 13 puntos; mantener los ejes categóricos con sus tratamientos
  reales.
- 2026-07-28: separar el barrido extremo de balance para cubrir el eje
  `[-1,1]` sin combinar `δ→1` con `M=640`.
- 2026-07-28: añadir greedy, cotas, métricas de cola/equidad/eficiencia, cinco
  cuotas, cinco geometrías, fallos al 20/30 % y ocho figuras nuevas.

## Progreso

La campaña ampliada quedó validada con `5 passed`. `quick` produjo 3,300 runs y
`full` 28,140, con 60 réplicas en cada una de las 469 celdas. El paquete contiene
18 figuras y un estudio de 39 balances interiores entre `-0.95` y `+0.95`.
Las 2,000 celdas comunes entre `quick` y `full` reprodujeron exactamente todos
los campos no temporales. La ejecución `full` terminó en 638.859 s con
`stderr` vacío.
