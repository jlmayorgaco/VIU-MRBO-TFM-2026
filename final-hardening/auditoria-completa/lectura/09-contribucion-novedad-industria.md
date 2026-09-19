# Auditoría de contribución, novedad, estado industrial, patentes y trabajo futuro

**Criterio:** `pre-thesis/guidelines/01-auditoria-maestra.md`, bloques 10 (líneas 141–152),
11 (153–170), 14 (206–220), 15 (221–235) y 38 (644–658).
**Artefacto:** `pre-thesis/build-v2/main-v2.pdf`, 146 páginas; fuentes en
`final-hardening/census.json`.
**Fecha:** 2026-09-19.

## Base de medición

- **Página impresa = página PDF − 17**, verificado en tres anclas: Introducción en la
  impresa 1 → PDF 18; §7.1 en la impresa 63 → PDF 80; J.6 en la impresa 129 → PDF 146.
  El material preliminar conserva numeración romana (Resumen = p. i = PDF 2).
  En adelante se cita **p. N** para la impresa y se añade **(PDF M)** cuando el
  hallazgo exige localizar la página física.
- **Extracción**: capa de texto completa del PDF, página a página (`fitz`), 307 KB.
  Todos los recuentos de este informe son sobre ese volcado, no sobre los `.tex`.
  Cada frase citada se reproduce tal como se imprime, con su partición de guion
  deshecha.
- **Verificación de recuentos**: los diecisiete términos de prioridad del bloque 11 se
  contaron sobre el documento completo, incluidos anexos y bibliografía. Las catorce
  apariciones de `ontribuci` se listan una a una más abajo; no hay muestreo.
- **Alcance**: este informe juzga argumentos, no tipografía ni aritmética. Cuando un
  hallazgo es numérico (denominadores patentarios, sensibilidad +20,9) se cita la
  página donde el número se imprime y la página donde se declara su alcance.

---

## Resumen de la medición

| Bloque | Frente | Veredicto |
|---|---|---|
| 10 | Contribuciones científicas | **No existe lista de contribuciones en ninguna parte del documento.** La palabra «contribución» se usa en sentido tesis **dos veces en 146 páginas**: p. i y p. 129 |
| 11 | Originalidad y novedad | **Cero reclamaciones de prioridad.** Ninguna frase es sobreafirmación. El problema es el opuesto y es grave: la contribución está infradeclarada hasta la invisibilidad |
| — | Brecha frente a dependencias globales | La brecha (p. 29) y las dependencias globales (p. 16) **no se contradicen, pero nunca se citan entre sí**. La reconciliación existe y está a 13 y 28 páginas de distancia |
| 14 | Estado industrial | **Proporcionado.** Es el mejor de los tres corpus. Dos defectos reales: ninguna fila tiene verificación independiente y el formato no separa despliegue de catálogo |
| 15 | Patentes | Protocolo correcto y dos análisis de sensibilidad reales. **Una celda sobreleída:** «Confirma pertinencia industrial» (p. 41) contradice a la Tabla 27 (p. 89) |
| 38 | Trabajo futuro | **No es una lista de deseos:** cada ítem deriva de una limitación declarada. Defecto: está repartido en cinco lugares, con **dos «primeros» en competencia**, y sin distinguir ingeniería de investigación |

---

# 1. Contribuciones científicas (bloque 10)

## 1.1. ¿Puede enunciarse la contribución en una frase con las palabras del documento?

Sí, exactamente una vez, y está en el Resumen:

> **«La contribución es una arquitectura verificable de contratos y juegos locales,
> más una composición funcional planar.»** — p. i (PDF 2)

Esa frase es gramaticalmente una respuesta y argumentalmente ninguna. No nombra un
mecanismo, no nombra un teorema, no nombra una cifra y no dice qué predicado verifica
la arquitectura verificable. Sustituida por «la contribución es una arquitectura de
software bien documentada» seguiría siendo verdadera. Un tribunal que la oiga tiene que
preguntar qué contratos, y el documento no vuelve a responder hasta la página 129.

La segunda frase existe y es mucho mejor:

> **«La contribución candidata más coherente es la contabilidad certificada de valor
> sobre revisiones atómicas físicamente ejecutables: qué transición existe, qué estado
> y recursos consume, qué coste común mejora, qué cota lo respalda y cómo conservar
> seguridad y progreso mientras se calcula.»** — p. 129 (PDF 146)

Esa frase sí es una contribución: identifica el objeto (la contabilidad de valor),
su unidad (la revisión atómica físicamente ejecutable) y sus cinco columnas
obligatorias. **Está en la última página del documento, dentro del Anexo J, precedida
de «No se reclama originalidad de esos bloques» y calificada de «candidata».**

Ese es el hallazgo central de esta auditoría. El enunciado más preciso de lo que el
trabajo aporta está colocado donde ningún tribunal lo leerá, y calificado con un
adjetivo que lo retira mientras lo enuncia.

## 1.2. Verificación: ¿hay un párrafo «Contribuciones principales» en la introducción?

**Confirmado: no lo hay.** Y la revisión previa se quedó corta — no lo hay en ninguna
parte del documento.

El índice (pp. iv–viii, PDF 5–8) no contiene ningún epígrafe «Contribuciones». Los dos
únicos títulos que prometen el contenido son:

- **§4.3 «Aporte y validación por subproblema»** (p. 13, PDF 30). No enumera aportes:
  describe qué incorpora cada SP, qué etapas son reanálisis y qué consulta el ejecutor
  de Cargo en el registro global. Es un apartado de alcance, no de contribución.
- **§7.1 «Contribución y resultados principales»** (p. 63, PDF 80). Tres párrafos que
  recorren SP1, SP2, SP3 y Cargo recitando resultados. **Ninguna de sus frases tiene la
  forma «la contribución es…».**

En el Capítulo 1, el lugar donde el párrafo debería estar lo ocupa **«Impacto
esperado»** (p. 4, PDF 21), que contiene la mejor formulación disponible en el cuerpo:

> «El impacto científico previsto es una regla de composición entre capas en la que
> cada interfaz expone un predicado verificable con su dominio declarado, de modo que
> la ausencia de garantía extremo a extremo deje de ser un supuesto implícito y pase a
> ser una condición explícita que otros trabajos puedan intentar cerrar.» — p. 4

Es correcta, es específica y es la frase que el tribunal debería recordar. Pero está
etiquetada como *impacto*, no como *contribución*; va seguida de un impacto industrial
y uno social; y el párrafo se cierra con **«Ninguno de los tres impactos se cuantifica
en esta memoria»** (p. 4), que un lector aplica retroactivamente a los tres, incluido
el científico, que sí está demostrado.

## 1.3. Las catorce apariciones de «contribución»

Recuento exhaustivo sobre el volcado completo. `ontribuci` aparece **catorce veces**.

| # | p. | PDF | Uso | ¿Sentido tesis? |
|---|---:|---:|---|---|
| 1 | i | 2 | «La contribución es una arquitectura verificable…» | **sí** |
| 2 | v | 6 | Índice: «7.1. Contribución y resultados principales» | título |
| 3 | xiii | 14 | Nomenclatura: «contribución normalizada de servicio» | técnico |
| 4 | 63 | 80 | Título de §7.1 | título |
| 5 | 63 | 80 | «La **contribución marginal** incorpora heterogeneidad operacional» | técnico |
| 6 | 64 | 81 | «La **contribución marginal** mejora la alineación» | técnico |
| 7 | 96 | 113 | «asigna a cada pareja robot–carga una contribución calculada…» | técnico |
| 8 | 96 | 113 | «la contribución de servicio $e_{ik}$» | técnico |
| 9 | 99 | 116 | «asigna la misma presión a contribuciones diferentes» | técnico |
| 10 | 99 | 116 | «cuando las contribuciones son heterogéneas» | técnico |
| 11 | 99 | 116 | «su contribución $e_{ik}$, su coste $g_{ik}$» | técnico |
| 12 | 108 | 125 | «$c^6_i$ la contribución normalizada» | técnico |
| 13 | 109 | 126 | «una utilidad de **contribución marginal**» | técnico |
| 14 | **129** | **146** | «La contribución candidata más coherente es…» | **sí** |

Diez de catorce son el término técnico (aportación marginal de un robot al servicio
agregado). Dos son títulos. **Dos son la contribución del trabajo, y están en la
página i y en la página 129.**

El caso más incómodo es el par #4–#5: **la sección titulada «Contribución» usa la
palabra únicamente en su acepción técnica.** Un lector que busque en el capítulo de
conclusiones la frase que define el aporte encuentra «La contribución marginal
incorpora heterogeneidad operacional», que habla de una función de utilidad.

## 1.4. Reconstrucción: las cinco contribuciones defendibles

Lo que sigue no está en el documento. Es la reconstrucción que exige el bloque 10
(«Enumerar exactamente 3–5 contribuciones»), hecha desde la evidencia, con su
clasificación y con la localización actual de cada una.

---

### C1 · Metodológica — la regla de composición certificada
**Es la contribución principal. Es la que el tribunal debe recordar.**

Cada interfaz expone un predicado verificable con su dominio, lo que habilita y lo que
**no** implica; una capa consume el certificado anterior sin ampliar su dominio; la
ausencia de garantía extremo a extremo se convierte en una condición explícita en
lugar de un supuesto implícito.

