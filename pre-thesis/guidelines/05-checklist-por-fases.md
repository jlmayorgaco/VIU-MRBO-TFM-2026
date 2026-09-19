# Checklist maestro por fases (FASE 0–40)

> Parte de las directrices del TFM. Contenido copiado sin cambios de
> `GUIDELINES.md`, lineas 7308 a 8406. Indice en [`00-INDICE.md`](00-INDICE.md).

---

 Sí. Tomaría de GLM **la organización por fases, la idea de pre-entrega/entrega/defensa, la documentación del repositorio, backups y checks operativos**, pero reemplazaría todas sus “normas” genéricas por las reglas verificadas de tu Máster y añadiría los gates científicos que faltaban. GLM acertó en que conviene trabajar por fases y revisar memoria, código, bibliografía, defensa y entrega como productos distintos. 

Este sería mi **CHECKLIST MAESTRO FINAL — TFM VIU MROB**, pensado para usarlo con Sonnet/Codex y también como checklist humano del director/jurado.

---

# CHECKLIST MAESTRO — TFM VIU MROB

## Sistema de prioridad

Usaría estas etiquetas en todo el checklist:

* **[VIU]** requisito oficial de la titulación.
* **[P0]** bloquea depósito/defensa científica.
* **[P1]** no bloquea formalmente, pero baja seriamente la calidad.
* **[P2]** pulido profesional.
* **[OPT]** mejora opcional.

La tesis **no se declara final mientras exista un P0 abierto**.

---

# FASE 0 — REQUISITOS OFICIALES VIU

## 0.1 Formato obligatorio

* [ ] **[VIU/P0]** Usar la plantilla oficial.
* [ ] **[VIU/P0]** A4.
* [ ] **[VIU/P0]** Arial 12.
* [ ] **[VIU/P0]** Texto justificado.
* [ ] **[VIU/P0]** Interlineado 1.5.
* [ ] **[VIU/P0]** Márgenes según plantilla.
* [ ] **[VIU/P0]** Portada sin número.
* [ ] **[VIU/P0]** Preliminares con numeración romana.
* [ ] **[VIU/P0]** Cuerpo con numeración arábiga.
* [ ] **[VIU/P0]** PDF como versión final.

VIU establece para este máster un cuerpo de **50–80 páginas** y anexos de **máximo 20 páginas**. 

## 0.2 Extensión

* [ ] **[VIU/P0]** Cuerpo principal entre 50 y 80 páginas.
* [ ] **[VIU/P0]** Anexos ≤20 páginas.
* [ ] **[VIU/P0]** No contar portada, resumen, índices ni anexos dentro del cuerpo.
* [ ] **[VIU/P0]** Resultados + Análisis + Validación ≥50 % del cuerpo principal. 

## 0.3 Resumen

* [ ] **[VIU/P0]** Resumen 200–300 palabras.
* [ ] **[VIU/P0]** Abstract equivalente semánticamente.
* [ ] **[VIU/P0]** 3–5 palabras clave.
* [ ] Problema.
* [ ] Propósito.
* [ ] Metodología.
* [ ] Principales resultados.
* [ ] Principal resultado negativo.
* [ ] Conclusión.
* [ ] Limitación principal.

VIU exige explícitamente 200–300 palabras y 3–5 palabras clave. 

## 0.4 Referencias

* [ ] **[VIU/P0]** APA 7ª edición.
* [ ] Bibliografía temática.
* [ ] Bibliografía metodológica.
* [ ] Toda cita tiene referencia.
* [ ] Toda referencia relevante aparece citada.

APA 7 es obligatoria para esta titulación. 

---

# FASE 1 — IDENTIDAD CIENTÍFICA DEL TFM

## 1.1 Título

