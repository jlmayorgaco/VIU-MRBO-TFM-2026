# Coherencia, flujo y «una sola tesis»

**Criterio aplicado:** `pre-thesis/guidelines/02-coherencia-y-flujo.md`
(1731 líneas, secciones A–CB). Ese fichero es la norma; aquí no se añade
criterio propio. Cada hallazgo se ancla a una sección con letra del mega-checklist.

**Artefacto auditado**

| Artefacto | Contenido |
|---|---|
| `pre-thesis/build-v2/main-v2.pdf` | 146 páginas. Preliminares = PDF 1–17 (romanos i–xvi). Cuerpo impreso p. 1 → PDF 18. Correspondencia exacta: **PDF = impresa + 17**. |
| `build-v2/main-v2.toc` / `.lof` / `.lot` | 73 entradas de índice, 28 figuras, 41 tablas |

**Reparto de páginas impresas** (el dato se usa en varios tests):

| Bloque | Páginas impresas | Extensión |
|---|---|---:|
| Preliminares | PDF 1–17 | 17 pp |
| 1 Introducción | 1–5 | 5 pp |
| 2 Objetivos | 6–7 | 2 pp |
| 3 Hipótesis | 8–10 | 3 pp |
| 4 Metodología | 11–18 | 8 pp |
| 5 Marco teórico | 19–33 | 15 pp |
| 6 Resultados | 34–62 | 29 pp |
| 7 Conclusiones | 63–69 | 7 pp |
| 8 Referencias | 70–80 | 11 pp |
| Anexos A–J | 81–129 | **49 pp** |

**Fecha de la auditoría:** 2026-09-19. No se modificó ningún fichero del TFM.

---

## Veredicto

El documento **no pasa el gate CA**. La norma fija un mínimo de **22/24 por
capítulo** y **cero ceros** en cualquier dimensión. Ningún capítulo llega a 22;
seis de los ocho bloques tienen al menos un 0. Media: **15,0/24**.

La causa no es la prosa —que es notablemente uniforme y honesta— sino tres
defectos estructurales concretos:

1. **Ningún capítulo tiene puente de salida.** Siete transiciones de capítulo,
   cero puentes explícitos (sección F). Dos capítulos terminan literalmente en
   una tabla sin una línea de prosa detrás (pp. 33 y 62).
2. **Seis taxonomías activas + una colisión.** SP1–SP3 significan **dos cosas
   distintas** dentro del mismo documento (p. 27 frente a todo el resto), y
   existen tres vocabularios de estado incompatibles (p. xvi, p. 62, p. 65).
3. **La integración es un apéndice disfrazado de culminación** (sección AW). El
   §6.5 (p. 54) nunca se anuncia en la Introducción ni en la Metodología, y el
   propio Resumen la llama «una arquitectura de integración **adicional**»
   (p. i).

Lo que sí funciona y conviene no tocar: la cadena SP1→SP2→SP3 dentro del
capítulo 6 (pp. 42, 47, 51) cumple el test AV casi al pie de la letra, y la
disciplina de «ninguna garantía se hereda» es genuinamente una sola voz.

---

## A. La prueba fundamental: ¿cuál es la historia?

**La historia, en una frase, tal como el documento la sostiene hoy:**

> Elegir qué robots mueven una carga no basta: cada capa —decisión, mecánica,
> ejecución, tráfico— certifica una propiedad distinta con su propio dominio, y
> este trabajo especifica esos contratos, demuestra qué entrega cada uno y
> muestra experimentalmente dónde deja de valer, sin que la cadena completa
> herede ninguna garantía conjunta.

Esa frase **sí** se puede escribir, y es mérito del documento: la idea
organizadora («cada capa entrega una propiedad concreta; ninguna garantía se
hereda automáticamente», norma § A) está presente y es consistente. Aparece
formulada en p. 1 (¶3), p. 3 (§1.1), p. 4 (Fig. 2), p. 19 (apertura del cap. 5),
p. 34 (Fig. 10), p. 60 (Tabla 22) y p. 63 (apertura del cap. 7).

**Lo que falla del checklist A:**

| Ítem de A | Resultado | Evidencia |
|---|---|---|
| ¿Pregunta central? | **Sí** | RQ1–RQ6, p. 4–5 |
| ¿Problema físico que motiva todo? | **Sí** | p. 1, ¶2: carga que rebasa la capacidad individual |
| ¿Idea organizadora? | **Sí** | contratos entre capas, p. 3–4 |
| ¿Secuencia lógica? | **Parcial** | SP1→SP2→SP3 sí (pp. 42–53); §6.1, §6.5 y §6.6 no encajan en ella |
| ¿Hallazgo principal? | **Sí** | falsos positivos 0.333→0.000 en la interfaz SP1–SP2 (p. 45) |
| ¿Limitación principal? | **Sí**, repetida 11 veces (ver AC) | Cargo acredita compatibilidad funcional, no composición |
| **¿Puede explicarse sin SP1/SP2/SP3/E0/E1/H6?** | **NO** | ver test N |
| **¿Se explica primero conceptual y después el acrónimo?** | **NO** | «SP1», «SP2», «SP3» aparecen sin definición en el Resumen (p. i) y en p. 3 ¶1; la definición funcional llega en p. 13 (§4.3), diez páginas después |
| ¿Cada capítulo aporta una pieza necesaria? | **No** | §6.1 (pp. 36–41, 6 pp) repite el cap. 5 dentro de Resultados |
| **¿Alguna idea aparece demasiado tarde?** | **Sí** | el «juego de integración» y su estado aumentado Y (Ec. 18) debutan en p. 54, al 78 % del cuerpo; la Prop. 6.8 (límite informacional), que el §7.7 usa como razón formal de toda la arquitectura, aparece en p. 61 |
| **¿Alguna idea aparece muchas veces porque nunca se decidió dónde vive?** | **Sí, tres** | (a) el aviso «Cargo = compatibilidad funcional» en pp. 3, 8, 13, 17, 28, 47, 50, 60, 63, 64, 113; (b) la revisión bibliográfica en §4.9 (p. 18), §5.6 (pp. 29–33), §6.1 (pp. 36–41) y Anexo F (pp. 88–94); (c) CoppeliaSim en §4.5 (pp. 14–15), §4.10 (p. 18), §6.6 (p. 59), §H.4 (p. 117) |

**Veredicto A: PARCIAL.** La historia existe y es defendible; el esqueleto
narrativo está contaminado por tres materiales que nunca encontraron domicilio.

---

## B. Test de «tesis vs archivo de proyecto»

| Ítem de B | Resultado | Página y evidencia |
|---|---|---|
| ¿Cuenta el resultado final o la historia de cómo se llegó? | **Mixto** | el cuerpo cuenta el resultado; pp. 15, 16, 26, 44, 113 cuentan el historial |
| **¿Se habla de «formulación previa»?** | **SÍ, literal** | p. 54: «Una **formulación previa** de esta misma arquitectura asumía convergencia al óptimo global» |
| **¿«campaña histórica» más veces de las necesarias?** | **SÍ, 12 veces** | pp. 3, 7, 13, 15, 16, 26, 36, 44, 45, 65, 87, 122 |
| **¿Nombres de archivos, carpetas, scripts o commits en el cuerpo?** | **SÍ, 8 lugares** | p. 38 y p. 39: `pre-thesis/scripts/build_review_figure_data.py`, `analytic_corpus_v3.csv`, `theme_period_v3.csv`, `top_coauthor_pairs_v3.csv`, `method_cooccurrence_v3.csv`; p. 57 (×3): `simulate_e2e_megagame.py`; **p. 58: la página entera contiene una sola línea, `thesis/resources/MROB_MegaGame_E2E_bundle/`**; p. 59 (×2): `run_sp4_v4_coppelia_paired_scene.py` y la campaña `SP4_V4_COPPELIA_PAIRED_NARROW`; p. 117: `legacy/results/sp4/SP4_V4_COPPELIA_PAIRED_NARROW/` y el flag `coppelia_real_kinematic_replay_pass`, `arrival_success=false`; p. 66: «campañas FULL–AGG … delimitadas en **SP1.N4**» |
| **¿Se nota que unos capítulos se escribieron hace meses?** | **SÍ** | §J.5 (p. 128) está **escrita entera sin acentos** («informacion», «trafico», «decision», «perdida», «diseno») mientras las 127 páginas anteriores los llevan |
| **¿Una misma etapa recibe distintos nombres según cuándo fue escrita?** | **SÍ, hasta cuatro** | el transporte cooperativo de E4 es: «E4» (p. 47), «Etapa 2.1» (p. 102), «sp2/sp3/sp6» en minúscula (p. 113), y `SP4_V4` en la campaña de CoppeliaSim (p. 59) |
| **¿E0–E8 aparecen por razones históricas y no porque ayuden al lector?** | **SÍ, y el texto lo admite** | p. 15: «Los códigos E0–E8 corresponden a los **nombres históricos** de las campañas sp0–sp8; **no son subproblemas adicionales**. El capítulo de resultados activa E2, E3, E4, E6, E7 y Cargo; **E0, E1, E5 y E8 permanecen como procedencia y material de monografía**». Es decir, la Tabla 3 (p. 16) dedica 4 de sus 10 filas a etapas que no sostienen ninguna conclusión |
| **¿Se explica trabajo que finalmente no se usa?** | **SÍ, sección entera** | §J.5 «Extension no ensayada» (p. 128): «**No se implemento ni se evaluo** en el demostrador de esta memoria, de modo que **no sostiene ninguna afirmacion activa**». Es el caso puro de la quinta opción prohibida por BZ, «mantener porque ya existe» |
| **¿Material que pertenece al repositorio, no al manuscrito?** | **SÍ** | §J.6 «Alcance y aporte» (p. 129) es una nota de posicionamiento interna («La revisión externa identifica…», «La contribución candidata más coherente es…», «no prioridad mundial»); ese contenido pertenece al cap. 5 o al 7, no al final de un anexo de demostraciones |
| **¿Resultados incluidos por completitud histórica?** | **SÍ** | §6.1 (pp. 36–41): 6 páginas y 6 figuras de bibliometría dentro del capítulo de Resultados |

**Veredicto B: FALLA.** Diez de trece marcadores de «archivo de proyecto» están
presentes y son localizables.

---

## D. Orden global de capítulos — «Test brutal»

Una oración por capítulo, «Capítulo X existe para demostrar/establecer ____»:

| Cap. | pp. | «existe para establecer…» | ¿Función clara? |
|---|---|---|---|
| 1 | 1–5 | …que la selección de una coalición y su ejecución física son interfaces distintas, y que la literatura no las conecta | **Sí** |
| 2 | 6–7 | …los seis objetivos específicos en que se descompone esa conexión | **Sí**, pero ver defecto abajo |
| 3 | 8–10 | …qué predicción comprobable corresponde a cada objetivo | **Sí** |
| 4 | 11–18 | …el modelo, el protocolo pareado y el reparto de dependencias globales bajo los que toda la evidencia debe leerse | **Sí** |
| 5 | 19–33 | …que ninguna familia publicada ni ningún producto comercial reúne selección local + certificación mecánica + recomposición | **Sí** |
| 6 | 34–62 | …qué certifica cada interfaz y dónde deja de certificar | **Sí** |
| 7 | 63–69 | …qué hipótesis quedan sustentadas y en qué dominio | **Sí** |

Las siete frases son distintas: **no hay redundancia a nivel de capítulo**. El
test brutal se pasa. Los defectos de D están en otro sitio:

| Ítem de D | Hallazgo | Página |
|---|---|---|
| **¿Algún concepto se usa antes de definirse?** | Las RQ de p. 4–5 están etiquetadas «(OE1)», «(OE3)», «(OE2)»… pero OE1–OE6 se definen en p. 6. El lector recibe la referencia a un objeto que aún no existe. | 4–5 vs 6 |
| **Ídem** | «SP1», «SP2», «SP3» se usan en el Resumen (p. i) y en p. 3 ¶1; su contenido funcional se define en §4.3, p. 13. | i, 3 vs 13 |
| **Ídem** | H6 (p. 10) predice sobre «el juego de integración», «continuaciones admisibles» y remite al «Anexo J» — tres objetos que no se han presentado y que la Metodología nunca describirá. | 10 |
| **Ídem** | El estado aumentado Y de la Ec. (18) introduce siete símbolos simultáneos (X, d, X̂, E_X, I, Π^inc, S, t) en una línea (p. 54), contra la regla O («evitar introducir 15 símbolos en una ecuación antes de explicar su función») y BK. | 54 |
| **¿La literatura aparece después de resultados que supuestamente motivó?** | **Sí, invertido**: §6.1 (pp. 36–41) coloca 6 páginas de bibliometría **dentro** del capítulo de Resultados, después de la Tabla 7 de contrato de evidencia (p. 36) y antes de SP1 (p. 42). La Tabla 8 (p. 41) es literalmente «Resultados de la revisión y objetivo específico al que condicionan», es decir, material de §5.5. | 36–41 |
| **¿Podrían intercambiarse dos capítulos sin afectar nada?** | §6.1 se podría mover íntegro al cap. 5 sin que nada del cap. 6 lo notase. Eso prueba falta de causalidad narrativa en ese punto. | 36–41 |
| **¿Las limitaciones fundamentales aparecen demasiado tarde?** | No. Aparecen en p. 3 y se repiten (en exceso, ver AC). | — |
| **¿Algún resultado aparece antes de explicar su metodología?** | **Sí**: §6.5 (pp. 54–58) presenta cuatro resultados cuyo modelo, protocolo y diseño experimental **no están en el cap. 4**. «Juego de integración» no aparece ni una sola vez en pp. 11–18. | 54 vs 11–18 |

**Veredicto D: PARCIAL.** El orden de capítulos es correcto; el orden **dentro
del capítulo 6** no lo es.

---

## F. Puentes entre capítulos — **inventario completo**

La norma exige, entre cada par Cᵢ→Cᵢ₊₁, un puente explícito que (a) genere la
necesidad del siguiente, (b) identifique la salida que pasa y (c) sea recogido
por la primera frase del capítulo siguiente.

| Transición | Última frase de Cᵢ | Primera frase de Cᵢ₊₁ | ¿Puente? |
|---|---|---|---|
| **1 → 2** (p. 5 → 6) | «RQ6. ¿Puede certificarse por bloque una arquitectura que encadene las tres capas…? (OE6)» | «La coalición seleccionada debe poder acoplarse a la carga y completar el transporte.» | **NO.** El cap. 1 termina en una lista; el cap. 2 abre reiniciando la motivación física ya dada en p. 1 ¶2, sin recoger ninguna RQ. La transición «problema → gap → pregunta → objetivo» que exige la sección S no existe: los objetivos aparecen de la nada y la relación RQ↔OE queda solo en los paréntesis de p. 4–5. |
| **2 → 3** (p. 7 → 8) | «…evalúa si la conclusión del modelo cinemático se sostiene en un motor de simulación 3D independiente.» (final de OE6) | «La hipótesis principal se contrasta mediante resultados parciales cuyos dominios no son intercambiables.» | **NO.** Cambio de objeto (objetivo → hipótesis) sin una sola frase de enlace. |
| **3 → 4** (p. 10 → 11) | «Un residual que no cierra, o una reproducción que invierte el resultado cualitativo, deja a H6 sin apoyo en ese bloque.» | «Se estudia una flota de AMR heterogéneos que forma coaliciones y transporta cargas entre una pose inicial y una pose objetivo.» | **NO**, y además **repetición**: esa primera frase reinicia la descripción del escenario ya dada en p. 1 ¶2 y p. 3 ¶3 (mini-introducción, ver AE). |
| **4 → 5** (p. 18 → 19) | «…la evidencia se limita a geometría y replay cinemático; no sustituye contacto, dinámica de ruedas ni validación de hardware.» | «Cada capa del transporte cooperativo certifica una propiedad distinta.» | **NO.** Además el orden es anómalo: Metodología **precede** al Marco teórico, de modo que el protocolo se declara antes de que el lector sepa contra qué literatura compara. Si ese orden es el impuesto por la plantilla VIU, el puente es **más** necesario, no menos: hace falta una frase del tipo «el protocolo anterior elige comparadores; el capítulo siguiente justifica por qué esos y no otros». No existe. |
| **5 → 6** (p. 33 → 34) | **No hay última frase.** La p. 33 es íntegramente la Tabla 5 (matriz industrial) con su pie. La última prosa del cap. 5 está en p. 32: «El marco normativo aplicable (VDA 5050, ISO 21423, ISO 3691-4, ANSI/A3 R15.08-3) no cubre esa combinación, según se detalla en el Anexo F.» | «La evaluación conecta la asignación lógica con la misión física mediante tres interfaces verificables.» | **NO, y es el peor de los siete.** El capítulo que establece la brecha —el que debe generar la necesidad de todo el capítulo 6— **termina en una tabla de 60 filas**, sin síntesis, sin declarar qué salida pasa al siguiente capítulo, sin nombrar una sola hipótesis. |
| **6 → 7** (p. 62 → 63) | **No hay última frase.** La p. 62 es §6.8 + la Tabla 23 de grado de cumplimiento; después de la tabla no hay prosa. | «La pregunta principal admite una respuesta condicionada.» | **NO.** Segundo capítulo que muere en una tabla. Es especialmente costoso aquí: la Tabla 23 y la Tabla 24 (p. 65) cubren el mismo terreno con **vocabularios distintos** (ver N), y una frase de puente habría resuelto la duplicación. |
| **7 → 8/Anexos** (p. 69 → 70 → 81) | «…lo que basta para exigir una cota continua, no muestreada, antes de cualquier prueba con hardware.» | (Referencias) / «Los estimandos y resultados principales de la memoria se enlazan con tablas o macros generadas…» | **La última frase de la tesis sí cumple BQ**: cierra científicamente, no con «se espera continuar trabajando». Es el único cierre del documento que la norma aprobaría sin reservas. |

**Puentes internos que sí existen y son buenos** (conviene registrarlos porque
son el modelo a replicar):

- p. 45 → 47: «El resultado no acredita contacto, estabilidad ni una arquitectura
  completamente vecinal; **SP2 vuelve a certificar el movimiento**» / «**SP2
  recibe una coalición cerrada de SP1** y certifica, en tres bloques
  encadenados, que puede moverse.» Cumple el ejemplo ideal de la sección F casi
  literalmente.
- p. 47 (pie Fig. 20) → 51: «**SP3 trata cada coalición como agente compuesto
  para el tráfico**» / «SP3 coordina rutas y reservas locales **después del
  certificado de ejecutabilidad de SP2**, tratando cada coalición como un agente
  compuesto.»
- p. 112 (anexo): «E7 toma las coaliciones restauradas como agentes compuestos y
  evalúa sus conflictos de ruta.»
- p. 44: «El umbral S_k ≥ d_k^srv puede cumplirse sin que los robots tengan
  puntos de contacto capaces de equilibrar el torque. **Ese contraejemplo motiva
  el certificado de E3.**»

**Puentes internos ausentes dentro del capítulo 6** (mismo defecto, a menor
escala):

| Transición interna | Problema | Página |
|---|---|---|
| §6.1 → §6.2 | El último párrafo de §6.1 («Las subsecciones siguientes evalúan las tres interfaces bajo esas restricciones») es genérico; no dice qué restricción concreta impone la revisión a SP1. | 41 → 42 |
| §6.4 → §6.5 | §6.4 termina en el piloto AWS («El protocolo completo… están en el Anexo I»); §6.5 abre con «SP1–SP3 certifican tres interfaces por separado», que es un resumen retrospectivo, no una necesidad generada por el piloto. | 53 → 54 |
| §6.5 → §6.6 | **Salto abrupto**: §6.5 termina con la Fig. 25 (trayectorias del demostrador extremo a extremo, 15 AMR); §6.6 abre «Un mundo pareado análogo al de E4 (Tabla 13)…», volviendo 12 páginas atrás a SP2. El tema E4 desaparece en p. 48 y reaparece en p. 59 (ítem de I: «¿Un tema desaparece y reaparece 12 páginas después?» — sí, exactamente 11). | 58 → 59 |
| §6.6 → §6.7 | §6.6 dice «Es una campaña independiente del piloto de almacén AWS de la Sección 4.5»; §6.7 abre «Las tres interfaces producen certificados distintos». Ninguna relación. | 59 → 60 |

---

## H. Títulos informativos — encabezados que prometen lo que el contenido no entrega

| Encabezado | p. | Qué promete | Qué entrega |
|---|---|---|---|
| **§4.5 «Validación estadística y CoppeliaSim»** | 14 | dos cosas bajo un solo título | Un párrafo de estadística (McNemar/Wilcoxon/Friedman/Holm) y tres párrafos que describen una **escena de almacén** sin relación con la estadística. Dos temas cosidos por una «y». Además, la escena descrita aquí (almacén AWS, 12 Pioneer) **no es** la que el §4.10 describe (paso estrecho, 4 AMR): son dos campañas distintas repartidas en dos subsecciones separadas por cinco subsecciones ajenas. |
| **§4.10 «CoppeliaSim: mundo pareado de paso estrecho (E4)»** | 18 | metodología | Correcto en contenido, pero colocado **después** del protocolo de revisión bibliográfica (§4.9), como si se hubiese añadido al final de la lista. |
| **§5.6 «Revisión académica e industrial»** | 29 | dos revisiones | El §4.9 (p. 18) y el §6.1 (p. 36) hablan de **tres** corpus (académico, industrial y **patentario**). El título de §5.6 omite el tercero, que sí aparece en el cuerpo del documento. Títulos paralelos desalineados. |
| **§6.1 «Cobertura del corpus, tendencia académica y actividad patentaria»** | 36 | un resultado del trabajo | Revisión de literatura. El encabezado es honesto, el **emplazamiento** no: seis páginas de bibliometría abren el capítulo titulado «Resultados y análisis». |
| **§6.5 «Juego de integración»** | 54 | la integración de SP1–SP3, culminación del trabajo | Cuatro lemas algebraicos **sobre geometrías nuevas que no son las de SP1–SP3**: dos coaliciones sobre una familia fija de curvas de Bézier (p. 55), una carga **circular** con cuatro contactos cardinales (p. 55), una factorización de potencial (p. 54) y una cota de presupuesto (p. 56). Ninguno ejecuta E1, E2, E3, E4, E6 ni E7. El propio texto lo reconoce en p. 56: «ninguno certifica que el sistema híbrido completo … alcance un óptimo global; no generalizan sin nueva demostración a otro número de coaliciones o de contactos». |
| **«Demostrador extremo a extremo»** (dentro de §6.5) | 56 | una cadena completa validada | Corrida única, n = 1, sin réplicas ni semillas (así lo dice el pie de la Tabla 20, p. 57), con **un tercer mecanismo de reclutamiento** («subasta distribuida vs. oráculo húngaro») distinto del de E1/E2 y del criterio agregado de Cargo. |
| **§7.6 «Recomendaciones y trabajo futuro»** + **§7.8 «Recomendaciones por dimensión»** | 66, 67 | dos veces lo mismo | Dos secciones de recomendaciones separadas por §7.7 «Cierre de OE6, H6 y RQ6». El lector recibe recomendaciones, luego el cierre de una hipótesis, luego más recomendaciones. |
| **§7.7 «Cierre de OE6, H6 y RQ6»** | 66 | — | Es el síntoma más visible de bloque añadido: RQ1–RQ5 se responden en §7.3 (p. 64) y RQ6 dos páginas después, en su propia sección; H1a–H5b se cierran en la Tabla 24 (p. 65) y H6 en la Tabla 25 (p. 67), cuyo título es literalmente «Estado final de H6, **en continuación de la Tabla 24**». |
| **Anexo A «Reproducibilidad y disponibilidad»** | 81 | dónde están los artefactos | Un párrafo declarativo. Ni un DOI, ni una URL, ni un hash, ni un nombre de repositorio. El encabezado promete disponibilidad y entrega una política. |
| **Anexo B.1 «Demostraciones complementarias de la etapa E2 (SP1)»** | 81 | demostraciones | Tres frases de alcance. La demostración está en B.2. |
| **Anexo C.2 «Demostraciones complementarias de la etapa E4 (SP2)»** | 83 | demostraciones | Dos frases de alcance. Las demostraciones están en C.3 y C.4. |
| **Anexo E.1 «Demostraciones complementarias de la etapa E7 (SP3)»** | 87 | demostraciones | Dos frases de alcance. Las demostraciones están en E.2–E.5. |
| **Anexo J.5 «Extension no ensayada: actualizacion de informacion por diferencias»** | 128 | — | El encabezado declara su propia irrelevancia. Debe eliminarse (decisión BZ). |
| **Anexo J.6 «Alcance y aporte»** | 129 | — | Discusión de novedad y prioridad. No es un anexo de demostraciones. |
| Encabezados de plantilla repetidos | 96–122 | — | «Problemas formales de referencia», «Métodos de comparación», «Diseño experimental», «Resultados», «Síntesis» se repiten como bloque idéntico en G.2.1 (pp. 97–102), H.1.1 (pp. 103–107), H.2.1 (pp. 108–112) e I.1.1 (pp. 118–122). Son títulos de contenedor, exactamente los que H prohíbe («Resultados», «Discusión»). |

