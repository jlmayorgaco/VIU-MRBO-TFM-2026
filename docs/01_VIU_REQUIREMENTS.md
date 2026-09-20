# 01 — Requisitos VIU aplicables

## 1. Naturaleza académica

El TFM debe ser personal, original e inédito y demostrar la aplicación de competencias del máster. La memoria puede encuadrarse como trabajo de investigación teórico/experimental o estudio técnico con innovación en robótica y automatización.

## 2. Carga y extensión

- Asignatura: 6 ECTS.
- Dedicación indicada: 25 horas por ECTS; referencia total de 150 horas.
- Cuerpo principal: 50–80 páginas.
- Anexos: máximo 20 páginas.
- Borradores: Word.
- Versión definitiva: PDF.

## 3. Formato

- Plantilla oficial obligatoria.
- A4.
- Arial 12.
- Texto justificado.
- Interlineado 1,5.
- Márgenes: superior/inferior 2,5 cm; izquierdo/derecho 3 cm.
- APA 7 para citas y referencias.
- Ecuaciones, figuras y tablas numeradas, citadas en el texto y con fuente.

No modificar estilos predefinidos de la plantilla oficial.

## 4. Estructura obligatoria de nivel superior

1. Introducción.
2. Objetivos.
3. Hipótesis de partida.
4. Metodología.
5. Marco teórico y estado del arte.
6. Resultados y análisis.
7. Conclusiones y recomendaciones.
8. Referencias bibliográficas.
9. Anexos, cuando proceda.

Preliminares: portada, resumen de 200–300 palabras, 3–5 palabras clave, índice de contenido, listado de figuras, índice de tablas y lista de símbolos/acrónimos cuando aplique.

## 5. Requisito crítico de distribución

Al menos el 50 % del cuerpo principal debe dedicarse a resultados, análisis y validación. Por ello, SP1–SP3 se desarrollan principalmente en el capítulo 6 y deben incluir evidencia, no solo explicación del método.

## 6. Presupuesto recomendado de páginas

Para un cuerpo objetivo de 66–74 páginas:

| Capítulo | Páginas objetivo | Función |
|---|---:|---|
| 1. Introducción | 5–6 | Contexto, problema, brecha, relevancia y mapa del documento |
| 2. Objetivos | 2 | Objetivo general y objetivos específicos medibles |
| 3. Hipótesis | 2 | Hipótesis contrastables y criterios de refutación |
| 4. Metodología | 9 | Metodología común, modelo, protocolo, métricas, estadística y reproducibilidad |
| 5. Marco teórico/SOTA | 11–13 | Fundamentos y comparación crítica de literatura |
| 6. Resultados y análisis | 34–39 | Formulación propuesta, pruebas, simulaciones, comparaciones y discusión |
| 7. Conclusiones | 4–5 | Respuesta a objetivos/hipótesis, limitaciones y recomendaciones |
| **Total** | **67–76** | Dentro del rango VIU y con ≥50 % en capítulo 6 |

Los tres subproblemas no deben convertirse en artículos independientes ni repetir la formulación común. Su profundidad será desigual y proporcional a la contribución y a la evidencia disponible.

## 7. Microestructura recomendada para cada bloque de resultados

No repetir tres miniartículos completos. Usar una formulación común y, para cada SP:

1. pregunta local y cambios respecto al caso anterior;
2. supuestos y formulación incremental;
3. método propuesto;
4. baseline y protocolo;
5. resultado teórico o nivel de garantía;
6. resultados cuantitativos;
7. análisis, limitaciones y transición al siguiente SP.

## 8. Fuentes institucionales usadas para esta síntesis

- `Instrucciones_TFM_MU Robotica F (2).pdf`.
- `Plantilla memoria TFM_ MROB (1).docx`.
- `P11_02_F02a Guia Docente_12MROB_V02.pdf`.
- `Texto Consolidado_Reglamento sobre Trabajo Fin de Título_1 (1) (2).pdf`.
- `Anexo+I+Solicitud+TFM+-MROB_AGV.pdf`.

## 9. Restricción editorial del autor: figuras TikZ inamovibles

Las cinco figuras siguientes forman parte obligatoria de toda versión final de
la memoria, con independencia del presupuesto de páginas:

1. escenario de almacén, asignación distribuida y formación de coaliciones
   (`fig:problema`);
2. geometría y entradas del robot diferencial/uniciclo (`fig:robot`);
3. retratos cualitativos sobre el símplex de las dinámicas replicadora, mejor
   respuesta, logit y Smith (`fig:tf-population-simplex`);
4. cronología y cobertura del corpus bibliográfico
   (`fig:tf-literature-timeline`);
5. mapa metodológico distribuido--centralizado y
   white-box--data-driven (`fig:tf-methodological-map`).

No pueden eliminarse, comentarse, encerrarse en `\iffalse`, sustituirse por una
captura rasterizada ni excluirse de la compilación. Si fuera necesario reducir
la memoria, se compactará primero la prosa, se ajustará el tamaño dentro de los
límites de legibilidad o se reubicará la figura. Su fuente seguirá siendo TikZ,
la figura permanecerá citada y numerada, y conservará la indicación de
elaboración propia. `thesis/config/protected-tikz-figures.json` mantiene el
registro verificable y la compilación debe fallar si alguna deja de estar activa.
Las solicitudes posteriores de recortar, reducir, cambiar o aclarar el documento
no revocan esta protección: estas figuras solo pueden mejorarse, nunca retirarse.
