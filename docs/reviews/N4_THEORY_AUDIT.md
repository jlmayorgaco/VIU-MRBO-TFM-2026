# Auditoría teórica de SP1.N4

Esta tabla separa resultados del modelo, propiedades de implementación y datos.
`Probado` significa que el argumento aparece con sus hipótesis; no significa
que la propiedad se mantenga fuera de ese modelo.

| Claim | Status | Assumptions | Evidence | Location | Risk |
|---|---|---|---|---|---|
| R1: la diferencia unilateral depende solo de las cargas afectadas y del robot que cambia | derived | Perfil atómico; demandas y capacidades fijas; misma definición de `D4` y `J4` | Derivación algebraica y enumeración unilateral | Ecs. 8--9; `tests/test_sp1_n4.py` | Confundir suficiencia para evaluar con disponibilidad gratuita de la información |
| La extensión de R1 a pares/triples usa participantes y cargas modificadas | derived / tested | Propuesta atómica, fase y versiones comunes | Tests aleatorios de deltas | `geo_qpg.py`; `tests/test_sp1_n4.py` | No es una prueba de coste de comunicación mínimo |
| R2: la utilidad wonderful-life induce un potencial exacto unilateral | proved | Una fase fija; desviación unilateral; referencia `(0,a_-i)` bien definida | Cancelación algebraica | Ec. 10 y Proposición 4 | Extenderla sin prueba a utilidad coalicional |
| BR, 2BR y C3 forman una jerarquía `h=1,2,3` | derived / implemented | Vecindades anidadas y generadores que agotan su orden | Definición de `N_h` y tests | Ec. 11; Tabla 6 | Leerlos como tres objetivos distintos |
| R3: existe un bloqueo unilateral con escape bilateral bajo las desigualdades dadas | proved conditionally | Dos robots/cargas; factibilidad y desigualdad estricta de distancia | Sustitución en `D4,J4`; caso de regresión | Ecs. 13--14; Lema 6 | Interpretarlo como caracterización completa de `h*=2` |
| Existen testigos reproducibles de orden 2 y 3 | validated in tests | Instancias deterministas de regresión | Tests unitarios | `tests/test_sp1_n4.py` | Inferir de dos testigos la distribución de `h*` |
| R4: cada etapa de refinamiento termina y entrega un mínimo `h`-local | proved conditionally | Espacio finito; mejora estricta; no-starvation; vecindad agotada | Argumento de descenso finito y tests de invariantes | Algoritmo 3; Proposición 5 | Confundir terminación con optimalidad global o Nash fuerte |
| Geo-ASR es revisión atómica tipo Smith | derived / implemented | Acciones discretas; probabilidad proporcional a ganancia positiva | Ecuación y ejecución E4 | Ec. 12; E4 | Llamarla dinámica poblacional Smith |
| Geo-LLL usa respuesta Gibbs finita y puede aceptar empeoramientos | implemented / empirical | Calendario finito de beta y conjunto discreto de acciones | Configuración y E4 | Ec. 12; E4 | Afirmar convergencia asintótica con una ejecución finita |
| La relajación F-II usa un potencial suave explícito y un mismo campo por fase | proposed formulation | `x_i` en simplex; softplus; fases Q/G separadas | Definición matemática | Ecs. 15--16 | Trasladar unidades o garantías del modelo atómico |
| Replicator, Smith, BNN y Logit están escritos como dinámicas distintas sobre el mismo campo | derived formulation | Campo regular; simplex; integración todavía no auditada aquí | Ecuaciones estándar y bibliografía verificada | Ec. 16 | Afirmar estacionariedad de Nash o convergencia sin hipótesis |
| E71 ordena dinámicas continuas, no coaliciones físicas | empirical context | Criterio continuo histórico; sin cierre común | Artefacto E71 | p. 31; `key_metrics.json` | Mezclarlo con E4 en un ranking |
| Convergencia de `x` no implica salida atómica factible | derived boundary | `R` no definido; robots indivisibles | Diferencia de dominios y evidencia de atomicidad N2 | Figura 23; `docs/04_CLAIMS_EVIDENCE.md` | Presentar `x_ik` como fracción física de robot |
| F-III formula restricciones compartidas y precios sombra | proposed | Coste espacial diferenciable; restricciones `g_k<=0` | Lagrangiano y dinámica candidata | Ecs. 17--19 | Signo/unidades incorrectos si cambia el coste individual |
| Primal--dual es mecanismo; vGNE es concepto de solución | derived taxonomy | Multiplicador común para la caracterización variacional | KKT/VI escrita | Ec. 20; Figura 24 | Llamar vGNE al algoritmo o primal--dual al equilibrio |
| La dinámica distribuida F-III converge | proposed, not established | Requeriría convexidad, monotonía, regularidad, conectividad, ganancias y discretización | Ninguna prueba aplicada | p. 32 | Claim no autorizado |
| F-IV convierte la instantánea en una decisión recurrente | future | Estado y kernel de transición aún no identificados | Modelo mínimo, sin campaña | Ec. 21; Figura 25 | Usar una referencia GNE estocástica como política de Markov ya resuelta |
| R5: propuestas independientes tienen deltas aditivos | proved conditionally | Misma fase/versiones; robots y registros modificados disjuntos | Descomposición de sumas y tests de composición | Proposición 6; `tests/test_sp1_n4.py` | Suponer que un conjunto maximal es el mejor lote |
| DMIS devuelve un conjunto independiente maximal | implemented / tested | Grafo de conflictos y prioridades deterministas/pareadas | Tests MIS y campaña E4 | Figura 26; `geo_qpg.py` | Confundir maximal con maximum |
| R6: el commit versionado escribe todos los registros o ninguno | proved in nominal model | Entrega fiable; versiones comparables; bloqueos; proponente activo | Invariantes de transacción y tests | Figura 27; `tests/test_sp1_n4.py` | Extrapolar a crash, pérdida, partición o bizantino |
| DMIS+TX igualó calidad/factibilidad de CF en E4 | empirical | Red nominal; mismos mundos/candidatos; simulador en un proceso | Contraste pareado sobre 1.200 mundos | Figura 29; claim `C-SP1-N4-DMIS-TX` | Llamar a la ejecución tolerante a fallos o medir latencia física con CPU |
| DPOP coincidió con MILP en E5 | empirical / exact on tested worlds | `N=6,8`; factor global de cuota; tolerancia numérica | 400/400 mundos, error máximo registrado | Figura 30; claim `C-SP1-N4-DPOP` | Presentarlo como solución escalable |
| E6 no muestra saturación | empirical negative | `16<=N<=64`; un equipo; Python; 60 mundos | Pendiente e IC log--log descriptivos | Figura 31; claim `C-SP1-N4-SCALING` | Convertir la pendiente en Big-O o extrapolar a `N` ilimitado |
| N4 entrega la entrada lógica de SP2 | derived interface | Asignación entera y versiones consistentes | Contrato SP1--SP2 | Cierre de p. 38 | Afirmar docking, wrench, estabilidad, seguridad o transporte |
