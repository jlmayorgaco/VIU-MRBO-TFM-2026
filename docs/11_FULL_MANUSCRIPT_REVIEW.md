# Revisión integral del manuscrito: potencia científica, cierre formal y densidad editorial

**Fecha de auditoría:** 2026-07-16

**Objeto:** manuscrito LaTeX completo y PDF compilado de 139 páginas

**Modo:** revisión editorial completa, auditoría metodológica, diagnóstico de patrones de escritura y revisión visual
**Decisión:** **revisión mayor; el documento todavía no está listo para entrega**

## 1. Dictamen ejecutivo

El manuscrito **sí contiene aportes técnicamente potentes**. No es una memoria vacía ni una acumulación de simulaciones. Hay resultados formales propios sobre juegos potenciales, caracterización de equilibrios, integrabilidad de payoffs, factibilidad de wrench, estabilidad local de pose y recuperación tras fallos. La contribución más defendible no es, sin embargo, “un sistema distribuido completo de transporte cooperativo”, sino una **arquitectura de certificados y juegos locales por capas**, con garantías delimitadas y resultados negativos explícitos.

Los tres núcleos que merecen ocupar el centro de la defensa son:

1. **SP3:** juego continuo de selección mecánica cuyo payoff marginal es el gradiente de un potencial estrictamente cóncavo; bajo Slater, los KKT de la relajación coinciden con un equilibrio variacional. La guardia de wrench elimina falsos positivos dentro del modelo planar.
2. **SP4:** juego de vivacidad con equilibrio variacional único para una instantánea congelada y prueba de estabilidad asintótica local del servolazo planar de pose con contactos fijos y wrench exacto.
3. **SP6:** juego binario de re-reclutamiento con potencial exacto; umbral suficiente para que todo Nash restaure el certificado y sea mínimo por inclusión; contraejemplo que demuestra ineficiencia no acotada del peor Nash.

SP0, SP1 y SP2 proporcionan una escalera formal útil, pero hoy ocupan demasiado espacio respecto de su peso científico final. SP5 aporta evidencia empírica valiosa sobre la diferencia RAW--SAFE--EXEC y el intercambio seguridad--progreso. SP7 y SP8 son todavía protocolos propuestos sin resultados y no deben ocupar el mismo rango narrativo que los SP cerrados.

La **hipótesis principal no está acreditada**. Falta una ejecución que componga selección, cierre, certificado mecánico, docking, transporte, seguridad y recuperación usando exclusivamente estado propio, percepción local y mensajes vecinales. Las propias fuentes de verdad lo reconocen: H1 y H2 están parciales, H3 está pendiente, H4 está parcial y H5 está pendiente. Esta honestidad es una fortaleza; el problema editorial es que el resumen, los objetivos y la retórica de contribución todavía prometen más de lo demostrado.

La recomendación es **no añadir más teoremas aislados**. El documento ya tiene suficiente teoría local. Para elevar el aporte, hay que hacer una de dos cosas:

- **Ruta A, científica:** ejecutar una integración mínima SP3--SP4--SP6 sobre Cargo, con un fallo, una guardia y comunicación vecinal real o simulada; o
- **Ruta B, editorial:** estrechar la tesis a “juegos y certificados por capas para coordinación de coaliciones y transporte cooperativo”, dejando explícito que la composición distribuida extremo a extremo es trabajo futuro.

Sin una de esas dos decisiones, el texto parece prometer una arquitectura distribuida completa y entregar una colección rigurosa de subsistemas separados.

## 2. Respuesta directa: ¿están los aportes potentes?

### 2.1 Sí están