* [ ] Cada palabra del título corresponde a algo realmente demostrado.
* [ ] “Coordinación” definida.
* [ ] “Distribuida” definida.
* [ ] “Local” definida.
* [ ] “Múltiples AMR” demostrado.
* [ ] “Transporte cooperativo” realmente ejecutado.
* [ ] “Cargas heterogéneas” definido operacionalmente.
* [ ] “Entorno industrial” usado como dominio, no como falsa validación industrial.
* [ ] El título oficial coincide con el registrado o se documenta cualquier cambio.

## 1.2 Pregunta central

Debe poder decirse en una frase.

* [ ] Problema físico/robótico inequívoco.
* [ ] Pregunta central inequívoca.
* [ ] Contribución central inequívoca.
* [ ] Limitación central inequívoca.
* [ ] La tesis completa puede explicarse sin recurrir primero a códigos E0–E8.

## 1.3 Historia científica

La narrativa debería ser aproximadamente:

$$
\text{seleccionar}
\rightarrow
\text{certificar capacidad/contacto}
\rightarrow
\text{transportar}
\rightarrow
\text{proteger}
\rightarrow
\text{recuperar}
\rightarrow
\text{coordinar tráfico}.
$$

* [ ] SP1 produce una salida consumible por SP2.
* [ ] SP2 produce una salida consumible por SP3.
* [ ] SP3 no parece otro paper pegado.
* [ ] Integración aparece como culminación natural.
* [ ] Cargo se presenta como demostrador funcional, no como composición formal si no lo es.

---

# FASE 2 — RQ, OBJETIVOS E HIPÓTESIS

## 2.1 RQ

Por cada RQ:

* [ ] Pregunta concreta.
* [ ] Respondible.
* [ ] Asociada a método.
* [ ] Asociada a evidencia.
* [ ] Contestada literalmente en conclusiones.
* [ ] Sin pregunta doble escondida.
* [ ] Sin prometer una validación fuera del alcance.

## 2.2 Objetivo general

* [ ] Compatible con título.
* [ ] Compatible con evidencia.
* [ ] No promete full-distributed si no existe.
* [ ] No promete hardware.
* [ ] No promete integración formal extrema-a-extrema si solo existe integración funcional.

## 2.3 OE

Para cada OE:

$$
OE
\rightarrow
RQ
\rightarrow
H
\rightarrow
\text{teoría/experimento}
\rightarrow
\text{resultado}.
$$

* [ ] No existe OE huérfano.
* [ ] No existe resultado central sin OE.
* [ ] Grado de cumplimiento declarado honestamente.

## 2.4 Hipótesis

Para cada H:

* [ ] Falsable.
* [ ] Variable independiente.
* [ ] Variable dependiente.
* [ ] Dirección esperada.
* [ ] Estimando.
* [ ] Unidad experimental.
* [ ] Regla de aceptación/rechazo.
* [ ] Familia de multiplicidad.
* [ ] Estado final coherente con los datos.

Especialmente:

* [ ] H1b revisada con la campaña QR.
* [ ] H1c revisada con cuórum vs lineal.
* [ ] H3 correctamente no sustentada.
* [ ] H5b revisada con \(A=64\).
* [ ] H6 separa prueba matemática de reproducción Coppelia.

---

# FASE 3 — TRAZABILIDAD COMPLETA

Crear una matriz maestra:

| Título/problem | RQ | OE | H | Método | Evidencia | Resultado | Conclusión |
| -------------- | -- | -- | - | ------ | --------- | --------- | ---------- |

Y comprobar:

* [ ] No hay columnas vacías.
* [ ] Cada claim fuerte tiene evidencia.
* [ ] Cada conclusión proviene de Resultados.
* [ ] Cada resultado tiene función narrativa.
* [ ] Cada hipótesis tiene un cierre.
* [ ] Cada teoría usada aparece antes de necesitarse.

---

# FASE 4 — ORGANIZACIÓN Y FLUIDEZ DEL DOCUMENTO

## 4.1 Macroestructura

