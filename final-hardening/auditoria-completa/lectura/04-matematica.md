# Auditoría matemática teorema a teorema — FASE 8 y FASE 9

Criterio: `pre-thesis/guidelines/05-checklist-por-fases.md`, FASE 8 (matemática) y
FASE 9 (juego / arquitectura de integración).

Universo auditado: los **29 entornos formales** del cierre activo de
`pre-thesis/main-v2.tex`, tal como los censa `final-hardening/census.json`
(89 ficheros compilados, 0 etiquetas duplicadas, 0 ecuaciones sin citar).
Se auditan también dos objetos que **no** son entornos formales pero funcionan
como resultados en el discurso: el certificado racional de *caging* y el
corolario sin enunciado del anexo Bézier.

No se ha editado ningún fichero de la memoria.

---

## 1. Resumen ejecutivo

| Medida | Valor |
|---|---:|
| Entornos formales en el documento activo | 29 |
| Resultados matemáticamente **distintos** | 18 |
| Pares duplicados cuerpo↔anexo (mismo resultado, dos números) | 10 |
| Resultados con demostración completa y correcta *tal como se escribe* | 12 |
| Resultados cuya redacción afirma más de lo que demuestra | **8** |
| Errores numéricos verificados | **1** (solución racional del QP de *caging*) |
| Resultados activos sin fila en `formal-spine-final-verdicts.csv` | 11 (los cuatro del juego de integración, entre ellos) |
| Resultados que no se usan después (huérfanos, FASE 8 último ítem) | 5 |

Las nueve categorías del criterio se abrevian: **EX** existencia de equilibrio,
**CAR** caracterización de equilibrio, **CONV** convergencia algorítmica,
**FIP** mejora finita, **OPT** optimalidad, **EST** estabilidad, **SEG**
seguridad, **VIV** vivacidad, **CPX** complejidad.

Ninguna de las nueve se sustituye por otra dentro de un mismo enunciado. Las
sustituciones que sí aparecen son de **enunciado a texto circundante**: el
teorema dice una cosa y el párrafo, el `\estadoaporte` o la conclusión dicen
otra. Ése es el patrón dominante de esta auditoría y lo recogen las fichas
F-01 a F-12.

---

## 2. Tabla maestra

Orden: el del documento. «Prueba» da el anexo o el fichero donde está la
demostración. «Conclusión activa» responde si alguna afirmación de
`07-conclusions.tex`, `conclusions-megajuego-addendum.tex` o la tabla de
cumplimiento de `thesis-results-v2.tex` descansa sobre el resultado.

