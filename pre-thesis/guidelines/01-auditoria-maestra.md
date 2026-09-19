# Auditoria maestra — los 60 frentes de revision

> Parte de las directrices del TFM. Contenido copiado sin cambios de
> `GUIDELINES.md`, lineas 1 a 984. Indice en [`00-INDICE.md`](00-INDICE.md).

---

Sí. Para una revisión verdaderamente completa no conviene pensar solo en “corregir redacción”. Yo la trataría como si el documento pasara sucesivamente por **director de TFM, metodólogo, matemático, especialista en teoría de juegos, roboticista, controlista, estadístico, Reviewer 1, Reviewer 2, editor académico, Turnitin y tribunal**.

Propongo que creemos un **Master Review Checklist** y que después vayamos definiendo cada ítem con: qué revisar, preguntas adversariales, criterios de aceptación y cambios concretos. Para este TFM, mi esquema maestro sería el siguiente.

1. **Conformidad administrativa y normativa VIU**

   * Título oficial frente al registrado/aprobado.
   * Uso consistente de AMR/AGV.
   * Plantilla oficial.
   * Portada, tutor, edición y fecha.
   * Número de páginas del cuerpo.
   * Máximo de páginas de anexos.
   * Porcentaje mínimo de Resultados/Análisis/Validación.
   * Extensión del Resumen/Abstract.
   * Número de palabras clave.
   * Índices obligatorios.
   * Numeración romana/arábiga.
   * Formato de referencias.
   * Formato de figuras, tablas y ecuaciones.
   * Márgenes, tipografía, interlineado, encabezados.
   * Correspondencia exacta entre índices y contenido.

2. **Coherencia entre título y tesis realmente realizada**

   * ¿La tesis responde literalmente a cada término del título?
   * “Coordinación”: ¿qué se coordina y mediante qué mecanismo?
   * “Distribuida”: ¿qué componentes son realmente distribuidos?
   * “Local”: ¿qué información es estrictamente local/vecinal?
   * “Múltiples AMR”: ¿cuántos, en qué experimentos y con qué escalado?
   * “Transporte cooperativo”: ¿hay transporte físico o solo asignación?
   * “Cargas heterogéneas”: ¿qué dimensión de heterogeneidad varía realmente?
   * “Entornos industriales”: ¿es dominio de aplicación, simulación industrial o validación industrial?
   * Identificar palabras del título que prometan más de lo demostrado.
   * Decidir si deben redefinirse en la introducción o cambiarse administrativamente.

3. **Problema científico**

   * ¿Existe una pregunta central inequívoca?
   * ¿El problema está delimitado?
   * ¿Se distingue problema industrial de problema científico?
   * ¿Se explica por qué MRTA/coalición no basta?
   * ¿Se explica por qué capacidad no implica wrench?
   * ¿Se explica por qué wrench no implica transporte?
   * ¿Se explica por qué seguridad no implica progreso?
   * ¿Se explica por qué reserva discreta no implica seguridad continua?
   * ¿Se explica qué parte de ese problema aborda realmente el TFM?
   * ¿Está claro qué NO intenta resolver?

4. **Motivación y relevancia**

   * Relevancia científica.
   * Relevancia robótica.
   * Relevancia industrial.
   * Relevancia de sistemas multiagente.
   * Necesidad real de múltiples AMR.
   * Justificación de heterogeneidad.
   * Justificación de comunicación local.
   * Justificación de resiliencia/fallo.
   * Justificación de tráfico multi-coalición.
   * Evitar motivaciones grandilocuentes no cuantificadas.
   * Diferenciar “impacto esperado” de “impacto demostrado”.

5. **Preguntas de investigación — RQ**

   * ¿Cada RQ es contestable?
   * ¿Cada RQ tiene datos o teoría que la responden?
   * ¿Hay RQ demasiado amplias?
   * ¿Hay RQ dobles que deberían separarse?
   * ¿Se introducen todas antes de responderlas?
   * ¿Se contestan literalmente en conclusiones?
   * ¿RQ6 pregunta algo que Coppelia realmente puede contestar?
   * ¿Alguna RQ quedó obsoleta tras evolucionar la tesis?
   * Construir matriz RQ → método → evidencia → conclusión.

