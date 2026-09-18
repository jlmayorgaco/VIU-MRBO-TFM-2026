# JCC_SEMANTIC_CROSSWALK — ¿es la campaña evidencia del juego de integración actual?

Fecha: 2026-09-18. Responde A1 y A1.1.

Compara, concepto a concepto, la formulación vigente de §6.5
(`pre-thesis/sections/v2/megajuego-compact.tex`) contra lo que
`src/viu_mrob_tfm/megajuego/` implementa y las ocho rejillas ejercitan.

El estado aumentado vigente es
$$Y=(X,\;d,\;\widehat X,\;\mathcal E_X,\;\mathcal I,\;\Pi^{\mathrm{inc}},\;\mathcal S,\;t).$$

---

## 1. Crosswalk

| # | concepto | JCC actual (§6.5) | campaña `results/megajuego/` | ¿equivalente? | diferencia | consecuencia científica | ¿sostiene la afirmación actual? |
|---|---|---|---|---|---|---|---|
| 1 | Estado aumentado | $Y$ de ocho componentes, Ec. (\ref{eq:megajuego-state}) | `Mechanism.__init__`: `z`, `phase`, `members`, `price`, `bel_cap`, `bel_mass`, `lease_*`, `plans`, `t_ctrl` + `Plant` | **sí**, componente a componente | el tiempo es `t_ctrl` con `ctrl_dt=0,02`; $\mathcal E_X$ es un escalar de error relativo, no un conjunto | el objeto implementado es el mismo | sí |
| 2 | Compromisos discretos $d$ | compromisos atómicos | `z_i \in \{\mathrm{idle}\}\cup\{(k,\text{modo},\text{puesto})\}` | **sí, exacto** | ninguna | — | sí |
| 3 | Planta de robots $X$ | uniciclo con límites | chasis $(x,y,\theta,v,\omega)$ **más dos ruedas con inercia** $J_w$, par, disco de fricción con registro de deslizamiento, batería | **la campaña es más rica** | §6.5 no modela rueda ni deslizamiento | la campaña puede sostener afirmaciones que §6.5 no; nunca al revés | sí, con margen |
| 4 | Planta de carga | cuerpo rígido planar | cuerpo rígido $(x,y,\theta,V,W)$ con huella rectangular, masa perturbada, inercia derivada | **sí** | ninguna relevante | — | sí |
| 5 | Contacto | contactos fijos conocidos | cargo: pad $f=k\varepsilon+du$, límite $\mu_{\text{top}}N_i$; caging: $f_n=k_b[\delta]_+$, $\lvert f_t\rvert\le\mu_bf_n$, unilateral | **sí**, y con unilateralidad explícita | §6.5 supone contacto fijo; la campaña lo simula | la campaña es más exigente | sí |
| 6 | Modelo rueda--suelo | ausente en §6.5 | tracción $F_s=\mathrm{clip}(c_g(r_w\omega_s-v_s),\text{disco})$, evento de deslizamiento | **solo en la campaña** | §6.5 no lo tiene | oportunidad, no conflicto | n/a |
| 7 | Acción/continuación $\gamma_i$ | política, contactos, trayectoria predicha | `z_i` + puesto + continuación `TrajPlayer` de $N$ nodos + comando + reparto de *wrench* + arrendamiento | **sí** | §6.5 no enumera las componentes; la campaña sí | — | sí |
| 8 | Potencial $\Phi$, coste $J_i$ | potencial exacto por factores, $J_i=\Phi(z)-\Phi(\mathrm{idle}_i,z_{-i})$ | `potential(z, viewer, ...)` y exactamente esa utilidad marginal | **sí, exacto** | ninguna | es la misma construcción | **sí** |
| 9 | Factores de acoplamiento $\psi_a$ | factores sobre bloques $\mathcal I_a$ | valor de coalición dependiente del conjunto de miembros; externalidad atómica por pares en `trajgame` | **sí** | — | — | sí |
| 10 | Seguridad | barrera, no certificada en conmutación | `safety` ∈ {`nested`, `coalition`, `none`}: barrera de coalición + barrera por AMR | **sí, y con ablación** | §6.5 no ablaciona | la campaña **añade** evidencia de ablación | sí |
| 11 | Reserva de tráfico $\mathcal S$ | reservas espacio--temporales | `lease_owner`/`lease_queue`/`lease_version` (exclusivo con orden total) o precio de congestión | **sí, y con ablación** | — | añade contraste lease/price | sí |
| 12 | Reclutamiento | cierre entero | `recruit` ∈ {`atomic`, `gne_pd`}: *shares* continuos con multiplicadores y atomización posterior | **sí** | §6.5 no contrasta las dos vías | añade contraste | sí |
| 13 | Recuperación | sustitución de miembro | fases `REC|FORM|TRANSPORT|DONE` y revisión continua | **parcial** | la campaña no inyecta fallo de miembro como factor | no sostiene por sí sola afirmaciones de recuperación | no |
| 14 | Re-certificación | admisión de continuación | `recertify` ∈ {True, False}, con `recert_reject` contado | **sí, y con ablación** | — | añade contraste | sí |
| 15 | Información local/global | $\mathcal I$ con procedencia | `n_hops=2`, `R_com=9,0` m, `comm_graph`, `nhop_sets`; **todo mensaje contado** | **sí** | la procedencia es visibilidad por saltos, no edad ni versión | la capa epistémica por diferencias **no** está implementada | sí para $n$-saltos; no para la capa delta |
| 16 | Error de creencia | $\widehat X,\mathcal E_X$ | `belief_err` ∈ {0,0; 0,35} sobre `bel_cap` y `bel_mass`, **por observador** | **sí** | error relativo uniforme, no covarianza | — | sí |
| 17 | Dinámica de revisión | mejora estricta sobre la vigente | reloj de Poisson `rev_rate=1,0`/s, histéresis `eps_sw=0,5`, permanencia `dwell=2,0` s, protocolo ∈ {BR, Smith, BNN, logit, replicator} | **sí** | §6.5 no fija el protocolo; la campaña lo ablaciona | añade contraste | sí |
| 18 | Planificador | continuación admisible | `planner` ∈ {`game`, `waypoint`} | **sí, y con ablación** | — | añade contraste | sí |
| 19 | Restricciones físicas | límites de actuación | $\tau_{\max}$, $v_{\max}$, $\omega_{\max}$, disco de fricción, $\mu_{\text{top}}$, $\mu_b$, penetración en pared | **la campaña es más estricta** | — | — | sí |
| 20 | Presupuesto de ejecución | $\kappa_WT+\delta N_{\mathrm{rev}}\le W_0$ | batería `E0=2·10⁵` J y `travel_cost` con término de energía; **no** hay contabilidad $\kappa_W$, $\delta$, $W_0$ | **no** | la campaña no instrumenta el presupuesto del teorema | **no puede sostener el teorema del presupuesto** | **no** |
| 21 | Criterio de parada | admisión de continuación | `T_max=300,0` s; `success` = ambas cargas entregadas | **sí** | — | — | sí |
| 22 | Objetivo social / oráculo | óptimo central de rama convexa | `oracle_assignment`: enumeración central con información verdadera, maximiza $\Phi$; `phi_oracle` por corrida | **parcial** | el oráculo es de asignación discreta, no el VI de la rama convexa | no sostiene el teorema del óptimo central | no |
| 23 | Métrica de éxito | entrega | `success` booleano, `n_done` ∈ {0,1,2} | **sí** | — | — | sí |
| 24 | Semántica de «entrega» | carga en pose destino | ambas cargas en destino dentro de `T_max` | **sí** | — | — | sí |
| 25 | Cargas simultáneas | 3 en el demostrador n=1 | **2** | **no** | escala distinta | no replica el escenario n=1 | no |
| 26 | Número de robots | 15 en el demostrador n=1 | **8** | **no** | escala distinta | no replica el escenario n=1 | no |
| 27 | Heterogeneidad de robots | declarada | masa $\mathcal U(19,36)$ kg, radio de rueda, par máximo, radio y capacidad derivada, **muestreados por robot** | **sí, y real** | — | sostiene heterogeneidad de flota | **sí** |
| 28 | Heterogeneidad de cargas | «cargas heterogéneas» | dos cargas de 60 y 95 kg nominales, $1{,}6\times1{,}1$ y $1{,}9\times1{,}3$ m, ambas $r_{\text{req}}=3$, **inercia derivada de la masa real**, masa perturbada $\times\mathcal U(0{,}9,1{,}1)$ | **sí, física** | mismo $r_{\text{req}}$ y mismo modo en ambas | **masa, inercia y geometría sí varían y entran en la planta**; el requisito de coalición no | parcialmente |