**Evidencia:**
- **Tabla 22, «Certificados que atraviesan las tres interfaces»** (p. 60, PDF 77), con
  sus cuatro columnas *Salida · Predicado verificable · Lo que habilita · Lo que no
  implica*. Esta tabla es el artefacto transferible del trabajo.
- Ecuación (8), la autorización ejecutable
  $\mathrm{GO}_k = \mathrm{CLOSE}_k \wedge \mathrm{SUPPORT}_k \wedge \mathrm{WRENCH}_k
  \wedge \mathrm{WHEELS}_k \wedge \mathrm{CONTACT}_k \wedge \mathrm{ROUTE}_k$ (p. 34,
  PDF 51), con la regla operativa «Un término falso produce abstención, espera o
  recuperación; no se repara el dato para convertirlo en éxito».
- Figura 10, contrato de composición SP1–SP3 (p. 34); Figura 2, contratos de
  información/decisión/factibilidad/ejecución (p. 4); Figura 18, composición de las
  tres etapas de SP1 con su par *certifica / no certifica* (p. 42).
- Proposición 6.8 y la Tabla 22 delimitan juntas por qué la garantía conjunta no se
  hereda (pp. 60–61).

**Dónde se enuncia hoy:** en ningún sitio como contribución. Lo más cercano es
«Impacto esperado» (p. 4) y la última frase de §6.7: «una garantía extremo a extremo
necesitaría además invariancia durante las conmutaciones y compatibilidad entre los
tres modelos; esa prueba no se reclama aquí» (p. 60).

**Por qué es la principal:** es lo único del trabajo que sobrevive a cambiar la planta,
el simulador, el mecanismo estratégico y la modalidad de contacto. Los cinco juegos
potenciales son instancias; la regla de composición es el resultado.

---

### C2 · Matemática — la familia de potenciales exactos cuyo conjunto de Nash coincide con el conjunto factible de su capa

Cinco veces, en cinco capas distintas, el trabajo construye la revisión local como un
juego de potencial exacto y demuestra que sus equilibrios puros **son exactamente** los
perfiles factibles de esa capa, con terminación finita contada en eventos.

**Evidencia:**

| Capa | Resultado | p. | Demostración |
|---|---|---:|---|
| E1 · cuotas | Teorema 6.1 — potencial exacto; si $\sum_k n_k \le N$ y $\lambda > \kappa_{\max}$, los Nash puros son exactamente los perfiles con $q_k = n_k$; a lo sumo $(K+1)N-1$ cambios | 42 | p. 95 (PDF 112) |
| E2 · servicio | Proposición 6.1 / G.1 — el campo marginal es gradiente de $\Phi$, y **al retirar el factor $e_{ik}/d^{\mathrm{srv}}_k$ las derivadas cruzadas dejan de coincidir** | 43 / 99 | p. 99 (PDF 116) |
| E4 · acoplamiento | Proposición 6.3 — potencial exacto y equilibrio variacional | 47 | p. 104 |
| E6 · reparación | Teoremas 6.3 y 6.4 — potencial exacto, terminación, y los Nash puros coinciden con las coaliciones factibles mínimas por inclusión, de donde $\mathrm{PoS}_6 = 1$ | 49 | pp. 109–110 |
| E7 · tráfico | Teorema 6.5 — potencial exacto y propiedad de mejora finita | 51 | p. 119 |
| Integración | Proposición 6.7 — **potencial exacto por factores** | 54 | p. 123 |

**Dónde se enuncia hoy:** cada resultado en su sección; **la familia, en ninguna
parte.** El documento nunca dice que el mismo movimiento se repite seis veces ni por
qué ese movimiento es el aporte. La Proposición G.1 en particular —la frontera de
integrabilidad, que es el resultado menos obvio de SP1— vive completa en el Anexo G
(p. 99) y en el cuerpo aparece comprimida a media página.

**Separación exigida por el bloque 10:** esto es contribución matemática, no
integración. Los juegos potenciales son de Monderer–Shapley; la construcción concreta
de cada $\Phi$ y la caracterización exacta del conjunto de Nash de cada capa no lo son.

---

### C3 · Matemática + experimental — la insuficiencia de la capacidad escalar y su medición

Cardinalidad y cobertura de servicio **no** son certificados mecánicos, y esto se
demuestra y se mide.

**Evidencia:**
- **Proposición C.3, «Insuficiencia de la capacidad escalar»** (p. 83, PDF 100): si
  todos los contactos están en el centro de masa, $r_i \times t_i = 0$ y ningún reparto
  genera $\tau_d \neq 0$ por grande que sea la suma escalar. Un contraejemplo de tres
  líneas que invalida una práctica corriente.
- El predicado sustituto: $W^{\mathrm{req}}_k \in \mathcal{W}_{C_k}$ (RQ3, p. 64).
- La medición: sobre **600 instancias**, la guardia situada en la interfaz SP1–SP2
  cambió la tasa de falsos positivos en **−0.333**, con cobertura **1.000** y abstención
  **0.500** (p. 63, PDF 80).
- Anexo F.2 lo eleva a lectura de diseño: «El paso de capacidad a wrench impide
  sustituir $W^{\mathrm{req}}_k \in \mathcal{W}_{C(q)}$ por la suma escalar
  $\sum_i c_i \ge d_k$» (p. 91).

**Dónde se enuncia hoy:** §7.1 (p. 63) y RQ3 (p. 64), en ambos casos como un resultado
entre otros. Nunca como contribución.

**Es la contribución más fácil de defender en sala:** tiene demostración, tiene
contraejemplo, tiene n = 600 y tiene un número con signo.

---

### C4 · Experimental — el diseño de ablaciones con resultados negativos conservados en el denominador

**Evidencia:**
- Cargo: tasa de misión **0.997** sin intersección carga–obstáculo; las ablaciones de
  seguridad y reparación degradan el éxito; reparación restaura **1.000** de los
  certificados recuperables; la reserva de SP3 da **1.000** de entrega frente a
  **0.739** al retirarla (p. 63).
- Y —esto es lo que la convierte en contribución y no en propaganda— los negativos
  están en el mismo párrafo y en las mismas tablas: **H3 no se sustenta** (IC del 95 %
  incluye cero, $p_{\mathrm{Holm}} = 0{,}068$, Tabla 24, p. 65); **el peor Nash del
  juego de reparación no admite cota uniforme**, $\mathrm{PoA}_6 = +\infty$
  (Proposición 6.4, p. 49); **tres de los cuatro escenarios de Industrial 2 agotaron el
  horizonte sin entregas con los cuatro métodos, incluidas las referencias** (pp. 63 y
  68); **H1b, H1c y H5b «no adjudicadas»** con la razón impresa (Tabla 24, p. 65).
- La regla metodológica que lo sostiene: «Colisiones, bloqueos, errores numéricos y
  agotamientos del horizonte permanecen en el denominador» (p. 14, PDF 31).

**Dónde se enuncia hoy:** disperso entre §7.1, la Tabla 23 (p. 62) y la Tabla 24
(p. 65). La honestidad del diseño nunca se presenta como aporte, cuando en un TFM de
simulación es precisamente lo que distingue un trabajo evaluable de uno decorativo.

---

### C5 · Ingeniería metodológica — el protocolo de tres revisiones con capas de evidencia

**Evidencia:**
- **Tabla 26, «Capas del corpus y tipo de afirmación que puede sostener cada una»**
  (p. 89, PDF 106): 3 014 descubiertos → metadatos; 244 analíticos → tendencias;
  59 canónicos → capacidades; 20 de lectura cercana → afirmaciones técnicas fuertes.
  Con una columna «Límite de evidencia» por capa.
- **Tabla 27, «Protocolo comparado de las tres revisiones»** (p. 89), con las filas
  **«Qué certifica»** y **«Qué no certifica»** para la académica, la industrial y la
  patentaria.
- La regla de codificación: «"Distribuido" no se asigna por la presencia de control
  local, sino por la combinación de autoridad de decisión, información disponible,
  existencia de líder o servidor y responsable del cierre» (pp. 88–89).

**Dónde se enuncia hoy:** en ningún sitio como aporte. §4.9 (p. 18) lo presenta como
protocolo y remite al Anexo F.

**Advertencia del bloque 10 aplicada:** esto es contribución de método de revisión, no
novedad algorítmica, y debe presentarse separado de C1–C3. Pero es transferible: otro
trabajo puede reutilizar las Tablas 26 y 27 tal cual.

---

## 1.5. Lo que **no** debe llamarse contribución, y el documento ya lo sabe

El bloque 10 exige no llamar contribución al uso de métodos conocidos. El TFM cumple
esta prueba mejor que la mayoría, y conviene dejarlo registrado porque es defensa
disponible:

- **Proposición 6.8**, el límite informacional bajo partición, lleva impreso encima:
  «es una aplicación de un argumento de indistinguibilidad clásico en cómputo
  distribuido (1985), **no un resultado de imposibilidad nuevo**» (p. 61, PDF 78).
  Exactamente la conducta que el bloque 10 pide.
- **Anexo J.6** (p. 129) enumera los bloques genéricos con antecedente directo —MPC
  distribuido, dinámicas poblacionales, ADMM/DisCo, homotopías, VI *anytime*, BeBOT,
  temporalización por alcanzabilidad— y concluye: «**No se reclama originalidad de esos
  bloques**». Y remata: «Las pruebas de este documento demuestran dominios concretos de
  esa arquitectura, **no prioridad mundial** sobre esos bloques genéricos».