6. **Objetivo general**

   * ¿Coincide con el título?
   * ¿Coincide con la contribución final?
   * ¿Es realizable con la evidencia existente?
   * ¿Promete arquitectura completamente distribuida?
   * ¿Promete integración física que Cargo no ejecuta?
   * ¿Usa verbos verificables?
   * ¿Puede declararse cumplido, parcialmente cumplido o no cumplido sin ambigüedad?

7. **Objetivos específicos — OE**

   * OE1–OE6: uno por uno.
   * ¿Cada OE produce un entregable verificable?
   * ¿Cada OE está asociado a una RQ?
   * ¿Cada OE está asociado a uno o más experimentos/teoremas?
   * ¿Hay objetivos redundantes?
   * ¿Hay objetivos añadidos después y no formalizados?
   * ¿Hay objetivos originales que quedaron abandonados?
   * ¿OE4/escala está realmente evaluado?
   * ¿OE6 define claramente integración vs composición?
   * Matriz OE → evidencia → estado final.

8. **Hipótesis**

   * Redacción falsable de HP y H1–H6.
   * Variable independiente.
   * Variable dependiente.
   * Dirección esperada.
   * Dominio.
   * Regla de decisión.
   * Estimando.
   * Unidad experimental.
   * Multiplicidad.
   * ¿Hipótesis definida antes de resultados?
   * ¿Hay circularidad entre definición y prueba?
   * ¿Alguna hipótesis es tautológica?
   * ¿H1b/H1c tienen ya evidencia suficiente?
   * ¿H5b está realmente refutada por \(A=64\)?
   * ¿H3 está correctamente clasificada como no sustentada?
   * ¿H6 mezcla matemática y Coppelia de manera inapropiada?
   * Tabla final coherente entre hipótesis, evidencia y estado.

9. **Trazabilidad integral**

   * Título → problema.
   * Problema → RQ.
   * RQ → OE.
   * OE → hipótesis.
   * Hipótesis → estimando.
   * Estimando → experimento/teorema.
   * Experimento → resultado.
   * Resultado → conclusión.
   * Conclusión → contribución.
   * Detectar cualquier elemento “huérfano”.
   * Detectar resultados valiosos que no responden a ninguna RQ/OE/H.
   * Detectar RQ/OE/H sin evidencia.
   * Crear una matriz maestra única.

10. **Contribuciones científicas**

    * Enumerar exactamente 3–5 contribuciones.
    * Separar contribución matemática.
    * Separar contribución metodológica.
    * Separar contribución experimental.
    * Separar contribución de ingeniería/software.
    * Separar integración de componentes de novedad algorítmica.
    * No llamar contribución a utilizar métodos conocidos.
    * No confundir “primera vez que yo lo implemento” con novedad científica.
    * Determinar cuál es la contribución principal que debe recordar el tribunal.

11. **Originalidad y novedad**

    * Claim de novedad principal.
    * Novedad de SP1.
    * Novedad de SP2.
    * Novedad de SP3.
    * Novedad del juego/arquitectura de integración.
    * Diferencia frente a MRTA.
    * Diferencia frente a CBBA.
    * Diferencia frente a MILP.
    * Diferencia frente a DMPC/NMPC.
    * Diferencia frente a MAPF.
    * Diferencia frente a MARL/GNN.
    * Diferencia frente a cooperative manipulation.
    * Diferencia frente a trabajos que ya hacen replacement.
    * Buscar antecedentes que puedan invalidar un “no existe”.
    * Expresar novedad como “no se identificó bajo este protocolo”, cuando corresponda.

12. **Estado del arte académico**

    * Estrategia de búsqueda.
    * Bases consultadas.
    * Fecha de corte.
    * Queries.
    * Criterios de inclusión/exclusión.
    * Deduplicación.
    * Corpus descubierto.
    * Corpus analítico.
    * Corpus canónico.
    * Lectura cercana.
    * Justificación de por qué ciertos trabajos son los más próximos.
    * Evitar llamar “systematic review” si no cumple ese estándar.
    * Coherencia de cifras 3014/244/59/etc.
    * Reproducibilidad del corpus.
    * Actualidad de referencias 2025–2026.
    * Ausencia de cherry-picking.

