# Revisión académica exigente de la tesis

**Fecha:** 2026-07-18  
**Objeto:** árbol de trabajo y `thesis/build/main.pdf` vigentes  
**Modo:** revisión completa, panel independiente, Devil's Advocate, auditoría editorial y detección conservadora de patrones de escritura artificial  
**Decisión:** **revisión mayor; la memoria no está todavía lista para depósito**

## 1. Dictamen ejecutivo

La tesis tiene una base científica sólida y defendible. Destacan la separación entre capas, la prudencia al formular garantías, la conservación de resultados negativos, el diseño pareado de los experimentos y una trazabilidad superior a la habitual en un TFM. No se recomienda rechazo ni rehacer el trabajo desde cero.

La versión actual tiene, sin embargo, tres bloqueos de predepósito:

1. El cuerpo principal ocupa 95 páginas y excede en 15 el máximo VIU de 80.
2. La misión Cargo no ejecuta el mismo mecanismo nuclear desarrollado en SP2, SP3 y SP6. Su 359/360 valida una composición híbrida simplificada, no el juego distribuido extremo a extremo.
3. OE5 se define como integración funcional, pero las conclusiones lo sustituyen por trazabilidad/reproducibilidad. Esta contradicción rompe la cadena objetivos--resultados--conclusiones.

También deben tratarse la reproducibilidad parcial de SP2--SP4, la atribución causal insuficiente de las ablaciones Cargo, la diferencia entre el título distribuido y la arquitectura realmente híbrida, y los avisos tipográficos del PDF.

La ruta más segura para el depósito no es añadir otra campaña grande. Es **reformular con precisión la contribución como arquitectura de contratos y juegos locales por capas**, presentar Cargo como demostrador híbrido de compatibilidad funcional, corregir objetivos y conclusiones, y comprimir la memoria sin eliminar evidencia nuclear. Integrar realmente SP2/SP3/SP6 en Cargo sería una ruta científicamente más ambiciosa, pero implica reimplementar y repetir la campaña.

## 2. Instantánea verificada

| Control | Resultado | Estado |
|---|---:|---|
| PDF total | 135 páginas | Informativo |
| Cuerpo principal | 95 páginas | **No cumple 50--80** |
| Resultados y análisis | 69/95 páginas, 72,6 % | Cumple el mínimo del 50 % |
| Anexos | 19 páginas | Cumple el máximo de 20 |
| Pruebas | 75 superadas | Cumple |
| Referencias/citas indefinidas | 0 | Cumple |
| Claves citadas | 76; todas en `.bib` y ledger | Cumple trazabilidad interna |
| Estado de fuentes citadas | 73 verificadas, 1 preprint verificado y 2 parciales de uso comercial acotado | Aceptable |
| Log de compilación | 29 avisos U+0016, 3 de fuente, 1 caja desbordada y 78 subllenas | Debe limpiarse |

La versión anterior documentada en el quinto dictamen de `docs/11_FULL_MANUSCRIPT_REVIEW.md` tenía cuerpo de 80 páginas y PDF de 117. La versión actual regresó a 95 y 135 tras ampliar contenido y figuras. El incumplimiento de extensión es, por tanto, una regresión verificable, no una interpretación nueva del reglamento.

## 3. Fortalezas que deben preservarse

### 3.1 Rigor conceptual

La memoria distingue correctamente equilibrio de Nash, optimalidad social, factibilidad mecánica, seguridad, seguimiento y ejecución digital. Las pruebas locales se acotan a sus supuestos y no se extrapolan de forma automática al sistema híbrido.

### 3.2 Evidencia y estadística

La unidad experimental es el mundo o bloque escenario--semilla. Los robots y las muestras temporales no se cuentan como réplicas independientes. Se conservan colisiones, bloqueos y *timeouts* en los denominadores; se usan comparaciones pareadas, intervalos y corrección de multiplicidad en las campañas principales. Cargo y SP8 corrigen la pseudorreplicación agrupando por instancia.

