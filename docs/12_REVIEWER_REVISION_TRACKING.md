# Trazabilidad del dictamen externo de `main(11).pdf`

Fecha de revisión: 2026-07-17. Este registro aplica la precedencia de `AGENTS.md`: el dictamen orienta la revisión científica, pero no sustituye el título administrativo ni la fidelidad comprobada de la plantilla VIU.

## Prioridad P0

| # | Observación | Estado | Resolución y evidencia |
|---:|---|---|---|
| 1 | Validación cuantitativa CoppeliaSim | **PARCIAL: PILOTO CINEMÁTICO CERRADO; GATE DINÁMICO ABIERTO** | Industrial 2 dispone de escena exportada, auditoría geométrica, replay cinemático validado y una campaña Python pareada de 32 ejecuciones. La memoria incorpora sus resultados negativos como C19. No valida Pioneer 3-DX, rueda--suelo, agarre cooperativo ni contacto 3D; `reviewer_dynamic_gate` continúa sin acreditar una planta dinámica independiente. |
| 2 | Contradicción AGV/AMR y título | **RESUELTA POR PRECEDENCIA** | `docs/00_TFM_CHARTER.md` y `thesis/metadata.tex` fijan el título administrativo con AMR. No se modifica sin aprobación expresa. AGV y AMR se definen en nomenclatura; el cuerpo usa el alcance técnico demostrado. |
| 3 | Cadena velocidad--aceleración--wrench de SP5 | **CERRADA** | `sp5.tex` define aceleración traslacional por diferencia finita, canal angular, wrench filtrado, reparto y margen aplicado. `payload_transport.py` implementa la transformación y `tests/test_sp5_payload_transport.py` comprueba dimensiones y saturación opcional. |
| 4 | Capacidad física frente a disponibilidad SP2 | **CERRADA** | SP2 separa carga útil `c_i^pay`, disponibilidad `a_ik` y servicio normalizado `e_ik`; el umbral histórico pasa a `d_k^srv`. SP3 conserva el primer certificado mecánico. Código, configuración, pruebas, notación y matriz de evidencia están sincronizados. |
| 5 | Restaurar generadores SP2/SP3 | **CERRADA DEFENSIVAMENTE** | Los generadores históricos completos no están en el árbol actual y no se inventan. SP2--SP4 se clasifican como reanálisis de observaciones archivadas; las secciones experimentales y el Anexo A declaran que no pueden reconstruirse íntegramente desde cero. |
| 6 | Reconciliar hipótesis y ejecución extremo a extremo | **CERRADA EN EL ALCANCE ACTUAL** | La campaña Cargo integra SP2--SP6 en una planta planar y se presenta como evidencia de composición, no como garantía híbrida ni validación industrial. La tabla transversal declara cada lectura global, cierre, certificado y planta. La transferencia dinámica independiente queda como limitación. |
| 7 | Preliminares en romanos | **SUPERADA POR INSTRUCCIÓN POSTERIOR DEL AUTOR** | Aunque la auditoría OOXML de la plantilla DOCX halló numeración arábiga continua, el autor instruyó después usar romanos en preliminares y reiniciar el cuerpo en 1. `docs/06_VIU_TEMPLATE_FIDELITY.md` conserva ambas evidencias y `thesis/main.tex` aplica la instrucción vigente. |
| 8 | Legibilidad de tablas metodológicas | **CERRADA Y VERIFICADA VISUALMENTE** | Las tablas SP0--SP7 dejaron tamaños manuales de 5,7--7 pt y usan `\scriptsize`. El PDF recompilado se inspeccionó en las páginas críticas; no hay desbordamientos y la tabla transversal es legible a página completa. |
| 9 | Nomenclatura incompleta | **CERRADA PARA LOS SÍMBOLOS CRÍTICOS** | Se añadieron `Q_W`, `G_C`, servicio SP2, cadena SP5, `D_6`, `lambda_6`, `delta_min`, rutas/conflictos SP7 y recursos/grafo SP8 a `frontmatter/04-nomenclature.tex`; `docs/05_NOTATION.md` conserva el inventario canónico completo. |
| 10 | Visibilidad de CoppeliaSim | **CERRADA EN EL ALCANCE CINEMÁTICO** | Metodología, resultados y conclusiones incorporan Industrial 2 como auditoría geométrica y piloto cinemático. El resumen y el abstract lo identifican sin atribuirle dinámica física ni rendimiento industrial. Se reporta el bloqueo de los tres escenarios congestionados y se mantiene abierta la validación dinámica tridimensional/hardware. |