| Bloque | Resultado propio | Potencia | Límite que debe acompañarlo |
|---|---|---:|---|
| SP0 | Nash = asignaciones factibles bajo penalización; terminación; óptimos globales del potencial = matching óptimo | Media | Calibración homogénea, ocupación global exacta, sin planta |
| SP0 anexo | Cota grafo--gap, imposibilidad bajo desconexión, frontera de eficiencia e integralidad | Media/alta | Resultados auxiliares no ejecutados como arquitectura vecinal |
| SP1 | Cuotas exactas como Nash; degeneración bajo escasez; incentivo de cuórum; cierre QR | Media | QR central/global; campaña de desarrollo, no confirmatoria |
| SP2 | Score marginal integrable; score plano no integrable con capacidades heterogéneas | Media/alta | Preferencias continuas, capacidad efectiva fija, sin cierre ni red |
| SP3 | Potencial de wrench y equivalencia KKT--equilibrio variacional; guardia mecánica | **Alta** | Relajación continua, geometría fija, guardia central, modelo planar cuasiestático |
| SP4 | Potencial fuerte de vivacidad y equilibrio variacional único; estabilidad local de pose | **Alta** | Instantánea congelada; docking y transporte evaluados por separado |
| SP5 | Guardia RAW--SAFE--EXEC y evidencia del intercambio seguridad--progreso | Media/alta empírica | No hay invariancia muestreada ni red distribuida real |
| SP6 | Nash factibles y mínimos bajo umbral; PoA no acotado; cota temporal condicionada | **Alta** | Fallo simple, certificado aditivo, viaje rectilíneo, sin reanudación dinámica completa |
| SP7 | Juego local de congestión/prioridad | Baja en estado actual | Propuesta sin prueba ni campaña |
| SP8 | Auditoría calidad--cómputo--comunicación | Baja en estado actual | Propuesta sin barridos ni curvas |

### 2.2 El aporte nuclear todavía no está cerrado

La cadena declarada es:

`OBSERVED → ESTIMATED → RAW → CLOSED → GUARDED → EXECUTED`.

El manuscrito acredita fragmentos de esa cadena, no una trayectoria completa:

- SP0: CLOSED con ocupación exacta global.
- SP1: CLOSED mediante QR global.
- SP2: capacidad escalar con agregado global; no consenso vecinal.
- SP3: GUARDED con certificado central y una aproximación de anillo que deja mayor residual KKT.
- SP4: EXECUTED en dos simuladores separados: docking sin carga y transporte con contactos ya fijados.
- SP5: EXECUTED con geometría obtenida de un estado global y mensajes contabilizados, no transmitidos.
- SP6: CLOSED/GUARDED y llegada cinemática; no reanudación de la planta completa.
- SP7--SP8: sin evidencia ejecutada.

Por eso no es defendible afirmar todavía que “el método distribuido completo transporta cargas heterogéneas y se recupera de fallos”. Sí es defendible afirmar que el TFM **construye y valida certificados locales y juegos por capas, identifica dónde se rompe la composición y cuantifica varios costes de descentralización**.

## 3. Auditoría de teoremas, juegos y equilibrios

### 3.1 SP0 y SP1: correctos, útiles y sobrerrepresentados

Las pruebas de potencial exacto y terminación son directas y coherentes con un juego finito. La caracterización de Nash bajo demanda realizable es clara. Los resultados negativos —Nash subóptimos, precio de anarquía sin cota uniforme, déficit lineal degenerado bajo escasez— aumentan la credibilidad.

El problema no es matemático, sino de jerarquía. SP0 ocupa aproximadamente ocho páginas del cuerpo y diez del anexo. Para una tesis cuyo aporte físico aparece en SP3--SP6, dieciocho páginas de matching homogéneo desplazan el foco. La cota grafo--gap y la imposibilidad bajo desconexión son más relevantes para “distribuido” que varias figuras temporales de SP0; conviene preservar aquellas y recortar estas.

### 3.2 SP2: resultado elegante, pero no equivale a dinámica distribuida

La demostración de que el score ponderado por capacidad marginal es gradiente de un potencial, mientras el score plano viola simetría de derivadas cruzadas, es limpia y útil. Debe presentarse como **resultado estructural de integrabilidad**.

