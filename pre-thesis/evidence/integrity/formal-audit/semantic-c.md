# Auditoría semántica formal C — últimas 45 unidades de `paper/`

## Veredicto

Se auditaron exactamente las 45 unidades consecutivas `PAPER-FR-0101`--`PAPER-FR-0145`, en el orden vigente de `pre-thesis/evidence/formal-results-audit.csv`. La revisión cubrió el enunciado y su pasaje de prueba o justificación, además de supuestos, dominio, unidades, dependencias, frontera o contraejemplo y enlace con el ledger canónico de claims y evidencia. Compilar no se trató como prueba ni como criterio de promoción.

| Veredicto | Filas | Lectura |
|---|---:|---|
| `PROMOTE` | 0 | Ninguna unidad reúne todavía enunciado cerrado, prueba autocontenida, notación reconciliada y enlace claim--evidencia nuevo. |
| `CANDIDATE` | 30 | Resultado recuperable para la monografía después de reparar sus brechas y crear trazabilidad canónica. |
| `REJECT` | 11 | El enunciado es falso con las hipótesis escritas, la prueba no alcanza la conclusión o la recomendación no es una consecuencia formal. |
| `DUPLICATE` | 3 | El contenido ya está cubierto por un resultado activo o por otra unidad más completa del mismo corpus. |
| `NOT_FORMAL` | 1 | Es una definición contable con extensiones no demostradas, no una proposición. |
| **Total** | **45** | Cobertura completa del lote C. |

El detalle fila a fila está en `semantic-c.csv`, con el esquema exacto de 18 campos `BASE_COLUMNS` usado por el consolidador conservador.

## Resultados que no sobreviven la auditoría

Los once rechazos tienen una frontera o un contraejemplo concreto:

- `co:admision` comprueba solo la fila del robot admitido. Esa operación puede destruir la dominancia diagonal de una fila existente; el ejemplo matricial de dos agentes registrado en el CSV satisface la prueba local y viola la conclusión global.
- `pr:rondas-color` conserva la cota cromática abstracta, pero la combina con una cota geométrica de grado falsa. La misma falla aparece de forma explícita en `pr:compatibilidad`: con radio de comunicación 1 y separación mínima 0,2, una rejilla interior produce 80 vecinos, frente a la cota declarada de 31.
- `pr:arrendamiento` presupone la exclusión mutua que intenta demostrar. Dos solicitantes pueden leer simultáneamente la versión expirada y publicar propietarios distintos con la misma versión siguiente.
- `th:N-logit` necesita un equilibrio regular aislado y una rama local única. Con fitness constante, todo punto interior es Nash, mientras el reposo logit es uniforme, lo que contradice la convergencia afirmada hacia un Nash interior arbitrario.
- `pr:sesgo` mezcla una ganancia semi-Markov por unidad de tiempo con una ecuación de Poisson de tiempo discreto. El sistema de un estado, recompensa 1 y duración 2 vuelve incompatibles la ecuación y la normalización propuestas.
- `th:subprovision` obtiene algunas desigualdades útiles, pero sus bicondicionales, unicidad y orden estricto no se siguen de mera concavidad. La función lineal `p(s)=s` deja una reserva no única y refuta los pasos estrictos de la prueba.
- `th:prima` hereda esa no unicidad y además reemplaza capacidades heterogéneas por un premio común sin justificación. El balance contable puede conservarse, no la implementación óptima afirmada.
- `pr:factorizada` confunde conectividad conjunta asintótica con acuerdo exacto dentro de una ventana finita de reclutamiento. Un dato puede no atravesar el árbol antes del cierre de la fase.
- `th:topologia-garantizada` usa solo `h>=0` para una barrera de grado relativo dos. En la frontera, una velocidad relativa saliente viola la restricción antes de que una aceleración finita pueda corregirla; también falta restringir el algoritmo a las aristas del árbol fijo.
- `co:precio-conectividad` convierte un multiplicador en recomendación de recableado sin demostrar sensibilidad, factibilidad alternativa ni preservación de conectividad. Una arista puente cara puede ser irremplazable.

Estos objetos deben permanecer en `archive-only` hasta que exista un enunciado nuevo y una demostración independiente; corregir prosa o compilar el archivo no los rehabilita.

## Duplicados y objeto no formal

| Unidad de `paper/` | Destino | Razón |
|---|---|---|
| `pr:ruta-ruedas` | `C-SP2-N1-KIN-FORMAL` | El spine activo ya contiene la elevación cinemática, la equivalencia más precisa, la cota de rueda y pruebas automatizadas. |
| `th:N-prima` | `archive-only` | Resume sin prueba la condición de prima desarrollada después en `sec_standby.tex`. |
| `pr:nucleo` | `archive-only` | Repite el inciso de capacidades iguales de `th:N-nucleo`, cuya versión contiene la justificación por jugador con veto. |

`pr:bateria` se clasificó `NOT_FORMAL`: define un presupuesto energético útil, pero su chequeo en línea y su interpretación de seguridad no se derivan de la identidad. Puede usarse como definición de fondo, nunca como teorema propio.

## Candidatos recuperables

Los candidatos de mayor valor técnico incluyen la identidad pasiva del *pad* isotrópico, el certificado planar de cerco, el grado relativo rueda--barrera, el potencial de congestión afín ponderado, la suma de Minkowski y el despeje, los precios lineales y su ventana explícita, el muestreador de Gibbs, MaxWeight, el conjunto internamente recurrente común, la construcción dual del núcleo divisible, las celdas de potencia y el consenso conmutado.

Su estado `CANDIDATE` no equivale a evidencia alcanzada. Algunas pruebas son correctas solo en un modelo ideal continuo; otras omiten regularidad, suavidad, condiciones de frontera, unidades o una dependencia bibliográfica primaria. Ninguna de las 30 unidades candidatas tiene todavía un claim y una evidencia canónicos propios. Antes de migrar debe cerrarse el enunciado, sincronizar símbolos con `docs/05_NOTATION.md`, incorporar la prueba completa, añadir test o contraejemplo automatizado cuando corresponda y superar revisión independiente.

## Validación y límites

El validador comprobó:

- 45 filas y las 18 columnas exactas de `BASE_COLUMNS`;
- cobertura consecutiva y en el mismo orden desde `PAPER-FR-0101-pr:fuera-eje` hasta `PAPER-FR-0145-co:precio-conectividad`;
- 45 `result_id` únicos, cero huecos numéricos y 45 pares únicos `source_path`--`locator`;
- cero campos obligatorios vacíos y solo la taxonomía permitida;
- coincidencia de ruta, localizador, etiqueta, entorno y título con el inventario;
- coincidencia SHA-256 del inventario con los siete archivos fuente auditados.

Resultado: `SEMANTIC_C_VALIDATION=PASS`; distribución `CANDIDATE:30, DUPLICATE:3, NOT_FORMAL:1, REJECT:11`.

Esta es una auditoría semántica estática de Stage 2.5. No ejecutó Stage 3, no regeneró ni modificó el inventario `formal-results-audit.csv`, no compiló `paper/` y no editó LaTeX, claims, manifiestos, notación, código ni datos.
