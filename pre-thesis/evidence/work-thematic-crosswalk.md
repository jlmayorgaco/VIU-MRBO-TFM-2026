# Auditoría temática del corpus `work`

La raíz física vigente es `material/compendios/`. Los `unit_id` y hashes se conservan tras la reubicación para no romper las 33 decisiones temáticas.

Fecha de corte: 8 de septiembre de 2026.

## Alcance y criterio de lectura

El universo auditado son los 33 PDF marcados como canónicos para el corpus
`work` en `source-manifest.csv`. Los 43 archivos físicos del directorio incluyen
10 duplicados exactos ya resueltos por hash; esta tabla no vuelve a contarlos.
Los 33 `unit_id`, rutas y SHA-256 se contrastaron con el manifiesto y con los
archivos presentes: 33 identificadores únicos, 33 hashes únicos, 33 rutas únicas
y cero discrepancias de hash.

La auditoría es documental y temática. Usa el charter, los requisitos VIU, la
matriz SP1--SP3, el protocolo, el ledger de claims y la notación como fuentes de
mayor precedencia; usa `content-crosswalk.csv` como punto de partida y los
localizadores de `idea-ledger.csv` para abrir cada documento. De las 3.094
unidades de ideas registradas en `work`, 2.455 son marcadores PDF, 606 son
encabezados candidatos obtenidos del texto y 33 son títulos de documento. Los
30 PDF con marcadores se localizaron por estos; los tres sin marcadores
(`SRC-ca9fecb0fd11eb9e`, `SRC-3277b8f3372cf0a9` y
`SRC-3c311c9ba087b9f3`) se localizaron por encabezados candidatos.

Ningún PDF de `work` es evidencia independiente: son borradores del autor,
compendios o exportaciones de conversaciones. Por ello, `claim_ids` queda vacío
en las 33 filas. Un enlace exacto a un claim solo podrá añadirse después de
auditar la unidad concreta, sus supuestos y su correspondencia con prueba,
código o datos. Del mismo modo, ningún documento se promueve directamente a
`thesis-body` o `thesis-appendix`; 15 son candidatos de extracción para la
monografía, 4 sirven como contexto/procedencia y 14 quedan solo en archivo. Esta
decisión no descarta sus ideas: la cobertura idea a idea, todavía con 3.094
revisiones semánticas pendientes, vive en `idea-ledger.csv`.

## Resultado de clasificación

| Dimensión | Conteo |
|---|---:|
| PDF canónicos auditados | 33 |
| Destino `monograph` | 15 |
| Destino `background` | 4 |
| Destino `archive-only` | 14 |
| Decisión `candidate` | 19 |
| Decisión `superseded` | 9 |
| Decisión `duplicate` de contenido, no de hash | 4 |
| Decisión `out-of-scope` | 1 |
| Decisión `incorporated` | 0 |
| Filas con claim ID defendible en este nivel | 0 |

El `content-crosswalk.csv` previo es deliberadamente grueso y contiene rutas
temáticas por nombre que no deben propagarse: por ejemplo, el PDF SP2 y ambos
PDF SP3 aparecen allí como `SP1`. La clasificación nueva corrige esos ámbitos
solo en este artefacto; no modifica el manifiesto ni declara que el contenido
haya sido validado.

## Clústeres y prioridades

### P0: auditar y extraer primero

- **Monografía integrada M1** (`SRC-7ea71387d0d0ab51`): candidato más amplio
  para derivaciones electromecánicas, Cargo/caging, GNE y ciclo de vida.
- **SP1 final del 26 de agosto** (`SRC-3c311c9ba087b9f3`): versión documental
  preferente para N1--N4, sus negativos y el coste de localidad.
- **SP2 definitivo** (`SRC-12aed037161e2ba6`): puente compacto desde coalición
  nominal a actuación, guardia y recuperación.
- **SP3 completo de 64 páginas** (`SRC-f91b259d373ab112`): paquete N1--N5 con
  teoría, experimento y amenazas a la validez.
- **Dossier matemático integral** (`SRC-52bbb326926f1030`): mapa de resultados
  formales que debe cruzarse con la auditoría semántica del corpus `paper`.

P0 significa prioridad de auditoría, no autorización de incorporación. Cada
fragmento debe sobrevivir la verificación formal, bibliográfica y experimental.

### P1: deltas científicos y registros de errores

- CFRD/Transactions (`SRC-32584f218d873480`) concentra el desarrollo SP1 que
  excede la memoria.
- Cargo--push GNE (`SRC-c4de2cde436be1e7`) aporta una separación física útil,
  todavía sin validación de contacto y actuación.
- El informe de gap (`SRC-beab593a2b13019e`) orienta la comprobación de novedad,
  pero exige verificar cada fuente primaria.
- La lectura cruzada de Claude (`SRC-73637cf3b199b2dd`) y la reparación R2
  (`SRC-a2ea245c285dfcb3`) son listas de fallos que conviene impedir que
  reaparezcan; no son evidencia.
- Del compendio v0.2 (`SRC-437ad193392af6ac`) solo interesa inicialmente el
  addendum de las pp. 252--272.
