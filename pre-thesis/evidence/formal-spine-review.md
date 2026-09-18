# Auditoría matemática independiente de la columna vertebral formal

**Fecha de corte:** 2026-09-08  
**Fuente de inventario:** `pre-thesis/evidence/formal-results-audit.csv`  
**Alcance:** revisión semántica de la columna vertebral SP1--SP3 y de sus resultados auxiliares; triage exclusivamente estructural del resto de `paper/`.

## Dictamen ejecutivo

No se identificó un P0: las identidades de potencial de SP1 y SP3, la prueba nominal de Cargo y las inclusiones principales de capacidad resisten la revisión. Sí hay cinco P1 que deben cerrarse antes de promover el conjunto como bloque definitivo:

1. **P1 — La imposibilidad por partición es falsa con los cuantificadores actuales.** `thesis/sections/mainmatter/06-results-and-analysis/sp8.tex:108` habla de una familia arbitraria con interacciones remotas. Una familia singleton con óptimo conocido admite una regla constante y contradice el enunciado. La prueba de `thesis/sections/appendices/09-sp8-proofs.tex:18` usa, sin declararlo, dos instancias localmente indistinguibles cuyos óptimos requieren acciones locales incompatibles.
2. **P1 — Cuatro resultados canónicos de SP2 no están en el inventario formal.** `C-SP2-N1-KIN-FORMAL`, `C-SP2-CARGO-NOMINAL-STABILITY`, `C-SP2-CROSS-MONO-FORMAL` y `C-SP2-N2-RELAX-FORMAL` viven en `Subdocuments/SP2/sp2.tex`, fuera de los corpus `paper/` y `thesis/`, y usan los entornos personalizados `sp2prop`/`sp2lema`. El CSV de 164 filas no puede ser la puerta de promoción mientras no los incluya o enlace explícitamente.
3. **P1 — La rama perturbada de la proposición histórica de pose mezcla unidades sin una escala declarada.** En `thesis/sections/appendices/06-sp4-proofs.tex:65`, `lambda_min(D_k+K_D)` y `||r_k^W||_2` se calculan en coordenadas que mezclan traslación y rotación, y un wrench que mezcla N y N m. La desigualdad algebraica es válida después de fijar una normalización métrica; sin ella no es una cota física invariante. La rama exacta `r_k^W=0` no queda afectada.
4. **P1 — Los enunciados de terminación confunden finitud de eventos con tiempo físico o presuponen maximalidad.** SP1 (`sp1.tex:268`), SP3 (`sp7.tex:107`) y SP6 (`sp6.tex:120`) prueban que no hay una sucesión infinita de mejoras aceptadas en un espacio finito. Alcanzar un Nash exige además que la trayectoria sea maximal y que el planificador no se detenga mientras exista una mejora. En SP1, justicia sin una cota de interactivación no implica una cota de tiempo de pared. En SP6, `bar_tau_a` acota intervalos *entre* mejoras, pero no el lapso detección--primera mejora ni la certificación terminal.
5. **P1 — La caracterización Nash de recuperación necesita costes estrictamente positivos en el propio teorema.** La prueba usa `kappa_i^6>0` al expulsar un miembro redundante. El supuesto aparece en la introducción del anexo y en el ledger, pero no en `thesis/.../sp6.tex:138`. Con capacidades `[1,0.2]`, demanda `1`, costes `[1,0]` y perfil `[1,1]`, el perfil es Nash bajo mejoras estrictas aunque no sea mínimo por inclusión.

Hay además dos riesgos de trazabilidad: el inventario detecta dos apariciones de `cor:sp1-strategic-regulation`, pero la primera (`sp1.tex:245`) está dentro de `\iffalse` y no forma parte del documento activo; y el recuento actual de `paper/` es 143, no las 104 unidades históricas del plan. Ninguno invalida una prueba, pero ambos impiden usar el conteo bruto como evidencia de cobertura.

## Veredictos semánticos

