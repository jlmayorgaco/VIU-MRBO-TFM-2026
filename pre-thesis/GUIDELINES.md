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
Sí. Para esta fase yo separaría completamente la pregunta de “¿la ciencia es correcta?” y revisaría otra cosa:

> **¿Se puede leer la tesis de principio a fin como una sola obra intelectual, escrita en un mismo momento, por una sola voz, con una dirección argumental inequívoca, sin notar las costuras de meses de trabajo, prompts, experimentos históricos, cambios de nomenclatura y teorías añadidas posteriormente?**

Busqué guías de tesis y escritura académica de **Monash, University of Melbourne, ANU, UNSW, Purdue OWL y University of Manchester**. Coinciden en varios principios especialmente útiles para nuestro caso: la estructura debe llevar al lector desde *qué se hizo y por qué* hasta *qué significa y por qué importa*; los capítulos deben funcionar individualmente pero contribuir explícitamente al argumento global; las introducciones y conclusiones de capítulo deben orientar y reconectar; los headings son señalización, no decoración; y los párrafos deben tener unidad, coherencia, idea temática y desarrollo suficiente. ([Monash University][1]) Melbourne además recomienda pensar la tesis como **lead-in → core → lead-out**, con el núcleo centrado en el trabajo propio, y que cada capítulo termine tanto sintetizando como anticipando el siguiente. ([Students][2]) UNSW menciona explícitamente como problema frecuente detectado por examinadores una **estructura disjointed**, demasiadas subsecciones anidadas, figuras pequeñas y una narración difícil de seguir. ([UNSW Sites][3])

Con eso, para tu tesis construiría el siguiente **Mega-checklist de organización, continuidad, legibilidad y acabado narrativo**.

---

# MEGA-CHECKLIST — COHERENCIA, FLUJO Y “UNA SOLA TESIS”

## A. La prueba fundamental: ¿cuál es la historia?

Antes de tocar capítulos, debe poder responderse en una sola frase:

* [ ] ¿Cuál es la pregunta central?
* [ ] ¿Cuál es el problema físico/robótico que motiva todo?
* [ ] ¿Cuál es la idea organizadora de la solución?
* [ ] ¿Cuál es la secuencia lógica de la tesis?
* [ ] ¿Cuál es el hallazgo principal?
* [ ] ¿Cuál es la limitación principal?
* [ ] ¿Qué debe recordar un jurado una semana después?
* [ ] ¿Puede explicarse la tesis sin usar SP1/SP2/SP3/E0/E1/JCC/H6?
* [ ] ¿Puede explicarse primero conceptualmente y después introducir acrónimos?
* [ ] ¿Cada capítulo aporta una pieza necesaria a esa historia?
* [ ] ¿Existe algún capítulo que podría desaparecer sin afectar la historia?
* [ ] ¿Existe alguna idea importante que aparezca demasiado tarde?
* [ ] ¿Existe alguna idea que aparezca muchas veces porque nunca se decidió dónde vive?

Para la versión final de tu TFM, yo intentaría que todo derive de un hilo como:

$$
\boxed{
\text{seleccionar}
\rightarrow
\text{certificar}
\rightarrow
\text{mover}
\rightarrow
\text{proteger}
\rightarrow
\text{recuperar}
\rightarrow
\text{coordinar tráfico}
}
$$

y transversalmente:

$$
\boxed{
\text{cada capa entrega una propiedad concreta;
ninguna garantía se hereda automáticamente}
}
$$

Ese debe ser el **esqueleto narrativo**, no la cronología de cómo hicimos la investigación.

---

# B. Test de “tesis vs archivo de proyecto”

Este es crucial para tu documento.

* [ ] ¿El texto cuenta el resultado final o cuenta cómo llegamos históricamente a él?
* [ ] ¿Aparecen versiones antiguas de conceptos que ya no forman parte del argumento?
* [ ] ¿Se habla de “formulación previa”?
* [ ] ¿Se habla de “campaña histórica” más veces de las estrictamente necesarias?
* [ ] ¿Aparecen nombres de archivos, carpetas, scripts o commits en el cuerpo?
* [ ] ¿Se nota que unos capítulos fueron escritos hace meses y otros recientemente?
* [ ] ¿Cambian las prioridades científicas de un capítulo a otro?
* [ ] ¿Una misma etapa recibe distintos nombres según cuándo fue escrita?
* [ ] ¿Aparecen E0–E8 solo por razones históricas y no porque ayuden al lector?
* [ ] ¿Se explica trabajo que finalmente no se usa?
* [ ] ¿Se conservan teorías porque “costó desarrollarlas” aunque rompan la historia?
* [ ] ¿Hay material que pertenece al repositorio, no al manuscrito?
* [ ] ¿Hay resultados incluidos por completitud histórica, no porque respondan la pregunta?
* [ ] ¿Se ven las “costuras” entre bloques producidos en momentos distintos?

**Regla:** la tesis final debe presentar la **arquitectura intelectual final**, no el historial de versiones.

---

# C. Macroestructura completa

La Universidad de Melbourne recomienda pensar una tesis como entrada, núcleo y salida; el núcleo debe ser claramente el trabajo propio. ([Students][2])

Revisaría:

### C1. Entrada

* [ ] ¿El lector entra rápidamente al problema?
* [ ] ¿Se tarda demasiado en llegar a la pregunta científica?
* [ ] ¿La revisión de literatura está antes de que el lector comprenda qué busca?
* [ ] ¿El problema industrial aparece antes que sus detalles?
* [ ] ¿Se define pronto cuál es la brecha?
* [ ] ¿La Introducción explica qué se hará y qué no?
* [ ] ¿Objetivos e hipótesis aparecen una vez, claramente?
* [ ] ¿Metodología empieza antes de que la motivación se agote?
* [ ] ¿La primera tercera parte prepara exactamente los experimentos posteriores?

### C2. Núcleo

* [ ] ¿Resultados ocupa visual y conceptualmente el centro de gravedad?
* [ ] ¿El trabajo propio domina sobre literatura?
* [ ] ¿SP1 → SP2 → SP3 parecen progresión y no tres mini papers?
* [ ] ¿La integración aparece como culminación natural?
* [ ] ¿Los experimentos se presentan en el orden que exige la lógica, no la fecha?
* [ ] ¿Cada resultado resuelve una incertidumbre introducida antes?
* [ ] ¿Los resultados negativos son parte de la historia?
* [ ] ¿El lector siente que cada sección hace avanzar la pregunta?

### C3. Salida

* [ ] ¿Conclusiones responden, no repiten?
* [ ] ¿La tesis “cierra el círculo” con la Introducción?
* [ ] ¿Las conclusiones usan el mismo vocabulario de la pregunta original?
* [ ] ¿No aparecen nuevas teorías?
* [ ] ¿No aparecen nuevas motivaciones?
* [ ] ¿No aparecen resultados no explicados antes?
* [ ] ¿Trabajo futuro nace directamente de limitaciones demostradas?

---

# D. Orden global de capítulos

Monash señala que una tesis sólida debe permitir responder, en un orden comprensible: qué se hizo, por qué, cómo, qué se obtuvo, qué significa y por qué importa. ([Monash University][1])

Para cada capítulo:

* [ ] ¿Por qué está exactamente en esa posición?
* [ ] ¿Qué necesita saber el lector antes de leerlo?
* [ ] ¿Todo ese conocimiento ya fue presentado?
* [ ] ¿Qué aprende al terminarlo?
* [ ] ¿Qué capítulo necesita inmediatamente después?
* [ ] ¿Podrían intercambiarse dos capítulos sin afectar nada? Si sí, falta causalidad narrativa.
* [ ] ¿Algún capítulo responde una pregunta antes de plantearla?
* [ ] ¿Algún concepto se usa antes de definirse?
* [ ] ¿Algún resultado aparece antes de explicar su metodología?
* [ ] ¿La literatura aparece después de resultados que supuestamente motivó?
* [ ] ¿Las limitaciones fundamentales aparecen demasiado tarde?

### Test brutal

Escribe una sola oración por capítulo:

> Capítulo X existe para demostrar/establecer ________.

Si dos capítulos dan la misma respuesta, hay redundancia.

Si no puedes completar la frase, el capítulo no tiene función clara.

---

# E. Arquitectura interna de cada capítulo

ANU recomienda que cada capítulo pueda leerse como una unidad discreta, pero dejando claro cómo contribuye a la pregunta global. ([Australian National University][4])

Cada capítulo debería pasar este contrato:

### Entrada del capítulo

* [ ] Máximo 1–3 párrafos introductorios.
* [ ] Explica por qué este capítulo viene ahora.
* [ ] Recuerda solo la información previa indispensable.
* [ ] Declara la pregunta local.
* [ ] Declara qué resultado entregará.
* [ ] Muestra brevemente las secciones que siguen.
* [ ] No repite una página de la Introducción general.

### Desarrollo

* [ ] Una sola progresión lógica dominante.
* [ ] Cada sección resuelve una pieza.
* [ ] La teoría precede inmediatamente al experimento que la usa.
* [ ] Las figuras aparecen cerca del argumento.
* [ ] Las tablas aparecen donde se interpretan.
* [ ] Los resultados importantes no quedan enterrados.

### Salida

* [ ] Síntesis breve.
* [ ] Responde la pregunta local.
* [ ] Identifica exactamente la salida/certificado producido.
* [ ] Declara el límite pertinente.
* [ ] Explica por qué el siguiente capítulo es necesario.
* [ ] No introduce nuevas derivaciones.

Melbourne recomienda precisamente que los capítulos terminen **recapitulando y mirando hacia delante**. ([Students][2])

---

# F. “Puentes” entre capítulos

Este punto es probablemente el más importante para que no parezca una colección de retazos.

Entre cada par de capítulos:

$$
C_i\longrightarrow C_{i+1}
$$

debe existir un puente explícito.

Revisar:

* [ ] ¿El final de \(C_i\) genera la necesidad de \(C_{i+1}\)?
* [ ] ¿Se identifica qué salida pasa al siguiente?
* [ ] ¿El vocabulario permanece constante?
* [ ] ¿La primera frase del nuevo capítulo continúa esa necesidad?
* [ ] ¿Hay salto abrupto de teoría de juegos a robótica?
* [ ] ¿Hay salto abrupto de asignación a wrench?
* [ ] ¿Hay salto abrupto de wrench a CBF?
* [ ] ¿Hay salto abrupto de control a tráfico?
* [ ] ¿La transición explica conceptualmente el cambio de escala/modelo?
* [ ] ¿Se cambia de planta sin anunciarlo?
* [ ] ¿Se cambia de unidad experimental sin anunciarlo?
* [ ] ¿Se cambia de objetivo sin anunciarlo?

Ejemplo ideal:

> “SP1 determina qué robots pueden formar una coalición admisible. Esa decisión, sin embargo, no garantiza que los contactos seleccionados puedan producir el wrench requerido. SP2 comienza precisamente en esa interfaz.”

Eso crea continuidad real.

---

# G. Secciones y subsecciones: profundidad jerárquica

UNSW identifica las subsecciones excesivamente anidadas como un problema frecuente de tesis. ([UNSW Sites][3])

* [ ] ¿Hay más de tres niveles de encabezado?
* [ ] ¿Una subsección contiene una sola subsección?
* [ ] ¿Hay headings para párrafos de cinco líneas?
* [ ] ¿Se usan headings porque el contenido no está bien conectado?
* [ ] ¿Un heading repite la primera oración que sigue?
* [ ] ¿Los headings informan el contenido o solo dicen “Resultados”, “Análisis”, “Discusión”?
* [ ] ¿Los headings paralelos tienen forma gramatical similar?
* [ ] ¿Tienen longitud similar?
* [ ] ¿Los títulos son sustantivos o frases, consistentemente?
* [ ] ¿Un lector puede entender la lógica leyendo solo el TOC?
* [ ] ¿El TOC parece una arquitectura intelectual o una lista de versiones/campañas?

**Test TOC:** imprimir solo el índice.

Si no puede contarse la tesis mirando únicamente sus títulos, hay que reorganizar.

---

# H. Títulos informativos

Melbourne recomienda que los encabezados reflejen el argumento de la sección, no solo su tema. ([Students][2])

Evitar:

> “Resultados”
> “Experimento 2”
> “Discusión”
> “Caso A”

Preferir:

> “La capacidad nominal no garantiza factibilidad de wrench”

cuando el estilo institucional lo permita.

Checklist:

* [ ] ¿El heading dice qué se discute?
* [ ] ¿Puede decir qué se demuestra?
* [ ] ¿Evita nomenclatura puramente interna?
* [ ] ¿Evita nombres históricos?
* [ ] ¿Permite al lector volver rápidamente a la sección?
* [ ] ¿Es breve?
* [ ] ¿Está alineado con el argumento?

---

# I. Reverse outline: la prueba definitiva de organización

Purdue recomienda revisión a nivel de documento y reverse outlining para evaluar organización. ([Purdue OWL][5])

Para **cada párrafo** escribir al margen una frase de 3–8 palabras:

> “define wrench”
> “explica limitación de capacidad”
> “introduce QP”
> “reporta efecto de la guardia”

Después observar la secuencia.

Revisar:

* [ ] ¿Dos párrafos consecutivos hacen lo mismo?
* [ ] ¿Un tema desaparece y reaparece 12 páginas después?
* [ ] ¿La secuencia puede agruparse en bloques lógicos?
* [ ] ¿Hay un párrafo que no sirve a la sección?
* [ ] ¿La sección termina donde debería?
* [ ] ¿Una definición se encuentra lejos de su primer uso?
* [ ] ¿Un resultado se interpreta antes de presentarlo?
* [ ] ¿Hay argumentos A → C → B?
* [ ] ¿El orden debería ser B → A → C?

Este ejercicio detecta “tesis hecha a trozos” mejor que la corrección gramatical.

---

# J. Unidad de párrafo

Purdue propone como regla fundamental **una idea principal por párrafo**, con unidad, coherencia, topic sentence y desarrollo suficiente. ([Purdue OWL][6])

Para cada párrafo:

* [ ] ¿Tiene una sola idea principal?
* [ ] ¿Puedo resumirlo en una frase?
* [ ] ¿La primera oración me dice de qué trata?
* [ ] ¿Las oraciones restantes desarrollan esa idea?
* [ ] ¿Termina hablando de lo mismo con lo que empezó?
* [ ] ¿Contiene dos resultados que deberían separarse?
* [ ] ¿Mezcla literatura + método + resultado + limitación?
* [ ] ¿Es tan corto que parece fragmento?
* [ ] ¿Es tan largo que oculta varios argumentos?
* [ ] ¿La última frase prepara el siguiente párrafo?

Purdue también recomienda revisar párrafos demasiado cortos o muy desequilibrados porque pueden indicar ideas insuficientemente desarrolladas o fragmentadas. ([Purdue OWL][7])

---

# K. La secuencia dentro del párrafo

La estructura que más usaría en esta tesis:

$$
\boxed{
\text{idea}
\rightarrow
\text{evidencia}
\rightarrow
\text{interpretación}
\rightarrow
\text{implicación/transición}
}
$$

Revisar:

* [ ] ¿La evidencia aparece después de decir qué pregunta responde?
* [ ] ¿Los números aparecen sin contexto?
* [ ] ¿Una tabla se presenta antes de explicar para qué sirve?
* [ ] ¿Se interpreta inmediatamente la cifra?
* [ ] ¿Se distingue resultado de interpretación?
* [ ] ¿Se termina indicando por qué importa?

No obligaría todos los párrafos a seguir una fórmula idéntica: eso también produce sensación de IA.

---

# L. Tema conocido → información nueva

Purdue recomienda que las oraciones comiencen con material familiar y avancen hacia información nueva, ayudando al lector a “enganchar” cada frase a la anterior. ([Purdue OWL][8])

Para cada par de oraciones:

$$
S_i\rightarrow S_{i+1}
$$

* [ ] ¿\(S_{i+1}\) empieza desde algo mencionado en \(S_i\)?
* [ ] ¿O introduce de repente otro sujeto?
* [ ] ¿El sujeto cambia cinco veces en cinco frases?
* [ ] ¿Los temas aparecen al principio de la oración?
* [ ] ¿La información nueva queda hacia el final?
* [ ] ¿Hay “saltos de cámara” entre robot, carga, algoritmo, paper y métrica?

Este solo principio puede mejorar muchísimo la sensación de fluidez.

---

# M. Cohesión léxica

Purdue señala que repetir de forma controlada términos clave, sinónimos y referencias anafóricas ayuda a mantener la coherencia. ([Purdue OWL][6])

* [ ] ¿El mismo objeto conserva el mismo nombre?
* [ ] ¿“carga”, “objeto”, “payload”, “cuerpo” se usan con intención o aleatoriamente?
* [ ] ¿“coalición”, “equipo”, “grupo” significan lo mismo?
* [ ] ¿“guardia”, “filtro”, “certificado” están diferenciados?
* [ ] ¿“local”, “vecinal”, “distribuido” tienen definiciones distintas?
* [ ] ¿“oráculo”, “referencia central”, “información perfecta” son categorías claras?
* [ ] ¿Se cambian palabras solo para “no repetir” aunque se pierda precisión?

En escritura científica, **repetir el término correcto suele ser mejor que usar sinónimos ornamentales**.

---

# N. Continuidad terminológica entre capítulos

Construiría una tabla canónica:

| Concepto                | Nombre único           |
| ----------------------- | ---------------------- |
| robots                  | AMR                    |
| objeto transportado     | carga                  |
| grupo activo            | coalición              |
| modalidad principal     | Cargo                  |
| referencia ideal        | oráculo                |
| viabilidad de esfuerzos | factibilidad de wrench |
| etc.                    | etc.                   |

Y revisar:

* [ ] Primera aparición definida.
* [ ] Acrónimo definido una sola vez.
* [ ] Mismo término hasta el final.
* [ ] No resucitar terminología histórica.
* [ ] Main y supplement iguales.

Manchester destaca que definir claramente los términos clave evita interpretaciones distintas del mismo concepto. ([Wordpress Multisite][9])

---

# O. Continuidad de símbolos

Aunque es matemático, aquí importa como legibilidad.

* [ ] Un símbolo mantiene significado.
* [ ] Un mismo objeto no cambia de símbolo entre SP.
* [ ] Los símbolos reaparecen después de 20 páginas con recordatorio suficiente.
* [ ] Símbolos locales mueren al terminar su sección.
* [ ] El lector sabe cuándo cambia la planta.
* [ ] Variables del juego y variables físicas son visualmente distinguibles.
* [ ] Evitar introducir 15 símbolos en una ecuación antes de explicar su función.

---

# P. Signposting: orientar sin sobreexplicar

Monash, Melbourne y Manchester destacan el papel del **signposting** para indicar al lector dónde está, de dónde viene y hacia dónde va. ([Monash University][1])

Debe existir:

### Signposting retrospectivo

> “SP1 estableció…”

### Signposting actual

> “Esta sección evalúa…”

### Signposting prospectivo

> “El resultado alimenta SP2…”

Revisar:

* [ ] ¿Cada capítulo tiene mapa corto?
* [ ] ¿Cada transición importante está señalada?
* [ ] ¿No hay exceso de “En la siguiente sección…”?
* [ ] ¿Los signposts añaden información o solo relleno?
* [ ] ¿Se evita mencionar constantemente números de sección si la relación conceptual basta?

---

# Q. Evitar el “GPS excesivo”

Demasiado signposting también parece mecánico.

Eliminar expresiones repetitivas:

> “Como se verá en la Sección 6.3…”
> “Tal como se presentó anteriormente…”
> “En la siguiente sección…”

cuando no aportan nada.

Conservar solo cuando:

* el salto no es obvio;
* se necesita recordar un supuesto;
* el lector debe recuperar una ecuación/resultado concreto.

---

# R. Introducción general como contrato con el lector

Monash describe una introducción eficaz como una combinación de contexto, términos, estado del conocimiento, gap, RQ/H, metodología, contribución y mapa de la tesis. ([Monash University][10])

Checklist:

* [ ] Problema en primeras 1–2 páginas.
* [ ] Alcance.
* [ ] Términos críticos.
* [ ] Brecha.
* [ ] Pregunta.
* [ ] Enfoque.
* [ ] Contribución.
* [ ] Limitaciones principales.
* [ ] Estructura.
* [ ] Ningún resultado detallado prematuramente.
* [ ] Ninguna subsección que se convierta en review extensa.
* [ ] La Introducción final refleja exactamente la tesis finalmente realizada.

---

# S. Final de Introducción y comienzo de Objetivos

La transición debe sentirse natural:

> problema → gap → pregunta → objetivo.

Revisar:

* [ ] ¿Objetivos parecen aparecer de la nada?
* [ ] ¿Se ha explicado previamente por qué cada OE existe?
* [ ] ¿Cada OE resuelve una dimensión ya motivada?
* [ ] ¿Hay OE que introducen conceptos nuevos?
* [ ] ¿Los objetivos están ordenados igual que la tesis?

---

# T. Estado del arte como argumento, no catálogo

Manchester y Purdue recomiendan que una revisión no solo resuma fuentes: debe sintetizar, comparar, interpretar críticamente y regresar a la pregunta de investigación. ([Wordpress Multisite][11])

Para cada subsección de literatura:

* [ ] ¿Empieza con una pregunta?
* [ ] ¿Agrupa trabajos por problema/método y no cronológicamente?
* [ ] ¿Compara?
* [ ] ¿Explica diferencia relevante?
* [ ] ¿Termina en una implicación para tu diseño?
* [ ] ¿Evita párrafos “Autor A hizo…, Autor B hizo…”?
* [ ] ¿Las figuras bibliométricas ayudan a decidir algo?
* [ ] ¿Cada familia introducida reaparece luego como comparador o fundamento?
* [ ] ¿Se eliminaron familias que nunca vuelven a aparecer?

---

# U. Transición estado del arte → metodología

Debe existir una frase equivalente a:

> “De estas limitaciones se derivan las decisiones metodológicas siguientes.”

Y luego una correspondencia explícita:

$$
\text{gap}_1\to \text{SP1}
$$

$$
\text{gap}_2\to \text{SP2}
$$

$$
\text{gap}_3\to \text{SP3}
$$

Si Metodología parece un documento independiente, todavía hay retazos.

---

# V. Metodología: orden cognitivo

UNSW recomienda para métodos una progresión coherente del experimento general hacia muestra/restricciones, medidas, procedimiento, intervención y análisis. ([UNSW Sites][3])

Para tu tesis adaptaría:

$$
\boxed{
\text{modelo}
\rightarrow
\text{información}
\rightarrow
\text{algoritmo}
\rightarrow
\text{comparadores}
\rightarrow
\text{escenarios}
\rightarrow
\text{métricas}
\rightarrow
\text{estadística}
}
$$

