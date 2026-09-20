# Coordinación distribuida de múltiples AMR

Código, configuraciones, evidencia y memoria del Trabajo Fin de Máster de Jorge Luis Mayorga Taborda.

**Título oficial:** *Coordinación distribuida local de múltiples AMR para el transporte cooperativo de cargas heterogéneas en entornos industriales*.

El repositorio estudia la formación distribuida de coaliciones de robots heterogéneos y su acoplamiento con el transporte cooperativo de cargas. La implementación principal es explicable, usa información local y separa asignación estratégica, factibilidad mecánica, movimiento, seguridad, recuperación y comunicación.

## Qué contiene

```text
src/viu_mrob_tfm/       Implementación Python con módulos históricos sp0--sp8
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

La memoria se organiza en tres subproblemas:

- `SP1`: formación distribuida de coaliciones, incluida la asignación de roles/contactos.
- `SP2`: ejecución y transporte cooperativo, seguridad y sustitución tras fallos.
- `SP3`: planificación y tráfico de múltiples coaliciones, escala y red imperfecta.

Los nombres `sp0`--`sp8` se conservan en código, comandos, configuraciones y resultados como identificadores históricos de campañas reproducibles; no representan nueve subproblemas vigentes. Su correspondencia con SP1--SP3 está documentada en `docs/02_RESEARCH_MATRIX.md`.

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
| `viu-run-sp0-theory` | Etapa E0 de SP1: auditoría formal uno-a-uno | `experiments/configs/sp0_theory.yaml` |
| `viu-run-sp1` | SP1 canónico: formación distribuida heterogénea por roles | `experiments/configs/sp1_canonical_smoke.yaml` |
| `viu-run-sp1-validation` | Batería integral SP1 E0--E6: LP/MILP, red, integralidad, escala y uniciclos | `experiments/configs/sp1_validation_smoke.yaml` |
| `viu-run-sp1-conference` | Campaña estadística SP1 con P0, E0--E6, gates, IC, figuras y tablas paper-ready | `experiments/configs/sp1_conference_v1.yaml` |
| `viu-run-sp1-conference-v2` | Remediación dirigida E1/E4/E5/E6 con paso por instancia, refinamiento y recuperación por caminos de aumento | `experiments/configs/sp1_conference_v2.yaml` |
| `viu-render-sp1-e6-videos` | Seis MP4 cenitales auditados desde trayectorias E6 | `results/sp1_validation/SP1_CONFERENCE_VALIDATION_v1/` |
| `viu-package-sp1-results` | Índice maestro con estadísticas y hashes, sin duplicar datos | `results/sp1_full/SP1_COMPLETE_RESULTS_v1/` |
| `viu-run-e1-quorum` | Etapa histórica E1: cuotas y cierre entero | `experiments/configs/sp1_theory.yaml` |
| `viu-run-sp2` | Evidencia de capacidad efectiva | `experiments/configs/sp2_effective_capacity.yaml` |
| `viu-run-sp3-evidence` | Evidencia de factibilidad de wrench | `experiments/configs/sp3_wrench_evidence.yaml` |
| `viu-run-sp4-evidence` | Evidencia de docking y transporte | `experiments/configs/sp4_transport_evidence.yaml` |
| `viu-run-sp5` | Transporte rígido y seguridad | `experiments/configs/sp5_payload_transport_smoke.yaml` |
| `viu-run-sp5-evidence` | Postproceso auditado de SP5 | `experiments/configs/sp5_safety_evidence.yaml` |
| `viu-run-sp6` | Fallo y re-reclutamiento | `experiments/configs/sp6_recovery_smoke.yaml` |
| `viu-run-sp7` | Tráfico entre coaliciones | `experiments/configs/sp7_traffic_confirmatory.yaml` |
| `viu-run-sp8` | Escalabilidad y red | `experiments/configs/sp8_network_confirmatory.yaml` |
| `viu-run-cargo-e2e` | Campaña integrada de SP1--SP2 | `experiments/configs/cargo_e2e_smoke.yaml` |

Los experimentos confirmatorios pueden ser costosos. Antes de ejecutarlos, compruebe `mode`, semillas, número de escenarios y directorio de salida en el YAML correspondiente.

## Ejecutar el SP1 canónico

La validación rápida del módulo nuevo se ejecuta con:

```powershell
viu-run-sp1 --config experiments/configs/sp1_canonical_smoke.yaml
```

También puede ejecutarse sin reinstalar el paquete:

```powershell
python -m viu_mrob_tfm.cli.run_sp1_canonical --config experiments/configs/sp1_canonical_smoke.yaml
```

La campaña genera `runs.csv`, asignaciones robot--slot, decisiones `start/wait/idle`, resumen con intervalos bootstrap, contrastes pareados descriptivos, figuras, `audit.json`, `report.md` y un manifiesto con hashes. Los artefactos del humo quedan en `results/sp1_canonical/SP1_CANONICAL_SMOKE_v1/`.

La configuración `sp1_canonical_confirmatory.yaml` contiene 30 semillas y barridos de régimen, escala y red. La ejecución vigente completó 360 mundos y 3.960 filas método--mundo en `results/sp1_canonical/SP1_CANONICAL_CONFIRMATORY_v1/`; su manifest mantiene el nivel `B-target` y los contrastes se reportan como descriptivos.

### Validación integral E0--E6

La batería ampliada se ejecuta completa con:

```powershell
viu-run-sp1-validation --config experiments/configs/sp1_validation_smoke.yaml --experiment all
```

También puede ejecutarse una sola capa, por ejemplo la recuperación entera:

```powershell
viu-run-sp1-validation --config experiments/configs/sp1_validation_smoke.yaml --experiment e4
```

La separación experimental es: E0 casos manuales; E1 referencias LP no regularizada y regularizada; E2 conectividad; E3 discretización; E4 recuperación entera frente al MILP; E5 escala; y E6 aproximación cinemática de uniciclos hasta posiciones de reclutamiento. E6 no incluye contacto ni transporte de la carga. El humo escribe sus artefactos en `results/sp1_validation/SP1_FULL_VALIDATION_SMOKE_v1/`.

`audit.status=passed` certifica ejecución e invariantes de software. Debe leerse junto con `scientific_status` y `scientific_acceptance`: actualmente el caso pequeño E0 sí supera la aceptación LP regularizado → Rep-C → Rep-D, pero E1--E3 y los Teoremas 1--5 siguen en estado parcial. Los gaps LP se dejan vacíos cuando el perfil no satisface la tolerancia primal. La configuración `sp1_validation_confirmatory.yaml` es deliberadamente costosa y permanece como protocolo candidato hasta su congelación y ejecución completa.

### Orquestador de validación completa de SP1

La campaña canónica y la batería E0--E6 también pueden ejecutarse en una sola orden:

```powershell
viu-run-sp1-full --canonical-smoke
```

Cada campaña conserva sus artefactos en el `output_dir` declarado por su YAML. El orquestador solo escribe un
manifiesto y un informe de agregación en `results/sp1_full/<experiment_id>/`, sin mezclar muestras. Para una
ejecución confirmatoria explícita:

```powershell
viu-run-sp1-full `
  --canonical-config experiments/configs/sp1_canonical_confirmatory.yaml `
  --validation-config experiments/configs/sp1_validation_confirmatory.yaml