## Prioridad P1

| Observación | Estado | Resolución |
|---|---|---|
| Nash de SP6 exactamente iguales a reparaciones mínimas | **CERRADA** | Teorema en el cuerpo, demostración bidireccional en Anexo G y prueba exhaustiva en `tests/test_sp6_recovery.py`. |
| PoS y PoA en SP0 y SP6 | **CERRADA** | SP0 y SP6 declaran `PoS=1` y ausencia de cota uniforme para `PoA`, con dominio, construcciones paramétricas y pruebas en los anexos respectivos. |
| Teorema de precios locales y `lambda_2` en SP0 | **CERRADA** | Elevado al cuerpo con cota de gap, contracción espectral, coste de mensajes e imposibilidad bajo desconexión; la prueba permanece en el Anexo B. |
| Equilibrio explícito del reparto de wrench | **CERRADA EN EL INTERIOR** | SP3 declara potencial y correspondencia KKT--equilibrio variacional; para el caso interior incluye la solución regularizada explícita. Con restricciones activas, la caracterización correcta sigue siendo el sistema KKT del QP. No se extiende al cierre discreto ni al contacto conmutado. |
| Estabilidad exponencial/ISS de SP4 | **ABIERTA** | Solo se acredita estabilidad asintótica local bajo contactos fijos y realización exacta. No hay hipótesis ni evidencia suficiente para elevarla a ISS o estabilidad exponencial. |
| Cobertura/abstención SP3 | **CERRADA** | El procesador y el cuerpo reportan cobertura `1,000`, abstención `0,500` y falsos positivos entre coaliciones retenidas, de modo que una precisión alta no se confunde con cobertura universal. |
| `lambda_2`, componentes y edad de información SP8 | **CERRADA CON MÉTRICA SEMÁNTICA** | Cada ejecución registra componentes, conectividad algebraica, conflictos remotos, rezago medio/máximo de versión y fracción de vistas ausentes. El cuerpo reporta los regímenes críticos y evita llamar edad temporal al rezago de una intención discreta. |
| Discusión transversal | **MEJORADA** | La nueva tabla de contrato distribuye decisión, agregado, cierre, certificación y planta, y evita heredar propiedades entre capas. |

## Prioridad P2

El pulido editorial se trata como una pasada separada para no mezclar cambios cosméticos con correcciones científicas. La versión actual usa verbos de evidencia acotados y mantiene APA mediante `biblatex`; las cinco incorporaciones de 2024--2025 fueron verificadas contra fuentes primarias y registradas en el ledger. Como control externo siguen recomendadas una auditoría independiente del corpus bibliográfico completo y una corrección ortotipográfica humana final.

## Segundo dictamen integral sobre la versión de 124 páginas

| Observación crítica | Estado | Resolución |
|---|---|---|
| Comandos `parencite` visibles | **CERRADA** | Se restauraron las barras invertidas en el Anexo B y la compilación busca comandos/citas sin resolver. |
| Posible factor erróneo en el potencial de SP2 | **OBJECIÓN NO CONFIRMADA** | La derivada de la integral normalizada coincide con el payoff implementado; se añadió una prueba numérica por debajo, en y por encima de la saturación. |
| Prueba de imposibilidad de SP8 demasiado fuerte | **CERRADA** | El resultado ya no afirma que toda partición cause colisión. Se demuestra indistinguibilidad para familias con acoplamientos remotos no observables y se limita la conclusión a optimalidad/detección uniforme. |
| Cobertura y abstención de SP3 | **CERRADA** | Tabla, macros, cuerpo y matriz de evidencia reportan cobertura 1,000, abstención 0,500 y falsos positivos condicionados a retención. |
| `TV(x;t)` sin definir en SP4 | **CERRADA** | El término, no implementado ni necesario para los resultados, se retiró del objetivo. |
| Contradicción sobre integración extremo a extremo | **CERRADA** | Hipótesis, SP4 y conclusiones distinguen campañas por componentes de la simulación Cargo integrada. |
| Alcance físico de Cargo y ablación de guardia | **CERRADA NARRATIVAMENTE; VALIDACIÓN FÍSICA ABIERTA** | Se declara registro global, reconstrucción de poses tras docking, ausencia de tracción durante transporte y ablación combinada de certificado, waypoint y filtro. |
| Pseudorreplicación entre escenarios/regímenes | **CERRADA** | Cargo agrupa 270 pares en 90 instancias para H2; SP8 agrupa 720 pares de régimen en 180 instancias. Se regeneraron IC, pruebas, tablas y manifiestos. |
| Orden y eventual inanición del token SP7 | **CERRADA CONDICIONALMENTE** | Se especifica el orden `(w_i,P_i,-i)` y se prueba ausencia de inanición bajo liberación acotada, solicitantes finitos y sin reentrada ilimitada. |
| Violación aplicada de SP5 | **CERRADA** | Se define como la fracción de muestras cuyo residual EXEC supera `1e-7`, después de reparto, saturación e integración. |
| Diagnósticos de red SP8 | **CERRADA** | Se reportan componentes, `lambda_2`, conflictos remotos, rezago de versiones y vistas ausentes. |
| Literatura 2024--2025 | **CERRADA** | Se incorporaron y delimitaron Shan, Dai, Qiu, Bezerra y Shida; el ledger distingue artículos revisados de preprints. |