- La **arquitectura híbrida** no debe reclamarse como diseño: la Tabla 3 (p. 16) y el
  párrafo que la cierra —«Estas dependencias hacen híbrida la arquitectura»— muestran
  que la hibridez es una concesión medida, no una elección. Presentarla como aporte
  sería exactamente el error de «primera vez que yo lo implemento».

---

# 2. Originalidad y novedad (bloque 11)

## 2.1. Barrido de lenguaje de prioridad: el resultado es cero

Recuento sobre las 146 páginas completas, anexos y bibliografía incluidos.

| Término buscado | Ocurrencias |
|---|---:|
| «por primera vez» | **0** |
| «novedoso» / «novedosa» | **0** |
| «innovador» / «innovadora» | **0** |
| «pionero» / «pionera» | **0** |
| «primera arquitectura» | **0** |
| «sin precedente» | **0** |
| «inédito» | **0** |
| «primer método» | 1 — y es una negación |
| «ningún trabajo» | 2 |
| «no existe» | 4 |
| «no se identificó» | 2 |
| «carece de precedente» | 1 |
| «novedad» | 4 — siempre nombrando la *auditoría* de novedad |
| «originalidad» | 1 — y es una renuncia |
| «mejor que» | **0** |
| «superior a» | 1 — «cardinalidad superior a dos», es geometría |

**Se confirma la comprobación anterior: el TFM no formula ni una sola reclamación de
prioridad.** No hay nada que rebajar.

## 2.2. Las ocho ocurrencias límite, una a una, con veredicto

Se transcribe cada frase que *podría* leerse como reclamación y se juzga según el
bloque 11: (a) sostenida por el corpus y el criterio declarados, (b) correctamente
matizada, (c) sobreafirmación.

**1 · p. 2 (PDF 19), Introducción.**
> «Dentro del corpus y del criterio de inclusión documentados en el Capítulo 5, **no se
> identificó** una solución que conectara la decisión de coalición con la ejecución
> física, la recuperación y la degradación de red.»

**(a) + (b).** El matiz antecede al verbo, no lo sigue. Es la formulación que el bloque
11 pide literalmente («Expresar novedad como "no se identificó bajo este protocolo"»).
**Modelo de redacción.**

**2 · p. 29 (PDF 46), recuadro «Brecha académica defendible».**
> «En el corpus revisado **no se identificó** una arquitectura que integre, en una misma
> cadena operativa, la selección local de una coalición física heterogénea de tamaño
> variable desde una flota mayor, la verificación mecánica de factibilidad de la carga
> compartida y la recomposición en línea de un miembro durante el transporte,
> manteniendo la decisión de coalición y la ejecución sin una autoridad global
> permanente […]. El enunciado se restringe al protocolo de búsqueda documentado y **no
> afirma inexistencia absoluta**.»

**(a) + (b).** Doblemente matizado, y el matiz está dentro del recuadro. Véase no
obstante la sección 3 de este informe: el matiz cubre el corpus y **no** cubre la
implementación evaluada.

**3 · p. 41 (PDF 58), Tabla 8, fila 1.**
> «**Ningún trabajo** del núcleo reúne certificación física, ejecución distribuida y
> reemplazo.»

**(a)**, con reserva de forma. Aquí falta el matiz que sí llevan las demás
formulaciones: «del núcleo» acota el corpus pero la fila no repite «bajo esta
codificación». La Figura 12a (p. 37) imprime el dato («Física + distrib. + reemplazo:
**0**») y su pie sí lo matiza: «los ceros significan "no identificado bajo esta
codificación", no inexistencia bibliográfica» (p. 37). El matiz está a cuatro páginas.

**4 · p. 32 (PDF 49) y p. 33 (PDF 50), Tabla 5.**
> «**Ninguno** de los precedentes revisados documenta simultáneamente una coalición
> física heterogénea multi-vehículo, selección local de miembros, verificación mecánica
> de factibilidad y recomposición durante la misión.»
> «**"No documentado" no equivale a inexistencia.**»

**(a) + (b).** El matiz está impreso dentro de la leyenda de la tabla, no en una nota
remota. Ejemplar.

**5 · p. 68 (PDF 85), §7.8.**
> «En lo teórico, la garantía extremo a extremo que hoy **no existe** requiere dos
> piezas concretas […]».

**(a).** «No existe» aquí se predica de un teorema que el propio trabajo no ha probado.
Es una confesión, no una reclamación.

**6 · p. 92 (PDF 109), Anexo F.2.**
> «El enunciado de brecha reclama solo que la composición de las tres piezas bajo
> información local **carece de precedente documentado en el corpus**: **no** el primer
> método distribuido de transporte cooperativo, **ni** el primer mecanismo de reemplazo,
> **ni** superioridad frente a ningún trabajo de la Figura 8.»

**(a) + (b), y es la mejor frase de novedad del documento.** Enuncia la reclamación y
sus tres negaciones en la misma oración. Está en la página 92, en un anexo.

**7 · p. 91 (PDF 108), Anexo F.2.**
> «La brecha **no puede formularse como "falta control distribuido de carga", que sería
> falso**, sino como una interfaz que ninguno de los dos frentes atraviesa.»
> «El resultado **obliga a estrechar el enunciado: el reemplazo durante el transporte ya
> existe.**»

**(a) + (b).** Autorrefutación explícita con los tres antecedentes nombrados —Verma
2019, Sahu 2026, Shibata 2023— y la restricción decisiva de cada uno. El bloque 11 pide
«Buscar antecedentes que puedan invalidar un "no existe"»: esto es exactamente eso,
hecho y documentado en la Tabla 28 (p. 92).

**8 · p. 129 (PDF 146), Anexo J.6.**
> «**No se reclama originalidad** de esos bloques. […] Las pruebas de este documento
> demuestran dominios concretos de esa arquitectura, **no prioridad mundial**.»

**(a) + (b).**

**Veredicto del barrido: ocho de ocho correctamente matizadas. Cero
sobreafirmaciones.** No hay una sola frase que retirar en este frente. En una auditoría
de novedad ese resultado es infrecuente y hay que decirlo.

## 2.3. El problema opuesto, que sí existe y es grave

**La contribución está infradeclarada hasta la invisibilidad.** Tres síntomas medidos:

### S1 · La novedad solo se enuncia en negativo

Las tres frases que podrían portar la reclamación (pp. 2, 29, 92) están todas
construidas como **ausencias en el corpus**: «no se identificó», «ninguno documenta»,
«carece de precedente documentado». Ninguna se convierte nunca en la afirmación
positiva correspondiente. El documento **nunca escribe** una frase de la forma:

> «Bajo el protocolo de la Tabla 27, este trabajo especifica la primera composición
> documentada de selección local, certificado mecánico y recomposición en línea.»

El tribunal tiene que hacer esa inversión por su cuenta, y el bloque 11 no exige
modestia: exige que la novedad se exprese como «no se identificó bajo este protocolo».
El TFM ha escrito la mitad matizadora de esa fórmula y ha omitido la mitad afirmativa.

### S2 · La rúbrica que condena a doce trabajos nunca se aplica al propio trabajo

- **Figura 8 (p. 31, PDF 48)** cruza **doce** trabajos contra ocho capacidades
  (heterogeneidad, coalición variable, reclutamiento local, *shared-load*, certificación
  física, ejecución distribuida, *recovery*, *replacement*), más una columna de tipo de
  evidencia (T/S/P) y una de nivel de centralización (C0–C4). **No hay fila para el
  TFM.**
- **Tabla 28 (p. 92, PDF 109)** repite el ejercicio contra los seis antecedentes más
  próximos con las mismas ocho columnas H/V/L/S/W/D/R/X y una «Restricción decisiva».
  **Tampoco hay fila para el TFM.**
- **Tabla 5 (p. 33, PDF 50)**, la industrial, **sí** añade la fila
  «**TFM objetivo** (referencia conceptual)» con su contenido explícito.

La asimetría es del lado académico y es justo el lado donde la brecha se declara. La
rúbrica existe, está codificada, está publicada — y el trabajo no se somete a ella.
Añadir una fila «Este TFM (cuerpo activo)» a la Figura 8 y a la Tabla 28 es el cambio
más barato y de mayor rendimiento de todo este informe: convierte una brecha declarada
en una posición medida con la misma vara.

Y forzaría además la respuesta honesta de la sección 3: en la columna **D** (ejecución o
decisión distribuida) y en la columna **C** (nivel de centralización), la fila del TFM
no puede ser «explícito»/C4 mientras la Tabla 3 (p. 16) diga lo que dice.

### S3 · Los mapas colocan un marcador que la Tabla 3 desmiente

Las **Figuras 6 (p. 28) y 7 (p. 30)** imprimen el marcador «**Este TFM · integración**»
en un plano cuyo eje horizontal es **autoridad de decisión (descentralizado →
centralizado)**. El marcador se sitúa del lado descentralizado / *white-box*.

La **Figura 8 (p. 31)** define la escala que da sentido a ese eje: «**C4 — decisión local
con intercambios vecinales sin autoridad central en tiempo de ejecución**».

La **Tabla 3 (p. 16)** describe la implementación evaluada: fila `Cargo`, decisión
«líder temporal tras gossip de identificadores», agregado «atributos resueltos en
**registro global**», cierre «**líder por carga**».

Los pies de figura contienen el descargo genérico («Las posiciones son descriptivas y
no representan calidad ni rendimiento», p. 28), pero el descargo cubre calidad y
rendimiento, **no** autoridad de decisión, que es precisamente lo que el eje mide. Un
marcador en la esquina descentralizada de un eje de autoridad es una afirmación sobre
autoridad. Es la única sobreafirmación que esta auditoría encuentra en todo el frente de
novedad, y es gráfica, no textual.