* [ ] Introducción prepara exactamente la tesis final.
* [ ] Estado del arte conduce al gap.
* [ ] Gap conduce a metodología.
* [ ] Metodología conduce a experimentos.
* [ ] Resultados siguen la misma lógica de los objetivos.
* [ ] Conclusiones responden la introducción.

## 4.2 Cada capítulo

Debe tener:

* [ ] Introducción breve.
* [ ] Pregunta local.
* [ ] Desarrollo.
* [ ] Resultado local.
* [ ] Síntesis.
* [ ] Puente al capítulo siguiente.

## 4.3 “No-retazos test”

Buscar:

* [ ] nomenclatura histórica innecesaria;
* [ ] versiones antiguas de teoría;
* [ ] conceptos añadidos tardíamente;
* [ ] diferencias fuertes de voz;
* [ ] repeticiones de introducción;
* [ ] bloques que parecen mini papers independientes;
* [ ] material conservado porque “costó hacerlo”.

Todo bloque debe clasificarse:

$$
\boxed{\text{KEEP / REWRITE / MOVE / DELETE}}
$$

---

# FASE 5 — MARCO TEÓRICO Y ESTADO DEL ARTE

## 5.1 Función

VIU pide una revisión crítica de teorías, antecedentes, tecnologías y limitaciones. 

Cada subsección debe:

1. definir;
2. comparar;
3. criticar;
4. identificar límite;
5. justificar una decisión del TFM.

## 5.2 Calidad de literatura

* [ ] Fundacionales apropiados.
* [ ] Últimos trabajos 2024–2026.
* [ ] Papers más próximos.
* [ ] Revisiones recientes.
* [ ] Adversarial search contra nuestra novedad.
* [ ] No citation dumping.
* [ ] No “Autor A hizo…, Autor B hizo…” sin síntesis.

## 5.3 Fuentes

Clasificar:

* THEORY.
* ALGORITHM.
* EXPERIMENTAL.
* REVIEW.
* STANDARD.
* INDUSTRIAL.
* PATENT.
* DATA.
* SOFTWARE.

Y no usar:

> fabricante → theorem
> patent → industrial validation
> review → garantía primaria.

---

# FASE 6 — AUDITORÍA DE REFERENCIAS Y APA

## 6.1 Metadata

Por cada referencia:

* [ ] Existe.
* [ ] Autor correcto.
* [ ] Año correcto.
* [ ] Título exacto.
* [ ] Journal/conference correcto.
* [ ] Volumen/número.
* [ ] Páginas/article number.
* [ ] DOI correcto.
* [ ] DOI resuelve.
* [ ] Preprint sustituido por versión final si existe.
* [ ] No retractado.

## 6.2 APA 7

* [ ] `et al.` correcto en texto.
* [ ] Hasta 20 autores completos en bibliography.
* [ ] DOI como `https://doi.org/...`.
* [ ] Orden alfabético.
* [ ] Sangría francesa.
* [ ] Títulos en sentence case.
* [ ] Journal y volumen en cursiva.
* [ ] Corporate authors consistentes.
* [ ] Fechas de consulta solo cuando corresponden.

## 6.3 Claim-source audit

Para cada claim:

> ¿el paper realmente dice esto?

Estados:

* DIRECT.
* SYNTHESIS.
* AUTHOR INFERENCE.
* UNSUPPORTED.

Nada `UNSUPPORTED` en versión final.

---

# FASE 7 — NOVEDAD

* [ ] Claim de novedad específico.
* [ ] No decir “no existe”.
* [ ] Usar “no se identificó bajo el protocolo…”.
* [ ] Closest prior work claramente identificado.
* [ ] Diferencia con CBBA.
* [ ] Diferencia con MILP.
* [ ] Diferencia con DMPC.
* [ ] Diferencia con MAPF.
* [ ] Diferencia con MARL.
* [ ] Diferencia con cooperative manipulation.
* [ ] Diferencia con replacement existente.
* [ ] No presentar integración de componentes conocidos como un theorem nuevo si no lo es.

---

# FASE 8 — MATEMÁTICA

