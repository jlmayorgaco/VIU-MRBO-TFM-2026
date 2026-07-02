# Alineacion con guia VIU

Este mapa deja explicita la estructura de la memoria final frente a la organizacion esperada para un TFM VIU. Los PDFs institucionales originales estan referenciados en `cleanup_manifest.csv` y se mantienen fuera del repositorio.

| Bloque VIU esperado | Ubicacion en la memoria final |
| --- | --- |
| Portada institucional | `docs/doc-05-final-report/main.tex` mediante `\makeviucover` y `viu-mrob-midreport.sty` |
| Resumen y palabras clave | `main.tex`, entorno `viuabstract` |
| Indice / contenido | `main.tex`, `\tableofcontents` |
| Nomenclatura | `sections/00-nomenclatura.tex` |
| Introduccion y contexto | `sections/01-introduccion.tex` |
| Objetivos | `sections/02-objetivos.tex` |
| Hipotesis / preguntas de investigacion | `sections/03-hipotesis.tex` |
| Metodologia | `sections/04-metodologia.tex` |
| Marco teorico / estado del arte | `sections/05-marco.tex` y `docs/literature/` |
| Modelo y propuesta tecnica | `sections/03-escalera-modular.tex`, `sections/06-modelo-control.tex` |
| Implementacion | `sections/07-implementacion.tex` |
| Resultados y validacion | `sections/08-resultados.tex`, `results/validation_suite_v1/` |
| Conclusiones | `sections/09-conclusiones.tex` |
| Anexos | `sections/anexo-a-matematico.tex`, `sections/anexo-b-reproducibilidad.tex`, `sections/anexo-c-validacion.tex` |
| Referencias | `references.bib`, estilo `apalike` |

Regla operativa: `docs/doc-05-final-report` es la unica version final; `doc-04` y `doc-06` quedan como entregas de trazabilidad.