- Del compendio total (`SRC-349e5c0a19e09ffb`) solo interesan inicialmente las
  Partes VII--VIII, pp. 557--581.

### P2: extensión o rescate condicionado

R5 A-DACP, empuje trasero, cruce y pasillo negociados, adaptación de información,
el resumen Python2D y el dossier de handoff pueden aportar experimentos,
contraejemplos o contexto. Antes de extraerlos hay que localizar los generadores,
repetir el caso con configuraciones y semillas versionadas y separar seguridad,
progreso y optimalidad. Caging permanece como extensión independiente de Cargo.

### Archivo y exclusión

Las revisiones R4, el compendio de chat, los compendios intermedios, las versiones
VIU previas y el MegaPaper PDF están sucedidos por fuentes más auditables. Cuatro
contenedores se clasifican como duplicados de contenido aunque sus hashes sean
distintos; no deben eliminarse hasta comprobar los deltas. `TFM-libro V0` trata
clasificación de audio con aprendizaje supervisado y queda fuera del alcance
SP1--SP3.

## Registro 33/33

La columna `prioridad` resume el orden de auditoría descrito arriba. Un guion
indica que el documento solo se conserva como versión, contenedor o material
fuera de alcance. El CSV asociado contiene los temas, localizadores, solapamiento,
evidencia faltante y racional completos.