---

## 2. Clasificación

La clasificación no es única para toda la campaña: depende de qué afirmación se
quiera sostener. Forzar una sola etiqueta sería el error que este gate existe
para evitar.

### 2.1 Como arquitectura del mecanismo → **CLASE E1**

Misma arquitectura, versión anterior con diferencias **menores y mapeables**:

- el estado aumentado, los compromisos discretos, el potencial exacto con
  utilidad marginal, las reservas, la re-certificación, la información a
  $n$ saltos y las creencias por observador están implementados uno a uno;
- las diferencias son de **escala y mezcla de modos** ($N=8$ frente a 15,
  $K=2$ frente a 3, ambas cargas en *cargo* frente a dos *cargo* más una
  *caging*), y son explícitas y mapeables, no conceptuales.

Con E1, la campaña **puede ampliar** la evidencia empírica de §6.5 sobre el
mecanismo, declarando su configuración.

### 2.2 Por resultado formal

| resultado de §6.5 | clase | motivo |
|---|---|---|
| Potencial exacto por factores | **E1** | implementado literalmente ($J_i=\Phi(z)-\Phi(\mathrm{idle}_i,z_{-i})$) y ejercitado en las cinco variantes de protocolo |
| Óptimo central de rama convexa | **E2** | `gne_pd` implementa multiplicadores primal--dual sobre *shares* continuos, y el oráculo enumera; pero la equivalencia VI de la rama convexa no se mide |
| Separación exacta de Bézier | **E3** | la campaña usa continuaciones discretizadas de $N$ nodos con gradiente proyectado y externalidad atómica por pares; **no** es la familia analítica de Bézier |
| Presupuesto de ejecución | **E3** | no hay contabilidad de $\kappa_W$, $\delta$ ni $W_0$ |
| Certificado de *caging* con KKT racional | **E3** | el modo *caging* está implementado pero **con $K=2$ nunca se ejercita** en el factorial |