## 2.4. Novedad por subproblema y diferenciación frente a las familias del bloque 11

| Frente | Novedad defendible | Dónde está | Estado |
|---|---|---|---|
| **SP1** | Caracterización exacta del conjunto de Nash de la regulación de cuotas (Teor. 6.1) y **frontera de integrabilidad** del campo marginal (Prop. G.1) | pp. 42 y 99 | La segunda, la menos obvia, vive en el Anexo G |
| **SP2** | Insuficiencia de la capacidad escalar (Prop. C.3) + guardia de wrench medida sobre 600 instancias | pp. 83 y 63 | Enunciada, no reclamada |
| **SP3** | Invariante de exclusión + terminación finita | pp. 51 y 119–120 | **Débil, y el trabajo hace bien en no reclamarla**: es construcción estándar de testigo |
| **Juego de integración** | **Potencial exacto por factores** (Prop. 6.7) y equivalencia variacional (Teor. 6.6) | p. 54 | Dos de los cuatro resultados con verificación numérica (Tabla 25, p. 67); el propio trabajo lo declara |
| **Arquitectura** | La regla de composición (C1) | Tabla 22, p. 60 | Nunca reclamada |

Diferenciación exigida por el bloque 11, comprobada una a una:

| Frente a | ¿Diferenciado? | Dónde |
|---|---|---|
| MRTA | **Sí** — «MRTA entrega una composición nominal y el control cooperativo suele recibir un equipo físico ya fijado» | pp. 1, 19, 28 |
| CBBA | **Sí, con precisión** — Tabla 9: «garantía CBBA original **inaplicable**»; «CBBA-capacidad modifica los problemas estudiados en sus fuentes, por lo que sus garantías originales no se transfieren» | pp. 44 y 98 |
| MILP / Húngaro | **Sí** — se usan como oráculos con ventaja informativa declarada, no como comparadores en igualdad | pp. 2, 16, 44 |
| DMPC / NMPC | **Parcial** — solo aparece como adaptación piloto en Industrial 2 («no implementaciones completas de CBBA, ORCA o DMPC», p. 66). El marco teórico no contrasta la arquitectura frente a DMPC como familia |
| MAPF | **Sí** | Figs. 6 y 7, pp. 28 y 30 |
| MARL / GNN | **Sí, y es la mejor frase de posicionamiento del documento** — «Una política aprendida no sustituye a esta arquitectura porque entrega **una acción, no un predicado verificable con dominio declarado**, y sin predicado no hay columna que rellenar en la regla de composición de la Tabla 22» | p. 67 |
| Cooperative manipulation | **Sí** — panel (b) de la Fig. 8 separa *supported cargo*, *rigid attachment*, *pushing/caging* y *grasping* como conjuntos de esfuerzos admisibles distintos que «no deben agruparse bajo la etiqueta genérica *cooperative transport*» | p. 31 |
| Trabajos que ya hacen *replacement* | **Sí, ejemplarmente** — Verma 2019 (planificación global, hitos conocidos), Sahu 2026 (maestro–esclavo), Shibata 2023 (equipo variable, sin selección desde flota heterogénea) | pp. 91–92, Tabla 28 |

**Solo DMPC/NMPC queda sin contraste argumental**, y es una laguna menor.

Nótese dónde está la mejor frase de posicionamiento del trabajo: en **§7.7**, después de
las conclusiones, como digresión sobre política aprendida (p. 67). Debería abrir el
Capítulo 5 o cerrar la introducción.

---

# 3. La brecha frente a las dependencias globales

Este frente no corresponde a un bloque numerado, pero es el punto donde el tribunal
atacará.

## 3.1. Dónde se enuncia la brecha

| Lugar | p. | PDF | Formulación |
|---|---:|---:|---|
| Introducción | 2 | 19 | «no se identificó una solución que conectara la decisión de coalición con la ejecución física, la recuperación y la degradación de red» |
| §5.5 cierre | 28 | 45 | «faltan entre ambos un certificado mecánico consumible y una regla que reabra la decisión tras un fallo» |
| **§5.6, recuadro** | **29** | **46** | **«… manteniendo la decisión de coalición y la ejecución sin una autoridad global permanente»** |
| §5.6 industrial | 29 | 46 | «ningún precedente integra las tres a la vez con selección local y certificación mecánica» |
| Tabla 5, lectura | 33 | 50 | «Ninguno de los precedentes revisados documenta simultáneamente…» |
| Tabla 8, filas 1 y 5 | 41 | 58 | «Ningún trabajo del núcleo reúne…» / «Ningún precedente comercial integra…» |
| Anexo F.2 | 91–92 | 108–109 | Auditoría adversarial + Tabla 28 |

La cláusula crítica es **«sin una autoridad global permanente»**, p. 29, dentro del
recuadro sombreado. Es la única formulación de la brecha que menciona la autoridad.

## 3.2. Dónde se declaran las dependencias globales

| Lugar | p. | PDF | Declaración |
|---|---:|---:|---|
| Fig. 1, pie | 2 | 19 | «El diagrama representa la arquitectura objetivo local; **no reclasifica como distribuidos los cierres o certificados globales declarados en los experimentos**» |
| §4.3 | 13 | 30 | «El ejecutor consulta **el estado global** para elegir un líder temporal y resuelve distancia, carga útil y fuerza en un **registro también global**. El conteo de mensajes […] **excluye la elección de líder, los atributos y las consultas al registro**. La cifra resultante es una **cota inferior** del tráfico» |
| **Tabla 3, fila `Cargo`** | **16** | **33** | Decisión: «líder temporal tras gossip de identificadores» · Agregado: «atributos resueltos en **registro global**» · Cierre: «**líder por carga**» |
| §4.6 cierre | 16 | 33 | «**Estas dependencias hacen híbrida la arquitectura**» |
| §6.7 | 60 | 77 | «bajo un contrato híbrido con **información global declarada**» |
| §7.2 | 64 | 81 | «**no** una arquitectura completamente distribuida»; «el registro global impide atribuir el resultado a coordinación local completa» (RQ2, p. 64) |
| §7.5 | 66 | 83 | «Cargo considera una carga y un fallo simple, con **líder temporal, registro global**, grafo estático» |
| Anexo J | 114 | 131 | «El tratamiento llamado "vecinal" abrevia gossip de identificadores **más selección por líder y registro global**» |
| Resumen | i | 2 | «No demuestra […] **coordinación completamente distribuida**» |

**Nueve declaraciones, ninguna ambigua.** La Tabla 3, además, hace el ejercicio etapa a
etapa para E0–E8 y no solo para Cargo: E1 «QR global», E2 «déficit global», E3 «QP de
wrench central», E4 «bilateral/global», E5 «filtro y reparto central por carga». Solo
E6 y E7 son «local». Esto es más transparencia de la que se encuentra en la mayoría de
las memorias, y hay que registrarlo como tal.

## 3.3. ¿Alguna frase reconcilia las dos cosas?

**Sí, cuatro. Ninguna está en la página de la brecha, ninguna está dentro del recuadro,
y el recuadro no cita a la Tabla 3.**

1. **p. 1 (PDF 18), último párrafo de la primera página del cuerpo:**
   > «El dibujo representa la arquitectura objetivo sin coordinador central; **las
   > dependencias globales que conserva la implementación evaluada se declaran después
   > en la metodología**.»

   Esta es la reconciliación exacta. Distingue *arquitectura objetivo* de *implementación
   evaluada* y remite. Está **28 páginas antes** del recuadro.

2. **p. 3 (PDF 20):** «Por eso la implementación evaluada es **híbrida**.»

3. **p. 28 (PDF 45), el párrafo inmediatamente anterior a §5.6:**
   > «La arquitectura propuesta conecta esos contratos mediante juegos locales con
   > supuestos propios. SP1–SP3 los evalúan por separado y **Cargo reúne sus funciones
   > con reglas simplificadas, líder por carga y registro global**. La composición
   > acredita compatibilidad funcional, mientras cada garantía permanece en el componente
   > donde se demostró.»

   Está a **una página** del recuadro — en la página anterior. El lector que pasa la hoja
   encuentra el recuadro y ya no vuelve.

4. **p. 41 (PDF 58), Tabla 8, fila 2:**
   > «**Toda dependencia global de la implementación evaluada se declara en la Tabla 3 en
   > vez de presentarse como distribuida.**»

   Es la formulación más limpia de todas y está en una tabla de consecuencias de diseño,
   doce páginas después del recuadro.

## 3.4. Veredicto

**No hay contradicción lógica.** El recuadro de la p. 29 enuncia lo que el corpus no
contiene; no enuncia lo que este trabajo logra. Las dos proposiciones son compatibles y
el documento las declara ambas nueve y cuatro veces respectivamente.

**Hay una vulnerabilidad de disposición, y es real.** El recuadro sombreado de la p. 29
es el único párrafo del documento con tratamiento tipográfico de tesis; es lo que un
tribunal subraya y lee en voz alta. Su última cláusula —«manteniendo la decisión de
coalición y la ejecución **sin una autoridad global permanente**»— nombra exactamente la
propiedad que la Tabla 3 (p. 16) niega a la implementación evaluada. Entre las dos hay
trece páginas y **cero referencias cruzadas**: el recuadro no cita la Tabla 3, y la
Tabla 3 no cita el recuadro.

