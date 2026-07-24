# Reproducción de SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1

Entorno: Python 3.11+, dependencias fijadas en `pyproject.toml`.

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game_v1 --mode full --workers 6 --resume
```

Los shards se guardan en `checkpoints/`. `--resume` reutiliza shards completos;
`--force` los recalcula. Las semillas de calibración y evaluación son disjuntas.
El guard de rondas genera censura explícita; no equivale a convergencia.