No debe venderse como convergencia de Smith, BNN o replicator. El propio texto reconoce que las etiquetas poblacionales de la campaña son reglas de ranking y no integraciones de las EDO. La red neuronal que obtiene el mejor rendimiento empírico distrae del núcleo white-box; debe quedar como comparador o análisis secundario, no como centro del aporte.

### 3.3 SP3 y SP4: precisión terminológica necesaria

Los cálculos de gradiente, concavidad/convexidad y KKT son consistentes con juegos poblacionales o juegos continuos de costes marginales. Sin embargo, en SP3 y SP4 se habla de “juego de potencial exacto” a partir de la coincidencia entre payoff y gradiente o de variaciones infinitesimales. En la tradición de Monderer--Shapley, “potencial exacto” suele exigir igualdad de **diferencias finitas de utilidad unilateral**. Si no se define una utilidad integral por jugador, la formulación más precisa es:

- “juego poblacional de potencial”;
- “campo de payoffs integrable con potencial”; o
- “juego continuo con potencial diferencial”.

Esto no destruye el resultado. Evita que un revisor cuestione la etiqueta cuando la prueba realmente establece integrabilidad y equivalencia variacional.

En SP4, la prueba de LaSalle es local y razonable bajo masa constante, contactos fijos, carta local de SE(2), matrices positivas y residual nulo. No cubre conmutación de contactos, saturación persistente, estimación de pose ni dinámica de rueda. La frase fuerte debe ser “estabilidad asintótica local del modelo planar reducido”, nunca “estabilidad del transporte cooperativo completo”.

### 3.4 SP6: el teorema más redondo, con una cota temporal conservadora

SP6 es la sección formal más completa: define juego, potencial, caracterización de entrada/salida, umbral suficiente, minimalidad y una frontera de eficiencia. El contraejemplo de coste arbitrariamente alto es especialmente valioso porque impide confundir equilibrio con optimalidad.

La cota temporal es formalmente válida bajo sus supuestos, pero el término `2^{n_R}-1` es una cota combinatoria gruesa; además presupone activación justa con separación temporal acotada, caminos libres y velocidad inferior garantizada. Debe denominarse “cota suficiente condicionada de arribo”, no garantía práctica de recuperación.

## 4. Auditoría de distribución

La palabra “distribuido” es el principal riesgo de sobreafirmación.

| Componente | Información usada en la evidencia | Estado real |
|---|---|---|
| Ocupación SP0 | vector exacto global | Centralizada |
| Cierre QR SP1 | matriz completa de preferencias | Centralizada |
| Déficit SP2 | agregado global para la mayoría de métodos | Centralizada/mixta |
| Juego SP3 exacto | agregados exactos y guardia central | Centralizada con ablación vecinal |
| SP3 anillo | cuatro rondas sobre grafo fijo | Aproximación distribuida; peor residual |
| Juego SP4 | conflictos y costes congelados | Resultado formal instantáneo; no red ejecutada completa |
| SP5 local | estado global filtrado por alcance; mensajes contados | Proxy informativo, no red |
| SP6 | déficit publicado por una carga; calibración global fuera de línea | Localizable, pero no integración de red |
| SP8 | sin experimento | Pendiente |

La tesis sí estudia mecanismos **distribuibles** y una variante vecinal concreta. No demuestra una arquitectura “estrictamente distribuida” en sentido operativo. Una redacción compacta y honesta sería:

> Se proponen juegos y certificados compatibles con información local; la evidencia actual valida sus propiedades por capas y una aproximación vecinal limitada, no la composición distribuida extremo a extremo.

## 5. Auditoría de control cooperativo

Hay control cooperativo, pero en alcance reducido:

- El reparto de wrench de SP3 es un certificado/optimizador cuasiestático, no un controlador de contacto cerrado con sensores.
- El docking de SP4 controla uniciclos hacia poses fijas, pero no lleva carga.
- El transporte de SP4 controla una carga planar con contactos ya establecidos y pose exacta.
- SP5 filtra el movimiento de una huella rígida y después realiza un wrench acotado; no demuestra invariancia tras muestreo y saturación.
- SP6 mueve reemplazos mediante un proxy rectilíneo y no reanuda el transporte dinámico.