13. **Bibliometría**

    * ¿Las gráficas responden una pregunta relevante?
    * ¿Los denominadores son claros?
    * Clasificación multietiqueta.
    * Periodos comparables.
    * Año 2026 incompleto.
    * Modularity \(Q\).
    * Comunidades.
    * Coautoría.
    * No inferir “agenda dominante” desde modularidad.
    * No inferir causalidad desde tendencias.
    * Sensibilidad a clasificación/codificación.
    * Legibilidad de etiquetas.
    * Evitar gráficos bonitos sin valor argumental.

14. **Estado industrial**

    * Qué significa “precedente industrial”.
    * Evidencia del fabricante vs verificación independiente.
    * Casos con carga compartida real.
    * Número real de vehículos.
    * Selección dinámica.
    * Control central/local.
    * Replacement.
    * Certificación mecánica.
    * No inferir ausencia de capacidad de “no documentado”.
    * No llamar validación industrial al piloto de simulación.
    * Vigencia de productos y fuentes.
    * Consistencia de año del caso vs año de la página web.

15. **Patentes**

    * Fuente del dataset.
    * Cobertura temporal.
    * CPC utilizados.
    * Duplicados/familias.
    * Solicitantes.
    * Balanceo.
    * Ampliación dirigida.
    * Sensibilidad del cambio +20.9 p.p.
    * No interpretar patentes como adopción industrial.
    * No confundir registros con invenciones independientes.
    * Leyendas y denominadores.
    * Países y titulares correctamente identificados.

16. **Marco normativo**

    * VDA 5050.
    * ISO 21423.
    * ISO 3691-4.
    * ANSI/A3 R15.08.
    * Estado actual de cada norma.
    * Título exacto.
    * Fecha y versión.
    * Qué regula realmente.
    * Qué NO regula.
    * No presentar ausencia normativa como prohibición.
    * No afirmar que una norma “no cubre” algo sin haber revisado su alcance.

17. **Arquitectura global de la tesis**

    * ¿SP1, SP2 y SP3 forman realmente una sola historia?
    * ¿Cada salida es entrada de la siguiente capa?
    * ¿Los contratos están formalmente definidos?
    * ¿Existe información suficiente en la interfaz?
    * ¿Se transporta la misma semántica entre capas?
    * ¿La integración es matemática o solo funcional?
    * ¿Cargo ejecuta realmente SP1+SP2+SP3?
    * ¿Qué mecanismos sustituye Cargo por reglas simplificadas?
    * ¿Existe una autoridad global escondida?
    * Diagrama definitivo de arquitectura.

18. **SP1 — formación de coaliciones**

    * E1/cuotas.
    * E2/servicio heterogéneo.
    * E3/contactos y wrench.
    * Exactitud del potencial.
    * Penalización suficiente.
    * Escasez.
    * QR.
    * Cuórum.
    * Integrabilidad del pago marginal.
    * Cierre entero.
    * Diferencia relajación/solución entera.
    * Dependencias globales.
    * Heterogeneidad realmente modelada.
    * Correspondencia entre teoría y código.
    * Comparadores correctos.

19. **SP2 — transporte**

    * Modelo de uniciclo.
    * Modelo de ruedas.
    * Dinámica de carga.
    * Contactos.
    * Bilateralidad.
    * Fricción.
    * Saturaciones.
    * Matriz de agarre.
    * Wrench.
    * Transformación rueda–twist.
    * No-holonomía.
    * Servo PD.
    * Lyapunov.
    * Dominio local.
    * LaSalle.
    * Realización exacta/no exacta.
    * Safety vs progress.
    * CBF/HOCBF.
    * Saturación posterior.
    * Recuperación.
    * Tiempo de llegada del reemplazo.
    * Falta de contacto físico real.

20. **SP3 — planificación y tráfico**

    * Definición de ruta.
    * Catálogo finito.
    * Potencial exacto.
    * Penalización de congestión.
    * Reservas.
    * Testigo.
    * Exclusión mutua.
    * Inanición.
    * Deadlock.
    * Liveness.
    * Condición \(\lambda_7>\theta_7\).
    * ¿Se verificó la premisa o solo la conclusión?
    * Huella extendida.
    * Tiempo discreto.
    * Interpolación continua.
    * Diferencia MAPF vs control continuo.
    * Escala E8.
    * Red degradada.
    * Calidad a \(A=64\).