## Tercer dictamen integral sobre la versión de 129 páginas

Por instrucción expresa del autor se conserva **AMR**. La recomendación de volver a AGV no se aplica: el término canónico y el título administrativo vigentes en el repositorio son los de `docs/00_TFM_CHARTER.md` y `thesis/metadata.tex`. La mención histórica de AGV en el marco teórico no altera el objeto de estudio.

| Observación | Estado | Resolución y evidencia |
|---|---|---|
| Atribución guardia/reparación en Resumen y Abstract | **CERRADA** | La guardia mecánica queda asociada a la reducción de falsos positivos de SP3 y el juego de reparación a la restauración del certificado de SP6. |
| Conteo SP8 de 4500 | **CERRADA DESDE EL GENERADOR** | La campaña contiene 4500 registros método--mundo: 4050 ejecuciones y 450 registros de oráculo no ejecutado fuera de su dominio certificado. El generador exporta ambos conteos y la prosa ya no los confunde. |
| Once métodos de SP4 frente a cinco reportados | **CERRADA** | SP4 identifica los cinco métodos principales de la tabla y las seis variantes diagnósticas/ablaciones secundarias que completan las 1188 ejecuciones. |
| `kappa^pad`, `D_0` y `P(N,K)` sin definición | **CERRADA** | Los dos primeros se definen antes de las ecuaciones que los usan; el anexo define `P(N,K)=N!/(N-K)!` como número de permutaciones parciales. |
| Justificación de `B=1.05` | **CERRADA** | SP0 declara costes normalizados y explica que el valor deja un margen positivo frente al máximo coste individual. |
| Separadores decimales y porcentajes faltantes | **CERRADA** | Se adoptó el punto decimal de forma uniforme por coherencia con código, tablas y artefactos; metodología declara la convención. Se restauró `95 %` en los tres intervalos de SP8. |
| DOI falso de Holm (1979) | **CERRADA** | Se retiró `10.2307/4615733`; la bibliografía y el ledger usan el registro estable de JSTOR y aclaran que no es un DOI. |
| Columnas temporales de Cargo | **CERRADA** | La nota metodológica especifica medias incondicionales sobre las 360 instancias, terminación por éxito o fallo y ceros de recuperación fuera del régimen aplicable. |
| Ambigüedad de `delta_ik`, `bar delta_ik` y `rho` | **CERRADA** | La nomenclatura distingue distancia física y normalizada y añade una nota explícita sobre las tres familias de `rho`. |
| Vídeos y nombre interno `capacity` | **YA AUSENTES** | La búsqueda del manuscrito actual no contiene la mención de vídeos ni el detalle de columna interna señalado por el dictamen. |
| Entorno, portabilidad y URL del repositorio | **CERRADA SALVO ARCHIVO INMUTABLE** | Metodología declara Python 3.11, dependencias, semillas, comandos Bash/PowerShell y URL de GitHub. Sigue pendiente crear un release archivado con DOI cuando el autor congele la entrega. |
| Rol de CoppeliaSim y elección de Python | **CERRADA EN EL ALCANCE DECLARADO** | La memoria justifica Python como entorno cuantitativo reproducible y reserva CoppeliaSim para geometría y replay cinemático. No se atribuyen contacto, actuadores, fricción ni validación de hardware. |
| Síntesis de qué es distribuido | **CERRADA** | La apertura de Resultados concentra la separación entre propagación/selección vecinal y líder, registro global y guardias no vecinales; la arquitectura se clasifica como híbrida. |
| Coste en bytes del registro global | **CERRADA COMO COTA INFERIOR** | Cargo explicita la contabilidad de 16 bytes de cabecera y 32 por registro anunciado, y que la consulta al registro queda excluida; por ello el valor reportado es una cota inferior. |
| Cota en línea de `lambda_6` y ausencia de CBS/ECBS | **CERRADA COMO TRABAJO FUTURO/DELIMITACIÓN** | Conclusiones proponen una cota conservadora basada en `delta_min`; SP7 explica que el oráculo enumera perfiles y órdenes del catálogo fijo de dos rutas, mientras CBS/ECBS cobraría sentido en un espacio de trayectorias más amplio. |
| Figura raster de SP3 | **CERRADA** | El generador produce ahora una figura PDF vectorial desde `summary.csv`; el cuerpo la incluye y su legibilidad se verificó sobre el PDF renderizado. |
| Patrones estilísticos tipo IA | **MITIGADOS** | Se podaron contrastes especulares, conectores y cierres formulaicos en las secciones de mayor visibilidad sin eliminar limitaciones científicas. No se introdujeron frases promocionales ni afirmaciones más fuertes. |
| Extensión VIU | **ABIERTA: RIESGO ADMINISTRATIVO** | La versión recompilada tiene 139 páginas; el cuerpo ocupa 101 páginas (13--113), por encima de 50--80. Los anexos ocupan 20 páginas (120--139), justo en el máximo permitido. Reducir el cuerpo exige una edición estructural separada para no eliminar evidencia. |
| Validación dinámica independiente | **ABIERTA** | Industrial 2 sigue siendo un piloto geométrico/cinemático. No hay evidencia de contacto tridimensional, fricción, actuadores, sensores reales ni hardware. |