### 2.3 Consecuencia

**Solo las afirmaciones de mecanismo pueden apoyarse en esta campaña.** Los
cuatro resultados formales de §6.5 siguen sostenidos por su demostración y por
su verificación numérica propia, no por el factorial.

---

## 3. Comparación con el demostrador n=1 (A1.1)

| propiedad | §6.5 demostrador | campaña factorial |
|---|---|---|
| AMR | 15 | 8 |
| Cargas | 3 | 2 |
| Modos | dos *cargo* + una *caging* | dos *cargo* |
| Robots reclutados | 12 | variable (6 requeridos: 3+3) |
| Corridas | 1, determinista | 570, pareadas por mundo |
| Semillas | `np.random.seed(26)` | 0–29 |
| Caging | sí | **no** |

**La campaña no contiene el escenario n=1 parametrizado ni es su generalización
factorial.** Es otra configuración de la misma arquitectura. Decirlo de otro
modo sería el «rescate por parecido nominal» que este gate debe impedir.

### 3.1 Decisión

Se adopta la opción limpia que el propio encargo plantea:

**(a)** el demostrador n=1 **permanece** como *ejemplo determinista trabajado y
certificado*, con su etiqueta actual («corrida única, $n=1$, sin réplicas»), y
es el único que ejercita *caging* y tres cargas;

**(b)** la campaña factorial se añade como **campaña de robustez y sensibilidad
del mecanismo**, con su propia configuración declarada ($N=8$, $K=2$, ambas
cargas en *cargo*), sus 30 mundos y su estadística pareada.

No se borra el n=1. Cumple una función que la campaña no cubre.

---

## 4. Qué afirmaciones nuevas habilita — y cuáles no

**Habilita** (sujeto a que la regeneración cierre, véase
`MEGAGAME_CAMPAIGN_AUDIT.md` §3):

1. Contraste de protocolos de revisión sobre el potencial exacto, 5 celdas × 30 mundos.
2. **Ablación de seguridad** (`nested` / `coalition` / `none`), 3 × 20.
3. Aptitud vectorial frente a escalar, es decir **margen de *wrench* frente a suma de capacidades**, 2 × 30. Este es el contraste que sostiene directamente el argumento «C1 no implica C2».
4. Arrendamiento frente a precio de congestión en el paso, 2 × 20.
5. Reclutamiento atómico frente a GNE-PD, 2 × 20.
6. **Efecto del error de creencia y valor de la recertificación**, 4 × 20, y de nuevo bajo capacidad reducida, 4 × 20.
7. Planificador de juego frente a waypoint, 2 × 30.
8. Recuento de **certificados falsos** (`false_cert`) bajo cada condición.

**No habilita**:

- nada sobre *caging* (no ejercitado);
- nada sobre el presupuesto de ejecución (no instrumentado);
- nada sobre la separación de Bézier (otra familia de trayectorias);
- nada sobre recuperación ante fallo de miembro (no es factor);
- nada sobre la capa epistémica por diferencias (no implementada);
- nada sobre validez industrial, hardware ni tres cargas simultáneas.