| Resultado | Veredicto | Razón y frontera segura |
|---|---|---|
| SP1: potencial exacto, cuotas realizables, Nash y óptimo de coste | **SUPPORTED** | La identidad WLU es exacta; todo perfil inexacto admite una desviación; todo perfil exacto es Nash para `lambda>kappa_max`; el espacio tiene `(K+1)^N` perfiles. Prueba: `03-sp1-proofs.tex:20-35`. Solo cubre el juego lógico finito con cargas obligatorias, costes adimensionales y ocupación coherente. |
| SP1: corolario activo de regulación | **LIMITED** | La prueba da un número finito de revisiones aceptadas bajo activación persistente. No da tiempo físico ni una cota bajo justicia sin demora acotada. Sustituir “en tiempo finito” por “tras un número finito de mejoras aceptadas” y declarar trayectoria maximal/política de mejor respuesta. |
| SP1: copia de `cor:sp1-strategic-regulation` en `sp1.tex:245` | **REJECTED** | Está desactivada por `\iffalse`; no es un resultado del documento compilado. Debe conservarse fuera de cualquier migración automática y no contarse dos veces. |
| Capacidad heterogénea: integrabilidad marginal | **SUPPORTED** | La regla de la cadena produce `f_marg`; las derivadas cruzadas de `f_plain` difieren si `e_ik != e_jk`, mientras las marginales coinciden. La integral es C1 en saturación. No prueba convergencia de Smith, cierre entero ni estimación distribuida. |
| Cargo nominal: estabilidad local con contactos fijos y wrench exacto | **SUPPORTED** | La sustitución produce `M_L e_ddot + K_D e_dot + K_P e=0`; el almacenamiento cuadrático y LaSalle dan convergencia local dentro de la carta angular. Requiere `M_L`, `K_P`, `K_D` constantes/SPD, referencia C2, modelo exacto, sin perturbación, saturación ni cambio de contacto. No se transfiere a caging, híbridos, hardware o asignación aproximada. |
| Proposición histórica SP4 con residual de wrench | **LIMITED** | La rama exacta es correcta. La cota con residual necesita declarar una métrica/escala que homogeneice m, rad, N y N m; sin ella no debe publicarse como cota física cuantitativa. |
| SP2: equivalencia cinemática Pioneer--cuerpo rígido | **SUPPORTED** | La derivación directa es válida para pivotes no estacionarios, acoplamiento ideal con yaw pasivo, alineación inicial, rama continua y seguimiento exacto. Excluye límites de aceleración/par, fricción y estabilidad de contacto. La rama estacionaria es singular y queda fuera. |
| SP2: no monotonía con tamaño de coalición | **SUPPORTED** | Retirar un robot elimina una intersección cinemática y, si la reacción nula es admisible, elimina un sumando físico. Los dos casos constructivos muestran que la intersección conjunta puede crecer o decrecer. No se traslada al oráculo secuencial `W_hat_C(n*)` ni al transitorio de desacoplamiento. |
| SP2: capacidad escalar insuficiente | **SUPPORTED** | `sum_i tbar_i >= ||F_d||` es necesaria por desigualdad triangular; contactos coincidentes con el centro no generan `tau_d != 0`, aunque la capacidad escalar sea arbitraria. La aceptación por caja bilateral tampoco certifica soporte o fricción. El dato 52/720 sigue siendo empírico y no prueba una ventaja entre las dos relajaciones. |
| SP3: identidad de potencial de rutas y cota de cambios | **SUPPORTED** | `C(m+1,2)-C(m,2)=m` iguala exactamente la variación del pago y del potencial. No hay repetición bajo mejora estricta y hay como máximo `prod_i |R_i|-1` cambios aceptados. |
| SP3: llegada de “toda trayectoria” a Nash | **LIMITED** | Es correcta para una trayectoria maximal que continúa mientras existe una mejora; una sucesión truncada puede terminar en un perfil no Nash. Añadir esa convención o un planificador justo/exhaustivo. |
| Imposibilidad bajo componentes desconectadas | **REJECTED** | El argumento de indistinguibilidad es válido, pero solo para clases que contienen al menos un par de instancias indistinguibles localmente y con conjuntos de acciones óptimas locales disjuntos. Esa riqueza no se sigue del enunciado actual. |
| Recuperación SP6: identidad de potencial, existencia y no repetición | **SUPPORTED** | La utilidad WLU reproduce la diferencia de `Phi_6`; un máximo del potencial es Nash y una mejora estricta no repite perfiles. Llegar a Nash presupone trayectoria maximal. |
| Recuperación SP6: Nash = reparación mínima por inclusión | **LIMITED** | La demostración es correcta con recursos aditivos no negativos, reserva completa factible, pesos y costes estrictamente positivos y `lambda_6>kappa_max/delta_min`. El teorema debe incorporar explícitamente `kappa_i^6>0`; el contraejemplo de coste cero muestra que no es decorativo. |
| Recuperación SP6: PoA no acotado | **SUPPORTED** | La instancia de capacidades `(1,1/2,1/2)` y costes `(M,1,1)` tiene los Nash `(1,0,0)` y `(0,1,1)` para `lambda=5M/2`; el cociente `M/2` diverge. |
| Recuperación SP6: cota temporal | **LIMITED** | La suma es válida solo si `bar_tau_a` acota detección--primera mejora, cada intervalo posterior y la decisión de parada; además presupone movimiento paralelo por segmentos libres, velocidad inferior garantizada y asentamiento acotado. Justicia por sí sola no basta. |

