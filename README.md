# VIU-MROB-TFM-2026

Repositorio organizado de la version V6 del TFM de Jorge Luis Mayorga Taborda para el
Master Universitario en Robotica y Automatizacion de Procesos (VIU).

El eje tecnico actual es **Smith-QR para coordinacion distribuida de coaliciones
multi-AMR con cargas heterogeneas**. La memoria final se concentra en una idea: los robots
siguen una arquitectura distribuida basada en deficit fisico-economico, dinamicas de
Smith, cierre entero de quorum, formacion rigida de carga y capacidad efectiva en espacio
`wrench`.

## Estado V6

- Rama de organizacion: `v6-organization`.
- Reporte final canonico: `docs/doc-05-final-report/main.tex`.
- Codigo principal: `src/viu_mrob_tfm`.
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
```

Tras `pip install -e .`, los entry points equivalentes son:

```powershell
viu-run-experiment experiments/exp-001-baseline-nominal/config.yaml
viu-validate-suite
```

## Arquitectura OOP nueva

La version V6 agrega contratos explicitos sin romper los imports historicos:

- `domain.robot`: `RobotSpec`, `RobotRuntimeState`, bateria y capacidad.
- `domain.load`: `LoadSpec`, `WrenchDemand`, masa y geometria rectangular de carga.
- `domain.world`: `WorldState`, `WarehouseMap`, `Obstacle`.
- `scenarios`: escenarios reproducibles.
- `allocation`: `BaseAllocator`, `SmithQRAllocator`.
- `control`: `SingleFieldController`, `RigidFormation`, `VectorialWrenchGame`.
- `simulation`: `SimulationEngine`, `PolicyStack`, `SimulationResult`.
- `simulations`: benchmark historico de almacen usado por validacion y comparativas.
- `validation`: `HypothesisSuite`.

La configuracion de experimentos queda separada de los metodos: `experiments/*/config.yaml`
para escenarios reproducibles, `configs/` para parametros transversales, y
`scripts/campaigns/` o `scripts/coppelia/` para campanas que generan multiples artefactos.

## Restaurar artefactos movidos

Nada fue borrado directamente. Para restaurar un archivo, buscarlo en
`cleanup_manifest.csv` y copiar `destination_path` de vuelta a `original_path`.
