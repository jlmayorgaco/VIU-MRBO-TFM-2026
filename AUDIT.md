# AUDIT — patrones de escritura atribuibles a IA en la memoria completa

> **Modo de trabajo:** auditoría de detección. Este archivo no atribuye autoría y no usa un “detector de IA” como prueba. Señala formas que pueden hacer que el texto huela a prosa generada o excesivamente plantillada.
>
> **Fecha del corte:** 18 de julio de 2026. **Estado auditado:** contenido actual del workspace, incluidas las modificaciones locales previas a esta auditoría. Las ubicaciones se expresan como `archivo:línea` y deben revisarse de nuevo si cambia la fuente.
>
> **Regla de integridad:** no se modificó la memoria, sus datos, figuras, tablas, referencias, configuraciones ni planes. El único archivo añadido al repositorio por esta tarea es `AUDIT.md`.

## Alcance

Se leyó la cadena completa incluida por `thesis/main.tex`: metadatos, portada, resumen, abstract, índices, nomenclatura, capítulos 1–7, SP0–SP8, simulación Cargo integrada, piloto Industrial 2 y anexos de reproducibilidad/demostraciones. También se inspeccionaron los fragmentos `.tex` generados que aparecen en el PDF.

El corpus fuente revisado contiene aproximadamente **44 856 palabras** en 35 archivos `.tex` principales y unas **1 619 oraciones de prosa** según una segmentación heurística que excluye la mayoría de ecuaciones, tablas y TikZ. Las celdas, captions y textos generados se revisaron aparte.

No se auditan como voz del autor los títulos bibliográficos de `references.bib`, las citas textuales ajenas ni los nombres oficiales de métodos. Las fórmulas, símbolos, rangos numéricos y operadores se consideran contenido técnico. Cuando `--` solo produce un rango/en dash LaTeX, una relación técnica o un trazo TikZ, se registra como falso positivo y no como “raya de IA”.

## Método

La revisión combina:

1. lectura manual frase por frase con el perfil de manuscrito académico técnico;
2. búsqueda global de artefactos de chatbot, fórmulas binarias, transiciones, listas, paralelismo, nominalizaciones, copula avoidance, vaguedad, inflación, meta-narración y ritmo local;
3. inventario de `:`, `;`, em dash Unicode y `--`, distinguiendo prosa, tablas y sintaxis LaTeX;
4. comparación entre aperturas, protocolos, resultados, síntesis SP y las versiones española/inglesa del resumen;
5. revisión de falsos positivos: cautelas epistemológicas obligatorias, enunciados matemáticos, convenciones VIU y terminología del dominio.

### Severidad y confianza

- **P0:** artefacto que puede dañar credibilidad de inmediato.
- **P1:** olor claro o acumulativo que conviene corregir antes de entregar.
- **P2:** patrón estilístico que merece revisión, pero puede ser correcto o exigido por el contexto.
- **Clara:** coincide directamente con un patrón.
- **Probable:** confluyen dos o más señales.
- **Contextual:** existe señal, pero también una justificación académica o técnica fuerte.

Cada hallazgo conserva la frase exacta, explica el motivo y propone una estrategia de arreglo. Las propuestas no son reemplazos automáticos: antes de aplicarlas deben preservarse cifras, alcance y nivel de evidencia.


## Auditoría de patrones de escritura atribuibles a IA — SP5–SP8, integración, piloto y conclusiones

### Alcance y criterio de este bloque

- **Modo:** detección. No se modificó ninguna fuente.
- **Archivos de prosa revisados íntegramente:** `sp5.tex`, `sp6.tex`, `sp7.tex`, `sp8.tex`, `cargo-e2e.tex`, `aws-industrial2.tex` y `07-conclusions.tex`.
- **Archivos renderizados auxiliares revisados:** macros y tablas incluidas desde `results/processed/{integrated,sp2,sp3,sp4,sp5,sp6,sp7,sp8}/**/tables/*.tex`, además de `thesis/generated/aws-industrial2-results.tex` y `thesis/generated/literature-coverage.tex`.
- **Volumen aproximado:** 425 oraciones de prosa en los siete archivos principales, más encabezados, celdas y leyendas generadas.
- **Criterio:** P0 indica un artefacto que afecta credibilidad; P1, un olor claro o acumulativo; P2, una forma que merece revisión pero puede ser correcta en prosa científica. `clara`, `probable` y `contextual` califican la confianza estilística, no la autoría.

### Cobertura de puntuación

Los conteos siguientes son heurísticos sobre prosa, captions y cajas; excluyen ecuaciones, etiquetas y la mayor parte de TikZ. Ningún archivo contiene una raya em Unicode. Los `--` de rangos, relaciones técnicas y trazos TikZ no se consideran automáticamente AI-ismos.

| Archivo | Oraciones aprox. | `:` | `;` | `--` en prosa | Lectura principal |
|---|---:|---:|---:|---:|---|
| `sp5.tex` | 86 | 9 | 2 | 2 | Los dos `--` son un rango numérico y `rueda--suelo`; no son pausas retóricas. |
| `sp6.tex` | 74 | 11 | 2 | 2 | Rango de teoremas y semillas; falsos positivos. |
| `sp7.tex` | 72 | 11 | 2 | 2 | Rangos de semillas/radios; falsos positivos. |
| `sp8.tex` | 66 | 12 | 7 | 5 | Dos comparaciones, un rango SP y el compuesto retórico `observabilidad--retransmisión--conflicto`; este último sí se marca. |
| `cargo-e2e.tex` | 56 | 3 | 3 | 2 | `tamaño--semilla` y `robot--robot`; compuestos técnicos. |
| `aws-industrial2.tex` | 16 | 1 | 0 | 4 | Compuestos/rangos LaTeX; el problema es la cadencia, no la raya. |
| `07-conclusions.tex` | 55 | 4 | 1 | 9 | Rangos SP y relaciones técnicas; no hay em dash retórico. |

### `sp5.tex`

#### R5-001 — P2 / probable

- **Ubicación:** `thesis/sections/mainmatter/06-results-and-analysis/sp5.tex:4`.
- **Cita:** “SP5 estudia esa pérdida de seguridad para la rama Cargo: tras el acoplamiento, carga y robots se representan mediante una huella rígida, y los límites de fuerza entran en $G_{C_k}\lambda_k$.”
- **Patrón:** colon explicativo, cláusulas coordinadas y apertura que resume de una vez problema, modelo e interfaz.
- **Por qué huele a IA:** la oración usa el colon como bisagra de una explicación densamente empaquetada, una forma recurrente en los inicios de los SP. El contenido es preciso; la sospecha nace de la repetición del molde.
- **Cómo arreglarla:** formular primero el cambio de seguridad y explicar en otra oración la huella y el lugar donde entran los límites de fuerza.

#### R5-002 — P2 / contextual

- **Ubicación:** `sp5.tex:8`.
- **Cita:** “La Figura~\ref{fig:sp5-scenario} separa control nominal, referencia filtrada y acción.”
- **Patrón:** metadiscurso de figura y tríada exacta.
- **Por qué huele a IA:** “la figura separa A, B y C” es una plantilla segura y repetible. Aquí también cumple la obligación académica de introducir la figura.
- **Cómo arreglarla:** conservar la referencia, pero convertirla en una afirmación sustantiva sobre dónde puede romperse la garantía y usar la figura como apoyo secundario.

#### R5-003 — P1 / clara

- **Ubicación:** `sp5.tex:77`.
- **Cita:** “\eqref{eq:sp5-velocity-projection} es referencia por muestra, no planificador.”
- **Patrón:** oposición compacta `X, no Y`.
- **Por qué huele a IA:** comprime la cautela epistemológica en la misma antítesis que reaparece decenas de veces en la memoria. La distinción es necesaria, pero el molde se ha convertido en una firma.
- **Cómo arreglarla:** afirmar positivamente que la ecuación calcula una proyección instantánea; declarar en una segunda oración que el horizonte de planificación queda fuera de esa operación.

#### R5-004 — P2 / probable

- **Ubicación:** `sp5.tex:113`.
- **Cita:** “donde $\varepsilon_{\mathrm{act},j,m}$ reúne discretización, iteración, predicción, saturación y reparto.”
- **Patrón:** nominalización contenedora y lista de cinco fuentes heterogéneas.
- **Por qué huele a IA:** `reúne` permite agrupar causas distintas sin explicar su mecanismo ni signo; el resultado parece una lista de cobertura.
- **Cómo arreglarla:** agrupar los términos por origen numérico y físico, o indicar que el residual solo los acota conjuntamente si no pueden separarse.

#### R5-005 — P1 / probable

- **Ubicación:** `sp5.tex:117`.
- **Cita:** “Campos potenciales son reactivos, VO/RVO/ORCA operan en velocidades y CBF da invariancia condicionada.”
- **Patrón:** clasificación ternaria perfectamente paralela y compresión de cinco fuentes en una sola frase.
- **Por qué huele a IA:** la frase suena a tabla generada en prosa: familia, verbo, propiedad; familia, verbo, propiedad. Además, `da invariancia` simplifica en exceso la dependencia de supuestos.
- **Cómo arreglarla:** convertir cada familia en una comparación motivada por el modelo de SP5 y reservar la garantía CBF para una oración con sus supuestos.

#### R5-006 — P2 / probable

- **Ubicación:** `sp5.tex:143-145`.
- **Cita:** “SP5 mantiene la coalición y modifica la entrada: la guardia filtra el \emph{wrench} antes de repartirlo. Cambiar miembros corresponde a SP6. Aquí se estudian seguridad y progreso.”
- **Patrón:** señalización de alcance mediante colon, frases telegráficas y metanarración `Aquí se estudian...`.
- **Por qué huele a IA:** el bloque parece andamiaje de una plantilla SP: qué se mantiene, qué pasa al siguiente SP y qué se estudia aquí.
- **Cómo arreglarla:** integrar el límite de membresía en la descripción causal de la guardia y sustituir la última frase por la pregunta o métrica concreta.

#### R5-007 — P2 / probable

- **Ubicación:** `sp5.tex:145`.
- **Cita:** “CBF local usa obstáculos a \(6\) m, predice \(0.8\) s y cuenta \(2N\) mensajes. La referencia global usa \(1.8\) s y \(N(N-1)\). El simulador lee estado global para parear mundos, sin paquetes ni consenso. Se mide la disponibilidad de información sin implementar una red completa.”
- **Patrón:** cuatro oraciones declarativas con ritmo de ficha técnica y cierres negativos.
- **Por qué huele a IA:** los datos son útiles, pero el bloque avanza por ranuras paralelas —alcance, horizonte, mensajes, excepción— sin puente argumental.
- **Cómo arreglarla:** organizarlo como contraste explícito de contratos de información y explicar qué efecto puede atribuirse a cada diferencia.

#### R5-008 — P1 / probable

- **Ubicación:** `sp5.tex:148`.
- **Cita:** “Se distinguen el \emph{wrench} nominal, la referencia filtrada y el \emph{wrench} realizable. Solo este último mueve la planta y ninguna colisión, saturación o pose se corrige después de integrar. La separación permite atribuir los fallos al filtro, al reparto de fuerzas o a la planta.”
- **Patrón:** dos tríadas, pasiva impersonal y cierre `permite atribuir A, B o C`.
- **Por qué huele a IA:** la simetría encaja demasiado bien: tres estados, tres cosas no corregidas y tres fuentes de fallo. `Permite` funciona como verbo genérico de validación.
- **Cómo arreglarla:** nombrar la cadena causal RAW/SAFE/EXEC y explicar con un ejemplo qué residual identifica cada etapa; eliminar una de las listas.

#### R5-009 — P1 / clara

- **Ubicación:** `sp5.tex:164`.
- **Cita:** “La \emph{violación aplicada} no es distancia ni probabilidad.”
- **Patrón:** definición por negación doble.
- **Por qué huele a IA:** la frase corrige dos interpretaciones antes de decir qué es la métrica. Es una variante directa de la plantilla “no es A ni B”.
- **Cómo arreglarla:** definir la magnitud positivamente como tasa de muestras con residual de barrera positivo y, solo después, aclarar sus unidades o límites interpretativos.

#### R5-010 — P1 / probable

- **Ubicación:** `sp5.tex:187-191`.
- **Cita:** “El experimento contiene \SPFiveWorlds{} mundos pareados y \SPFiveRuns{} ejecuciones: seis escenarios, \(N\in\{4, 8, 12\}\), seis semillas y ocho métodos. [...] Los ocho controles permiten tres comparaciones directas: Hamiltoniano con y sin CBF, aproximación VO frente a CBF anticipativa y CBF local frente a anticipación central.”
- **Patrón:** dos colon-listas cercanas, enumeración numerada implícita y regla de tres.
- **Por qué huele a IA:** el protocolo se narra como inventario de factores y después como inventario simétrico de comparaciones. Esa seguridad estructural hace que el texto suene ensamblado.
- **Cómo arreglarla:** separar diseño factorial de hipótesis; para cada contraste, indicar la pregunta que aísla en lugar de enumerar tres pares en una sola oración.

#### R5-011 — P2 / probable

- **Ubicación:** `sp5.tex:191`.
- **Cita:** “PD y el campo potencial completan la referencia nominal. McNemar exacto se usa para colisión y éxito seguro. Wilcoxon pareado, para la violación aplicada. Los intervalos remuestrean mundos y Holm corrige los cinco contrastes.”
- **Patrón:** sucesión telegráfica de método, prueba, prueba e inferencia; elipsis verbal en `Wilcoxon pareado`.
- **Por qué huele a IA:** el ritmo de checklist reduce la relación entre estimando, unidad experimental y prueba a frases de ranura.
- **Cómo arreglarla:** agrupar las pruebas por tipo de variable en dos oraciones completas y conectar explícitamente el remuestreo con la unidad independiente.

#### R5-012 — P1 / probable

- **Ubicación:** `sp5.tex:208-210`.
- **Cita:** “La comparación con la aproximación VO expone el intercambio entre progreso y seguridad. [...] El CBF local obtiene el mejor compromiso sin colisiones observado: éxito \SPFiveLocalCBFSafe{} y agotamiento \SPFiveLocalCBFTimeout{}. Ningún método domina en entrega segura y colisión.”
- **Patrón:** lector dirigido (`expone`), lenguaje de `mejor compromiso`, colon de revelación y conclusión de no-dominancia.
- **Por qué huele a IA:** interpreta antes de presentar los estimandos y usa una conclusión equilibrada muy reconocible. `Mejor compromiso` no define una función de preferencia.
- **Cómo arreglarla:** presentar éxito y timeout con sus valores, explicar el criterio exacto por el que se prefiere CBF local y reservar la no-dominancia para una comparación formal de Pareto si procede.

#### R5-013 — P1 / clara

- **Ubicación:** `sp5.tex:220`.
- **Cita:** “La agregación anterior oculta dónde aparecen las colisiones. La Figura~\ref{fig:sp5-collision-matrix} las desglosa por escenario y muestra que los fallos del Hamiltoniano sin filtro se concentran fuera del caso abierto nominal.”
- **Patrón:** objeto abstracto antropomorfizado (`la agregación oculta`) y metanarración de figura.
- **Por qué huele a IA:** es un puente de lector típico: anuncia que el resumen “oculta” algo y que la figura lo “revela”.
- **Cómo arreglarla:** indicar directamente en qué escenarios se concentran las colisiones y citar la figura al final como evidencia.

#### R5-014 — P1 / clara

- **Ubicación:** `sp5.tex:230-232`.
- **Cita:** “Más información y mayor anticipación no garantizan progreso. Tampoco se sustenta una menor violación aplicada del CBF local frente al potencial. [...] La referencia central no supera CBF local ni el residual al potencial. Más información o factibilidad previa al reparto no aseguran mejor acción final.”
- **Patrón:** acumulación de negaciones de frontera y repetición semántica casi literal.
- **Por qué huele a IA:** el mismo hallazgo se formula cuatro veces con sinónimos (`no garantizan`, `no se sustenta`, `no supera`, `no aseguran`). Este es un caso claro de expansión redundante y synonym cycling.
- **Cómo arreglarla:** conservar una sola oración cuantitativa y una sola interpretación; eliminar el resumen repetido o usarlo para explicar el mecanismo que causó el resultado.

#### R5-015 — P1 / clara

- **Ubicación:** `sp5.tex:234`.
- **Cita:** “Sin reparación posterior y con mundos pareados, se verifica consistencia, no fricción, rueda--suelo, percepción ni contacto conmutado.”
- **Patrón:** `se verifica X, no A, B, C ni D`, lista negativa y compuesto con `--`.
- **Por qué huele a IA:** la construcción intenta demostrar prudencia mediante una antítesis comprimida, pero gramaticalmente parece afirmar que se “verifica no fricción”.
- **Cómo arreglarla:** nombrar la consistencia concreta comprobada en una oración y listar después, con verbo propio, los fenómenos que el modelo no representa. Mantener `rueda--suelo` solo si la convención tipográfica se usa de forma coherente.

#### R5-016 — P1 / clara

- **Ubicación:** `sp5.tex:238-240`.
- **Cita:** “La guardia redujo las colisiones del Hamiltoniano sin filtro y del comparador VO, pero el precio fue una pérdida de progreso. En algunos tratamientos, cero colisiones observadas convivió con $0.833$ de agotamientos del horizonte; además, el residuo de la acción aplicada no desapareció después del reparto. La campaña sustenta seguridad operacional en los escenarios ensayados, no invariancia ni robustez general.”
- **Patrón:** falsa concesión pulida, punto y coma con `además` y cierre `X, no Y ni Z`.
- **Por qué huele a IA:** encadena exactamente resultado, coste, matiz y calibración de confianza. Es correcto, pero demasiado formulaico y repite resultados ya expuestos.
- **Cómo arreglarla:** elegir una conclusión cuantitativa principal, explicar el fallo de progreso como mecanismo y mover la ausencia de garantía a una limitación separada sin antítesis.

#### R5-017 — P2 / contextual

- **Ubicación:** `sp5.tex:240`.
- **Cita:** “El resultado se restringe a un cuerpo planar, contactos fijos y obstáculos circulares. SP6 mantiene esa interfaz conceptual y pregunta qué ocurre cuando un fallo elimina parte del soporte y obliga a reclutar un reemplazo.”
- **Patrón:** cierre canónico `resultado + tres límites + transición al siguiente SP`.
- **Por qué huele a IA:** todos los SP usan una forma semejante. La plantilla del repositorio exige esta función, por lo que el problema es la uniformidad global y no esta frase aislada.
- **Cómo arreglarla:** mantener hecho, límite y transición, pero hacer que el enlace surja del fallo concreto observado en SP5 y variar la sintaxis respecto de los demás cierres.


# Auditor�a de patrones de escritura atribuibles a IA � preliminares y metadatos

## Criterio, alcance y lectura de severidades

- **Modo:** detecci�n �nicamente. No se ha modificado ninguna fuente.
- **Perfil aplicado:** manuscrito acad�mico t�cnico biling�e. La notaci�n, los nombres de m�todos, las enumeraciones necesarias para resumir un protocolo y la cautela epistemol�gica no se consideran indicios por s� solos.
- **Archivos revisados �ntegramente:** `thesis/config/metadata.tex`; `thesis/sections/frontmatter/00-cover.tex`; `01-summary.tex`; `02-abstract.tex`; `03-contents.tex`.
- **Fuentes de control le�das antes de auditar:** `docs/00_TFM_CHARTER.md`, `01_VIU_REQUIREMENTS.md`, `02_RESEARCH_MATRIX.md`, `03_EXPERIMENT_PROTOCOL.md`, `04_CLAIMS_EVIDENCE.md`, `05_NOTATION.md` y `07_SP_SECTION_TEMPLATE.md`.
- **Interpretaci�n:** un hallazgo identifica una forma que puede hacer que la prosa *huela* a texto generado; no prueba autor�a de IA. `clara` significa que la forma coincide directamente con un patr�n pedido; `probable`, que coinciden dos o m�s se�ales; `contextual`, que la forma es sospechosa pero tambi�n convencional o �til en un resumen cient�fico.
- **Resultado de esta parte:** 26 frases marcadas: **P0 = 0**, **P1 = 6**, **P2 = 20**. Confianza: **clara = 4**, **probable = 16**, **contextual = 6**.

## Cobertura y puntuaci�n por archivo

| Archivo | Alcance efectivamente revisado | Unidades aproximadas | `:` en prosa | `;` en prosa | em dash Unicode en prosa | `--` en prosa o campos textuales | Clasificaci�n de la puntuaci�n |
|---|---|---:|---:|---:|---:|---:|---|
| `thesis/config/metadata.tex` | 14/14 l�neas; comentarios, t�tulo, autor�a, edici�n, fecha, encabezado y metadatos PDF | 10 campos textuales, 5 t�rminos clave y 2 oraciones de comentario; 0 oraciones de prosa corrida | 0 | 0 | 0 | 1 | `2025--2026` es un rango de curso en un campo LaTeX; falso positivo t�cnico, no raya ret�rica. |
| `thesis/sections/frontmatter/00-cover.tex` | 10/10 l�neas; comandos y comentario interno | 2 oraciones de comentario; 0 oraciones renderizadas | 0 | 0 | 0 | 0 | Sin usos sospechosos. |
| `thesis/sections/frontmatter/01-summary.tex` | 39/39 l�neas; cuatro p�rrafos y palabras clave | 16 oraciones, 296 palabras, m�s 5 palabras clave | 1 | 0 | 0 | 3 | El �nico `:` introduce la rectificaci�n negativa de FM-003. `SP0--SP8` es rango t�cnico; `carga--obst�culo` y `rueda--suelo` son relaciones compuestas escritas con la convenci�n de raya corta de LaTeX. Los tres `--` son falsos positivos para la regla de em dash. |
| `thesis/sections/frontmatter/02-abstract.tex` | 38/38 l�neas; cuatro p�rrafos y keywords | 16 oraciones, 293 palabras, m�s 5 keywords | 1 | 0 | 0 | 3 | El �nico `:` introduce la rectificaci�n negativa de FM-016. `SP0--SP8` es rango t�cnico; `payload--obstacle` y `wheel--ground` son compuestos t�cnicos LaTeX. Ning�n `--` funciona como pausa ret�rica. |
| `thesis/sections/frontmatter/03-contents.tex` | 11/11 l�neas; comandos de �ndices y saltos de p�gina | 0 oraciones de prosa | 0 | 0 | 0 | 0 | Sin prosa auditable. |

**Balance de puntuaci�n:** no hay punto y coma, em dash Unicode ni doble guion ret�rico. Por tanto, no existe aqu� el tic de abusar de `;` o de rayas. Los dos puntos aparecen solo dos veces y en ambos idiomas ocupan exactamente el mismo lugar discursivo: una negaci�n seguida de explicaci�n. El problema no es la densidad del signo, sino la plantilla ret�rica duplicada.

## P0 � Credibilidad inmediata

No se detectaron artefactos de chatbot, limitaciones del modelo, atribuciones vagas, halagos al lector, inflaci�n de novedad ni afirmaciones promocionales de alta gravedad.

## P1 � Indicios que conviene corregir antes de entregar

### FM-003

- **Severidad / confianza:** P1 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:6` (contin�a hasta la l�nea 8).
- **Cita exacta completa:** �No se presenta como completamente distribuida: varios cierres, agregados, optimizadores por carga y el registro del simulador mantienen dependencias globales.�
- **Patr�n:** rectificaci�n negativa `no X: Y`, voz impersonal con `se`, colon explicativo y lista nominal de cuatro elementos.
- **Por qu� huele a IA en contexto:** re�ne en una sola frase tres recursos muy t�picos de prosa generada: negar primero una etiqueta imprecisa, usar dos puntos para revelar la �matizaci�n� y rematar con un inventario perfectamente coordinado. La salvedad cient�fica es necesaria y coincide con la trazabilidad del TFM, pero la forma parece una plantilla de calibraci�n autom�tica de confianza.
- **C�mo arreglarla:** clasificar la arquitectura de manera positiva y exacta desde el comienzo; trasladar las dependencias globales a una segunda oraci�n y agruparlas por funci�n. Conservar todos los l�mites t�cnicos y eliminar tanto la negaci�n introductoria como los dos puntos.

### FM-010

- **Severidad / confianza:** P1 / clara.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:24` (contin�a hasta la l�nea 27).
- **Cita exacta completa:** �En SP8, 900 mundos hasta 128 robots mostraron que retransmitir elev� en 0.054 la tasa libre de conflictos, con 261.3 mensajes adicionales por agente, mientras la calidad colaps� en el mayor tama�o nominal.�
- **Patr�n:** conclusi�n dram�tica y vaga (`la calidad colaps�`), sujeto meton�mico (`900 mundos mostraron`) y cierre concesivo con `mientras`.
- **Por qu� huele a IA en contexto:** la primera mitad ofrece m�tricas precisas, pero la segunda reemplaza la m�trica por el sustantivo gen�rico `calidad` y un verbo enf�tico. Ese salto de precisi�n a dramatizaci�n es un patr�n frecuente de resumen autom�tico: cifra concreta, coste, giro concesivo y gran conclusi�n. La matriz de evidencia s� dispone de una medida espec�fica para el mayor tama�o, por lo que la vaguedad no es necesaria.
- **C�mo arreglarla:** nombrar la m�trica que lleg� al valor adverso y el tama�o exacto en que ocurri�; sustituir el verbo dram�tico por el resultado observado. Separar el coste de retransmisi�n y la degradaci�n de escala si ambos no caben con claridad en una sola oraci�n.

### FM-012

- **Severidad / confianza:** P1 / clara.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:31` (contin�a hasta la l�nea 32).
- **Cita exacta completa:** �La evidencia respalda una composici�n planar en los reg�menes ensayados, no una garant�a h�brida global.�
- **Patr�n:** contraste binario `respalda X, no Y`, variante acad�mica de �no es X, es Y�.
- **Por qu� huele a IA en contexto:** la frase usa una oposici�n perfectamente compacta para proyectar prudencia. El l�mite es cient�ficamente correcto, pero el molde `X, no Y` ya aparece varias veces en ambos res�menes y se vuelve una firma estil�stica reconocible.
- **C�mo arreglarla:** formular primero el alcance positivo mediante el tipo de evidencia y los reg�menes concretos; expresar la ausencia de garant�a global en una oraci�n de limitaci�n independiente. Mantener la distinci�n emp�rico/formal sin apoyarla en una ant�tesis.

### FM-016

- **Severidad / confianza:** P1 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:6` (contin�a hasta la l�nea 8).
- **Cita exacta completa:** �It is not presented as fully distributed: several closures, aggregates, per-payload optimisers, and the simulator registry retain explicit global dependencies.�
- **Patr�n:** negative correction `not X: Y`, passive construction, explanatory colon, and four-part nominal inventory.
- **Por qu� huele a IA en contexto:** it reproduces FM-003 almost mechanically and combines the same three signals: a denied label, a colon that stages nuance, and a balanced catalogue. The qualification is essential, but the packaging resembles confidence-calibration boilerplate rather than idiomatic technical English.
- **C�mo arreglarla:** state the architecture�s exact positive classification first; put the remaining global dependencies in a second sentence grouped by layer. Remove the passive negative frame and the colon without weakening the limitation.

### FM-023

- **Severidad / confianza:** P1 / clara.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:23` (contin�a hasta la l�nea 26).
- **Cita exacta completa:** �In SP8, 900 worlds with up to 128 robots showed that retransmission increased the conflict-free rate by 0.054 at the cost of 261.3 additional messages per agent, while quality collapsed at the largest nominal size.�
- **Patr�n:** vague dramatic conclusion (`quality collapsed`), metonymic evidence subject, and balanced `while` turn.
- **Por qu� huele a IA en contexto:** the sentence moves from exact quantities to an undefined quality judgement and a dramatic verb. This data-plus-concession-plus-inflated-ending pattern reads generated even though the underlying negative result is real.
- **C�mo arreglarla:** identify the exact quality metric, its observed value, and the corresponding robot or coalition count; use a descriptive verb. Split the communication trade-off from the scale failure if necessary.

### FM-025

- **Severidad / confianza:** P1 / clara.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:30` (contin�a hasta la l�nea 31).
- **Cita exacta completa:** �The evidence supports a planar composition in the tested regimes, not a global hybrid guarantee.�
- **Patr�n:** binary `supports X, not Y` correction.
- **Por qu� huele a IA en contexto:** this is the exact English counterpart of FM-012 and another clean �not X but Y� construction. It communicates an important boundary, yet its recurrence and symmetry make the prose feel templated.
- **C�mo arreglarla:** state the supported scope positively with its evidence class; move the missing global guarantee to a separate limitation sentence. Preserve the epistemic boundary without the antithetical template.

## P2 � Patrones de estilo y ritmo que merecen revisi�n

### FM-001

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:2` (contin�a hasta la l�nea 4).
- **Cita exacta completa:** �Este TFM eval�a una arquitectura h�brida e interpretable para formar coaliciones de robots heterog�neos y transportar una carga en modalidad Cargo.�
- **Patr�n:** apertura metadiscursiva de plantilla (`Este TFM eval�a...`) y acumulaci�n temprana de etiquetas abstractas.
- **Por qu� huele a IA en contexto:** es un arranque muy frecuente en res�menes generados porque permite rellenar el objeto despu�s del verbo `eval�a`. Tambi�n es una convenci�n acad�mica leg�tima y por eso la confianza es contextual, no una acusaci�n firme.
- **C�mo arreglarla:** considerar una apertura centrada directamente en el problema evaluado, la unidad experimental o la contribuci�n concreta; mantener `TFM` solo si la gu�a VIU exige que el g�nero del documento se explicite en la primera frase.

### FM-002

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:4` (contin�a hasta la l�nea 6).
- **Cita exacta completa:** �Combina juegos potenciales, cierre entero, umbrales de servicio, guardia planar de \emph{wrench}, control de pose, filtrado de seguridad, reparaci�n tras fallos, reserva de rutas y mensajer�a vecinal.�
- **Patr�n:** cat�logo nominal de nueve componentes con paralelismo uniforme.
- **Por qu� huele a IA en contexto:** la frase comprime la arquitectura como una lista exhaustiva y r�tmicamente regular. Los t�rminos son t�cnicos y leg�timos, pero la suma de nueve etiquetas sin relaci�n causal suena a inventario de palabras clave producido para maximizar cobertura.
- **C�mo arreglarla:** conservar solo los componentes nucleares en el resumen y agrupar los restantes por capa �decisi�n, control, seguridad y comunicaci�n� mediante relaciones funcionales. No sustituir unas etiquetas por sin�nimos; explicar c�mo se conectan.