### 3.3 Honestidad epistemológica

Se conservan H3 no sustentada, H5b refutada, los bloqueos de SP5, la pérdida de calidad de SP8 y los ceros de Industrial 2. La conclusión reconoce que 359/360 no estima una probabilidad industrial y que no existe Lyapunov común para el sistema híbrido.

### 3.4 Resultados defendibles

Sobreviven, con sus supuestos:

- los resultados formales locales de SP0--SP4 y SP6--SP8;
- la integrabilidad marginal de SP2 en el asignador ensayado;
- la reducción de falsos positivos de la guardia planar de SP3;
- la estabilidad local de SP4 con contacto fijo y wrench exacto;
- la caracterización de recuperación estratégica de SP6;
- la exclusión lógica de SP7 y el límite de observabilidad de SP8;
- el hecho empírico de que Cargo completó 359/360 misiones en su planta planar reducida y compuso varias funciones en un simulador.

## 4. Revisiones obligatorias

### B1. Reducir el cuerpo en al menos 15 páginas

**Evidencia:** `docs/01_VIU_REQUIREMENTS.md` fija 50--80 páginas; el cuerpo actual tiene 95. El anexo ya ocupa 19/20, por lo que trasladar contenido no basta.

**Corrección recomendada:** recuperar la jerarquía científica y comprimir, no recortar de forma uniforme. Priorizar:

1. condensar las tablas panorámicas repetidas por SP;
2. retirar duplicación exacta entre tabla, figura y paráfrasis numérica;
3. reducir SP0--SP2 respecto a SP3--SP6;
4. eliminar `\clearpage` no obligatorio y páginas parcialmente vacías;
5. dejar diagnósticos secundarios y listados de artefactos en el repositorio;
6. conservar en el cuerpo una figura/tabla por hipótesis y las fronteras negativas esenciales.

**Criterio de cierre:** referencias comienzan después de un cuerpo de 80 páginas o menos; anexos permanecen en 20 o menos; resultados siguen ocupando al menos la mitad.

### B2. Corregir la contradicción de OE5

`02-objectives.tex:48` define OE5 como integrar reclutamiento, cierre, acoplamiento, transporte, seguridad y reemplazo. `07-conclusions.tex:18` afirma que OE5 conserva trazabilidad y lo evalúa como reproducibilidad. Es un objetivo diferente.

**Corrección:** evaluar OE5 como integración funcional y declarar exactamente qué funciones se integraron y qué mecanismos SP fueron sustituidos. Mover la reproducibilidad a un criterio metodológico independiente. Reevaluar también OE2, RQ2 y RQ5 como parciales donde corresponda.

**Criterio de cierre:** cada OE y cada RQ tiene una respuesta individual que usa el mismo enunciado de Objetivos y distingue soportada, parcial, no sustentada o refutada.

### B3. Alinear Cargo con la contribución nuclear

Cargo usa líder temporal y registro global (`cargo-e2e.tex:11`), ranking empírico, criterio agregado sin QP geométrico (`cargo-e2e.tex:53`) y una recuperación simplificada. La propia sección documenta las diferencias.

El 359/360 acredita **compatibilidad funcional del ejecutor híbrido implementado**. No acredita que el payoff de SP2, la guardia QP de SP3 o el juego de SP6 hayan sobrevivido juntos hasta la acción ejecutada.

Hay dos rutas válidas:

- **Ruta científica:** incorporar en Cargo los mecanismos reales de SP2/SP3/SP6, repetir campaña y ablaciones, y auditar la equivalencia ecuación--código.
- **Ruta editorial recomendada para el depósito:** conservar la campaña, denominarla demostrador híbrido de compatibilidad, retirar cualquier inferencia de validación extremo a extremo del juego nuclear y rebajar HP/OE2/OE5 al alcance realmente observado.

**Criterio de cierre:** una tabla mapea cada ecuación o algoritmo reivindicado al código ejecutado; si hay sustitución, se etiqueta como proxy y no respalda directamente la afirmación formal original.

