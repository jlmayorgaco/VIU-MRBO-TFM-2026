---
name: latex-build-tfm
description: Cómo compilar este TFM sin redescubrirlo en cada sesión - motor correcto, orden de pasadas, scripts por subdocumento y errores conocidos de MiKTeX en PowerShell. Úsala antes de intentar compilar cualquier .tex del repositorio o de diagnosticar un fallo de compilación.
---

# Compilar el TFM

## 1. Motor

**LuaLaTeX**, no pdflatex. Los documentos cargan `fontspec` y abortan con
«Este documento requiere LuaLaTeX» seguido de un error fatal si se usa pdflatex.

**No hay latexmk** (no hay Perl en esta máquina). Las pasadas se orquestan desde
los `build.ps1`.

Excepción histórica: el informe intermedio en `docs/doc-02-mid-report/` se
compila con **XeLaTeX**. No confundir con el TFM.

## 2. Comandos

```powershell
# Tesis completa
make thesis                       # = powershell -ExecutionPolicy Bypass -File thesis/build.ps1
powershell -File thesis/build.ps1 -SkipBiber    # iteración rápida sin rehacer bibliografía

# Subdocumentos
powershell -File Subdocuments/SP1/build.ps1
powershell -File Subdocuments/SP2/build.ps1
```

Orden de pasadas en todos ellos: `lualatex` → `biber` → `lualatex` → `lualatex`.
Tres pasadas de LuaLaTeX. Con menos, las referencias cruzadas y el índice quedan
desactualizados sin avisar de forma evidente.

`thesis/build.ps1` ejecuta antes dos comprobaciones en Python
(`check_protected_tikz_figures.py`, `export_aws_industrial2_latex.py`). Si fallan,
la compilación no debe forzarse: indican figuras protegidas alteradas.

## 3. La trampa de PowerShell 5.1

`Subdocuments/SP1/build.ps1` **no** fija `$ErrorActionPreference = 'Stop'`, y es
deliberado. MiKTeX escribe avisos en stderr (por ejemplo «major issue: So far,
you have not checked for updates»). Si el llamador captura stderr —una tarea de
VS Code, una redirección `2>&1`, CI—, PowerShell 5.1 convierte cada línea en un
`ErrorRecord` y aborta la compilación **aunque LuaLaTeX haya terminado con
código 0**.

Regla: el control de errores se hace con `$LASTEXITCODE`, nunca redirigiendo
stderr de un ejecutable nativo. No añadas `2>&1` a estos comandos.

## 4. Pipeline de cifras y figuras

Antes de compilar para revisión de contenido, regenera lo que dependa de datos:

```bash
make smoke-sp1                    # comprobación rápida de la teoría SP1
make smoke-sp1-canonical          # campaña canónica reducida
python Subdocuments/SP1/scripts/sp1_n4_hstar.py
python Subdocuments/SP1/scripts/sp1_n4_cross_family.py
```

Los scripts escriben `generated/*.tex`. **La prosa no contiene cifras a mano**:
si un número del texto no coincide con el PDF, el fallo está en la macro o en la
campaña, no en el texto.

## 5. Comprobaciones antes de congelar

```bash
python Subdocuments/SP1/scripts/sp1_final_figs/meta_lint.py Subdocuments/SP1/sp1.tex
python ~/.claude/skills/no-ai-slop/scripts/slop_lint.py Subdocuments/SP1/sp1.tex
grep -c "Overfull" Subdocuments/SP1/build/sp1.log
```

Además: numeración consecutiva de figuras, tablas y ecuaciones; sin página
huérfana; 0 bandas negras de plantilla en el `main`; extensión dentro del
presupuesto de `docs/01_VIU_REQUIREMENTS.md` §6.

## 6. Higiene del repositorio

Los directorios `thesis/build-corrupt-*`, `thesis/$outDir` y los
`Subdocuments/SP1/sp1.tex.bak_*` son residuos de sesiones anteriores. No son
fuentes de verdad: no leas de ellos ni los uses como referencia de contenido.
Si necesitas una versión anterior, usa `git log`.