Por cada theorem/proposition/lemma:

* [ ] Enunciado.
* [ ] Supuestos.
* [ ] Dominio.
* [ ] Unidades.
* [ ] Prueba completa.
* [ ] Dependencias.
* [ ] Contraejemplo si existe.
* [ ] Implementación compatible.
* [ ] Resultado utilizado después.

Auditar especialmente:

* existencia ≠ convergencia;
* convergencia ≠ optimalidad;
* Nash ≠ óptimo social;
* estabilidad ≠ seguridad;
* seguridad ≠ progreso;
* terminación ≠ entrega;
* no-Zeno ≠ dwell time;
* convex branch ≠ hybrid global problem;
* graph factorization ≠ reduced locality.

---

# FASE 9 — JUEGO / ARQUITECTURA DE INTEGRACIÓN

Decidir definitivamente:

### Si es un juego

Debe definir:

$$
\mathcal G=
(\mathcal P,Y,\Gamma,J,\mathcal R,F,G).
$$

* [ ] jugadores/bloques;
* [ ] estado;
* [ ] información;
* [ ] acciones/continuaciones;
* [ ] conjunto certificado;
* [ ] payoff/cost;
* [ ] potencial;
* [ ] regla de revisión;
* [ ] incumbent;
* [ ] flow;
* [ ] reset;
* [ ] stopping/admission.

### Si no

Renombrar a:

> Arquitectura de Continuaciones Certificadas.

No llamar “juego” a una colección de certificados si el objeto global no está definido.

---

# FASE 10 — ROBÓTICA Y FÍSICA

## 10.1 Planta

* [ ] Pioneer P3-DX correctamente modelado.
* [ ] radio rueda;
* [ ] vía;
* [ ] wheel→twist;
* [ ] no-holonomía;
* [ ] torque;
* [ ] saturación;
* [ ] masa;
* [ ] inercia.

## 10.2 Contacto

* [ ] bilateral/unilateral.
* [ ] wrench.
* [ ] grasp/contact map.
* [ ] torque arm.
* [ ] fricción.
* [ ] tracción.
* [ ] slip.
* [ ] soporte.
* [ ] mantenimiento de contacto.

## 10.3 Sensores

* [ ] qué se mide;
* [ ] qué es exacto;
* [ ] qué se estima;
* [ ] qué queda fuera.

## 10.4 Realismo

Diferenciar:

$$
\text{modelo lógico}
\neq
\text{simulación cinemática}
\neq
\text{physics simulator}
\neq
\text{hardware}.
$$

---

# FASE 11 — “DISTRIBUTED” AUDIT

Para cada bloque:

| Elemento      | Local | Vecinal | Global |
| ------------- | ----: | ------: | -----: |
| medida        |       |         |        |
| agregados     |       |         |        |
| cierre        |       |         |        |
| QP            |       |         |        |
| líder         |       |         |        |
| registry      |       |         |        |
| planificación |       |         |        |

* [ ] Qué conoce cada robot.
* [ ] Qué consulta.
* [ ] Qué mensajes usa.
* [ ] Qué no se contabiliza.
* [ ] Qué depende de infraestructura global.
* [ ] El texto utiliza “distribuido” únicamente cuando corresponde.

---

# FASE 12 — DISEÑO EXPERIMENTAL

Para cada campaña:

* [ ] Pregunta.
* [ ] Hipótesis.
* [ ] Seed set.
* [ ] Unidad experimental.
* [ ] Tratamientos.
* [ ] Factores.
* [ ] Niveles.
* [ ] Baselines.
* [ ] Ablations.
* [ ] Oracles.
* [ ] Primary endpoint.
* [ ] Secondary endpoints.
* [ ] Horizon.
* [ ] Timeout.
* [ ] Failure definition.
* [ ] Success definition.
* [ ] Collision definition.
* [ ] Pre-specification.
* [ ] Raw data conservado.
* [ ] Ningún optional stopping.

