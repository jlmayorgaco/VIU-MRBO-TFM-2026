# Reproducción de SP1_SCALE_QPG_BENCHMARK_v2_preview

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_scale_qpg_v2 --mode preview --workers 6 --resume
```

Los parámetros se calibran únicamente con semillas 91000--91029 y se
congelan antes del preview. Full exige un `audit.json` de preview aprobado.
Los shards en `checkpoints/` son idempotentes; `--force` los recalcula.
