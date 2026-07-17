# Coordinación distribuida de múltiples AMR

Código, configuraciones, evidencia y memoria del Trabajo Fin de Máster de Jorge Luis Mayorga Taborda.

**Título oficial:** *Coordinación distribuida local de múltiples AMR para el transporte cooperativo de cargas heterogéneas en entornos industriales*.

El repositorio estudia la formación distribuida de coaliciones de robots heterogéneos y su acoplamiento con el transporte cooperativo de cargas. La implementación principal es explicable, usa información local y separa asignación estratégica, factibilidad mecánica, movimiento, seguridad, recuperación y comunicación.

## Qué contiene

```text
src/viu_mrob_tfm/       Implementación Python organizada por SP0--SP8
experiments/configs/    Configuraciones YAML versionadas
tests/                  Pruebas de modelos, invariantes y experimentos
results/                Evidencia cruda, procesada, tablas y figuras
thesis/                 Memoria VIU en LaTeX
docs/                   Alcance, protocolo y trazabilidad científica
references/             Registro bibliográfico y rúbrica metodológica
plans/                  Registro de decisiones y trabajos complejos
resources/              Plantilla oficial de la memoria
scripts/                Generadores auxiliares de artefactos
```

Los subproblemas forman una escalera de capacidades:

- `SP0--SP2`: asignación, cardinalidad y capacidades heterogéneas.
- `SP3--SP4`: factibilidad mecánica y transporte de la carga.
- `SP5--SP7`: seguridad, recuperación y tráfico entre coaliciones.
- `SP8`: escalabilidad y degradación de la comunicación.

## Instalación

Se requiere Python 3.11 o posterior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Para reproducir el entorno usado por la campaña confirmatoria puede instalarse `requirements-reproducible.txt` antes del paquete:

```powershell
python -m pip install -r requirements-reproducible.txt
python -m pip install -e . --no-deps
```

## Comprobación rápida

```powershell
python -m pytest -q
python -m compileall -q src tests
```

El experimento de humo más corto del transporte cooperativo se ejecuta con:

```powershell
viu-run-sp5 experiments/configs/sp5_payload_transport_smoke.yaml
```

Los resultados se escriben en la ruta `output_dir` declarada por cada YAML. Las semillas están fijadas en las configuraciones y todos los métodos de una comparación reciben instancias pareadas.

## Entradas de consola

| Comando | Función | Configuración de ejemplo |
|---|---|---|
| `viu-run-sp0-theory` | Auditoría formal y numérica de SP0 | `experiments/configs/sp0_theory.yaml` |
| `viu-run-sp1` | Cuotas y cierre entero de SP1 | `experiments/configs/sp1_theory.yaml` |
| `viu-run-sp2` | Evidencia de capacidad efectiva | `experiments/configs/sp2_effective_capacity.yaml` |
| `viu-run-sp3-evidence` | Evidencia de factibilidad de wrench | `experiments/configs/sp3_wrench_evidence.yaml` |
| `viu-run-sp4-evidence` | Evidencia de docking y transporte | `experiments/configs/sp4_transport_evidence.yaml` |
| `viu-run-sp5` | Transporte rígido y seguridad | `experiments/configs/sp5_payload_transport_smoke.yaml` |
| `viu-run-sp5-evidence` | Postproceso auditado de SP5 | `experiments/configs/sp5_safety_evidence.yaml` |
| `viu-run-sp6` | Fallo y re-reclutamiento | `experiments/configs/sp6_recovery_smoke.yaml` |
| `viu-run-sp7` | Tráfico entre coaliciones | `experiments/configs/sp7_traffic_confirmatory.yaml` |
| `viu-run-sp8` | Escalabilidad y red | `experiments/configs/sp8_network_confirmatory.yaml` |
| `viu-run-cargo-e2e` | Campaña integrada SP2--SP6 | `experiments/configs/cargo_e2e_smoke.yaml` |

Los experimentos confirmatorios pueden ser costosos. Antes de ejecutarlos, compruebe `mode`, semillas, número de escenarios y directorio de salida en el YAML correspondiente.

## Memoria

La fuente principal es `thesis/main.tex`. En Windows con MiKTeX:

```powershell
powershell -ExecutionPolicy Bypass -File thesis/build.ps1
```

El PDF resultante queda en `thesis/build/main.pdf`. Las afirmaciones de la memoria están vinculadas con su nivel de evidencia en `docs/04_CLAIMS_EVIDENCE.md`; las referencias se controlan en `references/LITERATURE_LEDGER.md`.

## Reglas de reproducibilidad

- No editar manualmente cifras o tablas derivadas.
- Conservar semillas y parámetros en YAML.
- Separar resultados crudos, procesados, figuras y tablas.
- Ejecutar la suite de pruebas después de modificar modelos, métricas o integradores.
- Actualizar la matriz de evidencia antes de redactar conclusiones nuevas.

Consulte `docs/00_TFM_CHARTER.md` para el alcance científico y `docs/03_EXPERIMENT_PROTOCOL.md` para el protocolo completo.

## Licencia

El código se distribuye bajo la licencia MIT incluida en `LICENSE`. La memoria, los recursos institucionales y los resultados conservan la autoría y condiciones que les correspondan.