---

# FASE 13 — ESTADÍSTICA

* [ ] Mundo/seed = unidad independiente.
* [ ] Pareamiento preservado.
* [ ] McNemar para binario pareado.
* [ ] Paired bootstrap CI.
* [ ] Wilcoxon cuando corresponde.
* [ ] Friedman si procede.
* [ ] Holm por familia coherente.
* [ ] IC del efecto.
* [ ] \(n\) explícito.
* [ ] Failures incluidos.
* [ ] Timeouts incluidos.
* [ ] No pseudo-replication.
* [ ] No “no significativo = equivalentes”.
* [ ] No causalidad desde contraste no causal.

---

# FASE 14 — COMPARADORES

Para cada método:

* [ ] Implementación corresponde al nombre.
* [ ] Si no, llamar “adaptación inspirada en…”.
* [ ] Información disponible declarada.
* [ ] Misma planta.
* [ ] Mismo escenario.
* [ ] Mismo horizonte.
* [ ] Misma unidad experimental.
* [ ] No comparar oracle con implementación local como si fueran arquitectónicamente equivalentes.

Categorías:

* oracle;
* exact small-instance solver;
* implementable central;
* distributed/local;
* proxy/adaptation;
* ablation.

---

# FASE 15 — RESULTADOS NEGATIVOS

Debemos buscar y conservar:

* [ ] H3.
* [ ] H5b a escala.
* [ ] Industrial 2.
* [ ] safety–progress tradeoff.
* [ ] worst Nash.
* [ ] non-convergence.
* [ ] timeouts.
* [ ] barrier residual after actuation.
* [ ] failed/limited theorems.

No esconderlos.

Integrarlos como:

$$
\boxed{\text{fronteras del mecanismo}}
$$

---

# FASE 16 — FIGURAS

Para cada figura:

* [ ] Vectorial si es plot.
* [ ] ≥300 dpi raster.
* [ ] Font ≥8 pt final; ideal 9–10.
* [ ] Cero clipping.
* [ ] Cero overlap.
* [ ] Labels legibles.
* [ ] Ejes.
* [ ] Unidades.
* [ ] \(n\).
* [ ] Error bars definidos.
* [ ] Colores consistentes.
* [ ] Colorblind-safe.
* [ ] Funciona en grayscale.
* [ ] Caption autosuficiente.
* [ ] Fuente.
* [ ] No white space absurdo.
* [ ] No figura decorativa.
* [ ] Revisada dentro del PDF.

Estados:

> KEEP / REDESIGN / SPLIT / MERGE / MOVE / DELETE.

---

# FASE 17 — TABLAS

* [ ] n.
* [ ] unidades.
* [ ] estimandos.
* [ ] IC.
* [ ] p-value cuando aplica.
* [ ] no texto microscópico.
* [ ] no cortes absurdos.
* [ ] oracle/proxy/ablation distinguidos.
* [ ] cifras consistentes con datos.
* [ ] caption explica población.

---

# FASE 18 — ECUACIONES

* [ ] Todas las variables definidas.
* [ ] Unidades coherentes.
* [ ] Signos correctos.
* [ ] Número.
* [ ] Referenciada en texto.
* [ ] Misma notación main/supp.
* [ ] No ecuación huérfana.
* [ ] No equation dump.

---

# FASE 19 — PSEUDOCÓDIGO

* [ ] Sintaxis.
* [ ] Indentación.
* [ ] Inputs.
* [ ] Outputs.
* [ ] Variables.
* [ ] `si/entonces/devolver`.
* [ ] No `si nodevolver`.
* [ ] Coincide con código real.
* [ ] Complejidad correcta.

---

# FASE 20 — REDACCIÓN ACADÉMICA

* [ ] Voz única.
* [ ] Español técnico natural.
* [ ] Frases preferentemente 15–35 palabras.
* [ ] Revisar >50 palabras.
* [ ] Un párrafo = una idea.
* [ ] Topic sentence.
* [ ] Evidencia.
* [ ] Interpretación.
* [ ] Puente.
* [ ] Evitar nominalización excesiva.
* [ ] Evitar traducciones literales.
* [ ] Evitar hype.

