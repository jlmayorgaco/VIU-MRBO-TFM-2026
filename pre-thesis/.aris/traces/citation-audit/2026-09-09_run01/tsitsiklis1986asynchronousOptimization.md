# Citation audit trace: tsitsiklis1986asynchronousOptimization

- Action: KEEP
- Existence: VERIFIED
- Metadata: VERIFIED
- Context: SUPPORTED
- Source type: crossref_doi
- Documents: monograph, thesis
- Citation contexts: 3 (0 nocite)

## Sources checked

- https://api.crossref.org/works/10.1109%2FTAC.1986.1104412
- https://doi.org/10.1109/TAC.1986.1104412

## Source note

Crossref DOI metadata verifies existence and core bibliographic metadata; DOI URL retained as resolver/publisher route.

## Metadata notes

- Automated DOI metadata record available from Crossref.

## Active citation contexts

- monograph:sections/source-snapshot/mainmatter/05-theoretical-framework.tex:45 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El resultado asíncrono citado supone activación persistente y retardos acotados \parencite{tsitsiklis1986asynchronousOptimization}; una copia que excede esa cota queda fuera de su dominio.
- monograph:sections/source-snapshot/mainmatter/06-results-and-analysis/sp8.tex:73 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: \begin{table}[!htbp] \centering \caption{Métodos y literatura comparada para E8.} \label{tab:sp8-methods} \viutablefont \setlength{\tabcolsep}{1.3pt} \begin{tabularx}{\textwidth}{p{2.0cm} p{1.45cm} p{2.25cm} p{2.0cm} p{1.75cm} Y} \toprule Método/fuente & Clase & Coste & Arquitectura & Parámetros & Garantía/límite \\ \midrule Gradiente asíncrono \parencite{tsitsiklis1986asynchronousOptimization} & Convexo, bajo los supuestos citados & $O(T(c_g+d_i d))$ por agente & Distribuido; valores obsoletos & Paso, retardo, tolerancia & Convergencia convexa.
- thesis:sections/source-snapshot/mainmatter/05-theoretical-framework.tex:45 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: El resultado asíncrono citado supone activación persistente y retardos acotados \parencite{tsitsiklis1986asynchronousOptimization}; una copia que excede esa cota queda fuera de su dominio.

## BibLaTeX entry

```bibtex
@article{tsitsiklis1986asynchronousOptimization,
  author       = {Tsitsiklis, John N. and Bertsekas, Dimitri P. and Athans, Michael},
  title        = {Distributed asynchronous deterministic and stochastic gradient optimization algorithms},
  journaltitle = {IEEE Transactions on Automatic Control},
  date         = {1986},
  volume       = {31},
  number       = {9},
  pages        = {803--812},
  doi          = {10.1109/TAC.1986.1104412},
  url          = {https://doi.org/10.1109/TAC.1986.1104412}
}
```
