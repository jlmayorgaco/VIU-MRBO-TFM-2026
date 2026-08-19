# SP1 — Contrato científico final

**Estado: congelado en Checkpoint A (2026-08-18).**
Cualquier modificación posterior a la ejecución de las campañas confirmatorias
debe registrarse aquí con fecha y motivo. Los umbrales prácticos de §4 se fijan
**antes** de observar el dato nuevo.

---

## 1. Alcance

SP1 estudia **exclusivamente el reclutamiento y la formación de coaliciones**.
Termina cuando entrega una coalición entera de AMR cuya cobertura de capacidad
ha sido verificada.

SP1 **no** afirma: viabilidad de agarre o contacto, viabilidad de *wrench*,
estabilidad de formación, transporte cooperativo, planificación de trayectorias,
evitación de obstáculos durante el transporte, operación con batería, ni
robustez ante comunicaciones degradadas más allá de las condiciones de red
explícitamente evaluadas.

Término canónico: **AMR**.

---

## 2. Pregunta general

**RQ-SP1.** ¿Hasta qué punto puede simplificarse y distribuirse el reclutamiento
de coaliciones antes de perder factibilidad o calidad de solución, y qué grado
de coordinación local se requiere cuando las simplificaciones previas dejan de
ser suficientes?

## 3. Hipótesis general del capítulo

**H-SP1.** El reclutamiento de coaliciones admite una jerarquía de modelos de
complejidad creciente. Cada nivel es suficiente dentro de una región de
operación identificable; violar su supuesto dominante produce un modo de fallo
observable que motiva el nivel siguiente. Dentro del dominio evaluado, la
información local y una coordinación estratégica de orden bajo permiten obtener
coaliciones enteras con un compromiso medible entre factibilidad, calidad,
comunicación y cómputo.

---

## 4. Hipótesis locales

### H-N1 — representación

Bajo capacidad homogénea de los AMR, la expansión por puestos es una
representación **entera exacta** del reclutamiento. Este resultado debe ser
invariante al escenario espacial, porque su origen es **combinatorio** —la
estructura bipartita totalmente unimodular— y no geométrico. A medida que las
capacidades individuales dejan de ser intercambiables, la cardinalidad por sí
sola deja de certificar la cobertura de capacidad.

**Precisión obligatoria** (corrige una formulación errónea previa):

- la formulación **por puestos** es integral por su estructura bipartita/TU;
- la heterogeneidad **destruye la posibilidad de representar coaliciones
  arbitrarias mediante puestos intercambiables**;
- la relajación **ponderada** permite participación fraccionaria de un AMR.

**No debe escribirse** que «la heterogeneidad causa que el LP sea fraccionario».
La relajación ponderada ya es fraccionaria bajo capacidad homogénea: en el banco
actual la brecha mediana con CV = 0 es 23,1 %.

### H-N2 — atomicidad / composición

Al conservar la capacidad individual, la relajación continua ponderada puede ser
fraccionaria y puede admitir asignaciones sin coalición entera ejecutable. La
presión, la composición y el escenario afectan a la magnitud y a las
consecuencias operativas de esa brecha de relajación.

### H-N3.A — coste de distribuir

Sustituir la información global por comunicación vecinal introduce un compromiso
medible entre calidad de solución, factibilidad y comunicación.

### H-N3.B1 — incentivo

Bajo el mismo contrato de información y la misma vecindad estratégica, el diseño
del *fitness* afecta a la calidad de la coalición terminal.

### H-N3.B2 — protocolo de revisión

Condicionado al mismo *fitness*, el protocolo de revisión afecta a convergencia,
exploración y comunicación, pero cambiar un protocolo de revisión unilateral
**no amplía por sí solo la vecindad estratégica**.

### H-N3.C — conectividad

La conectividad afecta a la capacidad de reconstruir decisiones globalmente
consistentes. Una partición persistente es un **control negativo** que demuestra
el límite informativo.

### H-N4.A — barrera estratégica