---

## I. Reverse outline — primera frase de cada sección

### Capítulo 1 — Introducción (pp. 1–5)
- **1.** (p. 1) «La IFR registró 102 900 robots de servicio para transporte y logística en 2024…» → *abre con dato de mercado*
- **1.1** (p. 3) «Una revisión local consulta el estado del AMR y mensajes vecinales; el cierre entero y la infraestructura compartida añaden las dependencias globales que se declaran en la metodología.» → *define el contrato*
- *(bloque sin encabezado)* (p. 4) «**Impacto esperado.** El impacto científico previsto es una regla de composición entre capas…» → *inserción; rompe la secuencia mapa→pregunta*
- *(bloque sin encabezado)* (p. 4) «**Preguntas de investigación.** El trabajo se articula en torno a seis preguntas…»

*Lectura de la secuencia:* mercado → problema físico → literatura → contrato →
figura → mapa de la tesis → **impacto** → **RQ**. El impacto se interpone entre
el mapa y las preguntas. El orden natural es RQ antes de impacto (A→C→B, ítem
de I).

### Capítulo 2 — Objetivos (pp. 6–7)
- **2.** (p. 6) «La coalición seleccionada debe poder acoplarse a la carga y completar el transporte.»
- **2.1** (p. 6) «Desarrollar una arquitectura híbrida e interpretable que conecte revisiones estratégicas vecinales con cierre entero y guardias físicas…»
- **2.2** (p. 6) «OE1. Formalizar la transición desde la asignación homogénea uno a uno hasta las cuotas variables y el servicio heterogéneo.»

*Lectura:* OE1–OE5 son legibles desde el cap. 1. **OE6** (p. 7) introduce
«continuaciones físicamente admisibles», «estado aumentado» y «potencial exacto,
KKT, presupuesto de ejecución» — tres conceptos nuevos en un objetivo, que la
sección S prohíbe explícitamente («¿Hay OE que introducen conceptos nuevos?»).

### Capítulo 3 — Hipótesis (pp. 8–10)
- **3.** (p. 8) «La hipótesis principal se contrasta mediante resultados parciales cuyos dominios no son intercambiables.»
- **3.1** (p. 8) «HP. En una región donde la flota cubra la demanda, el certificado Cargo planar sea factible…»
- **3.2** (p. 8) «H1a. Realizabilidad estratégica…»
- **3.3** (p. 9) «La tabla asigna un criterio observable a cada predicción.»
- *(bloque sin encabezado)* (p. 10) «**H6.** Certificado por bloque bajo continuaciones admisibles…»

*Lectura:* H1a–H5b viven en §3.2 y su estimando en la Tabla 1 (p. 9). **H6 vive
fuera de ambas**: aparece en p. 10, después de la tabla que debía contenerlo,
con su propio párrafo «Estimando y regla de decisión». Es el mismo patrón de
bolt-on que §7.7 y la Tabla 25.

### Capítulo 4 — Metodología (pp. 11–18)
- **4.** (p. 11) «Se estudia una flota de AMR heterogéneos que forma coaliciones y transporta cargas entre una pose inicial y una pose objetivo.»
- **4.1** (p. 11) «El robot i es un uniciclo con estado qᵢ = (p_{x,i}, p_{y,i}, θᵢ) y entradas acotadas (vᵢ, ωᵢ).»
- **4.2** (p. 12) «En Cargo, los robots se acoplan a puestos conocidos y la carga se mueve como un cuerpo compuesto.»
- **4.3** (p. 13) «La arquitectura contiene tres subproblemas.»
- **4.4** (p. 14) «Cada mundo se genera una vez y se reutiliza entre tratamientos.»
- **4.5** (p. 14) «Cada mundo w = (s_w, ζ_w, σ_w) reúne escenario, factores y semilla, y se ejecuta con todos los métodos.»
- **4.6** (p. 15) «Sean R los robots y L las cargas.»
- **4.7** (p. 16) «Cada celda experimental reutiliza el mundo y la semilla entre métodos…»
- **4.8** (p. 17) «La Tabla 4 clasifica la salida que cada familia entrega a la capa siguiente.»
- **4.9** (p. 18) «La brecha que justifica este trabajo se sostiene sobre tres corpus con protocolos distintos…»
- **4.10** (p. 18) «Además del piloto de almacén de la Sección 4.5, una segunda escena de CoppeliaSim reproduce el juego de acoplamiento de E4…»

*Lectura:* la sección V exige
modelo→información→algoritmo→comparadores→escenarios→métricas→estadística. Aquí
el orden real es modelo (4.1–4.2) → **aporte por subproblema (4.3)** →
**escenarios y métricas (4.4)** → **estadística (4.5)** → **formulación general
(4.6)** → protocolo (4.7) → comparadores (4.8) → **revisión bibliográfica
(4.9)** → **una escena de simulador (4.10)**. La formulación general llega
**después** de las métricas que la usan, la estadística **antes** de los
comparadores, y las dos últimas subsecciones no son metodología del mismo tipo
que las ocho primeras. Cuatro inversiones A→C→B en ocho páginas.

*Además:* §4.7 termina (p. 17) con «esta campaña no ejecuta la composición exacta
de los mecanismos parciales de SP1 y SP2» y §4.8 abre con «La Tabla 4
clasifica…» — dos párrafos consecutivos sin relación (ítem de I).

### Capítulo 5 — Marco teórico y estado del arte (pp. 19–33)
- **5.** (p. 19) «Cada capa del transporte cooperativo certifica una propiedad distinta.»
- **5.1** (p. 19) «La asignación multi-robot de tareas (MRTA) clasifica relaciones entre robots, tareas y horizonte de decisión…»
- **5.2** (p. 21) «En el grafo de comunicación G_c(t) = (R, E_c(t)), λ₂(L) > 0 mide conectividad algebraica cuando la topología es no dirigida…»
- **5.3** (p. 23) «La conectividad del grafo certifica propagación de información; la rigidez geométrica conserva localmente la forma…»
- **5.4** (p. 24) «Los campos potenciales combinan atracción al objetivo y repulsión de obstáculos con bajo coste de cálculo…»
- **5.5** (p. 26) «El corpus se organiza por la propiedad que cada familia entrega a la capa siguiente.»
- **5.6** (p. 29) «La revisión se organiza en dos frentes con criterios de inclusión distintos.»

*Lectura:* §5.1–§5.4 cumplen el test T ejemplarmente — cada una agrupa por
problema, compara y **termina en una implicación para el diseño** (p. 20: «el
reclutamiento debe entregarles una composición mecánicamente admisible»; p. 24:
«cada una conserva su propio contrato físico»). §5.5 cierra la brecha. §5.6 es
un cuerpo extraño: cambia de registro (recuadro con «Brecha académica
defendible», p. 29), cambia de tipo de fuente (productos comerciales) y arrastra
pp. 30–33 de figuras y tablas. **El capítulo tenía su final natural en p. 28**
(«extenderla al sistema híbrido exigiría una prueba adicional») y continúa cinco
páginas más (ítem de I: «¿La sección termina donde debería?» — no).

### Capítulo 6 — Resultados y análisis (pp. 34–62)
- **6.** (p. 34) «La evaluación conecta la asignación lógica con la misión física mediante tres interfaces verificables.»
- *Interfaz y protocolo transversal* (p. 34) «El capítulo se lee como una cadena de certificados, no como tres algoritmos independientes.»
- *Unidad experimental y comparación* (p. 35) «Una unidad experimental es un mundo, una semilla y una configuración congelada.»
- *Contrato de evidencia* (p. 36) «La evidencia se eleva por el predicado más débil comprobado.»
- **6.1** (p. 36) «El mapa de cobertura que producen las tres revisiones decide qué comparadores son legítimos en SP1–SP3, antes de cualquier resultado experimental.»
- **6.2** (p. 42) «SP1 decide la composición y los contactos antes de autorizar el movimiento de una carga en tres etapas encadenadas…»
- **6.2.1** (p. 44) «E3 reemplaza la cobertura escalar por un certificado planar de puestos y wrench.»
- **6.3** (p. 47) «SP2 recibe una coalición cerrada de SP1 y certifica, en tres bloques encadenados, que puede moverse.»
- **6.4** (p. 51) «SP3 coordina rutas y reservas locales después del certificado de ejecutabilidad de SP2…»
- **6.4.1** (p. 52) «Una reserva lógica autoriza una celda; no prescribe una trayectoria continua.»
- **6.5** (p. 54) «SP1–SP3 certifican tres interfaces por separado.»
- **6.6** (p. 59) «Un mundo pareado análogo al de E4 (Tabla 13), no las 108 instancias que la tabla resume, se reproduce en CoppeliaSim…»
- **6.7** (p. 60) «Las tres interfaces producen certificados distintos.»
- **6.8** (p. 62) «La Tabla 23 contrasta cada objetivo específico con la evidencia de este capítulo y declara el grado alcanzado.»

*Lectura:* el bloque §6.2→§6.3→§6.4 (pp. 42–53) es **el mejor tramo del
documento**: causalidad, puentes y vocabulario estable. El orden causal que pide
la sección W (coalición → capacidad → wrench → movimiento → seguridad →
reparación → tráfico → integración) se cumple exactamente en esas 12 páginas.
Los defectos están en los extremos: §6.1 (literatura) al principio, §6.5 y §6.6
al final.

**Hallazgo grave de I en §6.7:** la sección titulada «Síntesis transversal»
contiene, en la p. 61, un resultado formal **nuevo** —Proposición 6.8, límite
informacional bajo partición, con demostración y un «Testigo concreto en E7»—
que no está bajo ningún encabezado numerado. La sección E de la norma prohíbe
expresamente que la salida de un capítulo «introduzca nuevas derivaciones». El
§7.7 (p. 67) después remite a esa proposición como «la razón formal» de la
ausencia de garantía global: es decir, un resultado central del argumento vive
en el rincón menos localizable del documento.

### Capítulo 7 — Conclusiones y recomendaciones (pp. 63–69)
- **7.** (p. 63) «La pregunta principal admite una respuesta condicionada.»
- **7.1** (p. 63) «SP1 caracteriza la formación estratégica mediante una regulación exacta de cuotas y dos interfaces de capacidad.»
- **7.2** (p. 64) «El objetivo general se cumple parcialmente.»
- **7.3** (p. 64) «RQ1. Recursos y penalización suficientes permiten cuotas exactas…»
- **7.4** (p. 65) «La Tabla 24 restringe cada estado al dominio ensayado.»
- **7.5** (p. 65) «Este trabajo no establece una función de Lyapunov común para el sistema híbrido completo.»
- **7.6** (p. 66) «Primero deben sustituirse las reglas empíricas de Cargo por los mecanismos de SP1–SP2 que se pretendan reclamar como integrados…»
- **7.7** (p. 66) «RQ6. Sí se certifica por bloque, dentro de los dominios que cada resultado declara…»
- **7.8** (p. 67) «Las recomendaciones enunciadas hasta aquí son de implementación.»
- **7.9** (p. 68) «Los límites anteriores se declaran por resultado.»

