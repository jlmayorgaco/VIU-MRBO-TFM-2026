# Auditoria de prosa â€” patrones de escritura asistida

Criterio: guidelines/07 y skill ai-burstiness. Medido sobre el cierre activo.

```
lmscan disponible: puntuacion estadistica por parrafo activada.

fichero                                       parr frases     sd hallazgos de fichero
--------------------------------------------------------------------------------------------------------
01-introduction.tex                              9    40    7.0 sd de longitud de frase 7.0 (min 8); ninguna frase p
05-theoretical-framework.tex                    37   132    5.9 sd de longitud de frase 5.9 (min 8); ninguna frase p
thesis-results-v2.tex                            5    13    5.9 sd de longitud de frase 5.9 (min 8); ninguna frase p
sp2-e4-trimmed.tex                              18    49    7.4 sd de longitud de frase 7.4 (min 8); ninguna frase p
sp3-e7-trimmed.tex                              14    37    6.5 sd de longitud de frase 6.5 (min 8); ninguna frase p
aws-industrial2.tex                              3    14    7.0 sd de longitud de frase 7.0 (min 8); ninguna frase p
02-abstract-v2.tex                               4    15    8.9 ninguna frase por encima de 35 palabras
03-hypotheses.tex                                7    18    8.2 ninguna frase por encima de 35 palabras
04-methodology.tex                              21    80    6.2 sd de longitud de frase 6.2 (min 8)
sp1-compact.tex                                  4    11    8.1 ninguna frase por encima de 35 palabras
thesis-appendices.tex                            6    26    7.1 sd de longitud de frase 7.1 (min 8)
sp1-e2-trimmed.tex                              21    58    7.0 sd de longitud de frase 7.0 (min 8)
sp2-e6-trimmed.tex                              14    34    7.9 sd de longitud de frase 7.9 (min 8)
01-summary-v2.tex                                4    14    9.6 -
review-compact.tex                               4    12   19.4 -
results-interface.tex                            6    15   10.7 -
results-review.tex                               7    11   13.1 -
megajuego-compact.tex                            7    11   17.8 -
07-conclusions.tex                              12    45    8.2 -
conclusions-megajuego-addendum.tex               8    23   18.9 -
04-sp2-proofs.tex                                4    10   13.0 -
06-sp4-proofs.tex                                7    26   14.5 -
08-sp7-proofs.tex                                6    18    9.4 -
appendix-review-full-detail.tex                 19    59   14.2 -
cargo-e2e-v2.tex                                14    51   10.8 -
appendix-megajuego-detail.tex                   13    52   14.5 -


PARRAFOS A REESCRIBIR PRIMERO (174 con hallazgos)
========================================================================================================

megajuego-compact.tex  parrafo 5 (58 palabras)  lmscan 15%
  «Los cuatro resultados anteriores se demuestran en escenarios concretos y acotados --- dos …»
    [condicionado ] «optimo» x1 — solo con el problema de optimizacion declarado
    [VIU          ] 1 oraciones: el minimo VIU es 3

thesis-appendices.tex  parrafo 1 (69 palabras)  lmscan 11%
  «Los estimandos y resultados principales de la memoria se enlazan con tablas o macros gener…»
    [regla de tres] 2 enumeraciones ternarias
    [ritmo        ] frases de longitud casi igual (sd=2.2)

sp2-e6-trimmed.tex  parrafo 6 (33 palabras)  lmscan 11%
  «La construcción del Anexo usa un soporte de coste NUM y dos complementarios de coste total…»
    [condicionado ] «optimo» x1 — solo con el problema de optimizacion declarado
    [VIU          ] 2 oraciones: el minimo VIU es 3

sp3-e7-trimmed.tex  parrafo 3 (40 palabras)  lmscan 10%
  «El programa de está sujeto a exclusión de vértice, arista, zona y NUM . Con NUM , la enume…»
    [condicionado ] «optimo» x1 — solo con el problema de optimizacion declarado
    [ritmo        ] frases de longitud casi igual (sd=1.7)

appendix-review-full-detail.tex  parrafo 7 (55 palabras)  lmscan 10%
  «El primer frente resuelve la coalición lógica mediante emparejamientos uno a muchos, subas…»
    [regla de tres] 2 enumeraciones ternarias
    [VIU          ] 2 oraciones: el minimo VIU es 3

cargo-e2e-v2.tex  parrafo 10 (38 palabras)  lmscan 9%
  «Se miden éxito, intersección, tiempo, recuperación, error, wrench , saturación, energía, t…»
    [regla de tres] 2 enumeraciones ternarias
    [ritmo        ] frases de longitud casi igual (sd=2.6)

conclusions-megajuego-addendum.tex  parrafo 6 (87 palabras)  lmscan 7%
  «En lo económico, la decisión relevante no es el coste de la flota frente al de un manipula…»
    [estructura   ] paralelismo negativo: «no es el coste de la flota frente al de un manip…»
    [VIU          ] 2 oraciones: el minimo VIU es 3

01-introduction.tex  parrafo 7 (119 palabras)  lmscan 7%
  «Los experimentos siguen SP1--SP3. El primero pasa de asignación unitaria a cuotas y servic…»
    [regla de tres] 3 enumeraciones ternarias
    [ritmo        ] frases de longitud casi igual (sd=4.9)

07-conclusions.tex  parrafo 12 (96 palabras)  lmscan 6%
  «Primero deben sustituirse las reglas empíricas de Cargo por los mecanismos de SP1--SP2 que…»
    [regla de tres] 4 enumeraciones ternarias
    [ritmo        ] frases de longitud casi igual (sd=5.0)

results-review.tex  parrafo 6 (47 palabras)  lmscan 5%
  «El corpus patentario se desplaza hacia decisión de misión: media móvil de tres años del 37…»
    [condicionado ] «robusto» x1 — solo con definicion formal de robustez
    [VIU          ] 1 oraciones: el minimo VIU es 3

08-sp7-proofs.tex  parrafo 3 (83 palabras)  lmscan 1%
  «Si NUM y NUM , la definición proporciona una desviación con NUM y NUM , donde NUM . Para \…»
Traceback (most recent call last):
  File "C:\Users\walla\Documents\Github\VIU-MRBO-TFM-2026\.claude\skills\ai-burstiness\scripts\prose_audit.py", line 321, in <module>
    sys.exit(main())
             ~~~~^^
  File "C:\Users\walla\Documents\Github\VIU-MRBO-TFM-2026\.claude\skills\ai-burstiness\scripts\prose_audit.py", line 302, in main
    print("    [%-13s] %s" % (k, m))
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 40: character maps to <undefined>
```