| # | ID / etiqueta | Tipo | Enunciado en una línea | Hipótesis tal como se escriben | Dominio de validez | Prueba | Depende de | Qué establece | ¿Afirma más de lo que prueba? | Estado | ¿Conclusión activa? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `prop:pre-cross-partition-limit` | proposición | Con dos instancias indistinguibles en una componente $H$ y óptimos globales de proyección disjunta, ningún algoritmo determinista de historial local es óptimo en ambas | par $I_0,I_1$ indistinguible en $H$; proyecciones disjuntas de los óptimos; algoritmo determinista cuyo estado y salida en $H$ dependen solo de ese historial | lógico, sin unidades | en línea, `thesis-results-v2.tex:63` | argumento de indistinguibilidad, `fischerLynchPaterson1985Impossibility` | OPT (imposibilidad) | **Sí**, en el uso: la conclusión la llama «la razón formal» de toda ausencia de optimalidad global | LIMITED por uso | Sí — OE6 (F-04) |
| 2 | `thm:pre-sp1-exact-quota` | teorema | $\Phi_1$ es potencial exacto, los Nash puros son las cuotas exactas y toda ejecución justa maximal llega a una en $\le(K+1)^N-1$ cambios | $\sum_k n_k\le N$; $\lambda>\kappa_{\max}$; activación asíncrona justa; camino maximal (en `\estadoaporte`) | acciones finitas, costes adimensionales | `app:sp1-e1-full-proof` | eq. `eq:pre-sp1-quota-game` | CAR + FIP + OPT (sobre el conjunto exacto) | No — aclara que la cota cuenta cambios, no segundos ni rondas | **PASS** | Sí — H1a, RQ1 |
| 3 | `prop:sp2-marginal-alignment` | proposición | La puntuación marginal corregida por $e_{ik}/d_k^{\mathrm{srv}}$ es el gradiente exacto de un potencial; la plana no lo es si $e_{ik}\ne e_{jk}$ | $S_k(\rho)<d_k^{\mathrm{srv}}$; $E$, $d_k^{\mathrm{srv}}$ y pesos fijos; preferencias continuas | relajación continua, antes del cierre entero | `app:sp2-marginal-proof` (`04-sp2-proofs.tex`) | `eq:sp2-potential`, definida solo en el anexo | CAR (integrabilidad) | No | PASS con defecto de localización (F-10) | Sí — RQ1, OE1 |
| 4 | `prop:pre-sp1-wrench-residual` | proposición | El QP regularizado tiene minimizador único y $\rho^{W,\min}\le\rho^{W\star}$; el certificado es conservador y su conversa falla | $\Lambda_k$ cerrado, convexo y no vacío; $Q_W\succ0$; $\varepsilon_\lambda>0$ | cuasiestático, planar, anterior al transporte | `app:sp1-wrench-proofs`, con contraejemplo escalar | eq. `eq:sp3-wrench` | CAR + SEG (certificado sin falsos positivos) | No — declara la conversa explícitamente | **PASS** | Sí — H2, RQ3 |
| 5 | `prop:sp2-compact-e4-potential` | proposición | Los costes de E4 definen un juego de potencial exacto cuyo minimizador coincide con los KKT compartidos y el equilibrio variacional | costes y conflictos congelados; $\alpha_4>0$; símplex no vacíos; $y_\ell\le1$; punto interior factible (Slater) | instantánea continua congelada | `app:sp4-game-proof` | eq. `eq:sp2-compact-e4-cost` | EX + CAR | No | **PASS** (duplicado de #21) | Indirecta |
| 6 | `thm:sp2-compact-e4-pose` | teorema | $\dot V\le0$ y LaSalle sobre $\dot V=0$ dan estabilidad asintótica local de la pose | $M_k,D_k,K_P,K_D\succ0$; objetivo y contactos fijos; $\boldsymbol r_k^W=0$ | carga planar con contacto bilateral fijo | `app:sp4-pose-proof` | eq. `eq:sp2-compact-e4-pose` | EST | **Sí** — invoca LaSalle sin conjunto compacto positivamente invariante y omite la carta de $SE(2)$ que sí tiene la versión del anexo | **LIMITED** | Sí (F-06) |
| 7 | `thm:sp2-compact-e6-exact-potential` | teorema | El juego de reparación es de potencial exacto, hay Nash puro y todo camino maximal termina en $\le 2^{n_R}-1$ cambios | implícitas: $\{0,1\}^{n_R}$ finito; $U_i$ definida por diferencia de $\Phi_6$; camino maximal | juego binario con déficit y costes congelados | `app:sp6-proofs` | eq. `eq:sp2-compact-e6-potential` | EX + FIP | No. La identidad de potencial es verdadera **por construcción** de $U_i$, y el texto no la presenta como descubrimiento | **PASS** | Sí — H4 |
| 8 | `thm:sp2-compact-e6-feasible-nash` | teorema | Los Nash puros coinciden con las coaliciones factibles mínimas por inclusión; $\mathrm{PoS}_6=1$ | escritas en el cuerpo: capacidades no negativas, costes positivos, $\lambda_6>\kappa^6_{\max}/\delta_{\min}$ | reparación estática con certificado aditivo | `app:sp6-feasible-nash-proof` | `thm:sp2-compact-e6-exact-potential` | CAR + OPT (PoS) | **Sí** — el cuerpo omite $w_a>0$, $D_6(\boldsymbol0)>0$ y «la reserva completa cubre $\boldsymbol d_k^6$», que es lo único que garantiza $\delta_{\min}>0$ | **LIMITED** | Sí — H4 (F-09) |
| 9 | `prop:sp2-compact-e6-unbounded-poa` | proposición | No hay cota uniforme del peor Nash factible: $\mathrm{PoA}_6=+\infty$ con un recurso y tres robots | independencia de instancia y de $\lambda_6$; construcción explícita | familia constructiva de costes positivos | `app:sp6-feasible-nash-proof` | `thm:sp2-compact-e6-feasible-nash` | OPT (cota negativa) | No. Contraejemplo verificado: capacidades $(1,\tfrac12,\tfrac12)$, costes $(M,1,1)$, $\lambda_6=5M/2$, $\delta_{\min}=\tfrac12$, cociente $M/2$ | **PASS** | Sí — conclusiones, §Contribución |
| 10 | `thm:sp3-compact-e7-potential` | teorema | El juego de rutas es de potencial exacto; hay Nash puro y todo camino maximal termina en $\le\prod_i|\mathcal R_i^7|-1$ cambios | catálogos finitos no vacíos; mejoras estrictas; camino maximal | rutas discretas sobre grafo inflado | `app:sp7-potential-proof` | eq. `eq:sp3-compact-e7-potential` | EX + FIP | No — el anexo añade que «una trayectoria truncada no hereda la conclusión» | **PASS** | Sí — RQ5 |
| 11 | `prop:sp3-compact-e7-conflict-free` | proposición | Si $\theta_7<\infty$ y $\lambda_7>\theta_7$, todo Nash puro tiene $P_7=0$ | $\theta_7<\infty$; $\lambda_7>\theta_7$ | catálogo discreto; falla en pasillo y cuello | `app:sp7-conflict-free-proof` | `thm:sp3-compact-e7-potential` | CAR | No — declara que la accesibilidad se infirió *a posteriori* y que falló en dos escenarios | **PASS** | Sí — RQ4, RQ5 |
| 12 | `prop:sp3-compact-e7-no-starvation` | proposición | Con liberación finita del testigo y sin reingreso, la regla $(w_i,P_i,-i)$ concede el testigo a cada solicitante en tiempo finito | cuerpo: liberación «en un número finito y acotado de pasos»; abandono tras cruzar; solicitantes persistentes | una sola zona; ejecutor discreto | `app:sp7-no-starvation` | Algoritmo `alg:sp7-reserva` | VIV (una zona) | **Sí, leve** — el cuerpo pierde el «uniformemente» acotado que la versión del anexo sí escribe, y sin uniformidad la prueba no cierra | LIMITED de redacción | Sí — RQ4 |
| 13 | `prop:megajuego-exact-potential` | proposición | Si ningún factor omitido de $J_i$ depende de $z_i$, toda desviación unilateral admisible cumple $\Delta_iJ_i=\Delta_i\Phi$ | factorización $\Phi=\sum_i\phi_i+\sum_a\psi_a$; admisibilidad (dinámica, contactos, soporte, ruedas, energía, seguridad, causalidad) | bloques con factores separables, antes de eliminar estados | `app:megajuego-potential-proof` | definición de $J_i$ | CAR (estructura de potencial) | No en el enunciado. La salvedad de localidad **sí está escrita**, pero solo dentro de la demostración del anexo | PASS con defecto de colocación | Sí — OE6/H6 (F-03) |
| 14 | `thm:megajuego-central-optimum` | teorema | Sobre $K$ convexo con $\Phi$ convexa y $F=\nabla\Phi$, la VI equivale a $\arg\min_K\Phi$; con convexidad fuerte el óptimo primal es único | $K$ no vacío, cerrado y convexo; $\Phi$ convexa diferenciable; $F=\operatorname{col}_i\nabla_{z_i}J_i=\nabla\Phi$ | una rama convexa — **nunca instanciada** | `app:megajuego-potential-proof` (dos líneas) | `prop:megajuego-exact-potential` para $F=\nabla\Phi$ | CAR + OPT dentro de la rama | **Sí** — el título dice «óptimo central», $K$ no se define en ningún punto del documento y lo que está congelado (modo discreto, coalición, contactos, homotopía) no se declara antes del enunciado | **LIMITED** | Sí — OE6/H6 (F-02) |
| 15 | `thm:megajuego-bezier-separation` | teorema | Para $0\le a_A,a_B$ y $0<D\le\sqrt6$, $\|P_A-P_B\|\ge D$ para todo $s$ si y solo si $a_A+a_B\ge D$ | $a_A,a_B\ge0$; $0<D\le\sqrt6$; familia geométrica fija; sin otros obstáculos; horizonte y avance longitudinal fijados | dos coaliciones, una familia de curvas Bézier de grado seis | `app:megajuego-bezier-proof` | eq. `eq:megajuego-bezier-curves` | SEG (separación continua, no muestreada) | No | **PASS** — reverificado: $\|P_A-P_B\|^2=36z+A^2(1-z)^6$ con $z=(2s-1)^2$, derivada $36-6D^2(1-z)^5\ge0$ si $D\le\sqrt6$ | Sí — OE6/H6 |
| 16 | `thm:megajuego-execution-budget` | teorema | $\kappa_WT_{\mathrm{mov}}+\delta N_{\mathrm{rev}}\le W_0$, de donde $T_{\mathrm{mov}}\le W_0/\kappa_W$ y $N_{\mathrm{rev}}\le\lfloor W_0/\delta\rfloor$ | testigo inicial seguro; tubos que componen; entradas locales realizables; $\dot W\le-\kappa_W$ durante el movimiento; $\delta>0$ por sustitución admitida | ejecución por tubos; **solo tiempo de movimiento** | `app:megajuego-budget-proof` | definiciones propias de tubo, testigo y composición | Terminación + FIP; **no** VIV, **no** OPT, **no** SEG | **Sí, por texto residual**: el `\estadoaporte` sigue diciendo «condicionado a … ausencia de Zeno», que el propio teorema desmiente; y la conclusión lo usa como presupuesto de **cómputo**, que el teorema excluye | **LIMITED** (prueba corregida correcta; residuos abiertos) | Sí — OE6/H6 y recomendación económica (F-01) |
| 17 | `prop:pre-sp2-kinematic-equivalence` | proposición | La coalición reproduce $\xi_L$ sí y solo si cada eje longitudinal es (anti)paralelo al pivote, la velocidad lateral es nula y las ruedas respetan sus límites | $v_i^{\mathrm{piv}}\ne0$; $\xi_L$ continuamente diferenciable; pivotes anclados; rama continua de rumbo | SI (m, s, rad); acoplamiento rígido ideal | en línea, `sp2-canonical-bridge.tex:23` | eq. `eq:pre-sp2-pivot-wheels` | CAR (cinemática) | No | **PASS** | No citada (huérfana) |
| 18 | `prop:pre-sp2-opposite-monotonicity` | proposición | Al retirar un miembro, el conjunto de alineación crece y el de *wrenches* realizables decrece; la factibilidad conjunta no es monótona en cardinalidad | $j\in\mathcal C$; reacción nula admisible | inclusiones de conjuntos | en línea, `sp2-canonical-bridge.tex:46` | definiciones de $\Xi^{\mathrm{align}}$ y $\mathcal W_{\mathcal C}$ | CAR | No | **PASS** | No citada (huérfana) |
| 19 | `prop:pre-sp2-scalar-insufficiency` | proposición | $\sum_i\bar t_i\ge\|F_d\|$ es necesaria pero no suficiente para realizar $(F_d,\tau_d)$ ni para certificar soporte o fricción | $\|t_i\|\le\bar t_i$; $\sum_it_i=F_d$ | contraejemplo analítico en SI | en línea, `sp2-canonical-bridge.tex:58` | — | CAR (cota negativa) | No | **PASS** | Sí, implícitamente — RQ3, sin `\ref` |
| 20 | `prop:sp2-marginal-alignment-detail` | proposición | Idéntica a #3 | idénticas | idéntico | `app:sp2-proofs`, en otro anexo | — | CAR | — | **DUPLICADO** de #3 | — |
| 21 | `prop:sp4-potential` | proposición | Idéntica a #5, con «convexidad fuerte y condición de Slater» explícitas | idénticas + Slater nombrado | idéntico | `app:sp4-game-proof` | — | EX + CAR | — | **DUPLICADO** de #5 | — |
| 22 | `prop:sp4-pose-stability` | teorema (etiquetado `prop:`) | Igual que #6, más la rama perturbada $\boldsymbol r_k^W\ne0$ con cota de disipación normalizada por $S_q$ | añade «error angular dentro de una carta de $SE(2)$» | idéntico + rama ISS-like | `app:sp4-pose-proof` | — | EST | La rama perturbada **no** concluye convergencia y lo dice | **DUPLICADO** de #6 + desajuste etiqueta/entorno | Sí, vía #6 |
| 23 | `thm:sp6-exact-potential` | teorema | Idéntico a #7 | idénticas | idéntico | `app:sp6-proofs` | — | EX + FIP | — | **DUPLICADO** de #7 | — |
| 24 | `thm:sp6-feasible-nash` | teorema | Igual que #8 pero **con** $w_a>0$, $D_6(\boldsymbol0)>0$ y cobertura de la reserva completa | completas | idéntico | `app:sp6-feasible-nash-proof` | `thm:sp6-exact-potential` | CAR + OPT | No — ésta es la versión correcta | **DUPLICADO** de #8, y el duplicado es más fuerte que el original | Sí |
| 25 | `prop:sp6-unbounded-poa` | proposición | Idéntica a #9 | idénticas | idéntico | `app:sp6-feasible-nash-proof` | — | OPT | — | **DUPLICADO** de #9 | — |
| 26 | `cor:sp6-time-bound` | corolario | $T_{\mathrm{rec}}\le\bar\tau_d+2^{n_R}\bar\tau_a+\max_i\ell_i/v_i^{\min}+\tau_s$ | ventanas agregadas acotadas por $\bar\tau_a$; trayectorias libres; $v_i^{\min}>0$; política que prolonga un camino maximal | segundos; modelo de arribo por segmento libre | `app:sp6-proofs` | #23 y #24 | Terminación temporal (ni VIV ni CPX) | No — dice que «la sola justicia no la implica» y que el término de viaje omite giro y evitación. El factor $2^{n_R}$ la hace operativamente vacía, y el texto no lo dice | PASS con vacuidad práctica no declarada | Sin contraparte en el cuerpo; no sostiene conclusión |
| 27 | `thm:sp7-exact-potential` | teorema | Idéntico a #10 | idénticas | idéntico | `app:sp7-potential-proof` | — | EX + FIP | — | **DUPLICADO** de #10 | — |
| 28 | `prop:sp7-conflict-free` | proposición | Idéntica a #11, sin la coletilla empírica | idénticas | idéntico | `app:sp7-conflict-free-proof` | #27 | CAR | — | **DUPLICADO** de #11 | — |
| 29 | `prop:sp7-no-starvation` | proposición | Igual que #12 pero con «uniformemente acotado» | completas | idéntico | `app:sp7-no-starvation` | `alg:sp7-reserva` | VIV | No — ésta es la versión correcta | **DUPLICADO** de #12, y más fuerte que el original | Sí |

### Objetos que actúan como resultados sin ser entornos formales

| Objeto | Dónde | Qué afirma | Estado |
|---|---|---|---|
| Certificado racional de *caging* | `megajuego-compact.tex:97-109`, `appendix-megajuego-detail.tex:113-137` | $z^\star$ racional exacto del QP con valor $513025/2349$, único por convexidad estricta | **ERROR NUMÉRICO** — ver F-07 |
| «Corolario, óptimo físico nominal dentro de la familia» | `appendix-megajuego-detail.tex:102-111` | «respalda optimalidad física nominal para el coste de suavidad y la familia fijados» | **Demostración sin enunciado** — ver F-08 |
| Complejidad $O(|\mathcal R_i^7|(|\mathcal E_i^7|+n_i))$ frente a oráculo exponencial | `tab:sp3-compact-e7-methods`, H5a | sostiene H5a con estado «Apoyo teórico» | **CPX sin enunciado ni prueba** — ver F-11 |

---

## 3. Duplicación estructural (FASE 8, «resultado utilizado después»; FASE 27)

Diez de los veintinueve entornos son el mismo resultado numerado dos veces
dentro del mismo PDF, una vez en el cuerpo y otra en el anexo de detalle:

| Cuerpo (Sección 6) | Anexo de detalle | ¿Hipótesis idénticas? |
|---|---|---|
| `prop:sp2-marginal-alignment` | `prop:sp2-marginal-alignment-detail` | sí |
| `prop:sp2-compact-e4-potential` | `prop:sp4-potential` | el anexo nombra Slater; el cuerpo lo parafrasea |
| `thm:sp2-compact-e4-pose` | `prop:sp4-pose-stability` | **no**: el anexo exige carta de $SE(2)$ |
| `thm:sp2-compact-e6-exact-potential` | `thm:sp6-exact-potential` | sí |
| `thm:sp2-compact-e6-feasible-nash` | `thm:sp6-feasible-nash` | **no**: el cuerpo omite tres hipótesis |
| `prop:sp2-compact-e6-unbounded-poa` | `prop:sp6-unbounded-poa` | sí |
| `thm:sp3-compact-e7-potential` | `thm:sp7-exact-potential` | sí |
| `prop:sp3-compact-e7-conflict-free` | `prop:sp7-conflict-free` | sí |
| `prop:sp3-compact-e7-no-starvation` | `prop:sp7-no-starvation` | **no**: el cuerpo pierde «uniformemente» |
| — | `cor:sp6-time-bound` | sin contraparte en el cuerpo |

Consecuencia para el tribunal: el lector ve «Teorema 6.x» y «Teorema H.y» como
dos resultados. El recuento de aportaciones formales queda inflado, y en tres de
los diez pares **la versión del anexo es estrictamente más fuerte que la del
cuerpo**, que es la dirección equivocada: el enunciado que el tribunal lee
primero es el débil en hipótesis y el fuerte en conclusión.

`semantic-all.csv` ya marcó como `DUPLICATE` las versiones de la rama `thesis/`
de seis de estos resultados (`prop:sp2-marginal-alignment`,
`prop:sp6-unbounded-poa`, `prop:sp7-conflict-free`, `prop:sp7-no-starvation`, y
por `retain-canonical-result-only` otros dos). La duplicación se reprodujo al
refundir la v2 en formato compacto + anexo de detalle.

---

## 4. Fichas de los resultados marcados

### F-01 · `thm:megajuego-execution-budget` — la corrección es sólida; quedan dos residuos

**La prueba corregida es correcta.** Verificada línea a línea en
`appendix-megajuego-detail.tex:156-205`:

- Las definiciones de *tubo*, *testigo inicial seguro* y *composición de tubos*
  están escritas antes de la demostración, y la composición se declara
  explícitamente «hipótesis del teorema, no una consecuencia que se derive de
  otro resultado del documento». Correcto y honesto.
- La cota de revisiones $\delta N_{\mathrm{rev}}\le W_0$ se obtiene por
  agotamiento del presupuesto, sin ausencia de Zeno. Correcto.
- El contraejemplo que justifica haber retirado la hipótesis es correcto: con
  $t_{k+1}-t_k=1/k$ la serie diverge, luego no hay acumulación en tiempo finito,
  y sin embargo $\inf_k(t_{k+1}-t_k)=0$. **No-Zeno $\ne$ *dwell time*** queda
  bien argumentado, que era exactamente el ítem de FASE 8.
- La cota sobre $T_{\mathrm{mov}}$ está correctamente restringida a la medida
  del conjunto de instantes con movimiento, y el teorema declara en su propio
  cuerpo que los intervalos de espera, deliberación o parada segura no están
  acotados.
- La separación terminación / vivacidad está escrita: «Lo demostrado es
  terminación, no vivacidad».

**Residuo 1 — el `\estadoaporte` no se actualizó.**
`megajuego-compact.tex:113` sigue diciendo:

> `demostrado, condicionado a testigo inicial seguro y ausencia de Zeno`

Esa línea se imprime inmediatamente encima del teorema que, ocho líneas más
abajo, dice «La finitud de $N_{\mathrm{rev}}$ **no** requiere suponer ausencia
de Zeno». El documento se contradice a sí mismo en el mismo bloque
`contribucion`. Es el único resto textual de la versión antigua que he
localizado: no queda ninguna otra aparición de «Zeno», «dwell», «tiempo de
permanencia» ni «duración de la misión» asociada a este teorema fuera de los
pasajes ya corregidos.

**Residuo 2 — la conclusión usa el teorema fuera de su dominio.**
`conclusions-megajuego-addendum.tex:77-84`:

> «el criterio de viabilidad es si ese coste [de cómputo] cabe en el presupuesto
> de ejecución del Teorema `thm:megajuego-execution-budget`»

$W$ decrece por **movimiento** y por **sustituciones admitidas**. El teorema
excluye expresamente que los intervalos de deliberación consuman $\kappa_W$.
Usarlo como presupuesto de cómputo por misión invierte justamente la corrección
que se acaba de hacer. La recomendación económica es razonable, pero no la
sostiene este teorema.

**Hueco menor de hipótesis.** La demostración usa dos veces que el presupuesto
es no negativo («el presupuesto es no negativo y parte de $W_0$»; «$0\le W\le
W_0-\kappa_WT_{\mathrm{mov}}-\delta N_{\mathrm{rev}}$»), y $W\ge0$ **no figura
entre las hipótesis del enunciado**. Sin ella no hay cota. Es una línea.

**Hipótesis inertes.** «Testigo inicial seguro», «tubos que componen» y
«entradas locales realizables» no intervienen en la aritmética de las dos cotas;
sostienen el invariante de seguridad que la inducción arrastra pero que **no
forma parte de la conclusión enunciada**. No es un error, pero infla la
apariencia del resultado: un lector supone que el teorema certifica seguridad
persistente, y lo que certifica es contabilidad.

**Cotejo con el atlas.** El antecesor de este resultado,
`pr:presupuesto-progreso` (`paper/sec_continuacion.tex`), figura en
`semantic-all.csv` como LIMITED con la razón «la cota es una identidad contable
condicional, no consecuencia de las frases *consume* y *mejora* sin una ecuación
de balance precisa». La versión actual **sí** escribe la ecuación de balance.
La objeción del atlas está atendida. `co:terminacion` (FAIL) y `th:dwell` (FAIL)
del mismo atlas son precisamente los dos errores que esta corrección elimina.

---

### F-02 · `thm:megajuego-central-optimum` — un lector puede creer que el hibrido completo es convexo

**Respuesta directa a la pregunta: no, no está declarado antes del enunciado, y
sí, el lector puede creerlo.**

Lo que precede al teorema en `megajuego-compact.tex:54-57` es una sola línea:

> «Con $\Phi(d,z)=\sum_i\phi_i(z_i)+\sum_a\psi_a(z_{\mathcal I_a})$ y
> $J_i=\phi_i+\sum_{a:i\in\mathcal I_a}\psi_a$»

No hay ninguna frase que diga qué se congela. El conjunto $K$ aparece por
primera vez dentro del propio enunciado, como «$K$ no vacío, cerrado y convexo»,
y **no se instancia en ningún punto del documento**: ni en el cuerpo, ni en la
nomenclatura (`04-nomenclature-megajuego-v2.tex:12` se limita a «conjunto
factible»), ni en el anexo. El estado aumentado $Y$ de la
Ecuación `eq:megajuego-state` incluye modo discreto, compromisos atómicos y
reservas, todos no convexos. Un lector que encadene $Y$ con $K$ concluye que
el teorema habla del conjunto factible del híbrido.

Lo que atenúa, y dónde está:

1. El título del teorema dice «de una rama convexa».
2. El pie de la Figura `fig:megajuego-architecture` dice «no certifica: óptimo
   global del híbrido».
3. El párrafo posterior (`megajuego-compact.tex:133-138`) repite que ninguno de
   los cuatro resultados certifica óptimo global del híbrido.
4. El anexo, **después** de la demostración
   (`appendix-megajuego-detail.tex:27`), escribe la frase decisiva: «Fijar
   coalición y homotopía no garantiza por sí solo la convexidad requerida».

Los cuatro son negaciones. Ninguno dice **qué sí** está congelado para que la
rama sea convexa. Falta la afirmación positiva —modo discreto fijo, coalición
fija, conjunto de contactos activo fijo, clase de homotopía fija, y aun así la
convexidad de $\Phi$ y de $K$ como hipótesis verificable, no derivada— y falta
antes del enunciado, no en el anexo.

**Dos huecos adicionales del enunciado.**

- No se pide $z^\star\in K$. La desigualdad variacional
  $\langle F(z^\star),z-z^\star\rangle\ge0\ \forall z\in K$ presupone la
  pertenencia; tal como está escrito, el miembro izquierdo tiene sentido para
  $z^\star$ arbitrario y la equivalencia es falsa.
- La hipótesis $F=\nabla\Phi$ es exactamente lo que
  `prop:megajuego-exact-potential` debería suministrar, y el documento presenta
  ambos resultados en el mismo bloque `contribucion` como si encadenaran. No
  encadenan sin un supuesto que no está escrito: la proposición da una identidad
  **de diferencias finitas para desviaciones admisibles**, y el paso a la
  igualdad de gradientes requiere que $z_i$ sea interior a su conjunto
  admisible. Justo en la frontera —que es donde muerden las restricciones de
  contacto, ruedas, energía y seguridad— la identidad de diferencias no entrega
  el gradiente. Ver F-03.

**Demostración.** Dos líneas: «Es la condición de primer orden de minimización
convexa; en ambos sentidos se utiliza el segmento factible entre $z^\star$ y
$z$». Es correcta y es estándar. Bajo FASE 7 («no presentar integración de
componentes conocidos como un theorem nuevo si no lo es») convendría decir que
es la caracterización clásica de la VI de un problema convexo, no un resultado
del TFM; el anexo `app:megajuego-scope` lo dice en general para todos los
bloques, pero no para este teorema en particular.

---

### F-03 · `prop:megajuego-exact-potential` — la salvedad existe, pero está en el peor sitio posible

**Respuesta directa: sí, el documento enuncia la salvedad, y lo hace con la
formulación exacta del criterio de FASE 8 («graph factorization $\ne$ reduced
locality»).** `appendix-megajuego-detail.tex:10-17`:

> «Si se eliminan los estados mediante integración, una entrada local puede
> afectar costes remotos; esos gradientes deben propagarse mediante adjuntos o
> mensajes, o acotarse. **La factorización antes de eliminar estados no prueba
> localidad de la sensibilidad reducida.**»

Tres objeciones, todas de colocación y ninguna de contenido:

1. Está **dentro del entorno `proof`**, no en el enunciado ni en una observación
   posterior. Una salvedad que limita el alcance de una proposición no pertenece
   al cuerpo de su demostración: quien lea el teorema en el cuerpo de la memoria
   —que es donde está enunciado— no la verá nunca.
2. No aparece en el cuerpo de la memoria en ninguna forma. La Sección 6.5 enuncia
   la proposición y pasa directamente al teorema del óptimo central.
3. La misma demostración contiene una segunda salvedad de calado —«No se define
   el coste social como $\sum_iJ_i$: eso duplicaría factores compartidos»— que
   es correcta e importante (con factores de acoplamiento compartidos,
   $\sum_iJ_i$ cuenta cada $\psi_a$ tantas veces como $|\mathcal I_a|$) y que
   tampoco sale del anexo.

Lo que la proposición **sí** establece: una identidad estructural, verdadera por
construcción de $J_i$ a partir de la factorización. No establece localidad, no
establece convergencia de ninguna dinámica, y no establece que las desviaciones
admisibles formen un entorno. El enunciado no afirma nada de eso, de modo que el
resultado en sí es PASS.

---

### F-04 · `prop:pre-cross-partition-limit` — «la razón formal» es una sobreatribución

**Respuesta directa: sí, hay sobreafirmación, y está en la conclusión, no en la
proposición.**

La proposición y su `\estadoaporte` son ejemplares: declaran la clase
(«algoritmos deterministas basados en historial local»), niegan novedad («es una
aplicación de un argumento de indistinguibilidad clásico … no un resultado de
imposibilidad nuevo»), citan a Fischer–Lynch–Paterson, y el párrafo posterior
acota el alcance («no excluye optimalidad en una familia *singleton*, cuando la
interacción remota es nula o conocida, ni cuando ambas instancias comparten una
acción local óptima»). El testigo concreto en E7 está construido y es correcto.

El problema son dos frases:

1. `thesis-results-v2.tex:78-80`: «**Esta es la razón** por la que E7 certifica
   exclusión local y terminación, no optimalidad global de la asignación
   completa de rutas.»
2. `conclusions-megajuego-addendum.tex:24-26`: «Lo que OE6 no entrega es un
   certificado de optimalidad global del sistema híbrido bajo revisiones
   discretas arbitrarias; la Proposición … **da la razón formal de esa
   ausencia**.»

La segunda es la grave. La proposición habla de un algoritmo determinista
restringido al historial local de una componente. La ausencia de optimalidad
global del **sistema híbrido bajo revisiones discretas arbitrarias** tiene al
menos tres causas independientes, y la partición informacional es solo una:

- La regla de admisión es de mejora sobre la política vigente
  (`megajuego-compact.tex:10-12`): un esquema de ascenso que termina en óptimos
  locales del potencial, no en el global. Esto es cierto incluso con información
  perfecta y centralizada.
- El conjunto factible del híbrido no es convexo (F-02), de modo que la
  equivalencia VI–óptimo de `thm:megajuego-central-optimum` no se aplica fuera
  de una rama.
- La ruta espacial es «una solución local del optimizador de *spline* o
  potencial» (`megajuego-compact.tex:188-190`), por optimización no convexa, no
  por información.

Ninguna de las tres desaparece si se da información global. Por tanto la
proposición da **una** obstrucción suficiente en **una** clase de algoritmos, no
«la razón formal» de la ausencia. Además, para que la primera frase cierre
haría falta verificar que el E7 implementado pertenece a esa clase —determinista
y con estado y salida dependientes solo del historial local—, cosa que el texto
asume sin comprobar.

Redacción que sí sostendría la evidencia: «una de las obstrucciones es
informacional y la Proposición X la formaliza para los algoritmos deterministas
de historial local; las otras dos son la regla de mejora local y la no convexidad
del conjunto híbrido».

---

### F-05 · Convención de signo de $\Phi$ — no está declarada en ninguna parte

**Respuesta directa: no. El documento nunca dice que cambia de convención, y la
única convención que declara explícitamente es la contraria a la que usa el
juego de integración.**

El marco teórico fija la convención canónica en
`05-theoretical-framework.tex:47-53`, en forma de **utilidad**:

$$u_i(a_i',a_{-i})-u_i(a_i,a_{-i})=\Phi(a_i',a_{-i})-\Phi(a_i,a_{-i})$$

y el párrafo la lee en clave de maximización («toda estrategia con masa positiva
alcanza el pago máximo»). La nomenclatura tiene una sola entrada,
`04-nomenclature.tex:21`: «$\Phi$ · Función potencial global del juego», sin
signo.

Lo que el documento hace después:

| Bloque | Definición | Se busca | Convención |
|---|---|---|---|
| SP1 E1 | $\Phi_1(a)=-\{C+\lambda D+\lambda O\}$ | «Los **máximos globales** de $\Phi_1$…» | utilidad (maximizar) |
| SP1 E2 | $\partial\Phi/\partial\rho_{ik}=f^{\mathrm{marg}}_{ik}$ con pago | ascenso | utilidad |
| SP2 E4 | $J_G$, $J_i$ costes; «juego de potencial exacto» | «cuyo **minimizador** coincide con los KKT» | **coste (minimizar)** |
| SP2 E6 | $\Phi_6=-\lambda_6D_6-K_6$ | «el potencial alcanza un **máximo**, que es Nash» | utilidad |
| SP3 E7 | $\Phi_7=-\sum_ib^7-\lambda_7P_7$ | mejoras estrictas ascendentes | utilidad |
| Integración | $\Phi(d,z)=\sum_i\phi_i+\sum_a\psi_a$ | «$z^\star\in\arg\min_K\Phi$» | **coste (minimizar)** |

Dos convenciones opuestas, el mismo símbolo $\Phi$, la misma memoria, y una sola
entrada de nomenclatura. En E4 el conflicto es además interno al bloque: el
marco teórico dice «pago», `eq:sp4-payoff` define $f_{ia}$ como **el negativo**
del gradiente de $J_G$, y la proposición habla de minimizador. La relación está
escrita en el anexo (`06-sp4-proofs.tex:20-25`: «el negativo del gradiente, más
el precio compartido, coincide con el pago»), lo cual resuelve E4 pero no
enuncia la regla general.

Coste de no declararlo: un tribunal que compare el Teorema 6.1 («los máximos
globales de $\Phi_1$») con el Teorema 6.x («$\arg\min_K\Phi$») ve una
inconsistencia de signo donde hay una elección deliberada. Y en FASE 18 («signos
correctos») y FASE 31 («¿dónde están los supuestos?») esto se lee como descuido,
no como convención.

Lo que faltaría: una frase en el marco teórico o en la nomenclatura del tipo
«SP1, E6 y E7 usan potencial de utilidad, que se maximiza; E4 y el juego de
integración usan potencial de coste, que se minimiza; ambas convenciones son
equivalentes bajo cambio de signo y cada enunciado indica cuál emplea». Una
frase, dos ubicaciones.

---

### F-06 · `thm:sp2-compact-e4-pose` — LaSalle sin conjunto compacto positivamente invariante

**Respuesta directa: no. No se especifica ningún conjunto de nivel compacto
positivamente invariante, ni en el cuerpo ni en el anexo.**

El cuerpo (`sp2-compact.tex:74`) dice: «la función $V=\ldots$ satisface
$\dot V\le0$; el principio de invariancia de LaSalle **sobre el conjunto
$\dot V=0$** da entonces estabilidad asintótica local».

El anexo (`06-sp4-proofs.tex:56-63`) dice: «En el mayor conjunto invariante
contenido en $\dot V=0$ se cumple $\dot q^L_k=0$ y, por la dinámica,
$K_Pe^L_k=0$. Como $K_P\succ0$, $e^L_k=0$. El principio de invariancia de
LaSalle da estabilidad asintótica local en la carta angular considerada.»

**La mecánica del argumento es correcta.** Sustituyendo la ley de control en la
dinámica se obtiene $M_k\ddot q+(D_k+K_D)\dot q+K_Pe=0$, y
$\dot V=-\dot q^{\mathsf T}(D_k+K_D)\dot q\le0$ es exacta. La identificación del
mayor conjunto invariante con el origen es correcta. Lo que falta es la
precondición del teorema:

1. **El conjunto compacto positivamente invariante no se nombra.** LaSalle exige
   un $\Omega$ compacto y positivamente invariante donde vive la trayectoria.
   Aquí es inmediato —$V$ es cuadrática definida positiva, luego
   $\Omega_c=\{V\le c\}$ es compacto, y $\dot V\le0$ lo hace positivamente
   invariante— pero hay que escribirlo, y una línea basta. Sin él, el enunciado
   invoca un teorema cuyas hipótesis no ha verificado.
2. **El $c$ admisible no se acota, y es donde está la sustancia.** Dos
   restricciones lo limitan y ninguna se conecta con $\Omega_c$:
   - La hipótesis $\boldsymbol r^W_k=0$ (realización exacta) solo se cumple
     mientras $W^d_k=-K_Pe-K_D\dot q$ sea alcanzable por el reparto saturado
     $0\le\lambda\le\bar\lambda$ de `eq:sp2-compact-e4-pose`. Eso define una
     región del espacio de estados, y $\Omega_c$ debe caber dentro de ella. Como
     $\|W^d_k\|$ crece con $\|e\|$ y $\|\dot q\|$, es exactamente la condición
     que convierte «global» en «local», y es la que justifica la palabra
     «local» del enunciado. No está escrita.
   - La carta local de $SE(2)$: el anexo la exige («error angular dentro de una
     carta»), el cuerpo la omite, y en ningún caso se pide que $\Omega_c$ quede
     contenido en la carta.
3. **El cuerpo pierde una hipótesis respecto del anexo.** `thm:sp2-compact-e4-pose`
   no menciona la carta angular; `prop:sp4-pose-stability` sí. El enunciado que
   lee el tribunal es el débil.

Observación colateral: dentro de la carta y con realización exacta, el sistema
es lineal invariante y $V$ radialmente no acotada, de modo que lo demostrable
sería estabilidad asintótica **en toda la región donde la saturación no muerde**.
Decir «local» sin decir «local respecto de qué» renuncia a fuerza sin ganar
precisión.

La rama perturbada ($\boldsymbol r^W_k\ne0$) está bien tratada: la cota de Young
con la métrica $S_q$ está explicitada, la dependencia de la escala $\ell_0$ se
declara no invariante, y el anexo dice expresamente que de esa desigualdad «no
se deduce convergencia exacta». Eso es correcto: **estabilidad $\ne$ seguridad**
y la cota ISS-*like* no se disfraza de convergencia.

---

### F-07 · *Caging* — la solución racional publicada está mal transcrita

**Hallazgo nuevo, verificado en aritmética exacta.** El vector $z^\star$ que
aparece dos veces en el documento —`megajuego-compact.tex:103` y
`appendix-megajuego-detail.tex:131`— es:

$$z^\star=\Big(0,\,0,\,\tfrac{475}{261},\,-\tfrac{190}{\mathbf{29}},\,\tfrac{500}{29},\,-\tfrac{200}{29},\,\tfrac{2275}{261},\,-\tfrac{910}{261}\Big)$$

Con ese vector, y con $A$ tal como se publica en
`appendix-megajuego-detail.tex:127`:

| Comprobación | Resultado con el vector publicado | Debería ser |
|---|---|---|
| $Az$ | $(3700/261,\;0,\;221/29)\approx(14.18,\,0,\,7.62)$ | $(20,0,5)$ |
| $\tfrac12z^{\mathsf T}z$ | $1813525/7569\approx239.599$ | $513025/2349\approx218.401$ |
| $\lvert t_2\rvert\le0.4\,n_2$ | $6.552\le0.728$ — **falso** | debe cumplirse |

Es decir: tal como está impreso, el punto **no es factible, no satisface la
demanda de *wrench* y no vale lo que el texto dice que vale**.

La causa es una errata de un solo carácter. Con $t_2=-190/\mathbf{261}$ en lugar
de $-190/29$:

| Comprobación | Resultado |
|---|---|
| $Az$ | $(20,\,0,\,5)$ exacto |
| $\tfrac12z^{\mathsf T}z$ | $513025/2349$ exacto, idéntico al valor publicado |
| $\lvert t_i\rvert\le0.4\,n_i$ | los tres contactos activos quedan **exactamente** en la frontera del cono: $190/261=0.4\cdot475/261$, $200/29=0.4\cdot500/29$, $910/261=0.4\cdot2275/261$ |
| $0\le n_i\le30$ | $\max n_i=500/29\approx17.24$ |

El valor $513025/2349$, el residual KKT de $1.4\times10^{-11}$, la potencia
$P_{cu}^\star=20521/3915$ W y el resto de cifras derivadas son **correctos**: se
calcularon con el vector bueno. Lo que falla es la transcripción del vector al
`.tex`, repetida en los dos sitios.

Gravedad: alta en percepción, baja en contenido. Es el único resultado de la
memoria que se presenta como «solución racional **exacta**» verificada con
SymPy, y es trivialmente falsable por cualquier miembro del tribunal con una
calculadora: basta comprobar el signo de fricción del segundo contacto. Un
resultado exacto que no cierra destruye la credibilidad del bloque entero, que
por lo demás es correcto.

(Corrección: sustituir `-\tfrac{190}{29}` por `-\tfrac{190}{261}` en
`sections/v2/megajuego-compact.tex:103` y en
`sections/v2/appendix-megajuego-detail.tex:131`. No se ha aplicado.)

---

### F-08 · Una demostración sin enunciado, y afirma optimalidad

`appendix-megajuego-detail.tex:102-111` contiene:

```
\begin{proof}[Demostración del Corolario, óptimo físico nominal dentro de la familia]
```

No existe ningún `\begin{corolario}` correspondiente. El censo confirma que no
hay ningún entorno formal de tipo corolario en el juego de integración: el
documento demuestra un resultado que nunca enuncia. FASE 8 pide «Enunciado» como
primer ítem.

El contenido de esa demostración afirma:

> «Este razonamiento respalda **optimalidad física nominal** para el coste de
> suavidad y la familia fijados»

con la matización, en la misma frase, de que «no sustituye ese coste por energía
de batería ni extiende el resultado a otra homotopía, duración, adquisición o
planta con *compliance*». El razonamiento —restringir un conjunto no disminuye
su mínimo, y el mínimo global posee levantamiento factible, luego sigue siendo
alcanzable— es correcto. Pero una afirmación de **optimalidad** enterrada en un
entorno `proof` sin enunciado no es auditable: no tiene hipótesis listadas, no
tiene etiqueta, no se puede citar y no se puede contar entre los resultados.

Efecto colateral sobre el recuento: el cuerpo dice «los **cuatro** resultados
anteriores» y la conclusión dice «cuatro resultados demostrados algebraicamente
y verificados numéricamente». En entornos formales hay **tres** (`prop`
+ `thm` del bloque de potencial, `thm` de Bézier, `thm` de presupuesto = cuatro
entornos que se agrupan en tres contribuciones), el *caging* no es un entorno
formal, y este corolario es una prueba sin enunciado. El «cuatro» del texto no
se corresponde con ninguna partición limpia de los objetos del documento.

---

### F-09 · `thm:sp2-compact-e6-feasible-nash` — tres hipótesis se pierden al compactar

Cuerpo, `sp2-compact.tex:125`:

> «Con capacidades no negativas, costes positivos y
> $\lambda_6>\kappa_{\max}^6/\delta_{\min}$, los Nash puros coinciden
> exactamente con las coaliciones factibles mínimas por inclusión, de donde
> $\mathrm{PoS}_6=1$.»

Anexo, `sp2-e6-trimmed.tex:74`:

> «Supónganse capacidades no negativas, **$w_a>0$**, costes $\kappa_i^6>0$ para
> todo $i$ y **un déficit postfallo no trivial $D_6(\boldsymbol0)>0$**. **Si la
> reserva completa cubre $\boldsymbol d_k^6$, entonces $\delta_{\min}>0$.** Si
> $\lambda_6>\kappa_{\max}^6/\delta_{\min}$ …»

Las tres hipótesis en negrita no son adorno. La demostración
(`thesis-appendices.tex:44`) empieza precisamente por ellas: «La factibilidad de
la reserva completa implica que algún robot no seleccionado reduce estrictamente
$D_6$; como hay finitos perfiles deficitarios, el mínimo es positivo». Sin
cobertura de la reserva, $\delta_{\min}$ puede ser $0$ y el umbral
$\lambda_6>\kappa^6_{\max}/\delta_{\min}$ es inexigible. El enunciado del cuerpo
usa $\delta_{\min}$ sin definirlo (su definición es `eq:sp6-delta-min`, en el
anexo; la nomenclatura sí lo recoge, `04-nomenclature.tex:47`) y sin garantizar
su positividad.

`semantic-all.csv` ya había juzgado la versión previa de este mismo enunciado
como LIMITED con la razón literal: «la equivalencia es recuperable y está
probada bajo costes positivos, **pero es falsa bajo los supuestos escritos**;
FSF-13 es la versión activa corregida». La versión corregida está en el anexo.
El cuerpo volvió a la forma que el atlas había marcado.

---

### F-10 · Duplicación, desajuste etiqueta/entorno y resultados huérfanos

1. **Duplicación**: diez pares, tabla de la §3. Tres pares con hipótesis
   distintas, siempre en la dirección mala.
2. **Etiqueta/entorno**: `prop:sp4-pose-stability` es un `\begin{teorema}` con
   prefijo `prop:`, y `sp2-canonical-bridge.tex:64` lo cita como «El
   Teorema~\ref{prop:sp4-pose-stability}». Funciona, pero cualquier auditoría
   automática por prefijo lo clasificará mal; el censo, de hecho, lo lista como
   `teorema` con etiqueta `prop:`.
3. **Huérfanos** (FASE 8, «resultado utilizado después»): cinco entornos no se
   citan con `\ref` desde ningún punto del documento activo —
   `prop:sp2-marginal-alignment`, `prop:sp2-compact-e4-potential`,
   `thm:sp2-compact-e4-pose`, `thm:sp3-compact-e7-potential` y los tres del
   puente canónico `prop:pre-sp2-*`. Los tres del puente canónico son el caso
   más llamativo: sostienen materialmente RQ3 («cardinalidad y servicio no son
   certificados mecánicos») y no se enlazan desde ningún sitio, de modo que un
   lector de las conclusiones no puede llegar al resultado que las respalda.
4. **Cadena de prueba indirecta**: el `\estadoaporte` de
   `prop:sp2-marginal-alignment` remite a `app:sp1-full-detail`, que reenuncia el
   resultado como `prop:sp2-marginal-alignment-detail` **sin demostrarlo**; la
   demostración está en `04-sp2-proofs.tex`, dentro de otro anexo
   (`app:sp1-all-proofs`). El lector que siga el puntero no encuentra la prueba.

---

### F-11 · La complejidad se afirma sin enunciado (H5a)

`tab:conclusion-hypotheses` cierra H5a como «Apoyo **teórico**», con evidencia
«Revisión local $O(|\mathcal R_i^7|(|\mathcal E_i^7|+n_i))$ frente al oráculo
restringido exponencial».

**Complejidad** es una de las nueve categorías del criterio, y es la única que la
memoria afirma sin ningún entorno formal, sin demostración y sin verificación.
Las cotas $O(\cdot)$ viven en la columna «Coste» o «Coste declarado» de las
tablas de métodos (`tab:sp1-compact-e2-methods`, `tab:sp2-compact-e4-methods`,
`tab:sp2-compact-e6-methods`, `tab:sp3-compact-e7-methods`), sin derivación en
ningún anexo. FASE 19 pide «Complejidad correcta» y FASE 8 pide «Prueba
completa» para cada resultado usado después; H5a usa estas cifras como su único
apoyo.

La atenuación existe y es correcta («no caracteriza todo centralizador», «sin
curvas activas por tamaño o grado»), pero atenúa el alcance, no la ausencia de
demostración. Lo mínimo sería una línea por cota indicando de dónde sale el
conteo, o reclasificar H5a de «apoyo teórico» a «cota declarada por inspección
del algoritmo».

---

### F-12 · FASE 9 — el objeto global no está definido como juego

El criterio es explícito: si se llama juego, hay que definir
$\mathcal G=(\mathcal P,Y,\Gamma,J,\mathcal R,F,G)$; si no, hay que renombrar a
«Arquitectura de Continuaciones Certificadas», y «no llamar *juego* a una
colección de certificados si el objeto global no está definido».

Inventario de los doce elementos que pide FASE 9 en la Sección 6.5:

| Elemento | ¿Definido? | Dónde |
|---|---|---|
| jugadores / bloques | **No** | se habla de «cada bloque» y «cada continuación»; $\mathcal P$ no se define ni se dice si los jugadores son robots, coaliciones o bloques |
| estado | Sí | `eq:megajuego-state` |
| información | Sí | $\mathcal I$, con procedencia |
| acciones / continuaciones | Parcial | «continuación causal» en la figura; sin conjunto $\Gamma$ |
| conjunto certificado | Sí, en prosa | lista de admisibilidad de `prop:megajuego-exact-potential` |
| payoff / cost | Sí | $J_i$ |
| potencial | Sí | $\Phi$ |
| regla de revisión | Sí, en prosa | «se admite solo si mejora sobre la política vigente» |
| incumbent | Sí | $\Pi^{\mathrm{inc}}$ en el estado |
| flow | **No** | ninguna dinámica de revisión se define |
| reset | **No** | — |
| stopping / admission | Parcial | la admisión sí; la parada solo por agotamiento de presupuesto |

Ocho de doce, ninguno reunido en una definición. El objeto $\mathcal G$ no se
escribe nunca. Lo que existe formalmente son cuatro certificados por bloque
sobre escenarios concretos y acotados, cosa que el propio documento dice con
claridad («el certificado es válido por bloque, no como optimalidad global del
sistema híbrido»).

Lectura estricta del criterio: **el nombre «juego de integración» no está
sostenido**; la etiqueta correcta sería la que el propio checklist propone. Dos
salidas posibles y ambas legítimas: escribir la definición del objeto —lo que
obliga a fijar $\mathcal P$, $\Gamma$, $F$ y la regla de reset—, o renombrar. La
segunda es barata y no cuesta ninguna afirmación, porque ninguna afirmación
activa depende de que el objeto sea un juego: depende de los cuatro certificados.

---

## 5. Cotejo con los veredictos previos del proyecto

### 5.1 `formal-spine-final-verdicts.csv` (18 resultados, todos PASS)

**Los 18 FSF apuntan a fuentes que ya no son las compiladas.** Las rutas
registradas son `pre-thesis/sections/thesis-results.tex` y
`pre-thesis/sections/source-snapshot/mainmatter/06-results-and-analysis/sp{2,3,4,6,7}.tex`.
Ninguno de esos ficheros está en el cierre activo de `main-v2.tex`: el documento
compila `sections/v2/*-compact.tex` y `sections/v2/support/*-trimmed.tex`. El
veredicto PASS se emitió sobre la v1, no sobre los enunciados compactos que el
tribunal leerá.

Ese desfase tiene consecuencias materiales, no formales: F-06, F-09 y F-12
señalan exactamente los tres puntos donde la refundición compacta perdió
hipótesis respecto de la versión auditada.

Correspondencia y huecos:

| FSF | Resultado activo correspondiente | Observación |
|---|---|---|
| FSF-01 | #2 `thm:pre-sp1-exact-quota` | correspondencia limpia |
| FSF-02 | #3 `prop:sp2-marginal-alignment` | correspondencia limpia |
| FSF-03 | #17 | correspondencia limpia |
| FSF-04 «Cota de ruedas en giro puro» | **sin entorno formal** | vive como texto corrido en `sp2-canonical-bridge.tex:30-33` |
| FSF-05 | #18 | — |
| FSF-06 | #19 | — |
| FSF-07 | #6 / #22 | el cuerpo perdió la carta de $SE(2)$ |
| FSF-08 | rama perturbada de #22 | solo en el anexo |
| FSF-09, FSF-10 | #4 | — |
| FSF-11 «Potencial continuo y acción inactiva» | **no está en el documento activo** | el propio CSV dice «resultado conservado en la monografía» |
| FSF-12 … FSF-15 | #7, #8, #9, #26 | FSF-13 es la versión que el cuerpo debilitó (F-09) |
| FSF-16, FSF-17 | #10, #11, #12 | FSF-17 cubre dos resultados en una fila |
| FSF-18 | #1 | — |
| **sin FSF** | #13, #14, #15, #16 — **los cuatro del juego de integración** | el espinazo formal del proyecto no cubre la Sección 6.5 |
| **sin FSF** | *caging*, corolario sin enunciado | — |

El hueco relevante: **OE6 y H6 se cierran sobre cuatro resultados que el
espinazo formal nunca auditó**. La verificación que sí existe para ellos es la
numérica (extragradiente en 30 instancias, SymPy, residual KKT), no una
auditoría de enunciado.

### 5.2 `semantic-all.csv` (166 candidatos)

Distribución normalizada: 18 PASS, 87 LIMITED, 43 FAIL, 16 DUPLICATE, 2
CONJECTURE.

Solo 10 de las 29 etiquetas activas aparecen en el atlas, y aparecen con rutas
de la rama `thesis/`: el atlas cubre `thesis/` y `paper/`, no
`pre-thesis/sections/v2/`. La coincidencia es de nombre de etiqueta, no de
fichero. Aun así, dos de sus dictámenes siguen vigentes y se han verificado en
esta auditoría:

- `thm:sp6-feasible-nash` — LIMITED: «es falsa bajo los supuestos escritos».
  Reproducido en el cuerpo de la v2 (F-09).
- `cor:sp6-time-bound` — LIMITED: «es una identidad condicional incompleta, no
  una cota bajo justicia sola». La v2 **sí** corrigió la premisa: el anexo dice
  literalmente «la sola justicia no la implica». Objeción atendida.

Antecesores del juego de integración en `paper/megajuego.tex`, relevantes porque
la Sección 6.5 desciende de ellos:

| Etiqueta antigua | Veredicto | ¿Sobrevive en la v2? |
|---|---|---|
| `co:terminacion` | FAIL | **No** — sustituido por `thm:megajuego-execution-budget`, que sí escribe el balance |
| `th:dwell` | FAIL («no excluye Zenón») | **No** — la v2 retiró la hipótesis y explica por qué |
| `pr:presupuesto-progreso` | LIMITED («identidad contable condicional») | **Sí, como identidad contable declarada**, que es la forma correcta |
| `pr:caging` | FAIL («no prueba confinamiento de un cuerpo con orientación») | **No** — la v2 no enuncia ningún teorema de *caging*; presenta un QP con solución exacta, que es un objeto distinto y defendible |
| `th:cert` | FAIL («la regularización sí puede modificar el residual») | **Atendido** por #4, que demuestra justamente esa desigualdad y su contraejemplo |
| `th:potencial`, `th:vi` | LIMITED | reaparecen como #13 y #14, con los huecos de F-02 y F-03 |

La depuración de la monografía al cuerpo activo fue, en conjunto, correcta:
los seis FAIL de arriba no llegaron al documento. Lo que llegó con defecto es de
redacción y de colocación, no de contenido.

---

## 6. Lo que queda abierto, por prioridad

**P0 — falsable por el tribunal en un minuto**

1. F-07 · `z^\star` del QP de *caging*: `-190/29` → `-190/261`, en dos ficheros.

**P1 — el enunciado afirma más que la prueba**

2. F-01 · retirar «ausencia de Zeno» del `\estadoaporte` en
   `megajuego-compact.tex:113`; añadir $W\ge0$ a las hipótesis; reescribir el
   uso del teorema en la recomendación económica.
3. F-02 · declarar, antes del teorema, qué se congela para que la rama sea
   convexa, e instanciar $K$; pedir $z^\star\in K$.
4. F-06 · nombrar $\Omega_c=\{V\le c\}$ como compacto positivamente invariante,
   acotar $c$ por la región de realización exacta y por la carta de $SE(2)$;
   devolver la carta al enunciado del cuerpo.
5. F-09 · devolver al cuerpo las tres hipótesis del anexo.
6. F-04 · sustituir «la razón formal» por «una de las obstrucciones, la
   informacional».
7. F-12 · definir $\mathcal G$ o renombrar la Sección 6.5.

**P2 — higiene formal**

8. F-05 · una frase de convención de signo de $\Phi$.
9. F-03 · subir la salvedad de localidad del cuerpo de la demostración a una
   observación tras el enunciado.
10. F-08 · enunciar el corolario del óptimo físico nominal, o degradar su
    demostración a observación sin afirmación de optimalidad.
11. F-10 · decidir una sola numeración por resultado; corregir
    `prop:sp4-pose-stability` → `thm:`; citar los tres resultados del puente
    canónico desde RQ3.
12. F-11 · justificar o reclasificar las cotas $O(\cdot)$ que sostienen H5a.
13. F-12 bis · alinear `formal-spine-final-verdicts.csv` con las rutas de la v2,
    y añadir filas para los cuatro resultados del juego de integración.

---

## 7. Método y reproducción

- Censo: `final-hardening/census.json` (producido por
  `pre-thesis/scripts/census_formal_results.py`).
- Uso de cada resultado: búsqueda de `\ref{<etiqueta>}` restringida a los 89
  ficheros del cierre activo, no al repositorio.
- F-07: aritmética exacta con `fractions.Fraction` sobre la matriz $A$ y las
  restricciones $Hz\le g$ tal como se publican; se comprobaron $Az$,
  $\tfrac12z^{\mathsf T}z$, $0\le n_i\le30$ y $|t_i|\le0.4n_i$ para el vector
  publicado y para el corregido.
- F-15 (Bézier): reverificada la identidad
  $\|P_A-P_B\|^2=36z+A^2(1-z)^6$ con $z=(2s-1)^2$ y $b(s)=(1-z)^3$, y el signo
  de $36-6D^2(1-z)^5$ para $D\le\sqrt6$.
- F-09 (PoA): reverificado el contraejemplo, $\delta_{\min}=1/2$ y el umbral
  $\lambda_6=5M/2>2M$.

Ningún fichero de `pre-thesis/` ha sido modificado por esta auditoría.