## Verificación ejecutada

- `python -m pytest -q`: 74 pruebas superadas.
- Campañas confirmatorias regeneradas: Cargo, 360 mundos y 2160 ejecuciones; SP8, 900 mundos, 4500 registros y 4050 ejecuciones; SP3, tabla, macros y figura vectorial actualizadas.
- Compilación limpia: PDF A4 de 139 páginas generado sin errores LaTeX, referencias/citas indefinidas ni cajas `Overfull`.
- Resumen/abstract: 294/293 palabras en el PDF, dentro del intervalo VIU de 200--300.
- Revisión visual rasterizada: resumen, abstract, introducción, objetivos, hipótesis, metodología, matriz de operacionalización, conclusiones y Anexo A; sin cortes ni desbordamientos críticos.

## Cuarto dictamen integral sobre `main(13)`

Este dictamen desplaza el trabajo desde la ampliación científica hacia el cierre formal. Los estados siguientes distinguen correcciones realizadas, decisiones expresas del autor y dependencias externas que no deben simularse.

| Observación | Estado | Resolución y evidencia |
|---|---|---|
| Extensión: cuerpo por encima de 80 páginas | **CERRADA** | Referencias comienza en la página 81: el cuerpo ocupa exactamente 80 páginas. Los gráficos redundantes permanecen como artefactos procesados; cada SP conserva diagrama, formulación, comparación, tabla numérica y cierre. El PDF completo tiene 116 páginas. |
| Texto principal de anexos menor que Arial 12 | **CERRADA Y VERIFICADA** | Se retiraron los grupos `\footnotesize` de SP4, SP6 y SP7. Las pruebas rutinarias de SP7 y SP8 se condensaron; se preservan integrabilidad SP2, KKT--VE SP3, estabilidad local SP4, Nash/PoS/PoA SP6 e imposibilidad SP8. Los anexos ocupan 18 páginas (87--104) y la muestra rasterizada confirma Arial 12 en el cuerpo. |
| Título AGV frente a AMR | **DECISIÓN EXPRESA DEL AUTOR: AMR** | El dictamen atribuye AGV al Anexo I, pero `docs/00_TFM_CHARTER.md` y la instrucción expresa registrada por el autor fijan AMR. No se cambia el título sin una orden administrativa posterior; la discrepancia debe resolverse fuera del manuscrito si coordinación aporta un documento de mayor precedencia. |
| Preliminares romanos y reinicio arábigo | **CERRADA POR INSTRUCCIÓN DEL AUTOR** | `thesis/sections/frontmatter/00-cover.tex` inicia preliminares en romanos y `thesis/main.tex` reinicia la Introducción en 1. `docs/06_VIU_TEMPLATE_FIDELITY.md` declara que esta decisión prima sobre el patrón OOXML auditado. |
| Encabezado con nombre del estudiante | **OBJECIÓN NO APLICADA** | El DOCX oficial auditado solo contiene el título en encabezado. Se conserva esa fidelidad mientras no exista una instrucción administrativa verificable de mayor precedencia. |
| Release, etiqueta, SHA y archivo inmutable | **ABIERTA; DEPENDENCIA EXTERNA** | El repositorio aún no está congelado. La memoria no afirma que exista una release. Crear etiqueta, commit final, release o DOI exige la decisión del autor y se ejecutará después de cerrar contenido y pruebas. |
| H1 atribuye a cuórum el cierre producido por QR | **CERRADA** | H1 se divide en H1a (cuotas realizables), H1b (QR elimina grupos parciales) y H1c (efecto incremental del cuórum con QR fijo). Metodología, SP1, conclusiones y `docs/04_CLAIMS_EVIDENCE.md` conservan la misma atribución. |
| Potencial SP8 extendido indebidamente a vistas obsoletas | **CERRADA** | Cuerpo y Anexo I exigen `\widehat r_{ij}=r_j` para cada actualización cubierta por la identidad. Con retardo o pérdida no se reclama secuencia global de mejora; terminación y calidad quedan como observaciones empíricas. |
| Cargo no reconstruible desde la memoria | **CERRADA EN EL MODELO IMPLEMENTADO** | Cargo explicita conjunto visible, diez eventos, líder temporal, consulta al registro, puntuación exacta, desempate por ID, cierre agregado, abstención, reapertura, reparación, complejidad y registros. Un algoritmo numerado y una tabla comparan sus fases con SP2--SP6. |
| «Colisión» excede la métrica observada | **CERRADA** | La tabla usa «Intersección huella--obstáculo» y el texto limita 359/360 a la fase de transporte y a la huella compuesta. No se extiende a aproximación, robot--robot ni contacto 3D. |
| Industrial 2 desproporcionado | **CERRADA** | La sección se redujo a una imagen, 32 ejecuciones, resultado principal y alcance piloto. Las matrices completas permanecen en los artefactos procesados. |
| Nomenclatura incompleta | **CERRADA Y VERIFICADA** | Se añadieron AWS, KKT, QP, PD, BNN, QR, CBBA, HOCBF, VO/RVO/ORCA, MAPF, CBS/ECBS, CPU, IC, VE y LAP; la nomenclatura recompilada se verificó visualmente. |
| Etiquetas SP2 «Smith/replicator» | **CERRADA DESDE EL GENERADOR** | El generador y los artefactos regenerados usan «Puntuación inspirada en Smith/replicator»; no se atribuye la integración de las EDO a estas puntuaciones estáticas. |
| Brecha SP8 de 0.497 solo en conclusiones | **CERRADA** | SP8 presenta la media sobre 450 mundos certificados y define la normalización respecto al oráculo antes de reutilizarla en RQ5. |
| Convención de nombres | **CERRADA EN EL MANUSCRITO** | Se unificaron Greedy/Greedy-Q/Greedy por distancia como etiquetas de método; “método voraz” queda como descriptor genérico en prosa. |
| Acabado APA | **PARCIAL** | Se corrigieron los DOI espaciados señalados, el título de Chen--Sun y la referencia estable de Holm. Una auditoría bibliográfica completa permanece como control final, sin inventar ni retirar fuentes verificadas. |