Por tanto, el aporte de control es **una prueba local de estabilidad y una arquitectura RAW--SAFE--EXEC**, no un controlador cooperativo distribuido integral. Esta distinción debe aparecer en resumen, introducción y conclusiones, no solo en los límites de cada SP.

## 6. Auditoría empírica, estadística y reproducibilidad

### 6.1 Fortalezas

- Mundos y semillas pareadas.
- Fallos, colisiones y timeouts conservados en denominadores.
- Contrastes adecuados a endpoints binarios y continuos.
- Intervalos de confianza y corrección de Holm.
- Ablaciones explícitas y resultados negativos publicados.
- Separación entre oráculo central y comparación arquitectónica justa.
- Auditorías de invariantes, hashes y semántica RAW--SAFE--EXEC.
- La suite actual pasa: **50 pruebas superadas**.

### 6.2 Debilidades

1. **SP2 y SP3 no pueden regenerarse desde cero** porque sus generadores históricos fueron retirados. Se puede reproducir el postproceso desde CSV, no la campaña completa.
2. El anexo de reproducibilidad afirma todavía que solo SP0 posee cadena completa y que los demás SP “se incorporarán”. Está desactualizado respecto de SP4--SP6.
3. SP1 se presenta como evidencia de desarrollo; no debe mezclarse con campañas confirmatorias.
4. La reparación v4 de docking usa solo 12 mundos y no incorpora saturación de torque; sirve como evidencia descriptiva, no como cierre confirmatorio.
5. SP7 y SP8 carecen de configuraciones y resultados canónicos.

El nivel de reproducibilidad global debe declararse como **reproducibilidad completa para el código vigente y el postproceso; reproducción parcial de campañas históricas SP2/SP3**.

## 7. Bibliografía y “meta-referencias”

La consistencia local es buena:

- 83 claves citadas en el manuscrito.
- 90 entradas en `references.bib`.
- 90 entradas en el ledger, todas marcadas `VERIFICADA`.
- Ninguna cita carece de entrada BibLaTeX o de registro en el ledger.
- Siete referencias del `.bib` no se citan actualmente; pueden retirarse o reutilizarse solo si aportan una función concreta.

Las siete no citadas son: `cuturi2013sinkhorn`, `ponda2010dynamicCommunication`, `ren2004virtual`, `uribe2021dualDistributed`, `weed2018entropic`, `zavlanos2008distributedAuction` y `zlotStentz2006ComplexTasks`.

Esta auditoría verifica **consistencia interna**, no volvió a comprobar externamente cada DOI, página o interpretación. El ledger documenta esa verificación previa. No conviene añadir más referencias por volumen: el problema actual es sintetizar mejor las 83 ya usadas.

El mapa metodológico y varias tablas por SP repiten la función “método--supuesto--límite”. Es útil una tabla maestra en el capítulo 5 y, en cada SP, solo las diferencias necesarias para justificar baselines. La repetición actual da sensación de meta-revisión permanente y resta espacio al argumento propio.

## 8. Diagnóstico de patrones de escritura IA y “carreta”

### 8.1 Patrones críticos

**P0 — Texto de propuesta dentro de una memoria de resultados.**
El resumen y el abstract dicen que la validación “combinará”, “se comparará”, “se medirán” y “will combine/will be compared”. SP7, SP8 y las conclusiones continúan en futuro. Esto es el indicio más fuerte de documento inacabado; no es solo estilo.

**P0 — Conclusiones vacías.**
El capítulo 7 contiene únicamente frases como “Este apartado resumirá…” y “Este apartado declarará…”. No hay respuesta a objetivos, RQ ni hipótesis.

**P0 — Inconsistencia estructural.**
La introducción formula seis RQ; el capítulo de hipótesis y el charter contienen cinco. La trazabilidad posterior usa las cinco del charter. Debe conservarse una sola taxonomía.