El matiz que el recuadro sí lleva —«El enunciado se restringe al protocolo de búsqueda
documentado y no afirma inexistencia absoluta»— protege contra el reproche
bibliográfico («seguro que existe algo que no encontró») y **no** protege contra el
reproche que de verdad llegará: «usted describe una propiedad que su demostrador no
tiene».

**Falta exactamente una oración subordinada, dentro del recuadro.** Por ejemplo, con
palabras ya presentes en el documento: *«La implementación evaluada no alcanza esa
última condición; sus dependencias globales se declaran en la Tabla 3.»* Quince
palabras convierten el punto más atacable del documento en una demostración de rigor.

Y el corolario de la sección 2.3: **mientras el marcador «Este TFM» siga impreso en la
esquina descentralizada de las Figuras 6 y 7 sin fila propia en la Figura 8, la
reconciliación textual no cubre la gráfica.**

---

# 4. Estado industrial (bloque 14)

## 4.1. Qué afirmación sostiene la revisión industrial

Una sola, y está enunciada tres veces con la misma forma:

> «La industria demuestra **por separado** carga compartida, emparejamiento/relevo ante
> fallo y coordinación distribuida de flota. **Ninguno** de los precedentes revisados
> documenta **simultáneamente** una coalición física heterogénea multi-vehículo,
> selección local de miembros, verificación mecánica de factibilidad y recomposición
> durante la misión.» — p. 33 (PDF 50), lectura de la Tabla 5

Con la consecuencia de diseño en la Tabla 8 (p. 41):

> «El demostrador se plantea como **prueba de compatibilidad funcional, no como
> comparación con un producto equivalente**.»

## 4.2. ¿Es proporcionada la inferencia? Sí. Comprobación del bloque 14

| Ítem del bloque 14 | Estado | Evidencia |
|---|---|---|
| Qué significa «precedente industrial» | **definido** | Tabla 27 (p. 89): «sistema o despliegue **con fuente oficial**» |
| Evidencia del fabricante vs. verificación independiente | **NO distinguida** | ver D1 |
| Casos con carga compartida real | **separados** | 8 de 10 casos principales; AGILOX (fila 7) y Hyundai (fila 10) llevan «–» y la nota «Una carga por AMR: **no aplica** coalición física» (p. 33) |
| Número real de vehículos | **declarado por fila** | «2 AGV, 2×5 t» (Stäubli), «Dos plataformas, hasta 6 t» (KUKA KMP), «27 AMR» (AGILOX), «2 robots» (Beacon), «80–220 t» (GREATOX) |
| Selección dinámica | **declarada ausente** donde falta | «Sin selección dinámica, certificado online ni recomposición autónoma publicada» (filas 1, 9); «Selección a nivel de planta, no reclutamiento local» (fila 3) |
| Control central / local | **declarado** | «líder–seguidor» (4), «despacho central y líder–seguidor» (8), «coordinación entre pares sin líder central» (7) |
| *Replacement* | **distinguido con precisión** | Beacon: «emparejamiento automático y relevo de autoridad ante fallo documentados […] **No se documenta sustitución/reclutamiento de un nuevo miembro**» (p. 33), ampliado en p. 93 |
| Certificación mecánica | **columna entera «no documentado»** | ver D4 |
| No inferir ausencia de capacidad de «no documentado» | **CUMPLIDO, e impreso en la leyenda** | «**"No documentado" no equivale a inexistencia**» (p. 33); Tabla 27: «Qué no certifica: […] inexistencia de lo no documentado» (p. 89); símbolo «?» reservado para «arquitectura **no publicada**», distinto de «no documentado» |
| No llamar validación industrial al piloto de simulación | **CUMPLIDO** | p. i: «No demuestra […] validez industrial»; p. 62: Industrial 2 → «Delimitado»; p. 63: «tres de los cuatro escenarios del piloto no entregaron carga con ninguno de los métodos»; p. 66: «adaptaciones piloto, no implementaciones completas» |
| Vigencia de productos y fuentes | **parcial** | ver D3 |
| Consistencia año del caso vs. año de la fuente | **CORRECTA** | ver 4.4 |

## 4.3. Defectos

### D1 · Ninguna fila tiene verificación independiente, y eso no se declara

El pie de la Tabla 5 dice: «Fuente: elaboración propia **con documentación técnica
oficial de cada fabricante**» (p. 33). La Tabla 27 confirma la vía de recuperación:
«auditoría web de fabricantes e integradores» (p. 89).

Es decir: **las catorce filas descansan íntegramente en lo que el propio vendedor
publica sobre su producto.** No hay una sola verificación independiente, ni ensayo de
tercero, ni informe de integrador ajeno, ni publicación arbitrada sobre ninguno de los
diez casos.

Eso es legítimo —es el material disponible— pero el bloque 14 pide exactamente esta
distinción, y el documento no la hace en ninguna parte. La fila «Qué no certifica» de
la Tabla 27 enumera «cuota de mercado ni inexistencia de lo no documentado» y **omite**
lo que más importa: *ni exactitud de lo afirmado por el fabricante*. Un material
promocional que dice «hasta 70 t» no es una medición.

Esto muerde en las dos direcciones. Sobredeclara las capacidades que el fabricante
afirma (la columna «Carga comp.» de las filas 1, 5, 9) e infradeclara las que no le
interesa publicar (columna «Cert. factib.», ver D4).

**Corrección:** una fila más en la Tabla 27 y media frase en el pie de la Tabla 5.

### D2 · La matriz no separa despliegue documentado de página de catálogo

Las diez filas principales mezclan tres clases de evidencia con el mismo formato:

| Clase | Filas | Peso probatorio |
|---|---|---|
| **Instalación nombrada con cliente** | 1 (Airbus Stade), 7 (BMW Regensburg), 10 (HMGICS), 2 (sala limpia R3) | alto |
| **Caso de aplicación del fabricante** | 3 (SIASUN heavy-truck), 9 (HUBTEX Aviation) | medio |
| **Producto / catálogo / nota de prensa** | 4 (KUKA KMP 3000P, 2025), 5 (**GREATOX GTVL25, «cat. 2026»**), 6 (SPMT), 8 (Beacon, 2026) | bajo |

La fila 5 lleva impreso «cat. 2026» —el propio autor sabe que es catálogo— y aun así
ocupa la misma estructura de fila y aporta dos «?» a la matriz, es decir contribuye
igual que un despliegue verificado a la conclusión «ninguno integra las tres».

El lado académico **sí** resuelve esto: la Figura 8 (p. 31) lleva una columna «**Ev.**»
con T (teórica), S (simulación) y P (plataforma física). La matriz industrial necesita
la columna análoga —despliegue / caso / catálogo— y el dato ya está recogido en el
texto de cada celda.

### D3 · Vigencia

Los casos abarcan 2016–2026 y se auditaron en una sola pasada web del **11-09-2026**
(todas las referencias llevan «Consultado el 11 de septiembre de 2026»). La fila 1
(KUKA omniMove / Airbus) es de **2016** y la fila 9 (HUBTEX Aviation) de **2020**: diez y
seis años. La matriz no dice si esas capacidades siguen ofreciéndose ni si la
instalación sigue operando. Para un argumento sobre lo que «la industria resuelve hoy»,
una fila de hace una década necesita una nota de vigencia o una columna «última
evidencia».

### D4 · La columna que más pesa es la que menos informa

«Cert. factib.» —verificación mecánica de factibilidad— es **«no documentado» en las
diez filas**. Es la columna sobre la que descansa la mitad mecánica de la brecha.

Y es precisamente la columna donde la ausencia de documentación es menos informativa:
ningún fabricante tiene incentivo comercial para publicar que su producto resuelve un QP
de admisión antes de mover una carga, ni para publicar los casos en que se abstiene. El
descargo general del documento («"No documentado" no equivale a inexistencia», p. 33)
cubre el caso formalmente, pero el enunciado de brecha se apoya en esta columna más que
en ninguna otra y allí no lo repite.

### D5 · Denominador ausente en la Tabla 8

La Tabla 8 (p. 41) recoge: «**Doce trabajos con validación física frente a noventa y
nueve en simulación**». El dato procede del panel (c) de la Figura 13 (p. 37), cuyo pie
advierte: «Conteos positivos por tipo de evidencia; **no se presentan porcentajes de
prevalencia** porque la disponibilidad de extracción estructural varía por campo», sobre
**n = 244**.

Sin el denominador, «doce frente a noventa y nueve» se lee como una razón sobre el
corpus (12 %/88 %) cuando son dos conteos positivos independientes sobre 244 bajo una
extracción de cobertura desigual. Una cifra entre paréntesis lo arregla.

## 4.4. Lo que está bien y conviene defender

- **Consistencia de años: correcta.** Cada caso lleva el año de su fuente y el año de la
  fuente coincide con el del caso: KUKA AG (2016) con URL
  `…/solutions-database/**2016**/07/…`; AGILOX (2023); SIASUN (2024); Stäubli+R3 (2022);
  TII Scheuerle (2023); HUBTEX (2020, con PDF fechado `2020-04`); Hyundai (2023);
  KUKA KMP (2025); GREATOX (2026); Beacon (2026). No hay ningún caso fechado antes que
  su página. El bloque 14 pide esta comprobación y el documento la pasa limpia.