---

# FASE 21 — AI-WRITING / “TALLER INTERNO”

Eliminar del PDF final cuando sean innecesarios:

* [ ] `claim`.
* [ ] `gate`.
* [ ] `claim-ID`.
* [ ] `PASS/FAIL/LIMITED`.
* [ ] hashes.
* [ ] paths de repo.
* [ ] `complete=true`.
* [ ] “formulación previa”.
* [ ] “humo acotado”.
* [ ] “monograph-candidate”.
* [ ] lenguaje de pipeline.
* [ ] frases excesivamente templateadas.
* [ ] repetir “Resultado y alcance” mecánicamente.
* [ ] repetición excesiva “certifica/no certifica”.

La trazabilidad debe mantenerse **en repo**, no necesariamente imprimirse en el manuscrito.

---

# FASE 22 — ORIGINALIDAD / TURNITIN

VIU exige originalidad y advierte expresamente del uso de herramientas antiplagio. 

No utilizar un “umbral mágico”.

Gate real:

* [ ] 0 texto ajeno sin cita.
* [ ] 0 figuras adaptadas sin fuente.
* [ ] 0 referencias falsas.
* [ ] 0 paráfrasis demasiado próximas.
* [ ] 0 taxonomías apropiadas sin atribución.
* [ ] citas literales correctamente identificadas.
* [ ] main/supplement deduplicados.
* [ ] historial de autoría conservado.

---

# FASE 23 — REPRODUCIBILIDAD

Aquí rescato bastante del GLM.

* [ ] README.
* [ ] requirements/environment.
* [ ] versiones.
* [ ] seed lists.
* [ ] configs.
* [ ] raw results.
* [ ] processed results.
* [ ] scripts plots.
* [ ] scripts tables.
* [ ] manifests.
* [ ] commands exactos.
* [ ] Coppelia scene version.
* [ ] software versions.
* [ ] checksum interno.
* [ ] distinguir regenerate vs reanalyse.

GLM acierta al recomendar documentar dependencias, compilación, repo y problemas conocidos. 

---

# FASE 24 — CÓDIGO Y REPOSITORIO

No porque VIU exija GitHub público, sino por reproducibilidad.

* [ ] estructura clara.
* [ ] `.gitignore`.
* [ ] sin secrets.
* [ ] README.
* [ ] licencia cuando corresponda.
* [ ] commit final.
* [ ] tag/release final si conviene.
* [ ] scripts ejecutables.
* [ ] paths relativos.
* [ ] no depender de archivos temporales.
* [ ] código que genera tablas/figuras identificado.

---

# FASE 25 — COPPELIASIM

* [ ] Scene provenance.
* [ ] versión Coppelia.
* [ ] ZMQ.
* [ ] dt.
* [ ] wheel actuation.
* [ ] force transmission.
* [ ] force sensors.
* [ ] contact.
* [ ] friction.
* [ ] wheel→twist.
* [ ] closed loop vs replay.
* [ ] multi-dt.
* [ ] seeds.
* [ ] confirmatory manifest.

Claim permitido según evidencia:

> geometric/kinematic reproduction

hasta que física dinámica sea confirmada.

---

# FASE 26 — ANEXOS

* [ ] ≤20 páginas.
* [ ] Solo material necesario.
* [ ] Pruebas esenciales.
* [ ] Reproducibilidad mínima.
* [ ] No review histórica extensa.
* [ ] No atlas interno.
* [ ] No resultados candidatos.
* [ ] No teoría abandonada.

---

# FASE 27 — SUPPLEMENTARY

Debe complementar, no duplicar.

* [ ] pruebas extendidas;
* [ ] datos adicionales;
* [ ] sensibilidad;
* [ ] campañas históricas útiles;
* [ ] detalles reproducibles.