### 8.2 Patrones de voz artificial o burocrática

1. **Metadiscurso de auditoría repetido.** Expresiones como “el estado acreditado”, “la auditoría actual”, “el repositorio conserva”, “la evidencia alcanzada”, “esta distinción” y “no se reinterpreta” aparecen con alta frecuencia. Son útiles una vez; repetidas convierten la memoria en informe de QA.
2. **Microestructura demasiado uniforme.** Cada SP repite escenario, problema, tabla de métodos, juego, control, simulación, resultados, aporte y transición con frases casi isomorfas. La consistencia ayuda, pero la cadencia predecible parece generada y diluye la jerarquía científica.
3. **Cautelas redundantes.** Se contabilizan 13 ocurrencias de “no demuestra” y 9 de “no prueba”, además de múltiples variantes. La honestidad debe conservarse, pero una limitación no necesita aparecer en introducción, tabla, pie, resultado y conclusión del mismo SP.
4. **Conectores mecánicos.** “Por tanto” aparece 36 veces y “en consecuencia” 12. Muchos son legítimos en pruebas; fuera de ellas producen prosa monótona.
5. **Tríadas y listas densas.** Se acumulan cadenas de tres a seis sustantivos —“estado, percepción, comunicación, seguridad y robustez”— que suenan completas pero no siempre añaden información.
6. **Negación contrastiva repetida.** “No X; Y”, “no implica”, “no sustituye”, “no hereda” es una figura útil para rigor, pero demasiado frecuente genera un tono defensivo.
7. **Rutas, IDs y nombres internos.** Identificadores de campaña y lenguaje del repositorio deben concentrarse en el anexo reproducible, no interrumpir la lectura científica.
8. **Cajas de contribución proliferantes.** SP1 tiene cuatro cajas y el anexo de SP0 contiene varias más. Cuando todo se rotula “aporte”, nada queda jerarquizado.

### 8.3 Qué conservar y qué eliminar

Conservar:

- Supuestos junto a cada teorema.
- Resultados negativos cuantificados.
- Diferencia entre equilibrio, óptimo, factibilidad mecánica y seguridad.
- Distinción RAW--SAFE--EXEC.
- Limitación principal al cierre de cada SP.

Eliminar o consolidar:

- Frases que anuncian lo que hará el capítulo.
- Repeticiones de la misma limitación dentro de una sección.
- Explicaciones del repositorio en el cuerpo.
- Tablas bibliográficas redundantes.
- Cajas de contribución secundarias.
- SP7/SP8 como “resultados” cuando son protocolos futuros.

## 9. Defectos editoriales y de maquetación

El PDF compila y, en general, tiene una maquetación limpia y consistente. No se observaron páginas cortadas ni figuras desbordadas en la inspección de las 139 páginas. Sí hay cuatro problemas:

1. **Extensión:** el cuerpo principal ocupa aproximadamente 97 páginas, por encima del máximo VIU de 80. Hay que recortar al menos 17; para dejar margen a unas conclusiones reales, el recorte bruto debería ser de 20--23 páginas.
2. **Anexos:** ocupan 22 páginas, dos por encima del máximo de 20.
3. **Tablas y referencias pequeñas:** varias tablas usan cuerpos de 5.8--6.1 puntos y las ocho páginas de bibliografía son visualmente muy densas. La legibilidad impresa es dudosa.
4. **Mapa metodológico:** las páginas 42--44 concentran tablas y gráficos demasiado pequeños; el coste visual supera su aporte narrativo.

El capítulo 6 ocupa unas 64 de las 97 páginas del cuerpo, aproximadamente 66 %, por lo que sí cumple la exigencia de dedicar al menos la mitad a resultados y análisis.

La compilación genera avisos repetidos de glifo `U+0016` en Arial. No se encontró ese carácter de control en las fuentes LaTeX incluidas; parece un efecto interno de la configuración tipográfica. No es visible en la inspección, pero conviene eliminar el aviso antes de la entrega para asegurar una compilación limpia.