21. **Juego de integración / futuro JCC**

    * ¿Es realmente un juego o una arquitectura?
    * Definir jugadores/bloques.
    * Estado.
    * Información.
    * Acciones/continuaciones.
    * Conjunto admisible.
    * Costes/utilidades.
    * Potencial.
    * Factores.
    * Regla de revisión.
    * Incumbente.
    * Flujo continuo.
    * Saltos.
    * Condiciones de aceptación.
    * Información causal.
    * Presupuesto.
    * Seguridad.
    * Recuperación.
    * Reservas.
    * Qué resultado es nuevo.
    * Qué resultado es estándar.
    * Qué se demuestra solo por rama.
    * Qué NO se demuestra globalmente.
    * Nombre definitivo.

22. **Auditoría matemática general**

    * Definiciones antes del uso.
    * Dominios.
    * Dimensiones.
    * Unidades.
    * Existencia.
    * Unicidad.
    * Convexidad.
    * Concavidad.
    * Strong convexity.
    * Slater.
    * Compactitud.
    * Continuidad.
    * Diferenciabilidad.
    * Lipschitz.
    * Monotonicidad.
    * Integralidad.
    * Saturación.
    * Restricciones compartidas.
    * Condiciones necesarias vs suficientes.
    * Implicaciones “si” vs “si y solo si”.
    * Casos degenerados.

23. **Teoremas, proposiciones y lemas**

    * Enunciado exacto.
    * Hipótesis completas.
    * Dominio explícito.
    * Demostración completa.
    * Dependencias de otros resultados.
    * No circularidad.
    * No utilizar evidencia empírica como premisa matemática.
    * No inferir premisa desde la conclusión.
    * No confundir existencia de Nash con convergencia del algoritmo.
    * No confundir convergencia con optimalidad.
    * No confundir estabilidad con seguridad.
    * No confundir terminación con entrega.
    * No confundir no-Zeno con dwell time.
    * No confundir factibilidad con optimalidad.

24. **Notación matemática**

    * Un símbolo, un significado.
    * Evitar reutilizar \(z,\rho,\lambda,S,R,K\).
    * Convención de \(\Phi\) maximizada/minimizada.
    * Vectores vs escalares.
    * Negrita.
    * Transpuesta.
    * Índices \(i,j,k\).
    * Conjuntos.
    * Normas.
    * SI.
    * Unidades de torque, energía, fuerza.
    * Ángulos.
    * Errores normalizados.
    * Consistencia main/supplement.

25. **Modelo físico y realismo robótico**

    * Pioneer P3-DX real vs modelo abstracto.
    * Radio de rueda.
    * Wheelbase.
    * Torque.
    * Masa.
    * Inercia.
    * Fricción.
    * Tracción.
    * Slip.
    * Saturación.
    * Contacto bilateral/unilateral.
    * Sensores.
    * Pose exacta vs estimada.
    * Latencia.
    * Percepción.
    * Error de odometría.
    * Actuadores.
    * Compliance.
    * Rigidez.
    * Qué es simulación idealizada.
    * Qué puede transferirse a hardware.

26. **Heterogeneidad**

    * Heterogeneidad de robots.
    * Heterogeneidad de cargas.
    * Heterogeneidad de requisitos.
    * Capacidad.
    * Batería.
    * Fuerza.
    * Masa.
    * Inercia.
    * Geometría.
    * Contactos.
    * Deadline.
    * Ruta.
    * Determinar qué dimensiones se varían realmente.
    * Ajustar título/claims en consecuencia.

27. **Distributed/locality audit**

    * Qué mide cada robot.
    * Qué conoce.
    * Qué recibe.
    * Qué estima.
    * Qué consulta globalmente.
    * Qué calcula un líder.
    * Qué calcula un servidor.
    * Qué está precargado.
    * Qué necesita un registro global.
    * Qué mensajes se contabilizan.
    * Qué mensajes se excluyen.
    * Qué parte es central.
    * Qué parte es distribuible pero no implementada.
    * Qué parte es realmente distribuida.
    * Eliminar cualquier uso ambiguo de “distribuido”.

