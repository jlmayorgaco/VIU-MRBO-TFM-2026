# Auditoría de subsistemas y planta — bloques 18, 19, 20 y 25

Criterio: `pre-thesis/guidelines/01-auditoria-maestra.md`, bloque 18 (SP1,
líneas 263–280), bloque 19 (SP2, 281–305), bloque 20 (SP3, 306–327) y bloque 25
(modelo físico y realismo robótico, 413–436). Se recorren sus viñetas una a una,
en su orden, y cada una recibe un veredicto con página, fichero, línea y texto
literal.

Artefacto: `pre-thesis/build-v2/main-v2.pdf` (146 páginas) y los 89 ficheros
compilados que censa `final-hardening/census.json`. SP1 es §6.2 (pp. 42–46),
SP2 es §6.3 (pp. 47–50), SP3 es §6.4 (pp. 51–53).

Convención de páginas: se cita **siempre el folio impreso**, que es el número de
página del PDF menos 17 (la página 1 del PDF es la portada; el folio 1 cae en la
página 42 del PDF). Los anexos van de A (p. 81) a J (p. 123–129).

No se ha editado ningún fichero de la memoria.

Veredictos: **RESPONDE** (la pregunta tiene respuesta explícita y localizable),
**PARCIAL** (hay respuesta, pero incompleta, mal situada o más débil de lo que
el texto circundante sugiere) y **NO RESPONDE** (no hay respuesta en el
documento activo; cuando la ausencia está declarada, se dice).

---

## 1. Resumen ejecutivo

| Bloque | Viñetas del criterio | RESPONDE | PARCIAL | NO RESPONDE |
|---|---:|---:|---:|---:|
| 18 — SP1 | 15 | 4 | 7 | 4 |
| 19 — SP2 | 22 | 9 | 11 | 2 |
| 20 — SP3 | 19 | 12 | 3 | 4 |
| 25 — planta | 21 | 4 | 9 | 8 |
| **Total** | **77** | **29** | **30** | **18** |

Las dieciocho preguntas sin respuesta son:

- **SP1** (4): escasez; QR; cuórum; diferencia entre la relajación y la solución
  entera.
- **SP2** (2): fricción (omitida, y declarada como omitida); CBF/HOCBF, que no
  tiene formalismo en ningún punto del documento activo.
- **SP3** (4): interpolación continua; escala E8; red degradada en tráfico;
  calidad a $A=64$.
- **Planta** (8): radio de rueda del robot modelado; *wheelbase*; inercia;
  tracción; *slip*; sensores; percepción (declarada); error de odometría. A
  estas se añade, como hallazgo transversal y no como viñeta, la cadena que
  enlazaría el par de rueda con la fuerza de contacto que el certificado de
  *wrench* asigna.

El hallazgo más serio no es una ausencia aislada sino una **supresión**: la
versión v1 de la memoria contenía una observación titulada «Lo que el
certificado no certifica» que enumeraba las cuatro fronteras físicas del
certificado de E3 —conos de fricción, dinámica, restricción no holónoma y
mantenimiento del contacto—, y la v2 no la compila. Ficha S-01.

El segundo es una **contradicción de contrato**: la ecuación (8) de la p. 34 y
la Tabla 22 de la p. 60 presentan `SUPPORT` y `WHEELS` como predicados
verificados de la autorización de movimiento, y §7.5 (p. 65) declara que el
modelo «omite soporte vertical … y tracción rueda–suelo». Ficha S-02.

---

## 2. Bloque 18 — SP1, formación de coaliciones

### 2.1 Tabla ítem a ítem

| # | Pregunta | Veredicto | Dónde |
|---|---|---|---|
| 1 | E1 / cuotas | PARCIAL | Teorema 6.1, p. 42–43; prueba G.1, p. 95 |
| 2 | E2 / servicio heterogéneo | RESPONDE | Ec. (10), p. 43; Anexo G.2, pp. 96–101 |
| 3 | E3 / contactos y *wrench* | PARCIAL | Ec. (11)–(12), p. 45; Anexo B.3, p. 82 |
| 4 | Exactitud del potencial | PARCIAL | p. 42 (E1); Ec. (27), p. 81 (E2) |
| 5 | Penalización suficiente | PARCIAL | p. 42, p. 49, p. 51, p. 109 |
| 6 | Escasez | NO RESPONDE | p. 6 lo promete; p. 65 lo retira |
| 7 | QR | NO RESPONDE | H1b «No adjudicada», p. 65 |
| 8 | Cuórum | NO RESPONDE | H1c «No adjudicada», p. 65 |
| 9 | Integrabilidad del pago marginal | RESPONDE | Prop. 6.1, p. 43; Anexo B.2, p. 81 |
| 10 | Cierre entero | PARCIAL (declarado abierto) | p. 45, p. 81, Tabla 9, p. 44 |
| 11 | Diferencia relajación / solución entera | NO RESPONDE | — |
| 12 | Dependencias globales | RESPONDE | Tabla 3, p. 16; p. 99 |
| 13 | Heterogeneidad realmente modelada | PARCIAL | Ec. (10), p. 43; p. 96 |
| 14 | Correspondencia teoría ↔ código | PARCIAL | p. 99, p. 100, Anexo A, p. 81 |
| 15 | Comparadores correctos | RESPONDE | Tabla 9, p. 44; p. 44 |

### 2.2 Desarrollo

**1. E1 / cuotas.** El Teorema 6.1 (p. 42) es completo y su hipótesis está
escrita: «si $\sum_k n_k \le N$ y $\lambda > \kappa_{\max}$». La cota se
cualifica en la línea siguiente (p. 43): «La cota cuenta cambios estratégicos
aceptados, no segundos ni rondas globales». La demostración ocupa el Anexo G.1
(p. 95). Es PARCIAL por un motivo de encaje, no de matemática: la metodología
declara en `04-methodology.tex:405` (p. 16) que «El capítulo de resultados
activa E2, E3, E4, E6, E7 y Cargo; E0, **E1**, E5 y E8 permanecen como
procedencia y material de monografía, no como evidencia de una conclusión VIU»,
mientras la Figura 18 (p. 42) presenta E1 como la primera de «tres etapas
encadenadas» de SP1 y §6.2 no tiene ninguna tabla de resultados de E1. El lector
de §6.2 ve un cauce de tres etapas del que la primera no tiene campaña y la
metodología, treinta páginas antes, la ha desactivado.

**2. E2 / servicio heterogéneo.** Respondido con precisión. La Ec. (10)
(p. 43) define $\psi_i^b$, $\psi_{ik}^d$, $e_{ik}$ y $S_k$, y el Anexo G.2
(p. 96) delimita su interpretación: «El factor $a_{ik}$ representa
disponibilidad y $e_{ik}$ expresa servicio normalizado, **no masa**»
(`sp1-e2-trimmed.tex:35`). El mismo párrafo declara que «Los experimentos
suponen compatibilidad unitaria y omiten restricciones independientes de soporte
y balance energético».