Revisar:

* [ ] No empezar por seeds antes de explicar el experimento.
* [ ] No presentar estadística antes del endpoint.
* [ ] No presentar baselines antes de explicar qué comparan.
* [ ] No mezclar resultados en Metodología.
* [ ] No repetir teoría que pertenece al marco.
* [ ] No repetir toda la metodología de cada SP si existe protocolo común.

---

# W. Resultados: orden narrativo

UNSW recomienda ordenar resultados según importancia o según las RQ. ([UNSW Sites][3])

Para tu tesis usaría causalidad:

1. coalición lógica;
2. capacidad;
3. wrench;
4. movimiento;
5. seguridad;
6. reparación;
7. tráfico;
8. integración.

Dentro de cada resultado:

* [ ] Pregunta.
* [ ] Diseño mínimo necesario.
* [ ] Resultado.
* [ ] Efecto/incertidumbre.
* [ ] Interpretación.
* [ ] Límite.
* [ ] Puente.

Evitar:

> tabla → otra tabla → otra figura → conclusión 4 páginas después.

---

# X. El principio de “una figura, una función”

Cada figura debe ser clasificable como:

* contexto;
* modelo;
* método;
* resultado;
* síntesis.

Nunca varias funciones ambiguas.

Revisar:

* [ ] ¿Se presenta antes de verla?
* [ ] ¿Se explica después?
* [ ] ¿El texto dice qué debe observar el lector?
* [ ] ¿Puede entenderse sin leer 3 páginas?
* [ ] ¿Duplica una tabla?
* [ ] ¿Tiene una sola narrativa?
* [ ] ¿Está cerca de su texto?
* [ ] ¿No corta el flujo de una demostración?

---

# Y. Uso de figuras para aliviar densidad

Tu tesis tiene muchas ecuaciones.

Una figura debería sustituir 1–2 párrafos cuando pueda explicar:

* interfaces;
* secuencia;
* información;
* modos;
* flujo experimental.

Pero:

* [ ] no duplicar ecuación y diagrama si ambos dicen lo mismo;
* [ ] no meter 50 labels;
* [ ] no convertir cada concepto en figura;
* [ ] no hacer figuras tan densas que necesiten explicación mayor que el texto.

---

# Z. Equilibrio visual de cada página

Purdue señala que el balance de párrafos y páginas ayuda a la legibilidad. ([Purdue OWL][7])

Para cada página:

* [ ] ¿Hay bloques enormes de texto sin descanso?
* [ ] ¿Hay demasiadas cajas?
* [ ] ¿Hay media página vacía?
* [ ] ¿Hay una sola línea después de un heading?
* [ ] ¿Hay una figura microscópica?
* [ ] ¿La densidad cambia radicalmente entre páginas?
* [ ] ¿Una ecuación queda huérfana?
* [ ] ¿Una tabla se rompe innecesariamente?
* [ ] ¿Hay paths/URLs que dañan el layout?
* [ ] ¿La página parece terminada deliberadamente?

---

# AA. Ritmo visual del capítulo

No basta con páginas individuales.

Mirar 10–15 páginas como thumbnails:

* [ ] ¿Hay ritmo texto → figura → texto → tabla?
* [ ] ¿O 8 páginas seguidas son idénticas?
* [ ] ¿Hay una concentración absurda de figuras?
* [ ] ¿Hay 5 cajas naranjas seguidas?
* [ ] ¿Los resultados centrales destacan?
* [ ] ¿Todo parece igual de importante?

Un documento elegante necesita jerarquía.

---

# AB. Jerarquía de importancia

Debemos hacer visible:

### Nivel 1

Contribuciones centrales.

### Nivel 2

Resultados necesarios.

### Nivel 3

Detalles técnicos.

### Nivel 4

Reproducibilidad/apéndice.

Revisar:

* [ ] ¿Resultados secundarios ocupan más espacio que el central?
* [ ] ¿Caging compite visualmente con Cargo?
* [ ] ¿Revisión bibliométrica compite con resultados propios?
* [ ] ¿Paths y hashes ocupan espacio de contenido científico?
* [ ] ¿El lector sabe qué recordar?

---

# AC. Economía de repetición

Cada idea importante puede aparecer:

1. Resumen — una frase.
2. Cuerpo — completa.
3. Conclusión — interpretación.

No 12 veces.

Construir un “repetition map”:

* “no completamente distribuida”
* “planar”
* “no validación industrial”
* “no garantiza optimalidad”
* “Coppelia cinemática”
* “cada certificado tiene dominio”

Revisar:

* [ ] ¿Se repite por seguridad?
* [ ] ¿Puede centralizarse?
* [ ] ¿La repetición añade una dimensión nueva?
* [ ] ¿Se puede usar una tabla de límites una sola vez?

---

# AD. Evitar redefiniciones

Si algo se define en página 20:

* [ ] no volver a definirlo completo en página 45;
* [ ] recordar solo lo necesario;
* [ ] usar “como se definió en…” cuando de verdad sea útil.

La redefinición constante es una de las mayores señales de texto ensamblado.

---

# AE. Evitar “mini introducciones” repetidas

En tesis construidas por fragmentos es común:

> “La coordinación multi-robot es importante…”

al inicio de cuatro capítulos.

Buscar:

* [ ] reintroducciones del problema;
* [ ] reintroducciones de MRTA;
* [ ] reintroducciones de juegos;
* [ ] reintroducciones de Cargo;
* [ ] reintroducciones de industria.

Solo la Introducción general puede hacer la gran motivación.

Cada capítulo debe empezar desde donde terminó el anterior.

---

# AF. Evitar “mini conclusiones” redundantes

Cada subsección no necesita:

> “En conclusión…”

Usar síntesis solo cuando:

* cierra una pregunta;
* cambia el nivel de abstracción;
* prepara el siguiente bloque.

---

# AG. Continuidad de voz

Auditar si el texto parece escrito por una sola persona.

Buscar cambios en:

* [ ] formalidad;
* [ ] longitud de frases;
* [ ] uso de primera persona;
* [ ] uso de “este trabajo”;
* [ ] español vs anglicismos;
* [ ] “se propone” vs “proponemos”;
* [ ] estilo de captions;
* [ ] forma de introducir ecuaciones;
* [ ] forma de reportar resultados;
* [ ] forma de reconocer límites.

Congelar una **style sheet** final.

---

# AH. Style sheet de la tesis

Crear una página interna de reglas:

* AMR, no robot móvil salvo explicación.
* “carga”, no payload.
* “wrench” solo después de definir torsor.
* “vecinal”, “local”, “distribuido” con usos definidos.
* Decimal: coma o punto, según norma elegida.
* \(95\,\%\), consistentemente.
* \(p_{\rm Holm}\).
* CoppeliaSim.
* MuJoCo.
* Cargo.
* Caging.
* Figura/Tabla/Sección, capitalización uniforme.
* Inglés en cursiva cuando corresponda.

Esto elimina sensación de fragmentación.

---

# AI. Variedad sintáctica sin perder precisión

Purdue incluye la variedad de oraciones como parte de la claridad de escritura académica. ([Purdue OWL][12])

Revisar:

* [ ] ¿Todas las frases empiezan “El resultado…”?
* [ ] ¿Todas tienen 35–50 palabras?
* [ ] ¿Todo está en pasiva?
* [ ] ¿Todo son sustantivos abstractos?
* [ ] ¿Se alternan frases cortas después de una derivación compleja?
* [ ] ¿Los verbos importantes están visibles?

Ejemplo:

> “La evaluación de la preservación de la factibilidad…”

→

> “Se evaluó si la factibilidad se conservaba…”

Más suave.

---

# AJ. Longitud de oraciones

No impondría límites rígidos, pero usaría alarmas:

* <10 palabras repetidamente → estilo telegráfico.
* 15–30 → normalmente cómodo.
* 30–45 → revisar.
* > 50 → casi siempre dividir.
* > 70 → P1 editorial.

Especialmente si contiene:

* tres “que”;
* dos punto y coma;
* cinco conceptos;
* una cita;
* una limitación.

---

# AK. Puntuación y respiración

* [ ] Puntos frecuentes donde cambia el argumento.
* [ ] Evitar punto y coma como pegamento universal.
* [ ] Evitar dos puntos en cada párrafo.
* [ ] Evitar paréntesis de cuatro líneas.
* [ ] Evitar guiones largos para introducir caveats cada 3 frases.
* [ ] No esconder la conclusión importante entre comas.

---

# AL. Densidad de acrónimos

* [ ] ¿Cuántos acrónimos hay por página?
* [ ] ¿El lector necesita recordar E4, SP2, H4, OE3 simultáneamente?
* [ ] ¿Se puede usar el nombre funcional?
* [ ] ¿Acrónimos usados <3 veces pueden eliminarse?
* [ ] ¿Hay acrónimos que solo existen por historia del proyecto?

---

# AM. Densidad matemática

Para cada página matemática:

* [ ] ¿Hay frase antes de la ecuación?
* [ ] ¿Después se explica qué significa?
* [ ] ¿Se indica por qué importa?
* [ ] ¿Hay más de 3 ecuaciones seguidas sin narrativa?
* [ ] ¿El lector necesita demostrarla o solo usarla?
* [ ] ¿Una derivación puede ir al anexo?

El texto debe dirigir la matemática, no desaparecer entre ecuaciones.

---

# AN. “Equation sandwich”

Cada ecuación importante:

1. preparación;
2. ecuación;
3. interpretación.

Nunca:

> párrafo → 5 ecuaciones → nuevo heading.

---

# AO. Introducción de tablas

No:

> “La Tabla 13 muestra los resultados.”

Mejor:

> “La comparación busca separar calidad de cierre y coste computacional; la Tabla 13 resume ambos estimandos.”

Checklist:

* [ ] propósito antes;
* [ ] tabla;
* [ ] hallazgo después;
* [ ] no repetir cada celda.

---

# AP. Narración de números

No listar:

> 0.997, 0.750, 328.1, 37.40…

Construir relación:

> “La misión se completó en 359 de 360 mundos; el único fallo ocurrió durante recuperación.”

Después, si importa, proporción.

La narrativa debe priorizar significado.

---

# AQ. Cambios de escala

Tu tesis cambia mucho de escala:

$$
\text{robot}
\rightarrow
\text{coalición}
\rightarrow
\text{carga}
\rightarrow
\text{flota}
$$

Cada cambio debe anunciarse.

* [ ] ¿Quién es el agente ahora?
* [ ] ¿Qué representa un nodo?
* [ ] ¿Cuál es el estado?
* [ ] ¿Qué información tiene?
* [ ] ¿Qué dinámica se conserva?
* [ ] ¿Qué dinámica se abstrae?

Esto evitará que SP3 parezca otro paper.

---

# AR. Cambios de modelo

Igual con:

* lógico;
* relajación continua;
* discreto;
* cuasiestático;
* uniciclo;
* cuerpo rígido;
* MAPF;
* replay Coppelia.

Cada transición necesita una frase:

> “A partir de aquí se abandona la dinámica individual de ruedas y cada coalición se representa como…”

Sin eso, la tesis se fragmenta.

---

# AS. Cambios de nivel de evidencia

También hay que señalar:

* theorem;
* simulación;
* piloto;
* replay;
* análisis histórico.

No mezclar en un mismo párrafo sin indicar el cambio.

---

# AT. Resumen al principio de grandes secciones

Para un capítulo de 20 páginas:

> “Esta sección desarrolla tres pasos…”

Sí.

Para una sección de 1 página:

No.

Signposting proporcional a longitud.

---

# AU. Síntesis al final de grandes secciones

Una síntesis buena responde:

1. qué aprendimos;
2. qué limitación queda;
3. qué necesita resolver el siguiente bloque.

Máximo ~1 párrafo o pequeña tabla.

---

# AV. Consistencia de la secuencia SP1–SP3

Haría una revisión específica:

### SP1 termina diciendo:

> “tenemos una coalición candidata y un certificado X.”

### SP2 empieza:

> “tomamos precisamente esa coalición…”

### SP2 termina:

> “tenemos una coalición móvil/segura…”

### SP3 empieza:

> “tratamos esa coalición como agente compuesto…”

Eso crea una cadena.

Si cada SP empieza con su propia historia independiente, parecen papers pegados.

---

# AW. Integración como culminación, no apéndice

La integración no puede aparecer de repente en §6.5.

Debe ser anunciada:

* Introducción.
* Diagrama conceptual.
* Metodología.
* Resultados parciales.
* Culminación.

Pero sin resolverla antes.

El lector debe pensar:

> “Ahora entiendo por qué necesitábamos combinar todo esto.”

---

# AX. Mismo ejemplo conductor

Una forma excelente de unificar una tesis fragmentada es usar **un escenario conductor**.

Por ejemplo:

> carga industrial que requiere 3 AMR, paso estrecho, fallo de un miembro.

Ir reutilizándolo:

* SP1: quiénes.
* E3: contactos.
* SP2: transporte.
* recuperación.
* SP3: tráfico.
* integración.

No tiene que ser el experimento principal; puede ser un ejemplo pedagógico consistente.

---

# AY. Figuras conceptuales como “anchors”

Elegir 3–4 figuras que el lector reconozca:

1. arquitectura completa;
2. cadena de certificados;
3. escenario conductor;
4. integración.

Reusar **estilo**, no repetir la figura completa.

Eso da identidad visual.

---

# AZ. Coherencia cromática

* naranja VIU = headings/estructura;
* uno o dos colores funcionales adicionales;
* mismo significado de color en toda tesis;
* no cambiar paleta entre campañas;
* mismo método = mismo color siempre que sea posible.

La estética repetida de forma controlada crea unidad.

---

# BA. Coherencia tipográfica

* mismo tamaño de ticks;
* mismo font de plots;
* misma notación matemática;
* mismo formato de captions;
* misma precisión decimal;
* misma posición de leyendas;
* mismas unidades.

Un paper se nota pegado a otro inmediatamente cuando las figuras cambian de lenguaje gráfico.

---

# BB. Caption style sheet

Todas las captions deberían seguir una convención.

Figura:

> **Qué muestra + qué codifica + límite necesario.**

Tabla:

> **Población/diseño + qué contiene + aclaración crítica.**

No unas captions telegráficas y otras de seis líneas.

---

# BC. White space deliberado

El blanco es bueno si separa unidades.

Malo si produce:

* página con una URL;
* página con dos líneas;
* figura diminuta rodeada de vacío.

Todo espacio debe parecer deliberado.

---

# BD. Front matter como experiencia de entrada

El lector debería llegar al capítulo 1 sin agotarse.

Revisar:

* [ ] Portada.
* [ ] Resumen.
* [ ] Abstract.
* [ ] TOC.
* [ ] Figuras.
* [ ] Tablas.
* [ ] Acrónimos.
* [ ] Nomenclatura.

¿Todo es necesario?

En tu caso, **17 páginas antes de la Introducción me parece demasiado**.

---

# BE. TOC como herramienta, no inventario

UNSW señala como problema frecuente un índice con demasiadas subsecciones. ([UNSW Sites][3])

* [ ] máximo ~2–3 páginas idealmente;
* [ ] no mostrar niveles 4/5;
* [ ] nombres cortos;
* [ ] narrativa visible;
* [ ] evitar códigos históricos.

---

# BF. Referencias cruzadas

* [ ] Toda “como vimos” tiene destino claro.
* [ ] No referencias vagas.
* [ ] Evitar “anteriormente”.
* [ ] Usar sección/ecuación cuando realmente ayuda.
* [ ] No inundar con `(véase §2.3.1)`.

---

# BG. No hacer al lector memorizar números

Evitar:

> “según la Ecuación (47), Tabla 19 y Figura 21…”

si puede decirse:

> “el residual aplicado definido en (47)…”

Los números son navegación secundaria.

El concepto va primero.

---

# BH. Consistencia de nivel de detalle

Un síntoma de tesis hecha por etapas:

* 5 páginas para un detalle menor;
* 8 líneas para la contribución principal.

Revisar la longitud de cada sección contra:

$$
\text{importancia para la tesis}.
$$

No contra:

$$
\text{cantidad de trabajo que costó producirla}.
$$

---

# BI. Proporción teoría / experimento / interpretación

En cada SP:

* teoría suficiente;
* experimento suficiente;
* interpretación suficiente.

Evitar:

> 6 páginas matemáticas + 1 párrafo de resultados.

O:

> 8 tablas + ninguna interpretación.

---

# BJ. Nivel de detalle progresivo

Primera aparición:

> intuición.

Segunda:

> formulación.

Tercera:

> prueba/experimento.

No dar toda la matemática antes de que el lector entienda por qué existe.

---

# BK. Principio de “concepto antes que símbolo”

Antes de:

$$
\rho_{ik},\lambda,W,G,\Phi
$$

decir:

> “cada robot mantiene una preferencia por carga…”

Así el símbolo etiqueta una idea ya comprendida.

---

# BL. Principio de “resultado antes que decimals”

Primero:

> la guardia eliminó las falsas aceptaciones observadas.

Después:

$$
0.333\rightarrow0.
$$

No al revés.

---

# BM. Orden de la discusión

Cuando interpretes:

1. hallazgo;
2. mecanismo plausible;
3. relación con literatura;
4. límite;
5. implicación.

No:

literatura → caveat → número → otra literatura → conclusión.

---

# BN. Separar hechos e interpretación

Marcadores naturales:

> “Se observó…”
> “Esto indica…”
> “Una explicación compatible es…”
> “El diseño no permite establecer…”

Eso evita que inferencias parezcan datos.

---

# BO. Conclusiones como espejo de la Introducción

Monash subraya que la conclusión debe enlazar con la introducción y completar el marco del trabajo. ([Monash University][10])

Crear una tabla de edición:

| Introducción           | Conclusión           |
| ---------------------- | -------------------- |
| Problema               | Respuesta            |
| RQ                     | Respuesta            |
| Gap                    | Qué cerramos         |
| Contribución prometida | Contribución lograda |
| Scope                  | Límites              |
| Impacto esperado       | Implicaciones        |

Si algo de la izquierda no reaparece, está abierto.

Si algo aparece a la derecha sin estar a la izquierda, fue introducido demasiado tarde.

---

# BP. No convertir conclusiones en segundo Discussion

Manchester señala que una conclusión debe sintetizar, evaluar significancia y apuntar futuro, no reabrir toda la argumentación. ([Wordpress Multisite][13])

* [ ] no nuevas tablas;
* [ ] no nuevos teoremas;
* [ ] no nuevos papers;
* [ ] no cinco páginas de discusión económica/social no evaluada;
* [ ] respuesta directa primero.

---

# BQ. Última frase de la tesis

Tiene que cerrar científicamente.

No:

> “Se espera continuar trabajando…”

Sí algo cercano a:

> “Los resultados delimitan así qué propiedades pueden certificarse localmente y cuáles todavía requieren una composición híbrida demostrable antes del despliegue.”

La última frase importa.

---

# BR. “Single-voice pass”

Hacer una pasada donde no se corrige ciencia.

Solo preguntar:

* ¿Yo diría esto así?
* ¿Esta frase suena como el resto?
* ¿Es demasiado solemne?
* ¿Parece generada?
* ¿Parece nota interna?
* ¿Es traducción del inglés?
* ¿Se repite una plantilla?
* ¿Tiene verbos concretos?
* ¿Podría ser más sencilla?

---

# BS. “Read-aloud pass”

Leer en voz alta.

Marcar cuando:

* te quedes sin aire;
* tengas que regresar;
* no recuerdes el sujeto;
* una frase suene burocrática;
* dos términos suenen idénticos pero no lo sean;
* el ritmo sea monótono.

Es extremadamente eficaz.

---

# BT. “Naive reader pass”

Entregar capítulos a alguien técnicamente educado pero que no conozca el proyecto.

Después preguntar sin explicarle nada:

1. ¿Cuál es el problema?
2. ¿Qué propuso?
3. ¿Qué es distribuido?
4. ¿Qué demostró?
5. ¿Cuál es el mejor resultado?
6. ¿Qué no funciona?
7. ¿Qué falta?

Si las respuestas no coinciden con lo que nosotros creemos haber escrito, hay problema narrativo.

Melbourne recomienda precisamente anticipar qué conoce el lector y qué conceptos requieren explicación. ([Students][14])

---

# BU. “Cold chapter test”

ANU advierte que examinadores pueden leer Abstract/Introducción/Conclusión y semanas después saltar a un capítulo cualquiera. Cada capítulo debe ser entendible de forma relativamente autónoma. ([Australian National University][4])

Para cada capítulo abierto al azar:

* [ ] ¿entiendo su pregunta?
* [ ] ¿entiendo los símbolos esenciales?
* [ ] ¿sé cómo contribuye al TFM?
* [ ] ¿sé qué obtuvo?
* [ ] ¿sé sus límites?

No debe requerir releer 60 páginas.

---

# BV. “Page-turn test”

Leer solo:

* primera frase de cada párrafo;
* último párrafo de cada sección;
* primera frase de la siguiente.

¿Se puede seguir el argumento?

Si no, falta estructura temática.

Purdue justamente recomienda examinar los temas al comienzo de las oraciones como diagnóstico de cohesión. ([Purdue OWL][8])

---

# BW. “Heading-only test”

Leer únicamente:

* capítulo;
* sección;
* subsección;
* captions.

¿Cuenta la historia?

---

# BX. “Figure-only test”

Leer:

* figuras;
* captions;
* tablas.

¿Puede reconstruirse el argumento experimental?

Eso es especialmente importante para un jurado que escanea rápido.

---

# BY. “Remove 20% test”

Preguntar por cada sección:

> Si tuviera que eliminar 20 %, ¿qué quitaría?

Luego probablemente quitarlo aunque no sea obligatorio.

Una tesis elegante suele mejorar cuando deja de intentar demostrar que trabajaste mucho y empieza a mostrar claramente **qué aprendiste**.

---

# BZ. “No-retazos test” específico para TU TFM

Yo buscaría expresamente estas costuras:

* E0/E1 históricos vs SP1 actual.
* E2/E3 nomenclatura antigua.
* SP2 que en distintas épocas incluía formaciones distintas.
* Cargo con mecanismos diferentes a SP1/SP2 teóricos.
* Caging injertado en MegaJuego.
* Coppelia añadido posteriormente.
* revisión industrial añadida posteriormente.
* patentes añadidas posteriormente.
* MegaJuego añadido posteriormente.
* Atlas formal añadido posteriormente.
* hypotheses añadidas/reformuladas posteriormente.
* vocabulario de Claude/Codex.
* resultados antiguos mezclados con resultados activos.
* supplemental construido copiando main.

Cada una necesita una decisión:

