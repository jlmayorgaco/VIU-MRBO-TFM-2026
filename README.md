# VIU-MROB-TFM-2026

Repositorio base del Trabajo Fin de Máster del **Máster Universitario en Robótica y Automatización de Procesos (MROB)** de la **Universidad Internacional de Valencia (VIU)**. El proyecto estudia transporte cooperativo plano de cargas con **2 a 4 AGVs**, grafos de comunicación locales, un controlador distribuido nominal basado en consenso y una variante adaptativa/robusta para incertidumbre inercial de la carga, con validación centrada en simulación numérica reproducible.

**Tema del TFM:** *Control distribuido adaptativo basado en consenso para transporte cooperativo multi-AGV bajo incertidumbre inercial de la carga.*

**Estado del repositorio:** `initial scaffolding`

**Stack previsto:** Python 3.11+, NumPy, SciPy, Matplotlib, pytest y LaTeX.

## Estructura principal

```text
.
├── docs/               # Propuesta, informes intermedios y memoria final
├── src/                # Paquete Python principal
├── experiments/        # Configuraciones reproducibles de experimentos
├── results/            # Resultados brutos, procesados y figuras
├── tests/              # Smoke tests y pruebas unitarias iniciales
├── scripts/            # Utilidades de ejecución y limpieza
└── assets/             # Recursos institucionales y diagramas
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

En Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Ejecución de pruebas

```bash
pytest
```

## Compilación de la propuesta

```bash
make proposal-pdf
```

El PDF se genera desde [`docs/doc-01-proposal/main.tex`](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-01-proposal/main.tex) y se deposita en `docs/doc-01-proposal/build/`.

## Nota

Este repositorio tiene fines académicos y se encuentra en desarrollo activo. La estructura actual prioriza separación clara entre dominio, control, simulación, métricas, experimentos, visualización y documentación, sin implementar todavía el controlador completo del TFM.