```

`audit_status=passed` certifica invariantes y artefactos del software; `scientific_status` mantiene el nivel de
evidencia de cada campaña y no convierte el humo en validación estadística o prueba de convergencia.

### Campaña SP1 para conferencia

La configuración congelada se ejecuta con una sola orden y puede reanudarse por
experimento sin sobrescribir `SP1_FULL_VALIDATION_SMOKE_v1`:

```powershell
python -m viu_mrob_tfm.cli.run_sp1_conference `
  --config experiments/configs/sp1_conference_v1.yaml `
  --resume
```

El ensayo corto de infraestructura usa `sp1_conference_smoke.yaml`. La campaña
completa escribe exclusivamente en
`results/sp1_validation/SP1_CONFERENCE_VALIDATION_v1/` y genera `report.md`,
`report.pdf`, `audit.json`, `manifest.json`, un lock de dependencias,
`seeds.csv`, `exclusions.csv`, `all_runs.csv`, agregados, las tablas T1--T2 y
las figuras F1--F6 en PDF/PNG. `conference-ready` solo se asigna si pasan
conjuntamente los diez gates congelados; en cualquier otro caso se conserva
`partial` y el informe enumera los bloqueadores.

Después de completar E6, las animaciones cenitales auditadas se regeneran desde
las trayectorias guardadas —sin volver a simular ni interpolar estados— con:

```powershell
python -m viu_mrob_tfm.cli.render_sp1_e6_videos `
  --run-dir results/sp1_validation/SP1_CONFERENCE_VALIDATION_v1
```

Se generan seis MP4 H.264, una combinación por escenario `{open,warehouse}` y
tamaño `N={8,20,40}`, junto con `videos/video_catalog.csv`, `VIDEO_INDEX.md` y
un manifiesto con hashes. E6 solo representa aproximación a poses de contacto;
los vídeos no acreditan docking, wrench ni transporte de carga. El título y el
catálogo declaran cuántos obstáculos conservó realmente el simulador; los casos
warehouse N=20 y N=40 retienen cero y no validan evitación.

El índice consolidado, sin duplicar datos crudos, se regenera con:

```powershell
python -m viu_mrob_tfm.cli.package_sp1_results
```

#### Remediación dirigida V2

V2 conserva V1 como línea base y ejecuta solo E1, E4, E5 y E6:

```powershell
python -m viu_mrob_tfm.cli.run_sp1_conference_v2 `
  --config experiments/configs/sp1_conference_v2.yaml `
  --resume
```

La ejecución auditada está en
`results/sp1_validation/SP1_CONFERENCE_VALIDATION_v2/`. Incluye datos crudos,
tablas por tamaño/configuración, intervalos Wilson, McNemar exacto, cinco figuras
en PDF/PNG y seis MP4 cenitales. Los gates técnicos pasan, pero E5 no acredita
escalabilidad de Rep-D: la dinámica no converge desde `N=50` bajo el presupuesto
de 3.000 iteraciones. Los resultados y sus límites se detallan en `report.md` y
`docs/04_CLAIMS_EVIDENCE.md`.

La salida `results/sp1_full/SP1_COMPLETE_RESULTS_v1/` contiene el README de
navegación, estadísticas clave, un índice de 77 artefactos verificados y su
manifest consolidado.

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
