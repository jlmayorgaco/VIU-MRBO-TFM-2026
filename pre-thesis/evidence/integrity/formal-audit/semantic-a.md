# Auditoría semántica formal A — primeras 50 unidades de `paper/`

## Veredicto

Se auditaron las primeras 50 filas del corpus `paper`, ordenadas de forma estable por `path`, línea inicial y `result_id`, después de excluir cualquier fila con `audit_status=pass`. El intervalo resultante va de `PAPER-FR-0001-pr:cota` a `PAPER-FR-0050-pr:tubo`. El inventario de entrada no contenía ninguna de las 18 unidades del spine activo en estado `PASS`; sus 145 filas `paper` estaban en `pending-audit`.

| Veredicto | Filas | Lectura |
|---|---:|---|
| `PROMOTE` | 0 | Ningún resultado candidato tiene a la vez enunciado cerrado, prueba suficiente y enlace claim--evidencia canónico nuevo. |
| `CANDIDATE` | 29 | Resultado potencialmente útil, pero requiere una reparación acotada, trazabilidad nueva o evidencia adicional antes de migrarlo. |
| `REJECT` | 13 | El enunciado es falso en sus hipótesis actuales, la prueba no demuestra la conclusión o la propia fuente lo contradice. |
| `DUPLICATE` | 5 | El contenido ya está cubierto por un resultado activo mejor delimitado y con evidencia. |
| `NOT_FORMAL` | 3 | Es una definición, traducción directa del modelo o identidad construida por definición; no debe presentarse como teorema propio. |
| **Total** | **50** | Cobertura completa del lote A. |

El detalle fila a fila está en `semantic-a.csv`. Cada registro documenta supuestos, dominio, unidades, estado de prueba, dependencias, contraejemplo o frontera, claim, evidencia, veredicto y destino recomendado.

## Hallazgos que impiden promover material

Los trece rechazos no son meras ausencias editoriales:

- `th:mapa` usa como factor de contracción `1-epsilon lambda_2` bajo un rango de paso donde el modo de `lambda_max` puede dominar e incluso vuelve negativo ese supuesto factor.
- `th:cert` confunde el minimizador de un QP regularizado con el minimizador del residual. El contraejemplo escalar registrado en el CSV viola el bicondicional.
- `pr:caging` aplica la curva de Jordan en el plano de trabajo sin construir el espacio de configuraciones `SE(2)` de una carga rígida.
- `co:terminacion` deduce finitud de una estrategia híbrida a partir de la finitud de su parte discreta. Una sucesión continua estrictamente mejorante puede ser infinita.
- `pr:jerarquia` identifica estabilidad de orden `N` con máximo sobre una componente, aunque una transición conjunta puede estar desconectada o exigir una caída intermedia.
- `th:smallgain` concluye ISS sin exigir que los almacenamientos sean coercivos/comparables con las normas de estado.
- `th:dwell` solo acota una reversión binaria, no dos conmutaciones consecutivas entre tres o más modos.
- `th:descomposicion` mezcla un óptimo sobre mapa estimado con óptimos sobre mapa real. La observación inmediatamente posterior reconoce que la no negatividad afirmada puede fallar.
- `pr:composiciones` no demuestra su encapsulado no lineal y convexidad por sí sola no da la propiedad declarada.
- `th:entrega` hereda resultados inválidos y carece de equidad/ausencia de inanición; orden total no acota el tiempo de espera.
- `th:precio-seguridad` trata el multiplicador como congelado para conservar potencial y a la vez identifica reposos con vGNE sin factibilidad, signo ni complementariedad. La misma fuente corrige después esa afirmación.
- `th:rigidizacion` identifica un multiplicador de barrera con una fuerza de restricción; la observación posterior aclara que tienen unidades y condiciones KKT distintas.
- `co:agarre` no se deriva de la descomposición del núcleo y no formaliza la relación entre precarga, fricción y región de wrench.