### FM-004

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:10` (contin�a hasta la l�nea 12).
- **Cita exacta completa:** �La investigaci�n descompone el problema en SP0--SP8 y emplea demostraciones, or�culos acotados, baselines, ablaciones e intervalos de confianza del 95\,\%.�
- **Patr�n:** sujeto abstracto, verbo general (`emplea`) y lista metodol�gica de cinco piezas.
- **Por qu� huele a IA en contexto:** repite el patr�n de FM-002 con otra oraci�n-sumario: un sujeto institucional hace una acci�n general y despu�s enumera todos los sellos de rigor. Cada elemento es pertinente, pero la estructura parece una lista de comprobaci�n insertada en prosa.
- **C�mo arreglarla:** relacionar cada familia de evidencia con la pregunta que resuelve o reducir la lista a los dos rasgos metodol�gicos que distinguen este trabajo. Evitar reemplazar `emplea` por un verbo m�s solemne; el problema es la acumulaci�n, no el vocabulario aislado.

### FM-005

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:12` (contin�a hasta la l�nea 14).
- **Cita exacta completa:** �Los resultados formales delimitan equilibrios de asignaci�n, cuota y \emph{wrench}, estabilidad local con contactos fijos y terminaci�n finita de los juegos de reparaci�n y rutas.�
- **Patr�n:** regla de tres a dos niveles, nominalizaciones apiladas y verbo �nico extendido sobre objetos sem�nticamente distintos.
- **Por qu� huele a IA en contexto:** la frase forma una tr�ada impecable �equilibrios, estabilidad, terminaci�n� y dentro del primer miembro introduce otra tr�ada. `Delimitan` funciona bien con equilibrios, pero resulta menos natural con estabilidad y terminaci�n; esa simetr�a forzada es un indicio m�s fuerte que los t�rminos t�cnicos.
- **C�mo arreglarla:** asignar a cada clase de resultado su verbo preciso y romper la doble tr�ada. Priorizar en el resumen el resultado formal nuclear y condensar los resultados auxiliares sin fingir que todos comparten la misma operaci�n l�gica.

### FM-006

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:17` (contin�a hasta la l�nea 20).
- **Cita exacta completa:** �La campa�a Cargo integr� reclutamiento, acoplamiento, transporte planar reducido, obst�culo, fallo y reemplazo, y complet� 359 de 360 misiones sin intersecci�n carga--obst�culo durante el transporte.�
- **Patr�n:** cat�logo de seis etapas, paralelismo nominal y doble coordinaci�n con `y`.
- **Por qu� huele a IA en contexto:** la oraci�n intenta demostrar integraci�n enumerando cada bloque antes de dar el resultado. Es informativa, pero reproduce por tercera vez el molde �verbo general + lista larga + cifra de cierre�, un ritmo t�pico de s�ntesis generada.
- **C�mo arreglarla:** definir la misi�n integrada por su secuencia causal o por las dos interfaces m�s importantes, y dejar el resultado cuantitativo en una cl�usula independiente. Conservar fallo y reemplazo si son la evidencia distintiva; no listar componentes ya declarados en el primer p�rrafo.

### FM-007

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:20` (contin�a hasta la l�nea 21).
- **Cita exacta completa:** �No se sustent� la ventaja temporal prevista para el coste espacial.�
- **Patr�n:** impersonal refleja, negaci�n al inicio y resultado formulado por ausencia de sustento.
- **Por qu� huele a IA en contexto:** los generadores suelen usar pasivas impersonales para sonar cautos. Aqu� la forma es metodol�gicamente apropiada porque reporta un resultado negativo conforme a la matriz de evidencia, de modo que solo merece revisi�n por su repetici�n junto con FM-003 y FM-012.
- **C�mo arreglarla:** si el espacio lo permite, identificar el contraste o efecto que no alcanz� el criterio predefinido y usar un sujeto emp�rico concreto. No convertir el resultado negativo en una afirmaci�n de equivalencia o refutaci�n.

### FM-008

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:21` (contin�a hasta la l�nea 22).
- **Cita exacta completa:** �Retirar la seguridad redujo el �xito en 0.996 bajo obst�culo.�
- **Patr�n:** primera mitad de un par sint�ctico perfectamente paralelo con FM-009; nominalizaci�n del tratamiento como sujeto.
- **Por qu� huele a IA en contexto:** aislada es una frase cuantitativa eficaz. Junto a la siguiente forma una pareja casi generada por plantilla: infinitivo como sujeto + componente + `redujo` + pronombre/m�trica + efecto + condici�n.
- **C�mo arreglarla:** presentar ambas ablaciones dentro de una comparaci�n expl�citamente dise�ada o variar la estructura seg�n la relaci�n causal real. Nombrar la m�trica completa para que FM-009 no dependa de un pronombre.

### FM-009

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:22` (contin�a hasta la l�nea 23).
- **Cita exacta completa:** �Desactivar la reparaci�n lo redujo en 0.989 bajo fallo.�
- **Patr�n:** segunda mitad del paralelismo de FM-008 y pronombre resumidor (`lo`) para completar la simetr�a.
- **Por qu� huele a IA en contexto:** la variaci�n l�xica `retirar/desactivar` parece *synonym cycling* deliberado, mientras `lo` conserva el esqueleto id�ntico. La brevedad sacrifica claridad del referente para mantener la pareja r�tmica.
- **C�mo arreglarla:** repetir el nombre exacto de la m�trica si es necesario y elegir el verbo seg�n la operaci�n experimental, no para evitar repetir `retirar`. Si las dos ablaciones se comparan, explicitar que pertenecen a estratos distintos.

### FM-011

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:27` (contin�a hasta la l�nea 29).
- **Cita exacta completa:** �Un piloto cinem�tico tridimensional comprob� geometr�a y detect� bloqueos, no din�mica f�sica ni rendimiento industrial.�
- **Patr�n:** contraste el�ptico `verific� A y B, no C ni D`, alcance positivo/negativo comprimido y nombres vagos (`geometr�a`, `rendimiento`).
- **Por qu� huele a IA en contexto:** repite la estrategia de demostrar prudencia mediante una ant�tesis compacta. Adem�s, el verbo queda elidido en la parte negativa, lo que da una simetr�a pulida pero menos natural y menos precisa que dos afirmaciones independientes.
- **C�mo arreglarla:** nombrar qu� propiedad geom�trica se comprob� y qu� tipo de bloqueo se observ�; declarar despu�s, con verbo propio, los niveles que el piloto no valida. No ampliar el alcance de la evidencia.

### FM-013

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/01-summary.tex:32` (contin�a hasta la l�nea 34).
- **Cita exacta completa:** �Quedan fuera soporte tridimensional, contacto rueda--suelo, red m�vil, hardware y empuje mediante \emph{caging}.�
- **Patr�n:** conclusi�n mediante inventario negativo de cinco elementos y sujeto pospuesto/impersonal.
- **Por qu� huele a IA en contexto:** cerrar con �quedan fuera� seguido de una lista es una f�rmula segura y frecuente en res�menes generados. Aqu� los l�mites son concretos y obligatorios, por lo que el hallazgo es contextual; el olor surge de la acumulaci�n de otra lista y no de los conceptos.
- **C�mo arreglarla:** ordenar los l�mites por capa o prioridad y conservar solo los que cambian la interpretaci�n del resultado principal. Si todos deben aparecer, conectarlos con el tipo de evidencia que falta, no solo enumerarlos.

### FM-014

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:2` (contin�a hasta la l�nea 4).
- **Cita exacta completa:** �This master's thesis evaluates an interpretable hybrid architecture for forming coalitions of heterogeneous mobile robots and transporting one payload in Cargo mode.�
- **Patr�n:** formulaic document-opening frame (`This master's thesis evaluates...`).
- **Por qu� huele a IA en contexto:** it is a slot-fill opening common in generated abstracts, although it is also standard academic English. Its near one-to-one correspondence with FM-001 strengthens the mechanical-translation impression.
- **C�mo arreglarla:** consider opening directly with the evaluated problem, mechanism, or experimental unit. Keep the document label only if institutional style requires it.

### FM-015

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:4` (contin�a hasta la l�nea 6).
- **Cita exacta completa:** �It combines potential games, integer closure, service thresholds, a planar wrench guard, pose control, safety filtering, failure repair, route reservation, and neighbour messaging.�
- **Patr�n:** nine-item nominal catalogue with uniformly parallel syntax.
- **Por qu� huele a IA en contexto:** the sentence reads like keyword coverage rather than an account of how the layers interact. It also mirrors FM-002 exactly, including item order.
- **C�mo arreglarla:** retain the contribution�s core components and group the rest by functional layer; express at least one relationship between layers. Avoid synonym substitution as a cosmetic fix.

### FM-017

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:10` (contin�a hasta la l�nea 11).
- **Cita exacta completa:** �The study decomposes the problem into SP0--SP8 and uses proofs, paired worlds, bounded oracles, baselines, ablations, and 95\% confidence intervals.�
- **Patr�n:** abstract subject, generic verb (`uses`), and six-part methods checklist.
- **Por qu� huele a IA en contexto:** like FM-004, it packs recognised markers of rigour into a balanced list rather than relating them to the research design. `Paired worlds` adds one more item than the Spanish list, but the scaffold is unchanged.
- **C�mo arreglarla:** connect the evidence types to the claims they test or retain only the differentiating methodological features. Do not replace `uses` with inflated vocabulary; reduce or organise the inventory.

### FM-018

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:11` (contin�a hasta la l�nea 13).
- **Cita exacta completa:** �Formal results delimit assignment, quota, and wrench equilibria, local stability under fixed contacts, and finite termination of the repair and route games.�
- **Patr�n:** nested rule of three, stacked nominalisations, and one stretched verb for heterogeneous results.
- **Por qu� huele a IA en contexto:** it reproduces FM-005�s polished three-part symmetry. `Delimit` naturally modifies equilibria but is less idiomatic for stability and termination, suggesting that parallel shape overrode sentence-level precision.
- **C�mo arreglarla:** give each result class its precise verb and break the nested triad. Lead with the formal result most central to the contribution.

### FM-019

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:17` (contin�a hasta la l�nea 19).
- **Cita exacta completa:** �The Cargo campaign integrated recruitment, dynamic-unicycle docking, reduced planar transport, an obstacle, one failure, and replacement, completing 359 of 360 missions without payload--obstacle intersection during transport.�
- **Patr�n:** six-part catalogue followed by a participial result clause.
- **Por qu� huele a IA en contexto:** the `completing` clause is specific and therefore is not a superficial `-ing` analysis by itself. The concern is cumulative: a long inventory is made to flow seamlessly into a headline number, matching a common generated-summary cadence and FM-006�s structure.
- **C�mo arreglarla:** describe the mission as a causal sequence or retain only its distinguishing interfaces; place the completion result in its own finite clause or sentence. Do not delete the exact denominator or safety condition.

### FM-020

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:19` (contin�a hasta la l�nea 20).
- **Cita exacta completa:** �The predicted time advantage of the spatial cost was not supported.�
- **Patr�n:** passive negative-result formula.
- **Por qu� huele a IA en contexto:** `was not supported` is a common confidence-calibration construction. It is also the correct academic label for the claim in the evidence matrix, so the form should not be removed merely to sound less formal.
- **C�mo arreglarla:** if space permits, make the relevant comparison or estimated effect the grammatical subject. Preserve �not supported� unless the statistical evidence justifies a stronger label.

### FM-021

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:20` (contin�a hasta la l�nea 21).
- **Cita exacta completa:** �Removing safety reduced success by 0.996 under obstacles.�
- **Patr�n:** first sentence of a mirrored ablation pair; gerund treatment as subject.
- **Por qu� huele a IA en contexto:** it is clear in isolation, but with FM-022 it creates a templated pair whose only changes are component, effect size, and condition.
- **C�mo arreglarla:** present the two ablations under an explicit comparative relation or vary the structure according to their actual experimental strata. Name the success metric consistently.

### FM-022

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:21` (contin�a hasta la l�nea 22).
- **Cita exacta completa:** �Disabling repair reduced it by 0.989 under failure.�
- **Patr�n:** second half of the mirrored pair and pronoun-dependent compression.
- **Por qu� huele a IA en contexto:** `Removing/Disabling` looks like controlled synonym rotation around an identical skeleton. The pronoun `it` preserves the rhythm but weakens standalone precision.
- **C�mo arreglarla:** repeat the exact metric where ambiguity is possible and choose one experimental verb consistently unless the operations genuinely differ. State that the failure stratum differs from the obstacle stratum if needed.

### FM-024

- **Severidad / confianza:** P2 / probable.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:26` (contin�a hasta la l�nea 28).
- **Cita exacta completa:** �A three-dimensional kinematic pilot checked geometry and exposed deadlocks, but did not validate physical dynamics or industrial performance.�
- **Patr�n:** polished positive/negative concession (`did A and B, but did not C or D`) and vague objects.
- **Por qu� huele a IA en contexto:** the sentence balances two achievements against two exclusions with near-perfect symmetry. The limitation is real, but `checked geometry` and `industrial performance` are broad enough to sound like generic scope markers.
- **C�mo arreglarla:** name the geometric property and deadlock observation precisely; give the unvalidated layers their own sentence and verb. Keep the distinction between kinematic checking and physical validation.

### FM-026

- **Severidad / confianza:** P2 / contextual.
- **Ubicaci�n:** `thesis/sections/frontmatter/02-abstract.tex:31` (contin�a hasta la l�nea 33).
- **Cita exacta completa:** �Three-dimensional support, wheel--ground contact during transport, switching networks, hardware, and caging remain outside the validated scope.�
- **Patr�n:** five-item negative-scope catalogue as final sentence.
- **Por qu� huele a IA en contexto:** this is a conventional and useful limitations sentence, but it exactly mirrors FM-013�s list-ending strategy. After several inventories, another five-item catalogue reinforces the generated cadence.
- **C�mo arreglarla:** order the exclusions by layer or consequence and retain only those needed to interpret the central result. If all must remain, link each group to the evidence that is still missing.

## Patrones estructurales de conjunto

1. **Calco biling�e casi uno a uno.** Ambos textos tienen 16 oraciones, cuatro p�rrafos con distribuci�n **3/2/9/2**, el mismo orden argumental y casi los mismos moldes sint�cticos. La equivalencia de afirmaciones es deseable, pero no exige reproducir cada giro, lista y negaci�n. El ingl�s deber�a editarse como prosa acad�mica inglesa aut�noma despu�s de fijar la equivalencia de claims; de lo contrario, FM-014�FM-026 parecen traducciones mec�nicas de FM-001�FM-013.
2. **Inventarios acumulativos.** En cada idioma aparecen cuatro cat�logos extensos: componentes de arquitectura, m�todos de validaci�n, etapas de la misi�n y l�mites. Ninguna lista aislada es problem�tica, pero su recurrencia convierte el resumen en una sucesi�n de etiquetas nominales. La revisi�n debe decidir qu� inventario cumple cada funci�n y eliminar solapamientos.
3. **P�rrafo de resultados serial.** El tercer p�rrafo de cada idioma contiene nueve oraciones en el mismo orden: dos resultados formales/experimentales breves, integraci�n, resultado negativo, dos ablaciones paralelas, red, SP8 y piloto. Las longitudes s� var�an (espa�ol: 10�35 palabras; ingl�s: 9�37), por lo que **no** hay una uniformidad m�trica global grave. El olor procede de la secuencia id�ntica y del par de ablaciones construido con plantilla.
4. **Agentes abstractos repetidos.** `Este TFM eval�a`, `La investigaci�n descompone`, `Los resultados formales delimitan` y `La evidencia respalda` tienen equivalentes literales en ingl�s. Esta objetivaci�n es normal en escritura acad�mica, pero su repetici�n deja poca voz autoral y favorece nominalizaciones. Conviene cambiar solo donde permita nombrar el experimento, contraste o resultado concreto; no introducir primera persona por obligaci�n.
5. **Cautela mediante ant�tesis.** La prudencia se expresa repetidamente como `no se presenta`, `no se sustent�`, `no din�mica...`, `no una garant�a...` y sus calcos ingleses. La cautela est� exigida por `docs/04_CLAIMS_EVIDENCE.md` y debe conservarse; lo que debe variar es la forma ret�rica, alternando alcance positivo, resultado negativo concreto y limitaci�n independiente.
6. **Sin se�ales l�xicas fuertes.** No aparecen `delve`, `robust`, `comprehensive`, `leverage`, `pivotal`, `seamless`, met�foras promocionales, transiciones `Moreover/Furthermore/Additionally`, preguntas ret�ricas, emociones prefabricadas, atribuciones vagas ni conclusiones grandilocuentes. Los t�rminos `h�brida`, `interpretable`, `wrench`, `caging`, `baselines` y `or�culos` son t�cnicos o descriptivos y no deben marcarse de forma aislada.
7. **Sin synonym cycling general.** Solo el par `Retirar/Desactivar` �y `Removing/Disabling`� parece variaci�n controlada para mantener dos oraciones gemelas. En el resto, la repetici�n de t�rminos t�cnicos es preferible a buscar sin�nimos.
8. **Sin abuso de par�ntesis, encabezados o formato.** No hay parent�ticos de falsa precisi�n, negritas, emojis, listas con encabezados inline ni exceso de secciones en la prosa renderizada. `Resumen`, `Abstract` y los �ndices son encabezados institucionales, no andamiaje de IA.

## Archivos sin frases marcadas

### `thesis/config/metadata.tex`

- El t�tulo administrativo se reproduce por requisitos de portada, encabezado y metadatos PDF. La repetici�n es funcional, no synonym cycling ni redundancia narrativa.
- La lista de cinco palabras clave cumple el requisito VIU y no constituye una tr�ada forzada.
- El comentario interno es directo y no se renderiza. No requiere intervenci�n estil�stica.

### `thesis/sections/frontmatter/00-cover.tex`

- Las �nicas dos oraciones son comentarios t�cnicos sobre foliaci�n. Tienen sujeto y acci�n concretos, sin patrones detectables.
- Los comandos de paginaci�n no se auditan como lenguaje natural.

### `thesis/sections/frontmatter/03-contents.tex`

- Solo contiene comandos estructurales. No hay prosa ni puntuaci�n discursiva que pueda atribuirse a IA.

## Prioridad pr�ctica sugerida para la reparaci�n posterior

1. Corregir primero FM-010/FM-023 y FM-012/FM-025: son los indicios m�s claros y, adem�s, la vaguedad de `calidad` reduce precisi�n cient�fica.
2. Rehacer FM-003/FM-016 como clasificaci�n positiva con limitaci�n separada.
3. Desmontar los cat�logos FM-002/FM-015, FM-004/FM-017 y FM-006/FM-019 sin perder claims ni cifras.
4. Editar el ingl�s de manera idiom�tica e independiente, conservando equivalencia factual pero rompiendo el calco frase por frase.
5. Revisar al final el conteo VIU: el resumen espa�ol tiene 296 palabras, muy cerca del m�ximo de 300; cualquier reparaci�n debe evitar crecer o deber� compensarse con cortes.


## Parte B � Introducci�n, objetivos, hip�tesis y metodolog�a

### Criterio complementario

Se aplica el mismo modo `detect` de la Parte A. Las instrucciones de arreglo son operaciones editoriales propuestas, no cambios aplicados. No se consideran AI-ismos por s� solos la voz impersonal, los infinitivos de los objetivos, los criterios de refutaci�n, las listas en tablas ni la notaci�n t�cnica. S� se marcan cuando su repetici�n, simetr�a o acumulaci�n domina el ritmo.

## `thesis/sections/mainmatter/01-introduction.tex`

**Alcance:** archivo completo, incluidas citas y hoja de ruta; aproximadamente **43 oraciones**. **Puntuaci�n:** `:` = **1 en prosa** + **1 falso positivo** en `\label{sec:introduction}`; `;` = **4 en prosa**; `�` = **0**; `--` = **0**.

**Patrones estructurales:** ocho p�rrafos de cadencia bastante uniforme; predominan oraciones declarativas de extensi�n media/larga, inventarios de tres o cuatro elementos y cierres cautelares negativos. No hay artefactos de chatbot ni vocabulario promocional fuerte.

- **IN-001 � P2 � contextual � `01-introduction.tex:4-5`** � **Cita:** �La intralog�stica concentra buena parte del uso profesional de los robots m�viles aut�nomos (AMR).� **Patr�n/por qu�:** apertura panor�mica y cuantificador vago; retrasa el dato concreto y �buena parte� no fija magnitud. **C�mo:** abrir con la cifra IFR y derivar de ella el peso de la intralog�stica.
- **IN-002 � P2 � contextual � `01-introduction.tex:8-11`** � **Cita:** �El sistema Kiva y las plataformas comerciales de Geek+ y MiR ilustran su aplicaci�n en almacenamiento, preparaci�n de pedidos y abastecimiento interno \parencite{wurman2008coordinating,geekplusWarehouseSolutions,mirInternalTransport}.� **Patr�n/por qu�:** doble tr�ada y acumulaci�n de nombres/citas sin indicar qu� caso acredita cada uso. **C�mo:** asociar cada fuente con un uso concreto o conservar un ejemplo suficientemente explicado.
- **IN-003 � P2 � probable � `01-introduction.tex:12`** � **Cita:** �Estas operaciones suelen partir de cargas, interfaces y recorridos normalizados.� **Patr�n/por qu�:** generalizaci�n vaga en tr�ada; �suelen� comprime una premisa decisiva sin ejemplo ni referencia. **C�mo:** especificar las condiciones normalizadas y cu�l rompe el TFM.
- **IN-004 � P2 � clara � `01-introduction.tex:14`** � **Cita:** �Este TFM se ocupa de las cargas que rompen esa regularidad.� **Patr�n/por qu�:** metanarraci�n de documento y an�fora gen�rica. **C�mo:** formular directamente la clase de carga y su diferencia operacional.
- **IN-005 � P1 � probable � `01-introduction.tex:14-16`** � **Cita:** �Un bastidor voluminoso, un subconjunto pesado, una pieza fr�gil o un objeto con una pose de entrega precisa puede rebasar la capacidad, la superficie de apoyo o la maniobrabilidad de un AMR.� **Patr�n/por qu�:** enumeraci�n doble 4�3, muy pulida, sin correspondencia entre ejemplos y restricciones. **C�mo:** dividir por mecanismo de fallo o conservar uno o dos ejemplos vinculados con variables del modelo.
- **IN-006 � P2 � contextual � `01-introduction.tex:23-25`** � **Cita:** �Las taxonom�as de asignaci�n multi-robot distinguen las tareas simult�neas, la heterogeneidad de recursos y la dependencia entre decisiones \parencite{gerkeyMataric2004MRTA,korsahStentzDias2013iTax}.� **Patr�n/por qu�:** regla de tres bibliogr�fica que presenta un inventario cerrado. **C�mo:** nombrar la categor�a taxon�mica exacta aplicable y explicar su consecuencia para la formulaci�n.
- **IN-007 � P1 � probable � `01-introduction.tex:27-31`** � **Cita:** �Cubrir una cuota o un vector de recursos todav�a no acredita la ejecuci�n f�sica: los robots han de ocupar contactos compatibles, producir las fuerzas y momentos requeridos, regular la pose y respetar los l�mites de actuaci�n durante el movimiento \parencite{parkerTang2006ASyMTRe,zhangParker2013IQASyMTRe,alonsomora2017transport}.� **Patr�n/por qu�:** colon seguido de cuatro predicados paralelos; mezcla factibilidad de contacto, `wrench` y control. **C�mo:** separar requisitos mec�nicos y de control y asignar a cada afirmaci�n su fuente.
- **IN-008 � P2 � probable � `01-introduction.tex:32-33`** � **Cita:** �Una asignaci�n v�lida en t�rminos l�gicos puede fallar al acoplarse, bloquearse ante un obst�culo o perder su viabilidad cuando se retira un robot.� **Patr�n/por qu�:** tr�ada de fallos con paralelismo verbal y sin conexi�n causal. **C�mo:** enlazar cada fallo con su capa o con el SP que lo valida.
- **IN-009 � P1 � clara � `01-introduction.tex:35-41`** � **Cita:** �Las subastas distribuidas asignan tareas \parencite{gerkeyMataric2002MURDOCH,choiBrunetHow2009CBBA}. Los juegos de coalici�n describen preferencias y recursos \parencite{chenSun2012Coalition,dutta2021hedonic}; ASyMTRe comprueba composiciones funcionalmente ejecutables \parencite{parkerTang2006ASyMTRe,zhangParker2013IQASyMTRe}; y el control cooperativo mueve grupos ya constituidos \parencite{alonsomora2017transport}.� **Patr�n/por qu�:** inventario sim�trico de familias y dos puntos y coma; cuatro veces �sujeto + verbo + objeto�. **C�mo:** usar una tabla cr�tica o desarrollar la interfaz que falta entre familias concretas.
- **IN-010 � P2 � probable � `01-introduction.tex:42-43`** � **Cita:** �Cada familia parte de variables y supuestos propios, de modo que sus garant�as no pasan sin m�s a las dem�s capas.� **Patr�n/por qu�:** transici�n causal formularia y abstracciones sin referente preciso. **C�mo:** dar un ejemplo de garant�a y del supuesto que deja de cumplirse.
- **IN-011 � P1 � contextual � `01-introduction.tex:43-45`** � **Cita:** �En el corpus verificado no se encontr� un m�todo que reuniera la decisi�n de coalici�n con la factibilidad mec�nica, el movimiento, la seguridad, la reparaci�n y la comunicaci�n imperfecta.� **Patr�n/por qu�:** brecha por ausencia y lista de seis capacidades; puede parecer novedad fabricada si no se ven protocolo y criterio de inclusi�n. **C�mo:** remitir al corpus y definir qu� cuenta como �reunir� las capas.
- **IN-012 � P2 � contextual � `01-introduction.tex:45-47`** � **Cita:** �Esta conclusi�n se limita a la revisi�n documentada y no afirma la inexistencia universal de ese m�todo.� **Patr�n/por qu�:** descargo metadiscursivo y negaci�n defensiva aut�noma. **C�mo:** integrar el alcance en la frase anterior.
- **IN-013 � P2 � clara � `01-introduction.tex:49`** � **Cita:** �Este trabajo hace expl�citas las interfaces entre esas capas.� **Patr�n/por qu�:** metanarraci�n y verbo inflado que no identifica la interfaz. **C�mo:** nombrar la variable o salida que enlaza las capas.
- **IN-014 � P2 � probable � `01-introduction.tex:49-50`** � **Cita:** �Cada robot revisa su decisi�n con estado propio, percepci�n local y mensajes de sus vecinos.� **Patr�n/por qu�:** tr�ada can�nica reutilizada casi literalmente en metodolog�a; funciona como eslogan. **C�mo:** definir una vez observaciones y mensajes y remitir despu�s a esa definici�n.
- **IN-015 � P1 � probable � `01-introduction.tex:50-52`** � **Cita:** �Cuando el cierre entero, un agregado por carga, una guardia f�sica, el reparto de esfuerzo o un registro consultan informaci�n global, esa dependencia permanece visible.� **Patr�n/por qu�:** cinco sujetos y cierre abstracto; �permanece visible� evita explicar c�mo se registra. **C�mo:** llevar las dependencias a una tabla componente�informaci�n�fase.
- **IN-016 � P1 � clara � `01-introduction.tex:52-55`** � **Cita:** �Los optimizadores centralizados act�an como or�culos, certificados o referencias en instancias acotadas, no como coordinadores de la operaci�n.� **Patr�n/por qu�:** tr�ada parcialmente sin�nima y contraste �A, no B�. **C�mo:** usar el t�rmino exacto para cada funci�n y declarar aparte que no intervienen durante la operaci�n.
- **IN-017 � P2 � clara � `01-introduction.tex:55-56`** � **Cita:** �La arquitectura es, por ello, h�brida.� **Patr�n/por qu�:** transici�n mec�nica y recapitulaci�n de una sola etiqueta. **C�mo:** definir �h�brida� en la oraci�n anterior o sustituir la etiqueta por la propiedad concreta.
- **IN-018 � P2 � probable � `01-introduction.tex:56-58`** � **Cita:** �Su evaluaci�n determina hasta d�nde puede formar coaliciones y completar el transporte, qu� garant�as conserva cada componente y cu�nto cuesta sustituir informaci�n global por coordinaci�n vecinal.� **Patr�n/por qu�:** tr�ada de preguntas indirectas y promesa amplia sin m�tricas. **C�mo:** reemplazar cada cl�usula por la m�trica o hip�tesis que la responde.
- **IN-019 � P2 � probable � `01-introduction.tex:60-62`** � **Cita:** �SP0, SP1 y SP2 tratan la asignaci�n uno a uno, las cuotas variables y el servicio heterog�neo.� **Patr�n/por qu�:** correspondencia 3�3 demasiado limpia dentro de un p�rrafo ya enumerativo. **C�mo:** explicar el cambio incremental mediante una relaci�n causal.
- **IN-020 � P1 � probable � `01-introduction.tex:62-64`** � **Cita:** �SP3 y SP4 a�aden el certificado planar de \emph{wrench}, el acoplamiento y el control de pose; de SP5 a SP8 se estudian obst�culos, fallos, tr�fico y comunicaci�n imperfecta.� **Patr�n/por qu�:** punto y coma, dos listas yuxtapuestas y pasiva refleja. **C�mo:** dividir por bloque y explicar qu� salida del primero habilita el segundo.
- **IN-021 � P2 � probable � `01-introduction.tex:64-65`** � **Cita:** �En cada paso se declaran el modelo, la informaci�n disponible, la m�trica y el nivel de evidencia.� **Patr�n/por qu�:** pasiva refleja y promesa gen�rica en lista de cuatro. **C�mo:** remitir a la tabla o protocolo donde se declaran.
- **IN-022 � P1 � probable � `01-introduction.tex:66-67`** � **Cita:** �Las propiedades formales se apoyan en demostraciones y enumeraciones. La calidad se mide con or�culos acotados, comparadores, ablaciones y experimentos pareados.� **Patr�n/por qu�:** dos pasivas paralelas con sustantivos abstractos y listas. **C�mo:** nombrar la propiedad y el estimando concretos.
- **IN-023 � P2 � probable � `01-introduction.tex:68-70`** � **Cita:** �Una misi�n integrada recorre la cadena completa, mientras que un piloto industrial tridimensional revela bloqueos geom�tricos y cinem�ticos que los escenarios sint�ticos no representan.� **Patr�n/por qu�:** contraste equilibrado con �mientras que� y objetos vagos. **C�mo:** nombrar el bloqueo observado o la pregunta distinta de cada validaci�n.
- **IN-024 � P2 � probable � `01-introduction.tex:72`** � **Cita:** �La validaci�n f�sica se concentra en la modalidad Cargo soportada.� **Patr�n/por qu�:** nominalizaci�n y apertura formularia. **C�mo:** decir qu� parte de Cargo se valida y con qu� modelo.
- **IN-025 � P1 � clara � `01-introduction.tex:74-76`** � **Cita:** �El modelo no incluye soporte tridimensional, interacci�n entre rueda y suelo ni percepci�n completa; tampoco valida agarre f�sico o empuje por confinamiento geom�trico.� **Patr�n/por qu�:** dos listas negativas unidas por punto y coma y �tampoco�; mezcla ausencias de modelo y de validaci�n. **C�mo:** separar supuestos y validaciones pendientes.
- **IN-026 � P1 � probable � `01-introduction.tex:76-78`** � **Cita:** �Las garant�as obtenidas pertenecen a componentes concretos y no constituyen una prueba de convergencia, estabilidad o seguridad para todo el sistema h�brido.� **Patr�n/por qu�:** contraste negativo y tr�ada de garant�as formales distintas. **C�mo:** afirmar qu� proposici�n vale para qu� componente y remitir cada exclusi�n a su secci�n.
- **IN-027 � P2 � probable � `01-introduction.tex:78-79`** � **Cita:** �Los resultados solo se extienden a los modelos, tama�os, geometr�as y reg�menes de comunicaci�n evaluados.� **Patr�n/por qu�:** descargo gen�rico de cuatro elementos sin dominio concreto. **C�mo:** indicar rangos o remitir a la tabla experimental.
- **IN-028 � P1 � probable � `01-introduction.tex:81-86`** � **Cita:** �Los cap�tulos siguientes separan objetivos, hip�tesis, metodolog�a y fundamentos te�ricos antes de presentar la evidencia. Los Cap�tulos~2 a~5 cubren esos cuatro elementos. El Cap�tulo~6 contiene la formulaci�n, los resultados y las validaciones integrada e industrial. El Cap�tulo~7 contrasta los objetivos y las hip�tesis con la evidencia, fija las limitaciones y plantea trabajo futuro. Las demostraciones y el material de reproducibilidad quedan en los anexos.� **Patr�n/por qu�:** hoja de ruta formularia, recapitulaci�n redundante y varias tr�adas; cinco frases metron�micas con �cap�tulo(s)� como sujeto. **C�mo:** eliminar la segunda frase y conservar solo la l�gica estructural que el �ndice no muestra.