28. **Diseño experimental**

    * Pregunta por experimento.
    * Hipótesis.
    * Unidad experimental.
    * Semillas.
    * Número de réplicas.
    * Factores.
    * Niveles.
    * Tratamientos.
    * Control.
    * Ablaciones.
    * Baseline.
    * Oráculo.
    * Métrica primaria.
    * Métricas secundarias.
    * Horizonte.
    * Timeout.
    * Definición de fallo.
    * Colisión.
    * Éxito.
    * Preespecificación.
    * Seeds congeladas.
    * No optional stopping.

29. **Estadística**

    * Independencia.
    * Pareamiento.
    * Bootstrap.
    * Número de remuestreos.
    * McNemar.
    * Wilcoxon.
    * Friedman.
    * Holm.
    * Familias de hipótesis.
    * IC de efectos, no solo IC por método.
    * Proporciones.
    * Efectos absolutos.
    * Significancia vs importancia práctica.
    * No interpretar “no significativo” como equivalencia.
    * Denominadores.
    * Failures/timeouts incluidos.
    * Multiple comparisons.
    * Small-n pilot vs confirmatory.

30. **Baselines y comparadores**

    * ¿Está realmente implementado el algoritmo que se nombra?
    * CBBA real vs adaptación.
    * ORCA real vs aproximación.
    * DMPC real vs proxy.
    * SCP real vs referencia de formulación.
    * MILP.
    * Hungarian.
    * Greedy.
    * Central planner.
    * Perfect information.
    * Ablations.
    * Igualdad de información.
    * Igualdad de planta.
    * Igualdad de horizonte.
    * No rankings injustos entre métodos con información distinta.

31. **Reproducibilidad**

    * Código.
    * Configuración.
    * Seeds.
    * Raw data.
    * Processed data.
    * Scripts de figura.
    * Scripts de tabla.
    * Manifest.
    * Versiones.
    * SHA.
    * Entorno.
    * Coppelia scene.
    * Dependencias.
    * Comandos.
    * Qué experimentos se pueden regenerar.
    * Qué experimentos solo se pueden reanalizar.
    * Qué generadores se perdieron.
    * Separar reproducibilidad de trazabilidad.

32. **CoppeliaSim**

    * Qué escena.
    * Qué objetos.
    * Dinámica encendida/apagada.
    * Replay vs closed-loop.
    * Wheel actuation.
    * Force transmission.
    * Contacts.
    * Friction.
    * Sensibilidad a \(\Delta t\).
    * Sensor data.
    * Actual state vs commanded path.
    * Seeds.
    * Número de corridas.
    * Confirmatory vs smoke.
    * Qué afirma y qué no afirma.
    * No usar “escena real”.
    * No usar “validación física” si no corresponde.

33. **Resultados negativos**

    * H3.
    * Industrial 2.
    * H5b/A=64.
    * Timeouts.
    * CBF safe-but-stuck.
    * KKT residual sin vivacidad.
    * Peor Nash sin cota.
    * Ablaciones que no ayudan.
    * Hipótesis inconclusas.
    * Presentarlos como descubrimientos de frontera, no esconderlos.

34. **Interpretación causal**

    * ¿Una ablación elimina una sola variable?
    * ¿El efecto puede atribuirse al mecanismo?
    * ¿Hay módulos que cambian simultáneamente?
    * ¿Se dice “causó” cuando solo se observó asociación?
    * ¿Hay mecanismos alternativos?
    * ¿La campaña identifica el mecanismo o solo es compatible con él?

35. **Validez interna**

    * Bugs.
    * Data leakage.
    * Misma semilla.
    * Diferencias de implementación.
    * Parámetros tuneados por método.
    * Oráculos privilegiados.
    * Post-hoc selection.
    * Missing runs.
    * NaNs.
    * Failures eliminados.
    * Independencia real.

