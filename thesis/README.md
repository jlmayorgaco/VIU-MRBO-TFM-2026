# Memoria del TFM

La fuente principal es `main.tex`. El árbol se divide en metadatos y comandos (`config/`), preliminares, capítulos y anexos (`sections/`). Los artefactos de compilación se generan en `build/` y no se versionan.

## Compilación

Desde este directorio, en PowerShell:

```powershell
.\build.ps1
```

El PDF resultante queda en `build/main.pdf`. El script ejecuta LuaLaTeX, Biber y las pasadas adicionales necesarias para estabilizar índices y referencias. Si Perl está instalado, también puede usarse `latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex`.

La plantilla LaTeX reproduce los requisitos documentados en `docs/01_VIU_REQUIREMENTS.md` y fue destilada contra el DOCX oficial conservado en `resources/`. La evidencia, diferencias corregidas y limitaciones del cotejo se registran en `docs/06_VIU_TEMPLATE_FIDELITY.md`.