**3. E3 / contactos y *wrench*.** El QP está escrito (Ec. 11, p. 45) y la
Proposición 6.2 lo acota correctamente. Es PARCIAL porque **ni $G_k$ ni
$\Lambda_{ik}$ se construyen en ningún punto del documento activo**. El
enunciado se limita a «el producto de conjuntos de contacto
$\Lambda_k=\prod_{i\in C_k}\Lambda_{ik}$ cerrado, convexo y no vacío»
(`sections/sp1-wrench-condensed.tex:11-12`, p. 44). La nomenclatura (p. xiii,
`04-nomenclature.tex:42`) registra «$G_C(q),\boldsymbol\lambda_C$ — Matriz de
agarre y esfuerzos de contacto de la coalición $C$» y no da columnas, brazos ni
unidades; $\Lambda_{ik}$ y $\mathcal U_C$ no figuran en la nomenclatura.
Consecuencia inmediata: un certificado cuyo conjunto admisible puede ser
$\mathbb R^n$ —y de hecho el contraejemplo del Anexo B.3 (p. 82) usa
«$\Lambda_k=\mathbb R$»— no distingue empujar de tirar, ni fuerza normal de
tangencial. Véase la ficha S-01.

**4. Exactitud del potencial.** Para E1 es exacta y demostrada (p. 95). Para E2
la identidad $\partial\Phi/\partial\rho_{ik}=f_{ik}^{\mathrm{marg}}$ se
demuestra en el Anexo B.2 (p. 81), pero **el potencial $\Phi$ no aparece en el
cuerpo**: la Proposición 6.1 (p. 43) dice que la puntuación marginal «es el
gradiente exacto de un potencial escalar» sin exhibirlo. El potencial es la
Ec. (27) del Anexo G.2 (p. 81–82). El defecto de colocación ya está fichado como
F-10 en `04-matematica.md`; se registra aquí porque el ítem del bloque 18 lo
pregunta directamente.

**5. Penalización suficiente.** Los tres umbrales del TFM tienen naturalezas
distintas y el documento no las compara:

- $\lambda>\kappa_{\max}$ (E1, p. 42) — comprobable *a priori* con datos locales.
- $\lambda_6>\kappa^6_{\max}/\delta_{\min}$ (Teorema 6.4, p. 49) — el Anexo H.2
  admite que «Calibrar $\lambda_6$ exactamente usa la instancia completa fuera de
  línea» (p. 109, `sp2-e6-trimmed.tex:52`), es decir, el umbral suficiente **no
  es localmente computable**.
- $\lambda_7>\theta_7$ (Prop. 6.5, p. 51) — nunca se calculó; véase el ítem 12
  del bloque 20.

El cuerpo no reúne estas tres cláusulas en ningún sitio, de modo que el tribunal
no ve que la «penalización suficiente» significa tres cosas distintas según la
etapa.

**6. Escasez. NO RESPONDE.** El Teorema 6.1 asume $\sum_k n_k\le N$, es decir,
abundancia por hipótesis. Los objetivos prometen otra cosa (p. 6,
`02-objectives.tex:29`): «brecha respecto de la referencia global en abundancia
**y escasez**». La conclusión cierra el asunto por afirmación, no por evidencia
(p. 64, `07-conclusions-v2.tex:67`): «la escasez exige selección todo-o-nada. El
contraste específico de QR queda fuera del cuerpo activo». No hay ninguna
campaña, ningún dato y ningún resultado formal sobre escasez en el documento
activo.

**7 y 8. QR y cuórum. NO RESPONDEN.** QR se define en la nomenclatura (p. xiv,
`04-nomenclature.tex:67`, «Cierre entero por ordenamiento y cuórum») y aparece
en las hipótesis H1b y H1c (p. 8–9). La Tabla 24 (p. 65) las cierra: «H1b — No
adjudicada — El contraste QR–Smith se conserva fuera del cuerpo activo» y «H1c —
No adjudicada — El contraste cuórum–lineal se conserva fuera del cuerpo activo».
La declaración es honesta, pero dos de las tres hipótesis del SP1 no se
adjudican y el mecanismo de cierre entero que la Tabla 3 (p. 16) atribuye a E1
(«QR global») nunca se ejecuta en la memoria.

**9. Integrabilidad del pago marginal. RESPONDE.** El Anexo B.2 (p. 81) hace el
cálculo completo, incluida la falla del campo plano: «Si $e_{ik}\ne e_{jk}$,
estas expresiones difieren y violan la condición de simetría necesaria para que
el campo plano sea el gradiente de un potencial escalar dos veces diferenciable
en esa región». La frontera saturada se trata por continuidad (p. 82).

**10. Cierre entero.** El documento declara reiteradamente que el cierre entero
queda fuera de lo demostrado: p. 45, «sin transferirlos al cierre entero ni a
Euler muestreado» (`sp1-wrench-condensed.tex:43`); Tabla 9, p. 44, fila
primal–dual: «cierre entero heurístico; sin certificado de la solución entera»;
Anexo B.1, p. 81: «El cierre entero, la mecánica y la ejecución vecinal
discretizada se tratan mediante resultados independientes». Esa última frase es
la que no se cumple: **no existe en el documento ningún resultado independiente
sobre el cierre entero**. Es una promesa de reenvío a la nada.

**11. Diferencia relajación / solución entera. NO RESPONDE.** No hay ninguna
cifra, cota ni contraejemplo que mida cuánto pierde la solución entera respecto
del óptimo de la relajación continua cuyo potencial se demuestra en la
Proposición 6.1. El marco teórico enuncia el riesgo (p. 22,
`05-theoretical-framework.tex:195`: «Una proyección o un redondeo puede cambiar
el potencial de la relajación y crear déficit») y ahí se detiene.

**12. Dependencias globales. RESPONDE**, y bien: la Tabla 3 (p. 16,
`tab:results-model-map`) da, etapa por etapa, decisión, agregado, cierre,
certificación y planta —E2 usa «déficit global salvo la ablación primal–dual»,
E3 «QP de *wrench* central», Cargo «atributos resueltos en registro global»— y
la p. 16 concluye: «Estas dependencias hacen híbrida la arquitectura». La única
objeción es de colocación: dentro de §6.2 (pp. 42–46) la dependencia del
déficit global de E2 **no se menciona**; aparece en el Anexo G.2 (p. 99,
`sp1-e2-trimmed.tex:117`): «En la campaña, las reglas recibieron el déficit
global salvo la variante primal–dual de radio limitado».

**13. Heterogeneidad realmente modelada. PARCIAL.** Se modelan carga útil,
batería y distancia inicial, combinadas en un escalar $e_{ik}$ (Ec. 10, p. 43).
No se modela heterogeneidad de ruedas, de par disponible, de huella, de radio de
contacto ni de brazo de palanca. El propio texto lo dice donde corresponde
(p. 101, `sp1-e2-trimmed.tex:192`): «El índice mezcla disponibilidad y distancia
sin un modelo mecánico, de modo que una asignación operacionalmente cubierta
puede ser físicamente inviable».

**14. Correspondencia entre teoría y código. PARCIAL, con una brecha declarada
y otra no.** La declarada, p. 99 (`sp1-e2-trimmed.tex:117`): «las variantes
Smith se implementaron como ordenaciones secuenciales y no como integraciones de
la EDO»; y p. 100: «La ausencia del generador de instancias impide repetir la
creación de mundos y limita la reproducibilidad de la simulación». La no
declarada es que el **Anexo A, «Reproducibilidad y disponibilidad» (p. 81), es
un único párrafo sin repositorio, sin DOI, sin *hash* y sin listado**: dice que
«el banco Cargo nuevo registra configuración, semilla, entorno y *hashes* por
ejecución» sin indicar dónde puede consultarlos un tribunal. Los únicos punteros
a código del documento activo son nombres de *script* sueltos
(`run_sp4_v4_coppelia_paired_scene.py`, p. 59; `simulate_e2e_megagame.py`,
p. 57–58) y una ruta interna (`pre-thesis/resources/MROB_MegaGame_E2E_bundle/`,
p. 58).