36. **Validez externa**

    * Escenarios sintéticos.
    * Tamaño de flota.
    * Tipo de carga.
    * Geometría.
    * Planta planar.
    * Comunicación.
    * Sensores.
    * Falta de hardware.
    * Coppelia.
    * Industria.
    * Generalización a otros AMR.
    * Generalización a otra topología.
    * Generalización a múltiples cargas.

37. **Conclusiones**

    * Una conclusión por RQ.
    * Una por OE.
    * Una por hipótesis.
    * Contribuciones.
    * Resultados positivos.
    * Resultados negativos.
    * Limitaciones.
    * No introducir teoría nueva.
    * No introducir claims que no estén en resultados.
    * No inflar alcance.
    * Diferenciar “demostrado”, “observado”, “compatible con”.
    * Responder directamente a la pregunta principal.

38. **Trabajo futuro**

    * Solo trabajos que derivan de limitaciones reales.
    * Prioridad.
    * Hardware.
    * Coppelia dinámica.
    * Fricción.
    * Estimación.
    * SLAM.
    * Múltiples cargas.
    * Particiones.
    * Global hybrid stability.
    * JCC completo.
    * No convertir trabajo futuro en una segunda tesis dentro del capítulo final.

39. **Estructura narrativa**

    * ¿La historia se entiende sin conocer el proyecto?
    * Introducción → gap → método → resultados → conclusión.
    * Eliminar cronología de investigación.
    * Eliminar “antes pensábamos…”.
    * Eliminar decisiones internas del workflow.
    * Eliminar resultados históricos que no sostienen la tesis.
    * Evitar que el lector tenga que aprender E0–E8 además de SP1–SP3.
    * Mantener foco en una contribución central.

40. **Redacción académica**

    * Precisión.
    * Claridad.
    * Concisión.
    * Voz consistente.
    * Tiempo verbal.
    * Evitar nominalización excesiva.
    * Evitar frases >50–60 palabras.
    * Evitar listas dentro de párrafos.
    * Evitar traducciones literales del inglés.
    * Evitar anglicismos innecesarios.
    * Evitar “obviamente”, “claramente”, “notablemente”.
    * Evitar hype.
    * Evitar repetir la misma limitación cinco veces.

41. **Patrones de escritura asistida / AI-writing feel**

    * `claim`.
    * `gate`.
    * `claim-ID`.
    * “artefacto” en sentido de pipeline.
    * `commit`.
    * `digest`.
    * `belief`.
    * `PASS/FAIL/LIMITED`.
    * hashes visibles.
    * paths de repositorio en cuerpo.
    * “Resultado y alcance” repetido mecánicamente.
    * “certifica/no certifica” repetido con la misma sintaxis.
    * párrafos excesivamente simétricos.
    * tríadas constantes.
    * disclaimers repetidos.
    * prosa demasiado abstracta.
    * expresiones traducidas como “humo acotado”.
    * metadiscurso sobre cómo se escribió/revisó la tesis.
    * eliminar el taller interno sin eliminar trazabilidad.

42. **Plagio y similitud**

    * Frases copiadas de papers.
    * Definiciones demasiado próximas a las fuentes.
    * Descripciones de fabricantes.
    * Normas.
    * Captions.
    * Tablas adaptadas.
    * Figuras “inspiradas en”.
    * Texto main ↔ supplement duplicado.
    * Autocoincidencia potencial.
    * Citas necesarias.
    * Paráfrasis real vs sustitución de sinónimos.
    * Comprobar frases distintivas externamente.
    * Turnitin no puede predecirse exactamente; preparar trazabilidad de autoría.

43. **Referencias**

    * Cada cita existe.
    * Cada DOI resuelve.
    * Título exacto.
    * Autores exactos.
    * Año.
    * Journal/conferencia.
    * Volumen.
    * Número.
    * Páginas/article number.
    * Preprint vs peer reviewed.
    * Et al. incorrecto en bibliografía.
    * APA 7.
    * URLs.
    * Fechas de consulta.
    * Consistencia main/supplement.
    * Citas huérfanas.
    * Referencias no citadas.
    * Fuentes 2026 especialmente auditadas.

