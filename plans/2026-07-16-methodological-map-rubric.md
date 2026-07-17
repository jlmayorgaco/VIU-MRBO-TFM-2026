# Rúbrica reproducible para el mapa metodológico

## Propósito y resultado observable

Reemplazar la ubicación cualitativa no formal de la Figura 3 por una rúbrica auditable. Cada trabajo del mapa tendrá indicadores revisables, coordenadas nominales $(x_p,y_p)$ y una proyección de presentación que agrupe por proximidad metodológica sin borrar el significado cartesiano de los ejes.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: arquitectura distribuida, white-box y límites del alcance.
- `docs/02_RESEARCH_MATRIX.md`: distinción entre asignación, transporte, seguridad y red.
- `docs/04_CLAIMS_EVIDENCE.md`: C8 limita la conclusión al corpus verificado.
- `docs/05_NOTATION.md`: registro de los nuevos símbolos de clasificación.
- `references/LITERATURE_LEDGER.md`: evidencia primaria verificada por cada trabajo.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`: narrativa breve y Figura 3.
- `thesis/sections/appendices/06-methodological-map-audit.tex`: cálculo, sensibilidad y tabla de auditoría.

## Alcance y no alcance

Incluye una clasificación metodológica descriptiva de los trabajos visibles en la Figura 3, una familia primaria de mecanismo y cobertura SP. No mide calidad, impacto, citas, rendimiento ni madurez; tampoco convierte esta revisión en evidencia de una garantía del TFM.

## Diseño matemático/técnico

Para cada trabajo $p$ se puntúan, en $\{0,0.5,1\}$, la autonomía de decisión $\chi_p^{\mathrm{dec}}$, la localidad de información $\chi_p^{\mathrm{loc}}$, la dependencia de aprendizaje $\chi_p^{\mathrm{learn}}$ y la explicitud del mecanismo $\chi_p^{\mathrm{exp}}$. Las coordenadas nominales son

\[
x_p=1-2(0.6\chi_p^{\mathrm{dec}}+0.4\chi_p^{\mathrm{loc}}),\qquad
y_p=\chi_p^{\mathrm{learn}}-\chi_p^{\mathrm{exp}}.
\]

El peso $0.6/0.4$ prioriza quién toma la decisión en ejecución sobre el alcance de la información que usa. La revisión de agrupamiento añade cuatro familias primarias: juego/mercado, búsqueda/heurística, control/consenso y política aprendida. La distancia compuesta combina arquitectura, coincidencia de familia y solapamiento SP. Las coordenadas de presentación se obtienen mediante una proyección de estrés anclada a $(x_p,y_p)$ y restringida al cuadrante nominal.

## Hitos

- [x] Registrar los indicadores y la justificación de cada trabajo del mapa.
- [x] Añadir fórmula, escala y limitación a la memoria.
- [x] Ajustar los puntos del TikZ a las coordenadas nominales más el desplazamiento visual declarado.
- [x] Compilar, verificar citas y revisar visualmente la página.
- [x] Añadir distancia de familia y alcance SP a la distancia arquitectónica.
- [x] Reagrupar los puntos mediante una proyección anclada y actualizar el color por familia primaria.
- [x] Recompilar y revisar que los clústeres y etiquetas sean legibles.
- [x] Añadir separación vertical condicionada para evitar filas white-box saturadas sin cambiar las coordenadas nominales.
- [x] Auditar la franja vacía y declarar su origen ordinal y limitado al corpus.
- [x] Mover ecuaciones, sensibilidad y tabla de cálculo al anexo metodológico.
- [x] Recompilar y verificar visualmente el capítulo principal y el nuevo anexo.

## Validación

- Comprobar que todas las claves del mapa aparezcan en la rúbrica y en el ledger como `VERIFICADA`.
- Compilar `thesis/build.ps1` y revisar errores, referencias y solapes en la página renderizada.
- Confirmar que el texto no presenta el resultado como métrica empírica ni bibliometría.

## Riesgos y mitigaciones

- Falsa precisión: usar sólo tres niveles y declarar que la rúbrica es descriptiva.
- Arquitectura ambigua: usar el nivel intermedio y consignar la limitación, nunca inferir descentralización por el nombre del método.
- Oclusión visual: declarar cualquier jitter y no alterar el valor nominal de la tabla.
- Pérdida del significado cartesiano: mantener penalización de anclaje y restricciones de cuadrante; presentar la proyección como capa visual, no como nuevas coordenadas nominales.

## Registro de decisiones

- 2026-07-16: la Figura 3 pasa de ser una clasificación puramente cualitativa a una rúbrica ordinal, trazable al ledger.
- 2026-07-16: se adopta una distancia compuesta para que trabajos de juegos/mercados, búsqueda/heurísticas, control/consenso y políticas aprendidas formen vecindades distinguibles.
- 2026-07-16: se añade una penalización vertical condicionada por proximidad horizontal; es una corrección de legibilidad y no una nueva dimensión metodológica.
- 2026-07-16: la franja vacía no se rellenará artificialmente; se declarará como consecuencia de la discretización ordinal y de la composición del corpus. El detalle de cálculo se retira del flujo principal y pasa a un anexo auditable.
- 2026-07-16: se elimina el bono léxico basado en términos del título; ML-LNS y GraphT pasan a la frontera nominal $y=0$ y la orientación data-driven depende solo de la arquitectura acreditada.

## Progreso

Completado el 2026-07-16: se clasificaron los trabajos visibles, se eliminó el bono léxico no defendible y se dejó en el capítulo principal solo la lectura descriptiva de la Figura 3. La ecuación de ejes, la distancia, la proyección, la sensibilidad y la tabla trabajo por trabajo quedaron en el Anexo F. La sensibilidad $w\in[0.5,0.7]$ conserva la categoría horizontal de todo el corpus; Paul (2023) se clasifica como planificación centralizada y ML-LNS/GraphT como híbridos de mecanismo explícito y componente aprendido. La distancia final es $D=0.50d_{\mathrm{met}}+0.35d_{\mathrm{fam}}+0.15d_{\mathrm{SP}}$ y la Figura 3 usa una proyección de estrés anclada, restringida al cuadrante nominal, con repulsión entre marcadores y separación vertical condicionada por proximidad horizontal. El color distingue juegos/mercados, control/consenso, búsqueda/heurística y política aprendida. `thesis/build.ps1` finalizó correctamente, sin referencias o citas indefinidas; la Figura 3 se revisó en la página 42 y el Anexo F en las páginas 124--126 del PDF de 126 páginas. El bloque de anexos ocupa 20 páginas, el máximo permitido por la plantilla VIU.