**15. Comparadores correctos. RESPONDE.** La Tabla 9 (p. 44) declara la
inaplicabilidad de cada garantía importada: «Húngaro expandido — exacto para el
LAP expandido; capacidad aproximada», «CBBA-capacidad — garantía CBBA original
inaplicable», «Replicator/BNN/Smith — garantías de la EDO fuera de esta
implementación». Y el resultado adverso se publica sin suavizar (p. 44): la
regla propia «sigue por debajo de la red neuronal no certificada (0.263) y del
oráculo MILP (0.487)» frente a su 0.135 de completitud.

---

## 3. Bloque 19 — SP2, transporte

### 3.1 Tabla ítem a ítem

| # | Pregunta | Veredicto | Dónde |
|---|---|---|---|
| 1 | Modelo de uniciclo | RESPONDE | Ec. (1) y Figura 3, pp. 11–12 |
| 2 | Modelo de ruedas | PARCIAL | Ec. (21), Anexo C.1, p. 82 |
| 3 | Dinámica de carga | PARCIAL | Ec. (15), p. 47 |
| 4 | Contactos | PARCIAL | p. 12, p. 47, p. 103 |
| 5 | Bilateralidad | PARCIAL (con tensión interna) | Ec. (15) y Teorema 6.2, pp. 47–48 |
| 6 | Fricción | NO RESPONDE (declarado) | Prop. C.3, p. 83; §7.5, p. 65 |
| 7 | Saturaciones | PARCIAL | Ec. (15), p. 47; pp. 105, 114 |
| 8 | Matriz de agarre | PARCIAL | Ec. (7), p. 23 |
| 9 | *Wrench* | RESPONDE | Ec. (2), p. 12; Ec. (11), p. 45 |
| 10 | Transformación rueda–*twist* | RESPONDE | Ec. (21) y Prop. C.1, p. 82 |
| 11 | No-holonomía | PARCIAL | dentro de una demostración, pp. 82–83 |
| 12 | Servo PD | RESPONDE | Ec. (15), p. 47 |
| 13 | Lyapunov | RESPONDE | Teorema 6.2, p. 48; Anexo C.4, p. 85 |
| 14 | Dominio local | PARCIAL | cuerpo p. 48 vs. anexos pp. 85 y 105 |
| 15 | LaSalle | PARCIAL | p. 48 (cuerpo) vs. p. 85 (anexo) |
| 16 | Realización exacta / no exacta | RESPONDE | Anexo C.4, p. 85; Anexo H.1, p. 105 |
| 17 | *Safety* vs. *progress* | RESPONDE | Tabla 13, p. 48 |
| 18 | CBF / HOCBF | NO RESPONDE | — |
| 19 | Saturación posterior | PARCIAL | p. 24; pp. 105, 114 |
| 20 | Recuperación | RESPONDE | Teoremas 6.3–6.4, pp. 48–49 |
| 21 | Tiempo de llegada del reemplazo | PARCIAL | Corolario H.1, p. 110 |
| 22 | Falta de contacto físico real | RESPONDE | p. 103; p. 47; p. 60 |

### 3.2 Desarrollo

**1. Uniciclo.** Ec. (1), p. 11: $\dot q_i=[v_i\cos\theta_i\ \ v_i\sin\theta_i\
\ \omega_i]^\top$, con entradas acotadas $(v_i,\omega_i)$; la Figura 3 (p. 12)
explicita el punto adelantado $h_i$ y advierte que «no añade un estado físico».
La versión dinámica, con aceleraciones $\eta_i=(\eta_i^v,\eta_i^\omega)$ y su
conjunto de actuación $\mathcal U_i$, está en el Anexo H.1 (Ec. 33, p. 104).

**2. Modelo de ruedas. PARCIAL.** Existe —y es correcto— pero vive solo en el
Anexo C.1 (p. 82): «Con radio $r_i^w>0$, semivía $\ell_i^w>0$ y límite
$\bar\omega_{w,i}$, la cinemática rígida exige … $\dot\varphi_{i,L/R}=(v_{i,\|}
\mp\ell_i^w\dot\theta_i)/r_i^w$» (`sp2-canonical-bridge.tex:6-13`). Tres
carencias: $r_i^w$ y $\ell_i^w$ **no reciben valor numérico en ninguna campaña
de SP2**; no hay dinámica de rueda (inercia, par, deslizamiento); y §6.3, donde
el lector encuentra el transporte, no reproduce ni cita esta ecuación salvo por
la frase de apertura «El Anexo C.1 prueba la equivalencia entre *twist* de la
carga y ruedas» (p. 47).

**3. Dinámica de carga. PARCIAL.** Ec. (15), p. 47:
$M_k\ddot q_k^L+D_k\dot q_k^L=G_{C_k}\boldsymbol\lambda_k^\star$, con
$M_k,D_k\succ0$. **No se da ningún valor de masa ni de inercia para ninguna
carga de SP2**; $M_k$ es una matriz abstracta constante. La única carga con masa
declarada en todo el documento activo es la del Anexo J.1 (p. 125): «Cada carga
tiene 40 kg y cuatro *pads* simétricos en $(\pm0.45,\pm0.45)$ m», que pertenece
al juego de integración, no a SP2. Un revisor no puede comprobar si las
ganancias $K_P,K_D$ del servo son físicamente razonables porque no sabe qué masa
mueven.

**4. Contactos. PARCIAL.** Se declaran fijos en todos los enunciados y en la
metodología (p. 12: «El modelo supone contactos fijos, límites de actuación y
dinámica planar reducida»). Lo que falta es qué *es* un contacto: no hay
geometría de puesto, ni normal, ni brazo, ni conjunto admisible.

**5. Bilateralidad. PARCIAL, y con una tensión interna sin resolver.** La
Ec. (15) de la p. 47 restringe el reparto a
$\boldsymbol\lambda_k^\star\in\arg\min_{0\le\lambda\le\bar\lambda}$, es decir, a
una caja **no negativa**; el Teorema 6.2, doce líneas más abajo (p. 48) y su
`\estadoaporte` (p. 47), se enuncia «para contactos **bilaterales** fijos». Una
caja $0\le\lambda\le\bar\lambda$ es la forma canónica de un contacto unilateral
en la coordenada de empuje. El documento no aclara si $\lambda$ agrupa
componentes con signo por dirección (en cuyo caso la caja sí admite tracción) o
si hay una incoherencia entre la ecuación y la hipótesis del teorema. La
memoria distingue correctamente ambos regímenes en otros lugares —p. 11: «La
extensión *caging* se limita a su definición geométrica y a contactos
unilaterales»; p. 24: «En empuje, $\mathcal U_C$ incorpora unilateralidad y
fricción»— lo que hace más visible que aquí no lo haga.

