# Índice de resultados

Este directorio conserva la evidencia numérica utilizada por la memoria. La fuente de verdad para determinar si una afirmación está soportada es `docs/04_CLAIMS_EVIDENCE.md`; este archivo solo facilita la navegación.

## Organización

```text
results/
├── sp0/ ... sp8/       Salidas de campañas por subproblema
├── processed/          Síntesis auditadas usadas por tablas y figuras
├── coppeliasim_validation/
│                       Validaciones complementarias en simulador
├── physical_coalition/ Certificados físicos complementarios
├── theory_validation/  Comprobaciones numéricas de resultados formales
├── raw/                Datos crudos compartidos
├── figures/            Figuras globales generadas
└── tables/             Tablas globales generadas
```

Cada campaña conserva, cuando aplica, el YAML o manifiesto efectivo, semillas, tablas por ejecución, resúmenes, contrastes, auditorías y figuras. Los nombres `smoke`, `pilot` y `confirmatory` indican su función experimental; una ejecución de humo no constituye evidencia científica.

## Evidencia canónica actual

| Bloque | Directorio principal | Contenido |
|---|---|---|
| SP0 | `sp0/SP0_THEORY_v1/` | Juego potencial, auditoría exacta y comparación pareada. |
| SP1 | `sp1/SP1_QUORUM_v1/` | Cuotas variables, escasez y cierre entero. |
| SP2 | `processed/sp2/SP2_EFFECTIVE_CAPACITY_EVIDENCE_v1/` | Capacidad efectiva, cobertura y ablación. |
| SP3 | `processed/sp3/SP3_WRENCH_EVIDENCE_v1/` | Factibilidad de wrench y falsos positivos escalares. |
| SP4 | `processed/sp4/SP4_TRANSPORT_EVIDENCE_v1/` | Docking dinámico y transporte rígido como capas separadas. |
| SP5 | `processed/sp5/SP5_SAFETY_EVIDENCE_v1/` | Seguridad, progreso y separación RAW--SAFE--EXEC. |
| SP6 | `processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/` | Fallo, re-reclutamiento y recuperación. |
| SP7 | `processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/` | Tráfico, reservas y conflictos entre coaliciones. |
| SP8 | `processed/sp8/SP8_NETWORK_CONFIRMATORY_v1/` | Escala, mensajes, retardos y pérdidas. |
| Integrada | `processed/integrated/CARGO_E2E_CONFIRMATORY_v1/` | Composición experimental de SP2--SP6. |

Las campañas originales que alimentan un postproceso se mantienen en su carpeta `spX/`. Los directorios históricos o complementarios no sustituyen la evidencia señalada en la matriz de afirmaciones.

## Reproducción

Las configuraciones versionadas viven en `experiments/configs/`. Por ejemplo:

```powershell
viu-run-sp0-theory --config experiments/configs/sp0_theory.yaml
viu-run-sp5 experiments/configs/sp5_payload_transport_confirmatory.yaml
viu-run-sp6 experiments/configs/sp6_recovery_confirmatory.yaml
viu-run-sp7 experiments/configs/sp7_traffic_confirmatory.yaml
viu-run-sp8 experiments/configs/sp8_network_confirmatory.yaml
viu-run-cargo-e2e experiments/configs/cargo_e2e_confirmatory.yaml
```

Antes de repetir una campaña confirmatoria, revise su coste y cambie `output_dir` si desea conservar intacta la evidencia existente. Las tablas y figuras de la memoria no deben editarse manualmente.
