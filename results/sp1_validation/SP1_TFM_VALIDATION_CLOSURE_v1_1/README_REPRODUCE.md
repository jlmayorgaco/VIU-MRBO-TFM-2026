# Reproducción de SP1_TFM_VALIDATION_CLOSURE_v1_1

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_validation_closure_v1_1 --mode full --workers 6 --resume
```

Los checkpoints son idempotentes. `--force` recalcula los shards. V1 se lee
en modo inmutable; los dos CSV omitidos se reconstruyen en memoria desde sus
Parquet únicamente para verificar sus hashes.