| # | unit_id | SHA-256 | documento | ámbito | destino | decisión | prioridad |
|---:|---|---|---|---|---|---|---|
| 1 | `SRC-32584f218d873480` | `1a8c235fda942a810e4b1ad35edc20e714b5f76050e5c089a0aa3551bfc81bb5` | CFRD Dossier Transactions | SP1; transversal | monograph | candidate | P1 |
| 2 | `SRC-b5d82989c338d837` | `19002dfdaac7d193bc176165a242b446a35ca76cc61f5a95cbd8176bed962dad` | Compendio R4 A-DACP | SP3; transversal | archive-only | superseded | -- |
| 3 | `SRC-9c91bed248887adb` | `4f34207fd8ecf6ad248653925078be1190de8390688cfdf7c02a463549800542` | Compendio R5 A-DACP | SP2; SP3; transversal | monograph | candidate | P2 |
| 4 | `SRC-6c9c4930ac01451e` | `71e1545ec727d8046663fbf104ea5294addc865d198a922932c64faa73a7b2c2` | Compendio integral de chat | SP3; transversal | archive-only | superseded | -- |
| 5 | `SRC-ca9fecb0fd11eb9e` | `31724b4b05d7789383128aa6cd95f9da09ebd1943f86b8f031bacf24befacbe8` | Compendio maestro DENSO 100p | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 6 | `SRC-c4de2cde436be1e7` | `97d5122e1e6f17997d5ffe77c35725db3814ea0eee8d54e7130d17055c662c6d` | Desarrollo Cargo--push GNE | SP2 | monograph | candidate | P1 |
| 7 | `SRC-bad67694708989fb` | `0f6d9a8c06928da5e7b9ea602f318d1f469b32c58fc4f39cbc25f88f5edd09ac` | Empuje trasero GNE | SP2 | monograph | candidate | P2 |
| 8 | `SRC-beab593a2b13019e` | `599da18ecce3483dfb82ebbe2489890408dff151f215fec6a266651f74111783` | Informe de gap AMR heterogéneos | transversal | background | candidate | P1 |
| 9 | `SRC-2dafcae631db0d73` | `5c8b81abf0eb7578b7fb3a38d13eb48cb0ae7ed25148e2b9a2d796ac521cc28f` | Mega compendio MegaJuego | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 10 | `SRC-325e48b75e569319` | `2e4cc63a63552cad5f5789dad092d4f2bed5a37a73f036b8a503837e464acf69` | Cruce negociado | SP3 | monograph | candidate | P2 |
| 11 | `SRC-73637cf3b199b2dd` | `97bc60c76d812dfe3ad22e6bbac43534c297fe52ffc1c5b1451bae93fa22aa81` | Lectura cruzada de resultados matemáticos | SP1; SP2; SP3; transversal | background | candidate | P1 |
| 12 | `SRC-ed463444c24667b9` | `61ef7831aa83b03ba0cb9ca40f40f63cb01549f791a9edd361d0dbfb6aedfaf8` | Cierre MegaJuego v4 | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 13 | `SRC-7ea71387d0d0ab51` | `58b2bb302af1bfad9af7f64a80bf2ae42c4ab4aa664293c2cf57b9157518df93` | Monografía científica integrada M1 | SP1; SP2; SP3; transversal | monograph | candidate | P0 |
| 14 | `SRC-a2ea245c285dfcb3` | `c90d29152bb9994285e7ab565ee989ca59be07fc395d842de03161a8e982da44` | Reparación MegaJuego R2 | SP2; transversal | background | candidate | P1 |
| 15 | `SRC-244076e569684db6` | `abc23812ef000013140a77cdb6ab8d57e0acd041c39bc81156f3b943e0927066` | Pasillo negociado | SP3 | monograph | candidate | P2 |
| 16 | `SRC-3ce0e8603d586165` | `76f7fb38c4336d87ead31c6b75c7adb5e49655490238a650c1cff3ee865232a2` | Adaptación e información MegaJuego | SP2; SP3; transversal | monograph | candidate | P2 |
| 17 | `SRC-cd9898bc6c60eb64` | `92e5107cedb74d3d233c9cea5605c36beee73f30d2f4a1c0a12014c75b970ef2` | Simulación Python2D | SP2; SP3 | monograph | candidate | P2 |
| 18 | `SRC-3277b8f3372cf0a9` | `40ccaf54851d421038c98287fd4348e2bbbb6f00da5ca4775321c33afea81efc` | SP1 VIU corregido 23-ago | SP1 | archive-only | superseded | -- |
| 19 | `SRC-3c311c9ba087b9f3` | `d4221d93656b06a3d3dfc703970ea7823b79df9f505964ab1b14a013353f0582` | SP1 VIU final 26-ago | SP1 | monograph | candidate | P0 |
| 20 | `SRC-12aed037161e2ba6` | `c6d5917bb73c2115acc54ba3e8876b2d390ab34ac2fb52954380f9c8a12cd5e7` | SP2 VIU definitivo | SP2 | monograph | candidate | P0 |
| 21 | `SRC-f91b259d373ab112` | `8c045ddacddd25ab4632b3ab655b7751e69fb7d2c51f461506ba063227bea67b` | SP3 completo, 64 p. | SP3 | monograph | candidate | P0 |
| 22 | `SRC-e0424a59343782f0` | `0c396654b2cfcabe4622f9d756001ad15f4f410f01305dd0b145c9d4738cd825` | SP3 matemática madurada, 53 p. | SP3 | archive-only | duplicate | -- |
| 23 | `SRC-437ad193392af6ac` | `b4bd16fad36b266580743ec2297b4a1349f29761dfc6f0a9a57fb1aab7270ab6` | Compendio científico v0.2 | SP1; SP2; SP3; transversal | monograph | candidate | P1 |
| 24 | `SRC-def79cb7b409308f` | `435b69076174ccd64218532aa07b498143b99ea035d54e48321cfe2e213617b1` | Compendio maestro exhaustivo | SP1; SP2; SP3; transversal | archive-only | duplicate | -- |
| 25 | `SRC-349e5c0a19e09ffb` | `6f881aac7d372b6c1a1fe63015008569f419a550fd2dedf871a49a82390fa71e` | Compendio total sin recortes | SP1; SP2; SP3; transversal | monograph | candidate | P1 |
| 26 | `SRC-62dd677ce03f2814` | `4b54954dacd6f642eb67e5d4fc5a558340d292ecb888cdb62857ebc2646437a0` | Documento canónico vivo v0.1 | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 27 | `SRC-a720062584225555` | `e2820a726cbc2a78c067335e4951a0e3e929cab35563e708cf7ceed82f374ff0` | Dossier maestro handoff | transversal | background | candidate | P2 |
| 28 | `SRC-52bbb326926f1030` | `d64728e0a2a84b059c64d318123f76e620a31ef9633fdb2487a9a23508ba7efe` | Dossier matemático integral | SP1; SP2; SP3; transversal | monograph | candidate | P0 |
| 29 | `SRC-1493de2273eb5bd1` | `1400ab0e91e7c5fc5604a1dc8d0ba0b8e2c808e183448497aa377ad6bb63e2e9` | Borrador VIU de 73 p. | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 30 | `SRC-7ae61b51ea3953ad` | `62353a9e0da7ffc31c7c4d76664b0acd6179dabd20db77e522cd4cb451d8d52a` | Borrador VIU de 68 p. | SP1; SP2; SP3; transversal | archive-only | duplicate | -- |
| 31 | `SRC-5accde69f392e98d` | `06917dd265d06ed68be681ab1ce576c0b55b1a1cafeb071a5d24d05f2186d6dd` | MegaPaper IEEE unificado | SP1; SP2; SP3; transversal | archive-only | superseded | -- |
| 32 | `SRC-517e306d0d8ee15b` | `325f7580d6f88a301134081ddf6de790914b61ccebb837e067d6247033f655dd` | Monografía canónica 200p | SP1; SP2; SP3; transversal | archive-only | duplicate | -- |
| 33 | `SRC-f59dd7c31e663c03` | `b345c2e289695cfe6ef1fcb19211b078539f357f1dac51db6ad2873cff402aa2` | TFM-libro V0 | fuera de alcance | archive-only | out-of-scope | -- |

## Condición para la siguiente pasada

La pasada temática queda cerrada, pero no la auditoría de contenido. El siguiente
paso seguro es revisar las 19 fuentes candidatas en orden P0--P2 y resolver sus
unidades en `idea-ledger.csv`: `incorporated`, `duplicate`, `superseded`,
`background` o `archive-only`, con claim ID solo cuando la afirmación exacta y su
evidencia coincidan. Hasta entonces, los PDF sirven para descubrir material y
contraejemplos; no aumentan el nivel de evidencia de la memoria ni de la
monografía.
