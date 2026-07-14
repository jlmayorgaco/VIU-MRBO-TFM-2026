# Stage 2.5 — informe consolidado de integridad

**Fecha de cierre:** 2026-07-14
**Commit base del cierre:** `4b46455a3c58cd0d82bedbffea44eff336525fdf`
**Clausura TeX:** 28 archivos, SHA-256 FH-v2 `2fe96009eb6dbf047bc56e86c957410c1057a68da90ee7cedc3b03cc014abee6`
**PDF auditado:** 80 páginas, SHA-256 `6c68d2197facf29dd79f86876fbec4547d24cd707a0ea16e90b6e99cc8638ded`

## Dictamen

**PASS_WITH_EXTERNAL_NOTES — 0 bloqueadores internos.**

La evidencia local, la bibliografía, la coherencia de las afirmaciones, la originalidad muestreada, los siete modos de fallo de escritura asistida, la compilación y la maquetación pasan sus compuertas. La única excepción pendiente es externa: no se dispone del informe institucional de similitud ni de una revisión citacional independiente de otra familia de modelos. Esa ausencia se mantiene como advertencia explícita y no se convierte en un `PASS` ficticio.

## Resultados por compuerta

| Compuerta | Resultado | Evidencia |
|---|---|---|
| Afirmaciones empíricas | PASS | 142/142 afirmaciones locales verificadas; 0 `MISMATCH`; 0 `UNVERIFIABLE` interno; 4 hechos externos remitidos a fuentes; 146/146 unidades clasificadas. |
| Tabla A0--FULL | PASS | 20/20 filas verificadas campo a campo contra `paired_contrasts_holm.csv`: n, efecto, IC95 %, anchura, discordancias, p de Holm y decisión. |
| Bibliografía y contexto | PASS_LOCAL | 107/107 entradas existentes; 55 claves citadas en 97 usos; 13 correcciones bibliográficas revalidadas; 0 claves sin resolver; 0 contextos `WRONG` o `WEAK` residuales. |
| Originalidad web | PASS | 61/146 párrafos (41,78 %) y bloques adicionales; 82 consultas literales; 0 coincidencias pertinentes, cercanas o verbatim. |
| Autoplagio | PASS | 0 coincidencias de 12 o 20 palabras con la tesis previa; la única reutilización interna identificada es síntesis trazable de SP8 desde una sección fuente no incluida. |
| Modos de integridad asistida | PASS | 7/7 modos aprobados; 0 bloqueadores. |
| Claims y pruebas focalizadas | PASS | `check_claims.py`: 0 críticos/0 totales; 21 pruebas actuales de submit-ready, registro canónico y coalición física aprobadas; 37 pruebas focalizadas adicionales aprobadas en el subaudit. |
| PDF y depósito | PASS | Compilación LuaLaTeX/Biber; 0 referencias/citas indefinidas; 0 cajas overfull; 0 fuentes Type-3; revisión visual de portada, preliminares, matrices, resultados y anexos. |
| Presupuesto VIU | PASS | 63/80 páginas principales y 8/8 páginas de anexos. |
| Submit-ready normal | PASS_WITH_WARNINGS | 0 bloqueadores, 1 advertencia: falta el informe externo de similitud. |
| Submit-ready estricto | EXTERNAL HOLD | 0 bloqueadores internos; falla únicamente porque el modo estricto eleva la advertencia externa de similitud. |

## Correcciones cerradas durante la etapa

- Se declaró por etapa el presupuesto de centralización: señales por robot, cierres globales y alcance defendible.
- Se añadió una matriz de originalidad que separa antecedentes, mecanismo heredado, delta propio, evidencia y límite.
- Se alineó SP8 con su registro real: H8.1 suspendida por recursos no observados; H8.2--H8.3 conservadas solo como análisis exploratorios de calidad.
- Se clasificó CoppeliaSim/SP4 v4 como replay cinemático complementario no canónico, no como validación dinámica ni hardware.
- Se publicó el registro completo de los 20 contrastes A0--FULL y se verificó que todas las anchuras finales observadas son `<= 0,20`.
- Se repararon tres intervalos SP4, el rango de mensajes A0, la descripción de perfiles SP7 y las afirmaciones de trazabilidad por campaña.
- Se documentó la bandera heredada del freeze mediante un addendum ligado a la secuencia hashada de congelación y apertura.
- Se corrigieron y revalidaron 13 metadatos bibliográficos y dos contextos débiles; la nueva matriz de originalidad recibió una auditoría contextual adicional.
- Se ajustó la maquetación de los anexos al límite VIU, se eliminó la página huérfana final y se dejó una única tabla legible de 20 contrastes.

## Límites que permanecen explícitos

- El resultado central es simulación planar; no acredita hardware, seguridad funcional ni transferencia industrial.
- A0--FULL contiene componentes distribuidos, pero sus umbrales, cierres, guardias y reemplazo canónicos aún consultan información global.
- SP6--SP8 no comparten el cierre hashado completo de A0--FULL/SP5; su trazabilidad y fuerza inferencial se declaran por separado.
- El efecto FULL identifica el paquete completo, no el efecto causal individual de mensajes, memoria y reemplazo.
- El servicio institucional de similitud y la revisión citacional externa de otra familia siguen pendientes fuera del repositorio.

## Checkpoint obligatorio

La Etapa 2.5 queda cerrada. No debe iniciarse la siguiente etapa de revisión/redacción del pipeline hasta recibir confirmación explícita del autor.