### B4. Explicar qué es realmente distribuido

El título oficial contiene «coordinación distribuida local», mientras la arquitectura usa cierres globales o por carga, QP, líder, registro y pose/geometría globales. La memoria lo reconoce en `index.tex:89`, pero la identidad de la contribución sigue ambigua.

**Corrección:** añadir una tabla única con etapa, decisor, información recibida, mensajes reales, estado local/por carga/global, garantía y coste omitido. Para Cargo, la descripción más precisa es descubrimiento parcial de identificadores por *gossip* seguido de selección por líder con atributos del registro.

El título no se modifica sin autorización del autor y del director. Si la arquitectura híbrida no resulta defendible bajo ese título, la discrepancia debe elevarse, no ocultarse.

### B5. Resolver o reclasificar la reproducibilidad de SP2--SP4

Las conclusiones reconocen reanálisis de observaciones archivadas sin todos los generadores históricos. Esto permite verificar tablas y figuras, pero no regenerar mundos y ejecuciones desde cero.

**Corrección:** recuperar/versionar los generadores y verificar un subconjunto contra hashes o tolerancias, o reclasificar esas campañas como reanálisis retrospectivo. La entrega final debe registrar commit, configuración, entorno y hashes; la etiqueta/DOI solo se fija después de congelar el árbol.

### B6. Corregir la atribución causal de Cargo

La ablación `no_physical_guard` retira certificado, waypoint y filtro (`cargo-e2e.tex:104`). Prueba la necesidad del bloque combinado, no de la guardia mecánica. La variante sin reparación se detiene deliberadamente; repararla compara continuar frente a detenerse, no el juego SP6 frente a una política razonable.

**Corrección mínima editorial:** renombrar tratamientos y limitar la conclusión al bloque conjunto. **Corrección experimental:** ablaciones separadas, y baseline de reparación voraz razonable.

## 5. Revisiones importantes, no todas bloqueantes

### 5.1 Fuerza confirmatoria y multiplicidad

- SP4-v4 tiene 12 mundos y el transporte 18; conviene retirar «confirmatorio» o ampliar semillas.
- SP1 es desarrollo; beta igual a 2 necesita familia Holm explícita y validación holdout antes de presentarse como confirmación.
- SP5 debe mostrar estratos/escenarios y un margen de relevancia práctica, no solo el promedio de la mezcla sintética.

### 5.2 Validez física e industrial

Cargo reconstruye rígidamente las poses tras el acoplamiento y no deriva el transporte de rueda--suelo. El criterio agregado no modela soporte, centro de masa, vuelco, fricción, deslizamiento ni contacto. La seguridad se audita de forma muestreada y parcial. La red fuerza conectividad y omite el tráfico del registro (`cargo-e2e.tex:116`).

Por ello, «entorno industrial» describe el contexto y un piloto cinemático, no una validación industrial. La cifra 359/360 debe mantenerse como prueba de integración de software sobre un benchmark estrecho.

### 5.3 Dificultad del generador Cargo

El análisis adversarial encontró que casi cualquier triple satisface el criterio agregado: 100 % de los triples para N igual a 4 y aproximadamente 99,6 %/99,9 % para N igual a 8/12. Local y perfecto seleccionan los mismos miembros en 360/360 mundos. Esta estructura reduce la evidencia sobre heterogeneidad, selección combinatoria y degradación informativa.

Si no se amplía la campaña, debe declararse como limitación de validez interna del benchmark integrado.

## 6. Auditoría de patrones de escritura artificial

Esta auditoría identifica señales de estilo; **no determina autoría ni estima un porcentaje de texto generado**.

### Resultado