$$
\boxed{
\text{integrar}
\quad|\quad
\text{reformular}
\quad|\quad
\text{mover}
\quad|\quad
\text{eliminar}
}
$$

No dejar una quinta opción:

> “mantener porque ya existe”.

---

# CA. Scorecard final de fluidez

Calificaría cada capítulo 0–2 en estas dimensiones:

| Dimensión            | 0              | 1         | 2                 |
| -------------------- | -------------- | --------- | ----------------- |
| Propósito            | confuso        | deducible | explícito         |
| Dependencia anterior | abrupta        | parcial   | natural           |
| Pregunta local       | ausente        | implícita | clara             |
| Estructura           | fragmentada    | razonable | inevitable        |
| Terminología         | inestable      | casi      | estable           |
| Párrafos             | fragmentados   | mixtos    | cohesionados      |
| Transiciones         | ausentes       | mecánicas | naturales         |
| Figuras              | decorativas    | útiles    | argumentales      |
| Síntesis             | ausente        | resumen   | conclusión+puente |
| Voz                  | inconsistente  | casi      | única             |
| Densidad             | desequilibrada | aceptable | cómoda            |
| Conexión global      | débil          | visible   | fuerte            |

Máximo:

$$
24.
$$

Yo no cerraría ningún capítulo con menos de:

$$
\boxed{22/24}.
$$

Y la tesis completa debería tener cero capítulos con **0** en cualquier dimensión.

---

# CB. El flujo ideal que perseguiría en tu TFM

No necesariamente cambiar ahora los nombres oficiales de capítulos, pero cognitivamente quiero que el lector experimente esto:

**Introducción**
Hay una misión industrial de transporte cooperativo. Elegir robots no basta.

↓

**Estado del arte**
La literatura resuelve piezas, pero las garantías pertenecen a modelos diferentes.

↓

**Pregunta**
¿Cómo conectarlas sin atribuir a una capa propiedades que no demuestra?

↓

**Metodología**
Separaremos decisión, mecánica, ejecución y tráfico mediante contratos verificables.

↓

**SP1**
¿Quién debe participar y es nominal/mecánicamente admisible?

↓

**SP2**
Dada esa coalición, ¿puede acoplarse, moverse, evitar obstáculos y recuperarse?

↓

**SP3**
Dada una coalición móvil, ¿cómo comparte recursos con las demás?

↓

**Integración**
¿Qué propiedades sobreviven cuando esas capas se conectan?

↓

**Resultados integrados**
Algunas sí; otras no. Ahí aparecen H3, congestión, información y Coppelia.

↓

**Conclusión**
La principal contribución no es “un algoritmo que siempre gana”, sino identificar y conectar los certificados necesarios y mostrar sus fronteras de composición.

Eso se siente como **una tesis**.

No como:

> SP1 paper + SP2 paper + SP3 paper + bibliometría + patentes + MegaJuego + Coppelia.

---

## Las fuentes que usaría como norma editorial

Las más útiles para esta fase son:

* **Monash — Thesis structures:** una tesis debe construir respuestas claras a qué, por qué, cómo, resultados, significado e importancia; además destaca signposting y headings como navegación. ([Monash University][1])
* **University of Melbourne — Writing thesis sections:** macroestructura lead-in/core/lead-out, headings sustantivos, capítulos con introducción y conclusión, y relación explícita con RQ/H. ([Students][2])
* **ANU — Chapter writing:** cada capítulo debe ser legible como unidad y a la vez contribuir claramente al argumento global. ([Australian National University][4])
* **UNSW — Thesis FAQs:** entre los problemas que reportan examinadores están estructura discontinua, demasiadas subsecciones y figuras demasiado pequeñas; recomiendan contar la investigación de la forma más directa y sencilla posible. ([UNSW Sites][3])
* **Purdue OWL:** un párrafo debe tener unidad, coherencia, idea temática y desarrollo; las transiciones conectan párrafos y los temas iniciales de oración ayudan a crear cohesión. ([Purdue OWL][6])
* **Manchester Academic Phrasebank:** el signposting debe funcionar como un mapa, y las transiciones deben marcar cambios reales de tema/sección, no ser relleno formulaico. ([Wordpress Multisite][15])

Mi enfoque sería usar este checklist **como una auditoría separada de la auditoría científica**. Primero hacemos un **mapa narrativo de una página de toda la tesis**, después un **reverse outline capítulo por capítulo**, y solo entonces reescribimos. Eso evita el error típico de mejorar cada párrafo individualmente mientras la estructura global sigue pareciendo ensamblada.

[1]: https://www.monash.edu/student-academic-success/excel-at-writing/how-to-write/thesis-chapter/thesis-structures?utm_source=chatgpt.com "Thesis structures - Student Academic Success"
[2]: https://students.unimelb.edu.au/academic-skills/graduate-research-services/writing-thesis-sections-part-1?utm_source=chatgpt.com "Writing the thesis sections part 1"
[3]: https://www.unsw.edu.au/student/managing-your-studies/academic-skills-support/toolkit/honours-postgraduate/faqs?utm_source=chatgpt.com "Thesis FAQs | Current Students – UNSW Sydney"
[4]: https://www.anu.edu.au/students/academic-skills/research-writing/chapter-writing?utm_source=chatgpt.com "Chapter writing | Australian National University"
[5]: https://owl.purdue.edu/owl/graduate_writing/thesis_and_dissertation/index.html?utm_source=chatgpt.com "Thesis and Dissertation - Purdue OWL® - Purdue University"
[6]: https://owl.purdue.edu/owl/general_writing/academic_writing/paragraphs_and_paragraphing/index.html?utm_source=chatgpt.com "On Paragraphs - Purdue OWL® - Purdue University"
[7]: https://owl.purdue.edu/owl/general_writing/academic_writing/paragraphs_and_paragraphing/paragraphing.html?utm_source=chatgpt.com "Paragraphing - Purdue OWL® - Purdue University"
[8]: https://owl.purdue.edu/owl/general_writing/the_writing_process/proofreading/revising_for_cohesion.html?utm_source=chatgpt.com "Revising for Cohesion - Purdue OWL® - Purdue University"
[9]: https://www.phrasebank.manchester.ac.uk/writing-definitions/?utm_source=chatgpt.com "Academic Phrasebank | Defining terms"
[10]: https://www.monash.edu/student-academic-success/excel-at-writing/how-to-write/thesis-chapter/introduction-and-conclusion-thesis-chapters?utm_source=chatgpt.com "Introduction and conclusion thesis chapters - Student Academic Success"
[11]: https://www.phrasebank.manchester.ac.uk/referring-to-sources/?utm_source=chatgpt.com "Academic Phrasebank | Referring to sources"
[12]: https://owl.purdue.edu/owl/general_writing/academic_writing/index.html?utm_source=chatgpt.com "Academic Writing Introduction - Purdue OWL® - Purdue University"
[13]: https://www.phrasebank.manchester.ac.uk/writing-conclusions/?utm_source=chatgpt.com "Academic Phrasebank | Writing Conclusions"
[14]: https://students.unimelb.edu.au/academic-skills/graduate-research-services/developing-writing-skills-for-graduate-research?utm_source=chatgpt.com "Developing writing skills for graduate research"
[15]: https://www.phrasebank.manchester.ac.uk/signalling-transition/?utm_source=chatgpt.com "Academic Phrasebank | Signalling transition"
Sí. Aquí sí conviene crear un **estándar gráfico formal**, porque “la figura se ve bonita” no es suficiente. Para un TFM técnico como el tuyo, cada figura debería superar tres pruebas distintas:

$$
\boxed{
\text{integridad científica}
+
\text{legibilidad editorial}
+
\text{calidad de producción}
}
$$

IEEE recomienda preferir gráficos vectoriales, usar >300 dpi para imágenes color/grises y >600 dpi para line art si se rasteriza, y mantener tipografías consistentes de aproximadamente 9–10 pt al tamaño final. ([IEEE Author Center Journals][1]) Nature insiste en que las figuras sean tan simples como permita la claridad, que todos los símbolos y barras de error estén definidos y que se evite complejidad/color innecesarios. ([Nature][2]) IEEE también recomienda que una figura siga siendo interpretable en escala de grises y que no dependa solo del color: color + forma + tipo de línea. ([IEEE Author Center Journals][3])

Para tu tesis yo congelaría el siguiente **MEGA-CHECKLIST FIGURE QA** y no permitiría que Claude/Sonnet considere una figura “terminada” hasta pasar todos sus gates.

---

# 1. Regla cero: Claude NO puede aprobar una figura viendo solo el código

Para **cada figura**:

* [ ] Generar el archivo final.
* [ ] Insertarlo en el PDF de la tesis.
* [ ] Compilar el PDF.
* [ ] Renderizar la **página completa** del PDF a PNG.
* [ ] Inspeccionar visualmente esa página.
* [ ] Renderizar además la figura sola a resolución alta.
* [ ] Inspeccionar figura sola.
* [ ] Verificar código/datos.
* [ ] Solo entonces aprobarla.

Nunca aceptar:

> “El código usa `tight_layout()`, por tanto no hay overlaps.”

Eso es falso como procedimiento de QA. Matplotlib mismo reconoce que `tight_layout` tiene limitaciones; `constrained_layout` es normalmente más robusto, pero tampoco sustituye la inspección visual. ([Matplotlib][4])

---

# 2. Gate visual universal: absolutamente ningún elemento puede colisionar

Para toda figura:

* [ ] Ningún título toca un eje.
* [ ] Ningún label toca ticks.
* [ ] Ningún tick toca otro tick.
* [ ] Ningún texto toca una barra.
* [ ] Ningún texto tapa un punto importante.
* [ ] Ningún valor encima de una barra choca con el borde superior.
* [ ] Ninguna annotation sale del canvas.
* [ ] Ninguna flecha cruza texto innecesariamente.
* [ ] Ninguna leyenda cubre datos.
* [ ] Ningún panel label `(a)`, `(b)` choca con títulos.
* [ ] Ninguna colorbar invade otro panel.
* [ ] Ningún texto queda cortado por el bounding box.
* [ ] Ninguna leyenda queda parcialmente fuera del PDF.
* [ ] Ningún eje queda recortado al exportar.
* [ ] Ningún `ylabel` largo queda truncado.
* [ ] Ningún exponente de notación científica queda fuera.
* [ ] Ningún símbolo matemático se rompe por falta de font.
* [ ] Ninguna palabra se parte de forma absurda dentro de una figura.

**Gate:** overlap visible = figura rechazada.

No importa si el dato es correcto.

---

# 3. Legibilidad al tamaño FINAL, no ampliado

Esta regla es fundamental.

Una figura se juzga a:

$$
100\%\text{ del PDF}
$$

y, mejor aún, imprimiendo una página A4.

Para tesis A4 usaría como estándar interno:

* texto interno ideal: **9–10 pt** al tamaño final;
* mínimo aceptable normal: **8 pt**;
* 7 pt solo excepcionalmente;
* <7 pt: rediseñar la figura.

IEEE recomienda aproximadamente 9–10 pt para texto en gráficos a tamaño final. ([IEEE Author Center Journals][5])

Nature permite tamaños menores para sus columnas, pero eso responde a su layout editorial y **no es una razón para meter texto microscópico en una tesis**. ([Nature][6])

---

# 4. Tipografía global

Toda la tesis debe tener una sola gramática tipográfica.

* [ ] Una familia tipográfica para todas las figuras.
* [ ] Preferiblemente la misma o compatible con la tesis.
* [ ] Arial/Helvetica/Times/Cambria son opciones seguras según IEEE. ([IEEE Author Center Journals][5])
* [ ] Títulos de panel consistentes.
* [ ] Labels de ejes del mismo tamaño.
* [ ] Ticks del mismo tamaño.
* [ ] Leyendas del mismo tamaño.
* [ ] No mezclar fonts entre Python, TikZ, Excel y screenshots.
* [ ] Matemática usando símbolos consistentes.
* [ ] Fonts embebidos en PDF/SVG.
* [ ] Nunca depender de una fuente local que pueda desaparecer al compilar en otra máquina.

---

# 5. Grosor de líneas

A tamaño final:

* ejes: ~0.6–0.8 pt;
* líneas principales: ~1.0–1.5 pt;
* líneas secundarias: ~0.8–1.0 pt;
* grid: fino y discreto;
* error bars: visibles pero no dominantes.

Nature recomienda aproximadamente **0.25–1 pt** como rango de producción de línea al tamaño final y advierte que líneas más finas pueden desaparecer. ([Nature][6])

Para tesis yo sería algo más conservador:

> si una línea importante queda por debajo de ~0.75 pt, revisar.

---

# 6. Resolución y formato

### Plots, esquemas, diagramas

Preferir:

$$
\boxed{\text{PDF/SVG vectorial}}
$$

* [ ] Textos vectoriales.
* [ ] Líneas vectoriales.
* [ ] Fonts embebidos.
* [ ] Sin pixelación al hacer zoom.

### Fotografías / screenshots

* [ ] ≥300 dpi equivalente al tamaño de impresión.
* [ ] Sin compresión JPEG agresiva.
* [ ] Captura original, no screenshot de screenshot.

### Line art rasterizado

* [ ] ≥600 dpi.

IEEE da precisamente esos mínimos: >300 dpi color/grayscale y >600 dpi line art. ([IEEE Author Center Journals][1])

---

# 7. Color

Cada color debe tener una función semántica.

* [ ] No usar rainbow/jet.
* [ ] No depender solo de rojo vs verde.
* [ ] Paleta colorblind-safe.
* [ ] Métodos iguales = mismo color en toda tesis.
* [ ] Proposed = mismo color siempre.
* [ ] Oracle = mismo estilo siempre.
* [ ] Ablations = familia visual consistente.
* [ ] Backgrounds neutros.
* [ ] Nada fluorescente.
* [ ] Saturación moderada.
* [ ] Colorbar perceptualmente ordenada.
* [ ] Sequential palette para magnitud.
* [ ] Diverging palette solo si existe centro semántico real, por ejemplo 0.
* [ ] Categorical palette para categorías sin orden.

IEEE recomienda redundancia color + forma/tipo de línea y comprobar la figura en escala de grises. ([IEEE Author Center Journals][3])

---

# 8. Test de escala de grises

Cada figura:

* [ ] Convertir temporalmente a grayscale.
* [ ] ¿Se siguen distinguiendo series?
* [ ] ¿Se siguen distinguiendo proposed/oracle/ablation?
* [ ] ¿Las líneas tienen distintos estilos?
* [ ] ¿Los markers difieren?
* [ ] ¿Las barras pueden reconocerse?
* [ ] ¿La leyenda sigue funcionando?

Si no:

> color no puede ser el único canal.

---

# 9. Contraste

En texto sobre fondo:

$$
\text{contrast ratio}\ge4.5:1
$$

es una buena referencia de accesibilidad WCAG para texto normal.

IEEE también remite a WCAG para material gráfico accesible. ([IEEE Author Center Journals][7])

* [ ] Nada de gris claro sobre blanco.
* [ ] Nada de texto blanco sobre amarillo.
* [ ] Nada de labels sobre heatmap sin adaptar el color del texto.
* [ ] Evitar colocar texto sobre zonas texturadas/coloreadas, algo que Nature también desaconseja. ([Nature][2])

---

# 10. Grid

* [ ] Solo si ayuda a leer valores.
* [ ] Más débil que los datos.
* [ ] Preferir horizontal en barras.
* [ ] En scatter, muy sutil.
* [ ] No hacer caja cuadriculada tipo Excel.
* [ ] Evitar minor grid salvo necesidad.
* [ ] Grid detrás de los datos.

---

# 11. Ejes

Toda gráfica:

* [ ] X claramente definido.
* [ ] Y claramente definido.
* [ ] Unidad en label.
* [ ] Escala lineal/log explícita.
* [ ] Cero incluido cuando la semántica lo exige.
* [ ] Límites no manipulativos.
* [ ] Sin padding excesivo.
* [ ] Sin datos pegados al borde.
* [ ] Ticks razonables.
* [ ] Precisión decimal acorde al dato.
* [ ] Miles y exponentes consistentes.
* [ ] Cero escrito como `0`, no `0.000000`.

---

# 12. Cero y truncamiento del eje

### Bar charts

**Regla casi absoluta:**

$$
y_{\min}=0.
$$

Porque la longitud de la barra codifica magnitud.

No truncar barras salvo un caso excepcional y muy claramente indicado.

### Line/scatter

No es obligatorio empezar en cero, pero:

* [ ] rango justificado;
* [ ] no exagerar diferencias;
* [ ] si el rango estrecho altera la percepción, considerar inset o doble representación.

---

# 13. Títulos internos

Idealmente la caption del TFM contiene el título principal.

Dentro de la figura:

* [ ] evitar repetir “Figure 15 — ...”.
* [ ] panel title corto.
* [ ] no escribir un párrafo arriba del plot.
* [ ] título describe condición, no interpretación.

Por ejemplo:

**Mejor**

> `N = 64, loss = 0.25`

que:

> `Our method works better under the proposed configuration`

---

# 14. Captions

Nature recomienda que una caption permita entender la figura de forma relativamente independiente y que defina símbolos/error bars/estadística. ([Nature][2])

Para tu tesis:

* [ ] primera frase: qué muestra;
* [ ] segunda: diseño/población si hace falta;
* [ ] definir colores/markers no obvios;
* [ ] definir error bars;
* [ ] informar \(n\);
* [ ] aclarar IC;
* [ ] indicar si datos son pareados;
* [ ] declarar si es conceptual;
* [ ] declarar si es piloto;
* [ ] declarar si no es inferencial;
* [ ] fuente al final.

No poner una mini-discusión de media página.

---

# 15. Figure integrity

* [ ] No manipular imagen para ocultar fallos.
* [ ] No remover outliers visualmente sin regla.
* [ ] No ajustar límites para ocultar error.
* [ ] No seleccionar la mejor seed para screenshot salvo “representative” definido a priori.
* [ ] No combinar mundos de forma que parezca más \(n\).
* [ ] No duplicar puntos para aumentar densidad.
* [ ] No suavizar curvas sin declarar suavizado.
* [ ] No interpolar experimental data como si fueran mediciones.

---

# 16. Estadística en figuras

Nature pide definir error bars, \(n\) exacto y replicates. ([Nature][8])

En tu TFM:

* [ ] siempre definir qué es barra/error band:

  * SD;
  * SE;
  * IC95;
  * bootstrap CI;
  * quantiles.
* [ ] reportar \(n\).
* [ ] indicar unidad experimental.
* [ ] si paired, preservar pareamiento visual cuando sea útil.
* [ ] p-values exactos cuando se presentan.
* [ ] indicar Holm si es ajustado.
* [ ] no usar estrellas sin valores si se puede evitar.
* [ ] no poner `***` como principal resultado.
* [ ] no poner error bars donde cada barra es una sola corrida.

---

# 17. Multi-panel figures — reglas generales

Para `(a)`, `(b)`, `(c)`, `(d)`:

* [ ] panel labels misma posición.
* [ ] mismo font.
* [ ] misma distancia del panel.
* [ ] alineación exacta.
* [ ] alturas de axes coherentes.
* [ ] márgenes iguales.
* [ ] títulos alineados.
* [ ] si comparten x, evitar repetir labels innecesariamente.
* [ ] si comparten y, misma escala cuando la comparación visual lo requiere.
* [ ] leyenda global si evita repetición.
* [ ] colorbar global cuando representa lo mismo.
* [ ] no meter paneles solo para llenar espacio.
* [ ] todos los paneles deben pertenecer a la misma pregunta.

Nature recomienda multipanel solo cuando los paneles están lógicamente conectados. ([Nature][2])

---

# 18. Regla de alineación multipanel

Esto lo haría obligatorio programáticamente:

$$
x_{\text{left}}^{(a)}
=
x_{\text{left}}^{(c)}
$$

y equivalentes.

* [ ] misma anchura de plotting area;
* [ ] no confundir anchura total de axes con anchura del plot;
* [ ] considerar labels largos;
* [ ] colorbar no debe desplazar solo un panel.

---

# 19. BAR PLOTS

## Barras simples

* [ ] eje empieza en cero.
* [ ] barras no excesivamente delgadas.
* [ ] espacio entre barras ~20–40 % de anchura de barra.
* [ ] categorías ordenadas lógicamente.
* [ ] si hay ranking, ordenar por valor.
* [ ] si hay orden temporal, respetar tiempo.
* [ ] no ordenar arbitrariamente para “verse bonito”.
* [ ] máximo razonable de categorías.
* [ ] si >10–12 categorías, considerar horizontal.
* [ ] labels legibles.
* [ ] valores encima solo si aportan.
* [ ] suficiente headroom para labels.

### Headroom obligatorio

Si etiquetas sobre barras:

$$
y_{\max}
\ge
1.10-1.20\times \max(y)
$$

aproximadamente, dependiendo del label.

No poner el número pegado al techo.

---

# 20. Grouped bar plots

* [ ] máximo 3–4 series por grupo.
* [ ] misma anchura.
* [ ] misma separación.
* [ ] leyenda claramente asociada.
* [ ] grupos separados más que las barras internas.
* [ ] no usar 8 colores.
* [ ] usar hatch si grayscale importa.
* [ ] error bars centrados exactamente.
* [ ] categorías agrupadas con orden coherente.

Para tu figura de países:

> dos periodos = perfecto para grouped bars.

---

# 21. Stacked bars

Usarlas solo si interesa:

$$
\text{total + composición}.
$$

* [ ] partes suman total claramente.
* [ ] orden de segmentos fijo.
* [ ] no comparar segmentos centrales entre barras si esa es la pregunta principal.
* [ ] si comparar porcentajes, usar 100 % stacked.
* [ ] máximo ~4–5 categorías.
* [ ] labels internos solo si caben.

Si la pregunta es comparar todos los componentes:

> mejor grouped bar o small multiples.

---

# 22. Horizontal bar plots

Preferibles cuando:

* nombres largos;

* rankings;

* países/empresas/papers.

* [ ] ordenar de arriba a abajo de manera intuitiva.

* [ ] valor mayor arriba si ranking.

* [ ] suficiente margen izquierdo.

* [ ] no cortar labels.

* [ ] cifras al final de la barra con padding consistente.

---

# 23. SCATTER PLOTS

* [ ] markers suficientemente visibles.
* [ ] no saturar de puntos.
* [ ] alpha solo cuando hay overplotting.
* [ ] no usar alpha tan bajo que desaparezcan datos.
* [ ] tamaño de marker constante salvo que codifique una variable.
* [ ] si tamaño codifica variable, la **área**, no el radio, debe corresponder a magnitud.
* [ ] incluir leyenda de tamaños.
* [ ] ejes correctamente escalados.
* [ ] línea \(y=x\) solo si tiene interpretación.
* [ ] regression line solo si análisis lo justifica.
* [ ] banda de IC claramente definida.

