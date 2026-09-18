# Mapa de consulta del corpus `books`

La raíz física vigente es `material/books/`. Los `unit_id` y hashes se conservan tras la reubicación para mantener la continuidad de las 37 decisiones bibliográficas.

## Alcance y criterio

Esta auditoría registra exactamente los 37 objetos canónicos marcados con `corpus=books` e `is_canonical=yes` en `source-manifest.csv`. Los 37 archivos se comprobaron contra el SHA-256 registrado: no hubo ausencias ni discrepancias. La consulta se limitó a portada, metadatos internos, índice/marcadores y capítulos temáticamente pertinentes; no se copiaron figuras, tablas, demostraciones ni fragmentos para la memoria.

`use-now` significa prioridad de lectura y contraste para la tesis en curso, no autorización automática para citar ni promoción de evidencia. `use-later` reserva una fuente para la monografía, una derivación o una revisión posterior. `out-of-scope` conserva el objeto en el inventario pero impide que la mera coincidencia terminológica amplíe el alcance científico.

Los `claim_ids` indican dónde puede ser útil confrontar definiciones, supuestos o baselines. Ningún libro respalda por sí solo los resultados empíricos propios, y una celda con claim no cambia el estado del claim. Las 37 identidades se verificaron contra registros editoriales, DOI, repositorios o catálogos institucionales: diez están además verificadas en `references/LITERATURE_LEDGER.md`; las otras 27 requieren revisión contextual y alta en el ledger antes de cualquier cita.

## Resultado

| Decisión | Fuentes | Interpretación |
|---|---:|---|
| `use-now` | 10 | Fundamentos o contraste directamente pertinentes al cuerpo actual. |
| `use-later` | 22 | Material útil pero secundario, transferido desde otro dominio o reservado para extensión/monografía. |
| `out-of-scope` | 5 | Desarrollo web, aplicación espacial específica, ensayo político, actas demasiado heterogéneas o juego diferencial fuera del modelo. |
| **Total** | **37** | Cobertura canónica completa y sin duplicados. |

Cobertura temática no exclusiva: SP1 aparece en 12 fuentes, SP2 en 18, SP3 en 11 y el eje transversal en 32. Diez identidades tienen estado `verified-ledger`: las tres verificadas inicialmente y las siete fuentes `use-now` auditadas el 2026-09-08. El 2026-09-09 se cerró la identidad de las otras 27 contra fuentes autorizadas: 26 registros editoriales y un artículo con DOI de revista. Esta verificación de identidad no equivale a revisión del contexto citado ni a alta en el ledger.

## Prioridad inmediata

1. `SRC-e826761b9b60501e`: GNE, juegos poblacionales, disipatividad y multiplicadores distribuidos; ficha Springer de 2026 verificada, sin sustituir la prueba atómica propia.
2. `SRC-8d35243f573f11d9`: transporte cooperativo distribuido, estimación de wrench, admitancia y experimentos; registro institucional verificado y diferencia manipuladores--AMR obligatoria.
3. `SRC-c68ccfd92d3f5d54`, `SRC-bf8f10d20534d125` y `SRC-4ced4ee03f6d46a6`: uniciclo, formación, consenso multivehículo y cinemática móvil.
4. `SRC-d7808bdf107394b0` y `SRC-7df2a947e484a325`: fundamentos ya verificados de redes robóticas y juegos poblacionales.
5. `SRC-0b7ceba994fe5772`: contexto industrial y KPI; nunca como evidencia de fidelidad física.
6. `SRC-097398c064adff1a`: contraste de la extensión no prehensil; no transferir el preprint centralizado a Cargo.
7. `SRC-617a593591cb7e13`: seguimiento promedio y capa de estimación; separar consenso informativo de asignación y mecánica.

## Fuentes activas verificadas en el ledger el 2026-09-08

La verificación se hizo contra fichas de editorial o repositorio institucional, además de la portada y las secciones pertinentes de la unidad local. El estado `verified-ledger` confirma identidad y contexto de uso; no convierte estas fuentes de contexto en evidencia de los resultados propios ni añade citas activas.