## `thesis/sections/mainmatter/02-objectives.tex`

**Alcance:** archivo completo, encabezados y cinco objetivos; aproximadamente **15 oraciones**. **Puntuaci�n:** `:` = **0 en prosa** + **1 falso positivo** en `\label{sec:objectives}`; `;` = **0**; `�` = **0**; `--` = **0**.

**Patrones estructurales:** la lista numerada es obligatoria y no es AI-ismo por s� sola. El olor procede de que los cinco objetivos repiten infinitivo + inventario + criterio, casi todos en dos o tres oraciones de longitud parecida. Hay alta densidad de series de cuatro a siete elementos.

- **OB-001 � P2 � probable � `02-objectives.tex:4-6`** � **Cita:** �La formaci�n de coaliciones solo resulta �til si conduce a un transporte ejecutable. Por esta raz�n, los objetivos abarcan la decisi�n estrat�gica, las restricciones f�sicas, los fallos y la comunicaci�n.� **Patr�n/por qu�:** apertura condicional seguida de transici�n mec�nica y lista de cuatro. **C�mo:** formular directamente el nexo entre coalici�n y ejecuci�n, y eliminar �Por esta raz�n�.
- **OB-002 � P1 � probable � `02-objectives.tex:10-13`** � **Cita:** �Desarrollar y evaluar una arquitectura h�brida e interpretable que combine decisiones estrat�gicas locales y comunicaci�n vecinal con cierres enteros y guardias f�sicas para formar coaliciones de robots m�viles aut�nomos y transportar cargas heterog�neas.� **Patr�n/por qu�:** objetivo sobredenso, dos adjetivos de valoraci�n y cadena de componentes/finalidades. **C�mo:** separar el objeto desarrollado de los dos resultados medidos y definir �h�brida� mediante sus l�mites.
- **OB-003 � P2 � probable � `02-objectives.tex:13-14`** � **Cita:** �Medir su factibilidad, calidad de la soluci�n, respuesta ante perturbaciones y coste de informaci�n frente a referencias globales.� **Patr�n/por qu�:** cuatro nominalizaciones y referente vago �su�. **C�mo:** sustituir cada r�tulo por una m�trica o remitir a la tabla de m�tricas.
- **OB-004 � P2 � contextual � `02-objectives.tex:26-27`** � **Cita:** �Caracterizar la formaci�n de coaliciones en el caso homog�neo uno a uno, con cuotas variables y con servicio operacional heterog�neo.� **Patr�n/por qu�:** escalera de tres casos con sintaxis perfectamente paralela. **C�mo:** mantener los SP, pero expresar el cambio de hip�tesis entre casos.
- **OB-005 � P1 � probable � `02-objectives.tex:27-29`** � **Cita:** �Determinar las condiciones de realizabilidad, cierre entero y equilibrio, y medir la p�rdida de calidad frente a referencias globales bajo abundancia y escasez.� **Patr�n/por qu�:** dos objetivos en una oraci�n, tr�ada inicial y extremos binarios �abundancia/escasez�. **C�mo:** separar el resultado formal de la comparaci�n emp�rica y nombrar la m�trica de calidad.
- **OB-006 � P2 � contextual � `02-objectives.tex:31-33`** � **Cita:** �Construir un certificado de factibilidad mec�nica para la modalidad Cargo planar soportada a partir de la geometr�a de contacto, la matriz de agarre, los l�mites de actuaci�n y el residual normalizado de \emph{wrench}.� **Patr�n/por qu�:** lista t�cnica de cuatro; leg�tima, pero acumula entradas sin mostrar su relaci�n. **C�mo:** mantener todos los t�rminos y definir cu�l es dato, restricci�n y salida del certificado.
- **OB-007 � P2 � probable � `02-objectives.tex:34-35`** � **Cita:** �Vincular el certificado con el acoplamiento de robots diferenciales y con el servocontrol de pose dentro del dominio donde se acredita estabilidad local.� **Patr�n/por qu�:** verbo abstracto �vincular� y pasiva impersonal �se acredita�. **C�mo:** indicar la interfaz matem�tica que conecta certificado, acoplamiento y control.
- **OB-008 � P2 � contextual � `02-objectives.tex:37-38`** � **Cita:** �Medir la respuesta de las coaliciones ante obst�culos, un fallo simple y conflictos de circulaci�n.� **Patr�n/por qu�:** tr�ada de perturbaciones; convencional para un objetivo, pero repetida con otros cat�logos. **C�mo:** relacionar cada perturbaci�n con su endpoint o SP.
- **OB-009 � P2 � probable � `02-objectives.tex:38-39`** � **Cita:** �Registrar colisiones, progreso, bloqueos, restauraci�n del certificado y tiempo de recuperaci�n.� **Patr�n/por qu�:** inventario de cinco m�tricas heterog�neas. **C�mo:** agrupar seguridad, vivacidad y recuperaci�n o remitir a la tabla de m�tricas.
- **OB-010 � P2 � contextual � `02-objectives.tex:39-40`** � **Cita:** �La exclusi�n l�gica del tr�fico discreto se evaluar� por separado de la seguridad f�sica continua.� **Patr�n/por qu�:** pasiva futura y contraste binario pulido. La separaci�n es cient�ficamente necesaria. **C�mo:** conservar la distinci�n, pero indicar qu� prueba corresponde a cada nivel.
- **OB-011 � P1 � clara � `02-objectives.tex:42-44`** � **Cita:** �Determinar c�mo afectan el tama�o del sistema, el alcance limitado de la comunicaci�n, el retardo y la p�rdida de paquetes a la observabilidad, la calidad estrat�gica, el coste computacional y el volumen de mensajes.� **Patr�n/por qu�:** matriz 4�4 comprimida en prosa, de cadencia muy generada. **C�mo:** llevar factores y respuestas a una tabla/dise�o factorial y dejar aqu� la relaci�n primaria.
- **OB-012 � P1 � probable � `02-objectives.tex:44-46`** � **Cita:** �Comparar la coordinaci�n vecinal por eventos y la retransmisi�n peri�dica con informaci�n perfecta y con un or�culo exhaustivo, usado solo cuando certifique su soluci�n.� **Patr�n/por qu�:** paralelismo A/B frente a C/D y participial de salvedad al final. **C�mo:** identificar comparaciones preespecificadas y trasladar la condici�n del or�culo a una frase propia.
- **OB-013 � P1 � clara � `02-objectives.tex:48-49`** � **Cita:** �Integrar reclutamiento, cierre de coalici�n, acoplamiento, transporte, seguridad y reemplazo tras un fallo en una misi�n Cargo.� **Patr�n/por qu�:** cat�logo de seis etapas que usa �integrar� como verbo contenedor. **C�mo:** describir la secuencia causal o la interfaz cr�tica que convierte las etapas en una misi�n.
- **OB-014 � P2 � probable � `02-objectives.tex:49-51`** � **Cita:** �Usar ablaciones para identificar los componentes necesarios y acotar la transferencia de resultados al piloto industrial geom�trico y cinem�tico.� **Patr�n/por qu�:** dos finalidades abstractas y densidad de calificativos. **C�mo:** nombrar la decisi�n que tomar� cada ablaci�n y la propiedad concreta cuya transferencia se limita.

## `thesis/sections/mainmatter/03-hypotheses.tex`

**Alcance:** archivo completo, HP y H1a�H5b; aproximadamente **28 oraciones**. **Puntuaci�n:** `:` = **0 en prosa** + **1 falso positivo** en `\label{sec:hypotheses}`; `;` = **1 en prosa**; `�` = **0**; `--` = **0**.

**Patr�n estructural principal:** nueve hip�tesis usan casi la misma secuencia �afirmaci�n ? condici�n de apoyo/refutaci�n�. Los criterios son necesarios; la uniformidad l�xica (`recibir� apoyo`, `quedar� sin apoyo`, `para sustentar`, `perder� apoyo`, `se refutar�`) hace visible una plantilla. Una tabla separada de estimando/criterio de rechazo conservar�a rigor y romper�a la repetici�n.

- **HP-001 � P2 � clara � `03-hypotheses.tex:4-6`** � **Cita:** �Este trabajo parte de una hip�tesis principal sobre la arquitectura completa y la descompone en afirmaciones contrastables para las capas estrat�gica, mec�nica, operacional y de red.� **Patr�n/por qu�:** metanarraci�n y lista de cuatro capas. **C�mo:** presentar HP directamente y explicar despu�s la descomposici�n.
- **HP-002 � P2 � probable � `03-hypotheses.tex:6-7`** � **Cita:** �Cada una se eval�a dentro de los supuestos del subproblema correspondiente, mediante an�lisis formal, experimentos pareados o ablaciones.� **Patr�n/por qu�:** pasiva refleja y tr�ada metodol�gica. **C�mo:** remitir al protocolo que asigna evidencia a cada hip�tesis.
- **HP-003 � P2 � clara � `03-hypotheses.tex:7-9`** � **Cita:** �Por tanto, una propiedad verificada en una capa no se extiende autom�ticamente al sistema integrado.� **Patr�n/por qu�:** transici�n mec�nica y descargo negativo. **C�mo:** unir la limitaci�n al alcance de la frase anterior o dar un ejemplo.
- **HP-004 � P1 � clara � `03-hypotheses.tex:14-19`** � **Cita:** �Cuando la flota disponga de recursos suficientes, la configuraci�n Cargo sea factible en el plano y el horizonte sea compatible con la duraci�n de la tarea, una arquitectura h�brida que combine decisiones estrat�gicas locales, comunicaci�n vecinal, cierres enteros y guardias f�sicas expl�citas formar� coaliciones factibles y completar� la misi�n de transporte dentro de una regi�n de operaci�n medible.� **Patr�n/por qu�:** tres precondiciones + cuatro componentes + dos desenlaces en una sola oraci�n, con simetr�a excesiva. **C�mo:** separar dominio de validez, mecanismo y predicci�n medible.
- **HP-005 � P2 � probable � `03-hypotheses.tex:19-20`** � **Cita:** �La comparaci�n con referencias globales cuantificar� la p�rdida de calidad y el coste de la informaci�n.� **Patr�n/por qu�:** nominalizaciones gen�ricas sin m�trica ni comparador. **C�mo:** nombrar los estimandos y las referencias.
- **HP-006 � P2 � probable � `03-hypotheses.tex:20-22`** � **Cita:** �El apoyo a HP exige identificar una regi�n reproducible de �xito y confirmar, mediante ablaciones, la contribuci�n de sus bloques cr�ticos.� **Patr�n/por qu�:** metaevaluaci�n, nominalizaciones y �bloques cr�ticos� indeterminado. **C�mo:** definir regi�n, criterio y ablaciones en t�rminos observables.
- **HP-007 � P1 � clara � `03-hypotheses.tex:22-23`** � **Cita:** �El enunciado no presupone estabilidad global del sistema h�brido, una ejecuci�n enteramente distribuida ni validez en hardware.� **Patr�n/por qu�:** descargo negativo en tr�ada. **C�mo:** expresar el dominio positivo de HP y trasladar las tres exclusiones a alcance/limitaciones.
- **HP-008 � P2 � probable � `03-hypotheses.tex:34-37`** � **Cita:** �En condiciones de escasez, el cierre por ranking y cu�rum (QR) aplicado a la relajaci�n de Smith reducir� la fracci�n de robots que permanece en coaliciones parciales. La evidencia no apoyar� esta afirmaci�n si el efecto pareado frente a Smith continuo es nulo o adverso.� **Patr�n/por qu�:** pareja formularia afirmaci�n�no apoyo y disyunci�n �nulo o adverso�. **C�mo:** declarar directamente estimando, direcci�n y criterio de decisi�n.
- **HP-009 � P2 � clara � `03-hypotheses.tex:40-42`** � **Cita:** �Con el cierre QR fijado, el beneficio de cu�rum aumentar� el valor de las cargas completadas frente al beneficio lineal. Solo recibir� apoyo si la comparaci�n pareada favorece al incentivo de cu�rum.� **Patr�n/por qu�:** repetici�n casi literal de la plantilla anterior y �nfasis de confianza �Solo�. **C�mo:** fusionar predicci�n y criterio medible sin narrar el acto de �recibir apoyo�.
- **HP-010 � P2 � contextual � `03-hypotheses.tex:45-47`** � **Cita:** �La guardia vectorial de \emph{wrench} planar reducir� las falsas aceptaciones respecto al criterio escalar, sin una p�rdida sistem�tica de cobertura �til en los mundos evaluados.� **Patr�n/por qu�:** concesi�n equilibrada �mejora X sin perder Y�. Es una hip�tesis v�lida, pero su forma es muy t�pica. **C�mo:** definir por separado el endpoint primario y el margen de no deterioro.
- **HP-011 � P2 � probable � `03-hypotheses.tex:47-48`** � **Cita:** �La afirmaci�n quedar� sin apoyo si los falsos positivos no disminuyen o si la abstenci�n del filtro impide su uso operativo.� **Patr�n/por qu�:** tercera variante de �sin apoyo� y dos ramas sim�tricas. **C�mo:** fijar umbrales o reglas de decisi�n distintas para falsos positivos y abstenci�n.
- **HP-012 � P2 � clara � `03-hypotheses.tex:53-54`** � **Cita:** �Para sustentar esta ventaja, el intervalo de confianza del efecto temporal deber� excluir cero en la direcci�n favorable.� **Patr�n/por qu�:** direcci�n metadiscursiva sobre c�mo interpretar el resultado. **C�mo:** declarar el criterio estad�stico junto al estimando en el protocolo.
- **HP-013 � P2 � contextual � `03-hypotheses.tex:54-55`** � **Cita:** �Una tasa de �xito coincidente, por s� sola, no demostrar� equivalencia.� **Patr�n/por qu�:** cautela negativa con inciso de �nfasis. Cient�ficamente correcta. **C�mo:** indicar qu� an�lisis de equivalencia ser�a necesario o moverlo a amenazas/estad�stica.
- **HP-014 � P1 � probable � `03-hypotheses.tex:60-62`** � **Cita:** �La hip�tesis perder� apoyo si alguna instancia recuperable no restaura el certificado o si la diferencia de �xito no es favorable; el agotamiento del horizonte se registrar� como fallo de recuperaci�n.� **Patr�n/por qu�:** dos condicionales sim�tricos, punto y coma y cierre administrativo; tres criterios distintos comprimidos. **C�mo:** separar restauraci�n, �xito y censura/timeout en reglas de decisi�n propias.
- **HP-015 � P2 � contextual � `03-hypotheses.tex:65-67`** � **Cita:** �En el cat�logo binario de SP8, el coste de una activaci�n local crecer� con el grado vecinal, mientras que el del or�culo exhaustivo implementado crecer� con el n�mero de perfiles.� **Patr�n/por qu�:** contraste perfectamente equilibrado con �mientras que�. **C�mo:** expresar ambas complejidades con variables/�rdenes o estimandos separados.
- **HP-016 � P2 � probable � `03-hypotheses.tex:67-68`** � **Cita:** �La separaci�n deber� observarse dentro del dominio en el que el or�culo certifica su soluci�n.� **Patr�n/por qu�:** pasiva refleja y criterio vago �la separaci�n�. **C�mo:** definir la separaci�n cuantitativa y el dominio certificado.
- **HP-017 � P1 � clara � `03-hypotheses.tex:71-72`** � **Cita:** �La tasa global de perfiles libres de conflicto del m�todo con retransmisi�n peri�dica no colapsar� al aumentar la escala en el dominio ensayado.� **Patr�n/por qu�:** hip�tesis negativa con verbo dram�tico y no cuantitativo �colapsar�. **C�mo:** sustituirlo por un umbral o pendiente preespecificada.
- **HP-018 � P2 � probable � `03-hypotheses.tex:72-74`** � **Cita:** �La hip�tesis se refutar� si la tasa alcanza cero en alg�n tama�o o si su deterioro contradice la conservaci�n postulada.� **Patr�n/por qu�:** cierre de refutaci�n con dos ramas y referente abstracto �conservaci�n postulada�. **C�mo:** declarar la regla num�rica completa sin narrar �se refutar�.
- **HP-019 � P2 � probable � `03-hypotheses.tex:76-78`** � **Cita:** �El an�lisis conservar� las colisiones, los fallos de convergencia y los agotamientos del horizonte.� **Patr�n/por qu�:** tr�ada de incidencias con sujeto abstracto. **C�mo:** indicar que permanecen en el denominador y c�mo se codifica cada una.
- **HP-020 � P1 � contextual � `03-hypotheses.tex:78-79`** � **Cita:** �Las pruebas de SP5 y SP7 se interpretar�n como evidencia local sobre seguridad y tr�fico, no como una garant�a global del sistema integrado.� **Patr�n/por qu�:** pasiva futura y ant�tesis �X, no Y�, repetida en otras secciones. **C�mo:** afirmar el alcance positivo por SP y dar la limitaci�n global en otra oraci�n.
- **HP-021 � P1 � clara � `03-hypotheses.tex:27-74`** � **Cita estructural:** H1a�H5b repiten, con m�nimas variaciones, �constituir� un contraejemplo�, �no apoyar�, �solo recibir� apoyo�, �quedar� sin apoyo�, �para sustentar�, �perder� apoyo�, �deber� observarse� y �se refutar�. **Patr�n/por qu�:** andamiaje serial de calibraci�n de confianza; la repetici�n es m�s detectable que cualquier palabra aislada. **C�mo:** conservar los criterios, pero moverlos a una tabla con columnas hip�tesis, estimando y regla de decisi�n.

## `thesis/sections/mainmatter/04-methodology.tex`

**Alcance:** archivo completo, incluidas dos ecuaciones, dos figuras, textos internos y dos tablas; aproximadamente **54 oraciones/captions de prosa corrida + 26 celdas textuales**, unas **80 unidades**. **Puntuaci�n:** `:` = **5 en prosa explicativa**; los dem�s **19** son etiquetas, sintaxis TikZ o notaci�n de conjunto; `;` = **16 visibles** (**6 en cuerpo**, **8 en tabla**, **2 en r�tulos de figura**) + **61 terminadores de comandos TikZ**; `�` = **0**; `--` = **25**, de los cuales **21 son operadores de trayecto TikZ** y **4 son rangos/relaciones t�cnicas** (`SP0--SP8` dos veces, `robot--carga`, `rueda--suelo`). Ning�n `--` act�a como raya ret�rica.

**Patrones estructurales:** la metodolog�a es m�s variada por ecuaciones, figuras y tablas. El olor se concentra en aperturas impersonales, cat�logos que vuelven a duplicar tablas, contrastes negativos Cargo/caging y secuencias �se fija/se verifica/se reporta�. Los puntos y coma de tablas y los `--` t�cnicos son falsos positivos; no deben �corregirse� como AI-ismos sin considerar TeX.

- **ME-001 � P2 � probable � `04-methodology.tex:4-5`** � **Cita:** �Se estudia una flota de AMR heterog�neos que forma coaliciones y transporta cargas entre una pose inicial y una pose objetivo.� **Patr�n/por qu�:** apertura impersonal formularia. **C�mo:** usar como sujeto la flota/modelo o definir primero la unidad experimental.
- **ME-002 � P2 � contextual � `04-methodology.tex:5-7`** � **Cita:** �Caging se define como extensi�n secundaria y no hereda la validaci�n de Cargo.� **Patr�n/por qu�:** pasiva de definici�n y contraste negativo. La delimitaci�n es necesaria, pero repite el molde de cautela. **C�mo:** definir positivamente el alcance propio de caging y declarar aparte qu� evidencia pertenece a Cargo.
- **ME-003 � P1 � probable � `04-methodology.tex:7-10`** � **Cita:** �El trabajo cubre decisi�n estrat�gica, factibilidad f�sica, movimiento, obst�culos, fallo de un robot, tr�fico y comunicaci�n imperfecta. Quedan fuera el contacto tridimensional, la percepci�n real y la validaci�n en hardware.� **Patr�n/por qu�:** cat�logo positivo de siete seguido de cat�logo negativo de tres; apertura de alcance tipo checklist. **C�mo:** organizar incluido/excluido por capa en una tabla y reservar la prosa para la frontera decisiva.
- **ME-004 � P1 � clara � `04-methodology.tex:30-32`** � **Cita:** �La Figura~\ref{fig:method-unicycle-fleet} muestra la interpretaci�n geom�trica del modelo: la orientaci�n fija la direcci�n de avance de cada AMR, mientras que \(v_i\) y \(\omega_i\) gobiernan su traslaci�n y giro, respectivamente.� **Patr�n/por qu�:** metanarraci�n de figura, colon, �mientras que� y pareja �respectivamente�; exceso de simetr�a. **C�mo:** citar la figura y formular dos relaciones directas, sin escenificar la explicaci�n con dos puntos.
- **ME-005 � P2 � contextual � `04-methodology.tex:100-102`** � **Cita:** �Cada AMR tiene pose planar, velocidad longitudinal y velocidad angular.� **Patr�n/por qu�:** tr�ada en caption. Es compacta y leg�tima, pero repite la regla de tres. **C�mo:** mantenerla si la figura exige los tres estados; no a�adir m�s paralelismo alrededor.
- **ME-006 � P2 � probable � `04-methodology.tex:107-108`** � **Cita:** �Cada robot usa estado propio, percepci�n local y mensajes de los vecinos dentro del radio de comunicaci�n.� **Patr�n/por qu�:** misma tr�ada/eslogan de IN-014. **C�mo:** sustituir la repetici�n por una definici�n formal o referencia cruzada.
- **ME-007 � P1 � clara � `04-methodology.tex:108-110`** � **Cita:** �El cierre entero, algunos agregados por carga y los certificados f�sicos conservan informaci�n global en varias campa�as; por ello, la implementaci�n evaluada es h�brida.� **Patr�n/por qu�:** tr�ada, punto y coma, transici�n �por ello� y recapitulaci�n. **C�mo:** identificar la informaci�n global exacta y definir �h�brida� sin frase de remate.
- **ME-008 � P2 � probable � `04-methodology.tex:110-112`** � **Cita:** �La simulaci�n es digital, con paso \(\Delta t\) declarado y actualizaciones locales as�ncronas, sin rondas globales obligatorias.� **Patr�n/por qu�:** estructura equilibrada �con A y B, sin C�. **C�mo:** separar discretizaci�n de pol�tica de comunicaci�n y declarar el periodo/agenda concretos.
- **ME-009 � P2 � contextual � `04-methodology.tex:133`** � **Cita:** �El primer t�rmino certifica el \emph{wrench}; el segundo regula la pose.� **Patr�n/por qu�:** paralelismo binario perfecto con punto y coma. Es �til al explicar la ecuaci�n. **C�mo:** conservar si mejora lectura; si se revisa, nombrar cada t�rmino en oraciones independientes.
- **ME-010 � P2 � contextual � `04-methodology.tex:133-134`** � **Cita:** �El modelo supone contactos fijos, l�mites de actuaci�n y din�mica planar reducida.� **Patr�n/por qu�:** tr�ada t�cnica de supuestos. **C�mo:** mantener los tres, pero remitir a una tabla de supuestos si el mismo inventario reaparece.
- **ME-011 � P2 � contextual � `04-methodology.tex:136-137`** � **Cita:** �En caging, cada contacto es unilateral: el robot puede empujar, pero no tirar de la carga.� **Patr�n/por qu�:** colon y contraste �puede X, pero no Y�; la forma es sospechosa, la precisi�n f�sica es leg�tima. **C�mo:** formular la restricci�n como fuerza normal compresiva/no negativa y conservar una explicaci�n llana aparte.
- **ME-012 � P1 � clara � `04-methodology.tex:140-142`** � **Cita:** �No se usa el certificado de \emph{wrench} de Cargo ni su prueba de estabilidad; la Figura~\ref{fig:method-cargo-caging} contrasta las dos interfaces.� **Patr�n/por qu�:** apertura negativa, punto y coma y giro metanarrativo a una figura. **C�mo:** separar la limitaci�n de la referencia visual y expresar el alcance de caging en positivo.
- **ME-013 � P1 � clara � `04-methodology.tex:231-235`** � **Cita:** �El problema se divide en nueve subproblemas, SP0--SP8, porque re�ne cuestiones que suelen formularse y validarse por separado: asignaci�n b�sica, coaliciones de tama�o variable, heterogeneidad de capacidades, factibilidad mec�nica, acoplamiento y transporte, seguridad ante obst�culos, recuperaci�n tras fallos, tr�fico entre coaliciones y efecto de la escala y la comunicaci�n imperfecta.� **Patr�n/por qu�:** colon seguido de nueve elementos y oraci�n muy larga; parece lista de cobertura. `SP0--SP8` es un rango TeX, no raya ret�rica. **C�mo:** remitir a la tabla y explicar aqu� solo el principio incremental.
- **ME-014 � P2 � probable � `04-methodology.tex:236`** � **Cita:** �Cada cuesti�n requiere un modelo, m�tricas y comparadores propios.� **Patr�n/por qu�:** tr�ada gen�rica que podr�a aplicarse a cualquier protocolo. **C�mo:** indicar qu� elemento cambia realmente entre SP.
- **ME-015 � P2 � probable � `04-methodology.tex:236-239`** � **Cita:** �La secuencia comienza con el caso m�nimo de SP0 y a�ade una condici�n en cada escal�n, de modo que pueda identificarse qu� componente explica un fallo antes de evaluar la misi�n integrada.� **Patr�n/por qu�:** met�fora de escal�n, transici�n �de modo que� y pasiva refleja. **C�mo:** describir la dependencia experimental concreta entre dos SP consecutivos.
- **ME-016 � P1 � probable � `04-methodology.tex:251-268`** � **Cita estructural:** las ocho filas SP1�SP8 separan listas mediante punto y coma, por ejemplo �Casos de abundancia y escasez; MILP y ablaci�n sin cierre� y �Barridos en flota, radio, retardo y p�rdida; mensajes, CPU, memoria y gap cuando el or�culo termina.� **Patr�n/por qu�:** plantilla repetida `escenarios; m�todos/m�tricas` y fragmentos nominales sim�tricos. La tabla justifica la compactaci�n, pero ocho repeticiones producen cadencia autom�tica. **C�mo:** convertir columnas en campos homog�neos expl�citos (escenario, comparador, m�trica) para que el punto y coma no haga de separador universal.
- **ME-017 � P2 � clara � `04-methodology.tex:277-278`** � **Cita:** �Los escenarios se generan por mundo y se reutilizan entre tratamientos. La tabla siguiente resume qu� se var�a y qu� se mide.� **Patr�n/por qu�:** pasivas consecutivas y frase metanarrativa de tabla. **C�mo:** definir �mundo� y el emparejamiento; dejar que el t�tulo de la tabla anuncie el resumen.
- **ME-018 � P2 � contextual � `04-methodology.tex:290-301`** � **Cita estructural:** las cuatro filas repiten listas de factores y listas de m�tricas, por ejemplo �\(N\), \(K\), cuotas, demanda total, capacidades, bater�a y distancia� frente a �Factibilidad, d�ficit, exceso, cargas completas, utilidad y gap.� **Patr�n/por qu�:** acumulaci�n nominal de hasta siete elementos por celda. Es funcional en tabla, pero duplica cat�logos ya presentes. **C�mo:** comprobar que cada factor/m�trica se define una sola vez y usar referencias, no sin�nimos.
- **ME-019 � P1 � clara � `04-methodology.tex:307-309`** � **Cita:** �En cada comparaci�n se fijan las poses iniciales, la semilla, el mapa, el horizonte, el integrador, los l�mites de actuaci�n y la definici�n de �xito.� **Patr�n/por qu�:** pasiva refleja y lista de siete controles. **C�mo:** trasladar los controles comunes a una tabla/configuraci�n reproducible y destacar en prosa la regla de emparejamiento.
- **ME-020 � P2 � contextual � `04-methodology.tex:308-310`** � **Cita:** �Los robots y las muestras temporales est�n anidados en el mundo; no cuentan como r�plicas.� **Patr�n/por qu�:** punto y coma seguido de correcci�n negativa. La precisi�n estad�stica es valiosa. **C�mo:** conservar la regla, pero usar dos oraciones si se quiere romper el tic de `;`.
- **ME-021 � P2 � probable � `04-methodology.tex:310-311`** � **Cita:** �Colisiones, bloqueos, errores num�ricos y agotamientos del horizonte permanecen en el denominador.� **Patr�n/por qu�:** lista de cuatro con sujeto abstracto y formulaci�n administrativa. **C�mo:** indicar c�mo se codifica cada resultado o remitir al protocolo.
- **ME-022 � P2 � contextual � `04-methodology.tex:323-324`** � **Cita:** �Las instancias peque�as se verifican por enumeraci�n u or�culo con gap. Las campa�as usan al menos 30 semillas cuando el coste lo permite.� **Patr�n/por qu�:** pasiva y hedge gen�rico �cuando el coste lo permite�. Es metodol�gicamente aceptable, pero deja abierta la excepci�n. **C�mo:** remitir a la justificaci�n por campa�a y declarar el m�nimo real cuando ya exista.
- **ME-023 � P1 � probable � `04-methodology.tex:324-326`** � **Cita:** �McNemar exacto se aplica a respuestas binarias; Wilcoxon, a continuas u ordinales; Friedman, a tres o m�s m�todos.� **Patr�n/por qu�:** tr�ada perfectamente sim�trica con dos puntos y coma; parece checklist estad�stico. **C�mo:** usar tabla prueba�endpoint�supuesto o explicar la jerarqu�a de decisi�n.
- **ME-024 � P2 � probable � `04-methodology.tex:326-327`** � **Cita:** �Se reportan efecto, intervalo por \emph{bootstrap} pareado de 2000 remuestreos y \(p\) corregido con Holm.� **Patr�n/por qu�:** pasiva refleja y tr�ada de resultados. **C�mo:** identificar tama�o de efecto, nivel del intervalo y familia corregida.
- **ME-025 � P2 � probable � `04-methodology.tex:329-332`** � **Cita:** �Incluye estanter�as, cuatro zonas de despacho y destino, un paso central compartido y cuatro bases para una flota de \AwsSceneRobots{} Pioneer P3-DX.� **Patr�n/por qu�:** lista descriptiva de cuatro y sujeto el�ptico. **C�mo:** mantener solo los elementos que alteran la validaci�n o remitir a la figura.
- **ME-026 � P2 � probable � `04-methodology.tex:338-339`** � **Cita:** �Cada ejecuci�n reproduce la secuencia despacho, reclutamiento, aproximaci�n, transporte y entrega.� **Patr�n/por qu�:** cat�logo de cinco etapas con verbo contenedor. **C�mo:** expresar la transici�n cr�tica o usar un diagrama de secuencia.
- **ME-027 � P2 � probable � `04-methodology.tex:339-340`** � **Cita:** �Las rutas atraviesan el paso central, donde coinciden las coaliciones con una carretilla, dos peatones controlados y un AMR libre.� **Patr�n/por qu�:** escena construida como tr�ada de obst�culos/agentes. **C�mo:** explicar el conflicto experimental que produce cada tipo o reducir el inventario.
- **ME-028 � P2 � clara � `04-methodology.tex:340-342`** � **Cita:** �Tambi�n se incluyen el fallo de un miembro, la incorporaci�n de un reemplazo y un ciclo acelerado de retorno por bater�a.� **Patr�n/por qu�:** transici�n aditiva mec�nica y regla de tres. **C�mo:** enlazar estas perturbaciones con la hip�tesis que prueban.
- **ME-029 � P2 � probable � `04-methodology.tex:342-343`** � **Cita:** �Se registran poses, enlaces de comunicaci�n, detecciones, entregas, cola pendiente y estado del fallo.� **Patr�n/por qu�:** pasiva refleja y lista de seis logs. **C�mo:** remitir al esquema de datos o manifest y destacar solo la variable primaria.
- **ME-030 � P2 � contextual � `04-methodology.tex:350-352`** � **Cita:** �La vista oblicua muestra las estanter�as, las zonas de operaci�n, el paso central y la flota de AMR durante la ejecuci�n del piloto.� **Patr�n/por qu�:** caption con lista de cuatro. **C�mo:** conservar si orienta la lectura; evitar repetir la misma lista en el cuerpo.
- **ME-031 � P1 � clara � `04-methodology.tex:358-360`** � **Cita:** �CoppeliaSim comprueba la integraci�n geom�trica y el replay cinem�tico de estas interfaces. No modela el agarre, la fricci�n rueda--suelo ni la din�mica de contacto, y tampoco sustituye una validaci�n en hardware.� **Patr�n/por qu�:** cierre positivo seguido de tr�ada negativa y �tampoco�; f�rmula de alcance/descargo repetida. `rueda--suelo` es relaci�n t�cnica TeX. **C�mo:** definir primero qu� evidencia aporta el piloto y separar en una tabla qu� f�sica y validaci�n faltan.