*Lectura:* §7.1–§7.5 son un espejo correcto de la Introducción (test BO
cumplido: problema→respuesta, RQ→respuesta, scope→límites). **§7.7 rompe la
secuencia**: inserta el cierre de un objetivo, una hipótesis y una pregunta —los
tres con índice 6— entre las recomendaciones (§7.6) y más recomendaciones
(§7.8). El orden reparado sería 7.3 + 7.7 (todas las RQ), 7.4 + Tabla 25 (todas
las H), 7.5, 7.6 + 7.8, 7.9.

*Test BP («no convertir conclusiones en segundo Discussion»):* **se incumple en
un punto**. §7.7 (p. 67) introduce un argumento nuevo —por qué una política
aprendida no sustituye a la arquitectura— que no aparece en ninguna parte del
cap. 6 y que pertenece al cap. 5.

### Anexos A–J (pp. 81–129)
- **A** (p. 81) «Los estimandos y resultados principales de la memoria se enlazan con tablas o macros generadas…»
- **B.1** (p. 81) «La alineación marginal de E2 se demuestra para preferencias continuas, umbrales positivos y una matriz de servicio fija durante cada decisión.»
- **B.2** (p. 81) «La regla de la cadena aplicada al potencial de (27) da…»
- **B.3** (p. 82) «El objetivo de (11) es coercivo y su Hessiano 2(GᵀQ_W G + ε I) es definido positivo.»
- **C.1** (p. 82) «Sea ξ_L = (vᵀ, ω)ᵀ, sea J = [0 −1; 1 0] y sea rᵢ el pivote de i en el marco de la carga.»
- **C.2** (p. 83) «E4 aporta dos resultados con dominios distintos.»
- **C.3** (p. 84) «Apílese ρ = (ρ₁,…,ρ_N) y sea B la matriz cuyas filas recogen b_{iaℓ}…»
- **C.4** (p. 85) «En una carta local de SE(2), ė^L_k = q̇^L_k.»
- **D** (p. 86) «Para una desviación unilateral xᵢ → x′ᵢ, la utilidad marginal de (40) satisface…»
- **D.1** (p. 86) «Considérese un perfil deficitario.»
- **E.1** (p. 87) «E7 formaliza tráfico sobre un grafo inflado y movimiento muestreado.»
- **E.2** (p. 87) «Fijadas r_{−i}, sea m_e^{−i} el número de sus rutas que usa e.»
- **E.3** (p. 87) «Si P₇(r) > 0 y θ₇ < ∞, la definición (50) proporciona una desviación…»
- **E.4** (p. 88) «Desde una zona libre, el arbitraje asigna un propietario único y conserva el testigo…»
- **E.5** (p. 88) «Sea S un conjunto finito de solicitantes persistentes.»
- **F** (p. 88) «Las Secciones 4.9 y 5.6 presentan las tres revisiones en formato mínimo…»
- **F.1** (p. 88) «La revisión académica se ejecuta como un embudo de cuatro capas…»
- **F.2** (p. 91) «El primer frente resuelve la coalición lógica mediante emparejamientos uno a muchos, subastas y juegos hedónicos…»
- **F.3** (p. 92) «La lectura relevante del mapa industrial es que dos líneas funcionales coexisten con precedentes comerciales propios.»
- **F.4** (p. 93) «Esta subsección conserva, sin abreviar, la lectura panel a panel de las figuras…»
- **G** (p. 95) «La Sección 6.2 resume E1 y E2 en formato compacto; aquí se desarrollan sin abreviar…»
- **G.1** (p. 95) «Se retoma el Teorema 6.1 de la Sección 6.2.»
- **G.2.1** (p. 96) «Dos coaliciones de igual cardinalidad pueden producir valores distintos de servicio S_k.»
- **H** (p. 102) «Las Secciones 6.3 y 6.6 presentan en formato compacto cuatro bloques…»
- **H.1.1** (p. 102) «E4 evalúa primero el acoplamiento mediante el estado de los uniciclos, la llegada segura y el agotamiento del horizonte.»
- **H.2.1** (p. 108) «Cuando falla un miembro…»
- **H.3.1** (p. 113) «El demostrador ejecuta reclutamiento, acoplamiento, transporte y recuperación sobre una misma planta planar.»
- **H.4** (p. 117) «La Sección 6.6 resume la reproducción en CoppeliaSim del mundo pareado de paso estrecho.»
- **I** (p. 117) «La Sección 6.4 presenta el juego de rutas (E7) en formato compacto…»
- **I.1.1** (p. 117) «Dos coaliciones que cumplen sus restricciones individuales pueden quedar enfrentadas en un pasillo sin compartir celda.»
- **I.2.1** (p. 122) «Industrial somete la arquitectura a modos de fallo que…»
- **J** (p. 123) «La Sección 6.5 enuncia cuatro resultados en formato compacto; sus demostraciones completas siguen a continuación.»
- **J.1** (p. 123) «Demostración de la Proposición 6.7. Los factores no incidentes no cambian y se cancelan.»
- **J.2** (p. 124) «Se consideran dos coaliciones Cargo, cada una contenida en un disco exterior de radio 1.05 m…»
- **J.3** (p. 126) «Se considera una carga circular de radio R = 0.45 m y cuatro contactos cardinales…»
- **J.4** (p. 127) «Definiciones usadas en la prueba. Un tubo es un intervalo maximal de tiempo durante el cual la continuación vigente no cambia…»
- **J.5** (p. 128) «La informacion I de la Ecuacion (18) admite una extension en la que cada AMR transmite al vecino solo los hechos nuevos respecto de la ultima version…»
- **J.6** (p. 129) «La revisión externa identifica antecedentes directos de las piezas genéricas…»

*Lectura:* F, G, H, I y J abren todas con **la misma plantilla** («La Sección 6.X
presenta … en formato compacto; aquí se desarrollan sin recortes…», pp. 88, 95,
102, 117, 123). Es signposting mecánico repetido cinco veces (test P: «¿Los
signposts añaden información o solo relleno?»). Y **B, C, D y E no la usan**:
cuatro anexos abren en seco con una ecuación. Dos convenciones de apertura
coexistiendo en el mismo bloque.

---

## N. Continuidad terminológica entre capítulos — **carga cognitiva**

La tabla canónica que la norma pide (concepto → nombre único) **sí existe de
facto** para los objetos físicos, y esa parte está bien:

| Concepto | Nombre único usado | ¿Estable? |
|---|---|---|
| robots | **AMR** | Sí, en las 129 páginas |
| objeto transportado | **carga** | Sí; «payload» solo como `c_i^pay` |
| grupo activo | **coalición** | Sí |
| modalidad principal | **Cargo** | Sí |
| referencia ideal | **oráculo** / «referencia central» | Casi: alterna dos nombres (pp. 17, 48, 52, 57) |
| viabilidad de esfuerzos | **factibilidad de wrench** | Sí |

**El problema no son seis taxonomías: son once identificadores activos y una
colisión.**

| # | Taxonomía | Cardinal | Dónde vive | Estado |
|---|---|---:|---|---|
| 1 | **SP1–SP3** subproblemas canónicos | 3 | todo el documento | activa |
| 2 | **SP0–SP8** etapas históricas | 9 | **Fig. 5(b), p. 27** | histórica, **colisiona con #1** |
| 3 | **E0–E8** campañas | 9 | Tabla 3 (p. 16), Figs. 18/20/21 | 6 activas, 4 muertas |
| 4 | **Etapa 1.3 / 1.4 / 2.1 / 2.3 / 2.4 / 3.1 / 3.3** | 7 | §6.2.1 (p. 44), G.2.1 (p. 96), H.1.1 (p. 102), H.2.1 (p. 108), H.3.1 (p. 113), I.1.1 (p. 117), I.2.1 (p. 122) | histórica, redundante con #3 |
| 5 | **H1a–H5b, HP, H6** | 9 | §3.2 (p. 8), p. 10, Tablas 24–25 | activa |
| 6 | **RQ1–RQ6** | 6 | p. 4–5, §7.3, §7.7 | activa |
| 7 | **OE1–OE6** | 6 | §2.2 (p. 6) | activa |
| 8 | **Cargo / caging** modalidades | 2 | §4.2 (p. 12) | activa (caging apenas) |
| 9 | **C₁, C₂, C₃** certificados de interfaz | 3 | **solo Fig. 10, p. 34** | muerta al nacer |
| 10 | **GO, CLOSE, SUPPORT, WRENCH, WHEELS, CONTACT, ROUTE** | 7 | **Ec. (8), p. 34**, citada una vez en p. 36 | **muerta al nacer** |
| 11 | **C0–C4** niveles de centralización | 5 | solo Fig. 8, p. 31 | muerta al nacer |
| + | sufijos de campaña `-C` (E2-C, E4-C, E6-C, E7-C), `sp0–sp8` minúsculas (p. 15, p. 113), `SP4_V4_COPPELIA_PAIRED_NARROW` (p. 59, 117), `SP1.N4` y `FULL–AGG` (p. 66) | — | pp. 15, 48–52, 59, 66, 113, 117 | ruido de repositorio |

**Colisión dura — SP1/SP2/SP3 significan dos cosas incompatibles:**

| | En todo el documento | En la Fig. 5(b), p. 27 |
|---|---|---|
| SP1 | formación de coaliciones | «Cardinalidad» |
| SP2 | ejecución y transporte | «Capacidad heterogénea» |
| SP3 | planificación y tráfico | **«Factibilidad/wrench»** |
| SP4 | *(no existe)* | «Transporte de pose» |

La misma figura lleva un aviso al pie —«Los códigos SP0–SP8 son etapas
históricas agrupadas en SP1–SP3»— que reconoce el problema y no lo resuelve: el
lector ve «SP3 · Factibilidad/wrench» a 25 páginas de distancia de «SP3 ·
planificación y tráfico». La norma N exige «no resucitar terminología histórica»;
aquí la terminología histórica **reutiliza los símbolos de la vigente con otro
significado**. Es el defecto terminológico más caro del documento.

**Segunda colisión — tres vocabularios de estado para la misma cosa:**

| Fuente | Vocabulario |
|---|---|
| «Guía de lectura y niveles de evidencia», p. xvi | Soportada · Parcial · Pendiente · Refutada |
| Tabla 23, p. 62 (grado de cumplimiento de OE) | Cumplido · Parcial · Teórico · Delimitado |
| Tabla 24, p. 65 (estado de H) | Sustentada · No adjudicada · Apoyo parcial · No sustentada · Apoyo teórico · Apoyo delimitado |

La p. xvi declara una «clave de estados empleada en la memoria» de cuatro
valores. Ninguna de las dos tablas de cierre la usa. Un tribunal que memorice la
clave de entrada no podrá leer las tablas de salida.

**Carga cognitiva, cuantificada.** Para leer el §6.8 (Tabla 23, p. 62) el lector
debe tener simultáneamente en memoria: seis OE, nueve H, la correspondencia
OE↔H, seis códigos E activos, tres SP, el vocabulario de grado de cumplimiento y
la diferencia entre Cargo y el demostrador extremo a extremo. Son **siete
sistemas de índices en una tabla de seis filas**. La sección AL lo pregunta
directamente: «¿El lector necesita recordar E4, SP2, H4, OE3 simultáneamente?»
— sí, y además RQ3.

**Veredicto N: FALLA.** Recomendación mínima: retirar las taxonomías 9, 10 y 11
(muertas al nacer, coste cero), sustituir la 4 por la 3, y **renombrar los ejes
de la Fig. 5(b)** para eliminar la colisión.