**6. Fricción. NO RESPONDE, y está declarado.** SP2 no modela fricción. La
Proposición C.3 (p. 83) lo enuncia por la vía negativa —«$\sum_i\bar t_i\ge
\|F_d\|$ es necesario, pero no suficiente para realizar $(F_d,\tau_d)$ ni para
certificar soporte o fricción»— y su demostración añade: «omitir soporte o
fricción solo relaja la factibilidad». §7.5 (p. 65) cierra: el modelo «omite
soporte vertical, fricción 3D, deslizamiento, percepción y tracción
rueda–suelo». La única fricción efectivamente modelada en todo el documento es
la adherencia tangencial planar del bloque de *caging* del Anexo J.3 (p. 126):
«$|t_i|\le0.4n_i$ … Con adherencia tangencial de Coulomb se resuelve …».

**7. Saturaciones. PARCIAL.** En el cuerpo solo existe la caja
$0\le\lambda\le\bar\lambda$ de la Ec. (15) (p. 47). Los límites de actuación del
robot, la saturación de par y la comprobación de la barrera contra la
aceleración realmente aplicable están en los anexos: p. 102, «El primer estrato
integra uniciclos dinámicos con límites de par»; p. 105, «comprobación de la
barrera con la aceleración finalmente realizable»; p. 114, «Aproximación y
reemplazo integran uniciclos con pares saturados». El dato más relevante para un
tribunal —que el banco no llegó a saturar— también vive en anexo (p. 107): «No
hubo violaciones de barrera en la acción aplicada ni saturaciones de par. El
conjunto es demasiado pequeño para someter los actuadores a su régimen límite».

**8. Matriz de agarre. PARCIAL.** Se nombra en §5.3 (p. 23, Ec. 7): «Si
$\boldsymbol\lambda_C$ agrupa esfuerzos de contacto y $G_C(q)$ es la matriz de
agarre, el *wrench* aplicado es $W_C=G_C(q)\boldsymbol\lambda_C$». La discusión
que sigue es correcta y pertinente —«Como $G_C$ y $\mathcal U_C$ dependen de la
configuración, el margen de torque puede cambiar al rotar la carga o recolocar
un contacto» (p. 23)— pero **$G_C$ no se construye jamás**: ni sus columnas, ni
los brazos $r_i$, ni la normalización fuerza/torque. Es el mismo hueco del ítem
3 del bloque 18.

**10 y 11. Rueda–*twist* y no-holonomía.** La Proposición C.1 (p. 82) es el
puente y es correcta: «la coalición reproduce $\xi_L$ si y solo si cada eje
longitudinal es paralelo o antiparalelo a $v_i^{\mathrm{piv}}$, la velocidad
lateral es nula y (21) respeta los límites de rueda». La no-holonomía aparece
**una sola vez en las 146 páginas**, y dentro de esa demostración (p. 82–83):
«la restricción no holónoma y el diferencial de ruedas dan la segunda». No se
escribe la restricción ($-\dot x\sin\theta+\dot y\cos\theta=0$), no figura en la
nomenclatura y no se conecta con la generación de fuerza. Véase la ficha S-01.

**14 y 15. Dominio local y LaSalle.** El Teorema 6.2 del cuerpo (p. 48)
concluye «estabilidad asintótica local» invocando LaSalle «sobre el conjunto
$\dot V=0$», sin nombrar conjunto compacto positivamente invariante y **sin la
carta de $SE(2)$**, que sí está en las dos versiones de anexo (Anexo C.4, p. 85:
«En una carta local de $SE(2)$, $\dot e_k^L=\dot q_k^L$»; Teorema H.1, p. 105:
«error angular dentro de una carta de $SE(2)$»). Ya fichado como F-06 en
`04-matematica.md`; se confirma aquí desde el ángulo del bloque 19, donde
«dominio local» y «LaSalle» son ítems separados y ambos quedan peor en el cuerpo
que en el anexo.

**17. *Safety* vs. *progress*. RESPONDE, y es uno de los mejores resultados del
capítulo.** La Tabla 13 (p. 48) separa las dos cosas con datos: «Proyección CBF
— colisión 0.000 — horizonte agotado 0.824». El texto lo lee correctamente
(p. 106): «La tasa de *timeout* identifica el fallo de vivacidad aun cuando se
satisface la barrera».

**18. CBF / HOCBF. NO RESPONDE.** El documento activo usa HOCBF como etiqueta de
método en cinco lugares —la entrada de nomenclatura (p. xiv), la Tabla 3
(p. 16), §4.10 (p. 18), la Tabla 12 (p. 48) y la Tabla 21 con su discusión
(p. 59)— y **en ninguno define la función de barrera, la clase $\mathcal K$, el
grado relativo ni el QP de filtrado**. Lo más próximo es la prosa del
§5.4 (p. 24): «Una CBF define un conjunto seguro y una condición de invariancia
hacia delante. El filtro CBF-QP proyecta el control nominal sobre las
desigualdades admisibles bajo el modelo, el grado relativo y el estado
declarados». Ni «el modelo», ni «el grado relativo», ni «el estado declarado»
se instancian después. La etapa E5, que era la que llevaba la formulación de
seguridad, está desactivada por la metodología (p. 16: «E0, E1, E5 y E8
permanecen como procedencia»). El resultado es que la fila «Juego PD/replicator
+ HOCBF (TFM)» de la Tabla 12 y las 2 violaciones de barrera del piloto AWS
(p. 53) se refieren a un objeto matemático que la memoria no define.

**21. Tiempo de llegada del reemplazo. PARCIAL.** El Corolario H.1 (p. 110) da
$T_{\mathrm{rec}}\le\bar\tau_d+2^{n_R}\bar\tau_a+\max_i \ell_i/v_i^{\min}+\tau_s$
y declara sus dos debilidades: «El término $\ell_i/v_i^{\min}$ aproxima el viaje
por un segmento libre y omite el giro y la evitación» (p. 111). Lo que no
declara es que el factor $2^{n_R}$ vuelve la cota operativamente vacía. Falta
además contraparte en el cuerpo: §6.3 no menciona ninguna cota temporal de
recuperación, pese a que la Tabla 15 (p. 49) publica «Éxito temporal» como
métrica.

**Ítems 9, 12, 13, 16, 19 y 20, en breve.** *Wrench* (9): Ec. (2), p. 12, y
Ec. (11), p. 45, ambas con su residual normalizado y su tolerancia $\epsilon_W$.
Servo PD (12): Ec. (15), p. 47, «$W_k^d=-K_Pe_k^L-K_D\dot q_k^L$ la referencia
de *wrench*»; no se dan valores de $K_P$ ni $K_D$ en ninguna campaña.
Lyapunov (13): Teorema 6.2, p. 48, «$V=\frac12\dot q^{L\top}M_k\dot
q^L+\frac12e_k^{L\top}K_Pe_k^L$», con la derivada completa en el Anexo C.4,
p. 85: «$\dot V=-\dot q_k^{L\top}(D_k+K_D)\dot q_k^L+\dot q_k^{L\top}\boldsymbol
r_k^W$». Realización exacta / no exacta (16): las dos ramas están separadas y la
inexacta se cierra bien (p. 85), «Cuando el residual persiste, el término
$\|\widetilde{\boldsymbol r}_k^W\|_2^2/(2\lambda_D)$ impide deducir convergencia
exacta a partir de esta desigualdad». Saturación posterior (19): §5.4, p. 24,
«La saturación o el reparto de *wrench* pueden separar la acción ejecutada de la
orden nominal y de la salida del filtro», principio correcto que solo se
instrumenta en anexo (p. 105). Recuperación (20): Teoremas 6.3 y 6.4 y
Proposición 6.4, pp. 48–49, con la caracterización exacta de los Nash y
$\operatorname{PoA}_6=+\infty$; la campaña está en la Tabla 15, p. 49.

