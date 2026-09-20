---
name: multiagent-lit
description: Disciplina de estado del arte y comparación con la literatura en coordinación multi-robot, formación de coaliciones, asignación de tareas y transporte cooperativo. Úsala al escribir o revisar el marco teórico (capítulo 5), al posicionar una contribución frente a trabajos previos, o al añadir entradas a references/LITERATURE_LEDGER.md.
---

# Estado del arte multi-agente

El capítulo 5 tiene 11–13 páginas y la VIU pide **comparación crítica**, no
catálogo. Una revisión que enumera veinte trabajos sin decir qué distingue al
tuyo no cumple el requisito aunque cite bien.

## 1. El mapa del campo, para no perder el eje

Las familias que este TFM debe situar y frente a las que se posiciona:

| Familia | Representantes | Qué resuelve | Qué supone |
|---|---|---|---|
| Asignación centralizada | LSAP, MILP, subasta centralizada | Óptimo con vista global | Coordinador y estado completo |
| Subasta distribuida | CBBA y variantes | Consenso sobre pujas | Comunicación repetida; garantías bajo submodularidad |
| Formación de coaliciones | GRAPE y variantes | Partición estable por preferencias | Utilidad hedónica declarada |
| Juegos potenciales | Diseño de utilidad para alinear con el bienestar | Terminación por potencial | Desviaciones del tipo declarado |
| Dinámicas poblacionales | Replicator, Smith, BNN, Logit | Revisión continua, distribuida | Masas poblacionales, tiempo continuo |
| Optimización distribuida | Primal-dual, vGNE seeking | Restricciones acopladas | Grafo conectado, pasos declarados |
| Transporte cooperativo | Prehensil (grasp, wrench) / no prehensil (caging) | Ejecución física | Modelo de contacto declarado |

Cada afirmación de novedad se sitúa **dentro** de una de estas casillas, no
contra el campo entero.

## 2. Cómo se compara honestamente

1. **Compara supuestos antes que números.** Dos métodos con contratos de
   información distintos no son comparables sin decirlo. La contribución de N3
   es precisamente medir lo que cuesta cambiar ese contrato.
2. **Declara qué implementación comparaste.** Una variante propia de CBBA no es
   CBBA del artículo original. Di cuál es y por qué.
3. **Ninguna cita de rendimiento ajeno como si fuera medida propia.** Un número
   de otro artículo se midió en otro banco. O lo reproduces, o lo citas como
   dato ajeno con su condición.
4. **La ventaja es local.** «Mejor que X en este banco, bajo estas capacidades y
   esta topología» es una frase publicable. «Mejor que X» no lo es.
5. **Di lo que el trabajo previo hace mejor.** Un estado del arte donde todos los
   antecedentes salen perdiendo no es creíble. CBBA transmite menos bytes; dilo.

## 3. La brecha (gap) se enuncia, no se insinúa

Estructura de tres frases para el hueco que justifica el TFM:

> Los métodos de [familia] resuelven [problema] bajo [supuesto].
> Cuando [el supuesto se retira], [qué deja de valer, concretamente].
> Este trabajo [qué hace exactamente] y mide [qué].

Si la segunda frase no nombra algo que se rompe de forma verificable, no hay
hueco: hay una preferencia.

## 4. Gestión de fuentes

- `references/LITERATURE_LEDGER.md` es el registro. Cada entrada nueva pasa
  primero por ahí, con: clave BibTeX, qué afirmación respalda, y si se ha
  verificado contra el original.
- **Ninguna referencia sin verificar.** Un modelo de lenguaje produce citas
  plausibles y falsas con facilidad. Resuelve DOI, arXiv o el documento antes de
  que entre al `.bib`. Ver `citation-hygiene`.
- Preferencia por la fuente primaria. El survey se cita como survey, no como
  origen del método.
- Equilibrio temporal: los fundamentos pueden ser de los años ochenta o noventa
  (cierre de forma, caging, juegos potenciales); el posicionamiento competitivo
  necesita trabajo reciente. Si todo lo reciente falta, el capítulo envejece mal
  ante el tribunal.

## 5. Al escribir el capítulo

- Prosa corrida, no fichas ni tablas de dos columnas por método (`tfm-voice`).
- Cada término técnico prestado se cita en su **primera aparición técnica**.
- El capítulo termina situando el trabajo, no resumiendo lo dicho.
- Toda afirmación comparativa pasa por `claims-evidence-guard`.
