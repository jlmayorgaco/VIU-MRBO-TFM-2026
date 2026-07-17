# Ramas físicas Cargo y empuje/caging

## Propósito y resultado observable

Separar los SP físicos en dos subproblemas coherentes: `C` para carga soportada sobre una coalición en formación rígida y `E` para empuje no prehensil/caging. La memoria deberá declarar para cada rama estado, contacto, sensores, control, factibilidad, métricas y nivel de evidencia, sin transferir garantías entre modelos.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `thesis/sections/mainmatter/03-hypotheses.tex`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/sections/mainmatter/06-results-and-analysis/sp3.tex` a `sp6.tex`.

## Alcance y no alcance

La rama Cargo será el modo primario y exigirá soporte compartido, formación rígida y reparto de wrench. La rama E será secundaria: exigirá contacto unilateral, trayectorias de empuje y realimentación de pose de la caja mediante sensores de proximidad. Solo se denominará caging cuando se verifique confinamiento geométrico; en otro caso se informará como empuje cooperativo. No se formulará una prueba común de estabilidad para ambas ramas.

## Supuestos y preguntas resueltas

- La caja es un cuerpo rígido planar en ambas ramas, pero cambia la interfaz robot--carga.
- Cargo mantiene transformaciones relativas robot--carga dentro de tolerancias.
- Empuje/caging admite deslizamiento y pérdida de contacto; la entrada sobre la caja emerge de contactos unilaterales.
- La percepción de la rama E estima posición y orientación de la caja a partir de proximidad; el modelo deberá declarar observabilidad, ruido, alcance y tasa de muestreo.

## Diseño matemático/técnico

- `SP3-C`: soporte, rigidez, reparto de carga y conjunto realizable de wrench.
- `SP3-E`: unilateralidad, fricción, contacto activo y, si procede, certificado geométrico de caging.
- `SP4-C`: trayectoria del cuerpo compuesto coalición--carga y error de formación.
- `SP4-E`: trayectorias individuales de empuje cerradas con error estimado de pose de la caja.
- `SP5-C/E`: huellas y restricciones de seguridad específicas.
- `SP6-C/E`: recuperación ante pérdida de soporte frente a pérdida de contacto/confinamiento.

## Plan experimental

Cargo medirá error de formación, distribución de soporte, residual/margen de wrench y pose de carga. Empuje/caging medirá error de pose estimado, pérdida/recuperación de contacto, deslizamiento, progreso por empuje, distancia de caging cuando aplique y entrega. Las ramas no se compararán como si recibieran el mismo certificado físico; cada una tendrá baseline y criterio de éxito propios.

## Hitos

- [x] Actualizar charter, matriz SP y protocolo experimental.
- [x] Generalizar H2 y la matriz de evidencia por modalidad.
- [x] Introducir la distinción en marco teórico y resultados SP3--SP6.
- [x] Compilar, medir páginas y auditar referencias y notación.

## Validación

- Búsqueda de afirmaciones que mezclen rigidez, caging y empuje.
- Compilación LuaLaTeX sin referencias indefinidas.
- Revisión visual de las páginas modificadas.
- Confirmación de que Cargo sigue siendo primario y empuje/caging secundario.

## Riesgos y mitigaciones

- Inflación del alcance: mantener una sola contribución nuclear y evidencia secundaria C para la rama E.
- Uso impreciso de caging: reservar el término a confinamiento geométrico demostrado.
- Sensado insuficiente: no afirmar control de orientación si la configuración de proximidad no hace observable la pose planar.
- Transferencia inválida de estabilidad: analizar cada interfaz de contacto por separado.

## Registro de decisiones

- 2026-07-15: el autor solicita subdividir los SP mecánicos en Cargo y caging/empuje.
- 2026-07-15: se adopta `C` para Cargo y `E` para empuje/caging, sin crear una segunda escalera SP0--SP8.

## Progreso

La bifurcación C/E se propagó al charter, objetivos, hipótesis, matriz SP, protocolo, claims, notación, marco teórico y resultados SP3--SP6. Cargo permanece como modalidad primaria con evidencia B; empuje/caging es extensión C. El diagrama SP4 ahora separa trayectoria de carga y trayectorias robóticas e identifica sensado de proximidad. La auditoría encontró 65 claves citadas en los archivos revisados y ninguna ausente de la bibliografía. LuaLaTeX compila sin referencias indefinidas; la memoria queda en 67 páginas y el marco conserva 10 páginas. La revisión visual verificó los diagramas SP3/SP4 sin recortes.