### Verificación del cierre técnico

- PDF A4 de 116 páginas: cuerpo 1--80, referencias 81--86 y anexos 87--104 (18 páginas).
- Resumen/abstract: 300/298 palabras.
- `python -m pytest -q`: 74 pruebas superadas.
- Compilación completa con Biber: sin referencias/citas indefinidas ni cajas `Overfull`; Arial y fuentes matemáticas incrustadas.
- Inspección rasterizada de Resumen, Introducción, Metodología, SP0, SP3, SP8, Cargo, Industrial 2, Conclusiones, Referencias y anexos SP4/SP6/SP7/SP8.

El cierre técnico queda completado. La release inmutable y cualquier resolución administrativa AGV/AMR siguen siendo acciones externas necesarias antes del depósito definitivo; no se simulan en el manuscrito.

## Quinto dictamen integral sobre `main(14)`

Por instrucción expresa del autor y por precedencia de `docs/00_TFM_CHARTER.md`, esta revisión conserva **AMR** y elimina AGV de las fuentes y del PDF. La salida se mantiene en `thesis/build/main.pdf`; no se crea `main(15)` ni otra copia numerada.

| Observación | Estado | Resolución y evidencia |
|---|---|---|
| OE5 citado pero no definido | **CERRADA** | OE5 se restaura en Objetivos, se operacionaliza en Metodología y se evalúa en Conclusiones. El Anexo A distingue campañas regenerables, reanálisis y piloto. |
| Release, etiqueta, SHA y archivo inmutable | **ABIERTA; DEPENDENCIA EXTERNA DECLARADA** | El anexo informa URL, SHA base y árbol no consolidado, sin presentar ese SHA como instantánea final. La etiqueta/DOI solo podrá fijarse tras consolidar y congelar la entrega. |
| Regla Cargo mezcla m, kg y N | **CERRADA SIN ALTERAR RESULTADOS** | Distancia, carga útil y fuerza se normalizan por 1 m, 1 kg y 1 N; el orden es ascendente, los empates se resuelven por ID y el cierre exige cardinalidad, masa y fuerza. Una prueba verifica equivalencia numérica exacta con el ranking archivado. |
| Alcance de batería en RQ4 | **CERRADA** | Conclusiones delimitan batería como disponibilidad estática en SP2 y factor conjunto de Industrial 2; no se afirma dinámica de descarga/recarga ni efecto causal aislado. |
| Procedencia y licencia de la escena AWS | **CERRADA** | Industrial 2 y su figura atribuyen AWS RoboMaker Small Warehouse World, versión 1.0.4, licencia MIT-0; la referencia se registró como verificada en el ledger. |
| Encabezado sin alumno y folio `i` ambiguo | **CERRADA Y VERIFICADA VISUALMENTE** | El encabezado incluye nombre y título corto AMR. Los romanos minúsculos usan punto explícito y el cuerpo conserva reinicio arábigo en 1. |
| Tablas 1, 2, 9, 11, 14, 16, 19 y 25 demasiado pequeñas | **CERRADA** | Se fijan a 9 pt, se reajustan columnas y se inspeccionan rasterizadas; no hay cajas `Overfull`. |
| Párrafos telegráficos y estado «pendiente» en SP1 | **CERRADA** | Se integra la síntesis aislada de SP7 y SP1 formula el límite como fuera del alcance experimental, sin presentar trabajo futuro como deuda de la sección. |
| APA, DOI espaciados, capitalización y nombre Greedy/voraz | **CERRADA EN EL PDF ACTUAL** | Bibliografía a bandera izquierda, títulos en estilo oración, rangos con raya, arXiv normalizado y etiquetas visibles unificadas como «Voraz». Los DOI se verificaron visualmente sin espacios artificiales. |
| Metadatos PDF incompletos | **CERRADA** | `pdfinfo` informa título completo AMR, autor, materia y cinco palabras clave. |
| Cuenta administrativa de referencias dentro de 80 páginas | **ABIERTA; REQUIERE CONFIRMACIÓN VIU/TUTOR** | El cuerpo termina en 80 y Referencias comienza en 81. No se altera esa interpretación sin una regla administrativa verificable. |

### Verificación de `main(14)` corregido

- `python -m pytest -q`: 75 pruebas superadas; `tests/test_cargo_e2e.py`: 8 superadas.
- PDF A4 de 117 páginas: cuerpo 1--80, referencias 81--86 y anexos 87--105 (19 páginas).
- Compilación estable en `thesis/build/main.pdf`, sin errores LaTeX, referencias/citas indefinidas ni cajas `Overfull`.
- Cero apariciones de AGV en las fuentes de tesis y en el texto extraído del PDF; el único PDF de `thesis/build/` es `main.pdf`.
- Inspección rasterizada de encabezado/folio, tablas críticas, Cargo, AWS, referencias y Anexo A.