- **El tratamiento de Beacon Dual-AMR es ejemplar** y se repite idéntico en dos lugares
  (p. 33 y p. 93): reconoce que es «el precedente con mayor solapamiento funcional»,
  reconoce lo que documenta (emparejamiento automático, relevo de autoridad ante fallo)
  y acota lo que no (dos robots, despacho central, no sustituye a un miembro por otro de
  la flota). Reconocer al competidor más próximo con precisión es lo contrario del
  *cherry-picking*.
- **La distinción entre dos heterogeneidades** (p. 93): la de flota —modelos distintos
  bajo un mismo gestor, frecuente en las plataformas de contexto— frente a la de dentro
  de una coalición física —robots con capacidades y geometrías diferentes que deben
  cerrar conjuntamente restricciones de carga, contacto y wrench—. Es una distinción
  fina, correcta y necesaria, y es la que sostiene la parte «heterogénea» de la brecha.
- **Las cuatro filas de contexto A–D** (MiR, OTTO, Geek+, Swisslog) se excluyen de la
  matriz principal con la razón impresa: «no se incluyen como filas principales porque
  **no aportan carga compartida**» (p. 33). Exclusión declarada, no silenciosa.

## 4.5. Veredicto del bloque 14

**La revisión industrial NO está sobreleída.** Su conclusión se formula como restricción
de diseño experimental, no como afirmación de mercado, y el piloto de simulación jamás
se presenta como validación industrial. Es el más disciplinado de los tres corpus.

Los cuatro defectos (D1–D4) son de **declaración de límites**, no de inferencia: el
argumento aguanta, la documentación de su base probatoria no está completa.

---

# 5. Patentes (bloque 15)

## 5.1. Qué afirmación sostiene la revisión patentaria

Enunciada en el cuerpo (p. 41, PDF 58):

> «El corpus patentario se desplaza hacia decisión de misión: media móvil de tres años
> del 37,9 % al 58,8 % entre el cierre de 2022 y el de 2025 (**+20,9 puntos, robusto a
> la ampliación dirigida por solicitante**), mientras coordinación cinemática e
> interacción física bajan (Figura 17).»

Y convertida en consecuencia en la Tabla 8, fila 4 (p. 41):

> Desplazamiento de +20,9 puntos hacia decisión de misión en el corpus patentario · OE1 ·
> «**Confirma pertinencia industrial de la capa estratégica y justifica el peso de SP1 en
> la campaña.**»

## 5.2. Comprobación del bloque 15

| Ítem | Estado | Evidencia |
|---|---|---|
| Fuente del dataset | **declarada** | «texto, CPC G05D 1/69–1/6987, solicitante y snowballing» (Tabla 27, p. 89) |
| Cobertura temporal | **declarada** | corte **11-09-2026**; eje temporal = año de publicación (pp. 18, 89, 90) |
| CPC utilizados | **declarados uno a uno** | G05D 1/69, 1/692, 1/695, 1/696 y 1/698–1/6987 (p. 90) |
| Duplicados / familias | **tratado y justificado** | «se analiza a nivel de **publicación** y no de invención ni de familia jurídica, con el año de publicación como eje temporal porque el **de prioridad solo consta en 6 de los 167 registros**» (p. 90) |
| Solicitantes | **parcial** | n = 74 (2018–2022) y n = 49 (2023–2025) «titulares identificados», sobre 167 |
| Balanceo | **declarado, pero mal nombrado en el cuerpo** | ver P3 |
| Ampliación dirigida | **declarada y marcada gráficamente** | hachurado en el panel (b) de la Fig. 17 (p. 40) |
| Sensibilidad del cambio +20,9 p.p. | **DOS pruebas con número** | p. 95: excluyendo la ampliación → **+22,0**; colapsando los cuatro grupos de títulos muy similares → **+20,0** |
| No interpretar patentes como adopción industrial | **INCUMPLIDO en una celda** | ver P1 |
| No confundir registros con invenciones independientes | **CUMPLIDO** | Tabla 27: «Qué no certifica: número de invenciones ni familias jurídicas» (p. 89); «una única etiqueta temática y una macrocapa por publicación **para impedir el doble conteo**», citando OECD (2009) y WIPO 946 (2015) (p. 90) |
| Leyendas y denominadores | **parcial** | ver P4 |
| Países y titulares correctamente identificados | **CUMPLIDO, con la advertencia correcta** | p. 95: «China concentra la mayoría de titulares identificados y el **14,3 % reciente de Estados Unidos procede íntegramente de la ampliación dirigida, de modo que no admite lectura como cuota mundial**» |

## 5.3. Defectos

### P1 · «Confirma pertinencia industrial» contradice a la Tabla 27 — **es la sobrelectura**

La Tabla 27 (p. 89) fija lo que el corpus patentario puede sostener:

> **Qué certifica:** «desplazamiento de la actividad de protección».
> **Qué no certifica:** «número de invenciones ni familias jurídicas».

La Tabla 8 (p. 41) lo convierte en:

> «**Confirma pertinencia industrial** de la capa estratégica.»

Un desplazamiento de cuota temática dentro de un corpus de 167 publicaciones,
recuperado por una familia CPC y codificado por el propio autor con una etiqueta única
por registro, **no confirma** pertinencia industrial de nada. Es compatible con ella. El
bloque 15 lo prohíbe expresamente: «No interpretar patentes como adopción industrial».
«Pertinencia» es más débil que «adopción», pero el verbo **«Confirma»** no está
disponible para un corpus descriptivo, y la propia memoria lo reconoce sesenta páginas
después al decir que ese corpus solo certifica desplazamiento de actividad de
protección.

Es **una inconsistencia interna entre dos tablas del mismo documento**, no una opinión
de esta auditoría. Redacción proporcionada: «*Es coherente con la pertinencia industrial
de la capa estratégica*».

### P2 · «y justifica el peso de SP1 en la campaña» es justificación *post hoc*

La segunda mitad de la misma celda usa una tendencia externa para justificar el reparto
interno del esfuerzo experimental. Pero el peso de SP1 en la campaña no lo decidió el
corpus patentario: lo decidió qué etapas sobrevivieron como evidencia activa. El propio
documento lo dice en §4.6 (p. 15): «El capítulo de resultados activa E2, E3, E4, E6, E7 y
Cargo; **E0, E1, E5 y E8 permanecen como procedencia y material de monografía**».

La pregunta que un tribunal puede formular es simétrica y el documento no puede
responderla: si la tendencia hubiera ido hacia interacción física, ¿habría pesado más
SP2? Nada en la memoria sugiere que el diseño experimental fuera contingente a ese dato.
La celda debería decir qué hace el hallazgo —fijar un comparador, excluir una garantía—
como hacen las otras cuatro filas de la Tabla 8, que están bien redactadas.

### P3 · «robusto a la ampliación dirigida» nombra una operación distinta de la que se midió

En el cuerpo (p. 41): «+20,9 puntos, **robusto a la ampliación dirigida por
solicitante**».
En el recuadro de la Fig. 17a (p. 40): «**sin balanceo por solicitante**: +22,0 p.p.».
En el anexo (p. 95): «El resultado no depende de la ampliación dirigida por solicitante:
**excluyéndola** el cambio va del 32,7 % al 54,7 %, es decir 22,0 puntos».

Dos problemas distintos:

1. **La figura y el cuerpo nombran operaciones diferentes.** «Sin balanceo por
   solicitante» (reponderar) y «excluyendo la ampliación dirigida» (eliminar registros)
   no son lo mismo. El anexo respalda la segunda; la figura imprime la primera; el
   cuerpo cita la segunda. Uno de los tres rótulos está mal. Es un defecto puntual y
   verificable contra el generador del corpus v3.
2. **«Robusto» es más de lo que dos puntos autorizan.** Lo medido son tres valores sobre
   un mismo eje —20,9 base; 22,0 sin la ampliación; 20,0 colapsando títulos similares—
   en una única dirección de perturbación. Eso es un **análisis de sensibilidad**, y como
   tal es más de lo que la mayoría de los análisis patentarios de un TFM presenta. No es
   robustez. Redacción proporcionada: «*estable frente a las dos perturbaciones
   ensayadas (+22,0 y +20,0 puntos)*», que además mete los números en el cuerpo, donde
   hacen falta.

### P4 · Los tres paneles de la Figura 17 corren sobre tres denominadores distintos

| Panel | Denominador | Impreso |
|---|---|---|
| (a) actividad anual y MM3 | **167** registros analíticos | solo en el Anexo F.1 (p. 89) |
| (b) cobertura geográfica | **74 + 49 = 123** «titulares identificados» | sí, en el subtítulo del panel |
| (c) orientación funcional | **75** («se excluyen 92 registros de uso general o multisector») | sí, en el pie |

Los tres están declarados, lo cual ya es más de lo habitual. Pero están declarados en
tres lugares distintos y el pie no advierte que **son distintos entre sí**. Un lector que
compare el «60,8 % China» del panel (b) con el «69 % intralogística» del panel (c) está
comparando porcentajes de 123 y de 75 dentro de una misma figura.

Además, el panel (b) cubre 2018–2022 y 2023–2025, mientras el panel (a) arranca en 2012:
los dos periodos del panel (b) no agotan el corpus del panel (a), y eso no se dice.

### P5 · La MM3 temprana descansa sobre denominadores de un dígito

El panel (a) imprime los recuentos anuales **2, 3, 2, 2, 7, 6, 11, 19, 21, 26, 23, 23,
22** contra un eje etiquetado 2012–2025 (trece valores para catorce etiquetas). Sea cual
sea la correspondencia, los primeros años tienen **dos y tres publicaciones**. Una media
móvil de tres años sobre ventanas de cinco o siete registros no admite una cifra con un
decimal.