**22. Falta de contacto físico real. RESPONDE**, y en varios registros: p. 103
(`sp2-e4-trimmed.tex:6`), «La campaña aporta evidencia para cada fase por
separado, no para su composición extremo a extremo, y prescinde de una
simulación física del contacto»; p. 114, sobre Cargo, «Ninguno verifica
orientación, contacto ni colisiones de aproximación. Después, la carga planar
fija las poses por desplazamientos rígidos»; p. 59, sobre CoppeliaSim, «La
reproducción comprueba geometría y reejecución de la trayectoria comandada, no
física independiente ni hardware».

---

## 4. Bloque 20 — SP3, planificación y tráfico

### 4.1 Tabla ítem a ítem

| # | Pregunta | Veredicto | Dónde |
|---|---|---|---|
| 1 | Definición de ruta | PARCIAL | p. 51; tamaño del catálogo solo en p. 118 |
| 2 | Catálogo finito | RESPONDE | Teorema 6.5, p. 51; p. 118 |
| 3 | Potencial exacto | RESPONDE | Teorema 6.5, p. 51; Anexo E.2, p. 87 |
| 4 | Penalización de congestión | RESPONDE | Ec. (17), p. 51; Tabla 18, p. 52 |
| 5 | Reservas | RESPONDE | Algoritmo 3, pp. 119–120 |
| 6 | Testigo | RESPONDE | Algoritmo 3, p. 119; p. 120 |
| 7 | Exclusión mutua | PARCIAL | Anexo E.4, p. 88 (prosa, sin enunciado) |
| 8 | Inanición | RESPONDE | Prop. 6.6, p. 51; Anexo E.5, p. 88 |
| 9 | *Deadlock* | RESPONDE (solo empírico) | Tabla 18, p. 52; p. 120 |
| 10 | *Liveness* | PARCIAL | p. 120 |
| 11 | Condición $\lambda_7>\theta_7$ | RESPONDE | Prop. 6.5, p. 51; Ec. (50), p. 119 |
| 12 | ¿Premisa o solo conclusión? | RESPONDE | p. 51 |
| 13 | Huella extendida | RESPONDE | p. 121; Tabla 19, p. 53 |
| 14 | Tiempo discreto | RESPONDE | p. 119 |
| 15 | Interpolación continua | NO RESPONDE | p. 88 la nombra y no la define |
| 16 | MAPF vs. control continuo | RESPONDE | Tabla 17, p. 52; p. 118 |
| 17 | Escala E8 | NO RESPONDE (declarado) | p. 122; p. 26 |
| 18 | Red degradada | NO RESPONDE en SP3 (declarado) | p. 122 |
| 19 | Calidad a $A=64$ | NO RESPONDE | — |

### 4.2 Desarrollo

**1 y 2. Ruta y catálogo.** El cuerpo define $r_i\in\mathcal R_i^7$ (p. 51) y el
Teorema 6.5 acota la terminación por $\prod_i|\mathcal R_i^7|-1$. **El tamaño
del catálogo no está en el cuerpo**: aparece en el Anexo I.1 (p. 118), «Con
$|\mathcal R_i^7|=2$, la enumeración de $2^AA!\le384$ combinaciones certifica el
óptimo dentro del catálogo restringido», y en el diseño experimental (p. 121):
«ruta directa y desvío por coalición». Un lector de §6.4 ve una cota
exponencial en un catálogo cuyo cardinal es dos.

**7. Exclusión mutua. PARCIAL.** El Anexo E.4 (p. 88) se titula «Invariante
lógico de la reserva» y consta de cuatro líneas de prosa: «Desde una zona libre,
el arbitraje asigna un propietario único y conserva el testigo hasta observar su
salida y el despeje … por inducción, dos entradas incompatibles nunca quedan
autorizadas y los nodos activos permanecen distintos»
(`08-sp7-proofs.tex:24`). **No hay enunciado formal**: ni proposición, ni
invariante escrito, ni hipótesis. La propiedad que sostiene toda la contribución
de reserva de SP3 es la única del capítulo que no tiene entorno formal. El
cuerpo (§6.4) no la menciona.

**9 y 10. *Deadlock* y *liveness*.** El interbloqueo se mide, no se demuestra:
Tabla 18 (p. 52) da «Sin reserva de zona — Interbloqueo 0.261», y el criterio
operativo está en p. 120: «ocho pasos consecutivos sin movimiento definen un
bloqueo». La vivacidad global queda expresamente fuera (p. 120): «La completitud
del problema completo depende además del horizonte y de la interacción entre
zonas». Es PARCIAL por defecto de alcance declarado, no por ocultación.

**12. ¿Se verificó la premisa o solo la conclusión? RESPONDE, y es la respuesta
más honesta del capítulo 6.** La propia Proposición 6.5 lo dice en su
enunciado (p. 51): «esta accesibilidad se infiere empíricamente de observar
$P_7=0$ en los cruces y su fallo en el pasillo, **no de calcular $\theta_7$ y
$\lambda_7$ por separado y comprobar el margen antes del experimento**, y ahí el
testigo temporal es necesario». El Anexo I.1 lo repite (p. 119): «La
accesibilidad exigida por la Proposición … se cumplió en los cruces y falló en
el pasillo y el cuello».

**13. Huella extendida. RESPONDE**, con el dato geométrico en el anexo (p. 121):
«Radios 0.52–0.68 m sobre celdas de 1 m, **sin orientaciones intermedias**». La
segunda mitad de esa frase es importante y no se repite en el cuerpo: el modelo
no rota la huella entre celdas, de modo que una coalición alargada que gire no
está representada.

**15. Interpolación continua. NO RESPONDE.** El Anexo E.4 (p. 88) cierra con
«La separación entre muestras requiere que inflación e interpolación respeten la
huella; la ejecución física añade una guardia como la de E5». Esa es la única
aparición de «interpolación» en el documento activo. No hay interpolador
definido, no hay cota de separación entre muestras y la guardia de E5 pertenece
a una etapa desactivada (p. 16). La Tabla 19 (p. 53) traslada la
responsabilidad a un chequeo verbal —«Geometría — huellas infladas disjuntas en
el intervalo»— sin decir cómo se comprueba «en el intervalo» a partir de
muestras.

**Ítems 3, 4, 5, 6, 8, 11, 14 y 16, en breve.** Potencial exacto (3): Ec. (17),
p. 51, y prueba en el Anexo E.2, p. 87, con la identidad
$\binom{m+1}{2}-\binom m2=m$ y una salvedad que conviene retener, «pero una
trayectoria truncada no hereda la conclusión». Penalización de congestión (4):
el término $-\lambda_7\sum_e(n_e(\boldsymbol r)-1)$ de la Ec. (17), p. 51, y su
ablación en la Tabla 18, p. 52 («Sin penalización de congestión — Terminación
11.49» frente a 7.49 del método completo). Reservas y testigo (5, 6): Algoritmo
3, pp. 119–120, con la terna lexicográfica $(w_i,P_i,-i)$ y el envejecimiento
$w_i\gets w_i+1$; la liberación se declara hipótesis explícita (p. 120), «La
liberación del testigo tras el paso de despeje es exactamente la hipótesis que
la Proposición … necesita». Inanición (8): Proposición 6.6, p. 51, y Anexo E.5,
p. 88; el cuerpo pierde el «uniformemente acotado» del anexo, ya fichado como
F-12 en `04-matematica.md`. Condición $\lambda_7>\theta_7$ (11): Ec. (50),
p. 119. Tiempo discreto (14): p. 119, «El simulador usa paso digital unitario,
horizonte 48 y actualización simultánea de posiciones aceptadas». MAPF frente a
control continuo (16): Tabla 17, p. 52, «CBS/ECBS/LA-MAPF … garantías MAPF bajo
sus modelos; **no incluidas en el comparativo numérico**» y «ORCA … evitación
continua bajo su modelo; no planifica ni excluye interbloqueo»; y p. 118, «MAPF
con un conjunto general de rutas constituye un problema distinto».

