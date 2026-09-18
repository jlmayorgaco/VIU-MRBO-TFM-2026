# Citation audit trace: kuhn1955Hungarian

- Action: KEEP
- Existence: VERIFIED
- Metadata: VERIFIED
- Context: SUPPORTED
- Source type: crossref_doi
- Documents: monograph, thesis
- Citation contexts: 11 (0 nocite)

## Sources checked

- https://api.crossref.org/works/10.1002%2Fnav.3800020109
- https://doi.org/10.1002/nav.3800020109

## Source note

Crossref DOI metadata verifies existence and core bibliographic metadata; DOI URL retained as resolver/publisher route.

## Metadata notes

- Automated DOI metadata record available from Crossref.

## Active citation contexts

- monograph:sections/source-snapshot/appendices/02-sp0-proofs.tex:9 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El algoritmo húngaro resuelve el problema denso en $O(N^3)$ \parencite{kuhn1955Hungarian}.
- monograph:sections/source-snapshot/mainmatter/05-theoretical-framework.tex:11 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El caso uno a uno admite asignación bipartita y el algoritmo húngaro \parencite{kuhn1955Hungarian}.
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp0.tex:71 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El algoritmo húngaro lo resuelve en \(O(N^3)\) tiempo y \(O(N^2)\) memoria \parencite{kuhn1955Hungarian}, por lo que E0 pertenece a \(\mathsf P\).
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp0.tex:151 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: \begin{table}[!htbp] \centering \caption{Comparación computacional de métodos en E0.} \label{tab:sp0-method-literature} \scriptsize \setlength{\tabcolsep}{1.5pt} \renewcommand{\arraystretch}{1.04} \begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{2.25cm} >{\raggedright\arraybackslash}p{1.45cm} >{\raggedright\arraybackslash}p{2.25cm} >{\raggedright\arraybackslash}p{2.15cm} >{\raggedright\arraybackslash}p{1.55cm} Y} \toprule Método/fuente & Clase & Coste & Arq./información & Parámetros & Garantía/límite \\ \midrule Algoritmo húngaro \parencite{kuhn1955Hungarian} & LAP en P & $O(m^3...
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp2.tex:112 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El Húngaro expandido y CBBA-capacidad modifican los problemas estudiados en sus fuentes, por lo que sus garantías originales no se transfieren a esta comparación \parencite{kuhn1955Hungarian,choiBrunetHow2009CBBA}.
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp2.tex:127 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: \\ Húngaro expandido \parencite{kuhn1955Hungarian} & Aproximación LAP en P & $O(M^3)$, $M=\max\{N,S\}$ & Central; matriz robot--puesto global & Número y regla de puestos & Exactitud para el LAP expandido; capacidad aproximada mediante puestos.
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp3.tex:179 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: \\ Referencia escalar/húngara \parencite{kuhn1955Hungarian} & Aproximación LAP en P & $O(\max\{N,S\}^3)$ & Central; coste robot--puesto escalar & Pesos escalares & Óptimo del LAP escalar; la factibilidad vectorial requiere guardia.
- thesis:sections/source-snapshot/mainmatter/05-theoretical-framework.tex:11 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El caso uno a uno admite asignación bipartita y el algoritmo húngaro \parencite{kuhn1955Hungarian}.
- thesis:sections/source-snapshot/mainmatter/06-results-and-analysis/sp2.tex:112 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El Húngaro expandido y CBBA-capacidad modifican los problemas estudiados en sus fuentes, por lo que sus garantías originales no se transfieren a esta comparación \parencite{kuhn1955Hungarian,choiBrunetHow2009CBBA}.
- thesis:sections/source-snapshot/mainmatter/06-results-and-analysis/sp2.tex:127 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: \\ Húngaro expandido \parencite{kuhn1955Hungarian} & Aproximación LAP en P & $O(M^3)$, $M=\max\{N,S\}$ & Central; matriz robot--puesto global & Número y regla de puestos & Exactitud para el LAP expandido; capacidad aproximada mediante puestos.
- thesis:sections/sp1-wrench-condensed.tex:54 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: La guardia comprueba \eqref{eq:sp3-wrench}; el oráculo enumera instancias pequeñas, Hungarian es solo referencia escalar y CBBA, voraz y dinámicas poblacionales son comparadores aproximados \parencite{kuhn1955Hungarian,choiBrunetHow2009CBBA,sandholm2010population}.

## BibLaTeX entry

```bibtex
@article{kuhn1955Hungarian,
  author       = {Kuhn, Harold W.},
  title        = {The {Hungarian} method for the assignment problem},
  journaltitle = {Naval Research Logistics Quarterly},
  date         = {1955},
  volume       = {2},
  number       = {1-2},
  pages        = {83--97},
  doi          = {10.1002/nav.3800020109},
  url          = {https://doi.org/10.1002/nav.3800020109}
}
```