44. **Figuras**

    * ¿Cada figura responde una pregunta?
    * Legible a 100 %.
    * Fuentes.
    * Leyendas.
    * Unidades.
    * Colores.
    * Contraste.
    * Tamaño de fuente.
    * Sin solapes.
    * Sin whitespace excesivo.
    * Sin paneles decorativos.
    * No mezclar evidencia con ilustración conceptual.
    * Orden coherente.
    * Reproducible desde script.
    * Caption autosuficiente.

45. **Tablas**

    * Legibilidad.
    * Columnas alineadas.
    * n.
    * unidades.
    * denominadores.
    * IC.
    * p cuando corresponde.
    * método/oráculo/proxy/ablación claramente diferenciados.
    * No demasiada prosa dentro de celdas.
    * No dividir incómodamente entre páginas.
    * Evitar letras diminutas.
    * Fuente correcta.

46. **Ecuaciones**

    * Numeración.
    * Referenciadas en texto.
    * No numerar ecuaciones nunca citadas.
    * Dimensiones.
    * Unidades.
    * Notación.
    * Signos.
    * Índices.
    * Paréntesis.
    * Operadores.
    * Condiciones.
    * Criterios de optimalidad.
    * Convenciones de coste/utilidad.
    * Consistencia main/supplement.

47. **Pseudocódigo**

    * Sintaxis.
    * Indentación.
    * `si / entonces / devolver`.
    * Variables definidas.
    * Complejidad.
    * Inputs/outputs.
    * No contradicción con el código real.
    * No keywords concatenadas.
    * Legibilidad visual.
    * Correspondencia entre algoritmo y resultados.

48. **Layout / composición visual**

    * Portada.
    * Resumen.
    * Abstract.
    * TOC.
    * Saltos de página.
    * Páginas casi vacías.
    * Orphans/widows.
    * Headings aislados.
    * Tablas cortadas.
    * Figuras demasiado pequeñas.
    * Ecuaciones desbordadas.
    * Overfull boxes.
    * Rutas de archivos creando páginas vacías.
    * Espaciado antes/después.
    * Uso consistente del naranja VIU.
    * Jerarquía visual.
    * Densidad por página.

49. **Front matter**

    * Resumen 200–300 palabras.
    * Abstract equivalente.
    * Keywords en la misma página.
    * Nomenclatura compacta.
    * Eliminar símbolos históricos inactivos.
    * Guía de lectura: decidir si es necesaria.
    * Índices compactos.
    * Evitar 17 páginas antes de la Introducción.

50. **Anexos de la memoria VIU**

    * Máximo 20 páginas.
    * Solo pruebas necesarias.
    * Solo reproducibilidad indispensable.
    * No repetir resultados extensos.
    * No incluir corpus completo.
    * No meter campañas históricas.
    * No incluir teoría candidata.
    * No incluir pipelines internos.
    * Mantener lo necesario para sostener claims activos.

51. **Supplementary**

    * Debe complementar, no duplicar.
    * No ser una segunda tesis.
    * Eliminar atlas raw PASS/FAIL/LIMITED.
    * Eliminar `semantic-all.csv`/hashes del PDF público.
    * Eliminar protocolo epistemológico sin resultados si no aporta.
    * Reducir repetición del estado del arte.
    * Incluir pruebas extendidas.
    * Incluir tablas completas.
    * Incluir sensibilidad.
    * Incluir campañas históricas claramente etiquetadas.
    * Referenciar la memoria principal en lugar de copiarla.

52. **Consistencia entre main y supplementary**

    * Mismos números.
    * Mismos símbolos.
    * Mismos nombres.
    * Mismas hipótesis.
    * Mismos n.
    * Mismos p-values.
    * Mismos IC.
    * Mismas semillas.
    * Mismos estados Supported/Partial/etc.
    * Mismos títulos de métodos.
    * No contradicciones.

53. **Revisión de todas las cifras**

    * Cada cifra debe tener una única fuente.
    * Macro provenance.
    * Raw → processed → table.
    * Detectar números stale.
    * Detectar copiados manualmente.
    * Verificar SP7 y demás familias.
    * Tolerancia automática.
    * Cualquier cifra del abstract/conclusión debe poder regenerarse.