## Patrones transversales de la Parte B

1. **Cautela por negaci�n:** aparecen repetidamente `no afirma`, `no como`, `no constituyen`, `no presupone`, `no demostrar�`, `no colapsar�`, `no hereda`, `no se usa` y `tampoco`. Las limitaciones son correctas; el olor procede de usar casi siempre ant�tesis negativa en lugar de declarar primero el dominio positivo.
2. **Inventarios encadenados:** introducci�n, objetivos y metodolog�a vuelven a listar capas, SP, componentes, m�tricas y l�mites ya presentes en tablas. La reparaci�n debe eliminar duplicaci�n, no sustituir t�rminos por sin�nimos.
3. **Ritmo impersonal:** `se estudia`, `se declaran`, `se mide`, `se eval�a`, `se verifica`, `se reportan` y `se registran` forman una cadena. La voz impersonal es v�lida en espa�ol acad�mico; conviene cambiar solo cuando oculta el experimento, la variable o la regla de decisi�n.
4. **Regla de tres y paralelismo:** es la se�al dominante. Hay tr�adas en ejemplos, taxonom�as, garant�as, m�todos, escenarios, resultados y captions. Las listas necesarias deben convertirse en tablas o relaciones causales; variar a dos o cuatro elementos sin raz�n solo maquillar�a el patr�n.
5. **Puntuaci�n:** no hay raya larga ret�rica. Los cuatro `--` visibles de metodolog�a son TeX t�cnico y los otros 21 son operadores TikZ. El problema real son algunos puntos y coma del cuerpo y, sobre todo, el uso serial de punto y coma como �columna invisible� en la tabla SP.
6. **Ausencias relevantes:** no se detectaron saludos de chatbot, �vamos a ver�, preguntas ret�ricas, `Moreover/Furthermore`, apelaciones emocionales, met�foras promocionales, atribuciones vagas ni *synonym cycling* generalizado.

## Orden de reparaci�n recomendado para esta parte

1. Desmontar primero IN-009, IN-016, IN-025, IN-028, OB-011�OB-013, HP-004, HP-017/HP-021, ME-003, ME-013, ME-019, ME-023 y ME-031.
2. Convertir los inventarios repetidos en tablas o referencias cruzadas y conservar en prosa solo relaciones causales.
3. Reescribir las limitaciones desde el alcance positivo; mantener todas las exclusiones cient�ficas.
4. Revisar ritmo a nivel de p�rrafo despu�s de corregir frases. Parchear palabras sueltas no eliminar� la regularidad estructural.


---

## Resumen consolidado de cobertura y conteos

- **Archivos auditados �ntegramente:** 9/9: `thesis/config/metadata.tex`; cuatro archivos de `frontmatter`; `01-introduction.tex`; `02-objectives.tex`; `03-hypotheses.tex`; `04-methodology.tex`.
- **Cobertura textual aproximada:** 32 oraciones renderizadas en resumen/abstract, 43 en introducci�n, 15 en objetivos, 28 en hip�tesis y unas 80 unidades en metodolog�a (54 oraciones/captions + 26 celdas), adem�s de 14 l�neas de metadatos, 10 l�neas de portada, 11 l�neas de �ndices y sus comentarios/comandos. Total comparable: **�198 unidades de prosa o texto visible**.
- **Hallazgos:** **120** en total: **P0 = 0**, **P1 = 37**, **P2 = 83**. Confianza: **clara = 28**, **probable = 64**, **contextual = 28**.
- **Dos puntos visibles en prosa:** **8**: 2 en resumen/abstract, 1 en introducci�n y 5 en metodolog�a. Los dem�s `:` de los archivos son etiquetas, notaci�n o sintaxis TikZ. Solo el par biling�e de rectificaci�n negativa se considera un patr�n fuerte; los de ecuaciones/definiciones se evaluaron en contexto.
- **Puntos y coma visibles:** **21**: 11 en cuerpo de prosa y 10 en tablas/r�tulos compactos. Adem�s hay 61 `;` que terminan comandos TikZ y no son puntuaci�n ling��stica. La concentraci�n problem�tica est� en la comparaci�n bibliogr�fica de introducci�n, la oraci�n de H4 y algunas series/tablas de metodolog�a.
- **Raya larga Unicode `�`:** **0** en los nueve archivos.
- **Doble guion `--`:** **32 apariciones brutas, 0 ret�ricas**. Veintiuna son operadores de trayecto TikZ; once son rangos o relaciones t�cnicas LaTeX (`2025--2026`, `SP0--SP8`, `carga--obst�culo`, `rueda--suelo`, y equivalentes ingleses). Son falsos positivos para la regla de em dash.
- **Se�ales dominantes:** listas acumulativas, regla de tres, paralelismo sim�trico, calco biling�e del resumen, cautelas mediante negaci�n/ant�tesis, metanarraci�n documental, pasiva/impersonal seriada y longitud/cadencia de p�rrafos demasiado regular.
- **Se�ales no detectadas:** artefactos de chatbot, saludos o cierres conversacionales, autoalusi�n a limitaciones del modelo, halagos al lector, preguntas ret�ricas, met�foras promocionales, inflaci�n grandilocuente, citas vagas tipo �los expertos afirman�, emojis, negrita enf�tica o abuso ret�rico de rayas.
- **Integridad:** no se reescribi� ni modific� ninguna de las nueve fuentes. Cada propuesta �C�mo arreglarla� es una instrucci�n para una fase editorial posterior.


# Auditoría completa de patrones de escritura asociados a IA

## Alcance y criterio

Auditoría en modo **DETECT**. No se modificó ningún archivo fuente. Se revisaron completos:

- `thesis/sections/frontmatter/04-nomenclature.tex`;
- `thesis/sections/mainmatter/05-theoretical-framework.tex`;
- `thesis/sections/appendices/01-reproducibility.tex`;
- `thesis/sections/appendices/02-sp0-proofs.tex`;
- `thesis/sections/appendices/03-sp1-proofs.tex`;
- `thesis/sections/appendices/04-sp2-proofs.tex`;
- `thesis/sections/appendices/05-sp3-proofs.tex`;
- `thesis/sections/appendices/06-sp4-proofs.tex`;
- `thesis/sections/appendices/07-sp6-proofs.tex`;
- `thesis/sections/appendices/08-sp7-proofs.tex`;
- `thesis/sections/appendices/09-sp8-proofs.tex`.

Se aplicó `avoid-ai-writing` con un perfil académico-técnico. El informe **no atribuye autoría**: registra construcciones que pueden hacer que la prosa parezca generativa, aunque algunas sean correctas o convenientes en una prueba. **Clara** significa que el patrón se reconoce sin depender del contenido; **probable**, que estructura, léxico y ritmo producen señal; **contextual**, que el giro coincide con un patrón de IA pero puede estar justificado por rigor matemático.

No se marcaron automáticamente definiciones, hipótesis necesarias, pasos algebraicos, tablas genuinas, nombres técnicos, intervalos, operadores ni referencias cruzadas. En particular, `0--1`, `2024--2025`, `SP0--SP8`, `RAW--SAFE--EXEC`, `primal--dual`, `Brown--von Neumann--Nash`, `nodo--arista` y guiones de apellidos son usos legítimos. No hay una sola raya estilística Unicode `—` ni un `--` usado como raya narrativa.

## Resultado global

- **P0:** 0. No aparecen artefactos de chatbot, adulación, descargos sobre límites del modelo, atribuciones vagas («los expertos creen») ni inflación promocional/histórica.
- **P1:** la concentración principal está en el marco teórico: índice narrado, paralelismos muy regulares, listas de citas con análisis superficial, contrastes `no X, sino Y`, cadenas de `pero/no implica/no acredita` y cierres genéricos.
- **P2:** los anexos repiten una plantilla: alcance inicial, lista de exclusiones, `Por tanto/Así/En consecuencia`, `Esto completa/demuestra/prueba...` y salvedad final. Cada paso puede ser correcto; la repetición entre archivos es la señal.
- **Vocabulario AI de alta señal:** no se encontraron equivalentes promocionales claros de *delve, tapestry, beacon, game-changing, seamless, thriving, pivotal* o *testament to*. `robusto` aparece entre comillas para negar una equivalencia conceptual, no como elogio.
- **Ritmo:** el marco alterna párrafos de cuatro o cinco frases de longitud semejante y usa de manera recurrente la secuencia «afirmación → concesión → lista de limitaciones → sentencia de frontera». Los anexos tienen cierres casi intercambiables.

## Cobertura y puntuación

Los «cierres» son aproximados: se contaron terminadores después de retirar comentarios y bloques matemáticos simples; en nomenclatura incluyen entradas. `:` y `;` se dan como **crudo/prosa**; el primer valor incluye TikZ/LaTeX y el segundo excluye comandos gráficos y estructurales evidentes.

| Archivo | Palabras | Cierres aprox. | `:` crudo/prosa | `;` crudo/prosa | `—` | `--` crudo/prosa | `(` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `04-nomenclature.tex` | 888 | 62 | 0/0 | 0/0 | 0 | 9/9 | 7 |
| `05-theoretical-framework.tex` | 7.882 | 239 | 55/26 | 221/26 | 0 | 67/9 | 358 |
| `01-reproducibility.tex` | 302 | 14 | 5/2 | 7/7 | 0 | 3/3 | 0 |
| `02-sp0-proofs.tex` | 1.015 | 50 | 9/5 | 0/0 | 0 | 3/3 | 28 |
| `03-sp1-proofs.tex` | 1.107 | 54 | 14/8 | 0/0 | 0 | 2/2 | 19 |
| `04-sp2-proofs.tex` | 321 | 11 | 6/4 | 0/0 | 0 | 0/0 | 2 |
| `05-sp3-proofs.tex` | 474 | 16 | 10/7 | 0/0 | 0 | 0/0 | 14 |
| `06-sp4-proofs.tex` | 768 | 27 | 9/6 | 0/0 | 0 | 0/0 | 19 |
| `07-sp6-proofs.tex` | 1.472 | 61 | 26/18 | 0/0 | 0 | 1/1 | 42 |
| `08-sp7-proofs.tex` | 587 | 31 | 9/4 | 0/0 | 0 | 0/0 | 11 |
| `09-sp8-proofs.tex` | 357 | 15 | 3/2 | 0/0 | 0 | 0/0 | 3 |
| **Total** | **15.173** | **580** | **146/82** | **228/33** | **0** | **85/18** | **503** |

Los 221 punto y coma crudos del marco proceden casi todos de TikZ; los 26 narrativos sí se concentran en paralelismos. Todos los dobles guiones inspeccionados son rangos, nombres, términos o código.

## Hallazgos frase por frase

### `thesis/sections/frontmatter/04-nomenclature.tex`

- **NOM-001 · P2 · probable · `04-nomenclature.tex:72`** — «No representan una misma magnitud.» **Patrón/motivo:** negación correctiva muy corta después de una frase que ya distingue los significados; crea cadencia de aclaración automática. **Cómo corregir:** integrar la negación en la oración anterior.
- **NOM-002 · P2 · contextual · `04-nomenclature.tex:72`** — «Algunos símbolos se reutilizan entre subproblemas con decoraciones distintas ($\rho_{ik}$, $\rho_D$, $\rho_k^W$).» **Patrón/motivo:** repite el contenido anterior con otra terna. **Cómo corregir:** conservar una única explicación y añadir allí los ejemplos.
- **NOM-003 · P2 · contextual · `04-nomenclature.tex:72`** — «El superíndice o subíndice identifica el contexto.» **Patrón/motivo:** cierre sentencioso y genérico tras dos aclaraciones equivalentes. **Cómo corregir:** especificar qué decoración identifica cada contexto o fusionar con NOM-002.

### `thesis/sections/mainmatter/05-theoretical-framework.tex`

