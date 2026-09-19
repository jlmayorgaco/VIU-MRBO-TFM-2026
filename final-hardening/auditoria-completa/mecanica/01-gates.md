# Gates mecanicos — 2026-09-19 12:12

## Compilacion
```
errores LaTeX        0
referencias indef.   0
etiquetas duplicadas 0
overfull hbox        8
underfull            40
avisos biber         0
```

## Conformidad VIU
```
  p.2     Resumen                                          1 pag.
  p.3     Abstract                                        10 pag.
  p.13    Nomenclatura                                     0 pag.
  p.23    2 Objetivos                                      2 pag.
  p.80    7 Conclusiones y recomendaciones                 7 pag.
  p.98    A Reproducibilidad y disponibilidad              0 pag.
  p.98    B Demostraciones seleccionadas de SP1            1 pag.
  p.99    C Demostraciones seleccionadas de SP2            3 pag.
  p.104   E Demostraciones seleccionadas de SP3            1 pag.
  p.112   G Detalle completo de SP1                        7 pag.
  p.119   H Detalle completo de SP2                       15 pag.
  p.134   I Detalle completo de SP3                        6 pag.
[  ok  ] Tamano de pagina                 A4 vertical (595 x 842 pt)
[  ok  ] Paginas totales                  146
[  ok  ] Arial incrustada                 Arial-BoldItalicMT, Arial-BoldMT, Arial-ItalicMT, ArialMT
[  ok  ] Sustitucion de fuente            ninguna fuente sustituta detectada
[  ok  ] Resumen 200-300 palabras         280 palabras
[  ok  ] Encabezado con el estudiante     'Jorge Luis Mayorga Taborda' aparece en el encabezado
[  ok  ] Capitulos detectados             22
[  ok  ] Preliminares                     16 paginas (fuera del computo del cuerpo)
[  ok  ] Cuerpo 50-80 paginas             69 paginas
[ FALLO] Anexos <= 20 paginas             49 paginas
[ FALLO] Resultados >= 50 % del cuerpo    29 de 69 paginas (42 %)
Binary file (standard input) matches
```

## Margenes
```
Paginas que invaden margen (tolerancia 0.10 cm):
  p.1    izq -0.00, der -0.00, sup -0.00, inf 0.00
  p.19   sup 2.12
  p.44   izq 2.26, der 2.26
  p.55   der 2.87
  p.64   der 2.86
  p.73   der 2.89
  p.106  izq 2.89, der 2.89
  p.109  izq 2.88, der 2.88
  p.126  inf 2.38
9 pagina(s).
```

## Trazabilidad de cifras
```
Macros en cierre activo de main-v2.tex: 17
  trazables      : 15
  sin bundle     : 2 (derivadas, no de campana numerica)
  SIN REGISTRAR  : 0
  ausentes       : 0
  DIVERGENTES    : 0

Generador por familia trazable:
  aws-industrial2-results    <- scripts/export_aws_industrial2_latex.py
  cargo_e2e_numbers          <- viu-run-cargo-e2e
  cargo_e2e_results          <- viu-run-cargo-e2e
  literature-coverage        <- pre-thesis/scripts/build_review_figure_data.py
  sp2_ablation               <- viu-run-sp2
  sp2_comparison             <- viu-run-sp2
  sp2_numbers                <- viu-run-sp2 (experiments/configs/sp2_effective_capacity.yaml)
  sp3_numbers                <- viu-run-sp3-evidence (experiments/configs/sp3_wrench_evidence.yaml)
  sp4_docking_results        <- viu-run-sp4-evidence
  sp4_numbers                <- viu-run-sp4-evidence (experiments/configs/sp4_transport_evidence.yaml)
  sp4_transport_results      <- viu-run-sp4-evidence
  sp6_numbers                <- viu-run-sp6
  sp6_results                <- viu-run-sp6
  sp7_numbers                <- viu-run-sp7 (experiments/configs/sp7_traffic_confirmatory.yaml)
  sp7_results                <- viu-run-sp7

Sin bundle de campana (aceptado, se declara su generador):
  lit-bibliometric           <- pre-thesis/scripts/build_review_figure_data.py (sin bundle de campana: derivado del corpus de revision)
  lit-corpus-activity        <- pre-thesis/scripts/build_review_figure_data.py (sin bundle de campana: derivado del corpus de revision)

OK: toda cifra activa es trazable a su campana.
```

## Censo de resultados formales
```
  Resuelve la lista real de \input de main-v2.tex (recursivamente) y reporta:
Ficheros .tex activos: 89

=== RESULTADOS FORMALES: 29 ===
  sp1-wrench-condensed.tex           proposicion  Residual puro frente a reparto regularizado  prop:pre-sp1-wrench-residual
  sp2-compact.tex                    proposicion  Potencial exacto y equilibrio variacional de prop:sp2-compact-e4-potential
  sp2-compact.tex                    proposicion  Ineficiencia no acotada del peor Nash        prop:sp2-compact-e6-unbounded-poa
  sp3-compact.tex                    teorema      Potencial exacto y propiedad de mejora finit thm:sp3-compact-e7-potential
  sp3-compact.tex                    proposicion  Nash sin conflictos bajo accesibilidad       prop:sp3-compact-e7-conflict-free
  megajuego-compact.tex              proposicion  Potencial exacto por factores                prop:megajuego-exact-potential
  sp2-canonical-bridge.tex           proposicion  Monotonicidades opuestas                     prop:pre-sp2-opposite-monotonicity
  sp2-canonical-bridge.tex           proposicion  Insuficiencia de la capacidad escalar        prop:pre-sp2-scalar-insufficiency
  sp2-e4-trimmed.tex                 proposicion  Potencial exacto y equilibrio variacional de prop:sp4-potential
  sp2-e6-trimmed.tex                 proposicion  ineficiencia no acotada del peor Nash        prop:sp6-unbounded-poa
  sp3-e7-trimmed.tex                 teorema      potencial exacto y propiedad de mejora finit thm:sp7-exact-potential
  sp3-e7-trimmed.tex                 proposicion  Nash sin conflictos bajo accesibilidad       prop:sp7-conflict-free

=== ECUACIONES ETIQUETADAS: 50 | SIN CITAR: 0 ===

=== LABELS DUPLICADAS: 0 ===
Binary file (standard input) matches
```
