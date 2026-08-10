# Reporte de ejecución — SP1.A1 Hungarian ampliado

## Estado

- Resultado final: **correcto**.
- Perfil: `full`.
- Modo: `all`.
- Inicio UTC: `2026-07-28T15:35:25.1843840Z`.
- Fin UTC: `2026-07-28T15:46:04.0429409Z`.
- Duración: `638.859 s` (`10 min 38.859 s`).
- Código de salida: `0`.
- `stderr`: vacío.
- Ejecuciones Monte Carlo: **28,140**.
- Figuras: **18**.

Comando reproducible desde la raíz del repositorio:

```powershell
$env:MPLBACKEND = "Agg"
$env:PYTHONUTF8 = "1"
python -u scripts/sp1_a1_hungarian.py `
  --mode all `
  --profile full `
  --output-dir scripts/results/sp1_a1_hungarin `
  --no-show
```

Las figuras pueden regenerarse sin repetir los cálculos:

```powershell
python scripts/sp1_a1_hungarian.py `
  --mode plots `
  --output-dir scripts/results/sp1_a1_hungarin `
  --no-show
```

## Fuente y entorno

- Script actual: `scripts/sp1_a1_hungarian.py`.
- SHA-256 actual:
  `7271BD1304FD214C76BEB7EB568F259BE73829FCF8E95DBAC1FD3E3A571F1B6E`.
- Después del run solo se refinaron la separación visual por `δ` en dos
  gráficas de fallos y la descripción del CLI; los CSV numéricos no se
  modificaron.
- Commit de referencia: `39d7070c95e96a87a411d36df0036d4a43181b8c`.
- Rama: `codex/sp1-geo-qpg-signal-engine-closure-v1`.
- Script y artefactos sin seguimiento en Git.
- Python `3.13.9`, NumPy `2.3.5`, SciPy `1.16.3`,
  Matplotlib `3.10.6`, backend `Agg`.

## Dominio de balance

Se usa:

```text
δ = (N-M)/(N+M)
```

Los extremos exactos no son instancias finitas válidas:

- `δ=-1` implica `N=0`.
- `δ=+1` requiere `N→∞`.

Por ello, las gráficas muestran el eje completo `[-1,1]`, mientras el barrido
computable usa **39 valores interiores** desde `-0.95` hasta `+0.95`, con paso
`0.05`. Se evalúan `M={20,40,80,160}`. La instancia extrema ejecutada fue
`M=160`, `N=6,240`, `δ=0.95`.

Este estudio se separó del barrido de escalabilidad hasta `M=640` para evitar
que el crecimiento asintótico de `N` cerca de `δ=1` domine o vuelva
impracticable toda la campaña.

## Escenarios y ejecuciones

| Estudio | Celdas | Réplicas/celda | Runs |
|---|---:|---:|---:|
| Escalabilidad | 169 | 60 | 10,140 |
| Balance casi completo | 156 | 60 | 9,360 |
| Cuota × geometría | 75 | 60 | 4,500 |
| Fallos | 69 | 60 | 4,140 |
| **Total** | **469** | **60** | **28,140** |

Escenarios de cuotas:

```text
symmetric, low, moderate, high, extreme
```

Geometrías:

```text
uniform, clustered, separated, ring, corridor
```

Tratamientos de fallo:

```text
no_failure
idle_robot_failure
random_assigned_failure
critical_assigned_failure
random_5_percent
random_10_percent
random_20_percent
random_30_percent
```

## Nuevas métricas

Además de factibilidad, cobertura, coste, tiempo, memoria y comunicación, cada
run registra:

- mediana, P95, máximo, desviación y CV de las distancias asignadas;
- Gini y uniformidad de Jain de los costes;
- dispersión del coste medio entre cargas;
- utilización de robots y fracción de cargas atendidas;
- coste de un greedy secuencial con la misma cardinalidad;
- razón `coste_greedy/coste_Hungarian`;
- ahorro relativo de Hungarian frente a greedy;
- cota inferior relajada y distancia relativa a esa cota;
- tiempo del solver y de construcción por elemento de matriz;
- mensajes y bytes por slot asignado;
- tiempo de evaluación de métricas.

## Resultados descriptivos

- Cobertura observada: `0.025–1.0`.
- Hungarian nunca fue peor que el greedy en los 28,140 runs.
- Razón mediana `greedy/Hungarian`: `1.0855`.
- Ahorro mediano frente a greedy: `7.88 %`.
- Máxima razón observada `greedy/Hungarian`: `1.6791`.
- Exponentes temporales empíricos: `1.332–1.989`.
- `R²` de esos ajustes: `0.971–0.996`.

Mediana del P95 normalizado por geometría:

| Geometría | P95 normalizado |
|---|---:|
| corridor | 0.085 |
| uniform | 0.119 |
| clustered | 0.207 |
| ring | 0.258 |
| separated | 0.559 |

En los fallos aleatorios:

- con `δ=0`, cualquier fallo probado vuelve la instancia no factible;
- con `δ=0.20` y `δ=0.33`, los casos evaluados conservaron factibilidad hasta
  `30 %` de fallos;
- al `30 %`, el incremento mediano de coste fue `0.526` para `δ=0.20` y
  `0.345` para `δ=0.33`.

Son estadísticas descriptivas de este diseño experimental, no garantías
universales ni certificación del sistema físico.

## Reproducibilidad y validaciones

- `python -m py_compile`: correcto.
- `pytest -q tests/test_sp1_a1_hungarian.py`: **5 passed**.
- Claves `(study, seed)` únicas: `28,140/28,140`.
- Réplicas por celda: `60`.
- Valores de balance extendido: `39`.
- Parciales marcados erróneamente como factibles: `0`.
- Violaciones de `matrix_bytes = 8NM`: `0`.
- Violaciones del modelo de mensajes: `0`.
- Violaciones `coste_greedy ≥ coste_Hungarian`: `0`.
- Violaciones de la cota inferior: `0`.
- Gini/Jain fuera de rango: `0`.
- Figuras generadas y no vacías: `18/18`.
- Máximo `N`: `6,240`.
- Máxima matriz: `998,400` elementos.

El perfil `quick` se ejecutó por separado con 3,300 runs. Las 2,000 celdas
comunes entre `quick` y `full`, excluyendo únicamente métricas temporales,
produjeron el mismo SHA-256:

```text
3B140DF45727B1839F5D91352587A809E804E679FD8468FA01CC0305394F8BDE
```

## Artefactos principales

| Archivo | Tamaño | SHA-256 |
|---|---:|---|
| `config.json` | 1,685 B | `36474989099177066E6F686BFB582679B220648F2A66CE2F91578BD1A4906AAE` |
| `mc_all_runs.csv` | 19,500,722 B | `57C7753200F4CD0B5655EC5F56FB40C3B6C55EB04E89DE63929CE887A8AA8B13` |
| `mc_balance.csv` | 6,261,047 B | `2CEBAAEDC4DA5F8D0C7FF3FBCF38F2047F2FDA0B26D4BFBCB772C16632AA12DA` |
| `summary_balance.csv` | 73,716 B | `F983B637F41742FCE1B712FBE5E1270B0843C86387CEDEE7B2503AE2257F5913` |
| `scaling_exponents.csv` | 1,110 B | `C65308B12380FBA8B78FCC95DF0CB1AC9D893F88BA574D84BB7169DCD9762320` |
| `extended_full_run.log` | 22,929 B | `9CF7DA785E8275148E4D5C5F2A78FA85030FEB393CE349E931A57F10AC360BB7` |
| `balance_coverage_dense.png` | 107,208 B | `A3E65267F26BF2269F85AD95BFC534EF4EDA1AFEE3E92185F2CB87B893B3F50A` |

`extended_full_run.stderr.log` está vacío. El directorio conserva también los
logs de campañas anteriores para trazabilidad.

## Alcance y limitaciones

Hungarian sigue siendo un baseline central con información global, robots
homogéneos y reducción uno-a-uno mediante slots. El greedy es solo un baseline
heurístico secuencial, no otro óptimo. La campaña no demuestra formación
distribuida de coaliciones, comunicación vecinal, factibilidad mecánica de
roles/contactos, wrench, dinámica física ni robustez del sistema real.