---

## O. Continuidad de símbolos

La sección de Nomenclatura (pp. xii–xv) es cuidadosa y en dos puntos **declara
sus propias colisiones**, lo que demuestra que el autor las conoce:

> «Las decoraciones de ρ separan magnitudes distintas: ρ_{ik} es una
> preferencia, ρ_D un parámetro primal–dual y ρ^W_k el residual de wrench.»
> (p. xiv)

> «Aquí **z** es la variable continua de decisión del bloque; **el mismo símbolo
> designa las fuerzas de contacto en el QP de caging y una sustitución auxiliar
> en la prueba de Bézier**, y cada uso se define en su punto de aparición.»
> (p. xv)

Declarar una colisión no la elimina. Inventario:

| Símbolo | Significados simultáneos | Páginas |
|---|---|---|
| **ρ** | preferencia continua · parámetro primal–dual · residual de wrench · mezcla avanzar/ceder/esperar del juego de vivacidad | xiv, 45, 47, 104 |
| **z** | variable de decisión del bloque de integración · fuerzas de contacto del QP de caging · sustitución auxiliar de Bézier · normalización de la prueba de Lyapunov | xv, 55, 85, 124 |
| **C** | coalición C_k · función de coste C(a) · certificados C₁–C₃ · niveles de centralización C0–C4 · Anexo C | 12, 31, 34, 42, 82 |
| **E** | campañas E0–E8 · incertidumbre E_X · recursos de ruta E⁷ᵢ, E⁸_{ir} · contribución de servicio e_{ik} · Anexo E | xiii, 16, 43, 54, 87 |
| **S** | servicio operacional S_k(x) · **reservas espacio-temporales del juego de integración** · conjunto de solicitantes | 43, 54, 88 |
| **Φ** | potencial de cuotas Φ₁ · de reparación Φ₆ · de rutas Φ₇ · potencial por factores Φ(d,z) | 42, 48, 51, 54 |
| **J** | coste social de referencia · coste local J_i del bloque · matriz [0 −1; 1 0] · Anexo J | xii, 54, 82 |

La Nomenclatura avisa sobre **S** («no confundir con el catálogo de rutas R⁷ᵢ de
SP3», p. xv), lo cual confirma que el riesgo se detectó. Los subíndices
numéricos de Φ (Φ₁, Φ₆, Φ₇) son en realidad **índices de campaña histórica**
disfrazados de subíndice matemático: Φ₆ es «el potencial de E6», no «el sexto
potencial». Eso ata la notación matemática a la taxonomía #3.

**Ítems de O:**

| Ítem | Resultado |
|---|---|
| Un símbolo mantiene significado | **NO** (siete colisiones) |
| Un mismo objeto no cambia de símbolo entre SP | **Sí**, se cumple (q_k^L, G_C, λ_C, W estables) |
| Reaparición después de 20 páginas con recordatorio | **Sí**: p. 47 reintroduce W^d = −K_P e^L − K_D q̇^L definido en p. 12 |
| Símbolos locales mueren al terminar su sección | **Parcial**: Y, X̂, Π^inc (Ec. 18, p. 54) no reaparecen nunca |
| El lector sabe cuándo cambia la planta | **Sí**, excelente: la columna «Planta» de la Tabla 3 (p. 16) lo declara etapa por etapa; y el aviso «el modelo es cuasiestático y anterior al transporte» (p. 44) |
| Variables del juego y físicas visualmente distinguibles | **NO**: ρ y z cruzan ambos dominios |
| Evitar 15 símbolos en una ecuación antes de explicar su función | **NO**: Ec. (18), p. 54, ocho símbolos nuevos en una línea; Ec. (8), p. 34, siete predicados nuevos |

**Veredicto O: PARCIAL.** La disciplina de planta es ejemplar; la de símbolos
del juego, no.

---

## BU. «Cold chapter test»

Simulación de abrir cada capítulo en frío, sin leer nada más.

| Cap. | ¿Entiendo su pregunta? | ¿Los símbolos esenciales? | ¿Cómo contribuye? | ¿Qué obtuvo? | ¿Sus límites? | Veredicto |
|---|---|---|---|---|---|---|
| **1** (p. 1) | Sí | Sí | Sí | n/a | Sí (p. 3) | **PASA** |
| **2** (p. 6) | Sí | OE6 no (p. 7: «continuaciones físicamente admisibles» sin definir) | Sí | n/a | Parcial | **PASA con reserva** |
| **3** (p. 8) | Sí | H6 no (p. 10: remite al Anexo J) | Sí | n/a | Sí | **PASA con reserva** |
| **4** (p. 11) | Sí | Sí, se definen in situ | Sí | n/a | Sí (Tabla 3) | **PASA** |
| **5** (p. 19) | Sí | Sí | Sí | Sí (§5.5) | Sí | **PASA**, el mejor del documento en este test |
| **6** (p. 34) | Sí | **No**: la Ec. (8) presenta siete predicados (GO, CLOSE, SUPPORT, WRENCH, WHEELS, CONTACT, ROUTE) que no se definen aquí ni después | Sí | Sí | Sí (Tabla 7) | **PASA con reserva** |
| **6.5** (p. 54) | **No** | **No**: Ec. (18) introduce X, d, X̂, E_X, I, Π^inc, S, t de golpe | **No**: la sección nunca dice por qué estos cuatro bloques y no otros | Sí | Sí (p. 56) | **NO PASA** |
| **6.6** (p. 59) | Sí | Sí | **No**: exige saber qué es E4 y qué contiene la Tabla 13, 11 páginas atrás | Sí | Sí | **NO PASA** |
| **7** (p. 63) | Sí | Sí | Sí | Sí | Sí | **PASA** |
| **Anexos G/H/I** | Sí (cada uno abre remitiendo a su sección del cuerpo) | Sí | Sí | Sí | Sí | **PASA** |
| **Anexos C/D/E** | **No**: abren en seco con una ecuación y una referencia a «(40)», «(27)», «(50)» que están en otro anexo | **No** | **No** | — | — | **NO PASA** |
| **Anexo J** | Parcial | **No** (arrastra la Ec. 18) | Parcial | Sí | Sí | **NO PASA** |

**Hallazgo adicional del test BU — doble numeración de los mismos resultados.**
El mismo teorema tiene **dos números** según dónde se lea:

| Resultado | En el cuerpo | En el anexo | Páginas |
|---|---|---|---|
| Alineación marginal del servicio | Proposición 6.1 | **Proposición G.1** | 43 / 99 |
| Potencial exacto y VE del juego de vivacidad | Proposición 6.3 | **Proposición H.1** | 47 / 104 |
| Disipación y estabilidad local de la pose | Teorema 6.2 | **Teorema H.1** | 48 / 105 |
| Potencial exacto y terminación (reparación) | Teorema 6.3 | **Teorema H.2** | 49 / 109 |
| Caracterización exacta de los Nash | Teorema 6.4 | **Teorema H.3** | 49 / 109 |
| Ineficiencia no acotada del peor Nash | Proposición 6.4 | **Proposición H.2** | 49 / 110 |
| Potencial exacto y mejora finita (rutas) | Teorema 6.5 | **Teorema I.1** | 51 / 119 |
| Nash sin conflictos bajo accesibilidad | Proposición 6.5 | **Proposición I.1** | 51 / 119 |
| Ausencia condicional de inanición | Proposición 6.6 | **Proposición I.2** | 51 / 120 |

Nueve resultados con dos identidades. Peor: los anexos B, G y J **sí** citan
correctamente la numeración del cuerpo («Se retoma el Teorema 6.1», p. 95;
«Demostración de la Proposición 6.7», p. 123; «Esto demuestra la Proposición
6.2», p. 82), mientras C, D, E y H usan la numeración propia («Así se prueba el
Teorema H.3», p. 86; «El Teorema H.1 completa el enlace», p. 83; «La Proposición
H.1 se restringe…», p. 85). **Dos convenciones de referencia cruzada en el mismo
bloque de anexos** — la firma más clara de texto ensamblado en fases (test BZ).

Y hay un resultado que existe **solo** en la numeración de anexo: el **Corolario
H.1** (cota temporal de reparación), enunciado en p. 110 pero **invocado antes**,
en p. 86 («La cota requiere las ventanas, trayectorias libres y velocidades
positivas del Corolario H.1»). Referencia hacia adelante a 24 páginas, a un
resultado que el cuerpo nunca menciona.

---

## BW. «Heading-only test»

Leyendo **solo** el índice (pp. iv–vii) y los pies de figura:

**Lo que se puede reconstruir:** hay tres subproblemas ordenados; SP1 forma
coaliciones, SP2 ejecuta y transporta, SP3 planifica tráfico; hay un
demostrador; hay una reproducción en CoppeliaSim; hay una síntesis transversal y
un grado de cumplimiento; las conclusiones cierran objetivos, RQ e hipótesis.
**Eso es una arquitectura intelectual legible.** Los títulos de §6.2–§6.4 son
descriptivos y paralelos, y §6.7 «Síntesis transversal» anuncia bien su función.

**Lo que NO se puede reconstruir, y por qué el test falla:**

1. **No se ve el hallazgo.** Ningún encabezado del documento enuncia un
   resultado. Todos son temáticos. La norma H propone precisamente el ejemplo
   «La capacidad nominal no garantiza factibilidad de wrench» — que es **la tesis
   central de este trabajo** (pp. 19, 44, 63, 64) y no aparece en ningún título.
2. **No se ve por qué existe §6.5.** «Juego de integración» (p. 54) no dice qué
   integra ni qué establece. Un lector de índice no puede saber que es la
   culminación… ni que no lo es.
3. **El índice arrastra códigos históricos.** «6.2.1 Etapa 1.4: certificado
   planar de contacto» (p. 44) exhibe la numeración interna de etapas en el
   índice; los anexos añaden «G.2.1 Etapa 1.3», «H.1.1 Etapa 2.1», «H.2.1 Etapa
   2.3», «H.3.1 Etapa 2.4», «I.1.1 Etapa 3.1», «I.2.1 Etapa 3.3». La sección BE
   prohíbe expresamente «códigos históricos» en el TOC.
4. **El índice llega a nivel 4.** `paragraph` está indexado: «E1 — regulación
   exacta de cuotas» (p. 42), «Académica» / «Industrial» (p. 29), «Ejecución
   común» (p. 113), «Resultados» (p. 100, 106, 111, 120), «Síntesis» (p. 102,
   107, 112, 122). BE fija el máximo en niveles 2–3. Hay **cuatro entradas de
   índice tituladas solo «Resultados»** y **cuatro tituladas solo «Síntesis»**:
   en el índice son indistinguibles entre sí.
5. **El índice ocupa 4 páginas** (PDF 5–8) frente al máximo de 2–3 que fija BE.

**Veredicto BW: FALLA.** Se sigue la arquitectura, no el argumento.

---

## BX. «Figure-only test»

28 figuras y 41 tablas. Clasificadas por función (test X, «una figura, una
función»):

| Función | Figuras | n | % |
|---|---|---:|---:|
| Contexto / modelo | 1, 2, 3, 4 | 4 | 14 % |
| **Literatura, bibliometría, patentes, industria** | 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 27 | **12** | **43 %** |
| Método / arquitectura (cajas y flechas) | 10, 11, 18, 19, 20, 21, 22, 23 | 8 | 29 % |
| **Resultado experimental propio** | 24, 25, 26 | **3** | **11 %** |
| Escena / captura | 28 | 1 | 4 % |

**El test falla por una razón inapelable: solo 3 de las 28 figuras muestran un
resultado del trabajo.** Un tribunal que hojee las figuras verá cuatro páginas
de mapas bibliométricos (pp. 27, 28, 30, 31), un cuadrante industrial (p. 32),
seis paneles de tendencias y patentes (pp. 37–40), ocho diagramas de cajas con
flechas (pp. 34, 36, 42, 43, 47, 51, 52, 54) y **tres gráficos de resultados**
(pp. 57, 57, 59). No verá ni una sola curva, barra o distribución de SP1, SP2 o
SP3: todo el resultado empírico de las tres campañas vive en tablas de números
(Tablas 10, 11, 13, 15, 16, 18).

