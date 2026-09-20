# `material/` — corpus de consulta

Lo que se lee para escribir el TFM. **No es fuente del documento**: aquí no hay
nada que compile ni de lo que dependa `make`, `thesis/build.ps1` o los
`build.ps1` de `Subdocuments/`.

| Carpeta | Qué contiene | Versionado |
|---|---|---|
| `books/` | 43 PDF de libros y monografías (control cooperativo, consenso, teoría de coaliciones, robótica móvil). Fuente primaria para el marco teórico. | No |
| `compendios/` | 43 PDF de compendios, dossiers e informes generados a lo largo del proyecto. Material de trabajo, no publicable. | No |

Los PDF están en `.gitignore`. Solo se versiona este README.

## Cómo se usa

Una fuente de `books/` no entra en el TFM hasta pasar por
`references/LITERATURE_LEDGER.md` con estado `VERIFICADA`: título, autores,
venue, año y contenido relevante comprobados. Esa es la regla de la habilidad
`citation-hygiene` y no la relaja el hecho de tener el PDF a mano.

La auditoría de qué cubre este corpus y qué afirmaciones del documento siguen
sin respaldo primario está en `docs/16_AUDITORIA_MATERIAL_WORK.md`.

## Qué no va aquí

- Resultados de campaña → `results/` (vivo) o `legacy/results/` (archivado).
- Borradores propios en LaTeX → `Subdocuments/`.
- El artículo *megajuego* → `paper/`.