Esto **no afecta al titular**: la comparación se hace en los cierres de 2022 y 2025,
donde las ventanas son de ~70 registros. Afecta a la curva temprana del panel, que
invita a leer una tendencia donde hay ruido muestral.

### P6 · El sesgo estructural del CPC no se discute — y es la debilidad de fondo

El corpus se recupera por **G05D 1/69–1/6987**, la familia de *control de posición de dos
o más vehículos en coordinación*. Después se codifica cada registro en una de tres
macrocapas: decisión de misión, coordinación cinemática, interacción física.

Un corpus recuperado por una CPC de coordinación y clasificado luego en un eje cuyo
extremo es «decisión de misión» tiene una inclinación estructural que **ninguna prueba
de sensibilidad sobre solicitantes puede detectar**: reclasificar o reponderar titulares
no cambia de dónde vinieron los registros. Si la propia CPC se ha ido usando de forma
más amplia entre 2022 y 2025 —cosa plausible, dado que el volumen anual pasa de 2 a 23—,
el desplazamiento medido podría reflejar en parte el cambio de práctica clasificatoria
de la oficina y no un cambio de interés industrial.

El documento no lo menciona. Es la única objeción del frente patentario que no tiene
respuesta preparada en el texto, y es la que un tribunal con experiencia en análisis
patentario formulará primero. Basta con reconocerla como límite: la memoria ya sabe
escribir esas frases.

## 5.4. Veredicto del bloque 15

La revisión patentaria está **bien ejecutada y mal rematada**. El protocolo (fuente,
CPC, corte, unidad de análisis, anti-doble-conteo con manual OECD/WIPO citado), los dos
análisis de sensibilidad con número, y la advertencia sobre la cuota china y la
procedencia del 14,3 % estadounidense están todos donde deben estar y son de buena
calidad.

**El fallo está en una celda:** la Tabla 8 (p. 41) convierte «desplazamiento de la
actividad de protección» en «confirma pertinencia industrial» y añade una justificación
*post hoc* del diseño experimental. Es la única sobrelectura material que esta auditoría
encuentra en los dos corpus externos, y se corrige cambiando un verbo y borrando media
frase.

---

# 6. Trabajo futuro (bloque 38)

## 6.1. Dónde está

No hay una sección de trabajo futuro. Hay **cinco**:

| Lugar | p. | PDF | Contenido |
|---|---:|---:|---|
| §7.6 «Recomendaciones y trabajo futuro» | 66 | 83 | Cinco ítems de implementación |
| §7.7, cierre | 67 | 84 | «El trabajo futuro **más directo**…» + política aprendida como generador de propuestas |
| §7.8 «Recomendaciones por dimensión» | 67–68 | 84–85 | Teórica, económica, social |
| §7.9 «Condiciones bajo las que esta arquitectura no debe usarse» | 68–69 | 85–86 | Límites de uso |
| Anexo J.6 «Alcance y aporte» | 129 | 146 | La campaña congelada con sus factores |

## 6.2. ¿Lista de deseos o trabajo derivado de limitaciones reales?

**Derivado.** La correspondencia §7.5 → §7.6 es casi uno a uno:

| Limitación (§7.5, pp. 65–66) | Ítem de trabajo futuro |
|---|---|
| «Sus reglas integradas no reproducen todos los mecanismos parciales de SP1–SP2» | «Primero deben **sustituirse las reglas empíricas de Cargo** por los mecanismos de SP1–SP2 que se pretendan reclamar como integrados y **repetirse sus ablaciones**» |
| «omite soporte vertical, fricción 3D, deslizamiento, percepción y tracción rueda–suelo» | «Una **planta física independiente** deberá incorporar fricción, agarre, saturación, incertidumbre y ruido» |
| «los bancos activos no miden energía de radio» | «**ROS 2** permitirá medir edad de información, bytes, memoria, energía y CPU bajo topología móvil» |
| «Cargo considera **una carga** y un fallo simple» | «**Múltiples cargas** exigirán un oráculo espacio–temporal y comparadores publicados de subasta, MAPF y control» |
| «Tampoco se ensayaron agarre físico ni empuje por confinamiento geométrico» (p. 3) | «El **empuje/caging** mantendrá un modelo unilateral separado, con mundos pareados, ablaciones y resultados negativos conservados como regresión» |
| «Este trabajo no establece una función de Lyapunov común» | §7.8: «una **función de Lyapunov común, o un argumento de tiempo de permanencia**, para la conmutación entre modos de contacto, y una **prueba de compatibilidad entre los tres modelos de planta**» |

**No hay ni un ítem huérfano.** Cada uno nombra además *qué* haría falta, no solo *que*
haría falta: no dice «estudiar múltiples cargas» sino «múltiples cargas exigirán un
oráculo espacio–temporal y comparadores publicados». Eso es lo que separa un trabajo
futuro de una lista de deseos, y el capítulo lo hace bien.

## 6.3. ¿Está priorizado? Solo a medias, y hay dos «primeros» en competencia

- **p. 66:** «**Primero** deben sustituirse las reglas empíricas de Cargo por los
  mecanismos de SP1–SP2 […] y repetirse sus ablaciones.»
- **p. 67:** «El trabajo futuro **más directo** es la campaña congelada del Anexo J […]
  junto con extender CoppeliaSim a contacto y dinámica de ruedas antes de un piloto de
  hardware.»

Dos ítems distintos con marca de prioridad máxima, separados por una página, en
secciones distintas, sin que ninguno mencione al otro. Son compatibles —el primero es
condición de poder *reclamar* integración; el segundo es condición de poder *escalar*—
pero el lector no lo sabe y el texto no lo dice.

El resto del material (§7.8, Anexo J.6, la política aprendida) no lleva marca de
prioridad de ningún tipo.

## 6.4. ¿Distingue lo necesario para hardware de lo que es investigación?

**Implícitamente sí; explícitamente no.**

La **cadena de precondición para hardware sí está bien construida** y repartida en tres
frases:

1. p. 67: «extender CoppeliaSim a contacto y dinámica de ruedas **antes de** un piloto de
   hardware»;
2. p. 68 (§7.9): «**ningún resultado de esta memoria sostiene despliegue físico**: el
   verificador registró dos violaciones de barrera bajo el modelo declarado, lo que basta
   para exigir una **cota continua, no muestreada**, antes de cualquier prueba con
   hardware»;
3. p. 66: la planta física independiente con fricción, agarre, saturación, incertidumbre
   y ruido.

La cadena es correcta y la condición de bloqueo (violaciones de barrera → hace falta cota
continua) es específica y verificable. Es la mejor pieza del capítulo.

Lo que falta es la **etiqueta**. §7.6 mezcla en un mismo párrafo investigación
(«sustituir las reglas empíricas por los mecanismos de SP1–SP2», «múltiples cargas
exigirán un oráculo espacio–temporal») con ingeniería («ROS 2 permitirá medir bytes,
memoria, energía y CPU»). Son esfuerzos de naturaleza, coste y riesgo distintos y el
texto no los separa.

## 6.5. Comprobación ítem por ítem del bloque 38

| Ítem exigido | Estado | Dónde |
|---|---|---|
| Solo trabajos que derivan de limitaciones reales | **cumplido** | §7.5 → §7.6, correspondencia 6/6 |
| Prioridad | **parcial** | dos «primeros» (pp. 66 y 67); el resto sin orden |
| Hardware | **cumplido, y bien condicionado** | pp. 66, 67, 68 |
| Coppelia dinámica | **cumplido** | p. 67: «extender CoppeliaSim a contacto y dinámica de ruedas» |
| Fricción | **cumplido** | pp. 66 y 67 (factor de la campaña congelada) |
| Estimación | **AUSENTE** | Lo más cercano es «incertidumbre y ruido» (p. 66). §7.5 lista «**pose conocida**» como supuesto del modelo (p. 65) y no le da contrapartida en trabajo futuro |
| SLAM | **AUSENTE** | La cadena «SLAM» **no aparece ni una vez en 146 páginas**. «Percepción» aparece cuatro veces, siempre como omisión declarada (pp. 3, 11, 65, 116), nunca como línea futura |
| Múltiples cargas | **cumplido, con requisito** | p. 66 |
| Particiones | **MAL COLOCADO** | Las particiones persistentes aparecen en §7.9 como **condición de no uso** («Fuera del modelo de pérdidas Bernoulli — particiones persistentes, retardos no acotados — la mensajería vecinal no tiene garantía ensayada», p. 68) y en el anexo (p. 114), pero **nunca como ítem de trabajo futuro**, pese a que el modelo Bernoulli es limitación declarada. La Proposición 6.8 (p. 61) demuestra justo un límite bajo partición: es el ítem con motivación más fuerte del capítulo y no está en la lista |
| *Global hybrid stability* | **cumplido, y es el ítem mejor especificado** | p. 68: Lyapunov común **o** tiempo de permanencia, **más** prueba de compatibilidad entre los tres modelos de planta |
| JCC completo | **cumplido** | p. 67 y p. 129: campaña congelada del Anexo J, con factores enumerados (agentes, contacto activo, pérdida de miembro, homotopía, batería, fricción, retardo, presupuesto de cálculo) y con la salvaguarda metodológica «**no se escogerán solo los casos que ambos métodos completan como métrica principal**» |
| No convertir en una segunda tesis | **AL LÍMITE** | §§7.6–7.9 ocupan **cuatro páginas** (66–69). §7.8 abre tres dimensiones nuevas y la económica introduce una magnitud no medida (coste de cómputo por misión) con un requisito propio («medirlo en la plataforma de a bordo prevista, y no en una estación remota»). El material es bueno; el volumen es de agenda de investigación, no de cierre |