- **TF-001 · P2 · probable · `05-theoretical-framework.tex:4`** — «El transporte cooperativo enlaza selección, coalición, estimación, contacto y movimiento, pero cada una de esas capas responde a una pregunta distinta.» **Patrón/motivo:** lista abstracta de cinco sustantivos más concesión genérica. **Cómo corregir:** abrir con la tesis concreta de que cada capa certifica una propiedad distinta.
- **TF-002 · P1 · clara · `05-theoretical-framework.tex:4`** — «La asignación identifica quién debería participar; la formación determina si esos robots constituyen un equipo compatible; la mecánica comprueba si el equipo puede producir las fuerzas y torques requeridos; y el control ejecuta el movimiento sin violar restricciones de seguridad.» **Patrón/motivo:** cuatro cláusulas isomorfas separadas por punto y coma. **Cómo corregir:** usar una tabla o dos frases con dependencia causal.
- **TF-003 · P1 · clara · `05-theoretical-framework.tex:4`** — «Confundir estas preguntas conduce a inferencias inválidas: un Nash puede ser ineficiente, una suma de capacidades puede ocultar un torque irrealizable, el consenso no estabiliza la planta y una trayectoria segura puede bloquearse.» **Patrón/motivo:** colon seguido de cuatro ejemplos simétricos, inmediatamente después de otra lista. **Cómo corregir:** escoger uno o dos contraejemplos y explicar la inferencia invalidada.
- **TF-004 · P1 · probable · `05-theoretical-framework.tex:6`** — «El marco se organiza alrededor de esas fronteras de inferencia.» **Patrón/motivo:** metanarración con sujeto abstracto. **Cómo corregir:** empezar por la primera frontera sustantiva.
- **TF-005 · P1 · clara · `05-theoretical-framework.tex:6`** — «Primero se sitúa el transporte cooperativo como una composición de contratos entre capas.» **Patrón/motivo:** anuncio secuencial impersonal. **Cómo corregir:** afirmar directamente el modelo y definir `contrato`.
- **TF-006 · P1 · clara · `05-theoretical-framework.tex:6`** — «Después se revisan MRTA y formación de coaliciones, juegos y estimación distribuida, factibilidad mecánica, control, seguridad, recuperación, tráfico y comunicación imperfecta.» **Patrón/motivo:** transición mecánica e inventario de nueve temas; índice narrado. **Cómo corregir:** eliminar o reemplazar por una relación causal entre bloques.
- **TF-007 · P1 · clara · `05-theoretical-framework.tex:6`** — «La síntesis final no busca una genealogía exhaustiva, sino identificar qué propiedades aporta cada familia y qué interfaz permanece abierta para el problema focal.» **Patrón/motivo:** plantilla `no X, sino Y` con sustantivos abstractos. **Cómo corregir:** formular el objetivo en positivo.
- **TF-008 · P2 · contextual · `05-theoretical-framework.tex:11`** — «La infraestructura compartida y los cierres globales se declaran por separado.» **Patrón/motivo:** pasiva refleja y verbo metadiscursivo; no dice quién ni dónde. **Cómo corregir:** nombrar los supuestos y su ubicación.
- **TF-009 · P2 · probable · `05-theoretical-framework.tex:13`** — «La decisión estratégica y el movimiento quedan así acoplados: desplazarse modifica costes, vecindades y disponibilidad, mientras una revisión de coalición cambia el objetivo físico de cada agente.» **Patrón/motivo:** colon, terna y dos mitades equilibradas. **Cómo corregir:** describir una dependencia cuantitativa concreta.
- **TF-010 · P2 · contextual · `05-theoretical-framework.tex:15`** — «El equipo debe cerrarse, ocupar contactos, producir el \emph{wrench} y conservar seguridad \parencite{an2023cooperativeReview}.» **Patrón/motivo:** cuatro infinitivos sin jerarquía. **Cómo corregir:** presentarlos como cadena causal de certificados.
- **TF-011 · P2 · probable · `05-theoretical-framework.tex:15`** — «Ninguna flecha implica una garantía conjunta.» **Patrón/motivo:** descargo defensivo breve. **Cómo corregir:** precisar qué composición falta demostrar o llevarlo a la leyenda.
- **TF-012 · P2 · probable · `05-theoretical-framework.tex:57`** — «Una medición local puede alimentar una estimación de ocupación o recurso, pero esa estimación tiene edad, alcance y error.» **Patrón/motivo:** `puede..., pero...` y regla de tres. **Cómo corregir:** indicar qué errores se modelan y cómo afectan la decisión.
- **TF-013 · P1 · clara · `05-theoretical-framework.tex:57`** — «Esto no convierte al sistema en continuo ni ``sin reloj'': el integrador, el periodo de muestreo y la política de mensajes siguen condicionando la realización física.» **Patrón/motivo:** negación correctiva, colon y terna. **Cómo corregir:** afirmar en positivo que la implementación es digital y declarar sus parámetros.
- **TF-014 · P2 · contextual · `05-theoretical-framework.tex:59`** — «La coalición debe mantener su geometría, repartir soporte y realizar el \emph{wrench} de traslación y giro.» **Patrón/motivo:** regla de tres. **Cómo corregir:** enlazar cada elemento con su certificado o separar geometría de soporte/wrench.
- **TF-015 · P2 · probable · `05-theoretical-framework.tex:59`** — «Las dos modalidades pueden compartir asignación y estimación, pero no el modelo de contacto ni una prueba de estabilidad.» **Patrón/motivo:** oposición `pueden..., pero no... ni...`. **Cómo corregir:** definir la interfaz común y, en otra frase, los modelos incompatibles.
- **TF-016 · P1 · clara · `05-theoretical-framework.tex:59`** — «Por esa razón, la rama de empuje/caging se conserva como contraste conceptual y extensión secundaria, no como evidencia intercambiable con Cargo \parencite{an2023cooperativeReview,rosenfelder2024force}.» **Patrón/motivo:** transición mecánica y contraste `como X, no como Y`; pasiva refleja. **Cómo corregir:** declarar directamente la decisión del TFM y su causa.
- **TF-017 · P1 · probable · `05-theoretical-framework.tex:72`** — «Su satisfacción es estratégica: afirma que la composición nominal reúne suficientes contribuciones, pero todavía no asigna contactos ni demuestra que esas contribuciones puedan combinarse físicamente.» **Patrón/motivo:** personificación, colon, concesión y dos negaciones. **Cómo corregir:** decir qué certifica la ecuación y qué variables mecánicas faltan.
- **TF-018 · P2 · probable · `05-theoretical-framework.tex:72`** — «Replicar una tarea en varias plazas independientes tampoco preserva simultaneidad, complementariedad ni la condición todo-o-nada de la misión.» **Patrón/motivo:** negación enfática y terna conceptual. **Cómo corregir:** usar un contraejemplo mínimo y derivar las otras pérdidas.
- **TF-019 · P1 · probable · `05-theoretical-framework.tex:72`** — «Por ello, el algoritmo húngaro es un referente adecuado para la asignación uno a uno, mientras MILP, \emph{set partitioning} o formulaciones equivalentes son referencias más fieles para coaliciones y capacidades múltiples.» **Patrón/motivo:** `Por ello` más oposición equilibrada y lista abierta. **Cómo corregir:** separar el dominio del húngaro de la formulación central concreta.
- **TF-020 · P2 · probable · `05-theoretical-framework.tex:74`** — «La función objetivo introduce una segunda distinción.» **Patrón/motivo:** andamiaje que anuncia una clasificación. **Cómo corregir:** empezar por la distinción misma.
- **TF-021 · P1 · clara · `05-theoretical-framework.tex:74`** — «Minimizar distancia o coste de movilización puede favorecer equipos rápidos pero incapaces de cerrar una carga, mientras maximizar cobertura parcial puede dispersar recursos entre misiones que nunca se completan.» **Patrón/motivo:** dos ramas `puede... mientras... puede...` sin condiciones ni caso. **Cómo corregir:** aportar instancia mínima o centrarse en el conflicto que motiva el objetivo.
- **TF-022 · P2 · probable · `05-theoretical-framework.tex:74`** — «En tareas obligatorias interesa regular déficit y exceso; bajo escasez también debe decidirse qué cargas se activan.» **Patrón/motivo:** punto y coma y pasiva refleja. **Cómo corregir:** dividir y definir el criterio de activación.
- **TF-023 · P1 · probable · `05-theoretical-framework.tex:74`** — «La factibilidad de una instancia, la factibilidad de cada coalición y la calidad social de la asignación son, por tanto, propiedades diferentes.» **Patrón/motivo:** terna, repetición calculada y cierre `por tanto`. **Cómo corregir:** distinguir factibilidad de calidad en una frase; definir después los dos niveles de factibilidad.
- **TF-024 · P1 · clara · `05-theoretical-framework.tex:76`** — «Las subastas adjudican mediante precios: Bertsekas resuelve asignación clásica \parencite{bertsekas1988Auction}, MURDOCH usa contratos robóticos \parencite{gerkeyMataric2002MURDOCH}, CBBA resuelve paquetes por consenso y ACBBA admite desorden \parencite{choiBrunetHow2009CBBA,johnson2011acbba}.» **Patrón/motivo:** lista de nombres y resúmenes de una cláusula. **Cómo corregir:** comparar dos mecanismos por una propiedad transferible y mover el resto a tabla.
- **TF-025 · P2 · probable · `05-theoretical-framework.tex:76`** — «Estas familias ofrecen decisiones interpretables y permiten distribuir parte de la negociación.» **Patrón/motivo:** elogio genérico sin criterio observable. **Cómo corregir:** nombrar la variable interpretable y los mensajes distribuidos.
- **TF-026 · P1 · clara · `05-theoretical-framework.tex:76`** — «No obstante, una puja suele valorar una tarea o paquete desde el estado del postor; sin una regla de cierre común, varios ganadores compatibles en precio pueden llegar en momentos distintos o competir por el mismo puesto de contacto.» **Patrón/motivo:** concesión, punto y coma y dos fallos alternativos. **Cómo corregir:** formular el supuesto faltante y mostrar un fallo concreto.
- **TF-027 · P1 · probable · `05-theoretical-framework.tex:78`** — «Coaliciones \emph{anytime}, basadas en capacidades y hedónicas modelan composición y preferencia \parencite{shehoryKraus1998Coalition,vigAdams2006Coalition,dutta2021hedonic}.» **Patrón/motivo:** tres etiquetas y tres citas sin contraste. **Cómo corregir:** conservar en prosa la propiedad adoptada y llevar el inventario a tabla.
- **TF-028 · P2 · probable · `05-theoretical-framework.tex:78`** — «Su ventaja es representar explícitamente que la utilidad de un robot depende del grupo al que se incorpora.» **Patrón/motivo:** plantilla `Su ventaja es...`. **Cómo corregir:** enlazar la dependencia de grupo con el payoff o la restricción usada.
- **TF-029 · P2 · probable · `05-theoretical-framework.tex:78`** — «El coste aparece en el espacio combinatorio de subconjuntos y en la necesidad de verificar desviaciones o intercambios locales.» **Patrón/motivo:** nominalización vaga y parejas abstractas. **Cómo corregir:** dar el conteo o la complejidad aplicable.
- **TF-030 · P2 · probable · `05-theoretical-framework.tex:78`** — «Una coalición estable frente a esas desviaciones no tiene por qué minimizar el coste total, y una coalición socialmente valiosa puede resultar inalcanzable con la información o los movimientos disponibles.» **Patrón/motivo:** dos cautelas paralelas y modales. **Cómo corregir:** separar estabilidad de optimalidad y justificar la inalcanzabilidad con un supuesto.
- **TF-031 · P1 · probable · `05-theoretical-framework.tex:80`** — «Esta línea acerca ``capacidad disponible'' a ``coalición ejecutable'' porque comprueba cómo se conectan sensores, recursos y comportamientos.» **Patrón/motivo:** metáfora, pares entrecomillados y terna. **Cómo corregir:** describir la comprobación funcional exacta.
- **TF-032 · P1 · clara · `05-theoretical-framework.tex:80`** — «Sin embargo, la ejecutabilidad funcional no sustituye un certificado de soporte, contacto y \emph{wrench}; esas restricciones dependen de la pose y de los límites físicos en el instante de ejecución.» **Patrón/motivo:** `Sin embargo`, negación, terna y punto y coma. **Cómo corregir:** definir alcance funcional y luego explicar con una variable por qué no prueba realizabilidad.
- **TF-033 · P1 · probable · `05-theoretical-framework.tex:82-83`** — «Trabajos de 2024--2025 enlazan asignación con tiempo o movimiento: Shan et al. usan subasta para llegadas dinámicas \parencite{shan2024collectiveTransport}.» **Patrón/motivo:** apertura por recencia, colon y primer elemento de una lista de autores. **Cómo corregir:** organizar por mecanismo o supuesto.
- **TF-034 · P1 · probable · `05-theoretical-framework.tex:84-85`** — «Dai y Bezerra et al. aprenden coaliciones y rutas o revisiones espaciales \parencite{dai2024dynamicCoalition,bezerra2025dynamicCoalition}.» **Patrón/motivo:** segundo elemento telegráfico; dos trabajos comprimidos en una disyunción vaga. **Cómo corregir:** separar qué aprende cada uno.
- **TF-035 · P1 · probable · `05-theoretical-framework.tex:86-87`** — «Qiu et al. actualizan capacidad consumida y Shida et al. excluyen tareas inviables \parencite{qiu2024payloadConsumption,shida2025infeasibleTasks}.» **Patrón/motivo:** tercer par simétrico de autores. **Cómo corregir:** mover el inventario a tabla y conservar la diferencia que afecta al certificado.
- **TF-036 · P1 · clara · `05-theoretical-framework.tex:87-89`** — «Emplean capacidad nominal o aprendida, no un certificado conjunto de contacto, \emph{wrench}, seguridad y recuperación.» **Patrón/motivo:** `X, no Y` y lista de cuatro; sujeto plural impreciso. **Cómo corregir:** indicar por trabajo qué capa falta.
- **TF-037 · P1 · probable · `05-theoretical-framework.tex:89`** — «Los métodos aprendidos resultan útiles como comparadores de calidad empírica y adaptación, pero no ofrecen por sí mismos la trazabilidad requerida para el mecanismo principal.» **Patrón/motivo:** falsa concesión y evaluación global. **Cómo corregir:** nombrar métrica comparable y artefacto de trazabilidad ausente.
- **TF-038 · P1 · clara · `05-theoretical-framework.tex:89`** — «La brecha relevante no consiste en que MRTA carezca de métodos competitivos, sino en que la salida de asignación rara vez se expresa como un contrato verificable para las capas físicas posteriores.» **Patrón/motivo:** `no consiste en X, sino en Y`; dirección explícita de lectura. **Cómo corregir:** afirmar en positivo la ausencia del certificado y limitarla al corpus.
- **TF-039 · P2 · probable · `05-theoretical-framework.tex:94`** — «Esta descripción debe distinguir comunicación de sensado: un robot puede observar un obstáculo sin intercambiar mensajes con él, o recibir la intención de un vecino cuya carga no percibe directamente.» **Patrón/motivo:** instrucción, colon y dos ejemplos espejados. **Cómo corregir:** definir ambos grafos y dejar un solo ejemplo.
- **TF-040 · P1 · probable · `05-theoretical-framework.tex:94`** — «El grafo especifica quién puede compartir estado, no qué magnitud conoce cada agente ni con qué precisión.» **Patrón/motivo:** contraste `X, no Y ni Z`. **Cómo corregir:** definir en positivo el modelo de observación adicional.
- **TF-041 · P2 · contextual · `05-theoretical-framework.tex:96`** — «El consenso estático aproxima una cantidad fija; el consenso dinámico sigue señales agregadas que cambian mientras los robots se mueven y revisan su decisión \parencite{kia2019dynamicConsensus}.» **Patrón/motivo:** definiciones paralelas separadas por punto y coma. **Cómo corregir:** mantenerlo solo si se comparan formalmente los errores; si no, dividir.
- **TF-042 · P2 · probable · `05-theoretical-framework.tex:96`** — «Su error depende de conectividad, variación de la entrada, ganancias y discretización.» **Patrón/motivo:** cuatro factores sin jerarquía ni cota. **Cómo corregir:** citar la cota o nombrar solo los factores evaluados.
- **TF-043 · P1 · clara · `05-theoretical-framework.tex:96`** — «Alcanzar acuerdo sobre una ocupación estimada tampoco decide qué carga conviene atender, y mucho menos estabiliza la planta.» **Patrón/motivo:** énfasis escalonado `tampoco... y mucho menos...`. **Cómo corregir:** separar ambos no-resultados y asociarlos con su capa.
- **TF-044 · P2 · probable · `05-theoretical-framework.tex:96`** — «La estimación es una interfaz de información cuyo residual debe propagarse a la decisión que la utiliza.» **Patrón/motivo:** abstracción sin mecanismo. **Cómo corregir:** nombrar la variable y el término/cota afectado.
- **TF-045 · P1 · probable · `05-theoretical-framework.tex:98`** — «Los resultados asíncronos requieren, sin embargo, hipótesis como activación persistente y retardos acotados \parencite{tsitsiklis1986asynchronousOptimization}.» **Patrón/motivo:** `sin embargo` parentético y lista abierta con `como`. **Cómo corregir:** declarar las hipótesis exactas.
- **TF-046 · P1 · clara · `05-theoretical-framework.tex:98`** — «Por ello, ``distribuido'', ``asíncrono'' y ``robusto a red'' no son sinónimos.» **Patrón/motivo:** conector, terna entrecomillada y definición negativa sentenciosa. **Cómo corregir:** definir cada término en positivo.
- **TF-047 · P2 · contextual · `05-theoretical-framework.tex:106`** — «Descuentos, proyecciones o información obsoleta pueden romperla.» **Patrón/motivo:** terna y pronombre sin antecedente inmediato. **Cómo corregir:** nombrar la identidad de potencial y el mecanismo aplicable.
- **TF-048 · P2 · probable · `05-theoretical-framework.tex:106`** — «Un potencial exacto ordena desviaciones individuales y garantiza existencia de equilibrio puro en juegos finitos, pero no selecciona necesariamente el equilibrio de menor coste social.» **Patrón/motivo:** `garantiza..., pero no...`, repetido en el capítulo. **Cómo corregir:** separar existencia de eficiencia y enlazar esta última con PoA/PoS.
- **TF-049 · P2 · probable · `05-theoretical-framework.tex:106`** — «También debe distinguirse el potencial analítico, evaluado con agregados coherentes, del potencial visible que cada robot reconstruye con mensajes locales.» **Patrón/motivo:** pasiva prescriptiva y parentético. **Cómo corregir:** definir ambos símbolos y su error.
- **TF-050 · P2 · probable · `05-theoretical-framework.tex:119`** — «Las cinco dinámicas difieren en continuidad, exploración, soporte y estacionariedad, pero ninguna produce por sí sola el cierre discreto.» **Patrón/motivo:** cuatro dimensiones y concesión totalizante. **Cómo corregir:** identificar la diferencia que determina la elección y separar el cierre.
- **TF-051 · P2 · contextual · `05-theoretical-framework.tex:239`** — «Los retratos no representan la integración de un mismo campo de pagos.» **Patrón/motivo:** descargo breve añadido a una leyenda ya explicativa. **Cómo corregir:** incorporarlo en la primera frase de la leyenda como condición de lectura.
- **TF-052 · P1 · clara · `05-theoretical-framework.tex:244`** — «La mejor respuesta cambia de dirección al cruzar regiones de indiferencia, la replicadora no recupera una estrategia ausente, Smith compara pares, BNN activa excesos sobre $\bar f$ y logit mantiene masa positiva y aproxima la mejor respuesta al disminuir $\eta$.» **Patrón/motivo:** cinco métodos encadenados por comas con sintaxis paralela. **Cómo corregir:** usar tabla o seleccionar la propiedad decisiva para el método usado.
- **TF-053 · P2 · probable · `05-theoretical-framework.tex:244`** — «Estas diferencias importan durante transitorios y ante estrategias inicialmente ausentes, aun cuando varias dinámicas compartan estados estacionarios bajo pagos ideales.» **Patrón/motivo:** `importan` es énfasis vago y la concesión no cuantifica efecto. **Cómo corregir:** indicar qué transición o métrica cambia.
- **TF-054 · P1 · probable · `05-theoretical-framework.tex:246`** — «Una proyección, un ranking o un redondeo puede alterar el valor del potencial y reintroducir déficit; por tanto, la convergencia de la relajación no acredita convergencia de la ejecución entera.» **Patrón/motivo:** terna, punto y coma, `por tanto` y contraste `no acredita`. **Cómo corregir:** nombrar el cierre ejecutado y el contraejemplo/propiedad que pierde.
- **TF-055 · P2 · probable · `05-theoretical-framework.tex:246`** — «El contrato completo debe declarar tanto la dinámica de preferencias como la regla de cierre y el tratamiento de empates.» **Patrón/motivo:** prescripción abstracta y lista. **Cómo corregir:** declarar esos tres elementos allí mismo para el método focal.
- **TF-056 · P1 · probable · `05-theoretical-framework.tex:248`** — «Los precios duales interpretan congestión o déficit y ayudan a distribuir restricciones acopladas, pero no convierten una relajación convexa en una solución entera ni implican óptimo social.» **Patrón/motivo:** personificación, falsa concesión y doble negación. **Cómo corregir:** separar la función del precio de las dos garantías ausentes.
- **TF-057 · P2 · probable · `05-theoretical-framework.tex:250`** — «Pasividad y Lyapunov requieren almacenamiento, suministro, dominio y signo de la derivada \parencite{vanderschaf2017passivity,ortega2002passivity}.» **Patrón/motivo:** lista compacta de cuatro requisitos. **Cómo corregir:** formular el candidato y la desigualdad requeridos o reducir la lista.
- **TF-058 · P1 · probable · `05-theoretical-framework.tex:250`** — «La etiqueta no se transfiere si cambian puertos, contacto, saturaciones o integrador.» **Patrón/motivo:** negación sentenciosa y lista de cuatro. **Cómo corregir:** nombrar la hipótesis concreta que rompe la prueba.
- **TF-059 · P2 · probable · `05-theoretical-framework.tex:250`** — «En un sistema acoplado, una prueba para la capa estratégica y otra para la planta pueden coexistir sin formar automáticamente una prueba para la interconexión híbrida completa.» **Patrón/motivo:** paralelismo `una... y otra...` más negación cautelar. **Cómo corregir:** indicar la condición de composición que falta.
- **TF-060 · P1 · clara · `05-theoretical-framework.tex:255`** — «Conectividad no implica rigidez: un grafo conexo permite propagar información, mientras la rigidez fija localmente la forma salvo traslaciones y rotaciones del conjunto \parencite{desai2001formation,bullo2009distributed}.» **Patrón/motivo:** `X no implica Y`, colon y dos mitades equilibradas. **Cómo corregir:** definir conectividad y rigidez en frases separadas y después expresar la no implicación.
- **TF-061 · P1 · clara · `05-theoretical-framework.tex:263`** — «Las componentes internas no mueven el cuerpo ideal, pero sí afectan saturación, compresión y pérdida de contacto.» **Patrón/motivo:** construcción `no X, pero sí Y` y terna. **Cómo corregir:** afirmar directamente el efecto de las fuerzas internas y luego aclarar que su resultante ideal es nula.
- **TF-062 · P1 · probable · `05-theoretical-framework.tex:263`** — «Por ello, la capacidad escalar no sustituye $W_k^{\mathrm{req}}\in\mathcal W_C(q)=\{G_C(q)\boldsymbol\lambda:\boldsymbol\lambda\in\mathcal U_C\}$.» **Patrón/motivo:** conector mecánico y negación sentenciosa. **Cómo corregir:** afirmar en positivo que la factibilidad exige pertenencia al conjunto de wrench.
- **TF-063 · P1 · probable · `05-theoretical-framework.tex:265`** — «Un certificado útil para reclutamiento debe, por tanto, declarar qué demanda de \emph{wrench} cubre, con qué geometría, límites y tolerancia.» **Patrón/motivo:** `por tanto` parentético y lista de cuatro. **Cómo corregir:** definir el certificado mediante esas variables en vez de prescribirlo.
- **TF-064 · P2 · probable · `05-theoretical-framework.tex:265`** — «La abstención ante un certificado inconcluso es distinta de declarar que la tarea es imposible.» **Patrón/motivo:** nominalización y contraste definitorio. **Cómo corregir:** decir qué estado devuelve el algoritmo cuando el certificado es inconcluso.
- **TF-065 · P1 · probable · `05-theoretical-framework.tex:267`** — «Esta literatura resuelve una parte esencial del transporte, pero suele comenzar después de que la composición física ya ha sido elegida.» **Patrón/motivo:** elogio vago más falsa concesión y generalización de corpus. **Cómo corregir:** identificar los trabajos y el supuesto de equipo dado.
- **TF-066 · P1 · probable · `05-theoretical-framework.tex:269`** — «Si los contactos cambian, un robot se retira o el \emph{wrench} solicitado no se realiza, la prueba debe incorporar explícitamente ese residual o restringirse al régimen de contacto fijo.» **Patrón/motivo:** terna de eventos y alternativa binaria perfectamente cerrada. **Cómo corregir:** separar contacto conmutado, retirada y residual; indicar cuál se estudia.
- **TF-067 · P1 · clara · `05-theoretical-framework.tex:271`** — «Esta diferencia justifica mantener separadas las ramas físicas: un certificado de soporte y \emph{wrench} para Cargo no prueba confinamiento, y un certificado geométrico de \emph{caging} no acredita reparto de soporte.» **Patrón/motivo:** colon y dos negaciones especulares. **Cómo corregir:** definir en positivo el objeto certificado por cada rama.
- **TF-068 · P2 · probable · `05-theoretical-framework.tex:271`** — «En ambos casos permanece el problema adicional de seleccionar y adaptar el equipo con información local.» **Patrón/motivo:** cierre abstracto y genérico. **Cómo corregir:** formular la variable de selección/adaptación que queda abierta.
- **TF-069 · P1 · probable · `05-theoretical-framework.tex:276`** — «Su bajo coste permite actuar en tiempo real, pero los mínimos locales impiden deducir llegada al destino \parencite{khatib1986obstacle}.» **Patrón/motivo:** falsa concesión `ventaja, pero limitación`. **Cómo corregir:** indicar el coste y luego, por separado, el contraejemplo de mínimo local.
- **TF-070 · P1 · probable · `05-theoretical-framework.tex:276`** — «Los obstáculos de velocidad trasladan la predicción de colisión al espacio de velocidades; RVO reparte la maniobra entre agentes y ORCA la expresa mediante semiplanos recíprocamente admisibles \parencite{vandenberg2008rvo,vandenberg2011orca}.» **Patrón/motivo:** punto y coma y tres métodos descritos de forma panorámica. **Cómo corregir:** comparar solo el supuesto relevante para la carga rígida.
- **TF-071 · P1 · probable · `05-theoretical-framework.tex:278`** — «Los certificados distribuidos permiten imponer separación entre robots, pero pueden necesitar frenado de emergencia y resultar conservadores \parencite{wang2017barrier}.» **Patrón/motivo:** `permiten..., pero pueden...` y dos limitaciones vagas. **Cómo corregir:** indicar la condición que activa frenado y la magnitud del conservadurismo.
- **TF-072 · P1 · probable · `05-theoretical-framework.tex:278`** — «Para una coalición Cargo, la barrera debe aplicarse a la huella compuesta o a una aproximación conservadora, no solo a los centros de los AMR.» **Patrón/motivo:** prescripción `X, no solo Y`. **Cómo corregir:** definir directamente la función de barrera sobre la huella elegida.
- **TF-073 · P1 · clara · `05-theoretical-framework.tex:280`** — «Del mismo modo, una velocidad nominal segura puede dejar de serlo después del reparto de \emph{wrench}, la saturación o la integración digital.» **Patrón/motivo:** transición mecánica, modal y terna. **Cómo corregir:** nombrar la etapa exacta que viola la desigualdad y el residual observado.
- **TF-074 · P1 · clara · `05-theoretical-framework.tex:280`** — «Conviene distinguir al menos tres estados: acción nominal, acción filtrada y acción realmente ejecutada.» **Patrón/motivo:** instrucción al lector, número seguro y regla de tres. **Cómo corregir:** definir los símbolos RAW, SAFE y EXEC directamente.
- **TF-075 · P2 · probable · `05-theoretical-framework.tex:282`** — «La recuperación añade otra transición entre capas.» **Patrón/motivo:** frase puente abstracta. **Cómo corregir:** describir el evento que reabre reclutamiento.
- **TF-076 · P1 · probable · `05-theoretical-framework.tex:282`** — «ALLIANCE usa impaciencia y aquiescencia para activar alternativas ante bajo desempeño, mientras las subastas dinámicas vuelven a adjudicar tareas después de eventos \parencite{parker1998alliance,nanjanath2006dynamicAuctions}.» **Patrón/motivo:** dos familias balanceadas en una sola frase. **Cómo corregir:** comparar su disparador y garantía en tabla.
- **TF-077 · P2 · probable · `05-theoretical-framework.tex:282`** — «Estos mecanismos muestran que tolerancia a fallos no equivale a mantener una asignación estática.» **Patrón/motivo:** sujeto vago y definición negativa. **Cómo corregir:** afirmar qué transición de estado requiere la tolerancia a fallos.
- **TF-078 · P1 · clara · `05-theoretical-framework.tex:284`** — «También debe distinguirse reparación mínima de reparación barata: eliminar miembros redundantes puede reducir coste, pero una dinámica local no garantiza escoger la combinación socialmente óptima.» **Patrón/motivo:** instrucción, colon, falsa concesión y negación de garantía. **Cómo corregir:** definir ambos objetivos y decir cuál optimiza el juego.
- **TF-079 · P1 · probable · `05-theoretical-framework.tex:284`** — «Si la capacidad remanente es insuficiente, abortar o detener la carga es un resultado correcto y no un fallo del reclutamiento.» **Patrón/motivo:** reformulación `es X y no Y`. **Cómo corregir:** clasificar explícitamente el estado como `inviable` según el certificado.
- **TF-080 · P1 · probable · `05-theoretical-framework.tex:288`** — «Reservar un vértice o una arista evita coincidencias discretas; no garantiza separación euclídea durante la interpolación ni respeta automáticamente la cinemática de una carga.» **Patrón/motivo:** punto y coma y doble negación correctiva. **Cómo corregir:** separar seguridad lógica de seguridad continua y nombrar la guardia requerida.
- **TF-081 · P1 · clara · `05-theoretical-framework.tex:288`** — «A la inversa, ORCA o una CBF pueden evitar colisiones locales sin resolver prioridades de pasillo y provocar bloqueo mutuo.» **Patrón/motivo:** transición especular y construcción `pueden X sin Y`. **Cómo corregir:** describir el caso de bloqueo y la capa de prioridad que falta.
- **TF-082 · P1 · probable · `05-theoretical-framework.tex:290`** — «Ninguna de estas garantías cubre por defecto pérdidas en ráfaga, particiones persistentes, decisiones enteras y una planta móvil dentro de un único resultado.» **Patrón/motivo:** negación totalizante y lista de cuatro. **Cómo corregir:** atribuir a cada fuente su dominio y formular después el hueco exacto.
- **TF-083 · P1 · clara · `05-theoretical-framework.tex:292`** — «La retransmisión periódica reduce la probabilidad de perder un estado congelado bajo modelos independientes, a costa de mensajes y bytes; la transmisión solo por evento reduce tráfico, pero puede mantener versiones ausentes.» **Patrón/motivo:** dos políticas simétricas, punto y coma y concesión. **Cómo corregir:** presentar la comparación con la ecuación y la métrica medida.
- **TF-084 · P1 · probable · `05-theoretical-framework.tex:292`** — «Por tanto, la evaluación de red debe reportar conectividad, edad o rezago de la información, carga comunicativa y calidad operacional.» **Patrón/motivo:** conector y lista de cuatro categorías. **Cómo corregir:** nombrar las métricas exactas usadas en SP8.
- **TF-085 · P2 · probable · `05-theoretical-framework.tex:297`** — «El contrato básico de cada familia se compara en la Tabla~\ref{tab:tf-comparison}.» **Patrón/motivo:** meta-frase y metáfora de contrato. **Cómo corregir:** decir qué dimensiones compara la tabla.
- **TF-086 · P1 · clara · `05-theoretical-framework.tex:324`** — «La tabla muestra que las familias no son intercambiables: cada una comienza con un objeto ya resuelto por otra.» **Patrón/motivo:** reader steering (`La tabla muestra`) y colon con generalización. **Cómo corregir:** afirmar la dependencia específica y citar las columnas.
- **TF-087 · P1 · clara · `05-theoretical-framework.tex:324`** — «Los métodos de asignación suponen una medida de utilidad; el control de formación supone un equipo; los filtros de seguridad suponen un control nominal; y MAPF supone una abstracción espacial y temporal.» **Patrón/motivo:** cuatro cláusulas idénticas separadas por punto y coma. **Cómo corregir:** usar una tabla de entrada requerida por familia.
- **TF-088 · P1 · probable · `05-theoretical-framework.tex:326`** — «Un método local puede reducir coste comunicativo y adaptarse sin coordinador, pero debe medirse su pérdida de calidad, su dependencia de conectividad y los casos en que no detecta acoplamientos remotos.» **Patrón/motivo:** falsa concesión y terna de evaluación. **Cómo corregir:** formular las métricas y escenarios concretos.
- **TF-089 · P1 · probable · `05-theoretical-framework.tex:326`** — «Ninguna etiqueta metodológica resuelve por sí sola ese intercambio.» **Patrón/motivo:** conclusión genérica/sentenciosa. **Cómo corregir:** sustituir por el trade-off cuantificable que evaluará SP8.
- **TF-090 · P1 · clara · `05-theoretical-framework.tex:328`** — «En conjunto, ambos paneles muestran cómo se fueron acoplando coordinación móvil, asignación, coaliciones, transporte, seguridad y comunicación \parencite{khatib1986obstacle,nakamura1989dynamics,bicchi1995closure,balch1998behavior,shehoryKraus1998Coalition,kube2000cooperative,gerkeyMataric2004MRTA,pereira2004caging,vigAdams2006Coalition,parkerTang2006ASyMTRe,fink2008caging,vandenberg2008rvo,choiBrunetHow2009CBBA,johnson2011acbba,alonsomora2017transport,ames2017cbf,shibata2023event,paul2023collective,ebel2024cooperative,shan2024collectiveTransport,zhou2026cttapf}.» **Patrón/motivo:** reader steering, lista de seis temas y veintiuna citas; *laundry list* de autoridad. **Cómo corregir:** dividir por dos o tres hitos con relación explícita; dejar el inventario en la figura/ledger.
- **TF-091 · P2 · probable · `05-theoretical-framework.tex:328`** — «La figura no constituye una bibliometría exhaustiva ni acredita resultados del TFM.» **Patrón/motivo:** doble descargo defensivo. **Cómo corregir:** incluir el alcance en la leyenda una vez y retirar repeticiones del cuerpo.
- **TF-092 · P1 · clara · `05-theoretical-framework.tex:330`** — «La Figura~\ref{fig:tf-methodological-map} sintetiza la arquitectura de los trabajos del corpus, no su calidad, impacto o rendimiento.» **Patrón/motivo:** `X, no Y` y terna negativa. **Cómo corregir:** «La figura representa únicamente indicadores de arquitectura...» y definirlos.
- **TF-093 · P1 · probable · `05-theoretical-framework.tex:330`** — «El eje horizontal distingue ejecución distribuida con información local de planificación central/global; el vertical distingue mecanismos explícitos de políticas aprendidas.» **Patrón/motivo:** dos definiciones paralelas con punto y coma. **Cómo corregir:** usar dos frases o etiquetas de eje autosuficientes.
- **TF-094 · P1 · probable · `05-theoretical-framework.tex:332`** — «Por ello aparece una franja intermedia poco poblada; no representa una discontinuidad teórica ni ausencia universal de literatura.» **Patrón/motivo:** `Por ello`, punto y coma y doble negación cautelar. **Cómo corregir:** describir el recuento que origina la franja y limitar la inferencia en una sola frase.
- **TF-095 · P2 · probable · `05-theoretical-framework.tex:332`** — «Las alturas de presentación evitan solapes y tampoco representan calidad ni rendimiento.» **Patrón/motivo:** tercera salvedad visual consecutiva. **Cómo corregir:** reunir todas las convenciones gráficas en la leyenda.
- **TF-096 · P1 · probable · `05-theoretical-framework.tex:332`** — «La auditoría completa de indicadores, cálculos y trabajos se conserva como artefacto reproducible en el repositorio.» **Patrón/motivo:** metacomentario de repositorio dentro de la prosa académica y terna. **Cómo corregir:** citar un anexo/metodología reproducible, sin narrar la estructura interna.
- **TF-097 · P2 · probable · `05-theoretical-framework.tex:419`** — «Una fuente puede contar en varios SP; no es una bibliometría exhaustiva.» **Patrón/motivo:** punto y coma y descargo ya repetido en línea 328. **Cómo corregir:** conservar la precisión una sola vez en la nota de figura.
- **TF-098 · P2 · probable · `05-theoretical-framework.tex:518`** — «Los ejes codifican arquitectura y explicitud del mecanismo; el color identifica la familia primaria.» **Patrón/motivo:** paralelismo de leyenda con punto y coma. **Cómo corregir:** usar dos frases cortas o una leyenda tabular.
- **TF-099 · P1 · clara · `05-theoretical-framework.tex:523`** — «La brecha está en las interfaces: MRTA cierra, consenso estima, juegos incentivan y control mueve equipos dados, pero su composición debe conservar exclusividad, mecánica, seguridad, recuperación y calidad bajo red imperfecta.» **Patrón/motivo:** eslogan, personificación de cuatro familias, colon y lista de cinco requisitos. **Cómo corregir:** formular una interfaz concreta de entrada/salida y su condición verificable.
- **TF-100 · P1 · probable · `05-theoretical-framework.tex:523`** — «El corpus verificado no contiene un método único que cierre todas esas interfaces mediante una arquitectura distribuida y explicable.» **Patrón/motivo:** afirmación de ausencia/novedad amplia; aunque se limita después, suena a *novelty framing*. **Cómo corregir:** «En las fuentes auditadas no se identificó...» e indicar fecha y criterio.
- **TF-101 · P2 · probable · `05-theoretical-framework.tex:523`** — «Esta conclusión está limitada a las fuentes auditadas y no equivale a afirmar una inexistencia universal.» **Patrón/motivo:** descargo defensivo posterior en lugar de alcance integrado. **Cómo corregir:** incorporar el límite en TF-100.
- **TF-102 · P2 · probable · `05-theoretical-framework.tex:525`** — «El método utiliza módulos separados de planificación, control, percepción y comunicaciones.» **Patrón/motivo:** lista de cuatro módulos sin interfaz. **Cómo corregir:** indicar qué señal pasa entre módulos.
- **TF-103 · P1 · probable · `05-theoretical-framework.tex:525`** — «Los experimentos evaluarán las interfaces entre esos módulos y determinarán en qué condiciones cumplen sus contratos.» **Patrón/motivo:** promesa futura genérica y doble verbo abstracto. **Cómo corregir:** nombrar las hipótesis, métricas y condiciones ya evaluadas; usar pasado si hay resultados.
- **TF-104 · P1 · clara · `05-theoretical-framework.tex:527`** — «La validación seguirá SP0--SP8 de forma incremental; cada resultado negativo delimitará las garantías de su capa.» **Patrón/motivo:** cierre genérico en futuro, punto y coma y personificación del resultado. **Cómo corregir:** cerrar con la pregunta exacta que SP0 responde o con el estado actual de evidencia.

### `thesis/sections/appendices/01-reproducibility.tex`

- **REP-001 · P2 · probable · `01-reproducibility.tex:4-6`** — «La trazabilidad distingue la regeneración completa de una campaña del reanálisis de observaciones archivadas.» **Patrón/motivo:** sujeto abstracto y apertura definitoria formulaica. **Cómo corregir:** «Una campaña es regenerable cuando...» y definir el criterio.
- **REP-002 · P2 · probable · `01-reproducibility.tex:5-6`** — «La Tabla~\ref{tab:reproducibility-status} declara esa frontera sin reconstruir a posteriori generadores que no están disponibles.» **Patrón/motivo:** personificación de tabla y metáfora `frontera`; negación defensiva. **Cómo corregir:** decir qué columna distingue ambos estados y qué artefactos faltan.
- **REP-003 · P2 · contextual · `01-reproducibility.tex:19`** — «Sin etiqueta ni DOI al cerrar esta revisión; deben fijarse tras consolidar el árbol.» **Patrón/motivo:** fragmento telegráfico y punto y coma en celda. **Cómo corregir:** usar sujeto explícito y dos frases: estado actual y acción pendiente.
- **REP-004 · P2 · probable · `01-reproducibility.tex:20`** — «\texttt{9278953cb6affebaf2aa96cb8581a6565177e767}; existen cambios posteriores no consolidados, por lo que este SHA no se presenta como instantánea final.» **Patrón/motivo:** dato, punto y coma y descargo negativo. **Cómo corregir:** separar el SHA registrado de la advertencia de versión no final.
- **REP-005 · P2 · contextual · `01-reproducibility.tex:47-48`** — «Jorge Luis Mayorga Taborda es responsable de la formulación, implementación, ejecución, análisis y redacción.» **Patrón/motivo:** lista nominal de cinco tareas con ritmo administrativo. **Cómo corregir:** mantener si es declaración de autoría exigida; si no, usar la taxonomía CRediT o una formulación más específica.

### `thesis/sections/appendices/02-sp0-proofs.tex`

- **SP0-001 · P2 · probable · `02-sp0-proofs.tex:4`** — «Las pruebas reúnen la frontera de complejidad, la caracterización del juego y los certificados de eficiencia usados en SP0.» **Patrón/motivo:** apertura formulaica y regla de tres. **Cómo corregir:** empezar por el primer resultado o explicar la dependencia entre los tres.
- **SP0-002 · P2 · contextual · `02-sp0-proofs.tex:4`** — «Todos los resultados suponen costes normalizados, un espacio de acciones finito y, cuando se indica, $\lambda>\kappa_{\max}$.» **Patrón/motivo:** segunda terna inmediata y parentético evasivo `cuando se indica`. **Cómo corregir:** asignar cada supuesto al resultado correspondiente.
- **SP0-003 · P2 · probable · `02-sp0-proofs.tex:28`** — «El espacio contiene $(K+1)^N$ perfiles, no puede repetirse ninguno y la trayectoria termina tras, como máximo, $(K+1)^N-1$ cambios.» **Patrón/motivo:** tres conclusiones coordinadas y parentético. **Cómo corregir:** separar cardinalidad y cota; hacer explícita la inyección entre cambios y perfiles.
- **SP0-004 · P2 · probable · `02-sp0-proofs.tex:28`** — «El argumento no cubre retardos, errores de estimación ni dinámica física.» **Patrón/motivo:** salvedad final en terna, repetida en casi todos los anexos. **Cómo corregir:** vincular cada exclusión al supuesto que la causa o concentrar límites en una nota común.
- **SP0-005 · P2 · contextual · `02-sp0-proofs.tex:59`** — «La cota puede ser conservadora y cuenta valores escalares en vez de paquetes.» **Patrón/motivo:** hedge genérico `puede ser` y contraste. **Cómo corregir:** indicar por qué es conservadora y definir la unidad de comunicación adoptada.

### `thesis/sections/appendices/03-sp1-proofs.tex`

- **SP1-001 · P2 · probable · `03-sp1-proofs.tex:4`** — «Las afirmaciones formales de la Sección~\ref{subsec:sp1} se demuestran para una decisión lógica estática con costes adimensionales, robots homogéneos y ocupación coherente.» **Patrón/motivo:** apertura formulaica, pasiva y terna. **Cómo corregir:** declarar los supuestos junto al primer enunciado.
- **SP1-002 · P2 · probable · `03-sp1-proofs.tex:4`** — «Los resultados no se extienden por sí solos a la dinámica Smith muestreada, la comunicación vecinal ni la factibilidad mecánica.» **Patrón/motivo:** salvedad automática en terna. **Cómo corregir:** explicar cuál paso de la prueba falla en cada extensión.
- **SP1-003 · P2 · contextual · `03-sp1-proofs.tex:13`** — «Por ello la relajación lineal tiene un óptimo entero y el problema se resuelve mediante flujo de coste mínimo en tiempo polinómico.» **Patrón/motivo:** transición mecánica que compacta dos consecuencias. **Cómo corregir:** separar integralidad del algoritmo de resolución.
- **SP1-004 · P2 · probable · `03-sp1-proofs.tex:15`** — «Así, la selección todo-o-nada bajo presupuesto es NP-difícil, mientras las cuotas obligatorias aditivas permanecen en la clase polinómica.» **Patrón/motivo:** `Así` y oposición simétrica. **Cómo corregir:** enunciar las dos clases por separado y remitir a la reducción/asignación.
- **SP1-005 · P2 · contextual · `03-sp1-proofs.tex:25`** — «El juego es, por tanto, de potencial exacto \parencite{monderer1996potential}.» **Patrón/motivo:** conector parentético en una conclusión que ya sigue inmediatamente de la identidad. **Cómo corregir:** «La identidad cumple la definición de potencial exacto».
- **SP1-006 · P2 · probable · `03-sp1-proofs.tex:35`** — «Finalmente, desde cualquier perfil inexacto existe una mejora, por lo cual ningún máximo global puede ser inexacto.» **Patrón/motivo:** cierre anunciado (`Finalmente`) y cadena de conectores. **Cómo corregir:** afirmar directamente la contradicción para un máximo inexacto.
- **SP1-007 · P2 · clara · `03-sp1-proofs.tex:35`** — «Esto completa la Proposición~\ref{thm:sp1-feasible-nash}.» **Patrón/motivo:** cierre de prueba genérico y metatextual. **Cómo corregir:** omitirlo; el final del argumento y el entorno ya indican cierre.
- **SP1-008 · P2 · probable · `03-sp1-proofs.tex:38`** — «La trayectoria alcanza así $\boldsymbol z_1=\boldsymbol0$ en un número finito de revisiones, lo que demuestra el Corolario~\ref{cor:sp1-strategic-regulation}.» **Patrón/motivo:** `así` más fórmula `lo que demuestra`. **Cómo corregir:** declarar la cota/terminación y dejar la referencia al final sin anunciar la demostración.
- **SP1-009 · P2 · probable · `03-sp1-proofs.tex:38`** — «El argumento se refiere al juego finito de mejora estricta y no prueba convergencia de Smith muestreado ni del cierre QR bajo escasez.» **Patrón/motivo:** salvedad `X y no Y ni Z`. **Cómo corregir:** integrar el dominio en el enunciado del corolario.
- **SP1-010 · P2 · probable · `03-sp1-proofs.tex:68`** — «El mapa describe el valor obtenido después del cierre y no prueba estabilidad de la dinámica continua ni optimalidad del parámetro.» **Patrón/motivo:** figura personificada y doble descargo. **Cómo corregir:** especificar en la leyenda que la figura es descriptiva y qué variable representa.

### `thesis/sections/appendices/04-sp2-proofs.tex`

- **SP2-001 · P2 · probable · `04-sp2-proofs.tex:4`** — «La propiedad de alineación marginal de la Sección~\ref{subsec:sp2} se limita a preferencias continuas, una matriz fija de contribuciones de servicio durante la decisión, umbrales positivos y parámetros adimensionales fijos.» **Patrón/motivo:** apertura de alcance con cuatro supuestos. **Cómo corregir:** vincular cada supuesto al enunciado formal.
- **SP2-002 · P2 · probable · `04-sp2-proofs.tex:4`** — «La prueba no establece cierre entero, optimalidad combinatoria, consenso vecinal, capacidad mecánica ni convergencia de una discretización concreta.» **Patrón/motivo:** lista de cinco negaciones, muy similar a otros anexos. **Cómo corregir:** concentrar las exclusiones en el enunciado o explicar la frontera matemática relevante.
- **SP2-003 · P2 · probable · `04-sp2-proofs.tex:31`** — «En consecuencia, el potencial de~\eqref{eq:sp2-potential} enlaza de forma continua las regiones $S_k<d_k^{\mathrm{srv}}$ y $S_k\geq d_k^{\mathrm{srv}}$, y su gradiente coincide con la puntuación marginal en ambas, con la derivada correspondiente en la frontera.» **Patrón/motivo:** conector mecánico y frase sobrecargada. **Cómo corregir:** separar continuidad del potencial y coincidencia del gradiente.
- **SP2-004 · P2 · clara · `04-sp2-proofs.tex:31`** — «Esto completa la Proposición~\ref{prop:sp2-marginal-alignment} dentro del alcance declarado.» **Patrón/motivo:** cierre genérico más salvedad formulaica. **Cómo corregir:** omitir o terminar con el resultado matemático concreto.

