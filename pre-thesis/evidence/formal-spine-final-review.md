# Revisión independiente definitiva de la columna formal

**Fecha:** 2026-09-08  
**Objeto:** resultados formales que sostienen la memoria VIU activa  
**Decisión:** **PASS**  
**Bloqueantes P1/P2:** **0**

Este informe cierra los hallazgos registrados en las revisiones anteriores sin borrar su historial. La inspección volvió a contrastar enunciado, supuestos, dominio, unidades, prueba o contraejemplo, dependencia documental y presencia efectiva en el grafo que compila `pre-thesis/main.tex`. Los hashes de las fuentes y del PDF quedan fijados por el informe de congelación y por `source-snapshot.json`; la matriz fila a fila está en `formal-spine-final-verdicts.csv`.

## Veredicto por resultado

| Bloque | Resultado | Estado |
|---|---|---:|
| SP1 | Potencial exacto, cuotas y mejora finita | PASS |
| SP1 | Integrabilidad de capacidad heterogénea | PASS |
| SP2 | Equivalencia carga--unicíclo--ruedas | PASS |
| SP2 | Cota de ruedas en giro puro | PASS |
| SP2 | Monotonicidades cinemática y mecánica opuestas | PASS |
| SP2 | Insuficiencia de capacidad escalar | PASS |
| SP2 | Estabilidad local con contactos fijos y realización exacta del wrench | PASS |
| SP2 | Disipación perturbada normalizada con $\ell_0$ y $S_q$ | PASS |
| E3 | Unicidad del reparto regularizado | PASS |
| E3 | Residual puro frente a certificado regularizado | PASS |
| E3 | Potencial continuo y acción inactiva | PASS |
| SP6 | Potencial, maximalidad y cota en cambios aceptados | PASS |
| SP6 | Nash factibles mínimos con costes positivos | PASS |
| SP6 | $\mathrm{PoS}=1$ y ausencia de cota uniforme para PoA | PASS |
| SP6 | Cota temporal de recuperación | PASS |
| SP3/E7 | Potencial de rutas y terminación | PASS |
| SP3/E7 | Ausencia condicional de conflictos e inanición | PASS |
| Transversal | Imposibilidad informacional bajo partición | PASS |

## Cierre de los dos fallos intermedios

La cota temporal de SP6 define ahora $\bar\tau_a$ sobre cada ventana agregada de decisión, desde la detección o el último cambio aceptado hasta el siguiente cambio aceptado o la certificación terminal. Por tanto, $m\leq 2^{n_R}-1$ cambios aceptados inducen como máximo $m+1\leq 2^{n_R}$ ventanas; las activaciones que no cambian el perfil están incluidas dentro de ellas. La prueba compacta activa y el helper ejecutable usan el mismo conteo.

Los resultados SP2 que antes solo tenían enlace externo se incorporaron de forma autocontenida mediante `shared/formal-results/sp2-canonical-bridge.tex`, incluido por `sections/thesis-appendices.tex`. El puente conserva las restricciones de pivote no estacionario, acoplamiento ideal/contactos bilaterales fijos, límites de rueda, distinción entre residual puro y regularizado y normalización fuerza--momento.

## Alcance honesto

El veredicto valida la coherencia interna de los resultados bajo sus hipótesis; no convierte simulaciones en pruebas ni extiende garantías a hardware. La estabilidad Cargo sigue siendo local, con contactos bilaterales fijos y realización exacta del wrench. La terminación de SP1, SP6 y SP3/E7 cuenta cambios aceptados; solo SP6 añade una cota física bajo la hipótesis explícita de ventanas agregadas acotadas. La imposibilidad bajo partición aplica a algoritmos deterministas basados en el historial local dentro de la clase indistinguible declarada.