Peor aún: **las tres figuras de resultado que existen pertenecen a las dos
campañas más débiles del documento** —el demostrador extremo a extremo (Figs. 24
y 25, p. 57, n = 1 sin réplicas) y la reproducción en CoppeliaSim (Fig. 26,
p. 59, una sola semilla)—. La jerarquía visual (test AB) está **invertida**: lo
que se ve son las campañas de una corrida; lo que solo se lee son las de 1560,
600, 480 y 360 mundos pareados.

Defectos adicionales de X:

- **Figs. 6, 7 y 9** (pp. 28, 30, 32) son mapas de dispersión con decenas de
  etiquetas superpuestas cuyos propios pies declaran que las posiciones «no
  representan calidad ni rendimiento» y «se desplazan solo para evitar solapes».
  Una figura cuyo pie niega su lectura métrica ocupa una página entera para no
  permitir ninguna conclusión.
- **Figs. 14, 15, 16, 17** (pp. 38–40) tienen pies de seis a ocho líneas con
  advertencias metodológicas; **Figs. 11, 22** (pp. 36, 52) tienen pies de una
  línea. La sección BB exige una convención única de pie: no la hay.
- **Fig. 26** (p. 59) es la única figura que acredita el resultado de OE6 y mide
  aproximadamente un tercio de página.

**Veredicto BX: FALLA.**

---

## BY. «Remove 20% test»

Cuerpo = 69 pp impresas. 20 % = **14 páginas**. Con anexos (118 pp sin
referencias), 20 % = 24 páginas. Lo que quitaría, por orden de coste cero a
coste creciente:

| Qué | Páginas | Ganancia |
|---|---:|---|
| **§6.1 completo** (pp. 36–41) → mover a §5.5/Anexo F | **6 pp** | El capítulo de Resultados empieza en SP1, como debe. Elimina la triple exposición de la revisión (§4.9, §5.6, §6.1). |
| **§J.5 «Extension no ensayada»** (p. 128) | 1 p | El propio texto dice que no sostiene ninguna afirmación. Decisión BZ: **eliminar**. |
| **§J.6 «Alcance y aporte»** (p. 129) | 1 p | Es nota interna; lo aprovechable (posicionamiento frente a antecedentes) ya está en §5.5 y Anexo F.2. |
| **Demostrador extremo a extremo** (pp. 56–58, Figs. 24–25, Tabla 20) | **3 pp** | Corrida única, n = 1, con un tercer mecanismo de reclutamiento que confunde. La p. 58 entera es una línea de ruta de carpeta. Elimina el conflicto de «dos demostradores». |
| **Figs. 6, 7 y 9** (pp. 28, 30, 32) | 3 pp | Tres mapas de dispersión ordinales cuyos pies niegan la interpretación métrica. La Tabla 5 y la Fig. 8 ya sostienen la brecha industrial y académica. |
| **Fila E0, E1, E5, E8 de la Tabla 3** (p. 16) + sus menciones (pp. 3, 7, 13, 15, 26, 44, 45, 65) | ~1 p acumulada | Cuatro campañas declaradas «procedencia, no evidencia». Retirar la taxonomía #3 para esas cuatro y hablar solo de las seis activas. |
| **§7.8 «Recomendaciones por dimensión»** (pp. 67–68) fundido en §7.6 | 1 p | Elimina la duplicación de secciones de recomendación. |
| **Anexo F.4** (pp. 93–94, «Discusión ampliada de cobertura, tendencia y patentes») | 2 pp | Es la tercera exposición del mismo material bibliométrico. |
| **Figs. 14 y 15** (pp. 38, 40) fundidas en una | 1 p | Ambas miden cuota temática por periodo con dos taxonomías distintas. |
| **Total** | **≈ 19 pp** | |

Con eso el cuerpo baja de 69 a ~57 pp y el capítulo 6 de 29 a 20 pp, con el
100 % de esas 20 dedicadas al trabajo propio. Nada de lo eliminado es un
resultado del trabajo.

**Observación de BH (consistencia de nivel de detalle).** El reparto actual del
capítulo 6 contradice la importancia declarada:

| Sección | pp. | Evidencia que sostiene |
|---|---:|---|
| §6.1 revisión | 6 | literatura de terceros |
| §6.5 juego de integración | 5 | 4 lemas + n = 1 |
| §6.2 SP1 | 5 | 1560 + 600 mundos pareados |
| §6.3 SP2 | 4 | 108 + 480 + 360 mundos pareados |
| §6.4 SP3 | 3 | 360 mundos pareados + 32 ejecuciones |
| §6.6 CoppeliaSim | 1 | n = 1 |

La revisión bibliográfica y los cuatro lemas de una corrida ocupan **11 páginas**;
las tres campañas que reúnen ~3000 mundos pareados ocupan **12**. Es el síntoma
exacto de BH: extensión proporcional al trabajo que costó producir, no a su
importancia para la tesis.

---

## BZ. «No-retazos test» — costuras específicas de este TFM

La norma lista catorce costuras a buscar. Resultado:

| Costura | ¿Presente? | Evidencia | Decisión pendiente |
|---|---|---|---|
| **E0/E1 históricos vs SP1 actual** | **SÍ** | p. 15: «E0, E1, E5 y E8 permanecen como procedencia y material de monografía»; siguen ocupando 4 de 10 filas de la Tabla 3 (p. 16) y aparecen en la nomenclatura (p. xiii: «etapa E0 de SP1», cuatro entradas) | **eliminar** de nomenclatura y Tabla 3 |
| **E2/E3 nomenclatura antigua** | **SÍ** | coexisten «E2» (p. 43), «Etapa 1.3» (p. 96), «SP2 Capacidad heterog.» (p. 27) para el mismo objeto | **unificar** en E2 |
| **SP2 con formaciones distintas según la época** | **SÍ** | E4 se llama E4 (p. 47), Etapa 2.1 (p. 102), sp2/sp3/sp6 (p. 113) y SP4_V4 (p. 59) | **unificar** |
| **Cargo con mecanismos distintos de SP1/SP2 teóricos** | **SÍ, y se declara 11 veces** | p. 113: «Su selección mediante líder, su criterio agregado y su reemplazo voraz difieren de los mecanismos evaluados en las etapas históricas sp2, sp3 y sp6»; p. 13, 17, 50 | **integrar** (sustituir reglas) o **reformular** el alcance; hoy se opta por declarar, que es la opción menos costosa |
| **Caging injertado** | **SÍ** | declarado y no validado en §4.2 (p. 12); ausente de todo el cap. 6 salvo **un lema algebraico sobre una carga circular** (p. 55) y **una carga «Caging»** en el demostrador de p. 56; el Resumen lo excluye de la evidencia confirmatoria (p. i) | **eliminar** del cuerpo o **mover** a trabajo futuro |
| **Coppelia añadido posteriormente** | **SÍ** | cuatro emplazamientos distintos: §4.5 (p. 14), §4.10 (p. 18), §6.6 (p. 59), H.4 (p. 117), **y dos escenas distintas** (almacén AWS y paso estrecho) que el texto tiene que desambiguar explícitamente en p. 59 («Es una campaña independiente del piloto de almacén AWS de la Sección 4.5») | **reformular**: una sola subsección de metodología con las dos escenas |
| **Revisión industrial añadida posteriormente** | **SÍ** | §5.6 «Industrial» (p. 29), Fig. 9 + Tabla 5 (pp. 32–33), F.3 (pp. 92–93); el título de §5.6 no la anuncia completa | **integrar** en §5.5 |
| **Patentes añadidas posteriormente** | **SÍ** | ausentes del título de §5.6 (p. 29); presentes en §4.9 (p. 18), Fig. 17 (p. 40), §6.1 (p. 41), F.4 (p. 93–95) | **mover** al Anexo F con un párrafo en §5.5 |
| **MegaJuego añadido posteriormente** | **SÍ, con su nombre de proyecto visible** | p. 57 (×3): `simulate_e2e_megagame.py`; **p. 58: la página entera es `thesis/resources/MROB_MegaGame_E2E_bundle/`** | **eliminar** las rutas; **mover** el demostrador a anexo o eliminarlo |
| **Atlas formal añadido posteriormente** | **SÍ (como «juego de integración»)** | §6.5 (p. 54) + Anexo J (pp. 123–129) + los símbolos de p. xv, sin ninguna preparación en los caps. 1 y 4; el Resumen lo llama «adicional» (p. i) | **integrar** en la Metodología o **mover** entero al anexo |
| **Hipótesis añadidas/reformuladas posteriormente** | **SÍ** | H6 fuera de §3.2 y de la Tabla 1 (p. 10); Tabla 25 «Estado final de H6, **en continuación de la Tabla 24**» (p. 67); §7.7 «Cierre de OE6, H6 y RQ6» como sección propia (p. 66) | **integrar**: H6 en §3.2 y en las Tablas 1 y 24 |
| **Vocabulario de taller** | **SÍ** | p. 35, Tabla 6: «**Elevar un claim** — Solo un **gate** aprobado cambia `PENDIENTE` o `PARCIAL` a `SOPORTADA`»; «**claim-ID**, supuesto, prueba o **artefacto** y destino»; p. 36: «qué afirmación puede cruzar cada **gate**» | **reformular** a castellano académico |
| **Resultados antiguos mezclados con activos** | **SÍ** | Tabla 3 (p. 16) mezcla las seis etapas activas con cuatro de monografía en la misma tabla, sin marca visual que las separe | **reformular** la tabla |
| **Supplemental construido copiando main** | **PARCIAL** | los anexos G/H/I declaran explícitamente qué **no** repiten («La figura didáctica y la tabla de métodos de E2 no se repiten aquí porque ya están en el cuerpo», p. 95; ídem pp. 102, 117) — **esto está bien resuelto**. Pero las Tablas 13/34, 15/37 y 18/41 **sí son duplicados literales** entre cuerpo y anexo (pp. 48/106, 49/111, 52/121), igual que las Tablas 10/32 (pp. 44/101) | **eliminar** la copia del anexo o convertirla en referencia |

**Costura decimoquinta, no prevista por la norma pero presente:** **§J.5 (p. 128)
está escrita sin un solo acento** en 8 líneas de texto, en un documento que los
lleva en las otras 128 páginas. Es un bloque pegado desde otra fuente sin pasar
por la revisión de idioma.

**Veredicto BZ: FALLA — 14 de 14 costuras presentes**, y en nueve de ellas la
decisión efectiva ha sido la quinta opción prohibida: «mantener porque ya
existe», con una nota de alcance en lugar de una decisión estructural.

---

## 1. Puentes ausentes entre capítulos — lista operativa

Recapitulación accionable de la sección F. **Siete transiciones de capítulo,
siete sin puente.**

| # | Punto exacto | Qué falta |
|---|---|---|
| 1 | **p. 5 → p. 6** (cap. 1 → 2) | Una frase que convierta RQ1–RQ6 en la necesidad de los OE. Hoy el vínculo existe solo como «(OE1)» entre paréntesis dentro de cada RQ, apuntando hacia adelante a algo no definido. |
| 2 | **p. 7 → p. 8** (cap. 2 → 3) | Una frase que diga «cada OE genera una predicción comprobable; las siguientes son esas predicciones». |
| 3 | **p. 10 → p. 11** (cap. 3 → 4) | Una frase que diga qué protocolo exige contrastar esas hipótesis. Hoy el cap. 4 reinicia la descripción del escenario. |
| 4 | **p. 18 → p. 19** (cap. 4 → 5) | Una frase que explique por qué, después del protocolo, hace falta el estado del arte (y no al revés). |
| 5 | **p. 32/33 → p. 34** (cap. 5 → 6) | **El más grave.** El cap. 5 termina en la Tabla 5 sin síntesis. Falta el párrafo tipo «de estas limitaciones se derivan las decisiones metodológicas siguientes» que exige la sección U, con la correspondencia explícita gap₁→SP1, gap₂→SP2, gap₃→SP3. |
| 6 | **p. 62 → p. 63** (cap. 6 → 7) | El cap. 6 termina en la Tabla 23 sin prosa. Falta una frase que entregue al cap. 7 la pregunta que queda abierta. |
| 7 | **p. 69 → p. 81** (cap. 7 → anexos) | El Anexo A abre sin declarar qué contienen A–J ni en qué orden. |

