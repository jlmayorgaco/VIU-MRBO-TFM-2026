# VIU-MROB-TFM-2026

Repositorio organizado de la version V6 del TFM de Jorge Luis Mayorga Taborda para el
Master Universitario en Robotica y Automatizacion de Procesos (VIU).

El eje tecnico actual es **coordinacion distribuida de coaliciones multi-AMR con cargas
heterogeneas**, usando una familia de dinamicas y controladores: Smith-QR, replicator,
logit/BNN, primal-dual, tensor/quorum flow, wrench-market y referencias centralizadas.
La memoria final se concentra en una idea: los robots siguen una arquitectura distribuida
basada en deficit fisico-economico, cierre entero de quorum, formacion rigida de carga,
capacidad efectiva en espacio `wrench`, comunicacion limitada y escalabilidad warehouse.
La capa de control incluye ahora una ley explicita AMR cerrada para punto de mano,
wrench requerido, reparto vGNE, HOCBF e inversion uniciclo; ver
`docs/EXPLICIT_AMR_CONTROL_LAW.md`.

## Estado V6

- Rama de organizacion: `v6-organization`.
- Reporte final canonico: `docs/doc-05-final-report/main.tex`.
- Codigo principal: `src/viu_mrob_tfm`.
- Registro actual de resultados SP1-SP8: `results/README.md` y `docs/CANONICAL_RESULTS.md`.
- Suite compacta de validacion: `results/validation_suite_v1` (`39/39` gates en el snapshot actual).
- Artefactos pesados y borradores previos: `C:\tmp\VIU-MRBO-TFM-2026-v6-organization-20260620`.
- Manifiesto de cuarentena: `cleanup_manifest.csv` y `cleanup_manifest.json`.

## Estructura

```text
.
|-- configs/              # parametros canonicos conservados
|-- coppeliasim/          # escenas de smoke/plausibilidad
|-- docs/doc-04-advanced-report/ # informe avanzado VIU
|-- docs/doc-05-final-report/    # memoria final LaTeX canonica
|-- docs/doc-06-explanatory-report/ # version explicativa extendida
|-- experiments/          # configuraciones reproducibles
|-- results/              # snapshots compactos de evidencia
|-- scripts/              # CLI de ejecucion y validacion
|-- src/viu_mrob_tfm/     # paquete Python
`-- tests/                # pruebas de dominio, simulacion y OOP V6
```

## Instalacion

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Comandos principales

```powershell
python -m pytest -q
$env:PYTHONPATH='src'; python -m viu_mrob_tfm.validation.suite
python scripts/run_experiment.py experiments/exp-001-baseline-nominal/config.yaml
make report-pdf
```

Atajos equivalentes:

```powershell
make test
make validate-suite
make smoke-exp
make run-canonical
make method-matrix
make theory-validation
make stats-annex
make figures-paper
make thesis
make submit-check
```

## Cierre submit-ready

La rama de cierre usa `ROADMAP.md` como plan operativo y `docs/THESIS_NARRATIVE_LOCK.md`
como candado narrativo. El entregable academico principal es
`docs/doc-05-final-report/main.tex` y su PDF. `TFM.md` se conserva como fuente/borrador
auxiliar.

SP1-SP8 se consideran evidencia canonica congelada segun `docs/CANONICAL_RESULTS.md`.
Los scripts nuevos generan artefactos derivados en `docs/generated/` y
`results/theory_validation/`; no reejecutan campanas high-power. SP9 queda preparado como
protocolo CoppeliaSim/Pioneer y, si el runtime externo no esta disponible, genera un
reporte bloqueado en `results/sp9/SP9_BLOCKED_EXECUTION/` sin inventar datos.

Tras `pip install -e .`, los entry points equivalentes son:

```powershell
viu-run-experiment experiments/exp-001-baseline-nominal/config.yaml
viu-run-sp8 configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml
viu-validate-suite
```

## Arquitectura OOP nueva

La version V6 agrega contratos explicitos sin romper los imports historicos:

- `domain.robot`: `RobotSpec`, `RobotRuntimeState`, bateria y capacidad.
- `domain.load`: `LoadSpec`, `WrenchDemand`, masa y geometria rectangular de carga.
- `domain.world`: `WorldState`, `WarehouseMap`, `Obstacle`.
- `scenarios`: escenarios reproducibles.
- `allocation`: `BaseAllocator`, `SmithQRAllocator`.
- `control`: `SingleFieldController`, `RigidFormation`, `VectorialWrenchGame` y ley explicita AMR en `explicit_law.py`.
- `simulation`: `SimulationEngine`, `PolicyStack`, `SimulationResult`.
- `simulations`: benchmark historico de almacen usado por validacion y comparativas.
- `validation`: `HypothesisSuite`.

La configuracion de experimentos queda separada de los metodos: `experiments/*/config.yaml`
para escenarios reproducibles, `configs/` para parametros transversales, y
`scripts/campaigns/` o `scripts/coppelia/` para campanas que generan multiples artefactos.

## Restaurar artefactos movidos

Nada fue borrado directamente. Para restaurar un archivo, buscarlo en
`cleanup_manifest.csv` y copiar `destination_path` de vuelta a `original_path`.
