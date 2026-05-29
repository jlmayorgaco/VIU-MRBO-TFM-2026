# Plantilla LaTeX VIU - TFM MROB

Esta carpeta contiene una versión LaTeX de la plantilla de memoria VIU usada para la Tarea 1 del TFM.

## Archivos principales

- `main.tex`: contenido de la Tarea 1.
- `viu-mrob-memoria.sty`: estilo LaTeX que replica la estructura visual de la plantilla Word.
- `assets/`: recursos extraídos del DOCX oficial, incluyendo la portada VIU y la figura metodológica.
- `build/main.pdf`: PDF compilado.

## Compilación

Desde esta carpeta:

```powershell
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```

Se usa XeLaTeX para soportar Arial y caracteres Unicode en español.