### `thesis/sections/appendices/05-sp3-proofs.tex`

- **SP3-001 · P2 · probable · `05-sp3-proofs.tex:4`** — «La propiedad de potencial y la equivalencia KKT del juego continuo de SP3 suponen demanda, geometría, costes y límites fijos, preferencias continuas sobre simplex y restricciones lineales de ocupación de puestos.» **Patrón/motivo:** apertura con lista de seis supuestos. **Cómo corregir:** dividir supuestos del juego y del conjunto factible.
- **SP3-002 · P2 · probable · `05-sp3-proofs.tex:4`** — «Quedan fuera el cierre entero, la guardia mecánica distribuida y la estabilidad física de la carga.» **Patrón/motivo:** segunda frase de exclusiones en terna; plantilla repetida. **Cómo corregir:** integrar la frontera en el título/enunciado de la proposición.
- **SP3-003 · P2 · contextual · `05-sp3-proofs.tex:36`** — «Por tanto, $\Phi_W$ es estrictamente cóncavo para $\alpha>0$.» **Patrón/motivo:** transición innecesaria tras identificar el Hessiano. **Cómo corregir:** unir la conclusión causalmente a la frase del Hessiano.
- **SP3-004 · P2 · probable · `05-sp3-proofs.tex:44`** — «De este modo, los maximizadores de la relajación y sus equilibrios variacionales coinciden.» **Patrón/motivo:** conector de cierre estándar. **Cómo corregir:** indicar que la sustitución satisface exactamente las KKT/VI.
- **SP3-005 · P2 · clara · `05-sp3-proofs.tex:44`** — «La equivalencia termina antes de decodificar $\rho^\star$ en decisiones binarias, lo que completa la Proposición~\ref{prop:sp3-wrench-potential} sin extenderla al cierre entero.» **Patrón/motivo:** personificación (`termina`), cierre `lo que completa` y salvedad. **Cómo corregir:** separar el dominio continuo de la referencia a la proposición; omitir el meta-cierre.

### `thesis/sections/appendices/06-sp4-proofs.tex`

- **SP4-001 · P2 · probable · `06-sp4-proofs.tex:4`** — «Las pruebas de SP4 cubren la convexidad fuerte del juego de vivacidad para una instantánea congelada y la disipación del servolazo planar de pose.» **Patrón/motivo:** apertura de cobertura formulaica. **Cómo corregir:** presentar los dos resultados como enunciados, no como mapa del anexo.
- **SP4-002 · P2 · probable · `06-sp4-proofs.tex:4`** — «No cubren convergencia global del sistema híbrido recedente, estabilidad con contacto conmutado ni validez de una representación cinemática como dinámica física.» **Patrón/motivo:** salvedad en terna. **Cómo corregir:** asignar cada exclusión al resultado al que afecta.
- **SP4-003 · P2 · clara · `06-sp4-proofs.tex:27`** — «Además,» **Patrón/motivo:** transición aislada antes de una ecuación; andamiaje visible. **Cómo corregir:** sustituir por «El Hessiano es...» sin conector.
- **SP4-004 · P2 · probable · `06-sp4-proofs.tex:31`** — «Por tanto, $J_G$ es $\alpha_4$-fuertemente convexo. El conjunto factible es la intersección del producto de simplex con $B\rho\leq\boldsymbol1$, luego es convexo y compacto. La acción esperar tiene ocupación nula y proporciona un punto de Slater. Existe un único minimizador $\rho^\star$.» **Patrón/motivo:** cuatro frases de longitud semejante, cada una cerrando un escalón; ritmo metronómico. **Cómo corregir:** agrupar Hessiano/convexidad y Slater/existencia en dos pasos explícitos.
- **SP4-005 · P2 · clara · `06-sp4-proofs.tex:40`** — «Así, el minimizador y el equilibrio variacional coinciden y son únicos, lo que completa la Proposición~\ref{prop:sp4-potential}.» **Patrón/motivo:** `Así` más `lo que completa`. **Cómo corregir:** terminar con la igualdad/unicidad y retirar el meta-cierre.
- **SP4-006 · P2 · probable · `06-sp4-proofs.tex:76`** — «Esta cota demuestra disipación perturbada, no convergencia exacta cuando el residual persiste.» **Patrón/motivo:** contraste `X, no Y`. **Cómo corregir:** formular en positivo la propiedad ISS/disipativa exacta que acredita la cota.
- **SP4-007 · P2 · clara · `06-sp4-proofs.tex:76`** — «Con ello queda probada la Proposición~\ref{prop:sp4-pose-stability} dentro de sus supuestos.» **Patrón/motivo:** cierre pasivo genérico y salvedad. **Cómo corregir:** omitir; los supuestos deben estar en el enunciado.

### `thesis/sections/appendices/07-sp6-proofs.tex`

- **SP6-001 · P2 · probable · `07-sp6-proofs.tex:4`** — «Los cuatro resultados formales de SP6-C suponen un fallo simple, una carga afectada, recursos aditivos no negativos, costes positivos y una reserva finita.» **Patrón/motivo:** apertura numerada y lista de cinco. **Cómo corregir:** repartir los supuestos entre los cuatro enunciados.
- **SP6-002 · P2 · probable · `07-sp6-proofs.tex:4`** — «Quedan fuera los contactos friccionales, las cargas que compiten por la misma reserva, los fallos simultáneos y la convergencia de la planta física después del reacoplamiento.» **Patrón/motivo:** segunda lista de cuatro exclusiones. **Cómo corregir:** explicar la única frontera estructural del modelo aditivo y derivar el resto.
- **SP6-003 · P2 · probable · `07-sp6-proofs.tex:18`** — «El conjunto de perfiles $\{0, 1\}^{n_R}$ es finito y no vacío. Por tanto, $\Phi_6$ alcanza un máximo global. En ese perfil ninguna desviación unilateral puede aumentar la utilidad, luego existe al menos un Nash puro.» **Patrón/motivo:** tres escalones cortos con `Por tanto/luego`; ritmo de demostración plantilla. **Cómo corregir:** condensar en una inferencia formal desde finitud hasta existencia de Nash.
- **SP6-004 · P2 · clara · `07-sp6-proofs.tex:18`** — «Esto demuestra el Teorema~\ref{thm:sp6-exact-potential}.» **Patrón/motivo:** meta-cierre genérico. **Cómo corregir:** omitir.
- **SP6-005 · P2 · probable · `07-sp6-proofs.tex:45`** — «Constituyen la caracterización completa de los Nash puros anunciada en el texto principal.» **Patrón/motivo:** referencia metadiscursiva a algo «anunciado» y énfasis `completa`. **Cómo corregir:** «Estas dos desigualdades son necesarias y suficientes...» y retirar la referencia narrativa.
- **SP6-006 · P2 · probable · `07-sp6-proofs.tex:68`** — «Resta demostrar minimalidad.» **Patrón/motivo:** transición de razonamiento estereotipada. **Cómo corregir:** iniciar directamente el argumento por contradicción.
- **SP6-007 · P2 · clara · `07-sp6-proofs.tex:73`** — «Cada miembro es, pues, crítico para al menos una componente. Esto completa el Teorema~\ref{thm:sp6-feasible-nash}.» **Patrón/motivo:** `pues` y meta-cierre consecutivos. **Cómo corregir:** terminar con la primera frase sin `pues`; omitir la segunda.
- **SP6-008 · P2 · probable · `07-sp6-proofs.tex:90`** — «Finalmente, una solución factible de coste mínimo es mínima por inclusión porque todos los costes son positivos.» **Patrón/motivo:** cierre anunciado y sintaxis previsible. **Cómo corregir:** enlazar la minimalidad directamente con positividad, sin `Finalmente`.
- **SP6-009 · P2 · probable · `07-sp6-proofs.tex:100`** — «Esta suma no prueba seguridad ante obstáculos ni estabilidad posterior al contacto.» **Patrón/motivo:** salvedad final doble, paralela a todos los anexos. **Cómo corregir:** integrar esas dos hipótesis en el enunciado de la cota temporal.
- **SP6-010 · P2 · probable · `07-sp6-proofs.tex:115`** — «Así, $\boldsymbol x^A$ es Nash.» **Patrón/motivo:** conclusión telegráfica con conector. **Cómo corregir:** «Por las dos desigualdades de desviación, $\boldsymbol x^A$ es Nash».
- **SP6-011 · P2 · clara · `07-sp6-proofs.tex:119`** — «No existe una cota uniforme de eficiencia para el peor Nash, aun bajo el umbral de factibilidad. Esto demuestra la Proposición~\ref{prop:sp6-unbounded-poa}.» **Patrón/motivo:** negación sentenciosa seguida de meta-cierre. **Cómo corregir:** terminar con la divergencia $M/2\to\infty$, que ya prueba la afirmación.
- **SP6-012 · P1 · probable · `07-sp6-proofs.tex:123`** — «La enumeración exhaustiva de los perfiles binarios comprueba, para cada mundo confirmatorio, la identidad de potencial ante toda desviación unilateral, las condiciones de Nash, la factibilidad, la minimalidad, el ascenso estricto y el límite de $2^{n_R}-1$ cambios.» **Patrón/motivo:** lista de seis comprobaciones y parentético. **Cómo corregir:** agrupar por propiedad o usar tabla de auditoría.
- **SP6-013 · P1 · probable · `07-sp6-proofs.tex:123`** — «Estas comprobaciones confirman los enunciados finitos, pero no sustituyen las demostraciones anteriores ni añaden garantías físicas fuera del modelo.» **Patrón/motivo:** falsa concesión y doble descargo de cierre. **Cómo corregir:** declarar en positivo que la enumeración verifica casos finitos; dejar el alcance físico en los supuestos.

### `thesis/sections/appendices/08-sp7-proofs.tex`

- **SP7-001 · P2 · probable · `08-sp7-proofs.tex:4`** — «Estas pruebas suponen catálogos finitos, recursos no ponderados, costes fijos, mensajes coherentes y movimiento muestreado sobre un grafo inflado.» **Patrón/motivo:** apertura con lista de cinco. **Cómo corregir:** repartir supuestos por resultado.
- **SP7-002 · P2 · probable · `08-sp7-proofs.tex:4`** — «No cubren dinámica continua, errores de localización, contacto ni red imperfecta.» **Patrón/motivo:** salvedad en lista de cuatro. **Cómo corregir:** explicar cuál premisa discreta excluye cada extensión.
- **SP7-003 · P2 · clara · `08-sp7-proofs.tex:18`** — «Toda mejora estricta aumenta $\Phi_7$, no repite perfil y termina en un Nash tras, como máximo, $\prod_i|\mathcal R_i^7|-1$ cambios. Esto prueba el Teorema~\ref{thm:sp7-exact-potential}.» **Patrón/motivo:** terna de consecuencias, parentético y meta-cierre. **Cómo corregir:** separar monotonía y cota; omitir la segunda frase.
- **SP7-004 · P1 · probable · `08-sp7-proofs.tex:23`** — «Su variación de potencial es $-\Delta B+\lambda_7\Delta P>0$ para $\lambda_7>\theta_7$: es inmediata si $\Delta B\leq0$ y, en otro caso, se sigue de $\lambda_7\Delta P>\theta_7\Delta P\geq\Delta B$.» **Patrón/motivo:** colon y caso doble encajado en una frase densa. **Cómo corregir:** presentar los dos casos en líneas o frases separadas.
- **SP7-005 · P2 · probable · `08-sp7-proofs.tex:23`** — «Por exactitud, el perfil conflictivo no es Nash.» **Patrón/motivo:** conector compacto y negación sentenciosa. **Cómo corregir:** nombrar la identidad de potencial que transfiere la mejora.
- **SP7-006 · P2 · probable · `08-sp7-proofs.tex:23`** — «Esta es la frontera de los pasillos y cuellos de botella.» **Patrón/motivo:** cierre metafórico y genérico. **Cómo corregir:** decir que esos escenarios incumplen la premisa de desviación unilateral reductora.
- **SP7-007 · P2 · probable · `08-sp7-proofs.tex:28`** — «Inicialmente cada zona está libre.» **Patrón/motivo:** apertura trivial y formulaica. **Cómo corregir:** formularla como hipótesis inicial del invariante.
- **SP7-008 · P2 · probable · `08-sp7-proofs.tex:28`** — «Este solo se libera después de observar la salida del propietario y cumplir el intervalo de despeje.» **Patrón/motivo:** antecedente pronominal ambiguo (`Este`: arbitraje o testigo). **Cómo corregir:** repetir `el testigo`.
- **SP7-009 · P2 · clara · `08-sp7-proofs.tex:28`** — «Además, el ejecutor conserva una propuesta por destino, rechaza intercambios opuestos y movimientos hacia agentes estacionarios.» **Patrón/motivo:** transición mecánica y regla de tres. **Cómo corregir:** formular la condición de autorización de movimiento en una sola regla.
- **SP7-010 · P2 · probable · `08-sp7-proofs.tex:28`** — «La exclusión lógica queda invariante.» **Patrón/motivo:** cierre sentencioso/passivo sin nombrar el conjunto invariante. **Cómo corregir:** expresar formalmente qué intersección permanece vacía.
- **SP7-011 · P1 · clara · `08-sp7-proofs.tex:33`** — «Si algún $j\in S$ nunca fuese elegido, las concesiones retirarían en tiempo finito a los demás hasta dejarlo como máximo, contradicción.» **Patrón/motivo:** remate telegráfico `, contradicción` y causalidad demasiado comprimida. **Cómo corregir:** separar la consecuencia y explicar por qué contradice la hipótesis.
- **SP7-012 · P2 · probable · `08-sp7-proofs.tex:33`** — «El argumento falla si un propietario no libera, aparecen solicitantes sin límite o un agente reingresa indefinidamente.» **Patrón/motivo:** lista final de tres fallos. **Cómo corregir:** convertirlos en hipótesis explícitas de liberación, finitud y no reingreso.
- **SP7-013 · P2 · probable · `08-sp7-proofs.tex:35`** — «Estos invariantes excluyen coincidencias de celda, no certifican distancia euclídea entre muestras.» **Patrón/motivo:** contraste `X, no Y`. **Cómo corregir:** definir la seguridad lógica acreditada y luego la propiedad continua ausente.
- **SP7-014 · P1 · clara · `08-sp7-proofs.tex:35`** — «Una carga extensa aún puede violarla si la interpolación, la orientación o la dinámica no respetan la inflación.» **Patrón/motivo:** pronombre ambiguo (`la`) y terna condicional. **Cómo corregir:** nombrar `la separación euclídea` y precisar qué modelo de huella/interpolación la viola.

### `thesis/sections/appendices/09-sp8-proofs.tex`

- **SP8-001 · P2 · probable · `09-sp8-proofs.tex:4`** — «Las propiedades siguientes suponen un grafo de comunicación no dirigido y fijo durante cada ejecución, con catálogos y costes constantes.» **Patrón/motivo:** apertura formulaica de alcance. **Cómo corregir:** asociar los supuestos a cada proposición.
- **SP8-002 · P2 · probable · `09-sp8-proofs.tex:14`** — «Así, $\Phi_8^G$ es potencial exacto bajo coherencia y toda mejora estricta termina tras, como máximo, $\prod_i|\mathcal R_i^8|-1$ cambios.» **Patrón/motivo:** `Así`, dos resultados compactados y parentético. **Cómo corregir:** separar identidad de potencial de la cota finita.
- **SP8-003 · P2 · probable · `09-sp8-proofs.tex:14`** — «Con copias obsoletas por retardo o pérdida, la identidad puede fallar y no se reclama mejora finita global.» **Patrón/motivo:** hedge (`puede`) y descargo impersonal. **Cómo corregir:** indicar la igualdad exacta que deja de cumplirse y limitar el teorema en su enunciado.
- **SP8-004 · P1 · probable · `09-sp8-proofs.tex:18`** — «En la primera, el término remoto no observable $\Gamma(a,r_j)$ vale $0$ y $\Gamma(b,r_j)$ vale $1$. En la segunda se intercambian esos valores.» **Patrón/motivo:** paralelismo de plantilla y segunda frase telegráfica. **Cómo corregir:** mostrar ambas instancias en una tabla de dos filas.
- **SP8-005 · P1 · probable · `09-sp8-proofs.tex:18`** — «El óptimo global exige decisiones opuestas, pero todo algoritmo determinista basado solo en el historial local produce la misma. No puede ser óptimo en ambas.» **Patrón/motivo:** falsa concesión seguida de frase corta con sujeto elíptico. **Cómo corregir:** nombrar el algoritmo y formular la contradicción en una sola inferencia.
- **SP8-006 · P2 · probable · `09-sp8-proofs.tex:18`** — «El mismo argumento hace indistinguibles una interacción remota nula y otra no nula.» **Patrón/motivo:** referencia genérica a `el mismo argumento`; omite la construcción. **Cómo corregir:** indicar qué observaciones coinciden en las dos instancias.
- **SP8-007 · P1 · probable · `09-sp8-proofs.tex:18`** — «Por ello ninguna regla estrictamente intracomponente garantiza, para toda la familia acoplada, optimalidad global ni detección de todas las interacciones remotas, como afirma la Proposición~\ref{prop:sp8-partition-limit}.» **Patrón/motivo:** conector, parentético, doble negación amplia y meta-referencia. **Cómo corregir:** formular el teorema de imposibilidad con cuantificadores y retirar `como afirma`.
- **SP8-008 · P2 · contextual · `09-sp8-proofs.tex:18`** — «Sí pueden existir garantías para familias restringidas con información común adicional.» **Patrón/motivo:** concesión final vaga; no nombra familia ni información. **Cómo corregir:** aportar una condición suficiente concreta o eliminar la frase.
- **SP8-009 · P2 · probable · `09-sp8-proofs.tex:22`** — «La cota no vale para pérdidas correlacionadas ni resuelve una partición con probabilidad efectiva de entrega nula.» **Patrón/motivo:** doble salvedad final. **Cómo corregir:** incorporar independencia y probabilidad positiva de entrega en el enunciado.

## Patrones estructurales transversales

1. **Apertura de alcance clonada en anexos.** SP0, SP1, SP2, SP3, SP4, SP6, SP7 y SP8 empiezan con `Las pruebas/Las afirmaciones/La propiedad/Los resultados...` y continúan con una lista de supuestos y otra de exclusiones. La precisión es necesaria, pero la matriz sintáctica se repite casi sin variación. Solución: colocar supuestos en cada teorema/proposición y abrir el anexo con la dependencia matemática específica.
2. **Cierre de demostración clonable.** Aparecen `Esto completa`, `Esto demuestra`, `Esto prueba`, `Con ello queda probada`, `lo que completa` y `como afirma la Proposición`. Son metacomentarios intercambiables. Solución: terminar en el hecho matemático; el entorno y la referencia ya indican qué se probó.
3. **Conectores en cadena.** `Por tanto` aparece 16 veces en el corpus asignado; `Por ello`, 5; `Así`, 8; `En consecuencia`, 3; `Sin embargo`, 3; `No obstante`, 1; `Además`, 2; `Finalmente`, 2. En pruebas algunos son legítimos, pero el patrón `ecuación → Por tanto/Así → meta-cierre` se repite demasiado. Solución: expresar la relación causal en el verbo o usar el símbolo de implicación cuando proceda.
4. **Contraste negativo como motor del marco.** Se repiten `no implica`, `no sustituye`, `no acredita`, `no equivale`, `no cubre`, `no garantiza`, `no representa` y `no consiste en..., sino...`. Muchas cautelas son científicamente correctas; juntas generan una voz de corrección automática. Solución: definir primero la propiedad positiva acreditada y añadir solo la limitación que cambia la inferencia.
5. **Regla de tres y listas de cuatro/cinco.** Son frecuentes `edad, alcance y error`, `simultaneidad, complementariedad y todo-o-nada`, `contacto, wrench, seguridad y recuperación`, `conectividad, variación, ganancias y discretización`, etc. Solución: conservar listas solo cuando las categorías sean exhaustivas y estén formalizadas; si no, priorizar la variable evaluada.
6. **Metanarración de figuras/tablas.** `La tabla muestra`, `La figura sintetiza`, `los paneles muestran`, `no constituye`, `no representa`, `la auditoría se conserva...`. Solución: describir el dato o codificación directamente y reunir las salvedades visuales en leyendas/notas.
7. **Laundry lists de citas.** Las líneas 76, 78, 82--89 y, sobre todo, 328 acumulan nombres/citas con una cláusula por fuente. Solución: organizar por mecanismo/supuesto, comparar dos o tres fuentes y llevar la cobertura completa al ledger o tabla.
8. **Copula avoidance y personificación.** `la tabla declara`, `la restricción afirma`, `la literatura resuelve`, `la brecha está`, `el contrato debe declarar`, `la equivalencia termina`, `el resultado delimitará`. Solución: usar sujetos concretos (`la ecuación certifica X bajo Y`; `en el corpus se observó Z`) o cópulas simples.
9. **Uniformidad rítmica.** Varios párrafos del marco tienen cuatro frases medianas con la misma progresión; SP6 y SP7 encadenan frases breves de un paso cada una. Solución: combinar pasos matemáticamente dependientes y dejar frases cortas solo para resultados realmente decisivos.
10. **Parentéticos y hedging.** La densidad de paréntesis del marco es alta por TikZ/matemática, pero en prosa destacan `cuando se indica`, `como máximo`, `bajo regularidad`, `por sí solos`, `puede`, `suele`, `rara vez`. No deben eliminarse si calibran una afirmación; deben sustituirse por supuestos o frecuencias verificables cuando existan.
11. **Puntuación.** No hay raya `—`; el problema no está en rayas. El punto y coma narrativo sí suele marcar cláusulas espejadas. Los dos puntos son legítimos ante ecuaciones y definiciones, pero huelen a plantilla cuando introducen listas retóricas (`Confundir...:`, `Conviene distinguir...:`, `La brecha...:`).
12. **Ausencias relevantes.** No se hallaron preguntas retóricas, `vamos a`, `cabe destacar`, `es importante señalar`, `en conclusión`, emojis, negritas persuasivas, sycophancy, disclaimers de fecha de corte ni lenguaje turístico/promocional.

## Prioridad de corrección posterior

1. Corregir primero TF-002, TF-003, TF-006, TF-007, TF-024, TF-026, TF-033--TF-038, TF-052, TF-067, TF-074, TF-083, TF-087, TF-090, TF-099--TF-104 y SP7-011/SP7-014: son los pasajes con señal más visible.
2. Después eliminar o variar los cierres `Esto completa/demuestra/prueba` de todos los anexos.
3. Integrar las salvedades en los enunciados formales, en vez de añadir listas negativas al inicio y al final.
4. Revisar las 26 apariciones narrativas de punto y coma del marco; conservar solo las que comparan objetos verdaderamente paralelos.
5. Mantener sin cambios los dobles guiones técnicos y la notación matemática: editarlos sería introducir errores, no humanizar la prosa.

## Evaluación final

El corpus no contiene señales groseras de chatbot ni vocabulario promocional. El olor a IA proviene casi enteramente de la **arquitectura retórica**: simetría, exhaustividad aparente, metanarración, listas de límites y cierres de prueba intercambiables. El marco teórico necesita una revisión de voz y selección bibliográfica; los anexos necesitan sobre todo desplantillar aperturas/transiciones/cierres sin tocar la lógica. Las entradas marcadas como **contextuales** deben revisarse con prudencia: muchas son matemáticamente correctas y solo resultan sospechosas por acumulación.

# Auditoría DETECT de patrones de escritura de IA — capítulo 6, índice y SP0–SP4

> Informe autónomo. No modifica ninguna fuente del repositorio.

## 1. Alcance, criterio y resultado global

Modo aplicado: **DETECT**. Se revisó el texto compilable completo de:

- `thesis/sections/mainmatter/06-results-and-analysis/index.tex`;
- `sp0.tex`, `sp1.tex`, `sp2.tex`, `sp3.tex` y `sp4.tex` en el mismo directorio.

Se leyó antes el contrato científico y académico (`docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`, más `docs/07_SP_SECTION_TEMPLATE.md`) y la versión 3.3.1 de `avoid-ai-writing`. Por ello, una cautela epistemológica, una enumeración formal, una lista de variables o una delimitación de alcance **no se marca por sí sola**. Sí se marca cuando se repite como plantilla, forma cadenas de negaciones, crea simetrías demasiado pulidas o sustituye una explicación concreta por metadiscurso.

Cobertura aproximada (las macros y las ecuaciones introducen un margen pequeño en el conteo de frases):

| Archivo | Frases revisadas | Palabras de prosa | `:` | `;` | `—` | `--` en prosa |
|---|---:|---:|---:|---:|---:|---:|
| `index.tex` | 46 | 828 | 5 | 4 | 0 | 3 |
| `sp0.tex` | 119 | 1.780 | 15 | 9 | 0 | 1 |
| `sp1.tex` | 110 | 1.659 | 16 | 13 | 0 | 2 |
| `sp2.tex` | 105 | 1.776 | 9 | 18 | 0 | 17 |
| `sp3.tex` | 117 | 1.832 | 9 | 16 | 0 | 8 |
| `sp4.tex` | 90 | 1.393 | 8 | 17 | 0 | 0 |
| **Total** | **587** | **9.268** | **62** | **77** | **0** | **31** |

El conteo incluye títulos, pies y celdas textuales, pero excluye ecuaciones, etiquetas, comandos de dibujo TikZ y el bloque desactivado por `\iffalse` en `sp1.tex:153–187`. Los 31 casos de `--` son rangos o compuestos técnicos de LaTeX (`SP0--SP8`, `0--1`, `robot--carga`, `primal--dual`, `Replicator--CBF`, intervalos de semillas); **ninguno funciona como raya enfática de estilo IA**. Tampoco hay raya Unicode `—`. Los puntos y coma de las tablas son mayoritariamente separadores legítimos de microcampos, aunque su acumulación en algunas celdas produce prosa telegráfica.

Resultado: **122 hallazgos**, ninguno P0. No aparecen artefactos de chatbot, tono adulador, atribuciones vagas del tipo «los expertos creen», inflación promocional, emojis ni vocabulario inglés Tier 1 usado con sentido publicitario. El olor principal procede de la estructura:

1. aperturas y cierres de SP construidos con la misma secuencia «incremento–garantía–límite–transición»;
2. cadenas de `no implica`, `no certifica`, `no demuestra`, `no se extiende` y `queda fuera`;
3. tríadas y listas simétricas, a veces en frases consecutivas;
4. ritmo metronómico de frases breves con sujetos abstractos (`la evidencia`, `la separación`, `la integración`, `el resultado`);
5. metadiscurso de tabla, figura o anexo que anuncia lo que el lector debe ver;
6. tablas con muchas cláusulas separadas por punto y coma y cierres negativos casi idénticos.

Escala:

- **P1:** olor claro o muy probable; conviene corregir antes de entregar.
- **P2:** pulido o patrón contextual; puede conservarse si la precisión técnica lo exige.
- **Clara:** construcción reconocible sin depender del gusto.
- **Probable:** el patrón emerge por densidad o repetición.
- **Contextual:** la frase aislada es válida; el problema aparece por recurrencia.

## 2. Hallazgos en `index.tex`

Cobertura: 46 frases. Los `:` sospechosos se concentran en la pregunta marco y en dos tríadas negativas; el `:` de H3 introduce datos y es funcional. Un `;` pertenece a una celda de tabla y los tres `--` son falsos positivos técnicos.

### IDX-001 — P1 · clara · `index.tex:4`

- **Frase exacta:** «El capítulo sigue una pregunta única: qué se pierde, y qué debe añadirse, cuando una asignación lógica se convierte en transporte cooperativo bajo fallos y comunicación imperfecta.»
- **Patrón/motivo:** apertura meta, pregunta indirecta bipartita y simetría «qué se pierde / qué debe añadirse». Suena a marco generado antes de llegar al objeto técnico.
- **Reparación:** abrir con la transformación concreta que estudia el capítulo y formular después la pregunta sin «el capítulo sigue».

### IDX-002 — P2 · contextual · `index.tex:4`

- **Frase exacta:** «SP0 fija el caso de referencia; los escalones siguientes incorporan cuotas, heterogeneidad, factibilidad mecánica, movimiento, seguridad, recuperación, tráfico y red.»
- **Patrón/motivo:** catálogo de ocho elementos tras punto y coma y metáfora de «escalones». La taxonomía es real, pero la frase reproduce un mapa de plantilla.
- **Reparación:** agrupar los SP por los cuatro bloques canónicos y reservar el detalle para la matriz, evitando enumerar ocho capas en una sola frase.

### IDX-003 — P2 · probable · `index.tex:4`

- **Frase exacta:** «El cuerpo conserva los enunciados y los supuestos necesarios para interpretar cada resultado; las pruebas completas se remiten a los anexos.»
- **Patrón/motivo:** metadiscurso editorial, pasiva refleja y balance artificial a ambos lados del punto y coma.
- **Reparación:** decir de forma directa qué material permanece en el capítulo y qué demostraciones concretas están en anexos, o trasladar esta información a una nota metodológica única.

### IDX-004 — P2 · probable · `index.tex:9`

- **Frase exacta:** «Costes estratégicos se normalizan. Magnitudes físicas conservan SI.»
- **Patrón/motivo:** dos frases telegráficas sin artículo; la segunda personifica las magnitudes («conservan») para evitar una cópula simple.
- **Reparación:** unirlas con sujeto y criterio explícitos: definir cómo se normalizan los costes y afirmar que las magnitudes físicas se expresan en SI.

### IDX-005 — P2 · probable · `index.tex:11`

- **Texto exacto:** «Los SP no comparten planta ni información. La Tabla~\ref{tab:results-model-map} separa decisión, agregados, cierre, certificado y planta. Cualquier lectura global limita la distribución completa.»
- **Patrón/motivo:** tres frases de longitud y sintaxis similares; lista de cinco sustantivos y cierre abstracto («distribución completa»).
- **Reparación:** identificar en una sola frase qué etapas usan información global y explicar la consecuencia arquitectónica con el término canónico «arquitectura híbrida».

### IDX-006 — P1 · clara · `index.tex:39`

- **Frase exacta:** «Las propiedades solo se transfieren si se conservan estado, información y modelo: equilibrio no certifica contacto, \emph{wrench} no garantiza seguimiento y exclusión discreta no prueba separación continua.»
- **Patrón/motivo:** regla de tres exacta, tres verbos negativos rotados y colon enfático. Es uno de los patrones más visibles del corpus.
- **Reparación:** formular una regla de no transferencia y desarrollar solo el ejemplo más relevante; llevar los otros dos a la tabla de interfaces.

