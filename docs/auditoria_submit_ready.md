# Auditoría submit-ready

Fecha: 2026-06-15.

Veredicto global: **FAIL controlado**. La infraestructura clave está implementada, pero
la tesis todavía no es submit-ready porque faltan campaña estadística completa,
CoppeliaSim abierto/medido y recompilación final del manuscrito con figuras definitivas.

| Gate | Estado | Evidencia | Acción requerida |
|---|---|---|---|
| Narrativa Smith/coaliciones | PARTIAL | `docs/doc-04-advanced-report/sections/06-resultados.tex`, `07-conclusiones.tex`. | Reescribir título/resumen/objetivos completos. |
| H1 water-filling | PASS | `exp_results/conclusiones.md`. | Integrar figura PDF-ready en el cuerpo. |
| H2 integer clearing | PASS | `exp_results/conclusiones.md`. | Integrar tabla/figura final. |
| H3-A negativo estático | PASS | `exp_results/conclusiones.md`. | Mantener como resultado negativo explícito. |
| H3-B temporal | PASS en motor mínimo | `exp_results/h3b_temporal_arrivals.csv`. | Ejecutar sensibilidad final por llegada/deadline. |
| Smith-QR implementado sin alterar Smith | PASS smoke | `src/viu_mrob_tfm/simulations/warehouse.py`, `results/smith_qr_validation/summary.csv`. | Añadir unitarios específicos y correr 20 semillas. |
| R3 Smith-QR vs Smith | PASS smoke | Delta +0.2481 en `paired_deltas.csv`, n=1. | Confirmar IC95 con n=20. |
| Smith-QR vs greedy/MARL | FAIL smoke | Smith-QR queda por debajo en R3, n=1. | Reportar frontera o mejorar mecanismo antes de claim fuerte. |
| Logit/mutation | NEGATIVO | `results/smith_logit_validation/`. | Mantener como resultado negativo en discusión. |
| Centralizado limitado | PASS smoke | `classic_centralized_limited_comm` en R3: captura 0.1072. | Ampliar sweep R12/R8/R6/R4/R3/R1.5. |
| MARL baseline | PARTIAL | `configs/marl/marl_proxy.yaml`, `results/marl_validation`. | Entrenar PPO/MAPPO-lite si se quiere claim MARL real; si no, mantener proxy. |
| CoppeliaSim escenas | PARTIAL | `coppeliasim/scenes/*.lua`, `scene_manifest.csv`. | Abrir escenas, grabar MP4, medir colisiones/distancias. |
| Figuras PDF-ready | PARTIAL | `results/figures_pdf/` existe de iteraciones previas. | Registrar nuevas figuras Smith-QR/MARL/Coppelia en manifest. |
| Anexo teórico mini-libro | PARTIAL | `sections/08-anexo-teorico-extendido.tex`. | Añadir teoremas/lemmas de Smith-QR y contraejemplo R3. |
| Tests Python | PASS parcial | `py_compile` scripts/simulador y 3 tests pytest pasan. | Ejecutar suite completa antes de submit. |
| Manuscrito PDF | FAIL entorno | `lualatex` falla por `luaotfload`: no hay ruta de caché MiKTeX escribible; `pdflatex` no sirve porque el documento usa `fontspec`. | Corregir permisos/cache de MiKTeX o compilar en entorno LaTeX limpio. |
| BibTeX/citas | NOT RUN | No auditado. | Ejecutar auditoría de referencias antes de submit. |

## Decisión de integridad

El resultado de Smith-QR debe presentarse con tres frases obligatorias:

1. Smith-QR rescata parcialmente el colapso de Smith en R3.
2. La evidencia actual es smoke (`n=1`), no campaña estadística final.
3. Greedy y MARL-proxy siguen por encima de Smith-QR en la semilla inicial; si esto se
   mantiene con 20 semillas, es una frontera del método y no debe ocultarse.

## Próximo bloque ejecutable

```powershell
python scripts\validate_smith_qr.py --seeds 20 --out results\smith_qr_validation
python scripts\validate_marl_proxy.py --seeds 20 --out results\marl_validation
python scripts\build_coppelia_scene.py --scene-dir coppeliasim\scenes --out results\coppeliasim_validation
```