Eliminar del PDF público:

* [ ] raw PASS/FAIL ledger;
* [ ] hashes;
* [ ] `semantic-all.csv`;
* [ ] workflow del agente;
* [ ] candidatos no ejecutados;
* [ ] 30 páginas copiadas del main.

---

# FASE 28 — AUDITORÍA VISUAL COMPLETA

Página por página:

* [ ] No página casi vacía accidental.
* [ ] No label cortado.
* [ ] No URL aislada.
* [ ] No heading huérfano.
* [ ] No tabla cortada absurdamente.
* [ ] No caption separada.
* [ ] No figure demasiado pequeña.
* [ ] No box repetitivo innecesario.
* [ ] TOC compacto.
* [ ] Abstract cabe bien.
* [ ] keywords no saltan a página vacía.
* [ ] nomenclatura compacta.
* [ ] ritmo visual consistente.

---

# FASE 29 — BIBLIOGRAFÍA FINAL

Gate automático:

$$
C=\{\text{citas}\},
\qquad
R=\{\text{referencias}\}
$$

Exigir:

$$
\boxed{C=R}
$$

y:

* [ ] 0 DOI rotos.
* [ ] 0 metadata incorrecta.
* [ ] 0 `et al.` indebidos.
* [ ] 0 duplicados.
* [ ] 0 preprints obsoletos.
* [ ] 0 corporate pages presentadas como evidence científica.
* [ ] ISO actualizado.

---

# FASE 30 — CONCLUSIONES

* [ ] Respuesta pregunta central.
* [ ] RQ1–RQ6.
* [ ] OE1–OE6.
* [ ] H1–H6.
* [ ] Principal contribución.
* [ ] Principal resultado positivo.
* [ ] Principal resultado negativo.
* [ ] Limitaciones.
* [ ] Condiciones donde NO usar.
* [ ] Trabajo futuro derivado de gaps reales.
* [ ] Ninguna teoría nueva.
* [ ] Ningún claim nuevo.

---

# FASE 31 — “REVIEWER 1” FINAL

Preguntas:

* [ ] ¿Qué theorem es nuevo?
* [ ] ¿Qué theorem es estándar?
* [ ] ¿Dónde están los supuestos?
* [ ] ¿Dónde está la definición formal del juego?
* [ ] ¿Nash implica optimalidad?
* [ ] ¿Converge el algoritmo implementado?
* [ ] ¿Qué ocurre al discretizar?
* [ ] ¿La localidad es real?
* [ ] ¿Qué prueba la factorización?
* [ ] ¿Cuál es el contraejemplo?

---

# FASE 32 — “REVIEWER 2” FINAL

* [ ] ¿El modelo representa un AMR?
* [ ] ¿Cómo se transmite fuerza?
* [ ] ¿Dónde está fricción?
* [ ] ¿Qué pasa con slip?
* [ ] ¿Qué es simulado?
* [ ] ¿Qué es impuesto?
* [ ] ¿Qué es medido?
* [ ] ¿Qué validó Coppelia?
* [ ] ¿Qué falta para hardware?
* [ ] ¿Los baselines son reales?

---

# FASE 33 — JURADO VIU

El autor debe poder responder sin buscar:

* [ ] ¿Cuál es la tesis en una frase?
* [ ] ¿Cuál es el aporte?
* [ ] ¿Qué es distribuido?
* [ ] ¿Qué significa heterogéneo?
* [ ] ¿Por qué juegos?
* [ ] ¿Por qué no MILP siempre?
* [ ] ¿Por qué H3 falló?
* [ ] ¿Qué pasa a 64 coaliciones?
* [ ] ¿Qué certifica wrench?
* [ ] ¿Qué no certifica?
* [ ] ¿Qué validó Coppelia?
* [ ] ¿Qué falta para industrialización?

---

# FASE 34 — DEFENSA

De GLM sí rescataría preparar una narrativa breve y backups. 