---

# 24. Scatter con labels

Este es uno de tus problemas recurrentes.

**Regla: ningún label puede tocar su punto ni otro label.**

* [ ] offsets consistentes.
* [ ] usar repel/adjustText o algoritmo equivalente.
* [ ] revisar manualmente después.
* [ ] usar leader line si label se aleja.
* [ ] label alineado con punto.
* [ ] no etiquetar 50 puntos.
* [ ] etiquetar solo casos relevantes.
* [ ] resto explicado por color/familia.

Si el gráfico necesita todos los nombres:

> considerar tabla, interactive supplement o small multiples.

---

# 25. Quadrant scatter plots

Muy pertinente para tus mapas metodológicos.

* [ ] líneas de cuadrante claramente visibles pero secundarias.
* [ ] significado de ambos ejes definido.
* [ ] dirección semántica de ejes clara.
* [ ] cuadrantes etiquetados.
* [ ] labels no amontonados en origen.
* [ ] jitter no introducir significado falso.
* [ ] posiciones ordinales descritas como ordinales, no mediciones continuas.
* [ ] evitar interpretar distancia Euclídea si ejes son rúbricas cualitativas.
* [ ] explicar que posición no implica calidad si es el caso.

---

# 26. Bubble charts

Usar con cautela.

* [ ] área ∝ magnitud.
* [ ] no diámetro ∝ magnitud.
* [ ] 3–5 tamaños guía.
* [ ] burbujas no ocultan categorías.
* [ ] transparency moderada.
* [ ] evitar comparar valores muy próximos mediante área.
* [ ] incluir tabla o labels para valores importantes.

---

# 27. LINE PLOTS

* [ ] x realmente ordenado/continuo.
* [ ] puntos conectados tienen sentido.
* [ ] no conectar categorías nominales.
* [ ] markers si hay pocos puntos.
* [ ] líneas suficientemente gruesas.
* [ ] estilos diferentes.
* [ ] no más de ~5–6 curvas en un panel.
* [ ] si más, small multiples.
* [ ] legend cerca de datos o direct labels.
* [ ] no spaghettification.

---

# 28. Time series

* [ ] eje temporal con unidades.
* [ ] sampling rate claro.
* [ ] discontinuidades visibles.
* [ ] no suavizar sin declarar.
* [ ] eventos verticales etiquetados.
* [ ] shaded regions claramente explicadas.
* [ ] no esconder transitorios recortando x.
* [ ] si hay baseline/fault/recovery, delimitar fases.

---

# 29. Convergence curves

Muy importante en juegos/optimización.

* [ ] definir residual.
* [ ] escala log si corresponde.
* [ ] nunca plotear cero en log.
* [ ] indicar tolerance.
* [ ] marcar max iterations.
* [ ] mostrar fallos/no-convergence.
* [ ] no eliminar runs divergentes.
* [ ] mediana + quantile/CI si varias semillas.
* [ ] no mostrar una seed como prueba de convergencia general.
* [ ] separar convergence theorem de convergence observed.

---

# 30. Learning/training curves

Si aparecen ML/MARL:

* [ ] varias seeds.
* [ ] center statistic definido.
* [ ] banda definida.
* [ ] smoothing window declarado.
* [ ] raw or lightly smoothed curve disponible.
* [ ] evaluación separada de training reward.
* [ ] no escoger “best seed”.
* [ ] no usar test set para seleccionar epoch.

---

# 31. BOX PLOTS

* [ ] definir median/IQR/whiskers si no estándar.
* [ ] mostrar puntos cuando \(n\) es pequeño.
* [ ] evitar cajas para \(n<5\).
* [ ] no interpretar width si es constante.
* [ ] outliers no eliminar.
* [ ] mismo rango y escala en comparación.
* [ ] orden lógico.
* [ ] preferir paired dots si diseño pareado es importante.

---

# 32. VIOLIN PLOTS

Usarlos solo si hay suficiente \(n\).

* [ ] KDE no crear estructura falsa con \(n\) pequeño.
* [ ] bandwidth razonable.
* [ ] mostrar mediana/quantiles.
* [ ] idealmente puntos o box superpuesto.
* [ ] misma bandwidth logic entre grupos.
* [ ] no cortar densidad de forma engañosa.

Con \(n\) pequeño:

> strip/swarm > violin.

---

# 33. Strip / swarm plots

Muy buenos para \(n\) pequeño/mediano.

* [ ] jitter solo horizontal.
* [ ] no codificar valor falso con jitter vertical.
* [ ] alpha legible.
* [ ] si paired, conectar pares cuando no haya demasiados.
* [ ] no conectar 300 pares creando spaghetti.

---

# 34. Paired plots

Para tu tesis son especialmente valiosos.

* [ ] mismo mundo conectado entre métodos.
* [ ] líneas finas.
* [ ] statistic summary encima o al lado.
* [ ] efecto pareado reportado.
* [ ] no convertir observaciones correlacionadas en independientes.
* [ ] si \(n\) grande, usar difference plot.

---

# 35. Difference / effect plots

Excelente alternativa a barras.

Plotear:

$$
\Delta_i = y_{i,B}-y_{i,A}.
$$

* [ ] cero visible.
* [ ] IC del efecto.
* [ ] distribución de diferencias.
* [ ] signo favorable etiquetado.
* [ ] no hacer que usuario tenga que restar mentalmente dos barras.

Para H3:

> mejor mostrar directamente \(\Delta T\).

---

# 36. HISTOGRAMS

* [ ] bins justificados.
* [ ] misma bins para grupos comparados.
* [ ] rango común.
* [ ] count vs density claramente indicado.
* [ ] no escoger bins que fabriquen multimodalidad.
* [ ] no superponer 5 histogramas opacos.
* [ ] usar outline/alpha o small multiples.

---

# 37. KDE plots

* [ ] bandwidth reportado o estándar.
* [ ] suficiente muestra.
* [ ] soporte físico respetado.
* [ ] no permitir densidad en valores imposibles:

  * probabilidad <0;
  * tiempo <0.
* [ ] comparar con ECDF si la forma importa.

---

# 38. ECDF

Para distribuciones suele ser excelente.

* [ ] y = proporción acumulada.
* [ ] n claro.
* [ ] sin binning.
* [ ] marcar mediana/p95 si relevante.
* [ ] varias series distinguibles.
* [ ] no suavizar.

Para runtimes:

> ECDF frecuentemente mejor que histograma.

---

# 39. ERROR-BAR PLOTS

* [ ] definir center.
* [ ] definir error bar.
* [ ] CI ≠ SD.
* [ ] asymmetric CI mostrado asimétricamente.
* [ ] caps visibles.
* [ ] no poner 20 barras de error superpuestas.
* [ ] usar point-range mejor que bar+error cuando cero no importa.

---

# 40. HEATMAPS

* [ ] colorbar siempre.
* [ ] unidad.
* [ ] mínimo/máximo definidos.
* [ ] sequential/diverging correcto.
* [ ] centro de diverging meaningful.
* [ ] mismos limits entre paneles comparables.
* [ ] no autoscale cada panel independientemente sin decirlo.
* [ ] annotations solo si legibles.
* [ ] color del texto adaptativo a fondo.
* [ ] labels x/y claros.
* [ ] cells suficientemente grandes.
* [ ] no usar rainbow.

---

# 41. Heatmaps de valores normalizados

* [ ] rango esperado indicado:

  * `[0,1]`;
  * porcentaje;
  * z-score.
* [ ] no mezclar escalas.
* [ ] missing values diferenciados de cero.
* [ ] NaN con color específico.
* [ ] legenda de missing.

---

# 42. Confusion matrices

* [ ] counts o proportions, indicar cuál.
* [ ] normalización por fila/columna clara.
* [ ] diagonales no magnificadas por color independiente.
* [ ] mismo color scale entre métodos.
* [ ] números visibles.
* [ ] clases en mismo orden.
* [ ] total \(n\).

---

# 43. Correlation matrices

* [ ] solo si correlación responde pregunta.
* [ ] triangular para evitar duplicación.
* [ ] diverging palette centrada en 0.
* [ ] escala fija \([-1,1]\).
* [ ] no usar correlación para inferir causalidad.
* [ ] significance markers solo si necesarias y ajustadas.

---

# 44. NETWORK / GRAPH figures

Muy relevantes para comunicación/topología.

* [ ] nodes legibles.
* [ ] edges no dominan.
* [ ] edge crossings minimizados.
* [ ] posición física vs layout abstracto claramente diferenciados.
* [ ] color de nodo tiene significado.
* [ ] thickness de edge tiene significado.
* [ ] directed arrows visibles.
* [ ] legend.
* [ ] no usar force-directed layout si luego interpretas distancia geométricamente.
* [ ] grafo nominal/degradado con misma posición de nodos para comparar.
* [ ] nodos perdidos/partición claramente identificados.

---

# 45. Topology comparisons

Si comparas:

* complete;
* ring;
* R-disk;
* degraded;

mantener:

* mismos nodos;
* mismas posiciones;
* mismos colores;
* cambiar solo edges.

Así el lector ve **la variable experimental**, no un layout nuevo.

---

# 46. TRAJECTORY PLOTS — robótica

Este tipo necesita reglas específicas.

* [ ] aspect ratio = 1:1.
* [ ] `axis equal`.
* [ ] metros en ambos ejes.
* [ ] obstáculos a escala.
* [ ] footprint de robots/carga a escala.
* [ ] origen/destino.
* [ ] flecha de orientación si importa.
* [ ] trayectoria nominal vs ejecutada diferenciadas.
* [ ] timestamps/event markers si necesarios.
* [ ] start/end markers.
* [ ] collision point si ocurrió.
* [ ] clearance visual.
* [ ] ningún objeto dibujado con tamaño arbitrario.

**Nunca** deformar x/y para “ver mejor” una ruta física.

---

# 47. Trayectorias multi-robot

* [ ] evitar 100 colores.
* [ ] colorear por coalición o rol.
* [ ] robots de una coalición con misma familia de color.
* [ ] diferenciar miembro fallido/reemplazo.
* [ ] no etiquetar cada timestep.
* [ ] markers de eventos:

  * docking;
  * failure;
  * replacement;
  * delivery.
* [ ] posiciones de carga visibles.
* [ ] camino de carga destacado sobre robots si ese es el objeto de análisis.

---

# 48. Swept footprint figures

Para demostrar seguridad:

* [ ] dibujar footprint real/convex hull.
* [ ] no solo centro de masa.
* [ ] obstáculos inflados si esa es la abstracción.
* [ ] distinguir:

  * robot center path;
  * load path;
  * swept footprint.
* [ ] clearance mínimo marcado.
* [ ] collision geometry real.

---

# 49. Path-planning comparison

* [ ] mismos start/goal.
* [ ] mismo mapa.
* [ ] mismos obstáculos.
* [ ] misma footprint.
* [ ] método no cambiar color entre paneles.
* [ ] métricas en pequeño inset/table si útil:

  * length;
  * time;
  * clearance;
  * computation.
* [ ] evitar comparar rutas con mapas distintos.

---

# 50. Vector fields / phase portraits

* [ ] flechas normalizadas o magnitud real: indicar cuál.
* [ ] evitar saturación de flechas.
* [ ] nullclines/critical points visibles.
* [ ] estabilidad codificada claramente.
* [ ] simplex boundary exacta.
* [ ] direction field no ocultar trayectorias.
* [ ] streamline density moderada.
* [ ] no usar 3D si 2D basta.

Para tus dinámicas poblacionales:

> mismas coordenadas del simplex en todos los paneles.

---

# 51. Simplex plots

* [ ] vértices etiquetados.
* [ ] misma orientación de simplex en toda tesis.
* [ ] masa/probabilidad suma 1.
* [ ] trayectoria dentro del simplex.
* [ ] equilibrium marker diferenciado.
* [ ] arrows no saturadas.
* [ ] no interpretar distancia Euclídea sin justificación si no procede.

---

# 52. Pareto fronts

* [ ] ejes claramente “minimize/maximize”.
* [ ] puntos dominados vs no dominados.
* [ ] frontier no conectar de forma falsa.
* [ ] baseline destacado.
* [ ] knee point solo si se define matemáticamente.
* [ ] no seleccionar visualmente un “best” sin scalarization.

---

# 53. Log plots

* [ ] base indicada si no es estándar.
* [ ] ticks legibles.
* [ ] nunca 0 en log.
* [ ] valores no positivos tratados explícitamente.
* [ ] error bars compatibles.
* [ ] no mezclar log y lineal entre paneles sin señalización.
* [ ] slope reference solo si tiene interpretación.

---

# 54. Runtime / scaling plots

* [ ] median/p95 mejor que solo mean cuando hay heavy tails.
* [ ] log y si rango grande.
* [ ] número de seeds.
* [ ] timeouts incluidos.
* [ ] timeout threshold visible.
* [ ] no estimar complejidad asintótica desde pocos puntos.
* [ ] measured CPU ≠ theoretical complexity.
* [ ] hardware/software environment indicado en caption/methods.

---

# 55. Speedup plots

* [ ] baseline claramente definido.
* [ ] speedup:

$$
S=T_{\text{baseline}}/T_{\text{method}}
$$

* [ ] línea \(S=1\).
* [ ] mismo hardware.
* [ ] misma precisión/quality target.
* [ ] no comparar solver exacto y heurístico sin calidad.

---

# 56. Failure-rate plots

* [ ] denominator incluye fallos/timeouts.
* [ ] no condicionar silenciosamente en “runs successful”.
* [ ] categorías mutuamente excluyentes o declarar overlaps.
* [ ] preferir proportions con CI.
* [ ] counts si \(n\) pequeño.

---

# 57. Reliability / success plots

No usar solo barras de 0.99 vs 1.00.

Mejor:

* exact counts;
* CI;
* difference plot.

Si:

$$
359/360
$$

es más informativo escribirlo.

---

# 58. Ablation plots

* [ ] cambiar una cosa por vez.
* [ ] si se cambian 3 componentes, nombrarlo “block ablation”.
* [ ] mismo mundo.
* [ ] baseline visible.
* [ ] effect vs full method.
* [ ] no ordenar ablaciones como ranking absoluto.
* [ ] indicar qué se removió exactamente.

---

# 59. Sensitivity plots

* [ ] parámetro x realmente es el único barrido.
* [ ] otros params congelados.
* [ ] rango justificado.
* [ ] valor nominal marcado.
* [ ] no seleccionar nominal después de ver mejor resultado sin declararlo.
* [ ] CI por valor.
* [ ] no conectar si parámetro es categorical.

---

# 60. Hyperparameter heatmaps

* [ ] desarrollo vs confirmatorio claramente separado.
* [ ] no presentar tuning como evidencia final.
* [ ] valor elegido marcado.
* [ ] misma metric scale.
* [ ] no ocultar regiones fallidas.
* [ ] NaN/fail color específico.

---

# 61. Bibliometric timeline plots

Para tus figuras académicas:

* [ ] año 2026 parcial claramente indicado.
* [ ] counts vs proportions.
* [ ] denominador.
* [ ] una fuente puede estar en varias categorías: decirlo.
* [ ] no interpretar crecimiento absoluto sin normalización.
* [ ] no “línea de tendencia” sobre 3 puntos sin justificación.
* [ ] categorías estables a través del tiempo.
* [ ] cambios de taxonomía prohibidos.

---

# 62. Patent trend plots

* [ ] familia vs documento.
* [ ] deduplicación.
* [ ] CPC.
* [ ] assignee enrichment.
* [ ] rolling window claramente definida.
* [ ] años incompletos.
* [ ] diferencia entre shares y counts.
* [ ] no decir adopción industrial.
* [ ] sensitivities como panel separado o error range.

---

# 63. Country bar charts

* [ ] nombres/ISO codes claros.
* [ ] misma población/denominador.
* [ ] periodos claramente comparables.
* [ ] grouped bars para early vs recent.
* [ ] colores suficientemente distintos.
* [ ] valores encima de barras con headroom.
* [ ] ordenar por periodo reciente o total y declararlo.
* [ ] no mezclar inventor country, assignee country y filing office.

---

# 64. Company / assignee plots

* [ ] consolidar subsidiarias si aplica.
* [ ] regla de normalización documentada.
* [ ] no tratar nombres similares como mismo grupo sin evidencia.
* [ ] top-N + “otros” si necesario.
* [ ] no cherry-pick empresas tecnológicas esperadas.

---

# 65. Treemaps

Usar con mucha cautela.

* [ ] solo para composición jerárquica.
* [ ] no para comparaciones precisas.
* [ ] labels caben.
* [ ] área proporcional a valor.
* [ ] colores no duplican área sin necesidad.

En tesis científica:

> barras suelen ser mejores.

---

# 66. Pie charts

Mi recomendación:

$$
\boxed{\text{evitarlos}}
$$

salvo 2–3 categorías muy simples.

Para comparación precisa:

> bar chart.

---

# 67. Radar/spider charts

También evitar salvo caso excepcional.

Son difíciles de comparar y dependen del orden de ejes.

Si se usan:

* [ ] misma escala.
* [ ] orden justificado.
* [ ] no usar área como métrica.
* [ ] máximo pocas series.

Pero prefiero:

> dot plot / heatmap.

---

# 68. 3D plots

Evitar si no hay una tercera variable espacial real.

* [ ] nunca 3D bars.
* [ ] evitar perspectiva que oculta datos.
* [ ] no usar por estética.
* [ ] para superficie matemática real, incluir colorbar/contours.
* [ ] si existe oclusión, vistas complementarias.

---

# 69. Contour/surface plots

* [ ] niveles significativos.
* [ ] colorbar.
* [ ] contours labels si necesarios.
* [ ] optimum marker.
* [ ] feasible/infeasible regions diferenciadas.
* [ ] no extrapolar fuera del sampled domain.
* [ ] aspect ratio de variables significativo.

---

# 70. Architecture / block diagrams

Para tu tesis, importantísimos.

* [ ] flujo principal izquierda→derecha o arriba→abajo.
* [ ] no hacer zigzag.
* [ ] máximo 5–7 bloques principales.
* [ ] misma forma = mismo tipo de objeto.
* [ ] flechas con significado consistente.
* [ ] inputs/outputs nombrados.
* [ ] feedback separado.
* [ ] global vs local visualmente distinguible.
* [ ] no meter párrafos dentro de cajas.
* [ ] font ≥ texto de plots.
* [ ] suficiente white space.
* [ ] alinear cajas perfectamente.

---

# 71. Contract diagrams

Tu arquitectura tiene “certificados”.

Representaría cada interfaz con:

$$
\boxed{
\text{input}
\rightarrow
[\text{test/certificate}]
\rightarrow
\text{output}
}
$$

y debajo:

> dominio / no garantiza.

* [ ] no más de una línea de caveat.
* [ ] usar tabla para caveats largos.
* [ ] no usar “certificado” para evidencia bibliográfica.

---

# 72. Flowcharts

* [ ] decision diamonds solo para decisiones.
* [ ] process boxes para procesos.
* [ ] start/end.
* [ ] flechas no se cruzan.
* [ ] loops visibles.
* [ ] yes/no labels.
* [ ] no más de una ruta visual dominante.
* [ ] no usar flowchart para arquitectura estática.

---

# 73. State machine / hybrid diagrams

* [ ] estados definidos.
* [ ] guards en transiciones.
* [ ] resets si aplica.
* [ ] no mezclar estado físico con algoritmo.
* [ ] dirección de arrows clara.
* [ ] self-loops limpios.
* [ ] fallo/recovery destacable.
* [ ] terminal state.

---

# 74. Physical schematics

* [ ] dimensiones.
* [ ] coordinate frame.
* [ ] COM.
* [ ] forces.
* [ ] torques.
* [ ] contacts.
* [ ] normals/tangents.
* [ ] robot IDs.
* [ ] scale.
* [ ] notación igual a ecuación.
* [ ] flechas de fuerza apuntan en dirección correcta.
* [ ] no usar arrow puramente decorativa.

---

# 75. Wrench/contact diagrams

Especialmente:

* [ ] fuerza parte del contacto.
* [ ] brazo \(r_i\) desde COM a contacto.
* [ ] sentido de torque correcto.
* [ ] frame \(B/W\) identificado.
* [ ] normal/tangent.
* [ ] bilateral/unilateral visualmente diferenciados.
* [ ] friction cone si se modela.
* [ ] si NO se modela fricción, no dibujar cono implícitamente.

---

# 76. Robotics screenshots / CoppeliaSim

* [ ] resolución alta.
* [ ] UI recortada salvo que sea relevante.
* [ ] cámara útil, no cinematográfica.
* [ ] robot/carga visibles.
* [ ] obstáculos visibles.
* [ ] labels agregados vectorialmente, no con pixel font.
* [ ] scale/reference.
* [ ] caption dice “simulación”.
* [ ] no llamar “real”.
* [ ] si es representative frame, especificar seed/time.
* [ ] no escoger únicamente frame exitoso si se reportan fallos.

---

# 77. Before/after screenshots

* [ ] misma cámara.
* [ ] mismo zoom.
* [ ] misma escena.
* [ ] misma escala.
* [ ] cambios anotados.
* [ ] evitar imágenes que no pueden compararse.

---

# 78. Animation frames / sequence

* [ ] tiempo indicado.
* [ ] intervalos consistentes.
* [ ] misma cámara.
* [ ] misma escala.
* [ ] arrows discretas.
* [ ] eventos claros.
* [ ] no más de 4–6 frames por figura.

---

# 79. Maps / floorplans

* [ ] unidades.
* [ ] aspect equal.
* [ ] obstáculos a escala.
* [ ] legend.
* [ ] start/goal.
* [ ] paths.
* [ ] coordinate frame.
* [ ] no text overlapping corridors.
* [ ] labels fuera del área de movimiento cuando sea posible.

---

# 80. Tables rendered as figures

Evitar.

Si es texto/valores:

> LaTeX table > PNG.

Solo usar imagen si es esquema gráfico real.

---

# 81. Statistical annotation placement

* [ ] brackets no tocan bars/error bars.
* [ ] p-values no se montan.
* [ ] altura escalonada.
* [ ] no 20 brackets en un plot.
* [ ] si muchas comparaciones, mover a tabla.
* [ ] adjusted p-value claramente marcado.
* [ ] dirección de contraste definida.

---

# 82. Decimal precision

Congelar por métrica.

Ejemplo:

* success: 3 decimals;
* time: 2 decimals;
* messages: 1;
* p: scientific notation;
* distance: 3 m si precisión lo justifica.

No:

> 37.400000.

Ni mezclar:

> 0.9, 0.91337, 0.92.

---

# 83. Units