| Unidad | Clave del ledger | Registro autorizado | Identidad resuelta y contexto permitido |
|---|---|---|---|
| `SRC-617a593591cb7e13` | `chenRen2020AverageTracking` | [Springer / DOI 10.1007/978-3-030-39536-0](https://doi.org/10.1007/978-3-030-39536-0) | Chen--Ren, 1.ª ed., 2020, ISBN 978-3-030-39535-3. Seguimiento promedio distribuido y estimación; no integrabilidad, cierre entero ni Cargo. |
| `SRC-c68ccfd92d3f5d54` | `rozaMaggioreScardovi2022Coordination` | [Springer / DOI 10.1007/978-3-030-96087-2](https://doi.org/10.1007/978-3-030-96087-2) | Roza--Maggiore--Scardovi, 1.ª ed., LNCIS 490, 2022, ISBN 978-3-030-96086-5. Uniciclos, rendezvous y formación; no carga ni wrench. |
| `SRC-bf8f10d20534d125` | `renBeard2008Consensus` | [Springer / DOI 10.1007/978-1-84800-015-5](https://doi.org/10.1007/978-1-84800-015-5) | Ren--Beard, 1.ª ed., 2008, ISBN 978-1-84800-014-8. Consenso y formación multivehículo; no mecánica o instrumentación Cargo. |
| `SRC-e826761b9b60501e` | `martinezPiazuelo2026GNEBook` | [Springer / DOI 10.1007/978-3-032-06081-5](https://doi.org/10.1007/978-3-032-06081-5) | Martinez-Piazuelo--Ocampo-Martinez--Quijano, 1.ª ed., 2026, ISBN 978-3-032-06080-8. GNE, disipatividad y multiplicadores; no sustituye la formulación o prueba propia. |
| `SRC-4ced4ee03f6d46a6` | `siegwartNourbakhsh2004Autonomous` | [MIT Press, ISBN 978-0-262-19502-7](https://mitpress.mit.edu/9780262195027/introduction-to-autonomous-mobile-robots/) | La unidad local es la 1.ª ed. de Siegwart--Nourbakhsh (2004), no la 2.ª ed. de Siegwart--Nourbakhsh--Scaramuzza (2011). Fundamenta movilidad; no coaliciones, carga o reservas. |
| `SRC-0b7ceba994fe5772` | `yildirimReefkeAktas2023Warehouse` | [Palgrave / DOI 10.1007/978-3-031-12307-8](https://doi.org/10.1007/978-3-031-12307-8) | Yildirim--Reefke--Aktas, 1.ª ed., 2023, ISBN 978-3-031-12306-1. Contexto, selección y KPI; no evidencia de rendimiento o fidelidad física. |
| `SRC-8d35243f573f11d9` | `carriero2026DistributedControl` | [Repositorio institucional / Handle 11567/1288096](https://hdl.handle.net/11567/1288096) | Carriero, tesis doctoral defendida el 27-02-2026, Università degli Studi della Basilicata, DRIM. Transporte con manipuladores, estimación de wrench y admitancia; no valida Pioneer ni soporte 2.5D. |

Las otras tres unidades `verified-ledger` son Bullo--Cortés--Martínez (`SRC-d7808bdf107394b0`), Lee--Dimarogonas--Kim (`SRC-097398c064adff1a`, conservada como preprint) y Quijano et al. (`SRC-7df2a947e484a325`). Sus DOI/registro, identidad y límite de uso constan en el CSV reproducible.

## Cierre de las 27 identidades secundarias del 2026-09-09

La auditoría siguiente comprueba autoría, título, sello, edición/año e identificadores. No evalúa de manera independiente cada afirmación que pudiera citarse. Por ello estas unidades conservan `use-later` u `out-of-scope`, no se añadieron automáticamente al ledger y no modifican el estado de ningún claim.

| Unidad | Registro autorizado | Resolución de identidad |
|---|---|---|
| `SRC-a5352edb4fdf3762` | [Springer](https://link.springer.com/book/10.1007/978-3-030-95029-3) | Ding--Han--Ning, 1.ª ed., 2022; DOI e ISBN cerrados. |
| `SRC-eb06edb5b9fef4df` | [Springer](https://link.springer.com/book/10.1007/978-3-319-45150-3) | Wu et al., 1.ª ed., 2017; se resuelve el año ausente. |
| `SRC-d366d50beff01df1` | [Elsevier](https://shop.elsevier.com/books/consensus-tracking-of-multi-agent-systems-with-switching-topologies/dong/978-0-12-818365-6) | Dong--Nguang, 1.ª ed., 2020, ISBN 978-0-12-818365-6. |
| `SRC-e385619b26baf1b7` | [Routledge](https://www.routledge.com/Robust-Cooperative-Control-of-Multi-Agent-Systems-A-Prediction-and-Observation-Prospective/Wang-Zuo-Wang-Ding/p/book/9780367758233) | Wang et al., 2021; el título editorial dice *Prospective*, no *Perspective*. |
| `SRC-72cf71b8d4c2f78a` | [Routledge](https://www.routledge.com/Control-and-State-Estimation-for-Dynamical-Network-Systems-with-Complex-Samplings/Shen-Wang-Li/p/book/9781032310206) | Shen--Wang--Li, primera edición publicada en 2023; el nombre local indicaba 2022. |
| `SRC-ae2579b85f790469` | [DOI CRC](https://doi.org/10.1201/b17571) | Li--Duan, copyright/edición bibliográfica 2015; la copia tiene fecha de producción 2014. |
| `SRC-e0d36b349fca2523` | [World Scientific](https://www.worldscientific.com/worldscibooks/10.1142/Q0307) | Pitt, catálogo 2021 y DOI Q0307; la copia local muestra copyright 2022. |
| `SRC-029958c43a90def4` | [O'Reilly](https://www.oreilly.com/library/view/learning-javascript-design/9781098139865/) | Osmani, 2.ª ed., 2023; permanece fuera de alcance. |
| `SRC-7923e0f353c892cb` | [IntechOpen](https://www.intechopen.com/books/7227) | Hurtado (ed.), volumen de 2019, DOI 10.5772/intechopen.74181; se elimina la confusión con el DOI de un capítulo. |
| `SRC-f77a1852b0dd9547` | [Springer](https://link.springer.com/book/10.1007/978-981-97-0968-7) | Zhao et al., 1.ª ed., 2024. |
| `SRC-9b99df00a9de8dbe` | [Springer](https://link.springer.com/book/10.1007/978-3-030-98377-2) | Cai--Su--Huang, 1.ª ed., 2022. |
| `SRC-ba119b1e62a727e3` | [DOI IEEE](https://doi.org/10.1109/ACCESS.2018.2890086) | Wu et al., *IEEE Access* 7, 6853--6865, 2019; permanece fuera de alcance. |
| `SRC-6fdf8c2acc16ef8a` | [DOI CRC](https://doi.org/10.1201/9781003394372) | Wang--Long--Huang--Wen, primera edición publicada en 2025; los escaparates muestran otras fechas de disponibilidad. |
| `SRC-9752523ef477dbb6` | [Cambridge Core](https://www.cambridge.org/core/books/games-and-coalitions/3F59298409B0E267B4F9C19A1B1D9ADE) | Okada, 2026; DOI e ISBN cerrados. |
| `SRC-cc14c73b30364a27` | [Springer](https://link.springer.com/book/10.1007/978-3-031-27601-9) | Weiss--Agassi, 1.ª ed., 2023; permanece fuera de alcance. |
| `SRC-36d7e7ffdbd50096` | [ScienceDirect](https://www.sciencedirect.com/book/9780323901314/second-order-consensus-of-continuous-time-multi-agent-systems) | Li et al., Academic Press, 2021; ISBN y DOI cerrados. |
| `SRC-d872978ac0bf7e48` | [O'Reilly](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/copyright-page01.html) | Kleppmann, 1.ª ed., marzo de 2017; el nombre local indicaba 2018. |
| `SRC-9afea5b640d8009e` | [Springer](https://link.springer.com/book/10.1007/978-3-031-40180-0) | Lozovanu--Pickl, 1.ª ed., 2024. |
| `SRC-2db0fd66bf8a128b` | [DOI CRC](https://doi.org/10.1201/9781003098607) | Barreiro-Gomez--Tembine, primera edición publicada en 2022; el nombre local indicaba 2021. |
| `SRC-6140ef0a5f2b1f0b` | [Springer](https://link.springer.com/book/10.1007/978-3-031-26564-8) | Azar--Ibraheem--Humaidi (eds.), 2023; los capítulos siguen requiriendo verificación individual. |
| `SRC-c0cae4da012e4a4e` | [IntechOpen](https://www.intechopen.com/books/12723) | Küçük (ed.), *Multi-Robot Systems – New Advances*, 2023; se corrige el contenedor antes ambiguo. |
| `SRC-6ced88da54848d51` | [Springer](https://link.springer.com/book/10.1007/978-3-031-43575-1) | Clempner--Poznyak, 2024; Kacprzyk es editor de serie, no autor. |
| `SRC-3521ec0ec24d75f2` | [ScienceDirect](https://www.sciencedirect.com/book/9780128211861/advanced-distributed-consensus-for-multiagent-systems) | Mahmoud--Oyedeji--Xia, Academic Press, 2021. |
| `SRC-8e9b346a98c3d2f5` | [DOI CRC](https://doi.org/10.1201/9781003180982) | Wen et al., publicación 2021; el escaparate editorial muestra copyright 2022. |
| `SRC-cd6f9eaf695787a8` | [Springer](https://link.springer.com/book/10.1007/978-3-031-15226-9) | Cascalho et al. (eds.), actas CLAWAR 2022 publicadas en 2023; permanece fuera de alcance como volumen global. |
| `SRC-fda513c2ae72b910` | [Springer](https://link.springer.com/book/10.1007/978-3-031-22562-8) | Yadav, 1.ª ed., 2023. |
| `SRC-7c9c92629c5a9197` | [Springer](https://link.springer.com/book/10.1007/978-3-031-07051-8) | Glizer--Kelis, Birkhäuser, 2022; permanece fuera de alcance. |

El script `evidence/tools/verify_book_identities.py --check` inmoviliza estas 37 resoluciones y hace fallar `build.ps1 -Verify` si el CSV deja de coincidir con la auditoría. La columna `verification_source` conserva un registro por unidad; `verification_note` explica correcciones y discrepancias de edición.

## Incidencias de identidad y calidad documental

- `SRC-e0d36b349fca2523` presenta 2021 en el catálogo/DOI y copyright 2022 en la copia; `SRC-2db0fd66bf8a128b` presenta 2021 en el nombre local y primera edición 2022 en la página legal.
- `SRC-72cf71b8d4c2f78a`, `SRC-ae2579b85f790469`, `SRC-d872978ac0bf7e48` y `SRC-6fdf8c2acc16ef8a` tenían fechas de nombre de archivo, producción, copyright o disponibilidad incompatibles; el CSV conserva la resolución y la discrepancia, no un año silenciosamente sustituido.
- `SRC-097398c064adff1a` aparece como 2026 en el nombre, pero el ledger lo verifica como preprint de 2025.
- `SRC-6ced88da54848d51` atribuye a Janusz Kacprzyk en el nombre; la portada lo identifica como editor de serie y a Clempner--Poznyak como autores.
- `SRC-e385619b26baf1b7` y `SRC-c0cae4da012e4a4e` tienen metadatos PDF contaminados; sus identidades se resolvieron con Routledge e IntechOpen, pero no se dieron de alta como citas. `SRC-8d35243f573f11d9` conserva metadatos genéricos de plantilla, pero su identidad quedó confirmada por el repositorio institucional.
- `SRC-7923e0f353c892cb`, `SRC-c0cae4da012e4a4e`, `SRC-6140ef0a5f2b1f0b` y `SRC-cd6f9eaf695787a8` son contenedores editados. Si un capítulo llega a utilizarse, debe verificarse y registrarse como unidad bibliográfica independiente.

## Índice 37/37

| Unidad | Identidad abreviada | Consulta pertinente | Decisión |
|---|---|---|---|
| `SRC-617a593591cb7e13` | Chen--Ren, *Distributed Average Tracking* | consenso dinámico, Euler--Lagrange, formación | `use-now` |
| `SRC-c68ccfd92d3f5d54` | Roza--Maggiore--Scardovi, *Distributed Coordination Theory for Robot Teams* | uniciclos, formación y estabilidad | `use-now` |
| `SRC-a5352edb4fdf3762` | Ding--Han--Ning, *Distributed Control and Optimization of Networked Microgrids* | eventos, retardos y optimización distribuida | `use-later` |
| `SRC-eb06edb5b9fef4df` | Wu et al., *Synchronization Control for Large-Scale Network Systems* | sampled-data, saturación y retardo | `use-later` |
| `SRC-d366d50beff01df1` | Dong--Nguang, *Consensus Tracking... Switching Topologies* | fallos, reemplazo y topología variable | `use-later` |
| `SRC-e385619b26baf1b7` | Wang et al., *Robust Cooperative Control* | consenso robusto y formación | `use-later` |
| `SRC-72cf71b8d4c2f78a` | Shen--Wang--Li, *Control and State Estimation... Complex Samplings* | muestreo y estimación por eventos | `use-later` |
| `SRC-ae2579b85f790469` | Li--Duan, *Cooperative Control... Consensus Region* | baselines de consenso y tracking | `use-later` |
| `SRC-e0d36b349fca2523` | Pitt, *Self-Organising Multi-Agent Systems* | taxonomía sociotécnica y juegos | `use-later` |
| `SRC-029958c43a90def4` | Osmani, *Learning JavaScript Design Patterns* | sin contenido científico pertinente | `out-of-scope` |
| `SRC-7923e0f353c892cb` | Hurtado (ed.), *Applications of Mobile Robots* | revisión MARS, movimiento y navegación | `use-later` |
| `SRC-f77a1852b0dd9547` | Zhao et al., *Cooperative Control... Hybrid System Approach* | retardo, pérdida, eventos y reset | `use-later` |
| `SRC-9b99df00a9de8dbe` | Cai--Su--Huang, *Cooperative Control... Distributed Observer* | observadores, Euler--Lagrange y regulación | `use-later` |
| `SRC-ba119b1e62a727e3` | Wu et al., angular momentum management | aplicación espacial específica | `out-of-scope` |
| `SRC-d7808bdf107394b0` | Bullo--Cortés--Martínez, *Distributed Control of Robotic Networks* | localidad, grafos, complejidad y asincronía | `use-now` |
| `SRC-6fdf8c2acc16ef8a` | Wang et al., *Distributed Adaptive Consensus Control* | incertidumbre, eventos y formación no holónoma | `use-later` |
| `SRC-bf8f10d20534d125` | Ren--Beard, *Distributed Consensus in Multi-vehicle Cooperative Control* | consenso y formación multivehículo | `use-now` |
| `SRC-9752523ef477dbb6` | Okada, *Games and Coalitions* | puente cooperativo--no cooperativo | `use-later` |
| `SRC-cc14c73b30364a27` | Weiss--Agassi, *Games to Play and Games Not to Play* | ensayo político-filosófico | `out-of-scope` |
| `SRC-e826761b9b60501e` | Martinez-Piazuelo--Ocampo-Martinez--Quijano, *GNE Seeking in Population Games* | GNE, potencial, disipatividad y multiplicadores | `use-now` |
| `SRC-36d7e7ffdbd50096` | Li et al., *Second-Order Consensus* | redes conmutadas y muestreo por eventos | `use-later` |
| `SRC-4ced4ee03f6d46a6` | Siegwart--Nourbakhsh, *Introduction to Autonomous Mobile Robots* | robot diferencial, sensores y navegación | `use-now` |
| `SRC-d872978ac0bf7e48` | Kleppmann, *Designing Data-Intensive Applications* | fallos parciales, versiones y transacciones | `use-later` |
| `SRC-097398c064adff1a` | Lee--Dimarogonas--Kim, switching cooperative manipulation | extensión no prehensil con conmutación | `use-now` |
| `SRC-9afea5b640d8009e` | Lozovanu--Pickl, *Markov Decision Processes and Stochastic Positional Games* | extensión dinámica/estocástica | `use-later` |
| `SRC-2db0fd66bf8a128b` | Barreiro-Gomez--Tembine, *Mean-Field-Type Games for Engineers* | contraste mean-field--poblacional | `use-later` |
| `SRC-6140ef0a5f2b1f0b` | Azar--Ibraheem--Humaidi (eds.), *Mobile Robot* | formación, control y path planning | `use-later` |
| `SRC-0b7ceba994fe5772` | Yildirim--Reefke--Aktas, *Mobile Robot Automation in Warehouses* | contexto industrial y KPI | `use-now` |
| `SRC-c0cae4da012e4a4e` | Küçük (ed.), *Multi-Robot Systems* | trayectorias, comunicación y flota minera | `use-later` |
| `SRC-6ced88da54848d51` | Clempner--Poznyak, *Optimization and Games for Controllable Markov Chains* | best reply y mecanismos estocásticos | `use-later` |
| `SRC-3521ec0ec24d75f2` | Mahmoud--Oyedeji--Xia, *Advanced Distributed Consensus* | redes vulnerables, multivehículo y rutas | `use-later` |
| `SRC-8e9b346a98c3d2f5` | Wen et al., *Cooperative Control... Dynamic Topologies* | topologías conmutadas y resiliencia | `use-later` |
| `SRC-8d35243f573f11d9` | Carriero, tesis doctoral sobre transporte cooperativo | wrench, admitancia, CoppeliaSim y experimentos | `use-now` |
| `SRC-cd6f9eaf695787a8` | Cascalho et al. (eds.), *Robotics in Natural Settings: CLAWAR 2022* | actas heterogéneas; coincidencias periféricas | `out-of-scope` |
| `SRC-fda513c2ae72b910` | Yadav, *Advanced Graph Theory* | matching, digrafos y espectro | `use-later` |
| `SRC-7c9c92629c5a9197` | Glizer--Kelis, juegos diferenciales cero-suma singulares | teoría fuera de la formulación actual | `out-of-scope` |
| `SRC-7df2a947e484a325` | Quijano et al., population games in distributed control | juegos poblacionales y control distribuido | `use-now` |

La tabla de datos completa, incluidos hash, ruta, claims, limitación y nota de copyright por unidad, está en `book-consultation-map.csv`.