### IDX-007 — P2 · probable · `index.tex:39`

- **Texto exacto:** «En Cargo son vecinales la propagación versionada y la revisión. Líder, registro y QP permanecen por carga/globales. La arquitectura es híbrida.»
- **Patrón/motivo:** cadencia metronómica de tres diagnósticos; frase nominal comprimida en el centro.
- **Reparación:** convertirlo en un contraste continuo que nombre funciones vecinales y funciones centralizadas, y concluir una sola vez que la arquitectura es híbrida.

### IDX-008 — P1 · clara · `index.tex:75`

- **Frase exacta:** «Los resultados dependen de interfaces: estabilidad unilateral no implica eficiencia, cobertura escalar no implica \emph{wrench} y reserva discreta no implica separación geométrica.»
- **Patrón/motivo:** repetición literal de «no implica» tres veces, simetría perfecta y colon de máxima general.
- **Reparación:** declarar que cada garantía se restringe a su interfaz y expresar dos fallos concretos con verbos distintos solo si añaden significado.

### IDX-009 — P2 · contextual · `index.tex:75`

- **Frase exacta:** «La ejecución integrada prueba compatibilidad sin transferir automáticamente las garantías de cada capa.»
- **Patrón/motivo:** sujeto abstracto, verbo amplio («prueba compatibilidad») y cautela genérica «automáticamente».
- **Reparación:** nombrar qué interfaces funcionaron juntas y qué garantías permanecen locales, sin el adverbio.

### IDX-010 — P1 · probable · `index.tex:77`

- **Texto exacto:** «SP0 elimina vacíos mediante penalización, aunque conserva posibles ineficiencias, y relaciona precios, conectividad y mensajes. SP1 muestra que el déficit no selecciona bajo escasez. Cuórum prioriza y QR cierra usando ordenación global. SP2 restaura integrabilidad marginal, pero mantiene cierre secuencial y servicio sin contacto.»
- **Patrón/motivo:** resumen por turnos SP0→SP1→SP2, frases casi intercambiables, falsa concesión y tríadas.
- **Reparación:** organizar el párrafo alrededor de una conclusión transversal —qué propiedad se añade y qué límite persiste— y usar los SP como evidencia, no como lista.

### IDX-011 — P1 · probable · `index.tex:79`

- **Texto exacto:** «SP3 redujo falsos positivos en $0.333$ sobre 600 mundos mediante geometría y actuadores, dentro de un QP planar. SP4 enlaza residual y pose con estabilidad local bajo contactos fijos y \emph{wrench} exacto, pero separa acoplamiento y transporte. KKT no sustituye planta ni servolazo.»
- **Patrón/motivo:** plantilla resultado–límite–aforismo; la última frase funciona como eslogan negativo.
- **Reparación:** conectar el resultado SP3 con la hipótesis de SP4 y expresar una sola limitación operativa con su efecto medible.

### IDX-012 — P2 · probable · `index.tex:81`

- **Texto exacto:** «SP5 elimina colisiones observadas del Hamiltoniano, pero conserva bloqueos. SP6 restaura 360 certificados recuperables. Algunos exceden el plazo porque la minimalidad estratégica y el reacoplamiento físico son distintos.»
- **Patrón/motivo:** tres frases cortas y uniformes; «Algunos» carece de denominador y el cierre usa una oposición abstracta.
- **Reparación:** dar el número o proporción que excede el plazo y vincularlo a una causa observada, no a que dos conceptos «son distintos».

### IDX-013 — P1 · probable · `index.tex:83`

- **Frase exacta:** «En SP8, retransmitir mejora $0.054$ la tasa y añade $261.3$ mensajes/agente, pero la calidad colapsa a mayor escala: la comunicación recupera observabilidad parcial sin restaurar conectividad.»
- **Patrón/motivo:** «colapsa» dramatiza; el colon introduce una moraleja abstracta de gran alcance.
- **Reparación:** indicar el tamaño en el que la tasa llega a cero y separar el efecto medido de la interpretación sobre observabilidad.

### IDX-014 — P1 · clara · `index.tex:85`

- **Texto exacto:** «Cargo integra tablas vecinales, reclutamiento, uniciclos, carga, obstáculo, fallo y reemplazo. Completa 359/360 misiones. Retirar seguridad o reparación reduce éxito $0.996/0.989$. Bajo red degradada, vecinal y perfecto completan 90/90. Vecinal usa 249.3 mensajes y 58.2~kB por mundo degradado.»
- **Patrón/motivo:** lista inicial extensa seguida de cuatro frases métricas con ritmo de boletín. Parece salida resumida automáticamente.
- **Reparación:** condensar composición, resultado principal y coste de red en dos frases; dejar las ablaciones secundarias en tabla.

### IDX-015 — P1 · probable · `index.tex:87`

- **Texto exacto:** «AWS prueba estrés con cuatro cargas, tráfico, batería y radios. En tres escenarios congestionados, todos agotaron $60$~s. Replicator--CBF se detuvo más que el predictor. Evitar solapamientos no corrigió el bloqueo, por lo que el replay no confirma Cargo.»
- **Patrón/motivo:** «prueba estrés» es una cópula evitada y vaga; cuatro frases de igual cadencia; «el replay no confirma Cargo» queda demasiado elíptico.
- **Reparación:** identificarlo como piloto cinemático, describir el fallo común y precisar qué propiedad de Cargo no se reproduce.

### IDX-016 — P1 · clara · `index.tex:89`

- **Texto exacto:** «Las capas son compatibles, pero carecen de una ventaja temporal demostrada. Propagación y selección son vecinales, mientras que el líder y las guardias operan por carga. La arquitectura no alcanza descentralización integral, convergencia híbrida ni validez industrial.»
- **Patrón/motivo:** falsa concesión, simetría «mientras que» y tríada negativa final de alcance creciente.
- **Reparación:** emitir un diagnóstico único: qué partes son vecinales, cuál es el componente central y qué afirmación concreta queda sin evidencia.

## 3. Hallazgos en `sp0.tex`

Cobertura: 119 frases. El único `--` es `0--1`. La mayoría de los `;` está en la tabla comparativa; los usos narrativos más visibles aparecen en el pie de escalado y en la síntesis.

### SP0-001 — P1 · probable · `sp0.tex:4`

- **Texto exacto:** «El análisis comienza con el único escalón cuya solución central es una asignación clásica. Hay $N\geq K$ robots intercambiables y $K$ cargas unitarias: cada carga recibe un robot, ningún robot atiende más de una y la posición solo determina el coste. Este caso permite comprobar el oráculo y las métricas antes de introducir coaliciones.»
- **Patrón/motivo:** apertura meta, metáfora de escalón, tríada tras colon y finalidad genérica «permite comprobar».
- **Reparación:** empezar con la definición del caso SP0 y cerrar con la pregunta experimental específica.

### SP0-002 — P1 · contextual · `sp0.tex:6`

- **Texto exacto:** «La penalización hace coincidir los Nash puros con las asignaciones factibles, pero no selecciona por sí sola el coste mínimo. De hecho, dos Nash pueden tener una razón de costes arbitraria (Anexo~\ref{app:proof-sp0-poa}). SP0 no modela movimiento, contacto ni red imperfecta.»
- **Patrón/motivo:** contraste «logra X, pero no Y», transición automática «De hecho» y tríada de exclusiones.
- **Reparación:** enunciar el resultado y el contraejemplo de forma directa; mover los tres límites al párrafo de alcance.

### SP0-003 — P2 · probable · `sp0.tex:10`

- **Texto exacto:** «La Figura~\ref{fig:sp0-scenario} distingue asociaciones, selección e inactividad. Las aristas representan decisiones y excluyen trayectorias o enlaces.»
- **Patrón/motivo:** metadiscurso de figura y tríada visual autoevidente.
- **Reparación:** explicar qué lectura errónea evita la figura o suprimir la primera frase si el pie ya identifica los elementos.

### SP0-004 — P2 · contextual · `sp0.tex:46`

- **Texto exacto:** «SP0: asociaciones admisibles (gris), selección final (azul) y robot libre para $N>K$. La figura no representa movimiento ni comunicación.»
- **Patrón/motivo:** pie en forma de inventario seguido de disclaimer negativo.
- **Reparación:** convertir el pie en una afirmación visual sobre exclusividad y dejar la ausencia de movimiento en el cuerpo.

### SP0-005 — P2 · probable · `sp0.tex:58`

- **Texto exacto:** «La salida es una asociación lógica, sin trayectoria ni control. SP3 introduce contacto y SP4 transporte.»
- **Patrón/motivo:** dos frases telegráficas y transición mecánica a SP posteriores.
- **Reparación:** relacionar explícitamente el límite de SP0 con la variable que se añadirá en SP3/SP4.

### SP0-006 — P2 · probable · `sp0.tex:71`

- **Texto exacto:** «Es el problema lineal de asignación: su relajación tiene vértices enteros y el húngaro lo resuelve en $O(N^3)$ tiempo y $O(N^2)$ memoria. SP0 pertenece a $\mathsf P$. La integralidad y la extensión con mochila 0--1 se prueban en el Anexo~\ref{app:proof-sp0-complexity}.»
- **Patrón/motivo:** secuencia demasiado limpia «definición–clase–prueba» y pasiva meta.
- **Reparación:** integrar clase, algoritmo y referencia a la prueba en un único argumento causal.

### SP0-007 — P2 · contextual · `sp0.tex:83`

- **Frase exacta:** «Las \emph{operaciones registradas} no son comparables entre algoritmos: cuentan entradas/aristas, utilidades por puja, acciones o pares candidatos según el método.»
- **Patrón/motivo:** negación + colon + lista heterogénea. La cautela es necesaria, pero su forma se repite en varios SP.
- **Reparación:** nombrar la unidad específica por método en la tabla y reducir la frase a una advertencia breve.

### SP0-008 — P2 · probable · `sp0.tex:85`

- **Texto exacto:** «Solo escala el bienestar. No altera orden, oráculo ni pagos.»
- **Patrón/motivo:** dos frases cortas consecutivas, énfasis con «Solo» y tríada negativa.
- **Reparación:** unirlas y especificar qué transformación numérica realiza $B$.

### SP0-009 — P2 · probable · `sp0.tex:117`

- **Texto exacto:** «Cubrir un vacío o retirar un duplicado mejora el pago porque $\lambda$ supera el coste. Ningún perfil con déficit o exceso es Nash. Desde una asignación factible, toda desviación crea uno de ambos. Solo las de coste mínimo maximizan el potencial.»
- **Patrón/motivo:** cuatro frases declarativas de longitud similar; cadencia de razonamiento generada paso a paso.
- **Reparación:** condensar la prueba en dos relaciones causales y remitir el detalle al anexo.

### SP0-010 — P1 · clara · `sp0.tex:133`

- **Texto exacto:** «La penalización garantiza cobertura y exclusividad. La selección eficiente requiere un criterio adicional. El 2-intercambio amplía el vecindario de mejora y puede corregir equilibrios unilaterales, aunque solo certifica estabilidad frente a los pares examinados.»
- **Patrón/motivo:** contraste binario garantía/selección y falsa concesión final.
- **Reparación:** presentar el 2-intercambio como respuesta concreta al límite y declarar su certificado local una sola vez.

### SP0-011 — P1 · clara · `sp0.tex:137`

- **Texto exacto:** «Se comparan húngaro, subasta-$\varepsilon$, voraz y dos mejores respuestas. Los dos primeros globales conocen la matriz. Mejor respuesta usa costes propios y ocupación agregada. $\lambda=0$ es ablación.»
- **Patrón/motivo:** cuatro frases telegráficas, una sin artículo, con estructura de inventario.
- **Reparación:** usar una frase comparativa que agrupe por contrato de información y otra que defina la ablación.

### SP0-012 — P2 · contextual · `sp0.tex:151–153`

- **Texto exacto:** «Brecha aditiva $\leq N\varepsilon$. No demuestra ejecución distribuida.» / «Factible. No equivale a MURDOCH y carece de cota.» / «Termina en Nash factible si $\lambda>\kappa_{\max}$. No es óptimo social.»
- **Patrón/motivo:** tres celdas consecutivas con patrón garantía breve + negación breve.
- **Reparación:** normalizar las celdas como «garantía / alcance» mediante sintagmas nominales, sin repetir «No…» en cada fila.

### SP0-013 — P1 · contextual · `sp0.tex:162`

- **Frase exacta:** «SP0 no integra planta, pero regula el perfil discreto $a$ mediante la salida…»
- **Patrón/motivo:** construcción «no X, pero Y» usada como apertura de bloque.
- **Reparación:** abrir directamente con la salida regulada y añadir después que el modelo es estratégico, no físico.

### SP0-014 — P1 · clara · `sp0.tex:183`

- **Texto exacto:** «El oráculo selecciona coste mínimo. El lazo solo regula cobertura y exclusividad. $\boldsymbol z_0=0$ no implica optimalidad.»
- **Patrón/motivo:** tríada de frases cortas, oposición oráculo/lazo y cierre «no implica».
- **Reparación:** expresar en una sola frase la diferencia entre objetivo del oráculo y conjunto regulado.

### SP0-015 — P2 · probable · `sp0.tex:189`

- **Texto exacto:** «Es una estabilización lógica por eventos. Quedan fuera la estabilidad física y la dinámica continua.»
- **Patrón/motivo:** etiqueta abstracta seguida del cierre plantillado «quedan fuera».
- **Reparación:** precisar qué propiedad de terminación se demuestra y evitar repetir una lista de exclusiones.

### SP0-016 — P2 · probable · `sp0.tex:192`

- **Frase exacta:** «Como resultado complementario, el Anexo~\ref{app:proof-sp0-local-prices} audita una asignación factible $\sigma_t$ mediante precios locales.»
- **Patrón/motivo:** transición de plantilla y personificación del anexo («audita»).
- **Reparación:** enunciar el certificado de precios como resultado auxiliar y poner la referencia al final.

### SP0-017 — P2 · probable · `sp0.tex:205–207`

- **Texto exacto:** «Para $N=K=5$ hubo $120$ Nash entre $7776$ perfiles y una única asignación óptima ($0.833\%$ de los equilibrios): factibilidad no selecciona eficiencia.» / «La Figura~\ref{fig:sp0-equilibrium-efficiency} muestra ambos hechos: multiplicidad de equilibrios y desigualdad de eficiencia dentro del conjunto factible.»
- **Patrón/motivo:** aforismo negativo tras colon y metadiscurso «muestra ambos hechos».
- **Reparación:** interpretar la proporción de equilibrios óptimos directamente y dejar que el pie describa la figura.

### SP0-018 — P2 · probable · `sp0.tex:231`

- **Texto exacto:** «El intercambio redujo la pérdida y obtuvo mediana cero, pero su cuartil superior fue $0.00065$. Este resultado no permite declarar optimalidad global. La subasta-$\varepsilon$ quedó prácticamente superpuesta al oráculo…»
- **Patrón/motivo:** doble cierre cautelar y adverbio vago «prácticamente» pese a disponer de una diferencia exacta.
- **Reparación:** reportar el cuartil y la diferencia exacta; eliminar «prácticamente» y formular una sola limitación.

### SP0-019 — P1 · clara · `sp0.tex:244`

- **Texto exacto:** «La ablación verifica la respuesta a los términos de déficit y exceso, pero no demuestra cardinalidad variable ni comunicación vecinal. Los tiempos observados hasta $N=64$ tampoco demuestran escalabilidad asintótica.»
- **Patrón/motivo:** dos negaciones de frontera consecutivas, «pero no demuestra / tampoco demuestran».
- **Reparación:** declarar qué hipótesis local sí respalda la ablación y reunir los alcances no evaluados en una sola frase.

### SP0-020 — P1 · clara · `sp0.tex:248`

- **Texto exacto:** «SP0 separa dos propiedades que el resto de la tesis no debe confundir. El juego potencial regula cobertura y exclusividad: con $\lambda>\kappa_{\max}$, todo Nash puro es factible. La eficiencia exige otra capa de selección. En las 200 instancias, el 2-intercambio redujo la brecha de la mejor respuesta, aunque no adquirió una garantía de optimalidad global. SP1 conserva esta distinción y reemplaza la demanda unitaria por cuotas; SP2 elimina además la equivalencia entre robots.»
- **Patrón/motivo:** cierre completo de plantilla: tesis, garantía, límite, evidencia, cautela y transición doble.
- **Reparación:** conservar resultado y limitación en dos o tres frases; trasladar la transición SP1/SP2 al inicio del apartado siguiente.

## 4. Hallazgos en `sp1.tex`

Cobertura: 110 frases. Los dos `--` son `0--1` y `robot--carga`. El bloque `\iffalse` no se renderiza y no se considera olor del documento final.

### SP1-001 — P1 · probable · `sp1.tex:6`

- **Texto exacto:** «SP1 rompe la correspondencia uno-a-uno de SP0: una carga puede requerir $n_k\in\{1,2,3,4\}$ robots. Cuando la demanda es realizable, déficit y exceso bastan para describir el cierre. Bajo escasez aparece el problema nuevo. El mismo déficit puede corresponder a recursos dispersos entre varias cargas o concentrados en una coalición completa.»
- **Patrón/motivo:** apertura por contraste, frase genérica «aparece el problema nuevo» y simetría dispersos/concentrados.
- **Reparación:** introducir directamente el contraejemplo mínimo y derivar de él la necesidad del cuórum.

### SP1-002 — P1 · clara · `sp1.tex:6`

- **Frase exacta:** «El operador QR impone el cierre entero y el beneficio de cuórum modifica esa selección; las poses continúan siendo parámetros de coste, no estados físicos.»
- **Patrón/motivo:** punto y coma equilibrado y cierre «A, no B».
- **Reparación:** separar mecanismo y alcance físico; definir el papel de las poses sin oposición retórica.

### SP1-003 — P2 · probable · `sp1.tex:67`

- **Texto exacto:** «La cuota no expresa masa, fuerza, torque ni compatibilidad. SP2 introduce servicio y SP3 mecánica.»
- **Patrón/motivo:** lista negativa seguida de una transición telegráfica a dos SP.
- **Reparación:** especificar que $n_k$ solo es cardinalidad y mover la hoja de ruta a la transición final.

### SP1-004 — P2 · probable · `sp1.tex:85`

- **Texto exacto:** «La cuota no vuelve NP-difícil todo SP1. Con cargas obligatorias y $\rho_D\leq1$, expandir $n_k$ plazas produce asignación o flujo polinómico. Con cargas opcionales… contiene mochila 0--1. La dificultad está en seleccionar grupos completos bajo escasez.»
- **Patrón/motivo:** secuencia simétrica «Con obligatorias / Con opcionales» y frase final de recapitulación.
- **Reparación:** mantener el contraste matemático, pero integrarlo en una explicación continua sin repetir la conclusión.

### SP1-005 — P2 · probable · `sp1.tex:89`

- **Texto exacto:** «MILP-Q fija el techo global, mientras que Greedy-Q aporta una selección secuencial. Smith genera preferencias y QR grupos exactos, separando cuórum y cierre. Ambos usan ocupación global.»
- **Patrón/motivo:** pares perfectamente balanceados y copula avoidance («fija», «aporta», «genera»).
- **Reparación:** agrupar los métodos por información y función con verbos concretos: resuelve, ordena o cierra.

### SP1-006 — P2 · contextual · `sp1.tex:104–107`

- **Texto exacto:** «Preferencias en el simplex. No cierra coaliciones ni hereda convergencia continua.» / «Ocupaciones $0$ o $n_k$. No es óptimo ni plenamente distribuido.» / «Conserva cierre; aísla la no linealidad de cuórum.»
- **Patrón/motivo:** celdas con frases mínimas y negaciones acumuladas.
- **Reparación:** usar una sintaxis uniforme «garantiza…; requiere…» y reservar la negación solo para la diferencia decisiva.

### SP1-007 — P1 · clara · `sp1.tex:113`

- **Texto exacto:** «CBBA es mono-ganador y no se ejecuta sin extensión verificada. \textcite{shehoryKraus1998Coalition,vigAdams2006Coalition} son contexto, no tratamientos.»
- **Patrón/motivo:** dos fronteras negativas consecutivas y construcción «son A, no B».
- **Reparación:** explicar por qué CBBA no es comparable en una frase y clasificar las otras fuentes en la tabla.

### SP1-008 — P2 · probable · `sp1.tex:137`

- **Texto exacto:** «Un robot libre cubre déficit. Sin libres, la realizabilidad implica exceso y un traslado mejora. Toda desviación desde cuota exacta crea déficit o exceso por encima del ahorro espacial.»
- **Patrón/motivo:** tres frases de prueba con cadencia paso a paso.
- **Reparación:** condensar los dos casos en un argumento por casos explícito.

### SP1-009 — P1 · probable · `sp1.tex:139`

- **Frase exacta:** «La conclusión cambia bajo escasez.»
- **Patrón/motivo:** transición genérica que anuncia importancia en lugar de exponerla.
- **Reparación:** sustituirla por la afirmación concreta: bajo escasez, $D_n$ deja de distinguir concentración y dispersión.

### SP1-010 — P2 · probable · `sp1.tex:150 y 204`

- **Texto exacto:** «La demostración completa está en el Anexo~\ref{app:sp1-scarcity-proof}.» / «La derivación del incremento discreto y del contraejemplo se conserva en el Anexo~\ref{app:sp1-scarcity-proof}.»
- **Patrón/motivo:** metadiscurso repetido sobre el mismo anexo; «se conserva» evita una cópula simple.
- **Reparación:** mantener una sola remisión, al final del enunciado o del bloque.

### SP1-011 — P2 · contextual · `sp1.tex:202`

- **Frase exacta:** «Esto justifica el término, pero no prueba selección global para toda instancia.»
- **Patrón/motivo:** «Esto» anafórico, falsa concesión y disclaimer genérico.
- **Reparación:** indicar exactamente qué propiedad justifica el contraejemplo y cuál requiere una prueba adicional.

### SP1-012 — P2 · probable · `sp1.tex:206`

- **Frase exacta:** «$\argmax_k\rho_{ik}$ no es una coalición ejecutable.»
- **Patrón/motivo:** aforismo negativo aislado; correcto, pero repetido en espíritu a lo largo del capítulo.
- **Reparación:** explicar la condición de cierre que falta, en lugar de dejar la negación sola.

### SP1-013 — P1 · clara · `sp1.tex:214`

- **Texto exacto:** «QR agrega de forma determinista la matriz completa para aislar el efecto del cierre. Los resultados verifican \eqref{eq:sp1-qr-invariants}. La realización vecinal y su coste de consenso quedan fuera del alcance experimental de SP1.»
- **Patrón/motivo:** secuencia método–verificación–limitación idéntica a otros SP y cierre «quedan fuera».
- **Reparación:** unir contrato de información y resultado; dejar una sola frase de alcance.

### SP1-014 — P2 · contextual · `sp1.tex:219–225`

- **Texto exacto:** «SP1 regula cardinalidad, aunque todavía no regula movimiento.» / «Con cargas obligatorias realizables… Bajo escasez…»
- **Patrón/motivo:** concesión «aunque todavía» y simetría de dos regímenes.
- **Reparación:** definir primero la salida estratégica y después distinguir los regímenes sin aludir al movimiento en la apertura.

### SP1-015 — P1 · clara · `sp1.tex:236`

- **Texto exacto:** «QR convierte las preferencias en la acción discreta… Se usó $\widehat q_{ik}=q_k$ y la matriz completa. Ambos son datos globales y no un observador vecinal.»
- **Patrón/motivo:** tres frases cortas y cierre «son A y no B».
- **Reparación:** declarar en una sola frase que la ejecución usa el agregado exacto global; reservar el observador vecinal para trabajo pendiente.

### SP1-016 — P1 · clara · `sp1.tex:242`

- **Texto exacto:** «La mejora finita se prueba en el Anexo… El resultado no se transfiere a Euler, Smith-QR ni escasez, sin estabilidad muestreada u optimalidad de $y$. Las poses siguen estáticas. SP2 cambia conteo por servicio, SP3 añade \emph{wrench} y SP4 movimiento.»
- **Patrón/motivo:** cadena prueba–no transferencia–estado–tríada de transición.
- **Reparación:** separar garantía del juego finito y método ejecutado; eliminar la hoja de ruta de tres SP.

### SP1-017 — P1 · clara · `sp1.tex:249, 252 y 255`

- **Texto exacto:** «\textbf{Verificación analítica.}» / «\textbf{Cierre entero.}» / «\textbf{Cuórum, calidad y resultado negativo.}»
- **Patrón/motivo:** tres pseudoencabezados en negrita dentro de una subsección corta; el último fuerza una tríada.
- **Reparación:** convertirlos en párrafos con primeras frases informativas o usar un único nivel de encabezado si la navegación lo exige.

### SP1-018 — P1 · probable · `sp1.tex:253`

- **Frase exacta:** «El efecto pertenece al operador QR: no demuestra que la preferencia continua converja a una asignación entera.»
- **Patrón/motivo:** sujeto abstracto («el efecto pertenece»), colon y negación cautelar.
- **Reparación:** decir que la ablación aísla QR y que no se evaluó convergencia de Smith, en dos proposiciones concretas.

### SP1-019 — P1 · clara · `sp1.tex:256`

- **Texto exacto:** «El cierre es necesario y el cuórum aporta una ventaja pequeña frente a su ablación, pero Smith-QR no supera al método voraz ni se confirma la hipótesis de exceso.»
- **Patrón/motivo:** frase de balance artificial con dos positivos, «pero» y doble negación.
- **Reparación:** separar los tres contrastes y asignar a cada uno su estimando y conclusión.

### SP1-020 — P1 · probable · `sp1.tex:278–282`

- **Texto exacto:** «Limitan la generalización la flota pequeña, el coste sintético, el cierre central y la ausencia de un comparador CBBA multi-ganador. La métrica de valor no incorpora transporte, seguridad ni mecánica.» / «La evidencia cambia con el régimen… SP2 abandona el conteo de robots y pregunta cuánto servicio aporta realmente cada pareja robot--carga.»
- **Patrón/motivo:** listas de cuatro y tres límites, cierre por plantilla y «realmente» como intensificador hueco.
- **Reparación:** priorizar la limitación que afecta a la inferencia principal; cerrar con el hallazgo cuantitativo, sin pregunta retórica al SP siguiente.

## 5. Hallazgos en `sp2.tex`

Cobertura: 105 frases. Los 17 `--` son compuestos o rangos técnicos. La mayor densidad de punto y coma se concentra en la tabla; tres usos narrativos también sostienen simetrías muy marcadas.

### SP2-001 — P1 · probable · `sp2.tex:6`

- **Texto exacto:** «Una coalición con la cardinalidad correcta todavía puede quedar por debajo de la demanda si sus miembros no aportan el mismo servicio. SP2 mantiene exclusividad, cierre y poses estáticas, pero asigna a cada pareja robot--carga una contribución distinta. El índice combina carga útil nominal, batería y distancia; no pretende representar fuerza, torque ni contacto. El análisis comprueba qué puntuación queda alineada con ese índice y dónde falla la aproximación antes de pasar al certificado físico de SP3.»
- **Patrón/motivo:** apertura de cuatro frases, dos tríadas, «pero», punto y coma negativo y metadiscurso «el análisis comprueba».
- **Reparación:** abrir con el contraejemplo de igual cardinalidad y distinto $S_k$; definir después el índice y su alcance una sola vez.

### SP2-002 — P2 · probable · `sp2.tex:10`

- **Frase exacta:** «Solo una supera diez unidades por carga nominal, batería y distancia.»
- **Patrón/motivo:** «Solo» enfatiza y la coordinación causal es ambigua: parece que las tres magnitudes producen directamente las unidades.
- **Reparación:** nombrar las dos coaliciones y decir cuál valor de $S_k$ supera el umbral.

### SP2-003 — P1 · probable · `sp2.tex:66`

- **Texto exacto:** «$a_{ik}$ es disponibilidad y $e_{ik}$ servicio normalizado. $c^{\mathrm{ref}}=1\,\mathrm{kg}$ conserva la escala adimensional sin convertir $e_{ik}$ en masa. La distancia penaliza la llegada y deja intacta la capacidad mecánica. Restricciones de soporte y balance energético serían independientes y no se evaluaron. La compatibilidad se fijó a uno.»
- **Patrón/motivo:** cinco frases telegráficas, sujetos abstractos y dos disclaimers consecutivos.
- **Reparación:** reunir definición, interpretación y supuestos en un párrafo de dos o tres frases con un sujeto estable.

### SP2-004 — P2 · contextual · `sp2.tex:87`

- **Texto exacto:** «$10^{-5}$ puntos/m solo desempata. \eqref{eq:sp2-capacity-oracle} maximiza razones de cobertura sin representar masa ni completitud. Su \emph{diferencia de cobertura} no acota otras métricas.»
- **Patrón/motivo:** tres frases cortas y dos fronteras negativas.
- **Reparación:** explicar el objetivo exacto y limitar la interpretación en una sola frase.

### SP2-005 — P1 · probable · `sp2.tex:108`

- **Texto exacto:** «Ambas referencias tienen ventaja global. Solo un certificado permite llamarlas exactas.»
- **Patrón/motivo:** «ventaja global» es vago y la segunda frase usa énfasis normativo abstracto.
- **Reparación:** especificar que reciben todos los $e_{ik}$ y demandas; indicar el estado del solver en la tabla.

### SP2-006 — P2 · probable · `sp2.tex:112`

- **Texto exacto:** «Los MILP separan cobertura y completitud. Se comparan reglas voraces, poblacionales, primal--dual, lineales y neuronales. Húngaro expandido y CBBA-capacidad son adaptaciones sin garantías heredadas.»
- **Patrón/motivo:** tres frases de inventario, cinco adjetivos de método y pasiva impersonal.
- **Reparación:** agrupar por objetivo e información, no por una lista de familias.

### SP2-007 — P1 · contextual · `sp2.tex:125–132`

- **Texto exacto representativo:** «Óptimo solo con certificado; objetivo distinto de cobertura.» / «Exacto solo para la aproximación. No es una reducción exacta de capacidad.» / «No transfiere invariancia ni convergencia…» / «Sin garantía… ni optimalidad.»
- **Patrón/motivo:** tabla con 18 puntos y coma y una sucesión de cierres negativos casi idénticos.
- **Reparación:** separar «garantía» y «límite» en dos columnas o usar sintagmas paralelos sin frases completas repetidas.

### SP2-008 — P2 · probable · `sp2.tex:141`

- **Frase exacta:** «Para aislar la propiedad estratégica, sea $\rho_{ik}\in[0, 1]$… y manténgase fija la matriz $E=[e_{ik}]$ durante el instante de decisión.»
- **Patrón/motivo:** apertura de demostración muy nominalizada y oración sobrecargada con incisos.
- **Reparación:** dividir supuesto de $E$ fija y definición de $\rho$ en dos frases; explicar qué efecto se aísla.

### SP2-009 — P2 · probable · `sp2.tex:152`

- **Texto exacto:** «La puntuación plana ignora contribuciones distintas. La marginal pondera la presión por la fracción de demanda cubierta.»
- **Patrón/motivo:** simetría binaria de dos frases con sujetos espejo.
- **Reparación:** expresar la diferencia algebraica en una frase vinculada a $e_{ik}/d_k^{\mathrm{srv}}$.