Una porción sustancial de la pérdida residual tras la búsqueda local unilateral
se debe a **barreras estratégicas de orden bajo**, y no meramente a la elección
de la regla de revisión unilateral.

### H-N4.B — orden

Aumentar el orden estratégico de h = 1 a h = 2 captura la mayor parte de la
mejora observada, mientras que h = 3 muestra un beneficio adicional decreciente
en el dominio evaluado.

### H-N4.C — mecanismo

El orden mínimo de escape conectado detectado, **h_c\***, debe explicar por qué
el refinamiento *pair-first* resulta eficaz. **h_c\* es un diagnóstico empírico,
no un teorema.**

### H-N4.D — ejecución distribuida

DMIS+TX puede eliminar el orden global de confirmación bajo el modelo de canal
fiable nominal, preservando la lógica de candidatos, a un coste de comunicación
medible.

### H-N4.E — validez externa

El punto de operación *pair-first* debe evaluarse sobre geometrías
intralogísticas **held-out** antes de describirse como robusto fuera de las
geometrías sintéticas de desarrollo.

---

## 5. Criterios prácticos preinscritos

**Registro de precedencia.** El audit no encontró umbrales prácticos
preinscritos para N4 industrial. Los siguientes se fijan **como decisión de
diseño previa a la ejecución** (Checkpoint A) y no podrán modificarse tras
observar el dato:

| Criterio | Umbral | Aplicable a |
|---|---|---|
| Factibilidad condicionada a oráculo factible | ≥ 95 % | Geo-QPG-2BR + DMIS+TX |
| Brecha mediana certificada frente a MILP | ≤ 15 % | Geo-QPG-2BR + DMIS+TX |
| P(h_c\* ≤ 2) | ≥ 80 % | terminales BR del banco held-out |
| Pérdida de factibilidad frente a Pair-GRAPE | ≤ 5 puntos porcentuales | Geo-QPG-2BR + DMIS+TX |

Umbral heredado y reutilizado de SP1 previo: margen práctico del **5 %** para
contrastes de ahorro relativo (usado en N1.E1).

Si un criterio falla, el capítulo debe indicar **exactamente dónde** deja de ser
robusto el *pair-first*. No se ajustará el experimento hasta obtener el
resultado deseado.

---

## 6. Correcciones semánticas obligatorias

1. **Geo-QPG es bifásico.** Fase de cobertura Φ_Q = −D; fase de calidad
   Φ_G = −J. No se afirmará un único potencial escalar exacto que pruebe ambas
   fases simultáneamente. Una vez D = 0, los movimientos de calidad preservan la
   factibilidad si ése es el contrato implementado.
2. **a_i = 0** se define como *AMR ocioso / no asignado*.
3. **ASR**: si la suma de ganancias positivas es cero, el AMR conserva su acción.
4. **LLL**: no se etiquetará una salida estocástica o truncada como mínimo
   1-local salvo que un pulido determinista no truncado lo establezca.
5. **h-local**: sólo se afirmará minimalidad h-local con búsqueda exhaustiva no
   truncada. Para el diagnóstico real con h ≤ 3 se dirá *«primer escape
   conectado de mejora detectado hasta h = 3»*.
6. **DMIS** es conjunto independiente **maximal**, no máximo.
7. **DMIS+TX** no elimina toda la infraestructura lógica: elimina el **orden
   global de confirmación** bajo el contrato de comunicación nominal declarado.
8. **Sin afirmaciones de robustez** ante pérdida de paquetes, retardo arbitrario,
   partición o fallos bizantinos salvo simulación o prueba explícita.
9. **Métodos continuos**: el cierre R es **central**. Su tráfico no se ocultará
   dentro de afirmaciones de «distribuido».
10. **Primal–dual**: redacción «método primal–dual orientado a búsqueda de
    vGNE», salvo que se establezca la convergencia de la discretización
    implementada.
11. **«falso positivo de factibilidad»**, no «falso factible». Definición:
    *aceptado por el modelo de cardinalidad de N1 **y** que incumple la
    restricción real de capacidad agregada*.
