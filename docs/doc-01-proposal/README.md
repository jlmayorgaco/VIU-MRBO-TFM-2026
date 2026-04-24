# Propuesta TFM

Documento preliminar en LaTeX para la **Propuesta de Trabajo Fin de Máster**. La estructura usa un estilo propio con acento visual naranja, portada académica, tabla de contenidos y secciones modulares mediante `\input{sections/...}`.

## Compilación

Desde la raíz del repositorio:

```bash
make proposal-pdf
```

Secuencia manual equivalente:

```bash
cd docs/doc-01-proposal
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
bibtex build/main
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```