## 10. Plan de compactación a 78--80 páginas

| Bloque | Actual aprox. | Objetivo | Acción |
|---|---:|---:|---|
| Introducción | 5 | 4--5 | Reescribir en presente/pasado y alinear 5 RQ |
| Objetivos + hipótesis | 5 | 4 | Eliminar mecanismos ya descartados y detalles de protocolo |
| Metodología | 9 | 6--7 | Pasar de texto prospectivo a protocolo ejecutado; eliminar repeticiones por SP |
| Marco teórico | 13 | 8--9 | Una tabla maestra; retirar mapa denso o moverlo al material suplementario |
| SP0 | 8 | 4--5 | Mantener proposición central, ablación y un resultado de eficiencia |
| SP1 | 8 | 5--6 | Unificar cuatro cajas en una contribución principal y un resultado negativo |
| SP2 | 9 | 6 | Centrar integrabilidad; comprimir catálogo de 13 métodos |
| SP3 | 9 | 7--8 | Proteger teoría, guardia, resultado de anillo y límites |
| SP4 | 7 | 6--7 | Proteger equilibrio y estabilidad; fusionar resultados secundarios |
| SP5 | 7 | 5--6 | Una figura del frente seguridad--progreso y una tabla compacta |
| SP6 | 7 | 6 | Proteger teoremas, PoA y resultado temporal |
| SP7 + SP8 | 6 | 1--2 | Mover a trabajo futuro; conservar solo preguntas y protocolo mínimo |
| Discusión transversal | 1 | 2--3 | Añadir matriz RQ/H/evidencia y explicar la no composición |
| Conclusiones | 1 vacía | 3--4 | Redactar respuestas reales, límites y contribución nuclear |

Una distribución viable es 78--80 páginas: recortar 23--25 páginas de metodología, marco, SP0--SP2 y SP7--SP8; reinvertir 3--4 en discusión y conclusiones.

### Regla de densificación por SP

Cada SP debería poder leerse con esta secuencia compacta:

1. **Una pregunta y una diferencia respecto del SP anterior.**
2. **Un resultado formal o mecanismo central.**
3. **Un experimento y una comparación principal.**
4. **Un resultado negativo o límite.**
5. **Una frase que diga qué estado de la cadena se alcanzó.**

Todo lo demás va al anexo, a una tabla transversal o se elimina.

## 11. Prioridades de revisión

### P0 — Bloqueos de entrega

1. Redactar conclusiones reales y una discusión transversal que responda a cinco RQ y H1--H5.
2. Actualizar resumen y abstract con resultados, cifras selectas y límites; eliminar el futuro.
3. Resolver la discrepancia de seis versus cinco preguntas de investigación.
4. Reescribir objetivos para que describan lo ejecutado; retirar o reclasificar sigmoide, Smith como mecanismo principal, empuje/caging completo y validaciones no realizadas.
5. Mover SP7 y SP8 a trabajo futuro o marcarlos como delimitación de alcance, no como resultados.
6. Declarar explícitamente que HP, H3 y H5 no están soportadas en su forma actual.
7. Restaurar los generadores de SP2/SP3 o degradar formalmente la afirmación de reproducibilidad integral.
8. Actualizar el anexo de reproducibilidad para SP1--SP6.
9. Reducir el cuerpo a 80 páginas y los anexos a 20.

### P1 — Fortalecimiento científico

1. Elegir Ruta A (integración mínima) o Ruta B (reencuadre por capas).
2. Recentrar la contribución en SP3--SP4--SP6; presentar SP0--SP2 como construcción y calibración.
3. Corregir la terminología de potencial exacto en SP3/SP4 o definir utilidades continuas que justifiquen la igualdad finita.
4. Añadir una tabla única que distinga por SP: información, equilibrio, certificado, planta, evidencia y último estado.
5. Separar en las conclusiones “demostrado”, “observado”, “refutado” y “pendiente”.
6. Si se ejecuta integración, usar un solo escenario Cargo con: coalición cerrada, guardia wrench, docking, transporte, obstáculo y fallo simple. Medir qué garantía sobrevive a cada interfaz.