Nature recomienda nomenclatura SI y separación correcta entre número y unidad. ([Nature][2])

* [ ] `[m]`
* [ ] `[s]`
* [ ] `[N]`
* [ ] `[N m]`
* [ ] `[J]`
* [ ] `[rad/s]`
* [ ] `[ms]`

No poner unidad repetida en cada tick.

---

# 84. Legend

* [ ] no tapa datos.
* [ ] orden igual al visual.
* [ ] misma terminología en todas figuras.
* [ ] evitar borde pesado.
* [ ] máximo razonable de items.
* [ ] si 8 items, revisar diseño.
* [ ] direct labels preferibles en line plot cuando posible.
* [ ] no repetir leyenda en cada panel si compartida.

---

# 85. Direct labeling

IEEE recomienda conectar el label directamente a la línea cuando ayuda accesibilidad. ([IEEE Author Center Journals][3])

Para 2–4 curvas:

> label al final de cada curva puede ser mejor que leyenda.

* [ ] no overlap.
* [ ] padding.
* [ ] color + nombre.
* [ ] ordenar verticalmente.

---

# 86. Insets

Usar solo cuando:

* detalle pequeño es realmente necesario.

* [ ] indicar región ampliada.

* [ ] inset no tapa datos.

* [ ] ejes del inset claros.

* [ ] no meter tres insets.

* [ ] si el inset contiene otra narrativa, hacer panel separado.

---

# 87. Broken axes

Evitar.

Si imprescindible:

* [ ] símbolo de ruptura visible.
* [ ] caption lo explica.
* [ ] no barras.
* [ ] no usar para exagerar diferencia.

---

# 88. Secondary y-axis

Mi recomendación:

$$
\boxed{\text{evitar}}
$$

Puede crear relaciones visuales artificiales.

Preferir:

* dos paneles alineados;
* normalized metrics;
* small multiples.

Si se usa:

* [ ] colores de labels coinciden con series;
* [ ] no manipular escalas;
* [ ] relación física real.

---

# 89. Facets / small multiples

Muy buenos para tesis.

* [ ] misma escala cuando comparación lo requiere.
* [ ] mismos colores.
* [ ] mismo orden.
* [ ] title solo variable del facet.
* [ ] no repetir leyenda.
* [ ] suficiente tamaño de panel.

---

# 90. Annotations

* [ ] solo eventos/hallazgos importantes.
* [ ] frases cortas.
* [ ] flechas discretas.
* [ ] no escribir interpretación completa dentro del plot.
* [ ] evitar texto diagonal salvo estricta necesidad.

---

# 91. Figure-to-text consistency

Para cada figura:

* [ ] número coincide.
* [ ] caption coincide.
* [ ] nombres de métodos coinciden.
* [ ] valores del texto coinciden.
* [ ] \(n\) coincide.
* [ ] IC coincide.
* [ ] unidades coinciden.
* [ ] símbolos coinciden.
* [ ] colores descritos coinciden.

---

# 92. Figure-to-data provenance

Cada figura debe tener:

* source data;
* script;
* config;
* seed set;
* commit/hash si quieres internamente;
* output PDF/SVG.

Pero **esa información no necesita imprimirse dentro de la figura**.

Guardar internamente:

```text
fig_XX
data -> ...
script -> ...
config -> ...
output -> ...
```

No meter `SHA-256`, paths largos o nombres internos en el cuerpo.

---

# 93. Test automático de bounding boxes

Sonnet/Codex debería automatizar:

* detectar objects fuera del canvas;
* `bbox_inches="tight"` cuando corresponda;
* verificar text bounding boxes;
* warnings de constrained layout;
* overflows;
* dimensiones finales.

Pero después:

$$
\boxed{\text{visual inspection mandatory}}
$$

---

# 94. Test de overlap automático

Para plots con labels:

Calcular bounding boxes de cada `Text` en renderer coordinates.

Para todo par:

$$
\operatorname{IoU}(B_i,B_j)>0
$$

o intersección > pequeño umbral:

> FAIL.

También:

* text vs legend;
* text vs axis title;
* text vs colorbar;
* text vs annotation.

No reemplaza visión, pero detecta muchos errores.

---

# 95. Test de clipping

Para cada objeto:

$$
B_{\text{object}}
\subseteq
B_{\text{figure}}.
$$

Revisar:

* ticklabels;
* axis labels;
* legends;
* text;
* panel labels;
* colorbars.

---

# 96. Test de font sizes

Extraer programáticamente:

* axes title;
* xlabel;
* ylabel;
* tick labels;
* legend;
* annotations.

Comparar con style sheet.

Cualquier tamaño no permitido:

> FAIL.

---

# 97. Test de colors

Programáticamente:

* detectar más de N categorical colors;
* detectar `jet`;
* detectar red-green only contrasts;
* verificar palette mapping consistente entre figuras.

---

# 98. Test de final physical size

No revisar únicamente 2000×1200 px.

Exportar a **la anchura real usada en la tesis**.

Por ejemplo:

$$
W_{\text{fig}}\approx 150-160\,\text{mm}
$$

si ocupa casi todo A4.

Después verificar texto.

---

# 99. Page-context test

La misma figura puede ser bonita sola y mala dentro del PDF.

Revisar:

* [ ] ancho visual.
* [ ] espacio arriba/abajo.
* [ ] caption.
* [ ] page break.
* [ ] siguiente heading.
* [ ] no huérfanos.
* [ ] no media página vacía.
* [ ] no figura separada de su primera referencia.

---

# 100. Thumbnail test

Ver todas las páginas como thumbnails.

Buscar:

* figuras demasiado pequeñas;
* páginas saturadas;
* figuras gigantes sin necesidad;
* cambios de paleta;
* cambios de font;
* panels inconsistentes.

Esto detecta falta de identidad visual.

---

# 101. Print test

Antes de depositar:

* imprimir unas 10 páginas representativas:

  * bar;
  * scatter;
  * heatmap;
  * trajectory;
  * diagram;
  * multipanel;
  * screenshot.

Preguntar:

* [ ] ¿leo todo sin lupa?
* [ ] ¿grayscale funciona?
* [ ] ¿líneas sobreviven?
* [ ] ¿colores distinguibles?
* [ ] ¿labels caben?

---

# 102. Reviewer-5-second test

Mostrar la figura 5 segundos y ocultarla.

Preguntar:

> ¿Qué mensaje principal viste?

Si nadie puede responder:

> hay demasiada información o falta jerarquía.

---

# 103. Reviewer-30-second test

Dar 30 s.

Debe poder identificar:

* ejes;
* métodos;
* variable principal;
* dirección del efecto;
* incertidumbre.

---

# 104. Standalone test

Figura + caption deben permitir saber:

* qué se comparó;
* sobre qué \(n\);
* qué representan ejes;
* qué es error bar;
* qué significa color;
* resultado visual principal.

Sin leer 5 páginas.

---

# 105. “No white millimeter wasted” — pero con cuidado

Tu criterio anterior de aprovechar espacio es válido, pero:

$$
\boxed{\text{densidad útil}\neq\text{llenar cada hueco}}
$$

Un buen figure puede tener white space.

No llenar un espacio solo porque existe.

Cada elemento debe tener una narrativa.

---

# 106. Figura compleja tipo dashboard

Si quieres concentrar mucha información:

* [ ] máximo 1 narrativa central.
* [ ] 2–4 narrativas secundarias.
* [ ] jerarquía visual.
* [ ] panel principal más grande.
* [ ] mini-widgets secundarios.
* [ ] alignment grid.
* [ ] misma paleta.
* [ ] evitar 7 gráficos del mismo peso.
* [ ] caption explica lectura.

---

# 107. Hero figure de la tesis

Debe existir una figura que resuma:

$$
\text{reclutar}
\to
\text{certificar wrench}
\to
\text{transportar}
\to
\text{recuperar}
\to
\text{reservar}.
$$

Requisitos:

* legible;
* no más de ~6 pasos;
* physical layer visible;
* global/local dependencies visibles;
* certificados en interfaces;
* sin meter teoremas completos.

---

# 108. Audit específico de TODAS las figuras de este TFM

Yo crearía una hoja con una fila por figura:

| ID | Tipo | Función | Fuente | Vector | Font OK | Overlap | Color | n/stat | Caption | Scientific | Visual | Action |
| -- | ---- | ------- | ------ | ------ | ------- | ------- | ----- | ------ | ------- | ---------- | ------ | ------ |

Y acciones:

$$
\text{KEEP}
\quad
\text{REDESIGN}
\quad
\text{MERGE}
\quad
\text{SPLIT}
\quad
\text{MOVE SUPP}
\quad
\text{DELETE}.
$$

---

# 109. Score visual por figura

Puntuar 0–2:

| Criterio             | 0              | 1          | 2           |
| -------------------- | -------------- | ---------- | ----------- |
| legibilidad          | mala           | suficiente | excelente   |
| overlap/clipping     | presente       | dudoso     | ninguno     |
| tipografía           | inconsistente  | casi       | uniforme    |
| color                | confuso        | aceptable  | accesible   |
| ejes/unidades        | incompletos    | casi       | completos   |
| estadística          | ambigua        | parcial    | completa    |
| caption              | insuficiente   | usable     | autónoma    |
| densidad             | saturada/vacía | razonable  | óptima      |
| mensaje              | confuso        | visible    | inmediato   |
| integración estética | ajena          | casi       | misma tesis |

Máximo:

$$
20.
$$

No aprobar ninguna figura con:

$$
<18/20
$$

ni con un `0` en **overlap/clipping, ejes/unidades o integridad científica**.

---

# 110. Gate final de cada figura

Una figura solo recibe:

$$
\boxed{\text{FIGURE\_FINAL = TRUE}}
$$

cuando pase:

1. **Data gate** — datos correctos.
2. **Scientific gate** — representación correcta.
3. **Statistical gate** — \(n\), IC, tests correctos.
4. **Typography gate** — fonts consistentes.
5. **Overlap gate** — cero overlap.
6. **Clipping gate** — cero clipping.
7. **Color gate** — accesible/grayscale.
8. **Resolution gate** — vector o dpi correcto.
9. **Caption gate** — autónoma.
10. **Layout gate** — correcta dentro del PDF.
11. **Cross-reference gate** — texto/caption/data coinciden.
12. **Human visual inspection** — aprobada mirando el render final.

Si Claude dice:

> “la figura compila correctamente”

eso **no significa que la figura pasa**.

La condición correcta es:

> **“Compilé, rendericé a tamaño final, inspeccioné visualmente el render y no detecté overlap, clipping, ilegibilidad ni inconsistencia científica.”**

---

## Las reglas profesionales que congelaría para TODO el TFM

En resumen, usaría estas como **house style obligatorio**:

$$
\boxed{
\begin{aligned}
&\text{plots vectoriales PDF/SVG};\\
&\text{raster }\ge300\text{ dpi, line art }\ge600\text{ dpi};\\
&\text{font interno ideal }9\!-\!10\text{ pt};\\
&\text{nunca depender solo del color};\\
&\text{grayscale test obligatorio};\\
&\text{cero overlap};\\
&\text{cero clipping};\\
&\text{unidades SI};\\
&\text{error bars definidos};\\
&n\text{ explícito};\\
&\text{misma semántica de colores en toda la tesis};\\
&\text{inspección visual a tamaño final obligatoria}.
\end{aligned}
}
$$

IEEE respalda especialmente el uso de vector, resolución alta, fonts consistentes y redundancia color/forma; Nature añade simplicidad, captions autosuficientes y definición explícita de estadísticas/error bars. ([IEEE Author Center Journals][1])

Para tu caso concreto, yo convertiría este checklist en una instrucción directa para Sonnet/Codex: **recorrer Figure 1 → Figure N, renderizar cada página, puntuarla, generar `FIGURE_AUDIT.csv`, y no tocar la ciencia todavía; solo identificar KEEP / REDESIGN / SPLIT / MERGE / SUPPLEMENT / DELETE**. Esa auditoría visual aislada va a encontrar cosas que ni Claude leyendo LaTeX ni nosotros leyendo el texto vemos.

[1]: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/?utm_source=chatgpt.com "Resolution and Size - IEEE Author Center Journals"
[2]: https://www.nature.com/nature/for-authors/formatting-guide?utm_source=chatgpt.com "Formatting guide | Nature"
[3]: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/?utm_source=chatgpt.com "Create Graphics for Your Article - IEEE Author Center Journals"
[4]: https://matplotlib.org/stable/users/explain/axes/tight_layout_guide.html?utm_source=chatgpt.com "Tight layout guide — Matplotlib 3.11.2 documentation"
[5]: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/file-formatting/?utm_source=chatgpt.com "File Formatting - IEEE Author Center Journals"
[6]: https://www.nature.com/nature/for-authors/final-submission?utm_source=chatgpt.com "Final submission | Nature"
[7]: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/prepare-supplementary-materials/?utm_source=chatgpt.com "Prepare Supplementary Materials - IEEE Author Center Journals"
[8]: https://www.nature.com/nature/for-authors/initial-submission?utm_source=chatgpt.com "Initial submission | Nature"
Sí. Esta debería ser una auditoría independiente de la revisión editorial general. Aquí la pregunta sería:

> **¿La tesis utiliza la literatura como lo haría un investigador serio: fuentes reales, relevantes, primarias cuando corresponde, correctamente interpretadas, citadas exactamente donde sostienen una afirmación, integradas críticamente en el argumento y referenciadas sin un solo error APA?**

Para tu TFM usaría un **Mega-checklist de Literatura, Marco Teórico, Fuentes, Citaciones y Referencias** con gates suficientemente estrictos como para que una fuente incorrecta, una cita que no sustente lo dicho o un DOI inventado hagan fallar la auditoría.

La base normativa es clara. Las instrucciones específicas del Máster VIU en Robótica exigen **APA 7.ª edición** para citas y referencias y dicen expresamente que todas deben ser correctas.  VIU también exige originalidad, citar las fuentes consultadas y advierte del uso de herramientas antiplagio.  Para el Marco Teórico pide teorías, conceptos y antecedentes; una revisión crítica del estado del arte; identificar limitaciones; explicar fundamentos; analizar tecnologías/enfoques existentes y relacionar las herramientas utilizadas con los objetivos.  Finalmente, exige una bibliografía completa en APA 7 que incluya bibliografía temática **y metodológica**.  Otras guías oficiales VIU refuerzan además la correspondencia exacta entre citas y referencias, orden alfabético y sangría francesa. ([VIU Universidad Online][1])

Con eso, este sería mi estándar.

---

# MEGA-CHECKLIST DE LITERATURA, MARCO TEÓRICO, CITACIONES Y REFERENCIAS

## A. Gate cero: ninguna referencia existe “porque sí”

Para **cada referencia de la tesis** debemos poder responder:

* [ ] ¿Existe realmente?
* [ ] ¿La hemos leído o inspeccionado suficientemente?
* [ ] ¿Sabemos exactamente qué afirmación sostiene?
* [ ] ¿Es la mejor fuente disponible para esa afirmación?
* [ ] ¿Es primaria o estamos citando una fuente secundaria innecesariamente?
* [ ] ¿La cita está situada junto a la afirmación que sustenta?
* [ ] ¿La tesis no dice más que la fuente?
* [ ] ¿Los autores son correctos?
* [ ] ¿El año es correcto?
* [ ] ¿El título es exacto?
* [ ] ¿El venue es correcto?
* [ ] ¿El volumen/número/páginas o article number son correctos?
* [ ] ¿El DOI pertenece realmente a ese documento?
* [ ] ¿El DOI resuelve?
* [ ] ¿Existe una versión publicada más reciente que el preprint?
* [ ] ¿Ha sido retractado o corregido?
* [ ] ¿La entrada APA está correcta?
* [ ] ¿Aparece en el texto?
* [ ] ¿Toda cita en texto tiene referencia?
* [ ] ¿Podría un jurado abrirla y encontrar lo que nosotros afirmamos?

Una sola respuesta “no sé” → **referencia pendiente**.

---

# B. Pregunta fundamental del Marco Teórico

El Marco Teórico de VIU no debe ser una colección de resúmenes. VIU exige analizar teorías, conceptos, antecedentes, tecnologías y limitaciones que justifiquen el estudio. 

Cada sección debe responder:

$$
\boxed{
\text{¿Qué necesita saber el lector para entender por qué mi solución tiene esta forma?}
}
$$

Revisar:

* [ ] ¿Cada teoría introducida se utiliza después?
* [ ] ¿Cada método discutido reaparece como fundamento, comparador o contraste?
* [ ] ¿Cada concepto contribuye a una RQ/OE/hipótesis?
* [ ] ¿Hay teoría incluida únicamente “porque es interesante”?
* [ ] ¿Hay libros enteros resumidos sin impacto posterior?
* [ ] ¿Hay literatura que pueda eliminarse sin cambiar ningún argumento?
* [ ] ¿Falta teoría necesaria para entender un teorema o experimento posterior?
* [ ] ¿El nivel de detalle es proporcional a su importancia?

VIU pide precisamente que los fundamentos ya propios del máster se presenten brevemente y que los nuevos o profundizados reciban mayor detalle. 

---

# C. Arquitectura intelectual del Marco Teórico

No organizarlo como:

> Autor A hizo X.
> Autor B hizo Y.
> Autor C hizo Z.

Organizarlo por **problemas y propiedades**.

Para tu TFM:

$$
\text{asignación/coalición}
\rightarrow
\text{información/juegos}
\rightarrow
\text{contacto/wrench}
\rightarrow
\text{transporte/control}
\rightarrow
\text{seguridad}
\rightarrow
\text{fallo/recuperación}
\rightarrow
\text{tráfico/red}
$$

Para cada bloque:

* [ ] Definir el problema.
* [ ] Identificar familias metodológicas.
* [ ] Explicar qué garantía entrega cada familia.
* [ ] Explicar qué información requiere.
* [ ] Explicar qué modelo físico supone.
* [ ] Explicar qué NO resuelve.
* [ ] Identificar trabajos más próximos.
* [ ] Terminar con la implicación concreta para tu diseño.

La última frase de cada subsection debería poder escribirse como:

> “Por esta razón, en este TFM se necesita ______.”

Eso convierte literatura en **argumento**.

---

# D. Fundamentos vs Estado del Arte

Separar conceptualmente:

### Fundamentos

Resultados relativamente estables:

* juegos potenciales;
* GNE/VI;
* consenso;
* MRTA;
* wrench/grasp map;
* CBF;
* MAPF;
* Lyapunov/pasividad.

Aquí interesa:

$$
\text{definición}
+
\text{teorema pertinente}
+
\text{supuestos}
+
\text{cómo lo utilizas}.
$$

### Estado del Arte

Trabajos concretos recientes que intentan resolver tu problema.

Aquí interesa:

$$
\text{problema}
+
\text{método}
+
\text{evidencia}
+
\text{limitación}
+
\text{diferencia con tu tesis}.
$$

No mezclar continuamente ambas funciones.

---

# E. Cada fundamento teórico debe tener una “ficha”

Para cada teoría importante:

* [ ] Nombre.
* [ ] Fuente fundacional.
* [ ] Fuente moderna/autoritaria si conviene.
* [ ] Definición.
* [ ] Supuestos.
* [ ] Resultado utilizado.
* [ ] Qué NO dice ese resultado.
* [ ] Adaptación hecha en el TFM.
* [ ] Qué hipótesis cambia la adaptación.
* [ ] Dónde se usa.
* [ ] Si se implementa o solo sirve de contexto.

Ejemplo conceptual:

**Juegos de potencial**

* Monderer & Shapley → fundamento.
* Sandholm → dinámica poblacional/contexto.
* Tu tesis → potencial particular.
* Demostrar tú mismo que tu payoff satisface identidad.
* No escribir “por Monderer-Shapley nuestro algoritmo converge” si esa convergencia requiere supuestos adicionales.

---

# F. Audit de “citation overreach”

Esta es una de las auditorías más importantes.

Para cada frase con cita:

> ¿La fuente realmente dice esto?

Clasificar:

### Nivel 1 — directo

La fuente demuestra/reportó exactamente la afirmación.

### Nivel 2 — síntesis razonable

La afirmación resulta de combinar varias fuentes.

Debe citar varias.

### Nivel 3 — inferencia del autor

Entonces escribir:

> “Esto sugiere…”
> “En este trabajo se interpreta…”
> “Estos resultados son compatibles con…”

### Nivel 4 — no sustentada

Eliminar o buscar evidencia.

---

# G. Una cita no debe sostener cuatro afirmaciones diferentes

Mal:

> X es distribuido, óptimo, robusto a pérdidas y escalable a 1000 robots (Autor, 2024).

Quizá el paper solo demuestra dos.

Mejor separar:

> X utiliza comunicación vecinal (Autor, 2024). En las instancias ensayadas alcanza… Sin embargo, el artículo no proporciona una garantía de optimalidad…

Checklist:

* [ ] Cada cita tiene objeto inequívoco.
* [ ] No queda al final de un párrafo con cuatro claims.
* [ ] Si varias fuentes sostienen distintos elementos, situarlas junto al elemento correspondiente.

---

# H. Verbos de atribución

Congelar una taxonomía.

### Si hay demostración formal

> demuestra
> establece
> prueba
> caracteriza

### Si hay experimento

> reporta
> observa
> obtiene
> evalúa

### Si es propuesta

> propone
> introduce
> formula
> plantea

### Si solo lo menciona

> describe
> documenta

### Si es interpretación nuestra

> sugiere
> es compatible con
> motiva

Nunca usar:

> “demuestra robustez”

para tres simulaciones.

---

# I. Jerarquía de fuentes

No todas las referencias tienen el mismo valor probatorio.

Para esta tesis usaría aproximadamente:

### Nivel A — evidencia científica primaria

* journal peer-reviewed;
* conference peer-reviewed de primer nivel;
* libros académicos de referencia.

En robótica, **ICRA/IROS/RSS/CoRL/etc. pueden tener enorme peso**; no asumir que journal > conference automáticamente.

### Nivel B — autoridad normativa/técnica

* ISO;
* ANSI/A3;
* VDA;
* documentación técnica oficial.

Adecuadas para:

> especificaciones, normas, interoperabilidad.

No para:

> demostrar rendimiento científico.

### Nivel C — preprints

* arXiv;
* TechRxiv.

Útiles para frontera reciente.

Pero marcar:

> preprint / no necesariamente peer-reviewed.

Si existe versión publicada:

$$
\boxed{\text{citar versión final}}
$$

salvo razón concreta para citar ambas.

### Nivel D — fabricante

Útiles para:

* producto;
* capacidad declarada;
* arquitectura anunciada;
* caso comercial.

Redactar:

> “El fabricante informa…”

No:

> “se ha demostrado…”

### Nivel E — patentes

Útiles para:

* actividad de protección;
* reivindicaciones;
* tendencias tecnológicas.

No prueban:

* despliegue;
* rendimiento;
* adopción;
* eficacia.

### Nivel F — blogs/Wikipedia/agregadores

Sirven para descubrir fuentes.

No deberían sostener claims científicos principales.

---

# J. Fuente primaria obligatoria cuando existe

Si dices:

> “CBBA garantiza…”

citar Choi et al., no un survey que menciona CBBA.

Si dices:

> “el Hungarian es polinómico…”

citar Kuhn/fuente matemática apropiada.

Si dices:

> “ORCA…”

citar van den Berg.

Si dices:

> “CBF…”

citar Ames y/o la fuente concreta utilizada.

Los reviews pueden utilizarse para:

* síntesis;
* taxonomía;
* contexto.

No para reemplazar sistemáticamente originales.

---

# K. Citation laundering

Buscar casos:

> Paper B dice que Paper A demostró X
> → nosotros citamos B como si B hubiera demostrado X.

Revisar.

Regla:

> Si el claim depende de A y A es recuperable, leer/citar A.

Purdue también recomienda que las fuentes secundarias se utilicen como tales, dejando claro que el original no fue consultado. ([Purdue OWL][2])

---

# L. SOTA real

Para cada tema central:

* [ ] clásico/fundacional;
* [ ] review reciente;
* [ ] 3–10 trabajos recientes realmente próximos;
* [ ] papers 2024–2026;
* [ ] trabajos adversariales que podrían invalidar nuestra brecha;
* [ ] literatura de grupos distintos.

No llenar 2026 solo por actualidad.

Un clásico relevante de 1995 puede ser mucho mejor que un paper superficial de 2026.

---

# M. Audit de actualidad

Para una tesis defendida en 2026:

* [ ] última búsqueda fechada;
* [ ] revisar 2025;
* [ ] revisar 2026 hasta fecha de cierre;
* [ ] buscar “online first”;
* [ ] buscar conference papers recientes;
* [ ] buscar publicados derivados de preprints que ya tenemos;
* [ ] verificar si un “gap” fue cerrado durante la escritura.

El estado del arte envejece.

El día de congelar la tesis haría una última búsqueda de:

> `multi-robot cooperative transport coalition formation`

y los conceptos específicos centrales.

---

# N. Audit de closest prior work

Construir una tabla privada de los **10–20 trabajos más peligrosos para la novedad**.

Columnas:

| Paper | Coalición dinámica | carga compartida | wrench | local | fallo/replacement | tráfico | hardware | garantía |
| ----- | ------------------ | ---------------- | ------ | ----- | ----------------- | ------- | -------- | -------- |

Después preguntar:

* [ ] ¿Cuál es el más parecido?
* [ ] ¿Qué hace que nosotros no?
* [ ] ¿Qué hacemos que él no?
* [ ] ¿La diferencia es realmente importante?
* [ ] ¿Es algoritmo, información, planta o garantía?
* [ ] ¿Estamos representándolo justamente?

Una tesis fuerte discute el rival más cercano, no el más fácil de superar.

---

# O. Literatura adversarial

Buscar deliberadamente papers que destruyan nuestra narrativa:

> “dynamic robot replacement cooperative transport”

> “distributed cooperative object transport heterogeneous robots”

> “coalition formation physical feasibility multi robot”

> “decentralized MPC cooperative transport”

> “multi robot transport failure recovery”

Si encuentras uno más cercano:

> actualizar la brecha.

Nunca esconderlo.

---

# P. Review balance

Evitar:

* 15 citas del mismo grupo;
* 12 referencias de un solo autor;
* autocitación artificial;
* exceso de un país/lab porque nuestra query favoreció cierto vocabulario.

Revisar diversidad de:

* grupos;
* métodos;
* perspectivas;
* años.

No por cuota política, sino para evitar **literature tunnel vision**.

---

# Q. Autocitas

Las propias publicaciones reales son citables si son relevantes.

Pero:

* [ ] no crear technical reports internos solo para citarlos;
* [ ] no citar “revisión matemática interna” como autoridad externa;
* [ ] no citar la propia tesis dentro de sí misma;
* [ ] no inflar bibliografía con artefactos internos.

Un resultado original del TFM:

> se presenta directamente.

No necesita autocita.

---

# R. Marco Teórico no debe anticipar resultados propios

Buscar frases:

> “como demostraremos…”

Está bien ocasionalmente.

Pero no llenar el review con:

> “nuestro método supera…”

El estado del arte debe permitir que la solución parezca **necesaria**, no predeterminada.

---

# S. No usar literatura para decorar

Mal:

> “La robótica es un campo en rápido crecimiento (A; B; C; D; E).”

Cinco citas sin función.

Toda cita debe hacer trabajo intelectual.

Preguntar:

> ¿Qué cambia si elimino esta cita?

Si nada:

> probablemente sobra.

---

# T. Citation dumping

Evitar:

> (A, 2017; B, 2018; C, 2019; D, 2020; E, 2021; F, 2022; G, 2023)

sin explicar diferencias.

Mejor:

> A y B abordan asignación; C y D añaden restricciones dinámicas; E introduce reemplazo…

Las citas se convierten en **síntesis**.

---

# U. Cada párrafo del Marco Teórico

Debe tener aproximadamente:

$$
\boxed{
\text{afirmación temática}
\to
\text{evidencia de literatura}
\to
\text{comparación/síntesis}
\to
\text{implicación para el TFM}
}
$$

No:

$$
\text{paper A}
\to
\text{paper B}
\to
\text{paper C}.
$$

---

# V. Conceptos comunes vs claims citables

No necesitas citar:

> “un robot posee posición y orientación”

si es mero contexto.

Sí debes citar:

* definiciones específicas;
* algoritmos;
* teoremas;
* estadísticas;
* capacidades de productos;
* resultados previos;
* normas;
* taxonomías;
* claims de novedad.

Evitar tanto la **subcitación** como la **sobrecitación**.

---

# W. Ecuaciones tomadas/adaptadas

Para cada ecuación que no es originalmente tuya:

* [ ] identificar origen;
* [ ] citar fuente;
* [ ] si está adaptada, decirlo;
* [ ] explicar cambios de símbolos;
* [ ] comprobar que los supuestos siguen siendo válidos;
* [ ] no atribuir a una fuente nuestra extensión.

Ejemplo:

> “Siguiendo la formulación de Ames et al. (2017), se particulariza la condición CBF al cuerpo compuesto…”

No fingir que la ecuación particular aparece literalmente en Ames.

---

# X. Teoremas de literatura

Para cada theorem importado:

* [ ] enunciado fiel;
* [ ] no eliminar hipótesis;
* [ ] no cambiar `joint connectivity` por `connected`;
* [ ] no cambiar tiempo continuo por discreto;
* [ ] no cambiar grafo dirigido por no dirigido;
* [ ] no cambiar convexidad por no convexidad;
* [ ] no transferir guarantee a una modificación.

En tu TFM esto es especialmente crítico en:

* consenso;
* primal-dual;
* juegos poblacionales;
* CBF;
* MAPF;
* estabilidad.

---

# Y. Adaptaciones de algoritmos

Si modificamos CBBA, ORCA, Smith, etc.:

No decir:

> “CBBA obtiene…”

si implementamos una adaptación.

Escribir:

> **“adaptación inspirada en CBBA”**

y citar original.

Separar:

$$
\text{garantía del paper}
\neq
\text{garantía de nuestra adaptación}.
$$

---

# Z. Literatura comercial

Para cada empresa:

* [ ] fuente oficial;
* [ ] fecha;
* [ ] producto exacto;
* [ ] qué afirma el fabricante;
* [ ] qué observamos nosotros;
* [ ] no añadir funciones no documentadas;
* [ ] no interpretar marketing como prueba independiente.

Verbos:

> “documenta”
> “declara”
> “describe”

No:

> “demuestra”.

---

# AA. Normas

Cada norma:

* [ ] organismo oficial;
* [ ] número exacto;
* [ ] año/edición;
* [ ] estado vigente;
* [ ] título exacto;
* [ ] alcance;
* [ ] qué excluye;
* [ ] URL oficial;
* [ ] fecha de consulta si es página dinámica.

No usar un blog para explicar ISO si la página oficial existe.

---

# AB. Patentes

Para un patent:

* [ ] publication/application/grant number correcto;
* [ ] jurisdiction;
* [ ] assignee;
* [ ] inventors;
* [ ] priority/publication date;
* [ ] familia;
* [ ] no duplicar misma invención como patentes distintas sin aclararlo.

Y en narrativa:

> “reivindica…”

No:

> “implementa exitosamente…”

---

# AC. Fuentes de datos y bibliometría

OpenAlex/Crossref/Google Patents sirven como **fuentes de datos**, no como fuentes del contenido científico de un paper.

Distinguir:

> metadata source

de:

> scientific source.

Citar correctamente el dataset/API si sus datos sustentan una figura.

---

# AD. DOI audit

Para todos los artículos con DOI:

$$
\boxed{
\text{DOI}\rightarrow\text{publisher metadata}
}
$$

Verificar automáticamente:

* author list;
* title;
* year;
* journal;
* volume;
* issue;
* pages/article number.

Si uno no coincide:

> FAIL.

No copiar DOI de Semantic Scholar sin validar.

---

# AE. URLs

APA 7 trata DOI y URL como enlaces. Ya no utiliza `DOI:` antes del identificador; se usa:

> `https://doi.org/...`

([Purdue OWL][3])

Revisar:

* [ ] HTTPS.
* [ ] sin trackers.
* [ ] sin `utm_source`.
* [ ] sin sesión.
* [ ] fuente estable.
* [ ] publisher > agregador.
* [ ] DOI > URL de journal cuando DOI existe.

---

# AF. Fechas de recuperación

APA 7 generalmente **no exige fecha de recuperación para contenido estable**; se reserva principalmente para recursos que pueden cambiar con el tiempo. ([Purdue OWL][4])

Por tanto:

No:

> “Consultado el…” para cada journal article.

Sí puede tener sentido para:

* páginas de producto;
* estándares “under publication”;
* wikis/dashboards actualizables;
* páginas web sin versión archivada.

---

# AG. Autores en APA 7 — lista de referencias

Este punto ya afecta tu tesis actual.

En referencias:

* hasta **20 autores** → escribirlos.
* **NO usar `et al.`** en una entrada ordinaria de hasta 20 autores.
* si >20 → primeros 19, …, autor final.

([Purdue OWL][3])

Por tanto entradas como:

> `Fukao, T., et al.`

son candidatas directas a corrección.

---

# AH. Autores en citas dentro del texto

APA 7:

### Un autor

> Pérez (2024)
> (Pérez, 2024)

### Dos autores

Narrativa:

> Pérez y Gómez (2024)

Parentética:

> (Pérez & Gómez, 2024)

### Tres o más

Desde la **primera cita**:

> Pérez et al. (2024)

> (Pérez et al., 2024)

salvo necesidad de desambiguación. ([Purdue OWL][5])

---

# AI. `et al.`

Reglas:

* `et` sin punto.
* `al.` con punto.
* no cursiva.
* siempre representa más de un autor omitido.

Correcto:

> Smith et al. (2025)

Incorrecto:

> Smith et. al
> Smith et al
> Smith *et al.*

---

# AJ. Autores institucionales

Primera aparición, si después usarás sigla:

> International Organization for Standardization (ISO, 2023)

Después:

> ISO (2023)

Parentética inicial:

> (International Organization for Standardization [ISO], 2023)

Después:

> (ISO, 2023)

No inventar siglas poco conocidas solo para ahorrar palabras.

---

# AK. Mismo autor, mismo año

Si existen:

> Smith (2025a)
> Smith (2025b)

las letras deben corresponder al orden de las entradas según APA.

El `.bib` debe producirlas automáticamente.

No asignarlas manualmente a ojo.

---

# AL. Autores con mismo apellido

Desambiguar con iniciales cuando APA lo exige.

Evitar que:

> J. Zhang
> Y. Zhang

se conviertan ambos simplemente en:

> Zhang (2024)

si genera ambigüedad.

---

# AM. Múltiples fuentes en una misma cita

Orden coherente con APA, normalmente alfabético por primer autor dentro del mismo paréntesis:

> (Ames et al., 2017; Choi et al., 2009; Sandholm, 2010)

No ordenarlas según “cuál me gusta más”.

---

# AN. Cita directa

Purdue resume la regla APA:

si se cita textualmente, se añade localizador/página. ([Purdue OWL][6])

En este TFM yo **minimizaría drásticamente las citas textuales**.

Robótica/ingeniería se beneficia más de:

> paráfrasis exacta + referencia.

Las citas literales son necesarias solo si:

* la formulación exacta importa;
* una norma define algo;
* una afirmación comercial específica debe preservarse.

---

# AO. Citas largas

APA usa cita en bloque para citas textuales largas (40 palabras o más).

Para este TFM:

> casi ninguna debería ser necesaria.

Un bloque de 100 palabras de otro paper dentro del marco teórico suele ser síntoma de que falta síntesis.

---

# AP. Paráfrasis

Parafrasear NO es:

> cambiar sinónimos manteniendo la misma estructura.

Debe:

1. comprender la fuente;
2. cerrar la fuente;
3. reconstruir la idea desde nuestro argumento;
4. citar.

Turnitin puede detectar proximidad incluso aunque cambies unas pocas palabras.

---

# AQ. Plagio conceptual

También existe cuando:

* tomamos una taxonomía;
* una idea;
* una estructura;
* un argumento;
* una figura;

y no atribuimos.

No basta con que las palabras sean nuestras.

VIU exige explícitamente evitar contenido ajeno sin referenciar y utiliza antiplagio. 

---

# AR. Figuras y tablas derivadas de literatura

VIU exige procedencia/fuente de las ilustraciones. 

Clasificar:

### 1. Completamente propia

> Fuente: elaboración propia.

### 2. Datos externos, visualización propia

> Fuente: elaboración propia a partir de datos de X (2025).

### 3. Adaptación conceptual

> Adaptado de X (2025).

### 4. Reproducción

> Reproducido de X…

Y revisar licencia/permiso cuando proceda.

Nunca escribir:

> “Elaboración propia”

si en realidad redibujamos casi exactamente una figura ajena.

---

# AS. Captions con referencias

* [ ] cita en caption/note si figura deriva de fuente;
* [ ] la fuente está en Referencias;
* [ ] no depender solo de una cita perdida 2 párrafos antes;
* [ ] copyright/licencia si es necesario.

---

# AT. Referencias metodológicas

VIU dice explícitamente que la bibliografía debe cubrir **tema de investigación y metodología**. 

Por tanto debemos citar también:

* bootstrap;
* McNemar;
* Wilcoxon si se justifica metodológicamente;
* Holm;
* quizá Friedman;
* simuladores/software especializado;
* métodos numéricos relevantes;
* algoritmo exacto utilizado.

No necesitas citar matemáticas elementales.

Pero sí las metodologías científicas que fundamentan decisiones importantes.

---

# AU. Software

APA 7 permite/recomienda referenciar software especializado; no hace falta citar lenguajes o software ofimático estándar. ([Purdue OWL][7])

Para tu tesis revisar:

* CoppeliaSim;
* MuJoCo si finalmente se usa;
* HiGHS;
* solver particular;
* software científico cuyo comportamiento sea metodológicamente importante.

No llenar referencias con:

* Python;
* Word;
* Git.

salvo exigencia metodológica específica.

---

# AV. Datasets

Si un dataset externo sustenta un resultado:

* autor/organización;
* año;
* título;
* versión;
* descriptor `[Data set]`;
* repositorio;
* DOI/URL.

Además, explicar exactamente qué parte se utilizó.

---

# AW. Preprints / arXiv

Formato conceptual APA:

> Autor(es). (Año). *Título* [Preprint]. arXiv. URL

Pero antes:

* [ ] buscar versión journal/conference.
* [ ] comprobar fecha.
* [ ] no presentar peer-review si no existe.
* [ ] si versión publicada existe, preferirla.

---

# AX. Artículos de revista — plantilla

APA 7 básica:

> Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Journal Title, volume*(issue), pages/article number. [https://doi.org/](https://doi.org/)...

Purdue confirma la estructura y que el DOI debe incluirse cuando existe. ([Purdue OWL][8])

Revisar:

* título del artículo en sentence case;
* journal y volumen en cursiva;
* issue entre paréntesis;
* DOI.

---

# AY. Libros

Forma básica APA:

> Author, A. A. (Year). *Title of book*. Publisher.

Ya no se incluye ciudad del editor. ([Purdue OWL][9])

---

# AZ. Capítulos de libro

Conceptualmente:

> Author, A. A. (Year). Title of chapter. In E. E. Editor (Ed.), *Title of book* (pp. xx–xx). Publisher.

No confundir autor del capítulo con editor.

---

# BA. Conference papers

Aquí debemos ser cuidadosos porque en robótica son muy importantes.

Determinar primero:

* ¿paper publicado en proceedings?
* ¿solo presentación?
* ¿extended abstract?
* ¿paper con DOI?

No usar una sola plantilla ciegamente.

Purdue señala que proceedings requieren adaptar el formato según cómo estén publicados. ([Purdue OWL][2])

Lo importante:

* autores;
* año;
* título;
* conference/proceedings;
* pages/article;
* publisher si aplica;
* DOI.

---

# BB. Tesis

Formato APA típico para tesis publicada:

> Author, A. A. (Year). *Title* [Master’s thesis/Doctoral dissertation, University]. Repository/URL.

Purdue ofrece precisamente este esquema. ([Purdue OWL][2])

---

# BC. Informes técnicos

> Organization/Author. (Year). *Title of report*. Organization. URL

Si autor y publisher son la misma organización, revisar regla APA para evitar duplicación innecesaria.

---

# BD. Webpage

Conceptualmente:

> Author/Organization. (Date). *Title of page*. Site. URL

Pero:

* si autor = site, no duplicar innecesariamente;
* usar fecha real;
* si no existe fecha, usar convención coherente `s. f.`/`n.d.` según localización adoptada;
* retrieval date solo si contenido cambia.

---

# BE. Fuente corporativa

Ejemplo conceptual:

> AGILOX. (2024). *Título de la página/caso*. URL

Pero narrativamente:

> “AGILOX informa…”

No:

> “Se ha demostrado…”

---

# BF. Normas técnicas

Para ISO:

> International Organization for Standardization. (Year). *Title of standard* (ISO Standard No. xxxx:year). URL

Auditar siempre contra la página oficial.

---

# BG. Patentes

No tratar como artículo.

Verificar:

* inventores;
* año;
* título;
* número;
* autoridad;
* URL.

Y distinguir:

> 申请/application
> publicación
> grant.

---

# BH. Estado de publicación

Etiquetar correctamente:

* Published.
* Early access.
* Accepted.
* In press.
* Preprint.
* Under publication.
* Draft standard.

No convertir:

> “under publication”

en:

> “norma publicada”.

---

# BI. Retractions y corrections

Para cada paper central:

* [ ] buscar retraction;
* [ ] expression of concern;
* [ ] correction/erratum;
* [ ] nueva versión.

Especialmente papers 2025–2026.

Una fuente retractada no debe sostener un claim sin explicar el problema.

---

# BJ. Predatory venue audit

Para fuentes desconocidas:

* publisher;
* peer-review;
* indexing;
* editorial board;
* DOI;
* venue history.

No excluir automáticamente venue nuevo.

Pero no usar un journal dudoso como pilar si existe literatura sólida.

---

# BK. Quality ≠ citation count

No elegir papers solo porque tienen muchas citas.

Para trabajos recientes:

$$
\text{calidad}
\neq
\text{Google Scholar citations}.
$$

Priorizar:

* proximidad al problema;
* rigor;
* evidencia;
* reproducibilidad;
* relevancia.

---

# BL. Evidence-type tagging

Yo etiquetaría internamente cada referencia:

* `THEORY`
* `ALGORITHM`
* `EXPERIMENTAL`
* `REVIEW`
* `STANDARD`
* `INDUSTRIAL`
* `PATENT`
* `DATA`
* `SOFTWARE`

Después comprobar:

> ¿estamos utilizando una fuente INDUSTRIAL como THEORY?

Si sí:

> problema.

---

# BM. Claim-type tagging

Igualmente cada cita debería sostener uno de:

* definición;
* existencia;
* optimalidad;
* convergencia;
* estabilidad;
* seguridad;
* rendimiento;
* complejidad;
* implementación;
* caso industrial;
* norma.

Eso permite detectar transferencias indebidas.

---

# BN. Literature-to-claim matrix

Crear:

| Claim | Source | Exact support | Source type | Direct/indirect | Strength | Page/section |
| ----- | ------ | ------------- | ----------- | --------------- | -------- | ------------ |

Por ejemplo:

> “ORCA proporciona semiplanos recíprocos”
> van den Berg et al.
> direct
> primary algorithm.

Pero:

> “ORCA garantiza seguridad de Cargo rígido”

quizá:

> **NO SUPPORT**.

---

# BO. Page/equation locator interno

APA no exige páginas para paráfrasis.

Pero para nuestra auditoría privada yo registraría:

* página;
* ecuación;
* theorem;
* sección;

de las fuentes centrales.

Así, si el jurado pregunta:

> “¿Dónde dice esto Ames?”

puedes responder.

---

# BP. Reference-to-text correspondence

VIU insiste en bibliografía completa, y otras guías VIU especifican correspondencia exacta entre citas y referencias. ([VIU Universidad Online][1])

Gate automático:

$$
C=\{\text{citation keys usados}\}
$$

$$
R=\{\text{references impresas}\}
$$

Exigir:

$$
\boxed{C=R}
$$

Operativamente, esa es la opción más segura.

Si una fuente fue “consultada” pero nunca influye materialmente en el texto, no tiene mucho valor engordar la bibliografía; si sí influyó, cítala en el lugar correspondiente. Así cumples tanto la guía específica del máster como la correspondencia exacta.

---

# BQ. Referencias huérfanas

Detectar:

$$
R-C.
$$

Cada entrada que nunca se cita:

* citar donde realmente se usa;
* o eliminar.

Nada de bibliografía decorativa.

---

# BR. Citas huérfanas

Detectar:

$$
C-R.
$$

Cualquier key sin referencia:

> P0.

---

# BS. Duplicados bibliográficos

Detectar:

* mismo DOI;
* mismo title;
* arXiv + final paper;
* variante abreviada de autor;
* conference + preprint idéntico.

Decidir cuál debe citarse.

No contar dos veces el mismo trabajo como dos precedentes independientes.

---

# BT. Normalización de nombres

Especial atención:

* apellidos compuestos;
* partículas `de`, `van`, `von`;
* nombres españoles;
* ORCID metadata;
* tildes;
* guiones.

No dejar:

> Barreiro-Gómez

en una entrada y:

> Barreiro Gómez

en otra si es el mismo autor.

---

# BU. Capitalización

APA:

Artículos/libros:

> sentence case.

Journal:

> Title Case según nombre oficial.

Acrónimos propios:

> conservar.

No usar Title Case estadounidense indiscriminadamente en títulos de papers en las entradas.

---

# BV. Cursivas

Normalmente:

* journal name → cursiva;
* volume → cursiva;
* book/report completo → cursiva;
* article/chapter → no cursiva;
* issue → no cursiva.

Auditar automáticamente el `.bbl`/PDF final.

---

# BW. Orden alfabético

VIU también lo recomienda explícitamente en sus guías. ([VIU Universidad Online][1])

Revisar:

* autores;
* organizaciones;
* misma autoría;
* mismo año;
* `a/b/c`.

No ordenar por orden de aparición.

---

# BX. Sangría francesa

APA:

$$
0.5\text{ inch}\approx1.27\text{ cm}
$$

en líneas posteriores de cada referencia. Purdue también lo especifica. ([Purdue OWL][10])

Verificar visualmente.

---

# BY. DOI vs URL

Si DOI existe:

$$
\boxed{\text{usar DOI}}
$$

normalmente no necesitas además URL de publisher.

No:

> DOI + URL + Google Scholar URL.

---

# BZ. URLs rotas

Automatizar HEAD/GET cuando sea razonable:

* 200/redirect válido;
* no 404;
* no login obligatorio si existe alternativa;
* DOI resuelve.

No asumir que porque aparece azul funciona.

---

# CA. Citas al final del párrafo

Buscar párrafos de literatura con una sola cita al final y muchas afirmaciones.

Pregunta:

> ¿Qué parte sostiene exactamente esa cita?

Mover referencias a las frases adecuadas.

---

# CB. “Cita flotante”

Mal:

> “…como se ha demostrado. (Smith, 2022)”

Corregir integración gramatical.

---

# CC. Citas dentro de ecuaciones/figuras

Evitar meter `(Smith, 2022)` dentro de una expresión matemática.

Citar en la frase introductoria:

> “Siguiendo a Smith (2022), se define…”

---

# CD. Citas dentro de títulos

Evitar headings como:

> “Control basado en Ames et al. (2017)”

Mejor:

> “Control mediante funciones de barrera”

y citar en el texto.

---

# CE. Demasiadas autocitas a un mismo paper

Si un párrafo completo discute un único trabajo, no es necesario citarlo al final de cada oración, siempre que no haya ambigüedad.

Pero la atribución debe seguir clara.

---

# CF. Citas de review como acceso a 20 papers

Un review puede sostener:

> “existen varias familias…”

Pero si después afirmamos características específicas de un método:

> volver al paper original.

---

# CG. Citation chains en claims de novedad

Para un claim:

> “ningún trabajo integra A+B+C”

no basta citar 5 papers.

Necesitas:

* protocolo de búsqueda;
* conjunto examinado;
* matriz de capabilities;
* formulación condicionada:

> “No se identificó…”

Nunca:

> “No existe…”

---

# CH. Gap statement audit

Para cada brecha:

* [ ] población/corpus.
* [ ] fecha de corte.
* [ ] dimensiones exactas.
* [ ] trabajos más cercanos.
* [ ] qué les falta.
* [ ] limitación del claim.

La brecha es una conclusión del review, no una impresión.

---

# CI. Revisión del corpus

El corpus debe documentar:

* bases;
* queries;
* fecha;
* filtros;
* deduplicación;
* etapas;
* lectura de full-text;
* inclusión/exclusión;
* snowballing.

Y distinguir:

$$
\text{descubiertos}
\neq
\text{screened}
\neq
\text{full text}
\neq
\text{canonical}
\neq
\text{close reading}.
$$

---

# CJ. Bias audit del review

Reconocer:

* disponibilidad OA;
* cobertura de bases;
* inglés/español;
* keywords;
* clasificación humana/automática;
* recency;
* patentes;
* corporate sources.

Eso aumenta credibilidad.

---

# CK. Uso de citas en Resultados

Los Resultados propios no necesitan una referencia para existir.

Pero la interpretación sí puede compararse:

> “A diferencia de X…”

Cuidado con llenar Resultados de literature review.

---

# CL. Discusión con literatura

Una buena discusión hace:

$$
\text{nuestro resultado}
\rightarrow
\text{estudio previo}
\rightarrow
\text{coincidencia/diferencia}
\rightarrow
\text{explicación}.
$$

No repetir estado del arte.

---

# CM. Fuente de comparadores

Cada baseline debe tener:

* referencia original;
* versión implementada;
* diferencias de nuestra adaptación.

Si es una baseline propia:

> declararlo.

---

# CN. Referencias en conclusiones

Idealmente muy pocas.

Conclusiones derivan de tus resultados.

Solo citar si comparas explícitamente con literatura.

Una conclusión repleta de 15 nuevas referencias indica que la discusión llegó demasiado tarde.

---

# CO. Main vs supplementary

* misma bibliografía o subset coherente;
* metadata idéntica;
* misma key;
* mismas fechas;
* no citar una versión arXiv en uno y journal en otro sin razón.

Idealmente una sola `.bib`.

---

# CP. Language consistency

Como tesis española:

* APA metadata originales no se traducen arbitrariamente;
* títulos de artículos se mantienen como publicados;
* nombre del journal original;
* “et al.” igual;
* DOI igual.

No traducir títulos científicos ingleses en la referencia salvo regla específica.

---

# CQ. Traducciones de conceptos

Si traduces en el texto:

> “control barrier function (CBF), función de barrera de control…”

citar fuente original.

Pero la referencia sigue con el título original del paper.

---

# CR. AI como buscador, no fuente

Ningún claim científico debería depender de:

> “ChatGPT dice que…”

Si una herramienta de IA encuentra una referencia:

1. abrir referencia;
2. comprobar metadata;
3. leer material relevante;
4. citar fuente real.

Una referencia inventada por un LLM es **P0 absoluto**.

---

# CS. Audit antifake-reference

Automatizar para cada entrada:

1. DOI resuelve.
2. Título coincide.
3. Primer autor coincide.
4. Año coincide.
5. Journal coincide.

Si sin DOI:

* buscar publisher/venue;
* ISBN si libro;
* arXiv ID;
* standard number;
* patent number.

Estado:

* `VERIFIED_PRIMARY`
* `VERIFIED_METADATA`
* `UNVERIFIED`
* `BROKEN`
* `DUPLICATE`

Nada `UNVERIFIED` en versión final.

---

# CT. Retraction audit

Para fuentes que sostienen contribuciones centrales:

* Crossref;
* publisher;
* Crossmark si existe;
* correcciones.

No hace falta hacerlo a todas las 150 páginas corporativas, pero sí a papers esenciales.

---

# CU. Audit de “author credibility”

No es juzgar autores por fama.

Es comprobar:

* ¿publican en el área?
* ¿es la fuente primaria?
* ¿hay conflicto comercial?
* ¿es una fuente académica o marketing?
* ¿el venue corresponde?

No usar autoridad personal como sustituto de evidencia.

---

# CV. Número de referencias

No existe un número mágico.

No perseguir:

> “necesito 100 referencias”.

La pregunta correcta:

> ¿Está representada adecuadamente la literatura necesaria para sostener cada parte de la tesis?

Una referencia relevante vale más que diez tangenciales.

---

# CW. Recency balance

Para cada familia:

$$
\boxed{\text{fundacional}+\text{reciente}}
$$

Ejemplo:

* Monderer & Shapley → potencial.
* Sandholm → population games.
* papers recientes → aplicaciones multi-robot.

No sustituir teoría clásica por un paper nuevo que simplemente la cita.

---

# CX. Literature saturation test

Para cada subproblema:

Preguntar:

> Si busco cinco papers más, ¿probablemente aparecerá una familia metodológica nueva que cambie mi brecha?

Si sí:

> review aún no saturado.

---

# CY. Claim coverage score

Para cada claim fuerte puntuar:

| Factor          | 0          | 1          | 2        |
| --------------- | ---------- | ---------- | -------- |
| fuente existe   | no         | dudosa     | sí       |
| fuente primaria | no         | secundaria | sí       |
| claim directo   | no         | parcial    | sí       |
| actualidad      | obsoleta   | aceptable  | adecuada |
| metadata        | incorrecta | parcial    | exacta   |
| APA             | incorrecto | menor      | correcto |

Máximo:

$$
12.
$$

Claims centrales:

$$
\boxed{12/12}
$$

Nada menos.

---

# CZ. Source quality score

Para cada paper fundamental:

* relevancia;
* proximidad;
* rigor;
* evidencia;
* recoverability;
* status publication.

No convertirlo en ranking político de papers; sirve como herramienta privada para decidir qué sostiene qué.

---

# DA. Citation placement gate

Una cita pasa si:

$$
\boxed{
\text{lector puede señalar exactamente qué proposición respalda}
}
$$

Si no:

> mover o dividir frase.

---

# DB. Reference metadata gate

Una referencia pasa si:

$$
\boxed{
\text{authors + year + title + venue + DOI/URL}
}
$$

han sido verificados contra fuente autoritativa.

---

# DC. APA gate

Pasa solo si:

* orden;
* autores;
* capitalización;
* cursiva;
* volumen;
* número;
* páginas;
* DOI;
* sangría;

están correctos.

---

# DD. Originality gate

Pasa solo si:

* todo contenido ajeno está atribuido;
* citas literales identificadas;
* paráfrasis suficientemente independientes;
* figuras adaptadas atribuidas;
* ideas/taxonomías atribuidas;
* no hay autoplagio relevante main/supp.

VIU es explícita sobre originalidad y antiplagio. 

---

# DE. Marco Teórico gate

Pasa solo si cada sección:

1. define;
2. compara;
3. critica;
4. identifica límite;
5. conecta con el TFM.

No basta resumir.

---

# DF. Estado del Arte gate

Pasa solo si podemos defender:

* búsqueda;
* actualidad;
* representatividad;
* closest prior;
* gap condicionado.

---

# DG. Citation-reference consistency gate

Automático:

$$
\boxed{C=R}
$$

más:

* cero duplicates;
* cero broken DOI;
* cero `et al.` indebidos en references;
* cero missing years;
* cero undefined bib keys.

---

# DH. Audit específico para TU TFM

Yo añadiría búsquedas automáticas de:

* `et al.` dentro de Referencias;
* `s.f.` / `n.d.` mezclados;
* `Retrieved from`;
* `Consultado el` usado indiscriminadamente;
* `DOI:` en vez de `https://doi.org/`;
* arXiv con versión posterior publicada;
* títulos incompletos;
* “Tian 2026” vs 2025;
* ISO 21423 metadata;
* URLs antiguas;
* corporate dates inferidas;
* self-reference Mayorga interna;
* references mencionadas solo en supplementary;
* citas del main no presentes en `.bib`;
* título/DOI mismatch.

---

# DI. Audit de los papers 2025–2026

Especialmente estricto porque son recientes y fáciles de “alucinar”:

* [ ] paper existe;
* [ ] publisher;
* [ ] DOI activo;
* [ ] online date;
* [ ] volume/issue;
* [ ] title exacto;
* [ ] published vs early access;
* [ ] final version vs preprint;
* [ ] claim leído en full text, no solo abstract.

---

# DJ. Audit de teoría matemática

Para cada fuente matemática:

> ¿Estamos citando el resultado correcto o simplemente un paper cercano?

Por ejemplo:

* potencial exacto → fuente correcta;
* VI/GNE → fuente correcta;
* primal-dual → fuente correcta;
* consensus switching → fuente correcta;
* Lyapunov/passivity → fuente correcta;
* MAPF completeness → fuente correcta.

No citar una aplicación reciente para una propiedad clásica si el original es más apropiado.

---

# DK. Audit de la literatura de robótica

Para cada trabajo de transporte cooperativo registrar:

* robots;
* tipo de locomoción;
* carga soportada/empujada/caged/grasped;
* selección de equipo;
* tamaño coalición;
* planificador;
* controlador;
* información;
* contacto;
* fallo;
* hardware/sim;
* guarantee.

Así evitamos agrupar trabajos físicamente incomparables.

---

# DL. Audit de evidencia de hardware

No decir:

> “experimental validation”

como sinónimo de industrial.

Registrar:

* simulation;
* physics simulation;
* lab hardware;
* industrial floor;
* real deployment.

Y citar exactamente.

---

# DM. Audit de “distributed”

Cada paper citado como “distributed”:

* ¿qué está distribuido?
* decisión;
* control;
* estimación;
* comunicación;
* computation?

No aceptar el label del abstract sin entender la arquitectura.

---

# DN. Audit del lenguaje comparativo

Evitar:

> “A supera B”

si:

* distintos escenarios;
* información distinta;
* métricas distintas.

La literatura no es un leaderboard.

Usar:

> “A aborda X bajo…”
> “B añade Y…”

---

# DO. Marco teórico y nuestras ecuaciones

En cada derivación propia:

* identificar qué viene de literatura;
* qué definición adaptamos;
* qué parte es nueva.

Idealmente:

$$
\boxed{
\text{conocido}
\rightarrow
\text{especialización}
\rightarrow
\text{resultado propio}
}
$$

Que el tribunal pueda distinguirlo.

---

# DP. “Contribution boundary”

Esta revisión debe impedir dos errores:

### Plagio intelectual

presentar resultado previo como propio.

### Falsa modestia

presentar resultado propio como mera aplicación si realmente derivamos algo nuevo.

Debemos delimitar exactamente ambas fronteras.

---

# DQ. APA list final — ruleset compacto

Como house style:

$$
\boxed{
\begin{aligned}
&\text{APA 7 obligatoria};\\
&\text{autor-fecha en texto};\\
&\text{3+ autores: et al. desde primera cita};\\
&\text{hasta 20 autores completos en referencias};\\
&\text{DOI en formato https://doi.org/...};\\
&\text{orden alfabético};\\
&\text{sangría francesa};\\
&\text{sentence case en títulos};\\
&\text{journal+volume en cursiva};\\
&\text{correspondencia exacta texto↔referencias};\\
&\text{localizador en cita textual};\\
&\text{fecha de recuperación solo cuando procede}.
\end{aligned}
}
$$

Purdue confirma estas reglas esenciales de APA 7. ([Purdue OWL][3])

---

# DR. Gestión con Zotero/BibLaTeX

VIU recomienda gestores como Zotero/Mendeley para mantener consistencia. 

Pero gestor ≠ garantía de calidad.

Revisar manualmente:

* metadata importada;
* capitalization;
* corporate authors;
* conference names;
* article numbers;
* DOI;
* arXiv.

Un `.bib` malo genera automáticamente una bibliografía consistentemente mala.

---

# DS. Biblioteca canónica

Mantener una sola fuente maestra:

```text
references.bib
```

Cada entrada con:

* DOI;
* URL;
* type;
* verified=true interno;
* notes privadas si se necesita.

Main y supplement consumen el mismo archivo.

---

# DT. Automated literature QA report

Yo pediría a Sonnet/Codex generar:

```text
LITERATURE_AUDIT.csv
```

con:

| key | authors | year | title | type | DOI | DOI resolves | metadata match | cited main | cited supp | APA issue | claim supported | status |
| --- | ------- | ---: | ----- | ---- | --- | ------------ | -------------- | ---------- | ---------- | --------- | --------------- | ------ |

Estados:

* PASS
* FIX_METADATA
* VERIFY_CLAIM
* DUPLICATE
* REPLACE_PREPRINT
* REMOVE
* MISSING_REFERENCE.

Esto queda en repo, **no en el PDF final**.

---

# DU. Claim-source audit file

Separadamente:

```text
CLAIM_SOURCE_MATRIX.csv
```

| claim | text location | source | exact support | locator | source class | strength |
| ----- | ------------- | ------ | ------------- | ------- | ------------ | -------- |

Es la auditoría que detectará las “citas falsas aunque el paper exista”.

---

# DV. Reviewer 1 test

Para cada referencia importante:

> “Si yo fuera el autor de este paper, ¿diría que mi trabajo está representado correctamente?”

Si no:

> corregir.

---

# DW. Reviewer 2 test

> “¿Puede el lector distinguir claramente qué paper realmente hizo hardware, qué hizo simulación y qué solo formuló?”

Si no:

> corregir.

---

# DX. Turnitin test

Para cada párrafo de review:

* [ ] no copiar estructura sintáctica del abstract;
* [ ] no paráfrasis mínima;
* [ ] no cadenas de frases de una misma fuente;
* [ ] atribución de ideas;
* [ ] usar síntesis de múltiples trabajos.

No se trata de “bajar Turnitin”.

Se trata de producir texto realmente propio.

---

# DY. Tribunal test

El jurado debe poder preguntar:

> “¿Cuál es el paper más parecido a lo suyo?”

y tú responder inmediatamente:

1. autor;
2. qué hace;
3. diferencia;
4. por qué la diferencia importa.

Si no puedes:

> estado del arte no está listo.

---

# DZ. Gate final de literatura

Yo no congelaría el TFM hasta tener:

$$
\boxed{
\begin{aligned}
&0\ \text{referencias inexistentes},\\
&0\ \text{DOI incorrectos},\\
&0\ \text{citas sin referencia},\\
&0\ \text{referencias huérfanas},\\
&0\ \text{`et al.' indebidos en bibliography},\\
&0\ \text{preprints cuando existe final sin justificación},\\
&0\ \text{claims centrales sostenidos por marketing},\\
&0\ \text{claims de inexistencia absoluta},\\
&0\ \text{figuras adaptadas sin atribución},\\
&0\ \text{ecuaciones importadas sin origen}.
\end{aligned}
}
$$

Y además:

* 100 % de los **closest prior works** leídos;
* 100 % de las referencias centrales verificadas contra publisher/DOI;
* literatura 2025–2026 actualizada;
* marco teórico con síntesis y crítica;
* every gap condicionado al corpus;
* APA 7 validado visualmente en el PDF final.

---

## La regla que pondría encima del escritorio

Para cada referencia:

$$
\boxed{
\text{EXISTE}
\land
\text{ES CORRECTA}
\land
\text{ES PERTINENTE}
\land
\text{SOSTIENE EL CLAIM}
\land
\text{ESTÁ BIEN CITADA}
}
$$

Si falla una sola condición, **la referencia no está aprobada**.

Y para cada sección del Marco Teórico:

$$
\boxed{
\text{DEFINIR}
\rightarrow
\text{COMPARAR}
\rightarrow
\text{CRITICAR}
\rightarrow
\text{IDENTIFICAR LÍMITE}
\rightarrow
\text{JUSTIFICAR DISEÑO}
}
$$

Eso es exactamente lo que convierte una bibliografía larga en un **marco teórico de nivel tesis**.

En tu caso, yo haría esta auditoría en **tres pasadas separadas**: primero `source truth` —¿las referencias existen y sus metadatos son correctos?—; después `claim truth` —¿realmente sostienen lo que decimos?—; y solo al final `APA/render` —¿está perfectamente formateado?—. Mezclar las tres al mismo tiempo hace que se escapen errores mucho más graves, como un DOI auténtico asociado a una afirmación que el paper nunca hizo.

[1]: https://www.universidadviu.com/sites/universidadviu.com/files/media_files/Gu%C3%ADa%20Did%C3%A1ctica%20TFM%20MCRI.pdf?utm_source=chatgpt.com "•"
[2]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_print_sources.html?utm_source=chatgpt.com "Reference List: Other Print Sources - Purdue OWL® - Purdue University"
[3]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/apa_changes_7th_edition.html?utm_source=chatgpt.com "Changes in the 7th Edition - Purdue OWL® - Purdue University"
[4]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html?nt=1&utm_source=chatgpt.com "Reference List: Electronic Sources - Purdue OWL® - Purdue University"
[5]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/in_text_citations_author_authors.html?utm_source=chatgpt.com "In-Text Citations: Author/Authors - Purdue OWL® - Purdue University"
[6]: https://owl.purdue.edu/owl/owl_en_espanol/estilo_APA_7/citas_en_texto_lo_basico.html?utm_source=chatgpt.com "Citas en el Texto: Lo Básico - Purdue OWL® - Purdue University"
[7]: https://owl.purdue.edu/owl/owl_en_espanol/estilo_APA_7/lista_de_referencias_apa_fuentes_electr%C3%B3nicas.html?utm_source=chatgpt.com "Lista de Referencias APA: Fuentes Electrónicas - Purdue OWL® - Purdue University"
[8]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html?utm_source=chatgpt.com "Reference List: Articles in Periodicals - Purdue OWL® - Purdue University"
[9]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_textual_sources.html?utm_source=chatgpt.com "Reference List: Textual Sources - Purdue OWL® - Purdue University"
[10]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_basic_rules.html?utm_source=chatgpt.com "Reference List: Basic Rules - Purdue OWL® - Purdue University"
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
Guía estratégica y checklist final — TFM VIU MROB 2025–26
0. Cómo leer esta guía

Usaremos tres etiquetas:

[VIU]: requisito respaldado por documentación oficial MROB/VIU.
[P0]: requisito científico o administrativo que bloquea una versión final.
[STRAT]: recomendación estratégica para maximizar calidad y defensa.
[VERIFICAR]: puede ser una regla VIU vigente, pero no aparece en los documentos MROB que tenemos y debe comprobarse en el Aula actual.
1. Cómo se evalúa realmente tu TFM

Para MROB, la estructura de evaluación que sí está documentada es:

$$ \boxed{ 30\% \text{ Director} + 70\% \text{ Tribunal} } $$

La guía docente establece que el Director evalúa el TFM con un peso del 30 % y que el Tribunal de Defensa representa el 70 %. El tribunal valora, entre otros aspectos, la calidad del informe y los resultados, la estructura/formato de la presentación, el dominio del contenido y la comunicación durante la defensa.

Checklist de evaluación
 [VIU/P0] Entender que la nota del director pesa 30 %.
 [VIU/P0] Entender que el tribunal pesa 70 %.
 [STRAT] No tratar la defensa como una formalidad.
 [STRAT] Preparar el manuscrito pensando también en qué podrá reconocer y defender oralmente el tribunal.
 [STRAT] Alinear explícitamente el TFM con los criterios de la rúbrica de evaluación del aula.
 [STRAT] Tener una matriz criterio de rúbrica → evidencia en la tesis → evidencia en la defensa.
2. Requisitos formales del documento

La plantilla oficial de MROB exige A4, Arial 12, texto justificado, interlineado 1.5 y márgenes establecidos por la plantilla. También fija la numeración de preliminares y cuerpo.

Checklist formal
 [VIU/P0] Utilizar la plantilla oficial VIU.
 [VIU/P0] Formato A4.
 [VIU/P0] Arial 12 pt.
 [VIU/P0] Texto justificado.
 [VIU/P0] Interlineado 1.5.
 [VIU/P0] Márgenes oficiales.
 [VIU/P0] Portada sin numeración.
 [VIU/P0] Preliminares con números romanos.
 [VIU/P0] Cuerpo con numeración arábiga.
 [VIU/P0] PDF como entrega definitiva.
3. Extensión obligatoria

La guía MROB establece:

$$ 50\le P_{\text{cuerpo}}\le80 $$

y:

$$ P_{\text{anexos}}\le20. $$

Además:

$$ \boxed{ \frac{\text{Resultados + Análisis + Validación}} {\text{cuerpo principal}} \ge 50\% } $$

Checklist
 [VIU/P0] Cuerpo entre 50 y 80 páginas.
 [VIU/P0] Anexos ≤20 páginas.
 [VIU/P0] Resultados/Análisis/Validación ≥50 % del cuerpo.
 [P0] No “resolver” el porcentaje con relleno.
 [P0] Las páginas añadidas a Resultados deben contener evidencia, análisis o validación real.
 [STRAT] Mover desarrollo histórico, auditorías internas, tablas completas y derivaciones largas al suplemento.
4. Resumen y Abstract

VIU exige un resumen de 200–300 palabras y 3–5 palabras clave.

Debe contener
 Importancia del problema.
 Problema concreto.
 Propósito del TFM.
 Enfoque metodológico.
 Principales resultados.
 Principal resultado negativo relevante.
 Conclusión principal.
 Limitación crítica.
 3–5 palabras clave.
 Abstract equivalente al Resumen, no una versión con claims distintos.
5. Estructura científica del TFM

La guía VIU espera un trabajo coherente, original y metodológicamente riguroso.

Para tu caso, la estructura intelectual debería leerse como:

$$ \text{problema} \rightarrow \text{brecha} \rightarrow \text{hipótesis} \rightarrow \text{método} \rightarrow \text{SP1} \rightarrow \text{SP2} \rightarrow \text{SP3} \rightarrow \text{integración} \rightarrow \text{conclusiones}. $$
Checklist de coherencia
 El título describe lo que realmente se hizo.
 La introducción conduce al problema.
 El problema conduce a RQ.
 Las RQ conducen a objetivos.
 Los objetivos conducen a hipótesis.
 Las hipótesis conducen a experimentos/teoremas.
 Los resultados contestan esas hipótesis.
 Las conclusiones responden literalmente a las RQ.
 No hay capítulos huérfanos.
 No hay experimentos importantes que no respondan a ninguna pregunta.
 No hay hipótesis declaradas que simplemente desaparezcan.
6. Director del TFM

El reglamento asigna al director la función de orientar, vigilar la consecución de objetivos e informar sobre la presentación y defensa.

Director-readiness checklist
 [VIU] Mantener comunicación con el director.
 [STRAT] Enviar una versión completa antes del depósito.
 [STRAT] Entregar una tabla:
comentario;
corrección;
página/sección;
estado.
 El título no presenta contradicción conceptual evidente.
 Los objetivos originales se reconciliaron con lo finalmente realizado.
 Las hipótesis tienen estado final.
 Los resultados negativos están explicados.
 Las limitaciones son explícitas.
 No hay cambios científicos mayores introducidos después de la última revisión sin documentarlos.
 El director podría explicar en una frase cuál es la contribución del trabajo.
7. Entregas y checkpoints reales de MROB

No existe en la documentación que tenemos una regla de “mínimo tres borradores”.

Lo documentado es:

Tarea 1

Fundamentación hasta Metodología.

Tarea 2

Predepósito: versión completa del TFM.

Tarea 3

Depósito final.

Checklist
 Tarea 1 realizada.
 Correcciones de Tarea 1 incorporadas.
 Predepósito enviado al director.
 Feedback de predepósito resuelto.
 Versión de depósito corresponde a una versión revisada y estable.
 No existe una bifurcación accidental entre “versión del tutor” y “versión depositada”.
8. Marco teórico y literatura

VIU pide que el Marco Teórico analice teorías, conceptos, antecedentes, enfoques y soluciones existentes, identifique limitaciones y justifique el estudio.

Checklist
 Fundamentos necesarios.
 Estado del arte reciente.
 Trabajos fundacionales.
 Closest prior works.
 Literatura adversarial.
 Papers recientes 2024–2026.
 No citation dumping.
 No “Autor A hizo X, Autor B hizo Y” sin síntesis.
 Cada subsección termina justificando una decisión del TFM.
 Diferenciar fundamentos de estado del arte.
 Diferenciar papers científicos de fuentes comerciales.
 Diferenciar preprints de artículos revisados.
 Diferenciar claim del fabricante de validación independiente.
9. Referencias y APA 7

APA 7 es obligatoria.

Audit obligatorio

Por cada referencia:

 Existe.
 Autores correctos.
 Año correcto.
 Título exacto.
 Venue correcto.
 DOI correcto.
 DOI resuelve.
 Versión final usada si existe.
 No retractada.
 Entrada APA correcta.
 Claim realmente respaldado.

Y además:

$$ C=\text{citas en texto}, \qquad R=\text{referencias}. $$

Exigir:

$$ \boxed{C=R} $$
 0 referencias huérfanas.
 0 citas sin entrada.
 0 DOI falsos.
 0 et al. indebidos en bibliografía.
 0 duplicados arXiv/journal sin motivo.
10. Originalidad

VIU exige que el trabajo sea personal, original e inédito y puede utilizar herramientas para verificar autoría y originalidad.

Originality gate
 0 texto ajeno no atribuido.
 0 figuras adaptadas sin fuente.
 0 ecuaciones importadas sin atribución cuando corresponde.
 0 paráfrasis demasiado próximas.
 0 referencias inventadas.
 0 taxonomías apropiadas sin citar.
 Historial del trabajo conservado.
 Código/datos disponibles para defender la autoría del trabajo.
 El estudiante puede explicar todo resultado central.
11. Declaración de uso de IA

Aquí hay que distinguir lo confirmado de lo probable.

Varias guías VIU actuales de otros títulos exigen una declaración específica de IA generativa, pero los documentos MROB cargados no la mencionan explícitamente.

Por tanto:

AI Declaration Gate
 [VERIFICAR] Buscar en Aula MROB 2025–26 una plantilla de “Declaración de uso de IA Generativa”.
 [VERIFICAR] Revisar anuncios recientes.
 [VERIFICAR] Consultar la tutoría final.
 [VERIFICAR] Preguntar al director si persiste duda.
 Si existe formulario, cumplimentarlo exactamente.
 Describir de forma honesta qué herramientas se utilizaron y para qué.
 Conservar trazabilidad de revisión humana.
 No atribuir a una IA autoría de resultados científicos.

No asumir automáticamente que el formulario de otro máster VIU es el de MROB.

12. Metodología
 Diseño de investigación declarado.
 Variables/estimandos definidos.
 Unidad experimental.
 Factores y niveles.
 Métodos.
 Baselines.
 Ablations.
 Oracles.
 Seeds.
 Métrica primaria.
 Métricas secundarias.
 Statistical plan.
 Failure criteria.
 Timeout.
 Preespecificación.
 Justificación de por qué esa metodología responde a los objetivos.
13. Resultados

VIU considera Resultados, Análisis y Validación el eje central del TFM.

Checklist
 Cada resultado responde un OE/H/RQ.
 \(n\) visible.
 IC visibles.
 Efectos, no solo p-values.
 Comparadores honestos.
 Resultados negativos incluidos.
 Timeouts incluidos.
 No cherry-picking.
 Diferenciar piloto y confirmatorio.
 Diferenciar simulación y hardware.
 Interpretación crítica.
 Limitaciones.
14. Matemática

Por cada teorema:

 Dominio.
 Supuestos.
 Enunciado.
 Demostración.
 Dependencias.
 Contraejemplo cuando corresponda.
 No circularidad.
 Implementación compatible.

Auditar especialmente:

$$ \text{Nash}\neq\text{óptimo} $$ $$ \text{convergencia}\neq\text{optimalidad} $$ $$ \text{seguridad}\neq\text{progreso} $$ $$ \text{terminación}\neq\text{entrega} $$ $$ \text{no-Zeno}\neq\text{dwell time} $$ $$ \text{rama convexa}\neq\text{sistema híbrido global}. $$
15. Robótica
 Modelo cinemático.
 Modelo dinámico.
 Ruedas.
 No-holonomía.
 Contactos.
 Wrench.
 Saturación.
 Fricción.
 Slip.
 Tracción.
 Sensores.
 Pose exacta/estimada.
 Límites reales.
 Qué es idealización.
 Qué es simulación.
 Qué puede transferirse a hardware.
16. Figuras y tablas
 Vectoriales cuando corresponde.
 Cero clipping.
 Cero overlap.
 Fonts legibles.
 Paleta consistente.
 Colorblind-safe.
 Grayscale test.
 Ejes/unidades.
 \(n\).
 IC/error bars.
 Caption autónoma.
 Fuente.
 Inspección visual dentro del PDF.
17. AI-writing / apariencia de pipeline

Eliminar de la memoria final cuando no sean necesarios:

claim;
gate;
claim-ID;
PASS/FAIL/LIMITED;
hashes;
paths internos;
complete=true;
“formulación previa”;
“humo acotado”;
lenguaje de agente/software.

La trazabilidad puede vivir en el repositorio.

La memoria debe parecer una sola obra científica.

18. Depósito — documentos que sí tenemos confirmados para MROB

Según la guía y tutoría MROB:

Estudiante
TFM.
Certificado de notas / expediente académico.
Anexo IV.
Director
Anexo III firmado.

También se realiza la prueba antiplagio.

Checklist de depósito
 [VIU] PDF definitivo.
 [VIU] Anexo IV.
 [VIU] Certificado de notas / expediente.
 [VIU] Confirmar que el Director haya enviado Anexo III.
 [VIU] Prueba antiplagio.
 [VERIFICAR] Declaración IA si aplica.
 PDF abre correctamente.
 Título correcto.
 Director correcto.
 Fecha correcta.
 Sin comentarios internos.
 Sin marcas draft.
 Links revisados.
 Copia local de la versión depositada.
 Commit/hash interno congelado.
 Comprobante de subida.
19. Defensa

La defensa de MROB es mediante videoconferencia y en sesión pública.

El reglamento general establece que, tras la exposición, el tribunal puede hacer observaciones y preguntas sobre contenido y presentación.

Narrative checklist
 Problema.
 Brecha.
 Objetivos.
 Arquitectura.
 Método.
 Principales resultados.
 Resultado negativo.
 Limitaciones.
 Conclusión.
 Aporte.
No fijar aún como norma
 [VERIFICAR] duración exacta.
 [VERIFICAR] duración preguntas.
 [VERIFICAR] plazo para enviar slides.

La Tutoría Final Colectiva está destinada específicamente a “Indicaciones Defensa TFM”; ahí debe verificarse esto.

20. Resiliencia técnica de defensa

Esto no es normativa, pero sí sensato.

 Ethernet si posible.
 Wi-Fi backup.
 Hotspot móvil.
 Cargador.
 Cámara probada.
 Micrófono probado.
 Slides locales.
 Backup PDF.
 Vídeos fuera de PowerPoint además de incrustados.
 Demo pregrabada.
 Copia cloud.
 Copia USB/local.
21. Domain mastery

Dado que el tribunal valora explícitamente el dominio del contenido, este gate es importante.

Debes poder explicar sin notas:

 Cada ecuación central.
 Cada hipótesis.
 Cada baseline.
 Cada método estadístico.
 Cada resultado inesperado.
 Cada limitación.
 Closest prior work.
 Por qué usaste juegos.
 Por qué no basta MILP/DMPC.
 Qué significa “distribuido”.
 Qué validó Coppelia.
 Qué falta para hardware.
22. Preguntas de tribunal

Preparar respuestas para:

¿Cuál es la contribución central?
¿Qué tiene de nuevo?
¿Por qué teoría de juegos?
¿Qué es realmente distribuido?
¿Cuál es la diferencia con un centralizador?
¿Qué ocurre con \(N\) grande?
¿Por qué H3 falló?
¿Qué demuestra H5b?
¿Por qué capacidad no implica wrench?
¿Dónde está la fricción?
¿Qué validó Coppelia?
¿Por qué no hardware?
¿Qué theorem es realmente suyo?
¿Cuál es el paper más parecido?
¿Dónde no usaría este método?
23. Matrícula de Honor

Esto sí está reglado.

El tribunal puede proponer MH mediante informe motivado, pero la decisión corresponde a la Comisión de TFT. Se requiere calificación ≥9 y existe el límite general del 5 % de estudiantes matriculados, salvo la excepción para grupos de menos de 20.

MH checklist

Para que exista una razón real de propuesta:

 Contribución identificable en 30–60 s.
 Al menos un resultado memorable.
 Profundidad teórica.
 Validación experimental suficiente.
 Resultados negativos tratados científicamente.
 Literatura adversarial.
 Reproducibilidad.
 Figuras profesionales.
 Documento sin errores visibles.
 Defensa técnicamente sólida.
 Capacidad para responder preguntas difíciles.
 Claridad sobre límites.
 Distinción exacta entre trabajo propio y literatura.

Pregunta de control:

¿Qué podría escribir el tribunal en un informe motivado para proponer este TFM a Matrícula de Honor?

La respuesta debe ser concreta.

24. Readiness final

No depositaría hasta obtener:

VIU format ................ PASS
Body pages 50–80 .......... PASS
Annexes <=20 .............. PASS
Results >=50% ............. PASS
Abstract 200–300 .......... PASS
Keywords 3–5 .............. PASS
APA 7 ..................... PASS

Scientific P0 ............. 0
Editorial P0 .............. 0
Math P0 ................... 0
Bibliographic P0 .......... 0
Visual P0 ................. 0

Undefined refs ............ 0
Duplicate labels .......... 0
Broken DOI ................ 0
Unverified central refs ... 0
Stale numbers ............. 0

Y humanamente:

 Director-ready.
 Tribunal-ready.
 Turnitin/originality-ready.
 Defense-ready.
 MH-candidate-ready.
Qué cambié respecto a DeepSeek

Conservé sus mejores ideas:

estrategia alrededor de la evaluación;
importancia del director;
importancia de la defensa;
checklist administrativo;
preparación técnica;
rúbrica;
Matrícula de Honor;
comunicación y dominio.

Pero corregí:

30/70 como reparto real MROB;
eliminé “documento 40–70 / defensa 30–40”;
eliminé la falsa obligación de 3 borradores;
corregí Anexo III/IV para MROB;
no doy por obligatorio todavía el formulario de IA;
no invento 20 min / 15 min;
no invento “slides 2 días antes”;
incorporé los requisitos MROB que DeepSeek omitió:
50–80 páginas;
≤20 anexos;
≥50 % Resultados/Análisis/Validación;
APA 7;
Resumen 200–300;
3–5 keywords.

Esta versión sí la usaría como guía canónica de proceso y evaluación para el cierre del TFM.


La detección de IA es un desafío en constante evolución, especialmente con actualizaciones como la de Turnitin en agosto de 2026. He investigado a fondo para ofrecerte una guía actualizada que combine métodos manuales, ajustes técnicos y herramientas de código abierto para reducir al mínimo la detección, siempre con un enfoque de integridad académica.

### 🔍 Entendiendo el Detector de Turnitin (Actualización 2026)

Turnitin **reentrenó su modelo de detección de IA en inglés el 18 de agosto de 2026**, lo que ha invalidado muchas técnicas que funcionaban antes. Los trucos antiguos como el simple intercambio de sinónimos, añadir palabras de relleno o usar parafraseadores gratuitos **ahora fallan más de lo que funcionan**.

Lo que **sí sigue funcionando** en septiembre de 2026 se basa en tres pilares:
1.  **Reescritura estructural a nivel de párrafo**: Reorganizar el flujo de la argumentación, no solo cambiar palabras.
2.  **Variación en la longitud de las frases**: Mezclar frases muy cortas con otras muy largas.
3.  **Humanización que preserva la voz**: Mantener tu estilo personal mientras se rompen los patrones estadísticos de la IA.

### 🛠️ Métodos Manuales y Técnicos para Reducir la Detección

Aquí tienes una guía paso a paso con las técnicas más efectivas para aplicar manualmente a tu texto.

#### **1. Rompe la Estructura Uniforme (El Método Más Eficaz)**

Los detectores buscan patrones predecibles. La clave es la **"burstiness"** (irregularidad) y la **"perplejidad"** (imprevisibilidad).

*   **Varía la longitud de las frases drásticamente**: Alterna frases de 3-5 palabras con otras de 30 o 40. Evita tener tres frases consecutivas de longitud similar.
    *   *Ejemplo AI*: "La robótica móvil es un campo interdisciplinario. Requiere conocimientos de mecánica, electrónica y programación. Su aplicación es cada vez más común en la industria."
    *   *Ejemplo Humanizado*: "La robótica móvil es un campo interdisciplinario. Sin embargo, su implementación exitosa, que depende de una compleja integración de mecánica, electrónica, control y programación avanzada, sigue siendo un desafío monumental para los ingenieros. Y su aplicación en la industria no deja de crecer."
*   **Rompe el patrón de párrafo "tópico → 3 apoyos → transición"**: La IA tiende a seguir esta estructura de forma casi invariable. Introduce párrafos que comiencen con una pregunta, una cita, un dato sorprendente o una anécdota.
*   **Introduce "ruido" sintáctico**: Usa oraciones subordinadas, incisos, paréntesis, guiones largos (—) y puntos y coma (;) de forma natural. La IA tiende a una sintaxis más plana.

#### **2. Ajusta el Vocabulario y los Conectores**

La IA abusa de ciertos términos y estructuras repetitivas.

*   **Elimina la "jerga de IA"**: Los detectores tienen listas de palabras que son señales de alerta. **Evita o usa con extrema moderación** términos como: *delve, leverage, tapestry, nuanced, foster, robust, pivotal, transformative, landscape, realm, underscore, harness, facilitate, navigate, crucial, paramount, meticulous, seamless*.
*   **Varía los conectores lógicos**: No uses siempre "además", "por lo tanto", "sin embargo". Alterna con: "aun así", "no obstante", "por el contrario", "en consecuencia", "de ahí que", "así pues", "en definitiva".
*   **Usa un lenguaje más coloquial y directo (con moderación académica)**: La IA tiende a un registro demasiado formal y neutral. Introducir alguna expresión más natural, una pregunta retórica o una opinión matizada puede ayudar.
*   **Cuidado con la "voz pasiva" excesiva**: La IA a menudo la usa para sonar objetiva. En español, la pasiva refleja ("se observa que...") es más natural, pero no abuses de ella.

#### **3. Inyecta "Humanidad" con Elementos Personales**

*   **Incluye anécdotas o ejemplos concretos**: La IA generaliza. Tú puedes particularizar. "En mi experiencia al implementar el algoritmo en el simulador Gazebo, me encontré con que..."
*   **Expresa opiniones y matices**: "Si bien los resultados son prometedores, personalmente considero que la metodología presenta una limitación crucial que no debe pasarse por alto."
*   **Referencias a tu propio proceso**: "Durante el desarrollo de este TFM, una decisión de diseño clave fue la de priorizar la eficiencia computacional sobre la precisión absoluta, debido a las restricciones de hardware."

### 📚 Lista de Palabras y Frases a Evitar (o Usar con Cautela)

Los detectores buscan estas "señales" de IA. **No se trata de prohibirlas, sino de no abusar de ellas y, sobre todo, de no usarlas en patrones repetitivos.**

| Categoría | Palabras y Frases a Evitar / Moderar |
| :--- | :--- |
| **Verbos de "IA"** | *Delve into, leverage, harness, underscore, facilitate, navigate, foster, embody, exemplify, encompass, illuminate, elucidate.* |
| **Adjetivos "inflados"** | *Pivotal, crucial, paramount, robust, nuanced, transformative, meticulous, seamless, comprehensive, multifaceted, intricate, profound, compelling.* |
| **Sustantivos "abstractos"** | *Tapestry, landscape, realm, paradigm, synergy, nexus, interplay, framework (en exceso), implication.* |
| **Conectores "fórmula"** | *Moreover, furthermore, in conclusion, additionally, consequently, notably, importantly, it is worth noting that, it is important to note that.* |
| **Estructuras "cliché"** | *"In today's fast-paced world...", "In the realm of...", "A testament to...", "Shed light on...", "Pave the way for..."* |
| **Frases de "relleno"** | *"It goes without saying that...", "Needless to say...", "In order to..."* |

### 💻 Repositorios de GitHub y Herramientas de Código Abierto (2026)

Existen varias herramientas de código abierto que aplican estas técnicas de forma automatizada. Úsalas como **apoyo a tu propia reescritura**, no como sustituto.

| Repositorio / Herramienta | Enfoque Principal y Técnica | Enlace |
| :--- | :--- | :--- |
| **text-humanizer** | **Cadena de traducción multilingüe**. Pasa el texto por un LLM, luego lo traduce al turco (y opcionalmente al japonés) y finalmente lo reconstruye al español. Esto introduce variaciones estructurales profundas. | [https://github.com/korcarc/text-humanizer](https://github.com/korcarc/text-humanizer) |
| **humanize-text** | **Pipeline estándar de 5 pasos**. Combina reescritura con LLM (DeepSeek) a alta temperatura y múltiples saltos de traducción (chino → japonés → finlandés → inglés) para romper las huellas estadísticas de la IA. | [https://github.com/the-coding-freak/humanize-text](https://github.com/the-coding-freak/humanize-text) |
| **unmask-ai** | **Pipeline de 3 pasadas con Claude Sonnet 4**. Se enfoca en inyectar **perplejidad** (elecciones de palabras inesperadas) y **burstiness** (variación drástica de longitud de frases). También elimina activamente 30+ palabras de vocabulario de IA. | [https://github.com/imsv1301/unmask-ai](https://github.com/imsv1301/unmask-ai) |
| **StealthHumanizer** | **Reescritura multipaso y consciente del estilo**. Utiliza diferentes modelos (BART para textos cortos, Gemma para largos) y ofrece 4 niveles de reescritura y 6 estilos de escritura para preservar la voz del autor. | [https://github.com/rudra496/StealthHumanizer](https://github.com/rudra496/StealthHumanizer) |
| **texthumanizer** | **Humanizador offline (PyPI)**. Usa un modelo T5 local para reescribir texto preservando citas, abreviaturas y terminología técnica. Ideal para documentos `.docx` con referencias. | [https://pypi.org/project/texthumanizer/](https://pypi.org/project/texthumanizer/) |