**Diez de doce ítems cubiertos.** Faltan estimación y SLAM; particiones está presente pero
en la sección equivocada.

## 6.6. Dos cosas que hay que defender, no corregir

- **§7.9, «Condiciones bajo las que esta arquitectura no debe usarse»** (pp. 68–69). Una
  sección que enumera cuándo el propio trabajo no aplica —congestión alta, cargas no
  planares, contactos móviles, más de una carga, fuera del modelo Bernoulli, cualquier
  despliegue físico— es infrecuente en un TFM y es exactamente lo que el marco de
  contratos del trabajo exige de sí mismo. Es coherencia entre lo que la tesis predica y
  lo que practica.
- **El párrafo de la política aprendida** (p. 67): «Sí encaja como generador de propuestas
  dentro del filtro: **la política propone y el certificado de wrench admite o se
  abstiene**, lo que conserva el contrato y es la vía de extensión más inmediata para la
  familia de métodos que SP1 ya compara». Es el mejor ítem de trabajo futuro del
  documento —concreto, barato, y derivado directamente de C1— y está fuera de §7.6.

## 6.7. Veredicto del bloque 38

**No es una lista de deseos.** El defecto es de **arquitectura del capítulo**, no de
contenido: cinco ubicaciones, dos prioridades máximas en competencia, sin etiqueta que
separe investigación de ingeniería, y dos ítems del criterio ausentes (estimación, SLAM)
más uno colocado en la sección equivocada (particiones).

Una tabla de tres columnas —*qué limitación lo motiva · tipo (teórico / ingeniería /
campaña) · prioridad*— absorbe las cinco ubicaciones sin escribir contenido nuevo y
resuelve simultáneamente la prioridad, la clasificación y el riesgo de «segunda tesis».

---

# 7. Hallazgos ordenados por severidad

| # | Bloque | Hallazgo | p. | Severidad |
|---|---|---|---:|---|
| **H1** | 10 | **No existe lista de contribuciones en ningún lugar del documento.** El índice no tiene epígrafe «Contribuciones»; §7.1 lo promete en el título y entrega un recuento de resultados | v, 63 | **Alta** |
| **H2** | 10 | La única frase que define la contribución con precisión está en la **última página, en un anexo, calificada de «candidata»** | 129 | **Alta** |
| **H3** | 10 | La sección titulada «Contribución» usa la palabra **solo en su acepción técnica** («contribución marginal») | 63 | **Alta** |
| **H4** | 11 | La rúbrica de ocho capacidades que condena a doce trabajos (Fig. 8) y a seis antecedentes (Tabla 28) **nunca se aplica al propio TFM**, mientras que la matriz industrial sí incluye su fila | 31, 92 vs 33 | **Alta** |
| **H5** | — | El recuadro de brecha (p. 29) y la Tabla 3 de dependencias globales (p. 16) **no se citan entre sí**; el matiz del recuadro cubre el corpus y no la implementación evaluada | 29, 16 | **Alta** |
| **H6** | 15 | «**Confirma pertinencia industrial**» (Tabla 8) contradice el «Qué certifica» de la Tabla 27; el bloque 15 lo prohíbe expresamente | 41 vs 89 | **Alta** |
| **H7** | 11 | El marcador «Este TFM» se imprime en la esquina **descentralizada** de un eje de autoridad de decisión que la Tabla 3 desmiente | 28, 30 vs 16 | Media |
| **H8** | 14 | **Ninguna de las catorce filas industriales tiene verificación independiente** y la Tabla 27 no lo declara entre lo que la revisión no certifica | 33, 89 | Media |
| **H9** | 14 | La matriz industrial no distingue **despliegue documentado de página de catálogo**; el lado académico sí lo hace (columna Ev.) | 33 vs 31 | Media |
| **H10** | 15 | «**Robusto** a la ampliación dirigida»: tres puntos en un eje son sensibilidad, no robustez; y figura, cuerpo y anexo nombran **dos operaciones distintas** con un solo nombre | 40, 41, 95 | Media |
| **H11** | 15 | «**y justifica el peso de SP1 en la campaña**»: justificación *post hoc*; el peso lo fijó qué etapas quedaron activas (p. 15) | 41 | Media |
| **H12** | 38 | **Dos ítems marcados como prioridad máxima** en secciones distintas, sin relación declarada | 66, 67 | Media |
| **H13** | 38 | Trabajo futuro repartido en **cinco ubicaciones** sin etiqueta que separe investigación de ingeniería | 66–69, 129 | Media |
| **H14** | 15 | El **sesgo estructural del CPC** G05D 1/69–1/6987 no se discute; ninguna sensibilidad sobre solicitantes puede detectarlo | 18, 90 | Media |
| **H15** | 11 | La novedad **solo se enuncia en negativo**; el documento nunca escribe la afirmación positiva correspondiente | 2, 29, 92 | Media |
| **H16** | 38 | **Estimación y SLAM ausentes**; «particiones» está en §7.9 (no uso) y no en trabajo futuro pese a que la Prop. 6.8 lo motiva | 65–69 | Baja |
| **H17** | 14 | «Doce trabajos […] frente a noventa y nueve» sin el denominador n = 244 ni la advertencia «no prevalencias» del pie original | 41 vs 37 | Baja |
| **H18** | 15 | Los tres paneles de la Fig. 17 corren sobre **167 / 123 / 75** sin decirlo en un solo lugar | 40 | Baja |
| **H19** | 15 | MM3 con un decimal sobre ventanas de 5–7 registros en los primeros años | 40 | Baja |
| **H20** | 14 | Casos de 2016 y 2020 auditados en 2026 sin nota de vigencia | 33 | Baja |
| **H21** | 11 | DMPC/NMPC es la única familia del bloque 11 sin contraste argumental en el marco teórico | 66 | Baja |

## Lo que está bien y hay que llevar a la defensa

1. **Cero reclamaciones de prioridad en 146 páginas.** Ocho formulaciones límite, ocho
   correctamente matizadas. Ninguna frase que retirar.
2. **Auditoría adversarial de novedad realizada y publicada** (Tabla 28, p. 92), con la
   autorrefutación explícita: «El resultado obliga a estrechar el enunciado: **el
   reemplazo durante el transporte ya existe**».
3. **Renuncia expresa a prioridad mundial** sobre los bloques genéricos (p. 129).
4. **«No documentado» no equivale a inexistencia** impreso dentro de la leyenda de la
   tabla que lo necesita, no en una nota remota (p. 33).
5. **Tabla 3** (p. 16): declaración etapa a etapa de qué es global y qué es local, con el
   conteo de mensajes declarado como **cota inferior** porque excluye la elección de
   líder y las consultas al registro (p. 13).
6. **Proposición 6.8 etiquetada como no nueva** por el propio autor (p. 61).
7. **Resultados negativos en el denominador**: H3 no sustentada, $\mathrm{PoA}_6=+\infty$,
   tres de cuatro escenarios de Industrial 2 sin entregas, cuatro hipótesis «no
   adjudicadas» con su razón (pp. 62–68).
8. **§7.9**, condiciones bajo las que la arquitectura no debe usarse (pp. 68–69).
9. **Tablas 26 y 27** (p. 89): cada capa de corpus ligada a la clase de afirmación que
   puede sostener, con «Qué certifica / Qué no certifica» por revisión.

## Las cinco correcciones de mayor rendimiento

Ninguna requiere generar evidencia nueva. Las cinco son de redacción o de disposición.

1. **Un párrafo «Contribuciones principales» al final del Capítulo 1**, con las cinco
   entradas de la sección 1.4 de este informe, cada una con su localización
   (Teor. 6.1 p. 42 · Prop. C.3 p. 83 · Tabla 22 p. 60 · ablaciones §7.1 · Tablas 26–27
   p. 89). Todo el material existe; falta la página que lo reúne. **Resuelve H1, H2, H3
   y H15.**
2. **Una fila «Este TFM (cuerpo activo)» en la Figura 8 y en la Tabla 28**, codificada
   con la misma rúbrica y con su nivel C tomado de la Tabla 3. **Resuelve H4 y H7, y
   desactiva H5 por anticipado.**
3. **Una oración subordinada dentro del recuadro de la p. 29**: que la implementación
   evaluada no alcanza la última condición del enunciado y que sus dependencias están en
   la Tabla 3. **Resuelve H5.**
4. **Cambiar un verbo y borrar media frase en la Tabla 8, fila 4** (p. 41): «Es coherente
   con la pertinencia industrial de la capa estratégica», sin la justificación del peso
   de SP1. Y sustituir «robusto» por las dos cifras de sensibilidad. **Resuelve H6, H10 y
   H11.**
5. **Una tabla de trabajo futuro de tres columnas** (limitación · tipo · prioridad) que
   absorba §7.6, el cierre de §7.7, §7.8 y J.6. **Resuelve H12, H13 y H16.**

---

*Este informe no modifica ningún fichero de la memoria. Todas las citas se reproducen
literalmente del PDF compilado del 2026-09-19 y pueden reverificarse con la
correspondencia página impresa = página PDF − 17.*
