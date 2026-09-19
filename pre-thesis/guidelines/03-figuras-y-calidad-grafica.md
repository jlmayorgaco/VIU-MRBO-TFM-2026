# Figuras y calidad grafica

> Parte de las directrices del TFM. Contenido copiado sin cambios de
> `GUIDELINES.md`, lineas 2716 a 4673. Indice en [`00-INDICE.md`](00-INDICE.md).

---

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