# TITLE_DECISION — título, localidad y heterogeneidad

Fecha: 2026-09-18. Decide qué dice el título frente a lo que el documento
demuestra, y separa lo que es riesgo científico de lo que es riesgo
administrativo.

---

## 1. El título vigente y la contradicción

Título actual, en portada y en el Anexo I oficial:

> **Coordinación distribuida local de múltiples AMR para el transporte
> cooperativo de cargas heterogéneas en entornos industriales**

Contiene tres afirmaciones separables: **(a)** coordinación distribuida local,
**(b)** cargas heterogéneas, **(c)** entornos industriales. Las tres se examinan
por separado porque su situación probatoria es distinta.

### 1.1 La contradicción está escrita en el propio documento

No hay que inferirla. El documento la declara:

| Dónde | Qué dice |
|---|---|
| §7.2 | «no una arquitectura completamente distribuida» |
| Cuerpo, p. 19 | «El cierre entero y varios cálculos por carga consultan agregados globales; el registro del simulador también resuelve identificadores fuera del vecindario. Por eso la implementación evaluada es híbrida» |
| Tabla 3 | E0, E1, E2, E3, E4, E5 y Cargo con dependencias globales; **solo E6 y E7 son locales** |
| Algoritmo 1 | Entrada: «identificadores activos, **registro global**, demanda agregada»; «líder **designado globalmente**» |
| `docs/14_FULL_THESIS_RIGOROUS_REVIEW` B4 | Revisión previa que ya exigía resolver esto. **Sin cerrar.** |

La revisión interna de 2026-07-18 levantó este punto como bloqueante B4 y ningún
documento posterior registra su cierre. No es un hallazgo nuevo: es uno
pendiente desde hace dos meses.

### 1.2 Lo que sí es local

Para no sobrecorregir: la mensajería vecinal, la regla de revisión y los juegos
E6 y E7 son genuinamente locales. El término «local» describe con exactitud el
**mecanismo de revisión y comunicación**. Lo que no describe es el **cierre
entero, el reparto por carga ni el registro de atributos**.

---

## 2. Evaluación de familias de título

Criterios: exactitud científica, alineación con la evidencia, compatibilidad con
el Anexo I ya presentado, riesgo ante tribunal y coherencia terminológica.

### A) «Arquitectura híbrida basada en juegos y certificados físicos para la coordinación multi-AMR en transporte cooperativo industrial»

| Criterio | Valoración |
|---|---|
| Exactitud | **Alta.** «Híbrida» es la palabra que el propio §7.2 usa. «Certificados físicos» nombra la contribución real. |
| Evidencia | Sostenida: los certificados C1–C4 existen y están demostrados por separado. |
| Anexo I | **Cambio mayor.** Pierde «distribuida local», «cargas heterogéneas» y «AMR» como sujeto gramatical. |
| Riesgo tribunal | Bajo en lo científico, **alto en lo administrativo**. |
| Terminología | Coherente. |

Problema: «industrial» sobrevive sin respaldo (véase §4).

### B) «Coordinación multi-AMR mediante revisiones vecinales y certificados físicos para el transporte cooperativo de cargas con requisitos heterogéneos»

| Criterio | Valoración |
|---|---|
| Exactitud | **La más alta de las cuatro.** «Revisiones vecinales» es exactamente lo que es local y lo que está demostrado; «requisitos heterogéneos» es exactamente lo que varía. |
| Evidencia | Cada sintagma tiene respaldo: revisiones vecinales (E6, E7), certificados físicos (C2), requisitos heterogéneos (véase §3). |
| Anexo I | Cambio mayor. |
| Riesgo tribunal | **El más bajo en lo científico.** Ninguna pregunta de las tres «que hunden la defensa» ataca este título. |
| Terminología | Coherente; elimina «industrial» sin respaldo. |

Problema: es largo (20 palabras) y menos vendedor.

### C) «Arquitectura híbrida para coaliciones multi-AMR heterogéneas en el transporte cooperativo de cargas industriales»