**17, 18 y 19. E8, red degradada y $A=64$. NO RESPONDEN.** El documento lo
declara dos veces: p. 26 (`05-theoretical-framework.tex:236`), «La campaña
histórica E8, conservada en la monografía y no usada como evidencia VIU activa,
relaciona conectividad y edad de copia con calidad operacional y carga
comunicativa»; y p. 122 (`sp3-e7-trimmed.tex:177`), «E8 reutiliza ese juego y
degrada las vistas con escala, retardo y pérdida, pero se conserva como campaña
histórica en la monografía y no sustenta conclusiones VIU». La Tabla 24 (p. 65)
cierra H5b como «No adjudicada». El tamaño máximo ensayado en SP3 es
$A\in\{2,3,4\}$ (p. 121); **la cifra 64 no aparece en ninguna página del
documento**. La red degradada sí se ensaya, pero en el demostrador Cargo de SP2
—«pérdida 0.25 y retardo de hasta dos eventos», p. 115— no en el tráfico de SP3,
de modo que la pregunta del bloque 20 queda sin responder incluso teniendo el
documento un régimen degradado.

---

## 5. Bloque 25 — modelo físico y realismo robótico

### 5.1 Tabla ítem a ítem

| # | Pregunta | Veredicto | Dónde |
|---|---|---|---|
| 1 | Pioneer P3-DX real vs. modelo abstracto | PARCIAL | p. 15; p. 60 |
| 2 | Radio de rueda | NO RESPONDE para el robot modelado | símbolo p. 82; 0.1 m en p. 126 |
| 3 | *Wheelbase* | NO RESPONDE | — |
| 4 | Torque | PARCIAL | p. 102, p. 114; cifras solo en pp. 125–127 |
| 5 | Masa | PARCIAL | 40 kg solo en p. 125 |
| 6 | Inercia | NO RESPONDE | — |
| 7 | Fricción | PARCIAL | p. 126 (*caging*); omitida en el resto |
| 8 | Tracción | NO RESPONDE | p. 127, con una cifra sin procedencia |
| 9 | *Slip* | NO RESPONDE (declarado, y contradicho en p. 35) | §7.5, p. 65 |
| 10 | Saturación | PARCIAL | Ec. (15), p. 47; pp. 105–106, 114 |
| 11 | Contacto bilateral / unilateral | PARCIAL | p. 11; p. 24; pp. 47–48 |
| 12 | Sensores | NO RESPONDE | radio de sensado, p. 15 |
| 13 | Pose exacta vs. estimada | RESPONDE | Tabla 3, p. 16; p. 105; p. 116 |
| 14 | Latencia | PARCIAL | retardo de red, p. 115; no hay latencia de control |
| 15 | Percepción | NO RESPONDE (declarado) | p. 3; p. 11; p. 65 |
| 16 | Error de odometría | NO RESPONDE | — |
| 17 | Actuadores | PARCIAL | $\mathcal U_i$, p. 104; constantes de motor, p. 127 |
| 18 | *Compliance* | PARCIAL (declarada ausente) | p. 125 |
| 19 | Rigidez | RESPONDE | p. 23; p. 114 |
| 20 | Qué es simulación idealizada | RESPONDE | p. 59; p. 60; p. 65 |
| 21 | Qué puede transferirse a hardware | RESPONDE | p. 60; p. 66 |

### 5.2 Verificación (a): ¿son ciertas las omisiones que el documento declara?

El enunciado que hay que contrastar está en §7.5, p. 65
(`07-conclusions-v2.tex:126`):

> «El modelo usa carga planar, pose conocida, contactos fijos y fuerzas
> acotadas; omite soporte vertical, fricción 3D, deslizamiento, percepción y
> tracción rueda–suelo.»

| Omisión declarada | ¿Cierta del modelo? | Comprobación |
|---|---|---|
| Soporte vertical | **Sí** | El *wrench* es planar de tres componentes (Ec. 2, p. 12; Ec. 11, p. 45). Ninguna ecuación incluye peso ni reacción normal al suelo. |
| Fricción 3D | **Sí**, con matiz | No hay fricción 3D. Sí hay un cono de Coulomb **planar** en el bloque de *caging*: «$|t_i|\le0.4n_i$» (p. 126). La declaración dice «3D», así que es compatible, pero el lector de §7.5 puede concluir erróneamente que no hay fricción en ningún sitio. |
| Deslizamiento | **Sí** | No hay modelo de rueda–suelo en ninguna campaña. Pero véase la contradicción de la p. 35, más abajo. |
| Percepción | **Sí** | Tabla 3 (p. 16): E4 opera con «pose exacta de carga»; p. 116: «El modelo usa pose exacta, contacto fijo y grafo estático conectado por intercambio». El «radio de sensado» de la escena AWS (p. 15) es una compuerta de alcance, no un modelo de percepción, y el texto no lo presenta como tal. |
| Tracción rueda–suelo | **Sí para SP1–SP3**; **no exactamente para el Anexo J** | El Anexo J.3 (p. 127) sí hace una comprobación de fuerza por rueda: «la fuerza máxima por rueda requerida es 12.551914 N, inferior a 61.3125 N disponibles». Ese es el único cálculo de tipo tracción del documento, y **la cifra de 61.3125 N no se deriva ni se atribuye a ninguna fuente**: el párrafo declara $nk_t=0.5$ N·m/A y resistencia $0.6\,\Omega$, y de ahí no se sigue ese valor sin un coeficiente de adherencia y una carga normal que no se escriben. |

Dos anomalías adicionales, ninguna de ellas declarada:

- **La definición de éxito físico incluye una comprobación que la planta no
  puede producir.** P. 35 (`results-interface.tex:86`): «Esta definición obliga
  a observar también los rechazos y evita llamar éxito a una corrida que
  incumple contacto, **deslizamiento**, colisión, límites o criterio terminal».
  El deslizamiento es uno de los cinco términos del predicado $Y$ («éxito físico
  completo») que define las tasas de falso positivo y falso negativo de la
  Tabla 11 (p. 46) y de H2 (p. 65). Ninguna simulación del TFM produce
  deslizamiento, de modo que ese término del predicado es idénticamente
  verdadero por construcción de la planta y no por bondad del método.
- **El único modelo de masa e inercia del documento no pertenece a la rama que
  transporta.** Anexo J.1, p. 125: «Cada carga tiene 40 kg y cuatro *pads*
  simétricos … Con rodadura ideal, *pads* rígidos centrados y yaw libre, y
  torque como entrada, el reparto $f_i=(m_\ell/4)\ddot P$ satisface Newton–Euler
  de carga y momento cero por simetría». La declaración de alcance que lo
  acompaña es correcta y está bien situada: «Estas cotas cubren geometría,
  ruedas, reacciones, torque y batería; no son una simulación de *tracking* de
  *pads* deformables ni de inductancia de motor» (p. 125). El problema es que
  esta es la única planta del TFM con parámetros físicos, y la que sostiene
  SP2 —$M_k$, $D_k$, $K_P$, $K_D$— no tiene ninguno.

