# 02 — Fuente canónica

Este directorio no duplica la fuente editable. La autoridad documental permanece en [`docs/doc-05-final-report`](../../doc-05-final-report/).

## Archivos principales

- [main.tex](../../doc-05-final-report/main.tex): ensamblaje y orden narrativo.
- [sections](../../doc-05-final-report/sections/): capítulos, anexos y declaraciones.
- [references.bib](../../doc-05-final-report/references.bib): base bibliográfica.
- [viu-mrob-midreport.sty](../../doc-05-final-report/viu-mrob-midreport.sty): estilo de maquetación.
- [main.pdf](../../doc-05-final-report/main.pdf): salida canónica de compilación.

## Orden de la memoria

La fuente ensambla portada, resumen, *abstract*, índice y nomenclatura; después introduce problema, objetivos, hipótesis y metodología; desarrolla el marco teórico; presenta resultados integrados y modulares; cierra con conclusiones, bibliografía, reproducibilidad, validación, declaración de uso de IA y declaraciones académicas.

El núcleo matemático compilado está en [integrated-theory-core.tex](../../doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex). El suplemento [expanded-theory.tex](../../doc-05-final-report/sections/mainmatter/05-theoretical-framework/expanded-theory.tex) conserva desarrollos ampliados y no debe confundirse con evidencia empírica adicional.

## Compilación

Desde la raíz del repositorio:

```powershell
make report-pdf
```

Motor registrado: LuaLaTeX + Biber. Una modificación solo se considera cerrada cuando la compilación, las comprobaciones automáticas, la revisión visual y los hashes vuelven a pasar.