| Criterio | Valoración |
|---|---|
| Exactitud | **Media.** Corrige la localidad y traslada correctamente la heterogeneidad a las coaliciones. Pero «cargas industriales» reintroduce por la puerta de atrás la afirmación industrial. |
| Evidencia | Parcial. |
| Anexo I | Cambio mayor. |
| Riesgo tribunal | Medio: «¿qué tiene de industrial su carga?» sigue disponible. |
| Terminología | Coherente. |

### D) Forma mínimamente modificada del título oficial

> **Coordinación local de múltiples AMR para el transporte cooperativo de cargas
> con requisitos heterogéneos**

Cambios: se suprime «distribuida», se sustituye «cargas heterogéneas» por
«cargas con requisitos heterogéneos», se suprime «en entornos industriales».

| Criterio | Valoración |
|---|---|
| Exactitud | **Alta**, si el cuerpo define «local» como el mecanismo de revisión (véase §5). |
| Evidencia | Sostenida. |
| Anexo I | **Cambio menor.** Conserva estructura, sujeto y orden; tres supresiones y una precisión. |
| Riesgo tribunal | Bajo. |
| Terminología | Coherente. |

---

## 3. Qué es exactamente heterogéneo — auditoría §7

La pregunta debe responderse por campaña, porque la respuesta **no es la misma
en todas**.

### 3.1 SP1 (E1, E2): heterogeneidad de flota, no de carga

En `sections/v2/sp1-compact.tex`, la carga $k$ entra en el juego solo a través
de la cuota obligatoria $n_k$ y del umbral de servicio $d_k^{\mathrm{srv}}$.
El coste $\kappa_{ik}$ y la puntuación de servicio se parametrizan con
**carga útil, batería y distancia del robot $i$**. La Figura 19 lo ilustra con
dos robots de servicio distinto, no con dos cargas distintas.

**Veredicto SP1: heterogeneidad de flota.** Las cargas difieren en dos escalares
de requisito.

### 3.2 Cargo (demostrador, 360 mundos): requisitos multidimensionales

El Algoritmo 1 admite una coalición contra un criterio agregado de **tres**
componentes: $|C_k|\geq3$, $\sum c_i^{\mathrm{pay}}\geq m_k^{\mathrm{req}}$ y
$\sum f_i^{\max}\geq F_k^{\mathrm{req}}$. Existe, por tanto, un vector de
requisitos por carga
$$r_k=(n_k,\;m_k^{\mathrm{req}},\;F_k^{\mathrm{req}},\;|C_k|_{\min}).$$

**Pendiente de confirmar con los datos crudos** si esas componentes varían entre
cargas dentro de la campaña de 360 mundos o si están fijas. Hasta confirmarlo,
no se afirma nada.

### 3.3 Preflight Cargo en CoppeliaSim: heterogeneidad física real, pero prueba de humo

`src/viu_mrob_tfm/coppelia_cargo/config.py` declara `payload_mass_kg` como
**factor del diseño factorial**, con masas confirmatorias $(14{,}0,\;28{,}0)$ kg,
perturbación relativa de masa por mundo, **inercia derivada** de la masa real y
de la geometría
($m(L^2+W^2)/12+m\lVert\mathrm{com}\rVert^2$),
**régimen de fricción** como factor y desplazamiento del centro de masas.

Eso es heterogeneidad física genuina: masa, inercia, fricción y centro de masas.
Pero `results/coppelia_cargo_preflight_minimal_v5/gate_status.json` registra
**3 corridas primarias, una celda factorial**, con
`inferential_status = smoke_only_no_inferential_claim` y
`confirmatory_claim_eligible = false`.

**Veredicto: la heterogeneidad física está implementada y es ejecutable, pero
hoy no está medida.** No puede sostener el título mientras la campaña
confirmatoria no se ejecute.

### 3.4 Decisión de redacción

Mientras la campaña confirmatoria no se ejecute, la formulación exacta es
**«cargas con requisitos heterogéneos»**. Si la campaña se ejecuta con las dos
masas y sus regímenes de fricción, y la inferencia cierra, entonces
**«cargas heterogéneas»** pasa a ser defendible y debe definirse en el cuerpo
con el vector $r_k$ y sus unidades.

