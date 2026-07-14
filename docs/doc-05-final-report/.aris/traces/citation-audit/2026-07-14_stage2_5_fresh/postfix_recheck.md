# Revalidación independiente posterior a correcciones

**Fecha:** 2026-07-14  
**Veredicto global:** **PASS**  
**Alcance:** 13 entradas modificadas de `references.bib` y los dos contextos modificados de `sections/mainmatter/01-introduction.tex` (líneas 7 y 18 en la instantánea auditada).  
**Restricción observada:** no se modificaron ni la bibliografía ni el manuscrito.

## Instantánea revalidada

- `references.bib` — SHA-256 `2788B3F3AE69066F5967E460060A1BAFBFDFBA533E40EC6B2443CCACA0529095`
- `sections/mainmatter/01-introduction.tex` — SHA-256 `48AAA4C6B738CE0AEC62963B6BBEAE0414D947E84E956AAD012C1BBB81C68D9B`

La comprobación se hizo de nuevo sobre las entradas y frases actuales, contrastando autores, título, fecha, contenedor, paginación, DOI o URL con la fuente primaria, la página oficial del editor o la página oficial del proveedor. No se asumió que una corrección era válida por haber sido propuesta en la auditoría anterior.

## Resultado por entrada

| Clave | Fuente reabierta | Comprobación posterior a la corrección | Resultado |
|---|---|---|---|
| `agilox2026` | [AGILOX, página oficial](https://www.agilox.net/en/) | Autor corporativo, título y URL coinciden. La página no ofrece fecha de publicación estable; omitir `year` y conservar `urldate` es correcto. | PASS |
| `aziz2021complexity` | [PDF oficial AAMAS 2021](https://aamas.csc.liv.ac.uk/Proceedings/aamas2021/pdfs/p133.pdf) · [registro institucional](https://ira.lib.polyu.edu.hk/handle/10397/105485) | Los seis autores, título, AAMAS 2021, páginas 133–141, editor y DOI `10.5555/3463952.3463974` coinciden. | PASS |
| `bostonStretch2026` | [Boston Dynamics, página oficial de Stretch](https://bostondynamics.com/products/stretch/) | Autor corporativo, producto, título y URL coinciden. La página es no fechada; la retirada de `year` evita atribuirle un año editorial no demostrado. | PASS |
| `dinh2026bsplines` | [SSRN 5276334](https://ssrn.com/abstract=5276334) · [DOI](https://doi.org/10.2139/ssrn.5276334) | La fuente confirma `Cong Khanh Dinh`, el resto de autores, el título y la fecha de depósito de 2025. La corrección de nombre y la eliminación de una nota de publicación no sustentada son correctas. | PASS |
| `dorigo2021swarm` | [DOI IEEE](https://doi.org/10.1109/JPROC.2021.3072740) | Autores, título completo —incluido `[Point of View]`—, *Proceedings of the IEEE* 109(7), 1152–1165 y año 2021 coinciden. | PASS |
| `fisher1978submodular` | [capítulo oficial de Springer](https://link.springer.com/chapter/10.1007/BFb0121195) | Coinciden autores, título, libro *Polyhedral Combinatorics*, editores, serie/volumen, páginas 73–87, año y DOI. | PASS |
| `huang2006large` | [DOI](https://doi.org/10.4310/CIS.2006.v6.n3.a5) · [registro institucional GERAD](https://www.gerad.ca/en/papers/G-2006-57) | Autores, título, *Communications in Information and Systems* 6(3), 221–252, año 2006 y DOI coinciden. | PASS |
| `interact2026mobileRobots` | [publicación oficial de Interact Analysis](https://interactanalysis.com/mobile-robots-market-outpaces-fixed-automation/) · [PDF oficial](https://interactanalysis.com/wp-content/uploads/January-2026-Mobile-Robots-Report.pdf) | La página atribuye la pieza a Theresa Haworth y el comunicado fecha el contenido el 9 de enero de 2026; título, organización y URL coinciden. | PASS |
| `locusRobotics2026` | [Locus Robotics, sitio oficial](https://locusrobotics.com/) | Autor corporativo, título de la página y URL coinciden. Al no existir fecha editorial estable, son correctos la omisión de `year` y el uso de `urldate`. | PASS |
| `mirRobots2026` | [Mobile Industrial Robots, productos oficiales](https://mobile-industrial-robots.com/products) | Autor corporativo, título y URL coinciden. La página no muestra una fecha editorial estable; la entrada ya no inventa un año de publicación. | PASS |
| `mordor2026warehouseAutomation` | [informe oficial de Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/warehouse-automation-market) | La página identifica el informe como *Warehouse Automation Market Size and Share* y declara “Page last updated” el 26 de febrero de 2026; autor corporativo, fecha y URL coinciden. | PASS |
| `omronRobotics2026` | [OMRON Robotics, LD Series](https://robotics.omron.com/products/mobile-robots/ld-series/) | Autor corporativo, título y URL coinciden. La página de producto no presenta fecha editorial estable; omitir `year` es correcto. | PASS |
| `villani2009optimal` | [libro oficial de Springer](https://link.springer.com/book/10.1007/978-3-540-71050-9) | Springer confirma Cédric Villani, *Optimal Transport: Old and New*, 2009, la serie *Grundlehren der mathematischen Wissenschaften*, volumen 338 y el DOI. | PASS |

**Balance bibliográfico:** 13/13 `PASS`; 0 discrepancias de existencia, atribución, fecha, título, contenedor o identificador persistente.

## Revalidación de los contextos modificados

### Línea 7 — coalición temporal con capacidad conjunta adaptada a la carga

**Contexto auditado:** la afirmación presenta el transporte cooperativo como alternativa en la que varios robots forman una coalición específica para cubrir conjuntamente una carga.

**Dictamen:** **SUPPORTS**.

- [Tuci et al. (2018)](https://doi.org/10.3389/frobt.2018.00059) y [An et al. (2023)](https://doi.org/10.1109/OJCS.2023.3238324) documentan el transporte cooperativo de objetos por sistemas multirrobot y sus configuraciones de cooperación.
- [Dutta et al. (2021)](https://digitalcommons.unf.edu/unf_faculty_publications/1161/) formula la asignación de robots heterogéneos a tareas mediante coaliciones cuando las capacidades individuales son insuficientes.
- [Zhang et al. (2024)](https://doi.org/10.1109/IROS58592.2024.10801429) formula expresamente la asignación bajo restricciones de recursos como un juego de formación de coaliciones, con tareas que requieren la agregación de recursos de varios robots.

Las cuatro referencias respaldan directamente los dos componentes materiales de la frase: formación de equipos por tarea y agregación de capacidades/recursos. La sustitución de `farivarnejad2022multirobot` por fuentes de formación de coaliciones elimina la debilidad contextual anterior.

### Línea 18 — control cooperativo con coalición o contacto predefinidos

**Contexto auditado:** la frase sostiene que una parte frecuente de la literatura de formaciones, seguimiento y manipulación parte de un equipo o una configuración de contacto ya fijados.

**Dictamen:** **SUPPORTS**.

La [revisión completa de Tuci et al. (2018)](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2018.00059/full) aporta evidencia explícita: al sintetizar las estrategias de agarre, señala que la mayoría de los trabajos revisados emplea grupos ya acoplados al objeto y posicionados antes del transporte. Además, describe controladores que reciben el número total de robots, conexiones fijas, restricciones de formación y trayectorias predefinidas. Por tanto, la afirmación actual es una generalización fiel y prudente de la revisión, no una inferencia externa sin respaldo.

La retirada de `farivarnejad2022multirobot` deja una referencia que sí documenta de forma directa el supuesto señalado.

## Residuales

- **Ningún residual bibliográfico o contextual bloqueante.**
- Observación no bloqueante: la clave interna `dinh2026bsplines` conserva “2026” aunque el campo bibliográfico correcto es `year = {2025}`. La clave BibTeX no se muestra al lector ni altera la referencia renderizada; no constituye una discrepancia con la fuente, pero podría renombrarse en una futura normalización global de claves si se desea consistencia interna.
- Las páginas corporativas no fechadas son contenido mutable. El `urldate` ya preserva la fecha de consulta y la omisión de un año editorial no verificable es la representación más rigurosa disponible.

## Cierre

**PASS:** las 13 correcciones coinciden con las fuentes primarias u oficiales reabiertas y los dos contextos actuales alcanzan `SUPPORTS`. No quedan errores que requieran una nueva modificación del manuscrito o de `references.bib` dentro de este alcance.

---

## Adenda de frescura: matriz de originalidad incorporada posteriormente

**Generada:** 2026-07-14T12:44:54.910Z  
**Alcance nuevo:** todos los pares cita–contexto de la matriz añadida en `sections/mainmatter/05-theoretical-framework/index.tex`, líneas 453 y 462–464 de la instantánea auditada.  
**Dictamen de esta extensión:** **WARN — 13 `SUPPORTS`, 1 `WEAK`, 0 `WRONG`**.  
**Dictamen combinado vigente:** el `PASS` anterior se conserva para su alcance original —13 correcciones bibliográficas y dos contextos de la introducción—, pero el alcance ampliado del informe queda en **WARN** hasta resolver el único uso `WEAK` de A1.

### Hashes y control de frescura

- `references.bib` — SHA-256 `2788B3F3AE69066F5967E460060A1BAFBFDFBA533E40EC6B2443CCACA0529095`
- `sections/mainmatter/05-theoretical-framework/index.tex` — SHA-256 `96F44DAC02DA61AEA746C40BD2A570E25AE4D844A3C5F87EBA5ADBACBACD9093`

Las citas se extrajeron de la versión identificada por estos hashes. Cada uso se revisó desde cero el 14 de julio de 2026 contra el artículo, preprint o registro editorial primario; no se reutilizó como prueba el dictamen del bloque anterior. Los hashes se recalcularon inmediatamente antes de emitir esta adenda.

### Clasificación de cada uso nuevo

| Línea | Clave | Componente material respaldado por la fuente primaria | Dictamen |
|---:|---|---|---|
| 453 | `quijano2017population` | Presenta los juegos poblacionales y las dinámicas evolutivas como herramientas para sistemas de control distribuido. | SUPPORTS |
| 453 | `barreiro2017distributed` | Formula dinámicas poblacionales con información parcial sobre grafos no completos, prueba conservación de masa y convergencia a Nash y las aplica a optimización y control. | SUPPORTS |
| 453 | `martinez2020formation` | Propone dinámica poblacional distribuida en tiempo discreto para control de formación multirrobot. | SUPPORTS |
| 453 | `martinezpiazuelo2022tcss` | Desarrolla el análisis en tiempo discreto de dinámicas poblacionales distribuidas para optimización y control. | SUPPORTS |
| 453 | `martinezpiazuelo2022automatica` | Busca equilibrios de Nash generalizados en juegos poblacionales bajo restricciones explícitas de capacidad y migración. | SUPPORTS |
| 462 | `quijano2017population` | Sustenta el uso de masas poblacionales sobre estrategias como representación continua y su empleo en control distribuido. | SUPPORTS |
| 462 | `tuci2018cooperative` | Sustenta de forma directa el transporte cooperativo por grupos multirrobot, sus estrategias físicas y su coordinación. Sin embargo, no establece por sí solo el antecedente formal de MRTA ni un mecanismo de formación de coaliciones, también incluidos en la misma celda A1. | **WEAK** |
| 463 | `barreiro2017distributed` | Sustenta dinámicas poblacionales distribuidas y búsqueda de Nash con información local/parcial. | SUPPORTS |
| 463 | `martinez2020formation` | Sustenta la rama discreta y distribuida aplicada a formación de robots. | SUPPORTS |
| 463 | `martinezpiazuelo2022tcss` | Sustenta dinámica discreta distribuida, optimización/control y aplicación multirrobot. | SUPPORTS |
| 463 | `martinezpiazuelo2022automatica` | Sustenta conjuntamente capacidad, migración y búsqueda de Nash. | SUPPORTS |
| 464 | `paul2023collective` | Integra MRTA y transporte colectivo con cargas de trabajo, plazos y restricciones de alcance, comunicación y carga útil. | SUPPORTS |
| 464 | `brown2025assembly` | Propone una pila integrada con asignación de robots y subequipos, configuraciones de transporte colaborativo, planificación espacial y control distribuido anticolisión. | SUPPORTS |
| 464 | `zhou2026cttapf` | Formaliza CT-TAPF integrando formación de equipos, asignación de tareas y búsqueda de caminos sin colisiones. | SUPPORTS |

### Fuentes primarias o canónicas reabiertas

- `quijano2017population`: [repositorio institucional UPCommons](https://upcommons.upc.edu/entities/publication/347e912e-d763-4db7-a45b-f7fc1434ae08) y [DOI IEEE](https://doi.org/10.1109/MCS.2016.2621479).
- `barreiro2017distributed`: [manuscrito institucional](https://upcommons.upc.edu/bitstream/handle/2117/104264/1716-Distributed-Population-Dynamics_-Optimization-and-Control-Applications.pdf) y [DOI IEEE](https://doi.org/10.1109/TSMC.2016.2523934).
- `martinez2020formation`: [registro editorial ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2405896320314191) y [preprint oficial IFAC](https://ifatwww.et.uni-magdeburg.de/ifac2020/media/pdfs/0698.pdf).
- `martinezpiazuelo2022tcss`: [DOI IEEE](https://doi.org/10.1109/TSMC.2022.3151042).
- `martinezpiazuelo2022automatica`: [registro editorial ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0005109822001315) y [registro institucional IRI](https://www.iri.upc.edu/publications/show/2594).
- `tuci2018cooperative`: [artículo completo de Frontiers](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2018.00059/full).
- `paul2023collective`: [preprint de los autores en arXiv](https://arxiv.org/abs/2303.08933), [registro institucional SUNY](https://researchconnect.suny.edu/en/publications/efficient-planning-of-multi-robot-collective-transport-using-grap/) y [DOI IEEE](https://doi.org/10.1109/ICRA48891.2023.10161517).
- `brown2025assembly`: [artículo editorial de Elsevier](https://www.sciencedirect.com/science/article/pii/S0921889025002763) y [preprint de los autores](https://arxiv.org/abs/2311.00192).
- `zhou2026cttapf`: [preprint primario de arXiv 2605.16097](https://arxiv.org/abs/2605.16097).

### Residual y resolución sugerida

El único residual está en A1, línea 462. `tuci2018cooperative` es una fuente sólida para “transporte cooperativo”, pero el rótulo compuesto también afirma antecedentes de “MRTA” y “coaliciones”. Para convertir el uso en `SUPPORTS` pleno basta con separar explícitamente qué fuente respalda cada componente o acompañar Tuci con referencias específicas ya presentes en la bibliografía, por ejemplo una taxonomía MRTA (`gerkey2004formal` o `korsah2013taxonomy`) y un trabajo de formación de coaliciones (`dutta2021hedonic` o `zhang2024coalition`). Esta auditoría no aplicó ese cambio.

### Revalidación poscorrección de A1

**Generada:** 2026-07-14T12:47:17.470Z  
**Línea revalidada:** 462  
**Hash vigente de `sections/mainmatter/05-theoretical-framework/index.tex`:** SHA-256 `2A0EB03DFF9EAB113FAAD82EC13CCA564DCC6E109FCE82BC1FEFAE9902DA510B`  
**Hash vigente de `references.bib`:** SHA-256 `2788B3F3AE69066F5967E460060A1BAFBFDFBA533E40EC6B2443CCACA0529095`

La celda corregida separa ahora cuatro afirmaciones y coloca las fuentes inmediatamente después del componente correspondiente:

| Componente actual de A1 | Fuentes | Revalidación independiente | Dictamen |
|---|---|---|---|
| Taxonomías MRTA | `gerkey2004formal`, `korsah2013taxonomy` | Ambos artículos formulan expresamente taxonomías de asignación de tareas multirrobot; Korsah et al. amplían la taxonomía previa para utilidades y restricciones interrelacionadas. | SUPPORTS |
| Formación de coaliciones | `dutta2021hedonic`, `zhang2024coalition` | Dutta et al. formulan formación distribuida de coaliciones hedónicas para MRTA; Zhang et al. formulan un juego de formación de coaliciones para MRTA heterogénea con restricciones de recursos. | SUPPORTS |
| Transporte cooperativo | `tuci2018cooperative` | La revisión estudia explícitamente transporte cooperativo de objetos por sistemas multirrobot, incluyendo estrategias de empuje, agarre y caging. | SUPPORTS |
| Juegos poblacionales como representación continua | `quijano2017population` | El artículo representa decisiones mediante masas de población distribuidas entre estrategias y desarrolla sus dinámicas para control distribuido. | SUPPORTS |

**Balance de la línea:** 7/7 citas `SUPPORTS`; 0 `WEAK`; 0 `WRONG`.

La separación semántica elimina el residual anterior: Tuci ya no se utiliza para sostener MRTA o formación formal de coaliciones. Los hashes se recalcularon después de leer la corrección y antes de emitir este cierre.

**CIERRE POSCORRECCIÓN: PASS.** Esta comprobación sustituye el `WARN` de la adenda anterior. El alcance ampliado completo queda en **PASS**, sin residuales contextuales en la matriz de originalidad auditada.
