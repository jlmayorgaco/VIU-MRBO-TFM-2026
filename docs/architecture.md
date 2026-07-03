# Arquitectura V6 AMR

Este repositorio no adopta un paquete paralelo `agv_tfm`. La arquitectura canonica es
`src/viu_mrob_tfm`, porque ya integra codigo, documentos, scripts, tests y resultados
del TFM. Crear otro paquete duplicaria contratos y romperia reproducibilidad.

## Separacion de responsabilidades

- `domain`: entidades fisicas y de estado (`AMR`, robots runtime, cargas, mundo, grafo).
- `scenarios` y `simulations`: definicion de mundos reproducibles y motores de simulacion.
- `allocation`: asignadores discretos, incluido `SmithQRAllocator`.
- `control` y `controllers`: control continuo, formacion rigida y campos vectoriales.
- `metrics`, `validation` y `experiments`: calculo de evidencia, gates estadisticos y ejecucion reproducible.
- `plotting`, `scripts` y `coppeliasim`: visualizacion, entry points y validacion externa.

La regla de diseno se mantiene: escenario, metodo, experimento, corrida, metrica,
hipotesis, grafico y reporte son conceptos distintos. En la V6 esa separacion existe
como modulos y contratos compactos, no como una copia literal del arbol solicitado en el
andamio inicial.

## Terminologia canonica

Desde esta revision, el termino canonico del dominio es `AMR` (autonomous mobile robot).
Los nombres `AGV`, `AGVState`, `agv_count`, `agv_states` y `agvs` se conservan solo como
aliases legacy para configs, notebooks y tests historicos. Los nuevos configs deben usar
`amr_count`; los nuevos objetos deben importarse como `AMR` y `AMRState`.

## Entry points validados

- `python scripts/run_experiment.py experiments/exp-001-baseline-nominal/config.yaml`
- `python scripts/run_experiment.py --config experiments/exp-001-baseline-nominal/config.yaml`
- `viu-run-experiment experiments/exp-001-baseline-nominal/config.yaml` tras `pip install -e .`
- `python -m viu_mrob_tfm.validation.suite`
- `viu-validate-suite` tras `pip install -e .`

## Criterio PhD-level aplicado

La decision de arquitectura prioriza contratos ejecutables sobre carpetas vacias:
compatibilidad hacia atras, seeds deterministas, tests de dominio/simulacion, CLI
instalable, y separacion clara entre los bloques de investigacion. Las extensiones
futuras (MARL, MPC, ADMM, CBF-QP, CBS, ORCA) deben entrar como metodos/politicas con
contratos y tests propios, no como logica embebida en configs de experimento.