### 5.3 Verificación (b): ¿se declara donde el lector encuentra el resultado?

Las declaraciones existen y son numerosas. Su distribución es la siguiente:

| Página | Texto | ¿Antes o después del resultado? |
|---|---|---|
| 3 (§1) | «El soporte tridimensional, la interacción rueda–suelo y la percepción completa requieren otro modelo. Tampoco se ensayaron agarre físico ni empuje por confinamiento geométrico.» | 42–62 pp. antes |
| 11 (§4) | «El contacto tridimensional, la percepción real y la validación en hardware permanecen fuera de la campaña.» | 34–54 pp. antes |
| 12 (§4.2) | «El modelo supone contactos fijos, límites de actuación y dinámica planar reducida.» | 33–53 pp. antes |
| 15 (§4.5) | «El agarre, la fricción rueda–suelo, la dinámica de contacto y el comportamiento en hardware requieren modelos y ensayos adicionales.» | 30–50 pp. antes |
| 16 (Tabla 3) | planta por etapa: «carga estática planar», «uniciclo y carga planar en estratos separados», «viaje reducido», «grafo discreto» | 29–49 pp. antes |
| 44 (§6.2.1) | «El modelo es cuasiestático y anterior al transporte.» | **en el sitio** (E3) |
| 45 (§6.2.1) | «El resultado no acredita contacto, estabilidad ni una arquitectura completamente vecinal.» | **en el sitio** (E3) |
| 47–48 (§6.3) | «contactos bilaterales fijos»; «realización exacta del *wrench* nominal»; Tabla 12, «piloto planar de contacto fijo» | **en el sitio**, pero solo estas tres |
| 52–53 (§6.4) | «no certifica: contacto físico»; «El piloto AWS mueve actores cinemáticamente: evidencia integración lógica y visual, no contacto físico ni un gemelo digital.» | **en el sitio** (SP3) |
| 60 (§6.7) | «un reparto realizable no implica estabilidad fuera del supuesto de contacto fijo» | 10–13 pp. después |
| 65 (§7.5) | la lista completa de omisiones | **18 pp. después de §6.3, 21 después de §6.2.1** |

Lectura del contraste. La pregunta del encargo era si cada omisión se declara
«donde el lector encuentra el resultado, no solo en una sección de limitaciones
cuarenta páginas después». La respuesta es matizada y se puede dar con
precisión:

1. **Sí hay declaración local para lo que el resultado supone**: E3 declara que
   es cuasiestático y previo al transporte (p. 44) y E4 declara contactos
   bilaterales fijos y realización exacta (pp. 47–48). Eso cubre los ítems
   «contactos» y «realización» del bloque 25.
2. **No hay declaración local para lo que el resultado omite.** En las nueve
   páginas de §6.2.1 a §6.4 (pp. 44–53) **no aparecen** las palabras «soporte
   vertical», «fricción», «deslizamiento», «percepción» ni «tracción». Un
   tribunal que lea el capítulo 6 —que es lo que se defiende— no encuentra en él
   ninguna de las cinco omisiones de §7.5.
3. **Las declaraciones anteriores (pp. 3, 11, 12, 15) son correctas y
   suficientes para un lector lineal**, y eso reduce la gravedad: no hay
   ocultación. Pero están todas en capítulos que el tribunal lee antes de los
   resultados y que no vuelve a consultar al juzgarlos, y ninguna se cita desde
   §6.

Dicho de forma operativa: la omisión está declarada dos veces, una demasiado
pronto y otra demasiado tarde, y nunca en el punto de uso. La reparación es de
una línea por sección.

### 5.4 La restricción no holónoma y la generación de fuerza

Pregunta del encargo: el certificado de *wrench* supone que cada contacto puede
aplicar fuerza en su dirección asignada; ¿establece el documento en algún punto
que un AMR de tracción diferencial pueda orientarse y generar esa fuerza?

**No. En el documento compilado, no.** El desarrollo está en la ficha S-01.

---

## 6. Fichas

### S-01 · La v2 suprimió las cuatro fronteras físicas del certificado de *wrench*

**Lo que hay en la v2.** El certificado de E3 se presenta en las pp. 44–46. Sus
únicas cualificaciones son: «El modelo es cuasiestático y anterior al
transporte» (p. 44), «$\Lambda_k$ … cerrado, convexo y no vacío» (p. 44), «la
conversa no vale en general» (Proposición 6.2, p. 45), «El resultado no acredita
contacto, estabilidad ni una arquitectura completamente vecinal» (p. 45) y la
etiqueta de la Figura 18, «E3 · *Wrench* planar — no certifica: estabilidad de
movimiento» (p. 42).

**Lo que había en la v1.** El fichero
`pre-thesis/sections/source-snapshot/mainmatter/06-results-and-analysis/sp3.tex`
—que **no** figura entre los 89 ficheros de `final-hardening/census.json` y por
tanto no se compila en `main-v2.pdf`— contenía, en las líneas 142–154, una
observación numerada:

> `\begin{observacion}[Lo que el certificado no certifica]`
> **(i) Conos de fricción.** $A_{ik}\boldsymbol\lambda_{ik}\le\boldsymbol b_{ik}$
> acota magnitudes de esfuerzo, no direcciones admisibles de Coulomb: un reparto
> certificado puede exigir una componente tangencial fuera del cono.
> **(ii) Dinámica.** $\boldsymbol W_k^{\mathrm{dem}}$ se fija a priori; en
> transporte depende de la aceleración instantánea de la carga.
> **(iii) Restricción no holónoma.** $G_k$ supone que cada puesto entrega su
> esfuerzo en su dirección de contacto; **un AMR diferencial debe orientarse
> antes**.
> **(iv) Mantenimiento del contacto.** Un contacto unilateral puede perderse.
> Cargo completo exigiría además soporte, fricción y peso; el empuje,
> unilateralidad; y el *caging*, $q\in\mathcal C_k^{\mathrm{cage}}$.

Y cerraba: «El certificado es por tanto una *condición de entrada* sobre el
modelo planar cuasiestático, no una garantía de transporte».

**Comprobación de la supresión.** Ninguna de estas cadenas aparece en
`main-v2.pdf`: «certificado no certifica», «conos de fricción», «Coulomb» en el
contexto de E3 (solo aparece en el Anexo J.3, p. 126, para *caging*), «debe
orientarse», «dirección de contacto», «no holónoma» (la única instancia de
«holónoma» está en la p. 83, dentro de la demostración de la Prop. C.1). El
mismo fichero v1 definía $G_k$ como «el mapa a fuerza/torque» con su matriz de
normalización (líneas 66–70) y declaraba «Cada puesto planar transmite esfuerzo
escalar acotado, por lo que $\Lambda_{ik}$ es un intervalo» (línea 104): tampoco
eso se compila.