### SP2-010 — P1 · contextual · `sp2.tex:163`

- **Texto exacto:** «El campo plano no es, en general, integrable como potencial exacto… La conclusión no implica cierre entero, optimalidad combinatoria ni convergencia de una discretización concreta.»
- **Patrón/motivo:** triple frontera negativa al final de una proposición. Necesaria, pero idéntica a cierres de SP3/SP4.
- **Reparación:** conservar el supuesto que limita la proposición y trasladar las tres consecuencias a una nota de alcance común.

### SP2-011 — P2 · probable · `sp2.tex:167`

- **Texto exacto:** «La regla de la cadena prueba la alineación. La puntuación plana pierde simetría cruzada con heterogeneidad. El Anexo~\ref{app:sp2-marginal-proof} incluye la frontera saturada.»
- **Patrón/motivo:** tres frases de manual —prueba, interpretación, anexo— con ritmo uniforme.
- **Reparación:** condensar argumento e interpretación; dejar la referencia al final.

### SP2-012 — P1 · clara · `sp2.tex:169`

- **Texto exacto:** «Un robot requeriría $e_{ik}$, $(d_k^{\mathrm{srv}},V_k)$ y una estimación de $S_k$. Casi todas las reglas usaron déficit global. Solo primal--dual limitó radio. El experimento aísla la puntuación y deja pendiente el estimador. Las variantes Smith fueron ordenaciones, no EDO.»
- **Patrón/motivo:** cinco frases breves, énfasis «Solo», metadiscurso y cierre «A, no B».
- **Reparación:** distinguir en dos frases el contrato distribuido deseado y la información realmente ejecutada.

### SP2-013 — P1 · clara · `sp2.tex:173`

- **Frase exacta:** «La salida que SP2 intenta regular ya no es un conteo, sino el déficit relativo de servicio.»
- **Patrón/motivo:** construcción canónica «ya no X, sino Y».
- **Reparación:** afirmar directamente que la salida regulada es el déficit relativo y mencionar después la diferencia con SP1 si hace falta.

### SP2-014 — P1 · clara · `sp2.tex:192`

- **Frase exacta:** «La Proposición~\ref{prop:sp2-marginal-alignment} da estructura de gradiente con agregados exactos y $E$ fija, no estabilidad, convergencia discreta ni preservación tras cierre.»
- **Patrón/motivo:** «da estructura» evita una cópula y la frase termina con una tríada negativa.
- **Reparación:** especificar la identidad de gradiente demostrada; separar el alcance del resultado en una frase corta.

### SP2-015 — P1 · clara · `sp2.tex:194`

- **Texto exacto:** «El experimento no ejecutó~\eqref{eq:sp2-feedback-candidate}: ordenó secuencialmente y fijó $\widehat S_{ik}=S_k$ casi siempre. Posiciones, batería y $E$ son estáticos. El experimento no incluye una planta. SP3 introduce \emph{wrench} y SP4 transporte.»
- **Patrón/motivo:** colon de corrección, repetición «El experimento no», tríada y transición mecánica.
- **Reparación:** declarar una vez qué algoritmo se ejecutó y qué variables quedaron congeladas; eliminar la hoja de ruta.

### SP2-016 — P2 · contextual · `sp2.tex:197–199`

- **Texto exacto:** «La comparación utiliza… cinco familias de escenarios: ligero mixto, capacidad balanceada, capacidad pesada, batería limitada y Monte Carlo.» / «Se miden cobertura, completitud, brechas…, servicio…, alineación, distancia, energía, mensajes y CPU.»
- **Patrón/motivo:** listas de cinco y nueve elementos más varias pasivas impersonales. El protocolo exige detalle, pero el párrafo queda mecánico.
- **Reparación:** convertir escenarios y métricas en una tabla compacta; conservar en prosa solo factores y endpoint principal.

### SP2-017 — P1 · clara · `sp2.tex:201`

- **Texto exacto:** «Las observaciones permiten repetir análisis y figuras, pero no generar mundos nuevos. Esta carencia limita la simulación y conserva la reproducibilidad del recálculo presentado.»
- **Patrón/motivo:** falsa concesión y segunda frase autojustificativa; una carencia no «conserva» reproducibilidad.
- **Reparación:** indicar que los datos permiten reproducir el postproceso, pero no repetir la generación de instancias, sin convertir la limitación en virtud.

### SP2-018 — P2 · probable · `sp2.tex:205`

- **Frase exacta:** «La inversión confirma que repartir servicio parcial y completar tareas son objetivos diferentes.»
- **Patrón/motivo:** sujeto abstracto «la inversión» y conclusión autoevidente anunciada como confirmación.
- **Reparación:** cuantificar el intercambio y vincularlo a la diferencia entre los dos objetivos MILP.

### SP2-019 — P1 · clara · `sp2.tex:215`

- **Frase exacta:** «La Tabla~\ref{tab:sp2-main-results} conserva los valores exactos; la Figura~\ref{fig:sp2-results} permite leer tres relaciones que una clasificación única ocultaría: cobertura frente a completitud, calidad frente a CPU y efecto de la puntuación marginal.»
- **Patrón/motivo:** metadiscurso de lector, punto y coma, colon y regla de tres.
- **Reparación:** enunciar la relación principal; dejar tabla y figura como referencias parentéticas.

### SP2-020 — P2 · clara · `sp2.tex:220`

- **Frase exacta:** «Resultados de SP2: cobertura frente a completitud, calidad frente a coste y ablación de la puntuación plana frente a la marginal.»
- **Patrón/motivo:** pie construido como tres pares simétricos «X frente a Y».
- **Reparación:** describir qué codifica cada panel y cuál es el resultado visual principal.

### SP2-021 — P1 · probable · `sp2.tex:227`

- **Texto exacto:** «La corrección marginal elevó… y redujo… La completitud aumentó… El servicio… disminuyó… Estos cambios respaldan la ponderación…, no una trayectoria Smith que no se ejecutó.»
- **Patrón/motivo:** tres frases métricas con verbos paralelos y cierre de doble negación.
- **Reparación:** agrupar los efectos en una comparación principal y expresar aparte que la EDO Smith no se evaluó.

### SP2-022 — P1 · clara · `sp2.tex:237`

- **Texto exacto:** «Representar el déficit mediante un precio no basta si la selección dispersa capacidad o si la puntuación local no respeta la prioridad todo-o-nada. La ponderación marginal mejora la regla ensayada. El resultado no se extiende a cualquier método primal--dual.»
- **Patrón/motivo:** plantilla «no basta si X o Y», afirmación breve y disclaimer final.
- **Reparación:** vincular el fallo al método primal--dual concreto y a los datos observados; evitar generalizar para luego retractarse.

### SP2-023 — P1 · clara · `sp2.tex:239`

- **Texto exacto:** «El índice de servicio combina disponibilidad y llegada, pero no certifica capacidad física, energía de misión, fuerza ni torque. La mayoría de los métodos consulta el déficit agregado y no prueba un estimador vecinal. Las variantes poblacionales son ordenaciones secuenciales, no integraciones de sus EDO. El alcance se limita a los mundos evaluados.»
- **Patrón/motivo:** cuatro frases de frontera seguidas: «pero no», «no prueba», «A, no B», «se limita».
- **Reparación:** priorizar dos amenazas a la validez y explicar su consecuencia; eliminar la lista acumulativa.

### SP2-024 — P1 · clara · `sp2.tex:243`

- **Texto exacto:** «SP2 deja dos resultados distintos. Primero, ni la cardinalidad correcta asegura cobertura operacional ni una cobertura agregada alta asegura que las cargas se completen. Segundo… la ablación concentra mejor el servicio… La red neuronal… mientras primal--dual no superó al voraz.»
- **Patrón/motivo:** lista numerada inflada, doble «ni… ni», simetría y cierre «mientras».
- **Reparación:** convertir los dos resultados en un argumento causal continuo y separar el ranking empírico de la proposición formal.

### SP2-025 — P1 · probable · `sp2.tex:245`

- **Texto exacto:** «El umbral $S_k\geq d_k^{\mathrm{srv}}$ sigue siendo operacional. No certifica soporte, contacto, dirección de fuerza ni torque. SP3 reemplaza este índice por puestos geométricos y un conjunto de \emph{wrench} admisibles.»
- **Patrón/motivo:** límite en lista de cuatro seguido de transición de plantilla.
- **Reparación:** explicar cuál contraejemplo mecánico motiva SP3 y omitir la lista repetida.

## 6. Hallazgos en `sp3.tex`

Cobertura: 117 frases. Los ocho `--` son `0--1`, `primal--dual` o un rango de semillas. La tabla concentra la mayoría de los 16 puntos y coma.

### SP3-001 — P1 · probable · `sp3.tex:6`

- **Texto exacto:** «SP3 aborda el falso positivo que SP2 no puede detectar: una coalición puede cubrir un índice escalar y aun así ser incapaz de producir la fuerza y el torque requeridos. Para distinguir ambos casos, los robots se asignan a puestos con dirección de contacto y límites de actuador. El certificado es planar y cuasiestático, con carga fija y contactos conocidos. Rigidez tridimensional, transporte y \emph{caging} permanecen fuera del modelo.»
- **Patrón/motivo:** apertura por «falso positivo», colon, finalidad «Para distinguir», y tríada final «permanecen fuera».
- **Reparación:** abrir con el contraejemplo de wrench y definir de inmediato el certificado planar y sus supuestos.

### SP3-002 — P2 · probable · `sp3.tex:10`

- **Texto exacto:** «La Figura~\ref{fig:sp3-scenario} muestra robots, puestos, esfuerzos y centro de masa. Sumar capacidades no decide factibilidad geométrica.»
- **Patrón/motivo:** inventario de figura y aforismo negativo.
- **Reparación:** explicar qué configuración de puestos produce el residual o retirar la frase autoevidente.

### SP3-003 — P1 · probable · `sp3.tex:106`

- **Texto exacto:** «Hay factibilidad si $\rho_k^{W\star}\leq\epsilon_W$. \eqref{eq:sp3-wrench} es un certificado central. El oráculo enumera asignaciones pequeñas, resuelve esfuerzos y elige la mejor factible. Su exactitud solo cubre ese catálogo planar.»
- **Patrón/motivo:** cuatro frases breves y secuencia definición–arquitectura–procedimiento–límite.
- **Reparación:** integrar criterio, rol del QP y dominio del oráculo en dos frases.

### SP3-004 — P2 · probable · `sp3.tex:110`

- **Texto exacto:** «Cierre, contacto y confinamiento son distintos. Se comparan oráculo, referencias escalares, reglas y juegos con/sin guardia.»
- **Patrón/motivo:** tríada declarativa seguida de inventario impersonal.
- **Reparación:** precisar cuál de esas propiedades evalúa cada comparador.

### SP3-005 — P1 · contextual · `sp3.tex:123–130`

- **Texto exacto representativo:** «Selección 0--1; NP-dureza no demostrada; QP fijo en P.» / «Variante distribuida aproximada; sensibilidad, no teorema de red variable.» / «Mejora complementariedad local. No aporta optimalidad global ni distribución completa.»
- **Patrón/motivo:** celdas telegráficas, múltiples puntos y coma y cierres negativos repetidos.
- **Reparación:** separar clase, garantía y limitación en columnas distintas; evitar frases «No…» encadenadas.

### SP3-006 — P2 · probable · `sp3.tex:159`

- **Frase exacta:** «Todos los términos son adimensionales: residual marginal, coste $c_{ia}$, regularización $\alpha$ y precio de ocupación $\pi_a$.»
- **Patrón/motivo:** colon con inventario de cuatro nombres; correcto pero formular.
- **Reparación:** incorporar las unidades al definir cada término o usar una frase compacta que no repita la lista.

### SP3-007 — P2 · probable · `sp3.tex:167`

- **Texto exacto:** «La prueba está en el Anexo~\ref{app:sp3-wrench-proof}. El residual remunera soporte marginal y $\pi_a$ penaliza compartir puestos.»
- **Patrón/motivo:** metadiscurso de prueba y personificación de un residual.
- **Reparación:** colocar la referencia al final y explicar cómo el término marginal cambia el payoff.

### SP3-008 — P1 · probable · `sp3.tex:174`

- **Texto exacto:** «La proyección conserva simplex, sin eliminar el reloj digital. El anillo sustituye agregados por cuatro rondas vecinales y solo mide sensibilidad.»
- **Patrón/motivo:** dos frases de cautela con sujetos abstractos y énfasis «solo».
- **Reparación:** describir el integrador muestreado y el estimador de anillo con sus propiedades verificadas.

### SP3-009 — P1 · clara · `sp3.tex:176`

- **Texto exacto:** «El cierre discreto conserva un robot por puesto. La guardia evalúa~\eqref{eq:sp3-wrench}, añade hasta dos robots si hace falta y rechaza si no certifica. Toda carga aceptada cumple~\eqref{eq:sp3-certified-residual}. La reparación no es distribuida ni óptima.»
- **Patrón/motivo:** cuatro frases procedimentales uniformes y doble negación final.
- **Reparación:** presentar cierre y guardia como algoritmo secuencial; declarar su contrato global en una sola cláusula.

### SP3-010 — P1 · clara · `sp3.tex:178`

- **Texto exacto:** «Se combinan juego con precio, mercado residual, cierre pareado y guardia. Los tres primeros seleccionan. La guardia certifica. Un paso exacto cuesta… Los pares se limitan a dos robots.»
- **Patrón/motivo:** lista de cuatro, regla «los tres primeros», frases de dos y tres palabras y ritmo de esquema.
- **Reparación:** usar una frase que distinga selección y certificación, seguida del coste.

### SP3-011 — P2 · probable · `sp3.tex:182`

- **Texto exacto:** «SP3 separa selección estratégica y aproximación. Las salidas son error de \emph{wrench} y violación de puesto.»
- **Patrón/motivo:** apertura de bloque con verbo genérico «separa» y simetría binaria.
- **Reparación:** introducir directamente las dos salidas y explicar qué capa genera cada una.

### SP3-012 — P1 · clara · `sp3.tex:190`

- **Texto exacto:** «La variante exacta usa $\boldsymbol y_k$. El anillo, cuatro rondas.»
- **Patrón/motivo:** segunda frase fragmentaria y elipsis telegráfica.
- **Reparación:** indicar que la variante de anillo realiza cuatro rondas de consenso para estimar $\boldsymbol y_k$.

### SP3-013 — P1 · clara · `sp3.tex:192`

- **Texto exacto:** «La Proposición~\ref{prop:sp3-wrench-potential} caracteriza la relajación, no la convergencia de Euler, anillo o cierre. El residual KKT es métrica, no certificado distribuido.»
- **Patrón/motivo:** dos construcciones consecutivas «A, no B».
- **Reparación:** definir el alcance positivo de la proposición y del residual; reunir las exclusiones en una nota.

### SP3-014 — P1 · probable · `sp3.tex:194`

- **Frase exacta:** «El juego decide qué robot ocupa cada puesto, pero SP3 no simula la aproximación.»
- **Patrón/motivo:** falsa concesión usada como puente.
- **Reparación:** afirmar directamente que SP3 evalúa asignación de puestos con carga estática.

### SP3-015 — P1 · clara · `sp3.tex:203`

- **Texto exacto:** «En empuje, $\Lambda_{ik}$ sería unilateral y $\rho_k^{W\star}\leq\epsilon_W$ solo capacidad instantánea. \emph{Caging} requiere $q\in\mathcal C_k^{\mathrm{cage}}$. Este modo no se evaluó.»
- **Patrón/motivo:** tres frases de frontera muy cortas, una gramaticalmente elíptica.
- **Reparación:** condensar la delimitación de la rama E en una frase completa.

### SP3-016 — P2 · contextual · `sp3.tex:206–208`

- **Texto exacto:** «El experimento usa… seis familias de escenarios: …» / «Las métricas son precisión…, falsos positivos…, cobertura…, brecha…, residual…, CPU y mensajes.»
- **Patrón/motivo:** listas de seis escenarios, diez métricas y cuatro contrastes; densidad típica de protocolo generado.
- **Reparación:** trasladar factores, métricas y contrastes a una tabla de protocolo; dejar en prosa hipótesis, unidad experimental y endpoint principal.

### SP3-017 — P2 · probable · `sp3.tex:210`

- **Texto exacto:** «Los controles verifican finitud, simplex, exclusividad, complementariedad, potencial/QP y ausencia de aceptaciones inviables. El alcance se limita a los mundos evaluados.»
- **Patrón/motivo:** lista de seis y cierre genérico repetido.
- **Reparación:** señalar los dos invariantes más importantes y especificar qué dimensión del dominio limita la generalización.

### SP3-018 — P2 · probable · `sp3.tex:214 y 224`

- **Texto exacto:** «La Tabla… resume… Separa la calidad de la relajación de la factibilidad mecánica del cierre.» / «La Figura… separa la calidad del cierre de los falsos positivos mecánicos. Esta lectura es necesaria porque…»
- **Patrón/motivo:** metadiscurso duplicado «tabla/figura separa» y lector dirigido con «Esta lectura es necesaria».
- **Reparación:** exponer la comparación causal y citar tabla/figura al final.

### SP3-019 — P1 · clara · `sp3.tex:235 y 237`

- **Texto exacto:** «La guardia redujo… Por tanto, la capacidad escalar no garantizó…» / «El residual KKT fue… Por tanto, cuatro rondas locales no reprodujeron…»
- **Patrón/motivo:** dos párrafos consecutivos con exactamente la misma plantilla dato + «Por tanto» + negación.
- **Reparación:** variar la estructura: integrar efecto e interpretación en una frase y usar el segundo párrafo para comparar magnitud o mecanismo.

### SP3-020 — P1 · clara · `sp3.tex:240`

- **Frase exacta:** «La trayectoria representativa… muestra por qué el resultado de red se reporta como limitación y no como convergencia distribuida.»
- **Patrón/motivo:** metanarración, lector dirigido y construcción «como A y no como B».
- **Reparación:** describir el residual observado y concluir qué propiedad no se acreditó.

### SP3-021 — P1 · probable · `sp3.tex:250`

- **Texto exacto:** «El diseño divide mundos factibles e inviables. El oráculo conoce demanda, geometría y límites. Guardia y pares exceden vecindad estricta. No se miden formación, fuerzas verticales, deslizamiento, \emph{caging} ni estabilidad. La evidencia solo cubre el componente mecánico planar de H2.»
- **Patrón/motivo:** cinco frases cortas, lista de cinco ausencias y énfasis «solo».
- **Reparación:** convertirlo en un párrafo de amenazas a la validez con dos limitaciones priorizadas y su efecto.

### SP3-022 — P1 · clara · `sp3.tex:254`

- **Texto exacto:** «La campaña confirma la diferencia que motiva SP3: cubrir capacidad escalar no equivale a producir el \emph{wrench} requerido. La guardia… y el cierre… La Proposición… pero el anillo… y la guardia…»
- **Patrón/motivo:** cierre por plantilla con colon «no equivale», pareja de logros y pareja de límites.
- **Reparación:** cerrar con el efecto principal y una limitación arquitectónica; evitar recapitular todos los componentes.

### SP3-023 — P1 · probable · `sp3.tex:256`

- **Texto exacto:** «El certificado tampoco resuelve toda la mecánica. No incluye rigidez, soporte vertical ni control de formación, y la rama de empuje/caging no se ejecutó. SP4 parte únicamente de coaliciones que satisfacen…; sobre ellas añade dinámica y seguimiento de pose.»
- **Patrón/motivo:** «tampoco», doble negación, tríada y transición por punto y coma.
- **Reparación:** declarar el dominio planar del certificado y comenzar SP4 con sus supuestos de entrada.

## 7. Hallazgos en `sp4.tex`

Cobertura: 90 frases. No hay `--` en prosa. Trece de los 17 puntos y coma están en la tabla; los restantes sostienen paralelismos de dos procesos y de tabla/figura.

### SP4-001 — P2 · probable · `sp4.tex:6`

- **Texto exacto:** «Hasta SP3, la carga permanece inmóvil. SP4 introduce dos procesos temporales: los robots deben alcanzar sus contactos y, una vez acoplados, la carga debe seguir una referencia de pose con entradas limitadas. La factibilidad instantánea no basta; durante la aproximación puede haber colisiones y durante el transporte puede persistir error de pose por saturación.»
- **Patrón/motivo:** apertura de escalón, colon de dos procesos y paralelismo tras punto y coma.
- **Reparación:** definir las dos fases por sus estados y métricas, sin anunciar primero la progresión SP.

### SP4-002 — P1 · clara · `sp4.tex:8`

- **Texto exacto:** «Los dos procesos se evalúan en estratos separados. El acoplamiento usa uniciclos dinámicos con límites de par; el transporte usa una carga planar con contactos fijos. Esta separación permite atribuir los fallos, pero impide interpretar el experimento como una demostración extremo a extremo. Tampoco se simulan contacto físico ni empuje.»
- **Patrón/motivo:** simetría perfecta acoplamiento/transporte, sujeto abstracto «Esta separación», falsa concesión y «Tampoco».
- **Reparación:** explicar el diseño por estratos y su consecuencia inferencial en dos frases, con una sola delimitación final.

### SP4-003 — P2 · probable · `sp4.tex:12 y 49`

- **Texto exacto:** «La aproximación individual precede a la trayectoria de la carga… El \emph{wrench} de transporte se aplica después del acoplamiento.» / «Vista conceptual de SP4: aproximación a contactos y transporte de la carga entre poses.»
- **Patrón/motivo:** el cuerpo y el pie repiten la misma secuencia sin interpretación adicional.
- **Reparación:** usar el cuerpo para explicar la interfaz y el pie para identificar estados/variables visuales.

### SP4-004 — P1 · clara · `sp4.tex:74`

- **Texto exacto:** «\eqref{eq:sp4-control} actúa como oráculo híbrido global y difiere del algoritmo ejecutado. Sin reducción, su clase queda no establecida. La ejecución separa admisión, cierre, seguridad, acoplamiento y pose con \emph{wrench} acotado.»
- **Patrón/motivo:** copula avoidance («actúa como»), pasiva impersonal torpe («queda no establecida») y lista de cinco.
- **Reparación:** decir que la ecuación es la referencia global, que no se clasifica su complejidad y cómo se descompone el método ejecutado.

### SP4-005 — P2 · probable · `sp4.tex:78`

- **Texto exacto:** «En acoplamiento se comparan control directo/CBF, planificador y juego. En transporte, PD y Hamiltoniano reparten \emph{wrench}. SCP es referencia global.»
- **Patrón/motivo:** pares «En acoplamiento / En transporte» y tres frases de inventario.
- **Reparación:** agrupar por fase en una tabla y justificar en prosa un comparador por objetivo.

### SP4-006 — P1 · contextual · `sp4.tex:91–95`

- **Texto exacto representativo:** «Iteraciones de QP; global.» / «Guardia sin mecanismo de vivacidad; ejecución verificada.» / «VE único…; ejecución verificada, sin teorema global móvil.» / «Estabilidad local…; piloto planar, contacto fijo.»
- **Patrón/motivo:** alta densidad de punto y coma y garantías/límites con sintaxis casi idéntica.
- **Reparación:** dividir «tiempo» y «mensajes», y «resultado» y «límite» en columnas distintas.

### SP4-007 — P2 · contextual · `sp4.tex:126`

- **Texto exacto:** «Su convexidad fuerte garantiza un minimizador único. Bajo Slater, ese minimizador y los KKT del problema compartido coinciden con el equilibrio variacional único de la relajación.»
- **Patrón/motivo:** repetición próxima de «minimizador único / equilibrio… único». Es técnicamente correcta, pero suena mecánica.
- **Reparación:** conservar «único» donde aporta información y evitar repetirlo si la coincidencia ya lo implica.

### SP4-008 — P1 · contextual · `sp4.tex:128`

- **Frase exacta:** «La proposición no cubre el decodificador entero, el cambio temporal del grafo ni la convergencia de un número finito de iteraciones.»
- **Patrón/motivo:** tríada negativa formal idéntica a los cierres de SP2/SP3.
- **Reparación:** declarar el dominio positivo «instantánea continua congelada» y llevar las tres exclusiones a la discusión común.

### SP4-009 — P1 · probable · `sp4.tex:138`

- **Texto exacto:** «Replicator usa actualización multiplicativa. Los controles verifican simplex, capacidad y gradiente, no convergencia uniforme recedente.»
- **Patrón/motivo:** frase breve seguida de tríada y construcción «A, no B».
- **Reparación:** especificar qué controles numéricos pasaron y tratar la convergencia como pregunta no evaluada.

### SP4-010 — P2 · probable · `sp4.tex:148`

- **Texto exacto:** «Cada robot mide pose, velocidad, objetivo y conflictos. El juego elige acción y la guardia proyecta aceleración. El estado evoluciona como…»
- **Patrón/motivo:** tres frases funcionales de ritmo uniforme; lista de cuatro.
- **Reparación:** describir el flujo observación→decisión→control en una sola frase antes de la ecuación.

### SP4-011 — P1 · probable · `sp4.tex:168`

- **Texto exacto:** «El piloto usa pose simulada y no ejecuta el estimador $\hat q_k^L$. El agregado de transporte es central aunque el juego seleccione contactos.»
- **Patrón/motivo:** dos fronteras consecutivas, segunda con falsa concesión.
- **Reparación:** declarar el contrato de información completo del piloto en una frase.

### SP4-012 — P2 · probable · `sp4.tex:170`

- **Frase exacta:** «El candidato de almacenamiento sigue el enfoque de pasividad para sistemas mecánicos…, pero la demostración siguiente se realiza para la planta concreta de SP4.»
- **Patrón/motivo:** falsa concesión y metadiscurso «la demostración siguiente».
- **Reparación:** presentar el candidato y especificar directamente que la prueba se limita a la planta SP4.

### SP4-013 — P1 · contextual · `sp4.tex:179`

- **Texto exacto:** «El Anexo~\ref{app:sp4-pose-proof} demuestra el resultado. No se extiende a cambio de contacto, fricción desconocida, saturación persistente ni muestreo arbitrario.»
- **Patrón/motivo:** fórmula repetida prueba-en-anexo + lista negativa de cuatro.
- **Reparación:** colocar la referencia al final de la proposición y resumir el supuesto dominante: contactos fijos con realización no saturada.

### SP4-014 — P2 · contextual · `sp4.tex:184–186`

- **Texto exacto:** «El acoplamiento contiene… seis escenarios… seis semillas y once métodos… Cinco tratamientos… y seis… Un estudio con…» / «El acoplamiento mide éxito seguro, agotamiento, KKT y CPU. El transporte mide entrega, tiempo, error, trabajo y esfuerzo.»
- **Patrón/motivo:** sucesión de números y dos listas simétricas de métricas.
- **Reparación:** usar una tabla de diseño experimental y dejar en prosa unidad experimental, tamaño y endpoint primario.

### SP4-015 — P1 · probable · `sp4.tex:190`

- **Texto exacto:** «La guardia CBF eliminó colisiones y dejó abierta la vivacidad… Seguridad instantánea y llegada son objetivos distintos; la Figura~\ref{fig:sp4-docking-scenarios} localiza además los escenarios donde desaparece el progreso.»
- **Patrón/motivo:** metáfora «dejó abierta», sentencia binaria y figura personificada que «localiza» el problema.
- **Reparación:** reportar tasas de colisión, éxito y timeout; citar la figura como apoyo.

### SP4-016 — P2 · probable · `sp4.tex:210 y 220`

- **Texto exacto:** «La Tabla~\ref{tab:sp4-transport-results} muestra el compromiso.» / «Los valores exactos… están en la Tabla… La Figura… muestra que el control más rápido no es el que requiere menos trabajo mecánico.»
- **Patrón/motivo:** metadiscurso redundante de tabla/figura y construcción «no es el que».
- **Reparación:** enunciar el efecto tiempo–trabajo con sus diferencias y dejar referencias parentéticas.

### SP4-017 — P1 · clara · `sp4.tex:230`

- **Texto exacto:** «La separación limita la inferencia: acoplamiento no mueve carga y transporte parte acoplado. Cargo integra ambos y recuperación, pero con pose exacta y rigidez impuesta. La integración no demuestra menor tiempo bajo red local.»
- **Patrón/motivo:** sujeto abstracto, colon con par simétrico, falsa concesión y negación final.
- **Reparación:** especificar que no hay evidencia extremo a extremo en esta campaña y remitir la evaluación integrada a Cargo.

### SP4-018 — P1 · clara · `sp4.tex:234`

- **Texto exacto:** «SP4 aporta garantías locales para dos piezas, no para su composición completa. El juego instantáneo tiene un potencial exacto… y el servolazo estabiliza… Los experimentos muestran la frontera: una barrera sin coordinación puede bloquear… y en transporte existe un intercambio… SP5 conserva… pero introduce obstáculos…»
- **Patrón/motivo:** cierre de plantilla, «A, no B», colon de frontera, par simétrico y transición «conserva…, pero introduce».
- **Reparación:** cerrar con las dos garantías y el principal fallo observado; comenzar SP5 con el obstáculo nuevo.

## 8. Patrones transversales y orden de reparación recomendado

1. **Desactivar las cadenas de frontera.** Las cautelas son científicamente necesarias, pero su forma repetida delata plantilla. Crear una tabla transversal «garantía / dominio / no cubre» y dejar en cada SP solo la limitación que cambia la interpretación local.
2. **Reescribir aperturas y síntesis desde el dato o contraejemplo.** Las seis piezas empiezan o terminan con la misma coreografía. Abrir cada SP con su contraejemplo incremental y cerrar con una cifra o conclusión propia reduciría gran parte del olor sin perder rigor.
3. **Reducir metadiscurso visual.** Sustituir «la figura muestra», «la tabla separa», «permite leer» y «esta lectura es necesaria» por la afirmación analítica; la referencia puede ir al final.
4. **Romper el ritmo metronómico.** Combinar frases cortas consecutivas cuando forman una sola relación causal y dividir las oraciones que contienen dos listas o más de 30 palabras.
5. **Reestructurar tablas.** Muchas negaciones no proceden del contenido, sino de comprimir garantía y limitación en una misma celda. Separar columnas evitaría puntos y coma y frases «No…» repetidas.
6. **Mantener los falsos positivos técnicos.** No cambiar `robot--carga`, `primal--dual`, `0--1`, rangos de semillas, enumeraciones de propiedades formales ni listas de métricas cuando sean la representación más precisa; el problema es su densidad narrativa, no la notación.
7. **Eliminar intensificadores y sujetos abstractos evitables.** Casos concretos: «realmente», «prácticamente», «la inversión confirma», «esta separación permite», «la evidencia cambia» y «el resultado no se extiende».

## 9. Evaluación final

El texto no huele a IA por grandilocuencia ni por vocabulario promocional. Huele a IA por **regularidad editorial**: cada SP explica, delimita, enumera, remite al anexo, reporta y vuelve a delimitar con una sintaxis muy parecida. La prioridad no debe ser borrar precisión científica. Debe ser conservar una sola cautela donde ahora aparecen tres, reemplazar metadiscurso por interpretación y dejar que cada SP tenga una voz y un ritmo propios.


