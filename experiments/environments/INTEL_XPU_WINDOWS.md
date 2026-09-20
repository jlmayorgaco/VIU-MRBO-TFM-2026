# Entorno diagnóstico Intel XPU para Windows

Este entorno es opcional y no reemplaza el entorno CPU de referencia. Su uso
se limita a pruebas de aceleración; SciPy/HiGHS permanece en CPU.

## Creación reproducible

```powershell
conda create -n mrob-xpu python=3.11 pip -y
conda run -n mrob-xpu python -m pip install torch==2.13.0+xpu --index-url https://download.pytorch.org/whl/xpu
conda run -n mrob-xpu python -m pip install -e ".[dev]"
```

## Verificación

```powershell
conda run -n mrob-xpu python -c "import torch; print(torch.__version__); print(torch.xpu.is_available()); print(torch.xpu.get_device_name(0))"
```

## Benchmark

```powershell
conda run -n mrob-xpu python -m viu_mrob_tfm.benchmarks.intel_xpu --preset quick
```

Las salidas se escriben por defecto en `output/intel_xpu_benchmark/`. El tiempo
`resident` excluye las transferencias iniciales; `end_to_end` incluye copias de
entrada y salida. Los resultados son diagnóstico de este equipo y no evidencia
confirmatoria del TFM.