Preparar:

* [ ] versión 30 s.
* [ ] versión 2 min.
* [ ] presentación completa.
* [ ] backup PDF.
* [ ] vídeo si mejora la explicación.
* [ ] backup local.
* [ ] demo no dependiente de internet si es posible.
* [ ] 20–30 preguntas adversariales.
* [ ] slides de backup con matemáticas/datos.

No imponer 10–15 min hasta verificar la convocatoria real.

---

# FASE 35 — CONGELACIÓN FINAL

Antes de depositar:

* [ ] commit final identificado;
* [ ] datos congelados;
* [ ] figures congeladas;
* [ ] bibliography congelada;
* [ ] PDF final generado desde source limpio;
* [ ] supplementary final;
* [ ] versión archivada;
* [ ] SHA interno si se desea;
* [ ] README final.

---

# FASE 36 — GATES AUTOMÁTICOS

Quiero que Sonnet/Codex compruebe automáticamente:

```text
LaTeX errors ............... 0
Undefined references ....... 0
Duplicate labels ........... 0
Critical bib warnings ...... 0
Broken DOI ................. 0
Citation without ref ....... 0
Ref without citation ....... 0
Figure clipping ............ 0
Known stale macros ......... 0
P0 claims .................. 0
```

Y además:

```text
Body pages ................. 50–80
Annex pages ................ <=20
Results fraction ........... >=50%
Spanish abstract ........... 200–300 words
English abstract ........... 200–300 words
Keywords ................... 3–5
APA 7 ...................... PASS
```

---

# FASE 37 — GATES HUMANOS

La automatización no puede aprobar:

* [ ] calidad matemática;
* [ ] novedad;
* [ ] claridad;
* [ ] coherencia narrativa;
* [ ] calidad visual;
* [ ] plausibilidad física;
* [ ] AI-writing feel;
* [ ] sobreclaims.

Estos requieren revisión humana.

---

# FASE 38 — TEST DE LECTURA FINAL

Realizar:

### Heading-only test

Leer solo títulos.

### Figure-only test

Leer figuras + captions.

### First-sentence test

Leer primera frase de cada párrafo.

### Cold chapter test

Abrir un capítulo al azar.

### 5-second figure test

Entender el mensaje visual principal.

### Read-aloud test

Detectar frases artificiales o demasiado largas.

### Tribunal test

Preguntar “¿y por qué?” cinco veces seguidas.

---

# FASE 39 — CHECKLIST DE ENTREGA

GLM acierta en que la propia operación de entrega debe revisarse. 

* [ ] PDF correcto.
* [ ] No draft.
* [ ] Nombre correcto.
* [ ] Supplement correcto si se entrega.
* [ ] Código/datos si la convocatoria lo exige.
* [ ] Archivos abren.
* [ ] Links funcionan.
* [ ] Página inicial correcta.
* [ ] Director/tutor correcto.
* [ ] Fecha correcta.
* [ ] Confirmar recepción/subida.

---

# FASE 40 — CRITERIO “10/10”

No usaría la frase de GLM “la práctica vale más que la teoría”. En nuestro caso, la regla correcta sería:

$$
\boxed{
\text{10/10}
=
\text{pregunta clara}
+
\text{teoría correcta}
+
\text{evidencia sólida}
+
\text{claims exactos}
+
\text{narrativa excelente}
+
\text{presentación impecable}
}
$$

Y el **gate final absoluto**:

> Para cada término del título, cada objetivo, cada hipótesis, cada theorem, cada tabla, cada figura y cada frase de conclusión, debemos poder señalar exactamente **qué evidencia lo sostiene y dentro de qué dominio es verdadero**.

Ese sería el checklist que yo usaría como **documento canónico**. Lo mejor del GLM queda —fases, documentación, backups, preparación operativa—, pero las normas inventadas desaparecen y el centro pasa a ser lo que realmente exige VIU y lo que un tribunal técnico serio va a revisar.