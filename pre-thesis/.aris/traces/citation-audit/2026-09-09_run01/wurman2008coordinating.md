# Citation audit trace: wurman2008coordinating

- Action: KEEP
- Existence: VERIFIED
- Metadata: VERIFIED
- Context: SUPPORTED
- Source type: manual_primary
- Documents: thesis
- Citation contexts: 1 (0 nocite)

## Sources checked

- https://api.crossref.org/works/10.1609%2Faimag.v29i1.2082
- https://doi.org/10.1609/aimag.v29i1.2082
- https://ojs.aaai.org/aimagazine/index.php/aimagazine/article/view/2082

## Source note

AAAI/OJS article page verifies title, authors, DOI, publication date 2008-03-20, AI Magazine 29(1), and warehouse/Kiva context.

## Metadata notes

- Crossref API did not return this DOI in the automated lookup, but the AAAI/OJS primary page verifies the bibliographic identity. Page range is retained as supplied in the BibLaTeX entry; the OJS citation page records the article start page as 9.

## Active citation contexts

- thesis:sections/source-snapshot/mainmatter/01-introduction.tex:8 `parencite` -> SUPPORTS (claim). Context is consistent with the verified title/abstract/metadata and the local claim scope.
  - Context: En almacenes, Kiva documentó la coordinación de flotas para mover estanterías \parencite{wurman2008coordinating}; Geek+ y MiR ofrecen soluciones comerciales para preparación de pedidos y transporte interno \parencite{geekplusWarehouseSolutions,mirInternalTransport}.

## BibLaTeX entry

```bibtex
@article{wurman2008coordinating,
  author       = {Wurman, Peter R. and D'Andrea, Raffaello and Mountz, Mick},
  title        = {Coordinating Hundreds of Cooperative, Autonomous Vehicles in Warehouses},
  journaltitle = {AI Magazine},
  date         = {2008},
  volume       = {29},
  number       = {1},
  pages        = {9--19},
  doi          = {10.1609/aimag.v29i1.2082},
  url          = {https://doi.org/10.1609/aimag.v29i1.2082}
}
```
