# Sesión manual de Web of Science — 2026-09-13

## Alcance y estado

Sesión ejecutada mediante la interfaz institucional de Web of Science Core
Collection, con las consultas del paquete
`manual-packs/web_of_science_query_pack.csv`. La fuente estuvo accesible hasta
que Web of Science mostró un hCaptcha por actividad inusual. No se intentó
resolver, automatizar ni eludir ese control.

La interfaz también rechazó el intervalo fundacional `1940-01-01` a
`1999-12-31` como fuera de la cobertura de la base suscrita. Este resultado se
clasifica como `outside_subscription_coverage`, nunca como una búsqueda de cero
resultados.

## Consultas verificadas antes del bloqueo

| Ejecución | Consulta Topic | Ventana | Resultados mostrados | Exportación solicitada |
|---|---|---:|---:|---|
| F01_primary | `multi-robot coalition formation` | 2000–2026 | 80 | Plain Text, Full Record and Cited References |
| F02_primary | `heterogeneous multi-robot task allocation` | 2000–2026 | 275 | Plain Text, Full Record and Cited References |
| F03_primary | `game theoretic multi-robot task allocation` | 2000–2026 | 14 | Plain Text, Full Record and Cited References |
| F03_foundational | `game theoretic multi-robot task allocation` | 1940–1999 | n/a | `outside_subscription_coverage` |
| F04_primary | `distributed auction consensus multi-robot task allocation` | 2000–2026 | 13 | Plain Text, Full Record and Cited References |
| F05_primary | `multi-robot cooperative payload transport` | 2000–2026 | 23 | Plain Text, Full Record and Cited References |
| F06_primary | `multi-robot shared load object transport` | 2000–2026 | 3 | Plain Text, Full Record and Cited References |
| F07_primary | `multi-robot non-prehensile transport caging pushing` | 2000–2026 | 1 | Plain Text, Full Record and Cited References |
| F08_primary | `multi-robot wrench contact force feasibility payload` | 2000–2026 | 0 | no export |
| F09_primary | `distributed multi-robot formation docking cooperative transport` | 2000–2026 | 0 | no export |
| F10_primary | `decentralized leaderless multi-robot cooperative transport` | 2000–2026 | not executed | hCaptcha before execution |

## Reanudación tras la verificación manual

Después de que la persona usuaria resolviera manualmente el hCaptcha, se
reanudó la sesión desde F10 sin intentar automatizar ni eludir ninguna
verificación. Las consultas se ejecutaron una por una en la misma base, edición
y ventana primaria. Los resultados siguientes son resultados de las
formulaciones exactas del paquete; un cero no sustenta una afirmación de
ausencia de literatura.

| Ejecución | Consulta Topic | Ventana | Resultados mostrados | Exportación solicitada |
|---|---|---:|---:|---|
| F10_primary | `decentralized leaderless multi-robot cooperative transport` | 2000–2026 | 0 | no export |
| F11_primary | `multi-robot coordination packet loss delay switching topology` | 2000–2026 | 0 | no export |
| F12_primary | `multi-robot coalition failure recovery robot replacement transport` | 2000–2026 | 0 | no export |
| F13_primary | `multi-robot traffic planning carried payload warehouse` | 2000–2026 | 0 | no export |
| F14_primary | `multiple robot coalitions congestion coordination logistics` | 2000–2026 | 0 | no export |
| F15_primary | `heterogeneous robot capability heterogeneous load coalition` | 2000–2026 | 0 | no export |
| F16_primary | `heterogeneous distributed coalition cooperative payload failure recovery` | 2000–2026 | 0 | no export |

Las variantes fundacionales restantes del paquete (F05, F07--F10) no se
reenviaron individualmente: la interfaz ya había rechazado esa ventana temporal
a nivel de cobertura de la base. Su estado es
`outside_subscription_coverage`, no cero resultados.

## Estado inicial y limitación superada

En el primer registro de esta sesión, los eventos de exportación de F01–F07
cerraron sus diálogos, pero sus archivos todavía no eran localizables. Esa
limitación quedó superada al recuperar los ficheros de descargas sin alterarlos
y copiarlos a la carpeta de ingesta del repositorio.

## Recuperación, integridad e ingesta reproducible

Los ficheros crudos se conservan como exportaciones `Plain Text` con `Full
Record and Cited References`; no se fusionaron ni editaron manualmente. La
tabla registra el hash SHA-256 del archivo preservado, el número de registros
observado mediante el delimitador `PT` y la completitud frente al resultado que
mostró WoS.

| Ejecución | Archivo preservado | Mostrados por WoS | `PT` observados | Estado | SHA-256 |
|---|---|---:|---:|---|---|
| F01_primary | `inputs/wos/F01_primary_wos_plaintext_full_record_cited_references.txt` | 80 | 50 | `partial` | `fe113a792181e582af1b7bd3d05d6c4a303e654ddaf83226b1ae7e05bce46bea` |
| F02_primary | `inputs/wos/F02_primary_wos_plaintext_full_record_cited_references.txt` | 275 | 50 | `partial` | `2fb8a62156d0b6f9f788fe355e0cf3e57965660fd8b80b7341bfd022f56c588d` |
| F03_primary | `inputs/wos/F03_primary_wos_plaintext_full_record_cited_references.txt` | 14 | 14 | `complete` | `fdba00941fbdd6ded439aa1e14727b30748095b965a43a31a71f74f999dda116` |
| F04_primary | `inputs/wos/F04_primary_wos_plaintext_full_record_cited_references.txt` | 13 | 13 | `complete` | `0cc38314187498206e385e5cb6a29971bfd23af4e8b144ea4adba329229bceb` |
| F05_primary | `inputs/wos/F05_primary_wos_plaintext_full_record_cited_references.txt` | 23 | 23 | `complete` | `8ec26e0e4f05d343e656959bc81b6c1d3c65997525487ae5c07dbc751d9a41c2` |
| F06_primary | `inputs/wos/F06_primary_wos_plaintext_full_record_cited_references.txt` | 3 | 3 | `complete` | `8ae9a79ad4585b18cdfc3db140fd1e62c2205f91da59831c4873012b59f76ea6` |
| F07_primary | `inputs/wos/F07_primary_wos_plaintext_full_record_cited_references.txt` | 1 | 1 | `complete` | `6ba3ce9cb545f0484b07b1c949b7fed4a2e9adca9a90a28e5f147b24d31656b7` |

La suma de registros presentes es **154**. No se etiqueta como cobertura
completa: faltan **30** registros de F01 y **225** de F02. La declaración
estructurada de esta condición y de los hashes está en
`inputs/wos/wos_export_manifest.json`.

El importador fue ampliado para leer el formato etiquetado nativo de WoS (que
usa `PT`/`ER` y líneas de continuación), sin convertir los registros en
evidencia científica. La reconstrucción posterior ejecutó Stage 1A con
`--mode all --resume`, rebasó los congelados archivando sus versiones previas y
regeneró Stages 1B–5. El estado final de cobertura es
`wos_partially_reconciled`; una exportación parcial no sustenta exhaustividad,
ausencia de trabajos ni conclusiones de novedad.