Esta es una decisión **condicionada a un resultado que aún no existe**, y así
debe permanecer hasta que exista.

---

## 4. «Entornos industriales»

El único respaldo es el piloto derivado de AWS RoboMaker: 12 AMR, 4 cargas,
4 escenarios × 4 métodos × **2 semillas** = 32 ejecuciones, con **3 de los 4
escenarios entregando cero** con los cuatro métodos y 2 violaciones de barrera
registradas. El propio texto dice que «ninguna de estas cifras sostiene un
ranking ni una fiabilidad industrial».

**Un escenario derivado de un entorno industrial no es un entorno industrial.**
No hay hardware, ni planta, ni dato de campo. La palabra debe salir del título y
del resumen; puede permanecer en el cuerpo como *procedencia del escenario*,
siempre con el calificativo adyacente.

---

## 5. Recomendación

**Dos decisiones separadas, porque tienen dueños distintos.**

### 5.1 Decisión científica — se toma ahora, sin permiso de nadie

Reescribir **resumen, Abstract, Introducción, objetivos y brecha reclamada** de
modo que:

1. «distribuido» y «local» se usen **solo** para el mecanismo de revisión y la
   mensajería vecinal, nunca para el cierre entero, el reparto por carga ni el
   registro de atributos;
2. la arquitectura se describa como **híbrida**, que es lo que §7.2 ya dice;
3. «cargas heterogéneas» pase a **«cargas con requisitos heterogéneos»**;
4. «industrial» se use solo como procedencia del escenario, con calificativo;
5. la Metodología incorpore la **tabla de taxonomía de localidad** (§8 del
   encargo), que clasifica cada etapa por información usada y tipo de cierre.

Nada de esto requiere aprobación del tutor: corrige afirmaciones a lo que la
evidencia sostiene, que es obligación del autor.

### 5.2 Decisión administrativa — no se toma sin el tutor

**Conservar el título oficial de portada por ahora**, y consultar al tutor.

Motivo: el Anexo I ya presentado fija un título y, en ediciones anteriores,
terminología AGV. Cambiar la portada sin registro puede generar una discrepancia
entre el expediente y la memoria depositada, y ese es un riesgo de
procedimiento, no de contenido. El coste de preguntar es una consulta; el coste
de no preguntar puede ser una incidencia en el depósito.

**Si el tutor autoriza el cambio, la recomendación es la familia D**, por tener
la mejor relación exactitud/continuidad:

> Coordinación local de múltiples AMR para el transporte cooperativo de cargas
> con requisitos heterogéneos

y, si además se prefiere nombrar la contribución real en lugar del mecanismo,
la familia **B**, que es la más exacta de las cuatro.

### 5.3 Puente mientras tanto

Si el título de portada se conserva, el cuerpo **debe definir explícitamente**
qué significa ahí «local», en la Introducción y en la Metodología:

> En este trabajo, «local» califica el mecanismo de revisión y la mensajería
> vecinal. No califica el cierre entero, el reparto por carga ni el registro de
> atributos, que consultan agregados globales; la
> Tabla~[taxonomía de localidad] detalla esa dependencia etapa por etapa.

Con esa definición escrita, el título deja de ser una afirmación no sostenida y
pasa a ser un término definido. Sin ella, no.

---

## 6. Resumen de decisiones

| # | Decisión | Estado | Dueño |
|---|---|---|---|
| 1 | «distribuido/local» solo para revisión y mensajería | **aplicar ahora** | autor |
| 2 | Arquitectura descrita como híbrida | **aplicar ahora** | autor |
| 3 | «cargas con requisitos heterogéneos» | **aplicar ahora** | autor |
| 4 | «industrial» solo como procedencia del escenario | **aplicar ahora** | autor |
| 5 | Tabla de taxonomía de localidad en Metodología | **aplicar ahora** | autor |
| 6 | Definición explícita de «local» en Introducción | **aplicar ahora** | autor |
| 7 | Cambio del título de portada | **consultar** | tutor |
| 8 | «cargas heterogéneas» sin matiz | **condicionado** | campaña confirmatoria |
