# Auditoría de figuras y redacción de resultados SP0--SP8

## Alcance de la revisión

Esta auditoría cubre el capítulo 6 y las secciones `sp0.tex`--`sp8.tex`. Se revisó la cadena afirmación--métrica--dato--figura--interpretación contra `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md` y `docs/04_CLAIMS_EVIDENCE.md`. No se generaron observaciones nuevas ni se modificó la fuerza de las afirmaciones. Las figuras incorporadas proceden de campañas y artefactos ya versionados.

## Hallazgo principal

La ausencia visual no se debía a falta general de datos. SP0 y SP2--SP8 ya contenían bloques de figuras experimentales, pero estaban desactivados mediante `\iffalse`. Solo SP1 mostraba su figura cuantitativa. La corrección consistió en recuperar esas figuras y añadir, cuando respondía a otra pregunta experimental, un segundo panel o gráfico canónico.

## Cobertura por subproblema

| SP | Evidencia visible en el cuerpo | Pregunta que responde | Límite que debe conservarse |
|---|---|---|---|
| SP0 | eficiencia de equilibrio; escala y bienestar | ¿cuánto se pierde frente al óptimo y cómo cambia con la escala? | no se valida robustez de red ni una ley general de escalabilidad |
| SP1 | desempeño por régimen de demanda | ¿cuándo bastan déficit, cuórum y cierre QR? | el ajuste es de desarrollo; QR usa ordenación central y no equivale a CBBA |
| SP2 | factibilidad, utilidad y coste con capacidad efectiva | ¿qué aporta la capacidad multidimensional frente a la cardinalidad? | la factibilidad es operativa, no mecánica; no se evalúa una EDO de Smith ni un estimador vecinal |
| SP3 | desempeño mecánico agregado; trayectoria KKT representativa | ¿cuántos falsos positivos elimina el filtro físico y cómo evoluciona una ejecución? | QP planar, guarda global y contactos idealizados; la trayectoria no constituye inferencia estadística |
| SP4 | matriz de acoplamiento; compromiso transporte--control | ¿qué fallos aparecen al pasar de acoplar a transportar? | campañas separadas; estabilidad local bajo contactos fijos, no prueba extremo a extremo |
| SP5 | seguridad--progreso; matriz de colisiones | ¿la capa de seguridad evita colisiones y qué coste paga en bloqueo? | geometría circular y evidencia empírica; no se prueba invariancia global |
| SP6 | recuperación por fallo; coste y comunicación | ¿qué fallos son recuperables dentro del plazo y con qué sobrecoste? | certificado aditivo; la dinámica de reacoplamiento no está modelada por completo |
| SP7 | entregas por régimen; compromiso tráfico--coste | ¿qué exclusiones locales se resuelven y dónde cae el rendimiento? | ejecutor discreto; no equivale a MAPF ni garantiza separación continua |
| SP8 | escala de red; calidad--comunicación; frontera de coste | ¿cuánto recupera la retransmisión y cuándo deja de compensar? | colapso en escenarios grandes; oráculo limitado y sin evidencia de energía, memoria o hardware |

## Auditoría de estilo

No se detectó un problema de corrección gramatical, sino de voz editorial. Los patrones dominantes eran introducciones casi isomorfas ("SPX añade..."), síntesis con el mismo orden retórico y acumulación de cautelas al final de cada sección. Además, al estar ocultas las figuras, la evidencia aparecía como tablas densas seguidas de paráfrasis numéricas, lo que reforzaba la impresión de texto generado.

La revisión cambia el eje narrativo de cada SP: parte del fallo heredado, muestra la medición que lo aísla y cierra con el límite que bloquea el siguiente escalón. También incorpora una frase de lectura antes de cada figura para que el gráfico tenga función argumental. Se conservaron cifras, términos canónicos y clasificación de evidencia.

## Riesgo editorial pendiente

El capítulo 6 ocupa aproximadamente 70 páginas en la compilación revisada. Aunque supera el 50 % del cuerpo principal, deja muy poco margen para cumplir simultáneamente el intervalo de 50--80 páginas del cuerpo y la estructura VIU. La siguiente intervención debería ser una pasada de compresión: mantener en el cuerpo los gráficos que sostienen hipótesis, resumir tablas que duplican exactamente la figura y trasladar desgloses secundarios a anexos. Esa decisión debe hacerse por trazabilidad, no aplicando un recorte uniforme a los nueve SP.

## Decisión de evidencia

Las nuevas inclusiones cambian la presentación, no el estatus científico. SP0 conserva evidencia A; SP1, SP2, SP3 y SP6 mantienen sus reservas parciales; SP4 sigue limitado a su afirmación local; SP5, SP7 y SP8 continúan como evidencia C o exploratoria donde así lo fija la matriz. Ningún gráfico se interpreta como prueba de convergencia, estabilidad, robustez u optimalidad global.