El detalle máquina-legible, incluidas rutas, pruebas y condiciones de promoción, está en `formal-spine-verdicts.csv`.

## Contraenunciado corregido para la partición

Una formulación demostrada por el argumento existente es:

> Sea una clase de juegos que contiene dos instancias con el mismo historial intracomponente para una componente conectada, pero cuyos conjuntos de acciones locales compatibles con un óptimo global son disjuntos. Ningún algoritmo determinista basado exclusivamente en ese historial puede devolver un óptimo global en ambas instancias. Si las instancias difieren entre interacción remota nula y no nula, tampoco puede detectar correctamente la interacción en ambas.

Esta versión no prohíbe resolver familias restringidas mediante mapa previo, prioridades o una regla constante; identifica exactamente la condición de indistinguibilidad que usa la prueba.

## Comprobaciones ejecutadas

Se ejecutó sin caché ni escritura de bytecode:

```text
python -m pytest -q -p no:cacheprovider \
  tests/test_sp1_theory.py tests/test_sp2_canonical.py \
  tests/test_sp2_submit_ready.py tests/test_sp6_recovery.py \
  tests/test_sp7_traffic.py tests/test_sp8_network.py
59 passed in 28.54s
```

Una auditoría adversarial adicional, con semilla `20260908`, verificó:

- 132 instancias pequeñas aleatorias de SP1 mediante enumeración exhaustiva de perfiles;
- 180 instancias positivas de SP6, comparando todos los Nash con todos los conjuntos mínimos por inclusión;
- el contraejemplo SP6 de miembro redundante con coste cero;
- 120 juegos aleatorios de rutas SP3, identidad exacta, ausencia de perfiles repetidos y llegada del ejecutor a Nash;
- 1.000 identidades numéricas de la derivada de Lyapunov nominal de Cargo.

Estas pruebas validan implementaciones e identidades finitas; no sustituyen las demostraciones ni validan contacto físico, MuJoCo o hardware.

## Correspondencia código--resultado

- SP1: `src/viu_mrob_tfm/sp1/theory.py`; la prueba automatizada cubre WLU y enumeración pequeña, no la dinámica Smith ni QR bajo escasez.
- SP2: `src/viu_mrob_tfm/sp2_canonical/kinematics.py`, `mechanics.py`, `support.py` y `dynamics.py`; los tests cubren identidades cinemáticas, guardas y contraejemplos, pero no constituyen una prueba de estabilidad de la planta simulada.
- SP3: `src/viu_mrob_tfm/sp7/theory.py`; el ejecutor realiza barridos exhaustivos hasta que no hay una mejora, condición más fuerte y más clara que el enunciado editorial actual.
- Recuperación: `src/viu_mrob_tfm/sp6/theory.py`; el código acepta costes nulos, por lo que la función general no satisface automáticamente la caracterización mínima del teorema.
- Partición: `tests/test_sp8_network.py` exhibe un conflicto remoto oculto; no comprueba el par de mundos indistinguibles ni los cuantificadores del teorema.

## Triage estructural exhaustivo de `paper/`

El inventario contiene 143 resultados candidatos: 49 teoremas, 72 proposiciones, 10 lemas y 12 corolarios. El escaneo de proximidad encuentra un entorno `proof` próximo en 103 y no lo encuentra en 40. Un marcador léxico de condición/supuesto aparece en 123 enunciados y falta en 20. La matriz es:

| Prueba próxima | Marcador de condición | Cantidad |
|---:|---:|---:|
| sí | sí | 91 |
| sí | no | 12 |
| no | sí | 32 |
| no | no | 8 |

No hay etiquetas formales repetidas entre esas 143 filas. Sí existen dos colisiones fuera de ese subconjunto que deben resolverse antes de compilar la monografía: `obs:biblioteca-fisica` aparece en `paper/sec_auditoria.tex:264` y `paper/sec_fundamentos.tex:127`; `tembine2021meanfield` aparece dos veces como `bibitem` activo en `paper/megajuego.tex:1489` y `paper/megajuego.tex:1583`.

Cada fila no revisada de `paper/` recibe **CONJECTURE** y `STRUCTURAL_TRIAGE_ONLY` en el CSV. Este valor es una barrera conservadora de promoción, no un dictamen de falsedad: “prueba próxima” solo significa proximidad textual; “marcador” solo detecta palabras como *si*, *bajo*, *supóngase* o *sea*. Ninguno verifica alcance, dominio, unidades, dependencias, circularidad o corrección algebraica. Las 40 filas sin prueba próxima tienen prioridad `HIGH`; las 12 con prueba pero sin marcador, `MEDIUM`; las restantes, `LOW`. Esta clasificación permite auditar las 143 sin fingir una revisión semántica.