**Puentes internos ausentes** (mismo defecto, dentro del cap. 6): p. 41→42,
p. 53→54, **p. 58→59** (salto de la integración a E4, 11 páginas atrás),
p. 59→60.

---

## 2. Encabezados que prometen lo que el contenido no entrega

Ver la tabla completa en el test **H**. Los cinco de mayor coste:

1. **§6.5 «Juego de integración»** (p. 54) — promete la integración de SP1–SP3;
   entrega cuatro lemas sobre geometrías que no son las de SP1–SP3 (dos discos
   con curvas de Bézier, una carga circular con cuatro contactos cardinales) más
   un demostrador de n = 1.
2. **§4.5 «Validación estadística y CoppeliaSim»** (p. 14) — dos temas sin
   relación bajo un solo encabezado, y la escena descrita no es la de §4.10.
3. **§6.1 «Cobertura del corpus…»** (p. 36) — encabezado correcto, capítulo
   equivocado: 6 páginas de literatura abriendo «Resultados y análisis».
4. **Anexo A «Reproducibilidad y disponibilidad»** (p. 81) — ni un identificador,
   ni una URL, ni un hash.
5. **Anexos B.1 / C.2 / E.1 «Demostraciones complementarias…»** (pp. 81, 83, 87)
   — tres encabezados que anuncian demostraciones y entregan un párrafo de
   alcance.

Y los que **prometen dos veces lo mismo**: §7.6 «Recomendaciones y trabajo
futuro» (p. 66) frente a §7.8 «Recomendaciones por dimensión» (p. 67); §4.5
frente a §4.10 (CoppeliaSim); §4.9 frente a §5.6 frente a §6.1 frente a Anexo F
(las revisiones).

---

## 3. Mini-introducciones y mini-conclusiones repetidas (AE, AF)

### Mini-introducciones (AE)

**(a) La motivación general del problema se reinicia cuatro veces.** La norma
permite una sola: la del capítulo 1.

| Dónde | Texto | Ya dicho en |
|---|---|---|
| p. 1, ¶2 | «El problema cambia cuando una carga rebasa la capacidad individual o exige apoyo en varios puntos.» | — (correcto, es el original) |
| **p. 6, §2** | «La coalición seleccionada debe poder acoplarse a la carga y completar el transporte.» | p. 1 ¶2, p. 3 ¶1 |
| **p. 11, §4** | «Se estudia una flota de AMR heterogéneos que forma coaliciones y transporta cargas entre una pose inicial y una pose objetivo.» | p. 1 ¶2, p. 3 ¶4 |
| **p. 19, §5** | «Cada capa del transporte cooperativo certifica una propiedad distinta. La asignación entrega una composición nominal; la comprobación mecánica decide si esa composición puede realizar el wrench requerido…» | p. 1 ¶3 casi palabra por palabra |
| **p. 34, §6** | «La evaluación conecta la asignación lógica con la misión física mediante tres interfaces verificables. SP1 forma coaliciones y asigna contactos; SP2 ejecuta el transporte y repara fallos; SP3 reserva rutas…» | Resumen p. i, §4.3 p. 13 |
| **p. 63, §7** | «Los contratos por capas permiten formar coaliciones y el demostrador Cargo completa una misión en una planta planar reducida…» | p. 60 §6.7 |

**(b) La misma advertencia se reintroduce 11 veces.** «Cargo acredita
compatibilidad funcional, no la composición formal de las garantías de SP1–SP2»:
pp. **3, 8, 13, 17, 28, 47** (pie Fig. 20), **50, 60, 63, 64, 113**. La sección
AC permite tres apariciones (resumen, cuerpo, conclusión). Van once.

**(c) La advertencia de «campaña histórica / monografía / no adjudica» se
reintroduce 12 veces:** pp. **3, 7, 13, 15, 16, 26, 36, 44, 45, 65, 87, 122**.
Puede centralizarse en una sola tabla de alcance (test AC: «¿Se puede usar una
tabla de límites una sola vez?» — sí, y ya existe: la Tabla 3, p. 16).

**(d) Plantilla de apertura de anexo repetida cinco veces**, literalmente la
misma estructura en pp. **88, 95, 102, 117, 123**:

> «La Sección 6.X presenta … en formato compacto; aquí se desarrollan sin
> recortes la metodología, el diseño experimental y la discusión. La figura
> didáctica y la tabla de métodos no se repiten aquí porque ya están en el
> cuerpo.»

**(e) Recuadro «Resultado y alcance: demostrado para…» repetido 14 veces**:
pp. **42, 43, 45, 47, 49, 51, 54, 55, 56, 61** (cuerpo) y **98, 104, 110, 119**
(anexos, con el mismo texto que el cuerpo). En las cuatro apariciones de anexo
el recuadro es **copia literal** del que ya está en el cuerpo.

**(f) Mini-introducción por bloque de SP repetida tres veces** con la misma
sintaxis: «SP1 decide la composición y los contactos **antes de autorizar el
movimiento** … en **tres etapas encadenadas**» (p. 42); «SP2 recibe una coalición
cerrada de SP1 y certifica, en **tres bloques encadenados**, que puede moverse»
(p. 47); «SP3 coordina rutas y reservas locales … El razonamiento completo …
se conservan en el Anexo I» (p. 51). Aquí la plantilla **ayuda** (paralelismo) y
la recomendación es conservarla; se registra por completitud.

### Mini-conclusiones (AF)

| Dónde | Texto | ¿Justificada? |
|---|---|---|
| p. **60**, §6.7 «Síntesis transversal» | cierra las tres interfaces | **Sí** — cierra una pregunta y cambia de nivel |
| p. **102**, «Síntesis» de G.2.1 | «La heterogeneidad rompe la equivalencia entre cardinalidad y cobertura…» | **No** — repite lo ya dicho en p. 44 |
| p. **107**, «Síntesis» de H.1.1 | «Para una instantánea congelada, el juego posee un potencial exacto fuertemente convexo…» | **No** — repite la Prop. 6.3 / H.1 |
| p. **112**, «Síntesis» de H.2.1 | «Con reserva suficiente y una penalización por encima del umbral…» | **Parcial** — su última frase sí es puente a E7 |
| p. **122**, «Síntesis» de I.1.1 | «El potencial exacto garantiza terminación de las mejoras de ruta…» | **No** — repite el Teorema 6.5 / I.1 |

Cuatro encabezados idénticos titulados «Síntesis» que resumen resultados **ya
enunciados como teoremas dos veces** (en el cuerpo y en el anexo). La sección AF
permite la síntesis solo cuando «cierra una pregunta, cambia el nivel de
abstracción o prepara el siguiente bloque»: solo la de p. 112 lo hace.

Además, **doble cierre del capítulo 6**: §6.7 «Síntesis transversal» (p. 60) y
§6.8 «Grado de cumplimiento frente a objetivos e hipótesis» (p. 62) cierran dos
veces; y §6.8 se solapa con §7.2 y la Tabla 24 (p. 65), que vuelven a declarar
el cumplimiento de los mismos OE e H con **otro vocabulario**.

---

## 4. Dónde la narrativa implica que SP1+SP2+SP3 se validaron como una cadena

Ésta es la tensión más delicada del documento, porque el propio texto contiene
**la refutación explícita** de lo que otras frases sugieren. Las declaraciones
honestas son once (pp. 3, 8, 13, 17, 28, 47, 50, 60, 63, 64, 113) y están bien
escritas. El problema es que **conviven con doce formulaciones que implican lo
contrario**, y el lector medio retendrá la implicación visual y estructural
antes que la nota de alcance.

### Implicaciones de cadena validada

| # | Página | Texto o elemento | Por qué implica cadena validada |
|---|---|---|---|
| 1 | **p. 34** | «El capítulo se lee como **una cadena de certificados**, no como tres algoritmos independientes. … una salida solo habilita la comprobación siguiente.» | Declara que el capítulo **es** una cadena ejecutada. Lo que el capítulo contiene son tres campañas independientes sobre plantas distintas (Tabla 3, p. 16) que nunca se ejecutan encadenadas. |
| 2 | **p. 34, Ec. (8)** | `GO_k = CLOSE_k ∧ SUPPORT_k ∧ WRENCH_k ∧ WHEELS_k ∧ CONTACT_k ∧ ROUTE_k` | Una conjunción lógica de seis predicados presentada como «la autorización ejecutable». Sugiere que existe un sistema que evalúa los seis. No existe: ningún experimento del documento evalúa esa conjunción, y los seis predicados no vuelven a aparecer. |
| 3 | **p. 36** | «La Ecuación (8) es el contrato de avance que **SP1–SP3 deben satisfacer conjuntamente** para autorizar cada transición.» | «Conjuntamente» afirma una satisfacción simultánea que ninguna campaña comprueba. |
| 4 | **p. 34, Fig. 10** | Diagrama SP1 →C₁→ SP2 →C₂→ SP3, «Cada flecha transmite un certificado con dominio explícito» | El diagrama muestra un flujo ejecutado. El aviso «Sin transferencia automática de optimalidad, estabilidad o seguridad» está dentro de la figura, en cuerpo menor, y niega la transferencia de **garantías**, no la ejecución de la cadena. |
| 5 | **p. 7, OE6** | «**Integrar SP1–SP3** en una arquitectura común de continuaciones físicamente admisibles» | El objetivo promete integración de los tres SP. Lo que §6.5 entrega no toca ninguno de los mecanismos de SP1–SP3. |
| 6 | **p. 54, §6.5** | «SP1–SP3 certifican tres interfaces por separado. El juego de integración **las conecta** mediante un esquema híbrido» | «Las conecta» en presente indicativo. Los cuatro bloques que siguen usan geometrías nuevas (dos discos con Bézier, carga circular con 4 contactos) que no son las de E1–E7. |
| 7 | **p. 66, §7.7** | «El juego de integración **conecta SP1–SP3** con cuatro resultados demostrados algebraicamente y verificados numéricamente» | Repite la afirmación en las conclusiones, que es donde más pesa. Ninguno de los cuatro resultados instancia un mecanismo de SP1, SP2 ni SP3. |
| 8 | **p. 56** | Encabezado **«Demostrador extremo a extremo»** | «Extremo a extremo» es precisamente el término que el resto del documento niega («una garantía extremo a extremo requeriría demostrar su composición», p. 3). |
| 9 | **p. 57, Tabla 20** | Título: «**Escenario extremo a extremo**: certificado contra oráculo o cota conocida» | El pie aclara «corrida única, n = 1, sin réplicas», pero el título de la tabla —lo que se lee al hojear— afirma end-to-end. |
| 10 | **p. i, Resumen** | «SP1 regula cuotas… SP2 revela… En SP3, la reserva reduce… **Cargo completa casi todas las misiones**…» | La secuencia de cuatro frases en cascada sugiere una progresión ejecutada. La salvedad («sin ejecutar como una sola cadena todos los mecanismos teóricos») llega **al final de la cuarta frase**, en subordinada. |
| 11 | **p. 63, §7.1** | «**Cargo combina las seis etapas** mediante reglas propias del ejecutor y alcanzó una tasa de misión 0.997» | «Combina las seis etapas» precede a la cifra de éxito. La salvedad llega tres frases después. La secuencia narrativa (test BL, «resultado antes que decimales») coloca aquí la implicación antes de la corrección. |
| 12 | **p. 64, §7.2** | «se demuestra una **composición funcional planar**» | «Composición demostrada» es exactamente lo que el resto del documento niega. La palabra correcta sería «coexistencia» o «compatibilidad», que es la que usa §6.7 (p. 60): «acredita **coexistencia funcional** en su banco numérico». |