- **P0, artefactos críticos:** no detectados. No hay restos de chatbot, marcadores, conclusiones vacías ni texto de propuesta en futuro como en revisiones antiguas.
- **P1, patrones fuertes:** no detectados. Cero apariciones de «cabe destacar», «es importante», «en este sentido», «en este contexto» y adjetivos promocionales como «revolucionario», «crucial» o «transformador».
- **P2, patrones editoriales:** persisten una microestructura casi isomorfa en SP0--SP8, acumulación de cautelas al final de secciones, tablas seguidas de paráfrasis numéricas y algunos párrafos con enumeraciones densas. La plantilla canónica explica parte de esa regularidad.

### Dictamen de estilo

No hay base responsable para afirmar que la memoria «parece escrita por IA» en sentido fuerte. Sí hay una voz de auditoría técnica muy regular que puede sentirse mecánica. La solución no es «humanizar» con sinónimos ni eliminar cautelas: es jerarquizar, reducir repetición y variar la función argumental de cada SP según el fallo que resuelve.

## 7. PDF, bibliografía y presentación

El PDF es visualmente profesional y no muestra cortes graves. Varias tablas son densas y pequeñas, y existen páginas parcialmente vacías. El log no contiene citas ni referencias indefinidas, pero registra caracteres U+0016 ausentes, sustituciones de fuente y problemas de cajas. La extracción textual del PDF presenta códigos de control en fórmulas, lo que puede perjudicar búsqueda y accesibilidad aun cuando el render sea legible.

**Criterio de cierre:** compilación repetible con cero referencias/citas indefinidas, cero caracteres ausentes, cero cajas desbordadas y verificación visual de tablas y fórmulas críticas.

## 8. Orden de corrección recomendado

1. Corregir OE5 y la matriz OE/RQ/HP en conclusiones.
2. Elegir y documentar la ruta Cargo: integración real o demostrador híbrido. Para un depósito próximo, se recomienda la segunda.
3. Reescribir la síntesis de contribución y distribución con una tabla de información/decisor/garantía.
4. Limitar causalmente las ablaciones y reclasificar SP4/SP1 donde proceda.
5. Ejecutar la reducción estructural de 15 páginas, preservando SP3--SP6 y resultados negativos.
6. Cerrar reproducibilidad, manifiestos y estado de release.
7. Limpiar fuentes, caracteres, tablas y cajas; recompilar y revisar visualmente.
8. Reejecutar las 75 pruebas y actualizar la matriz de evidencia si cambia la fuerza de HP/OE/RQ.

## 9. Preguntas que debe poder responder la defensa

1. ¿Cuál es la contribución nuclear única: un juego distribuido integrado o una arquitectura híbrida de contratos por capas?
2. ¿Qué resultado de Cargo depende de la teoría de juegos y no se explica por líder, registro, waypoint y planta favorable?
3. ¿Por qué Cargo sustituye el payoff SP2, el QP SP3 y el juego SP6?
4. ¿Qué información y tráfico serían necesarios sin registro global?
5. Si casi cualquier triple es factible, ¿dónde se prueba la selección heterogénea no trivial?
6. ¿Qué demuestra reparar frente a una variante programada para detenerse?
7. ¿Qué mantiene segura la carga entre fallo y reemplazo en un sistema físico?
8. ¿Qué afirmación exacta sostiene «distribuida local» bajo la arquitectura híbrida?
9. ¿Qué parte de SP2--SP4 puede regenerarse y cuál solo reanalizarse?
10. ¿Cuál es el falsador cuantitativo preespecificado de HP?

## 10. Decisión final y condición de aprobación

**Revisión mayor, con base científica suficiente para llegar a una defensa sólida.**

La memoria puede considerarse apta cuando: cumple las 80 páginas; corrige OE5; alinea HP, contribución y Cargo; clasifica honestamente las dependencias globales; resuelve o declara la reproducción parcial; limita las inferencias causales de las ablaciones; y genera un PDF limpio. Sin esos cambios, el tribunal puede aceptar los resultados locales y aun así cuestionar la contribución central y el cumplimiento administrativo.

## 11. Informes independientes del panel

Los dictámenes separados se conservan en `docs/reviews/2026-07-18/` para mantener trazabilidad entre el consenso final y cada perspectiva.