54. **Auditoría de claims**

    * Cada afirmación fuerte tiene fuente o prueba.
    * Ninguna conclusión usa un teorema FAIL.
    * LIMITED siempre mantiene su limitación.
    * No promover piloto a confirmatorio.
    * No promover simulación a hardware.
    * No promover “no observado” a “imposible”.
    * No promover “compatible con” a causalidad.
    * No promover “0 colisiones” a invariancia.
    * No promover “resultado local” a garantía global.

55. **Defensa ante Reviewer 1**

    * ¿Dónde está la novedad formal?
    * ¿Qué theorem es realmente nuevo?
    * ¿Qué theorem es aplicación de un resultado estándar?
    * ¿Dónde están los supuestos?
    * ¿Existe un contraejemplo?
    * ¿Convergencia de qué dinámica?
    * ¿Bajo qué información?
    * ¿Cuál es el dominio?
    * ¿Qué ocurre al discretizar?
    * ¿Qué ocurre al cambiar de modo?

56. **Defensa ante Reviewer 2**

    * ¿La planta representa un AMR real?
    * ¿Qué se simuló?
    * ¿Qué se midió?
    * ¿Qué se impuso?
    * ¿Dónde están fricción y contacto?
    * ¿Por qué Coppelia?
    * ¿Por qué no hardware?
    * ¿Qué comparadores son realmente SOTA?
    * ¿Qué pasa con percepción y SLAM?
    * ¿Puede implementarse a bordo?

57. **Defensa ante tribunal VIU**

    * Explicar tesis en 30 segundos.
    * Explicarla en 2 minutos.
    * Contribución en una frase.
    * Mayor resultado.
    * Mayor resultado negativo.
    * Mayor limitación.
    * Razón para usar juegos.
    * Razón para no usar centralizado siempre.
    * Qué es distribuido.
    * Qué falta para industria.
    * Qué publicaría como paper.

58. **Riesgos de rechazo**

    * Incumplimiento de formato.
    * Título contradictorio.
    * Objetivos sin responder.
    * Hipótesis no cerradas.
    * Claims sobredimensionados.
    * Referencias falsas/incompletas.
    * Duplicación/plagio.
    * AI-writing muy evidente.
    * Datos no reproducibles.
    * Comparadores mal nombrados.
    * Teoremas incorrectos.
    * Errores visuales groseros.
    * Coppelia presentada como algo que no es.

59. **Readiness final**

    * `0` errores LaTeX.
    * `0` refs indefinidas.
    * `0` labels duplicados.
    * `0` warnings bibliográficos críticos.
    * `0` P0 científicos.
    * `0` P0 editoriales.
    * `0` P0 normativos.
    * Anexos ≤20.
    * Resultados ≥50 %.
    * Resumen 200–300.
    * Todas las hipótesis cerradas o justificadamente no adjudicadas.
    * Bibliografía auditada.
    * PDF leído página por página.
    * Supplement limpio.
    * Claim ledger congelado.
    * Código/datos congelados.
    * Versión final identificada por commit/hash.

60. **Pregunta final de control**

    * Para cada página: **¿por qué está esta página aquí?**
    * Para cada figura: **¿qué argumento demuestra?**
    * Para cada ecuación: **¿qué usa después?**
    * Para cada teorema: **¿qué conclusión permite?**
    * Para cada experimento: **¿qué hipótesis decide?**
    * Para cada conclusión: **¿qué evidencia exacta la sostiene?**
    * Para cada término del título: **¿dónde está demostrado?**
    * Si una pieza no tiene una respuesta clara, se corrige, mueve o elimina.

Yo convertiría esto en nuestro **índice maestro de auditoría**. No revisaría la tesis de nuevo “de principio a fin” de forma lineal; revisaría estos 60 frentes y marcaría cada uno como **P0 / P1 / P2 / cerrado**.

El orden más lógico para definirlos uno por uno sería empezar por **1–9: normativa → título → problema → RQ → objetivos → hipótesis → trazabilidad**. Hasta que ese esqueleto no esté perfecto, tiene poco sentido pulir frases o mover gráficos. Después pasaríamos a **10–17: contribución, novedad y literatura**; después **18–36: ciencia, matemática, robótica y experimentos**; y finalmente **37–60: conclusiones, escritura, Turnitin, layout, anexos y readiness final**.