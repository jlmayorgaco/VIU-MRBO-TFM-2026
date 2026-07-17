# Revisión SP0--SP8 con la plantilla maestra

## Propósito y resultado observable

Revisar SP0--SP8 con una gramática científica común que distinga incremento, oráculo, cadena de información, aporte propio, resultado formal, protocolo, evidencia y transición. El resultado será verificable en la plantilla canónica, en una matriz de auditoría por SP y en los recuadros naranjas de contribución de la memoria.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija una contribución nuclear única y evita presentar cada SP como una tesis independiente.
- `docs/01_VIU_REQUIREMENTS.md` limita la extensión y desaconseja nueve miniartículos completos.
- `docs/02_RESEARCH_MATRIX.md` fija el nivel de evidencia objetivo y el carácter condicionado de SP7.
- `docs/03_EXPERIMENT_PROTOCOL.md` fija baselines, estadística, ablaciones y reproducibilidad.
- `docs/04_CLAIMS_EVIDENCE.md` es la autoridad sobre el estado de cada afirmación.
- `docs/05_NOTATION.md` contiene la notación canónica.
- `docs/07_SP_SECTION_TEMPLATE.md` es la microestructura obligatoria vigente.
- La plantilla adjunta por el autor amplía el contrato con contraejemplos, cadena `OBSERVED--ESTIMATED--RAW--CLOSED--GUARDED--EXECUTED`, tabla metodológica detallada y estados de reproducibilidad.

## Alcance y no alcance

Incluye la reconciliación de ambas plantillas, la auditoría de SP0--SP8, la clasificación explícita de aportes propios y los cambios de redacción necesarios para impedir sobreafirmaciones. No incluye inventar datos, ejecutar campañas pendientes ni convertir propuestas de SP4--SP8 en resultados demostrados.

## Supuestos y preguntas resueltas

- La caja naranja identifica autoría del TFM, no prioridad universal.
- Cada caja declarará uno de cuatro estados: demostrado, validado empíricamente, propuesto o conjetural.
- Los resultados `PENDIENTE` o `REFUTADA` no pueden presentarse como contribuciones confirmadas.
- La tabla compacta de seis columnas se conserva en el cuerpo para respetar legibilidad y páginas; las doce dimensiones de la plantilla maestra se auditan mediante una matriz complementaria o se integran sin duplicar nueve tablas panorámicas.
- Juego y control se integran dentro del bloque de mecanismo/cadena de información, preservando el orden canónico requerido por `AGENTS.md`.

## Diseño matemático/técnico

Cada SP se evaluará con los estados:

1. `OBSERVED`: sensores y estado propio;
2. `ESTIMATED`: agregados inferidos o globales;
3. `RAW`: preferencia/masa continua;
4. `CLOSED`: asignación entera;
5. `GUARDED`: decisión que supera capacidad, mecánica o seguridad;
6. `EXECUTED`: acción aplicada a la planta.

La etiqueta final de cada SP será el último estado realmente alcanzado por código y evidencia. La servorregulación estratégica y la física permanecerán separadas.

## Plan experimental

No se generan campañas nuevas. La auditoría comprobará que cada SP declare mundo/semilla, baselines, información, métrica, contraste, ablación, fallos y estado de reproducibilidad. Los huecos se marcarán como pendientes sin completar cifras manualmente.

## Hitos

- [x] Hito 1 — plantilla canónica reconciliada con estados de aporte y cadena de información.
- [x] Hito 2 — matriz SP0--SP8 con contraejemplo, estado terminal, evidencia y claim defendible.
- [x] Hito 3 — cajas naranjas y cierres de SP revisados contra la matriz de claims.
- [x] Hito 4 — referencias, pruebas y PDF validados.

## Validación

- Buscar todas las cajas `contribucion` y comprobar su estado explícito.
- Verificar que los claims fuertes existen y están soportados en `docs/04_CLAIMS_EVIDENCE.md`.
- Comprobar claves bibliográficas y ledger para referencias citadas.
- Ejecutar las pruebas pertinentes de SP0--SP3.
- Compilar la memoria y revisar visualmente las páginas afectadas.

## Riesgos y mitigaciones

- **Sobrecarga de páginas:** integrar los doce campos como contrato de contenido sin repetir tablas panorámicas redundantes.
- **Prioridad bibliográfica no demostrada:** usar “aporte propio dentro de este TFM” y evitar “primero”, “nuevo universal” o “estado del arte”.
- **Propuestas confundidas con resultados:** marcar estado y evidencia dentro de la caja.
- **Arquitectura distribuida nominal:** declarar cualquier lectura global, cierre central o estimador no implementado.

## Registro de decisiones

- 2026-07-16 — Se conserva la secuencia canónica del repositorio y se incorporan las exigencias nuevas como criterios internos de cada bloque.
- 2026-07-16 — La caja naranja pasa a exigir estado de evidencia explícito; no funciona como certificado de novedad universal.
- 2026-07-16 — SP4--SP8 se tratarán como mecanismos propios propuestos mientras sus claims permanezcan pendientes.

## Progreso

Revisión completada. La plantilla canónica integra contraejemplo, cadena de información, doce dimensiones metodológicas y estados de aporte. SP0--SP3 declaran resultados demostrados/validados; SP4--SP8 incorporan problema de control, resultado pendiente y cajas de mecanismo propuesto sin sobreafirmar. Todas las cajas del cuerpo y anexos declaran estado. Las 23 pruebas pertinentes pasan y la compilación limpia `review.pdf` produce 122 páginas sin citas o referencias indefinidas; la inspección visual de las nueve cajas principales y sus continuaciones no detectó recortes ni solapamientos.