### P2 — Calidad de prosa

1. Eliminar metadiscurso y frases de anuncio.
2. Sustituir cinco cautelas repetidas por una limitación precisa al final de cada SP.
3. Reducir conectores mecánicos y listas nominales.
4. Unificar cajas de contribución.
5. Trasladar IDs, rutas y manifiestos al anexo reproducible.
6. Revisar tamaños de tablas y bibliografía para lectura impresa.

## 12. Evaluación por perspectivas

### Editor académico

La contribución es suficiente para un TFM sólido si se estrecha la afirmación nuclear y se cierra la narrativa. La ausencia de conclusiones, la discrepancia de RQ y las secciones prospectivas impiden aprobar la versión actual como manuscrito final.

### Revisor metodológico

El diseño pareado, las auditorías y los resultados negativos son superiores a la media. La principal debilidad es la reproducibilidad incompleta de SP2/SP3 y la mezcla de campañas confirmatorias, de desarrollo y reparaciones descriptivas sin una síntesis final que las jerarquice.

### Revisor de juegos y control

Los resultados formales son plausibles y bien delimitados. SP3, SP4 y SP6 justifican el aporte. Debe precisarse el uso de “potencial exacto” en juegos continuos y evitar extrapolar KKT o LaSalle a cierre entero, contacto conmutado o red imperfecta.

### Revisor de sistemas distribuidos

La arquitectura completa no está validada como distribuida. Los agregados globales dominan SP0--SP3, SP5 simula localidad desde estado global y SP8 no tiene campaña. El manuscrito debe hablar de compatibilidad/distribuibilidad por capas o aportar la integración vecinal que falta.

### Abogado del diablo

Un evaluador hostil podría resumir el trabajo así: “Hay varios juegos y simuladores bien auditados, pero cada uno resuelve un subproblema diferente con información distinta; no existe el sistema distribuido que promete el título”. La revisión debe neutralizar esa crítica mediante un reencuadre explícito o un experimento integrador, no mediante más disclaimers.

## 13. Puntuación y decisión

| Criterio | Puntuación /100 | Observación |
|---|---:|---|
| Originalidad | 76 | Buena combinación de juegos, wrench, control y recuperación |
| Rigor formal | 80 | Resultados locales claros; precisión terminológica pendiente |
| Rigor experimental | 78 | Pareamiento, IC, Holm, negativos e invariantes sólidos |
| Distribución real | 48 | Predominan agregados globales y proxies de red |
| Control cooperativo integral | 58 | Buen modelo reducido; capas separadas |
| Reproducibilidad | 66 | Tests y postproceso sólidos; generadores faltantes |
| Coherencia narrativa | 49 | RQ inconsistentes, objetivos prospectivos, conclusiones vacías |
| Calidad de escritura | 61 | Clara pero repetitiva, defensiva y metadiscursiva |
| Densidad/eficiencia | 45 | 97 páginas de cuerpo y repetición estructural |
| Bibliografía | 84 | Ledger y consistencia local muy buenos |

**Decisión final: revisión mayor.**

**Potencial tras revisión:** TFM fuerte y defendible.
**Riesgo principal:** seguir añadiendo capas y texto sin cerrar la afirmación nuclear ni compactar.

## 14. Evidencia técnica de esta auditoría

- Compilación exitosa del PDF: 139 páginas.
- Inspección visual de las 139 páginas mediante renderizado por lotes.
- Cuerpo principal estimado: 97 páginas; capítulo 6: 64 páginas; anexos: 22 páginas.
- Suite de pruebas: 50/50 superadas.
- Citas: 83 usadas, 0 faltantes en BibLaTeX, 0 faltantes en ledger.
- Ledger: 90/90 entradas marcadas `VERIFICADA`.
- Manuscrito no modificado durante la revisión; este informe es un artefacto separado.