Los tres objetos `NOT_FORMAL` son `th:robusto`, cuya equivalencia repite la definición del radio; `le:orientacion`, que reescribe la pertenencia al cono del parachoques; y `th:potencial-valor`, cuyo núcleo es la utilidad wonderful-life definida directamente a partir del mismo valor.

## Duplicados con destino canónico

| Unidad de `paper/` | Claim activo | Razón |
|---|---|---|
| `pr:degeneracion` | `C1B-SP1` | Mismo contraejemplo de déficit constante bajo escasez. |
| `co:lexico` | `C1B-SP1` | Consecuencia directa del mismo par de perfiles testigo. |
| `pr:notiron` | `C-SP2-EL-CONTACT-MODEL` | Consecuencia de complementariedad y contacto unilateral ya delimitada. |
| `pr:composicion-disjunta` | `C-SP1-N4-DMIS-TX` | La versión activa añade fase, versiones, tests y evidencia pareada. |
| `th:dos-monotonias` | `C-SP2-CROSS-MONO-FORMAL` | Misma oposición entre suma de wrench e intersección cinemática, con supuestos activos más precisos. |

Estos cinco resultados no deben copiarse a la tesis o monografía como pruebas independientes; el crosswalk debe apuntar al destino canónico.

## Candidatos recuperables

Doce de los 29 candidatos tienen una prueba esencialmente completa en la fuente, pero ninguno posee un claim/evidence nuevo en la matriz. Los de mayor valor técnico son:

- generación positiva de wrench (`th:span`), después de normalizar fuerza y momento y cerrar el argumento de polaridad;
- equivalencia optimización--VI (`th:vi`) dentro de una rama continua bien definida;
- margen entre muestras (`le:muestras`) cuando exista una cota computable de la derivada;
- aproximación local de una inversa SPD (`th:saltos`), cuya prueba de serie de Neumann falta en el texto;
- valor rank-one de un actuador (`th:actuador-adicional`) y descomposición de esfuerzo en la métrica `R` (`pr:descomposicion-R`);
- construcción de orden arbitrario con compatibilidad completa (`th:compatibilidad-completa`), que necesita claim y prueba automatizada;
- reducción de reparación heterogénea a Set Cover (`th:mohr`), promovible solo en su parte NP-completa hasta verificar las fuentes W[2] y de aproximación;
- disipación KL, monotonía de brecha espectral y la cota de cuatro mecanismos, siempre que se conserven reversibilidad, estacionaria y prefactores;
- certificado geométrico de tubo (`pr:tubo`) si la cota de error está garantizada durante todo el intervalo, no solo en muestras.

`CANDIDATE` no significa evidencia alcanzada. Antes de migrar cualquiera se requiere: enunciado corregido, símbolos sincronizados con `docs/05_NOTATION.md`, prueba autocontenida, claim nuevo o vínculo explícito, evidencia/test o contraejemplo automatizado y revisión independiente.

## Validación y límites

El validador comprobó:

- 50 filas y las 15 columnas obligatorias, más `result_id`, `title` y `recommended_destination` para coordinación entre lotes;
- selección exacta, en el mismo orden, respecto de las primeras 50 filas `paper` no `PASS` del inventario;
- cero pares duplicados `source_path`--`locator`;
- cero campos obligatorios vacíos y solo los cinco veredictos permitidos;
- coincidencia SHA-256 entre el inventario y los seis archivos fuente auditados.

Resultado: `SEMANTIC_A_VALIDATION=PASS`; distribución `CANDIDATE:29, DUPLICATE:5, NOT_FORMAL:3, REJECT:13`.

Esta auditoría es semántica y estática. No recompiló `paper/`, no ejecutó campañas, no certificó fuentes bibliográficas externas y no modificó LaTeX, código, datos, claims ni notación. Los ensayos numéricos narrados en el borrador no se consideran evidencia por aparecer en prosa; solo se usaron para localizar dependencias y fronteras. La ausencia de `PROMOTE` evita que el borrador adquiera autoridad por su propia redacción.