**Lo que queda en la v2 sobre no-holonomía.** Solo la Proposición C.1 (p. 82),
que es una equivalencia **cinemática**: fija que el eje longitudinal de cada
robot sea paralelo o antiparalelo a la velocidad de su pivote,
$v_i^{\mathrm{piv}}$. Eso no responde la pregunta: la dirección de la velocidad
del pivote y la dirección de la fuerza de contacto asignada por el QP no
coinciden en general —en una rotación pura de la carga, la velocidad del pivote
es tangencial y el reparto puede exigir componente radial—, y el documento no
enlaza ambas direcciones en ningún punto. La Proposición C.3 (p. 83) se aproxima
por la vía negativa (la suma escalar no certifica soporte ni fricción) pero no
habla de orientación.

**El único lugar donde orientación y fuerza de contacto se tocan** es el
Anexo J.3, p. 126: «Para robots **estacionarios orientados hacia sus normales**,
radio de rueda 0.1 m, semivía y brazo de *bumper* 0.2 m,
$\tau_{iL/R}=0.05(n_i\mp t_i)$». La orientación se **supone**, los robots están
**parados**, y el bloque pertenece a la rama de *caging*, no a Cargo. El propio
párrafo lo dice (p. 127): «este experimento no es transporte».

**Consecuencia.** De las cuatro fronteras que la v1 declaraba, la v2 conserva
(ii) parcialmente —«cuasiestático y anterior al transporte», p. 44— y (iv)
parcialmente, en forma de hipótesis de contactos fijos en SP2. **(i) y (iii)
desaparecen.** El lector de la v2 recibe un certificado de *wrench* cuyo
conjunto admisible no está definido, cuya matriz de agarre no está construida y
del que no se dice que asigne a cada robot una dirección de fuerza que su
cinemática diferencial deba poder producir. La reparación es barata: la
observación existe, está escrita por el autor y solo hay que volver a compilarla
o resumirla en cuatro líneas detrás de la Proposición 6.2 (p. 45).

### S-02 · `SUPPORT` y `WHEELS` figuran como predicados verificados y no existen

La autorización de movimiento se define en la p. 34
(`results-interface.tex:44-51`, Ec. 8):

> $\mathsf{GO}_k=\mathsf{CLOSE}_k\wedge\mathsf{SUPPORT}_k\wedge
> \mathsf{WRENCH}_k\wedge\mathsf{WHEELS}_k\wedge\mathsf{CONTACT}_k\wedge
> \mathsf{ROUTE}_k$

y se refuerza en la Figura 10 (p. 34): el certificado $C_2$ es
«soporte–*wrench*–ruedas y pose dentro de tolerancia». La Tabla 22 (p. 60)
repite: «SP2 — predicado verificable: soporte, ruedas, contacto y pose dentro de
tolerancia». La Tabla 19 (p. 53) los convierte en dos filas de chequeo:
«Cinemática — *twist* realizable por las ruedas» y «Mecánica — soporte, contacto
y residual dentro de tolerancia».

Contra eso, §7.5 (p. 65) declara que el modelo «omite **soporte vertical** … y
**tracción rueda–suelo**», y esta auditoría confirma que ni el soporte ni el
límite de rueda tienen ecuación, umbral ni métrica en ninguna campaña: el único
chequeo de rueda del documento es una desigualdad simbólica del Anexo C.1
(p. 83, $|\omega|\le\min_i r_i^w\bar\omega_{w,i}/(d_i^{\mathrm{ICR}}+\ell_i^w)$)
sin valores, y el único cálculo de fuerza por rueda es el de la p. 127, en otra
rama y con una cifra sin procedencia.

No es un error de cálculo: es un contrato que promete seis conjuntos y entrega
cuatro. Tres lugares del documento (pp. 34, 53 y 60) afirman que la coalición
solo avanza si «soporte» y «ruedas» pasan, y ninguno dice cómo se comprueban.

### S-03 · El robot real se nombra y sus parámetros no se usan

«Pioneer P3-DX» aparece dos veces en el documento activo. La primera, p. 15
(`04-methodology.tex:363`), como modelo visual de la escena de CoppeliaSim:
«cuatro bases para 12 Pioneer P3-DX». La segunda, p. 60
(`thesis-results-v2.tex:34`), como trabajo futuro: «La campaña MuJoCo con
Pioneer P3DX deberá decidir si el certificado vectorial reduce falsos positivos
dentro del dominio parametrizado».

**Ningún parámetro del P3-DX se usa en ninguna ecuación ni campaña.** Las
cadenas «*wheelbase*», «entre ejes», «inercia», «*slip*», «odometría» y
«latencia» no aparecen en las 146 páginas. El radio de rueda y la semivía
aparecen como símbolos sin valor en el Anexo C.1 (p. 82) y con valores redondos
—0.1 m y 0.2 m— en el Anexo J.3 (p. 126), donde no se atribuyen a ningún robot
comercial y sirven a un cálculo estático de pérdidas de cobre. Los radios que sí
tienen valor son de envolvente, no de rueda: 0.32 m para el disco exterior del
robot (p. 125) y 0.52–0.68 m para la huella inflada de coalición (p. 121).

El efecto es de expectativa: el nombre de un robot comercial en la metodología y
en la síntesis sugiere una planta parametrizada que el documento no tiene. La
frase de p. 60 resuelve el problema de forma elegante si se lee entera —remite a
una campaña futura— pero la de p. 15 no lleva ninguna salvedad.

### S-04 · Lo que sí transfiere a hardware está bien acotado

Se registra por simetría, porque los dos últimos ítems del bloque 25 son los
únicos que el documento responde de forma ejemplar.

- P. 60: «Ese resultado acredita coexistencia funcional en su banco numérico, no
  convergencia global ni transferencia industrial».
- P. 60: «Una garantía extremo a extremo necesitaría además invariancia durante
  las conmutaciones y compatibilidad entre los tres modelos; esa prueba no se
  reclama aquí».
- P. 66 (§7.6): «Una planta física independiente deberá incorporar fricción,
  agarre, saturación, incertidumbre y ruido; ROS 2 permitirá medir edad de
  información, bytes, memoria, energía y CPU bajo topología móvil».
- P. 65 (§7.4), fila HP: «Apoyo delimitado … Compatibilidad funcional; planta
  reducida, registro global y seguridad combinada».
- P. 59: la reproducción en CoppeliaSim se declara como «geometría y reejecución
  de la trayectoria comandada, no física independiente ni hardware», con el
  error de reejecución publicado ($6.89\times10^{-9}$ m) para que se vea que es
  un *replay*, no una simulación.

La frontera entre simulación idealizada y transferible está, por tanto, escrita.
Lo que falta —y es el objeto de S-01 y S-02— es que las piezas concretas del
modelo que la producen estén escritas en el mismo sitio.

---

## 7. Lo que esta auditoría no cubre

- No se reauditan los enunciados formales uno a uno: eso es
  `04-matematica.md`. Cuando un ítem de los bloques 19 y 20 coincide con una
  ficha de ese informe (LaSalle/F-06, potencial de E2/F-10, «uniformemente
  acotado» de la Prop. 6.6/F-12, solución racional del QP de *caging*/F-07), se
  cita y no se repite el análisis.
- No se verifica la aritmética de las tablas de resultados ni las macros
  generadas.
- No se juzga el bloque 21 (juego de integración), 22, 23, 24 ni 26, que quedan
  fuera del encargo.
- Los ficheros de la rama `source-snapshot/` que **no** están en
  `census.json` se han leído únicamente para documentar la supresión de la
  ficha S-01; no forman parte del artefacto auditado.