12. **bytes/AMR**, nunca «bytes/agente».

---

## 7. Estructura final del capítulo

Objetivo: 16–18 páginas de cuerpo con maquetación VIU 12 pt, sin reducir
legibilidad ni comprimir figuras.

1. Pregunta científica y progresión (diagrama F1; frontera con SP2)
2. Protocolo experimental común (T1)
3. **N1 — ¿cuándo basta la cardinalidad?**
   3.1 Formulación por puestos y estructura LP integral
   3.2 Experimento de validez frente a heterogeneidad (F3)
   3.3 Robustez geométrica
   3.4 Interpretación y transición a N2
4. **N2 — ¿cuándo importa la composición?**
   4.1 Formulación entera ponderada
   4.2 Atomicidad: LP frente a MILP (F4)
   4.3 Robustez presión × heterogeneidad
   4.4 Certificación del oráculo como evidencia secundaria
   4.5 Interpretación y transición a N3
5. **N3 — ¿qué cuesta distribuir la decisión?**
   5.1 Contrato de información vecinal
   5.2 N3.A arquitectura distribuida: CBBA-RB / Weighted-GRAPE / Pair-GRAPE (F5)
   5.3 N3.B protocolo de revisión × *fitness*; familias continua y dual
   5.4 N3.C robustez topológica y control negativo por partición (F6)
   5.5 Interpretación y transición a N4
6. **N4 — ¿por qué persisten los mínimos locales?**
   6.1 Potencial Geo-QPG y vecindad estratégica V_h
   6.2 h = 1 frente a h = 2 frente a h = 3 (F7)
   6.3 Mecanismo: h_c\*
   6.4 Confirmación distribuida: CF frente a DMIS+TX (F8)
   6.5 Validez held-out industrial
   6.6 DPOP y escalado como validación secundaria compacta
7. Síntesis transversal y contrato SP1 → SP2 (F9, T5, limitaciones)

**Traslados respecto del capítulo actual**

- Replicator / Smith / BNN / Logit: de N4 F-II → **N3.B**.
- Primal–dual vGNE: de N4 F-III → **N3.B**, como familia restringida/dual
  separada, no como otro protocolo de revisión poblacional.
- F-IV temporal: **fuera del cuerpo** → anexo o trabajo futuro.
- DPOP detallado, escalado, trazas, atlas redundante, tablas estadísticas
  completas: **anexo**.

---

## 8. Tablas del cuerpo (máx. 5)

| ID | Contenido |
|---|---|
| T1 | Protocolo experimental común: factores, unidad mundo–semilla, respuestas, inferencia |
| T2 | Métodos de referencia N1/N2: LP, LSAP, MILP, voraz — información, garantía, papel |
| T3 | Familias distribuidas y de revisión N3 |
| T4 | Métodos estratégicos y de ejecución N4 |
| T5 | Trazabilidad de evidencia de SP1 |

---

## 9. Registro de niveles de afirmación

Todo resultado del capítulo se marcará como:

- **FORMAL** — demostrado a partir de supuestos declarados;
- **EMPÍRICO** — observado en campaña finita, con denominador explícito;
- **DIAGNÓSTICO** — análisis *post hoc* o mecanístico;
- **LÍMITE** — no establecido fuera del dominio evaluado.

---

## 10. Condiciones de cierre

SP1 se considerará cerrado cuando un lector pueda responder, tras una sola
lectura y sin consultar registros brutos:

1. por qué el reclutamiento homogéneo se reduce a cardinalidad y dónde falla esa
   representación;
2. por qué la composición entera de AMR es necesaria y por qué el LP puede no
   representar una coalición ejecutable;
3. qué se paga al retirar la información global, y qué papel juegan la regla de
   revisión, el *fitness* y la conectividad;
4. por qué los métodos unilaterales siguen siendo subóptimos, qué orden
   estratégico se requiere habitualmente en el dominio evaluado y qué cuesta la
   confirmación distribuida;
5. qué objeto exacto entrega SP1 a SP2 y qué propiedad física **no** ha quedado
   certificada.
