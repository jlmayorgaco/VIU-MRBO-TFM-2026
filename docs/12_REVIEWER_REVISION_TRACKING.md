# Trazabilidad del dictamen externo de `main(11).pdf`

Fecha de revisión: 2026-07-17. Este registro aplica la precedencia de `AGENTS.md`: el dictamen orienta la revisión científica, pero no sustituye el título administrativo ni la fidelidad comprobada de la plantilla VIU.

## Prioridad P0

| # | Observación | Estado | Resolución y evidencia |
|---:|---|---|---|
| 1 | Validación cuantitativa CoppeliaSim | **PARCIAL: PILOTO CINEMÁTICO CERRADO; GATE DINÁMICO ABIERTO** | Industrial 2 dispone de escena exportada, auditoría geométrica, replay cinemático validado y una campaña Python pareada de 32 ejecuciones. La memoria incorpora sus resultados negativos como C19. No valida Pioneer 3-DX, rueda--suelo, agarre cooperativo ni contacto 3D; `reviewer_dynamic_gate` continúa sin acreditar una planta dinámica independiente. |
| 2 | Contradicción AGV/AMR y título | **RESUELTA POR PRECEDENCIA** | `docs/00_TFM_CHARTER.md` y `thesis/metadata.tex` fijan el título administrativo con AMR. No se modifica sin aprobación expresa. AGV y AMR se definen en nomenclatura; el cuerpo usa el alcance técnico demostrado. |
| 3 | Cadena velocidad--aceleración--wrench de SP5 | **CERRADA** | `sp5.tex` define aceleración traslacional por diferencia finita, canal angular, wrench filtrado, reparto y margen aplicado. `payload_transport.py` implementa la transformación y `tests/test_sp5_payload_transport.py` comprueba dimensiones y saturación opcional. |
| 4 | Capacidad física frente a disponibilidad SP2 | **CERRADA** | SP2 separa carga útil `c_i^pay`, disponibilidad `a_ik` y servicio normalizado `e_ik`; el umbral histórico pasa a `d_k^srv`. SP3 conserva el primer certificado mecánico. Código, configuración, pruebas, notación y matriz de evidencia están sincronizados. |
| 5 | Restaurar generadores SP2/SP3 | **CERRADA DEFENSIVAMENTE** | Los generadores históricos completos no están en el árbol actual y no se inventan. SP2 y SP3 se clasifican como reanálisis reproducibles de observaciones archivadas; las secciones experimentales y el Anexo A declaran que no pueden reconstruirse íntegramente desde cero. |
| 6 | Reconciliar hipótesis y ejecución extremo a extremo | **CERRADA EN EL ALCANCE ACTUAL** | La campaña Cargo integra SP2--SP6 en una planta planar y se presenta como evidencia de composición, no como garantía híbrida ni validación industrial. La tabla transversal declara cada lectura global, cierre, certificado y planta. La transferencia dinámica independiente queda como limitación. |
| 7 | Preliminares en romanos | **NO APLICADA; contradice la fuente VIU auditada** | `docs/06_VIU_TEMPLATE_FIDELITY.md` registra que la plantilla DOCX oficial usa numeración arábiga continua, portada sin número visible y Resumen en la página 2. Se conserva ese contrato; no se aplica la recomendación romana sin una plantilla oficial posterior. |
| 8 | Legibilidad de tablas metodológicas | **CERRADA Y VERIFICADA VISUALMENTE** | Las tablas SP0--SP7 dejaron tamaños manuales de 5,7--7 pt y usan `\scriptsize`. El PDF recompilado se inspeccionó en las páginas críticas; no hay desbordamientos y la tabla transversal es legible a página completa. |
| 9 | Nomenclatura incompleta | **CERRADA PARA LOS SÍMBOLOS CRÍTICOS** | Se añadieron `Q_W`, `G_C`, servicio SP2, cadena SP5, `D_6`, `lambda_6`, `delta_min`, rutas/conflictos SP7 y recursos/grafo SP8 a `frontmatter/04-nomenclature.tex`; `docs/05_NOTATION.md` conserva el inventario canónico completo. |
| 10 | Visibilidad de CoppeliaSim | **CERRADA EN EL ALCANCE CINEMÁTICO** | Metodología, resultados y conclusiones incorporan Industrial 2 como auditoría geométrica y piloto cinemático. Se reporta el bloqueo de los tres escenarios congestionados y se mantiene abierta la validación dinámica tridimensional/hardware. El resumen y el abstract omiten este piloto secundario para respetar el límite de 300 palabras. |

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
| Extensión VIU | **ABIERTA: RIESGO ADMINISTRATIVO** | La versión recompilada tiene 134 páginas; el cuerpo ocupa aproximadamente 98 páginas (13--110), por encima de 50--80. Los anexos ocupan 18 páginas (117--134), dentro del máximo de 20. Reducir el cuerpo exige una edición estructural separada para no eliminar evidencia. |
| Validación dinámica independiente | **ABIERTA** | Industrial 2 sigue siendo un piloto geométrico/cinemático. No hay evidencia de contacto tridimensional, fricción, actuadores, sensores reales ni hardware. |

## Verificación ejecutada

- `python -m pytest -q`: 74 pruebas superadas.
- Campañas confirmatorias regeneradas: Cargo, 360 mundos y 2160 ejecuciones; SP8, 900 mundos, 4500 registros y 4050 ejecuciones; SP3, tabla, macros y figura vectorial actualizadas.
- Compilación limpia: PDF A4 de 134 páginas generado sin errores LaTeX, referencias/citas indefinidas ni cajas `Overfull`.
- Resumen/abstract: 281/278 palabras, dentro del intervalo VIU de 200--300.
- Revisión visual rasterizada: preliminares, nomenclatura, figura SP3, SP8, Cargo, AWS, conclusiones y anexos; sin cortes ni desbordamientos críticos.
