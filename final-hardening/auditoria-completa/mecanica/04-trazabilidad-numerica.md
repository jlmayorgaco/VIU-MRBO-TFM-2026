# Trazabilidad numerica del cuerpo activo

Regla del proyecto: la prosa no contiene cifras a mano. Toda cifra de
resultado debe venir de `shared/generated-macros/`.

Excluidos del recuento: comentarios, ecuaciones, `tikzpicture`, algoritmos,
matematica en linea, anos y enteros de una o dos cifras (indices y
cardinalidades).

| categoria | n |
|---|---:|
| literales decimales en prosa o tablas | 893 |
| literales que coinciden con el valor de alguna macro | 248 |
| ficheros activos revisados | 89 |

Un literal que **coincide** con el valor de una macro es sospechoso: la
cifra correcta esta disponible como macro y aun asi se escribio a mano, de
modo que una regeneracion de campana no la actualizaria.

## Literales que duplican el valor de una macro

| fichero | linea | valor | macro disponible | contexto |
|---|---:|---:|---|---|
| `sections/source-snapshot/mainmatter/01-introduction.tex` | 4 | 900 | `SPEightWorlds` | La IFR registró 102\,900 robots de servicio para tr |
| `sections/v2/appendix-sp2-detail.tex` | 46 | 120 | `SPSixIrrecoverableWorlds` | El método directo agota el horizonte de 120~s sin llegar |
| `sections/v2/coppelia-compact.tex` | 11 | 108 | `SPFourDockWorlds`, `SPFiveWorlds` | las 108 instancias que la tabla re |
| `sections/v2/sp2-compact.tex` | 126 | 480 | `SPSixWorlds` | tion{Resultados agregados de E6-C sobre 480 mundos pareados  |
| `sections/v2/sp3-compact.tex` | 71 | 360 | `CargoEtwoEWorlds`, `SPSixRecoverableWorlds` | tion[Resultados agregados de E7-C sobre 360 mundos pareados  |
| `sections/v2/support/sp1-e2-trimmed.tex` | 106 | 1560 | `SPTwoWorlds` | \caption[E2 en 1560 mundos pareados. Diferenc |
| `sections/v2/support/sp2-e6-trimmed.tex` | 112 | 480 | `SPSixWorlds` | En los 480 mundos, todo método que in |
| `sections/v2/support/sp2-e6-trimmed.tex` | 116 | 480 | `SPSixWorlds` | tion{Resultados agregados de E6-C sobre 480 mundos pareados  |
| `sections/v2/support/sp2-e6-trimmed.tex` | 136 | 480 | `SPSixWorlds` | ina en un número finito de cambios. Las 480 instancias respe |
| `sections/v2/support/sp3-e7-trimmed.tex` | 109 | 360 | `CargoEtwoEWorlds`, `SPSixRecoverableWorlds` | tion[Resultados agregados de E7-C sobre 360 mundos pareados  |
| `sections/v2/thesis-results-v2.tex` | 103 | 600 | `SPThreeWorlds` | positivos, cobertura y abstención sobre 600 instancias. & Cu |
| `shared/generated-macros/aws-industrial2-results.tex` | 8 | 0.00 | `AwsOpenCentralDeliveries` | \newcommand{\AwsOpenCentralDeliveries}{0.00} |
| `shared/generated-macros/aws-industrial2-results.tex` | 9 | 1.00 | `AwsOpenAuctionDeliveries`, `AwsOpenPredictiveDeliveries` | \newcommand{\AwsOpenAuctionDeliveries}{1.00} |
| `shared/generated-macros/aws-industrial2-results.tex` | 10 | 1.00 | `AwsOpenAuctionDeliveries`, `AwsOpenPredictiveDeliveries` | ewcommand{\AwsOpenPredictiveDeliveries}{1.00} |
| `shared/generated-macros/aws-industrial2-results.tex` | 11 | 1.00 | `AwsOpenAuctionDeliveries`, `AwsOpenPredictiveDeliveries` | \newcommand{\AwsOpenTfmDeliveries}{1.00} |
| `shared/generated-macros/aws-industrial2-results.tex` | 12 | 0.008 | `AwsPredictiveDeadlockMin` | \newcommand{\AwsPredictiveDeadlockMin}{0.008} |
| `shared/generated-macros/aws-industrial2-results.tex` | 13 | 0.010 | `AwsPredictiveDeadlockMax` | \newcommand{\AwsPredictiveDeadlockMax}{0.010} |
| `shared/generated-macros/aws-industrial2-results.tex` | 14 | 0.467 | `AwsTfmDeadlockMin` | \newcommand{\AwsTfmDeadlockMin}{0.467} |
| `shared/generated-macros/aws-industrial2-results.tex` | 15 | 0.646 | `AwsTfmDeadlockMax` | \newcommand{\AwsTfmDeadlockMax}{0.646} |
| `shared/generated-macros/aws-industrial2-results.tex` | 16 | 67.62 | `AwsCentralCpuMin` | \newcommand{\AwsCentralCpuMin}{67.62} |
| `shared/generated-macros/aws-industrial2-results.tex` | 17 | 83.01 | `AwsCentralCpuMax` | \newcommand{\AwsCentralCpuMax}{83.01} |
| `shared/generated-macros/aws-industrial2-results.tex` | 18 | 13.63 | `AwsPredictiveCpuMin` | \newcommand{\AwsPredictiveCpuMin}{13.63} |
| `shared/generated-macros/aws-industrial2-results.tex` | 19 | 16.27 | `AwsPredictiveCpuMax` | \newcommand{\AwsPredictiveCpuMax}{16.27} |
| `shared/generated-macros/aws-industrial2-results.tex` | 32 | 1.8 | `AwsSceneSensingRadius` | \newcommand{\AwsSceneSensingRadius}{1.8} |
| `shared/generated-macros/aws-industrial2-results.tex` | 33 | 3.2 | `AwsSceneCommunicationRadius` | ewcommand{\AwsSceneCommunicationRadius}{3.2} |
| `shared/generated-macros/aws-industrial2-results.tex` | 37 | 10.000 | `AwsCFifteenCentral`, `AwsCFifteenGreedy` | \newcommand{\AwsCFifteenCentral}{10.000} |
| `shared/generated-macros/aws-industrial2-results.tex` | 38 | 10.000 | `AwsCFifteenCentral`, `AwsCFifteenGreedy` | \newcommand{\AwsCFifteenGreedy}{10.000} |
| `shared/generated-macros/aws-industrial2-results.tex` | 39 | 9.750 | `AwsCFifteenReplicator` | \newcommand{\AwsCFifteenReplicator}{9.750} |
| `shared/generated-macros/aws-industrial2-results.tex` | 40 | 8.000 | `AwsCFifteenRandom` | \newcommand{\AwsCFifteenRandom}{8.000} |
| `shared/generated-macros/aws-industrial2-results.tex` | 41 | 3.125 | `AwsCSixteenCentral` | \newcommand{\AwsCSixteenCentral}{3.125} |
| `shared/generated-macros/aws-industrial2-results.tex` | 42 | 3.250 | `AwsCSixteenGreedy` | \newcommand{\AwsCSixteenGreedy}{3.250} |
| `shared/generated-macros/aws-industrial2-results.tex` | 43 | 1.375 | `AwsCSixteenReplicator`, `AwsCSeventeenReplicator` | \newcommand{\AwsCSixteenReplicator}{1.375} |
| `shared/generated-macros/aws-industrial2-results.tex` | 44 | 0.500 | `AwsCSixteenRandom`, `SPThreeGuardedAbstention` | \newcommand{\AwsCSixteenRandom}{0.500} |
| `shared/generated-macros/aws-industrial2-results.tex` | 45 | 0.750 | `AwsCSeventeenCentral`, `CargoEtwoENoGuardCollision` | \newcommand{\AwsCSeventeenCentral}{0.750} |
| `shared/generated-macros/aws-industrial2-results.tex` | 46 | 1.250 | `AwsCSeventeenGreedy` | \newcommand{\AwsCSeventeenGreedy}{1.250} |
| `shared/generated-macros/aws-industrial2-results.tex` | 47 | 1.375 | `AwsCSixteenReplicator`, `AwsCSeventeenReplicator` | \newcommand{\AwsCSeventeenReplicator}{1.375} |
| `shared/generated-macros/aws-industrial2-results.tex` | 48 | 0.875 | `AwsCSeventeenRandom` | \newcommand{\AwsCSeventeenRandom}{0.875} |
| `shared/generated-macros/aws-industrial2-results.tex` | 49 | 1.625 | `AwsCEighteenCentral` | \newcommand{\AwsCEighteenCentral}{1.625} |
| `shared/generated-macros/aws-industrial2-results.tex` | 50 | 2.000 | `AwsCEighteenGreedy` | \newcommand{\AwsCEighteenGreedy}{2.000} |
| `shared/generated-macros/aws-industrial2-results.tex` | 51 | 1.875 | `AwsCEighteenReplicator` | \newcommand{\AwsCEighteenReplicator}{1.875} |
| `shared/generated-macros/aws-industrial2-results.tex` | 52 | 1.375 | `AwsCSixteenReplicator`, `AwsCSeventeenReplicator` | \newcommand{\AwsCEighteenRandom}{1.375} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 1 | 360 | `CargoEtwoEWorlds`, `SPSixRecoverableWorlds` | \newcommand{\CargoEtwoEWorlds}{360} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 2 | 2160 | `CargoEtwoERuns` | \newcommand{\CargoEtwoERuns}{2160} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 3 | 0.997 | `CargoEtwoESuccess` | \newcommand{\CargoEtwoESuccess}{0.997} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 4 | 1.000 | `CargoEtwoECentralSuccess`, `CargoEtwoEDegradedSuccess` | \newcommand{\CargoEtwoECentralSuccess}{1.000} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 5 | 0.989 | `CargoEtwoEFailureSuccess`, `CargoEtwoERepairEffect` | \newcommand{\CargoEtwoEFailureSuccess}{0.989} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 6 | 1.000 | `CargoEtwoECentralSuccess`, `CargoEtwoEDegradedSuccess` | \newcommand{\CargoEtwoEDegradedSuccess}{1.000} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 7 | 328.1 | `CargoEtwoEMessages` | \newcommand{\CargoEtwoEMessages}{328.1} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 8 | 249.3 | `CargoEtwoEDegradedMessages` | newcommand{\CargoEtwoEDegradedMessages}{249.3} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 9 | 58.2 | `CargoEtwoEDegradedKilobytes` | ewcommand{\CargoEtwoEDegradedKilobytes}{58.2} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 10 | 0.750 | `AwsCSeventeenCentral`, `CargoEtwoENoGuardCollision` | newcommand{\CargoEtwoENoGuardCollision}{0.750} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 11 | 356 | `CargoEtwoENoGuardCertified` | newcommand{\CargoEtwoENoGuardCertified}{356} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 14 | 0.068 | `CargoEtwoETimingPHolm` | \newcommand{\CargoEtwoETimingPHolm}{0.068} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 15 | 0.996 | `CargoEtwoEGuardEffect` | \newcommand{\CargoEtwoEGuardEffect}{0.996} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 16 | 0.989 | `CargoEtwoEFailureSuccess`, `CargoEtwoERepairEffect` | \newcommand{\CargoEtwoEGuardCI}{[0.989;1.000]} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 16 | 1.000 | `CargoEtwoECentralSuccess`, `CargoEtwoEDegradedSuccess` | \newcommand{\CargoEtwoEGuardCI}{[0.989;1.000]} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 18 | 0.989 | `CargoEtwoEFailureSuccess`, `CargoEtwoERepairEffect` | \newcommand{\CargoEtwoERepairEffect}{0.989} |
| `shared/generated-macros/cargo_e2e_numbers.tex` | 19 | 1.000 | `CargoEtwoECentralSuccess`, `CargoEtwoEDegradedSuccess` | \newcommand{\CargoEtwoERepairCI}{[0.967;1.000]} |
| `shared/generated-macros/cargo_e2e_results.tex` | 5 | 360 | `CargoEtwoEWorlds`, `SPSixRecoverableWorlds` | Híbrido vecinal & 360 & 0{,}997 & 0{,}000 & 37{, |
| `shared/generated-macros/cargo_e2e_results.tex` | 6 | 360 | `CargoEtwoEWorlds`, `SPSixRecoverableWorlds` | Información perfecta & 360 & 0{,}997 & 0{,}000 & 37{, |

## Literales decimales por fichero

| fichero | literales | usos de macro |
|---|---:|---:|
| `shared/generated-macros/lit-corpus-activity.tex` | 401 | 0 |
| `sections/v2/floats/ind-fig-patents.tex` | 44 | 0 |
| `sections/v2/appendix-review-full-detail.tex` | 42 | 1 |
| `sections/v2/sp1-compact.tex` | 28 | 0 |
| `shared/generated-macros/literature-coverage.tex` | 27 | 0 |
| `sections/v2/floats/ind-tab-matrix.tex` | 24 | 0 |
| `figures/protected/01-distributed-coalition-scenario.tex` | 19 | 0 |
| `shared/generated-macros/sp2_comparison.tex` | 19 | 0 |
| `sections/v2/appendix-megajuego-detail.tex` | 18 | 0 |
| `shared/generated-macros/cargo_e2e_results.tex` | 16 | 0 |
| `config/v2-review-palette.tex` | 15 | 0 |
| `sections/v2/megajuego-compact.tex` | 15 | 0 |
| `shared/generated-macros/sp4_docking_results.tex` | 12 | 0 |
| `sections/source-snapshot/mainmatter/05-theoretical-framework.tex` | 11 | 0 |
| `shared/generated-macros/sp7_results.tex` | 11 | 0 |
| `sections/v2/floats/lit-fig-bibliometric.tex` | 10 | 6 |
| `shared/generated-macros/sp3_numbers.tex` | 10 | 0 |
| `sections/v2/floats/lit-fig-stage-coverage.tex` | 9 | 0 |
| `sections/v2/floats/lit-fig-period-shift.tex` | 9 | 0 |
| `shared/generated-macros/sp2_numbers.tex` | 9 | 0 |
| `shared/generated-macros/sp6_results.tex` | 8 | 0 |
| `shared/generated-macros/sp4_transport_results.tex` | 8 | 0 |
| `sections/v2/results-review.tex` | 7 | 1 |
| `sections/v2/floats/ind-tab-standards.tex` | 7 | 0 |
| `sections/v2/sp2-compact.tex` | 6 | 0 |

## Muestra de literales (los 40 primeros)

| fichero | linea | valor | contexto |
|---|---:|---:|---|
| `config/v2-review-palette.tex` | 84 | 5.55 | =white,font=\sffamily\bfseries\fontsize{5.55}{5.75}\selectfont] at (#1 |
| `config/v2-review-palette.tex` | 84 | 5.75 | ,font=\sffamily\bfseries\fontsize{5.55}{5.75}\selectfont] at (#1,#2){# |
| `config/v2-review-palette.tex` | 85 | 5.35 | !black,font=\sffamily\bfseries\fontsize{5.35}{5.60}\selectfont] at ( ) |
| `config/v2-review-palette.tex` | 85 | 5.60 | ,font=\sffamily\bfseries\fontsize{5.35}{5.60}\selectfont] at ( ) {#3\, |
| `config/v2-review-palette.tex` | 85 | 4.68 | extsuperscript{[#6]}\\[-.45mm]\fontsize{4.68}{4.95}\selectfont #4};} |
| `config/v2-review-palette.tex` | 85 | 4.95 | erscript{[#6]}\\[-.45mm]\fontsize{4.68}{4.95}\selectfont #4};} |
| `config/v2-review-palette.tex` | 88 | 5.55 | =white,font=\sffamily\bfseries\fontsize{5.55}{5.75}\selectfont] at (#1 |
| `config/v2-review-palette.tex` | 88 | 5.75 | ,font=\sffamily\bfseries\fontsize{5.55}{5.75}\selectfont] at (#1,#2){# |
| `config/v2-review-palette.tex` | 89 | 5.35 | !black,font=\sffamily\bfseries\fontsize{5.35}{5.60}\selectfont] at ( ) |
| `config/v2-review-palette.tex` | 89 | 5.60 | ,font=\sffamily\bfseries\fontsize{5.35}{5.60}\selectfont] at ( ) {#3\, |
| `config/v2-review-palette.tex` | 89 | 4.68 | extsuperscript{[#6]}\\[-.45mm]\fontsize{4.68}{4.95}\selectfont #4};} |
| `config/v2-review-palette.tex` | 89 | 4.95 | erscript{[#6]}\\[-.45mm]\fontsize{4.68}{4.95}\selectfont #4};} |
| `config/v2-review-palette.tex` | 90 | 0,0 | w[fill=#1,draw=white,line width=.35pt] (0,0) circle (1.75mm);}\,\textc |
| `config/v2-review-palette.tex` | 112 | 5.35 | {\fontsize{5.35}{5.65}\selectfont\color{m |
| `config/v2-review-palette.tex` | 112 | 5.65 | {\fontsize{5.35}{5.65}\selectfont\color{muted}# |
| `figures/protected/01-distributed-coalition-scenario.tex` | 13 | 0.12 | \fill[Cardboard!35] (#3,#3) -- (#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 13 | 0.13 | ll[Cardboard!35] (#3,#3) -- (#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 14 | 0.12 | (#3+0.12,-#3+0.13) -- (#3,-#3) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 14 | 0.13 | (#3+0.12,-#3+0.13) -- (#3,-#3) -- cycle; |
| `figures/protected/01-distributed-coalition-scenario.tex` | 15 | 0.12 | \fill[Cardboard!80] (-#3,#3) -- (-#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 15 | 0.13 | [Cardboard!80] (-#3,#3) -- (-#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 16 | 0.12 | (#3+0.12,#3+0.13) -- (#3,#3) -- cy |
| `figures/protected/01-distributed-coalition-scenario.tex` | 16 | 0.13 | (#3+0.12,#3+0.13) -- (#3,#3) -- cycle; |
| `figures/protected/01-distributed-coalition-scenario.tex` | 20 | 0.12 | (#3,#3) -- (#3+0.12,#3+0.13) |
| `figures/protected/01-distributed-coalition-scenario.tex` | 20 | 0.13 | (#3,#3) -- (#3+0.12,#3+0.13) |
| `figures/protected/01-distributed-coalition-scenario.tex` | 21 | 0.12 | (-#3,#3) -- (-#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 21 | 0.13 | (-#3,#3) -- (-#3+0.12,#3+0.13) -- |
| `figures/protected/01-distributed-coalition-scenario.tex` | 22 | 0.12 | (#3+0.12,#3+0.13) -- (#3,#3); |
| `figures/protected/01-distributed-coalition-scenario.tex` | 22 | 0.13 | (#3+0.12,#3+0.13) -- (#3,#3); |
| `figures/protected/01-distributed-coalition-scenario.tex` | 24 | 3,0 | (0,-#3) -- (0,#3) (-#3,0) -- (#3,0); |
| `figures/protected/01-distributed-coalition-scenario.tex` | 24 | 3,0 | (0,-#3) -- (0,#3) (-#3,0) -- (#3,0); |
| `figures/protected/01-distributed-coalition-scenario.tex` | 35 | 0.5 | \foreach \i in {-0.5,-0.3,...,0.7}{ |
| `figures/protected/01-distributed-coalition-scenario.tex` | 35 | 0.3 | \foreach \i in {-0.5,-0.3,...,0.7}{ |
| `figures/protected/01-distributed-coalition-scenario.tex` | 35 | 0.7 | \foreach \i in {-0.5,-0.3,...,0.7}{ |
| `main-v2.tex` | 40 | 1.18 | \pgfplotsset{compat=1.18} |
| `sections/frontmatter-evidence-key.tex` | 14 | 1.14 | \renewcommand{\arraystretch}{1.14} |
| `sections/results-interface.tex` | 29 | 1.12 | \renewcommand{\arraystretch}{1.12} |
| `sections/results-interface.tex` | 30 | 0.96 | \begin{tabularx}{0.96\textwidth}{>{\raggedright |
| `sections/results-interface.tex` | 63 | 1.10 | \renewcommand{\arraystretch}{1.10} |
| `sections/results-interface.tex` | 64 | 0.96 | \begin{tabularx}{0.96\textwidth}{>{\raggedright |