### Las once declaraciones correctoras (para contraste)

pp. **3** («Como sustituye parte de los mecanismos parciales de SP1 y SP2, sus
resultados no constituyen una validación integrada de ambos subproblemas»),
**8** (HP), **13** (§4.3: «no ejecuta un único juego común a SP1–SP3»),
**17** (§4.7), **28** (§5.5), **36** (Tabla 7, columna «Frontera explícita»),
**47** (pie Fig. 20: «Cargo integra funcionalmente los mecanismos, **no reproduce
las pruebas de E4 y E6 como una composición demostrada**» — la formulación más
precisa del documento), **50**, **60** (§6.7 + Tabla 22), **63**, **64**, **113**.

### Diagnóstico

El documento **no miente**; **reparte la verdad de forma asimétrica**. Las
afirmaciones de cadena ocupan los lugares de máxima visibilidad —encabezados
(p. 56), títulos de tabla (p. 57), aperturas de capítulo (p. 34), figuras
(p. 34), objetivos (p. 7) y conclusiones (pp. 63, 64, 66)— mientras las
correcciones viven en subordinadas, pies de figura y columnas de «límite». Eso
incumple el criterio BN («separar hechos e interpretación») en su espíritu: el
lector que hojea recibe una tesis integrada; el que lee línea a línea recibe la
tesis real.

**Reparación de coste mínimo** (sin tocar ninguna cifra ni ningún resultado):

1. p. 34: cambiar «El capítulo se lee como una cadena de certificados» por «El
   capítulo evalúa por separado los tres eslabones de una cadena que este trabajo
   **no ejecuta como tal**».
2. p. 36: sustituir «deben satisfacer conjuntamente» por «deberían satisfacer
   conjuntamente en un sistema desplegado».
3. p. 56 y p. 57: retitular «Demostrador extremo a extremo» → «Escenario
   ilustrativo de una corrida (n = 1)».
4. p. 54 y p. 66: sustituir «las conecta» / «conecta SP1–SP3» por «propone un
   marco común para conectarlas, instanciado en cuatro bloques acotados».
5. p. 64: sustituir «se demuestra una composición funcional planar» por «se
   observa coexistencia funcional en una planta planar».
6. Eliminar la Ec. (8) y su vocabulario GO/CLOSE/… o convertirla en objetivo
   declarado de trabajo futuro; hoy es una promesa que nada del documento cumple.

---

## CA. Scorecard final de fluidez

Escala de la norma: 0 / 1 / 2 por dimensión, máximo **24**. Umbral de cierre:
**22/24** por capítulo y **cero ceros** en el documento.

| Dimensión | C1 | C2 | C3 | C4 | C5 | C6 | C7 | Anexos |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Propósito | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 |
| Dependencia anterior | 2 | 1 | 1 | 1 | 1 | 2 | 2 | 1 |
| Pregunta local | 1 | 1 | 1 | 1 | 2 | 1 | 2 | 1 |
| Estructura | 1 | 2 | 1 | **0** | 1 | 1 | 1 | **0** |
| Terminología | 1 | 1 | 1 | 1 | **0** | 1 | 1 | **0** |
| Párrafos | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 |
| Transiciones | 1 | **0** | **0** | 1 | **0** | 2 | 1 | 1 |
| Figuras | 2 | 1* | 1* | 1 | 1 | 1 | 1* | 1 |
| Síntesis | 1 | **0** | **0** | **0** | **0** | 2 | 2 | 1 |
| Voz | 2 | 2 | 2 | 2 | 1 | 1 | 2 | **0** |
| Densidad | 2 | 2 | 2 | 1 | **0** | 1 | 2 | 1 |
| Conexión global | 2 | 2 | 2 | 1 | 2 | 1 | 2 | 1 |
| **TOTAL /24** | **19** | **16** | **15** | **12** | **12** | **17** | **20** | **9** |

\* Capítulos sin figuras: se puntúa 1 (la ausencia es defendible en capítulos de
2–7 pp); no se penaliza como «decorativas».

**Media: 15,0 / 24.** **Ningún capítulo alcanza 22.** **Seis de los ocho bloques
tienen al menos un 0.**

### Justificación de cada 0

| Bloque | Dimensión | Motivo | Página |
|---|---|---|---|
| C2 | Transiciones | sin puente de entrada ni de salida | 6, 7 |
| C2 | Síntesis | el capítulo acaba en mitad de la lista de OE | 7 |
| C3 | Transiciones | sin puente de entrada ni de salida | 8, 10 |
| C3 | Síntesis | acaba en el estimando de H6 | 10 |
| C4 | Estructura | 10 subsecciones; orden de V violado en cuatro puntos; §4.5 mezcla dos temas; §4.10 añadida al final | 11–18 |
| C4 | Síntesis | acaba en §4.10 sin cierre | 18 |
| C5 | Terminología | **Fig. 5(b) redefine SP1/SP2/SP3 con otro significado** | 27 |
| C5 | Transiciones | **el capítulo termina en la Tabla 5 sin prosa de cierre** | 33 |
| C5 | Síntesis | ídem | 33 |
| C5 | Densidad | pp. 27–33: siete páginas consecutivas de figuras y tablas a página completa | 27–33 |
| Anexos | Estructura | doble numeración de nueve resultados; J.5 y J.6 no son demostraciones; Corolario H.1 citado 24 pp antes de existir | 83, 86, 104–120, 128–129 |
| Anexos | Terminología | «Etapa 1.3/2.1/3.1», `sp2/sp3/sp6`, `SP4_V4`, `legacy/results/sp4/` | 96–122 |
| Anexos | Voz | **§J.5 sin acentos**; §J.6 en registro de nota interna | 128, 129 |

### Lectura de la scorecard

- **C7 (20/24)** es el capítulo más sólido pese a la fragmentación de §7.6–§7.8:
  responde en el mismo vocabulario de la pregunta, cierra el círculo con la
  Introducción y su última frase cumple BQ.
- **C1 (19/24)** pierde sobre todo en el orden interno (impacto antes que RQ) y en
  la ausencia de puente.
- **C6 (17/24)** contiene el mejor tramo del documento (pp. 42–53) y los dos
  peores (§6.1 al principio, §6.5–§6.6 al final).
- **C4 y C5 (12/24)** son los que más ganarían con reparaciones baratas: un
  párrafo de puente al final de cada uno y el reordenamiento de §4.6 antes de
  §4.4 suben ambos a 16–17 sin tocar una cifra.
- **Anexos (9/24)** es el bloque que requiere una decisión estructural, no una
  reescritura: unificar numeración, eliminar J.5, reubicar J.6, retirar las
  tablas duplicadas.

### Tres reparaciones que más suben la nota por página tocada

1. **Siete párrafos de puente** (uno por transición de capítulo, ~60 palabras
   cada uno), más los cuatro internos del cap. 6. Coste: media página. Efecto:
   +2 en «Transiciones» y +1–2 en «Síntesis» en cinco capítulos → media de
   15,0 a ~17,5.
2. **Unificar la numeración de teoremas** (eliminar Teorema/Proposición H.1–H.3,
   I.1–I.2, G.1, H.2 y usar solo 6.x) y retirar «Etapa N.N» de los siete
   encabezados. Coste: búsqueda y reemplazo. Efecto: Anexos de 9 a 13.
3. **Mover §6.1 al capítulo 5 y §6.5 al Anexo J**, dejando en §6.5 un párrafo de
   una página que enuncie los cuatro certificados y remita. Coste: reubicación
   sin reescritura. Efecto: C6 de 17 a 20; el capítulo de Resultados pasa a ser
   100 % trabajo propio y su centro de gravedad cae sobre SP1–SP3.

---

## Anexo de esta auditoría — otros tests de la norma aplicados de pasada

| Sección | Hallazgo | Página |
|---|---|---|
| **BD** (front matter) | La norma dice literalmente «17 páginas antes de la Introducción me parece demasiado». Este documento tiene **exactamente 17** (PDF 1–17). | PDF 1–17 |
| **BE** (TOC) | Índice de 4 páginas (máx. 2–3); indexa nivel `paragraph`; cuatro entradas «Resultados» y cuatro «Síntesis» indistinguibles; códigos históricos «Etapa N.N» visibles. | PDF 5–8 |
| **Z / BC** (equilibrio de página) | **p. 58: página entera con una sola línea**, y esa línea es una ruta de carpeta. **p. 46: página entera con una tabla de 3 filas.** | 46, 58 |
| **AB** (jerarquía de importancia) | La revisión bibliométrica (11 figuras) compite visualmente con los resultados propios (3 figuras) y gana. | 27–41 vs 57–59 |
| **AC** (economía de repetición) | 11 repeticiones de la salvedad de Cargo; 12 de la salvedad de monografía; 14 recuadros «Resultado y alcance». | ver AE |
| **AD** (redefiniciones) | Nueve resultados enunciados dos veces con dos numeraciones; cuatro tablas duplicadas literalmente entre cuerpo y anexo (13/34, 15/37, 18/41, 10/32). | 44–52 vs 101–121 |
| **AG / BR** (voz única) | La voz es **notablemente uniforme** en 128 de 129 páginas: mismo registro, «se» impersonal consistente, misma forma de reconocer límites. Dos excepciones: el recuadro «Brecha académica defendible» (p. 29) y **§J.5 sin acentos** (p. 128). | 29, 128 |
| **AW** (integración como culminación) | La norma exige anunciarla en Introducción, diagrama conceptual, Metodología, resultados parciales y culminación. Presente en: **Objetivos (OE6, p. 7)**, **Hipótesis (H6, p. 10)**, **Nomenclatura (p. xv)**, **Resultados (§6.5, p. 54)**, **Anexo J**. **Ausente en Introducción (cap. 1) y en Metodología (cap. 4)** — los dos lugares que la norma considera obligatorios. El Resumen la llama «adicional» (p. i). | i, 7, 10, 54 |
| **AX** (mismo ejemplo conductor) | **No existe.** Cada etapa usa su propio escenario: E2 usa 4 robots didácticos (Fig. 19, p. 43), E4 usa 4–12 uniciclos, E7 usa 2–4 coaliciones en cuadrícula, Cargo usa 1 carga y 1 fallo, el demostrador E2E usa 15 AMR y 3 cargas, CoppeliaSim usa 12 Pioneer P3-DX o 4 AMR. Seis escenarios distintos. El escenario conductor que la norma propone —carga industrial de 3 AMR, paso estrecho, fallo de un miembro— **es exactamente el de la Fig. 1 (p. 2)** y no se vuelve a usar nunca. | 2, 43, 50, 56, 59 |
| **AY** (figuras ancla) | Las Figs. 10, 18, 20, 21, 23 comparten estilo (cajas «certifica / no certifica») y funcionan como ancla visual. **Esto está bien resuelto** y es el mejor activo de identidad gráfica del documento. | 34, 42, 47, 51, 54 |
| **BO** (conclusiones como espejo) | Problema→respuesta ✓ (p. 63); RQ→respuesta ✓ (p. 64, 66); Gap→qué cerramos **parcial** (§5.5 no reaparece con su vocabulario en el cap. 7); Contribución prometida→lograda ✓ (pp. 6 vs 63); Scope→límites ✓ (pp. 3 vs 65); Impacto esperado (p. 4)→implicaciones **parcial** (§7.8, p. 67, retoma científico/económico/social pero sin nombrar la p. 4). | 4, 63–68 |
| **BQ** (última frase) | «…el verificador registró dos violaciones de barrera bajo el modelo declarado, lo que basta para exigir una cota continua, no muestreada, antes de cualquier prueba con hardware.» **Cumple.** Es exactamente el tipo de cierre que la norma pide. | 69 |
| **Vocabulario de taller** | «Elevar un claim», «gate aprobado», «claim-ID», «artefacto» en la Tabla 6 (p. 35) y en p. 36. | 35, 36 |