## Promoción segura

Puede entrar en la memoria, con los supuestos visibles junto al enunciado:

- SP1: potencial exacto, caracterización de cuotas y óptimo de coste;
- integrabilidad de la señal marginal heterogénea;
- Cargo nominal local con contactos bilaterales fijos y wrench exacto;
- equivalencia cinemática, monotonías opuestas y contraejemplo de capacidad escalar;
- identidad de potencial y cota de cambios aceptados de SP3;
- identidad de potencial de recuperación y PoA no acotado.

Puede promoverse después de una corrección local: corolario temporal SP1, llegada a Nash SP3, caracterización mínima SP6 y cota temporal SP6. No debe promoverse el teorema de partición con su cuantificación actual, la copia inactiva del corolario SP1 ni ninguno de los 143 resultados de `paper/` solo por superar el triage sintáctico.

## Integración mínima en `thesis-results.tex`

El scaffold activo incluye `sp2.tex`, `sp3.tex`, `sp4.tex`, `sp6.tex` y `sp7.tex`, pero no `sp1.tex` ni `sp8.tex`. Por ello, hoy quedan fuera precisamente el teorema de cuotas de SP1 y el límite por partición. **Sí es seguro incorporar ambos como texto condensado completo en `pre-thesis/sections/thesis-results.tex`**, siempre que cada bloque contenga definición, enunciado, prueba y frontera, y use etiquetas nuevas para no depender de unidades históricas omitidas.

La formulación mínima suficiente de SP1 es:

> Sean `a_i in {0,...,K}`, `q_k(a)=|{i:a_i=k}|`, cuotas obligatorias positivas `n_k` con `sum_k n_k <= N`, y costes fijos adimensionales `kappa_ik in [0,kappa_max]`. Defínanse `D=sum_k[n_k-q_k]_+`, `O=sum_k[q_k-n_k]_+`, `C=sum_{i:a_i!=0}kappa_{i,a_i}`, `Phi=-(C+lambda D+lambda O)` y `U_i(a)=Phi(a)-Phi(0,a_-i)`, con `lambda>kappa_max`. Entonces `Phi` es un potencial exacto; los Nash puros son exactamente los perfiles `q_k=n_k`; todo camino maximal de mejoras estrictas termina en uno de ellos tras a lo sumo `(K+1)^N-1` cambios aceptados; y los máximos globales de `Phi` son las asignaciones exactas de coste mínimo.

La prueba condensada debe conservar los tres casos: robot libre que cubre déficit; traslado exceso--déficit cuando todos están activos; salida ante exceso sin déficit. La identidad WLU prueba exactitud, la cota de costes hace estrictas esas desviaciones y la finitud excluye repetición. El texto no debe convertir el número de cambios en tiempo físico ni transferir el resultado a Smith, QR, escasez, comunicación o mecánica.

La formulación mínima suficiente de SP8 es:

> Sea una clase de juegos que contiene dos instancias `I_0,I_1` con el mismo historial observable para una componente conectada `H`, pero con proyecciones disjuntas sobre `H` de sus conjuntos de óptimos globales. Ningún algoritmo determinista cuyo estado y salida en `H` dependan exclusivamente de ese historial puede devolver un óptimo global en ambas instancias. Si, además, el predicado “existe interacción remota” difiere entre `I_0` e `I_1`, tampoco puede detectarlo correctamente en ambas.

La prueba completa cabe en un párrafo: indistinguibilidad obliga al algoritmo a producir la misma salida local en las dos instancias; la disyunción de las proyecciones óptimas implica que esa salida falla en al menos una; el mismo argumento binario resuelve la detección. Debe añadirse de inmediato la frontera: una partición no impide optimalidad en familias singleton, con interacción remota nula/conocida o con un óptimo local común. Esta versión sí coincide exactamente con la prueba existente y puede formar parte de la síntesis SP3 sin recuperar todo `sp8.tex`.

## Límites de esta auditoría

La revisión no modificó fuentes, código, tests ni el CSV generado. No auditó semánticamente los 143 resultados de `paper/`, no ejecutó CoppeliaSim/MuJoCo y no infiere estabilidad física desde tests unitarios. Los números y veredictos corresponden al árbol observado el 8 de septiembre de 2026; si se regenera el inventario, el CSV de veredictos debe compararse por `source_result_id`, ruta, línea y hash de fuente.
