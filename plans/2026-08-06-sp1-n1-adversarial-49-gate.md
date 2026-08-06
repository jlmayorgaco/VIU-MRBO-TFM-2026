# Revisión adversarial y puerta 4,9 de SP1.N1

## Propósito y resultado observable

Someter el bloque de diez páginas de SP1.N1 a una revisión equivalente a la de
un tribunal VIU especialmente estricto. El resultado observable será un dictamen
con descuento por hallazgo, una matriz afirmación--evidencia--límite y, tras una
segunda fase autorizada por el usuario, una versión corregida que no conserve
objeciones críticas o mayores remediables mediante los datos ya disponibles.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md` y
  `docs/07_SP_SECTION_TEMPLATE.md` fijan alcance, evidencia y lenguaje.
- `experiments/configs/sp1_n1_confirmatory_v2.yaml` y los RAW de
  `scripts/results/sp1_levels/n1_v2/raw/` permanecen congelados.
- `thesis/sp1_levels_23p/main.tex` y sus figuras producen el PDF de diez páginas.
- `scripts/sp1_n1.py` genera estadísticas, métricas y figuras desde los RAW.

## Alcance y no alcance

Incluye formulación N1, diseño E1--E4, validez estadística, comparadores,
trazabilidad, redacción, figuras y cumplimiento editorial VIU. No evalúa aquí
la contribución completa de SP1.N2--N4 ni la calidad global de toda la memoria.
No se alteran semillas, hipótesis congeladas o resultados; todo análisis nuevo
se identifica como diagnóstico o sensibilidad posterior.

## Supuestos y preguntas resueltas

- El objeto evaluado es un bloque del capítulo 6, no un artículo autónomo.
- La nota objetivo 4,9/5 no puede garantizarse: la puerta interna exige que un
  descuento adicional solo pueda apoyarse en una preferencia del evaluador o en
  una limitación científica ya declarada, no en una omisión corregible.
- Se adopta el punto de vista de un tribunal de robótica móvil, optimización y
  metodología cuantitativa.

## Diseño matemático/técnico

La auditoría comprobará definición previa de variables, unidades, clase del
LSAP, alcance del MILP, diferencia entre factibilidad y optimalidad, unidad
experimental, familias de hipótesis, estimandos, multiplicidad, censura y
correspondencia entre texto, figuras, configuración, RAW y matriz de evidencia.

## Plan experimental

No se reabre la campaña. Se permiten postprocesos de sensibilidad sobre los
4.500 mundos existentes de E1, por ejemplo estratificación por tamaño/cuota, sin
cambiar el contraste confirmatorio. Toda nueva figura o tabla se genera desde
RAW mediante el script vigente y conserva denominadores e incertidumbre.

## Hitos

- [x] Hito 1 -- dictamen adversarial con nota inicial y objeciones localizadas.
- [x] Hito 2 -- cierre de objeciones críticas y mayores remediables.
- [x] Hito 3 -- recompilación, revisión visual y pruebas completas.
- [x] Hito 4 -- re-revisión con matriz de verificación y nota residual honesta.

## Validación

- Contrastar cifras del PDF con CSV, configuración y manifiesto.
- Ejecutar `python scripts/sp1_n1.py --reuse-raw` si cambia el postproceso.
- Ejecutar `python scripts/build_sp1_levels_pdf.py` y comprobar diez páginas.
- Ejecutar las pruebas SP1.N1, Húngaro y TikZ protegido.
- Renderizar e inspeccionar las diez páginas; verificar fuentes y referencias.

## Riesgos y mitigaciones

- **HARKing:** no cambiar hipótesis ni gates; rotular sensibilidades nuevas.
- **Baseline débil:** limitar la conclusión o añadir diagnóstico de orden sin
  reescribir el confirmatorio.
- **Sobreafirmación física:** usar carga útil escalar, no factibilidad mecánica.
- **Microbenchmark:** declarar reloj, alcance de la medición y exclusiones; no
  convertir el ajuste observado en complejidad asintótica.
- **Presupuesto:** conservar diez páginas compactando antes de añadir contenido.

## Registro de decisiones

- 2026-08-06: se retira la calificación interna 5/5 previa por falta de una
  revisión adversarial suficientemente exigente.
- 2026-08-06: el primer pase es de solo lectura, conforme al protocolo de
  revisión; las correcciones comienzan después de registrar el dictamen.

## Progreso

El dictamen inicial quedó registrado en
`reports/2026-08-06-sp1-n1-adversarial-jury-review.md`: revisión mayor y nota
interna conservadora de 3,95/5. Se identificaron cinco objeciones obligatorias:
clasificación de endpoints, alcance de E1, alcance físico de E4, formulación del
MILP y alcance de las mediciones de E2. La fase de corrección está en curso y no
reabre los RAW ni modifica los gates confirmatorios.

La fase terminó con las cinco objeciones obligatorias cerradas. El PDF conserva
10 páginas, fue renderizado completo, no registra cajas desbordadas ni referencias
indefinidas y superó 21 pruebas dirigidas más el comprobador de las cinco figuras
TikZ protegidas. La re-revisión final queda añadida al dictamen y fija una puerta
interna de 4,90/5 para este bloque, condicionada a no extrapolarla al TFM completo.
