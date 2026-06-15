# Claim-evidence map

Fuente narrativa principal: `docs/doc-04-advanced-report`.

| Claim | Teorema / experimento | Artefacto | Estado |
|---|---|---|---|
| H1: el equilibrio homogéneo sigue la regla de water-filling. | Protocolo mínimo H1. | `exp_results/conclusiones.md`, `exp_results/h1_water_filling.csv`. | PROBADO+GATE |
| H2: el clearing entero reduce coaliciones fraccionarias inútiles. | Protocolo mínimo H2. | `exp_results/conclusiones.md`, `exp_results/h2_integer_clearing.csv`. | PROBADO+GATE |
| H3-A: el precio no es mejora estática. | Protocolo mínimo H3-A. | `exp_results/conclusiones.md`. | NEGATIVO DOCUMENTADO |
| H3-B: el precio solo tiene hipótesis válida en régimen temporal con llegadas/deadlines. | Protocolo mínimo H3-B. | `exp_results/h3b_temporal_arrivals.csv`, `exp_results/conclusiones.md`. | PROBADO+GATE EN MOTOR AISLADO |
| Smith original falla bajo comunicación R3. | Benchmark warehouse, `comm_degradation:R3_p0`. | `results/smith_qr_validation/summary.csv`. | PROBADO EN SMOKE, FALTA n=20 |
| Smith-QR mejora a Smith en R3. | Smith-QR validation, delta pareado. | `results/smith_qr_validation/paired_deltas.csv`. | PROBADO EN SMOKE, FALTA IC95 n=20 |
| Smith-QR domina a greedy en R3. | Comparación R3. | `results/smith_qr_validation/paired_deltas.csv`. | FALSO EN SMOKE |
| Logit/mutation rescata R3 sin cambiar mecanismo. | `smith_logit_validation`. | `results/smith_logit_validation/`. | NEGATIVO DOCUMENTADO |
| MARL-proxy compite empíricamente pero no sustituye teoría interpretable. | MARL proxy validation. | `configs/marl/marl_proxy.yaml`, `results/marl_validation/summary.csv`. | BASELINE IMPLEMENTADO, FALTA CAMPAÑA |
| Centralizado global es referencia no deployable; centralizado limitado pierde bajo red degradada. | `classic_centralized_limited_comm` en R3. | `results/smith_qr_validation/summary.csv`. | PROBADO EN SMOKE, FALTA n=20 |
| CoppeliaSim valida plausibilidad robótica, no la decisión científica principal. | Generación de escenas industrial warehouse. | `coppeliasim/scenes/*.yaml`, `coppeliasim/scenes/*.lua`, `results/coppeliasim_validation/scene_manifest.csv`. | GENERADO, NO ABIERTO |
| El TFM está listo para submit. | Auditoría integral. | `docs/auditoria_submit_ready.md`. | NO: PENDIENTE |

## Comandos de reproducción largos

```powershell
python scripts\validate_smith_qr.py --seeds 20 --out results\smith_qr_validation
python scripts\validate_marl_proxy.py --seeds 20 --out results\marl_validation
python scripts\build_coppelia_scene.py --scene-dir coppeliasim\scenes --out results\coppeliasim_validation
```

## Regla de redacción

Ninguna conclusión del cuerpo principal debe afirmar dominancia de Smith-QR sobre greedy
o MARL hasta que `paired_deltas.csv` tenga IC95 positivo con 20 semillas. Si el resultado
se mantiene negativo, se reporta como frontera: Smith-QR rescata el colapso de Smith, pero
no es la mejor política operativa en R3.
