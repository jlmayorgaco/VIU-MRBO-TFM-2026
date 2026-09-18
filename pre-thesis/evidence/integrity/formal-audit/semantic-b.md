# Auditoría semántica B — `PAPER-FR-0051` a `PAPER-FR-0100`

Fecha de corte: 2026-09-08. Esta es una revisión de integridad Stage 2.5, no una revisión académica Stage 3 ni una autorización editorial. Se auditaron los cincuenta resultados consecutivos asignados del corpus `paper`, leyendo el enunciado, su demostración cuando existe y el contexto inmediato que fija definiciones o reconoce límites.

## Cobertura y criterio

- Rango: `PAPER-FR-0051-pr:barrera-compuesta`–`PAPER-FR-0100-pr:balance-adaptativo`.
- Cobertura: 50/50 identificadores, sin huecos, duplicados de ID ni duplicados de etiqueta dentro del bloque.
- Coincidencias literales con los 18 resultados activos aprobados: 0.
- Enlaces exactos preexistentes a `docs/04_CLAIMS_EVIDENCE.md`: 0/50. El CSV conserva `NONE_IN_DOCS_04`; una afinidad temática no se trató como evidencia.
- Evidencia independiente enlazada: 0/50. `SOURCE_PROOF_ONLY`, `SOURCE_DERIVATION_ONLY` y `SOURCE_STATEMENT_ONLY` describen qué contiene el propio borrador, no una validación externa.

`PASS` significa que el resultado matemático local queda sustentado por el argumento escrito bajo los supuestos indicados en el registro. No autoriza su inclusión automática. `LIMITED` indica un núcleo recuperable con supuestos, dominio, unidades o prueba incompletos. `FAIL` identifica una implicación falsa, una prueba inválida o una extrapolación que admite contraejemplo. `CONJECTURE` reserva una idea de diseño todavía no formulada como resultado demostrable.

| Veredicto | Cantidad | Destino dominante |
|---|---:|---|
| PASS | 15 | `monograph` |
| LIMITED | 20 | `monograph` o `background`, tras corrección |
| FAIL | 13 | `archive-only` |
| CONJECTURE | 2 | `monograph`, rotulada como conjetura |
| DUPLICATE | 0 | — |

## Resultado por identificador

| ID | Veredicto | Hallazgo decisivo | Destino |
|---|---|---|---|
| 0051 | LIMITED | Las cotas log-sum-exp son correctas; “barrera válida” requiere regularidad dinámica, signo y unidades de `kappa`. | monograph |
| 0052 | LIMITED | La identidad de segunda derivada es plausible y verificable, pero no tiene prueba y no implica factibilidad HOCBF. | monograph |
| 0053 | FAIL | `psi(t-)>=0` no implica `h(t-)>=0`; la prueba usa una premisa ausente. | archive-only |
| 0054 | PASS | El temporizador positivo excluye Zenón por agente mediante una prueba directa. | monograph |
| 0055 | LIMITED | Resultado clásico de tiempo finito citado, sin prueba ni condiciones de existencia completas. | background |
| 0056 | FAIL | Un reset integral no conserva universalmente el equilibrio ni reduce siempre el sobreimpulso. | archive-only |
| 0057 | FAIL | La conectividad enraizada no basta sin detectabilidad y condiciones sobre el observador. | archive-only |
| 0058 | LIMITED | La cota de estado se deriva; no se cierra el error de salida anunciado ni el observador. | monograph |
| 0059 | PASS | Invariancia del intervalo y cota de progreso correctas para el sistema escalar de primer orden. | monograph |
| 0060 | PASS | La sensibilidad `epsilon/mu` de la VI se prueba por evaluación cruzada y monotonía fuerte. | monograph |
| 0061 | PASS | Contracción correcta para un gradiente con jacobiano simétrico acotado; no cubre toda VI monótona. | monograph |
| 0062 | LIMITED | Falta exigir grafo estático conectado y perturbación en el subespacio de desacuerdo. | monograph |
| 0063 | LIMITED | La cota de obsolescencia necesita canal fiable y ordenado; no cubre pérdida o reordenamiento. | monograph |
| 0064 | PASS | Cota última `v/mu` correcta para un cero interior móvil en una ODE no proyectada. | monograph |
| 0065 | LIMITED | Se localizan raíces imaginarias, pero no se demuestra primer cruce ni transversalidad. | monograph |
| 0066 | PASS | Aproximación de Kurtz bien delimitada a horizonte finito y tasas Lipschitz. | monograph |
| 0067 | PASS | El `commit` certificado sigue de una cadena exacta de cotas. | monograph |
| 0068 | LIMITED | La cota presupone, pero no define, un balance aditivo que evita contar dos veces el progreso. | monograph |
| 0069 | LIMITED | La integración de márgenes es válida entre saltos; faltan convenciones para tasas cero y resets. | monograph |
| 0070 | PASS | La contribución marginal exacta y los pares simétricos producen un potencial exacto. | monograph |
| 0071 | LIMITED | Tangencia y descenso son correctos solo con `T_i>0` y `lambda_i>=0`, omitidos. | monograph |
| 0072 | LIMITED | Convolución correcta en espacio euclídeo con covarianzas válidas; no es global sobre `SE(2)`. | monograph |
| 0073 | LIMITED | La cota integral exige laplacianos simétricos y preservación del promedio. | monograph |
| 0074 | PASS | Cotas de gradiente y Frank–Wolfe correctamente demostradas en sus dominios. | monograph |
| 0075 | PASS | La desigualdad `2c` se obtiene por tres aplicaciones de la cota uniforme. | monograph |
| 0076 | FAIL | Dos incisos exactos se mezclan con leyes de condicionamiento y rondas sin prueba ni unidades comunes. | archive-only |
| 0077 | FAIL | Fijar autoridad `a` no fija margen de demanda `delta` ni mezcla de red `eta`. | archive-only |
| 0078 | FAIL | La ley cúbica usa una linealización angular; no es un `Theta(d^3)` global del modelo trigonométrico. | archive-only |
| 0079 | LIMITED | Covariance Intersection requiere estimaciones de entrada consistentes y una carta local para pose. | background |
| 0080 | FAIL | Dificultades del promedio ingenuo no prueban que la localización solo admita CI o centralización. | archive-only |
| 0081 | FAIL | Una región gaussiana por muestra no se convierte en invariancia probabilística de una trayectoria. | archive-only |
| 0082 | PASS | El margen `2 epsilon_p` garantiza separación posicional por desigualdad triangular. | monograph |
| 0083 | LIMITED | Poder calcular las aristas no hace local un payoff que dependa de estado global. | background |
| 0084 | LIMITED | Jerarquía bibliográfica plausible; faltan prueba y convenciones para degeneraciones geométricas. | background |
| 0085 | PASS | La intersección robusta crece al reducir válidamente el conjunto de parámetros. | monograph |
| 0086 | CONJECTURE | La ampliación de un conjunto no define por sí sola pago, riesgo ni identidad de potencial. | monograph |
| 0087 | PASS | El ejemplo bilineal demuestra exactamente la divergencia de Euler y el rango contractivo del extragradiente. | monograph |
| 0088 | LIMITED | Los conjuntos de fase no están incrustados en un espacio común ni se formalizan los resets. | monograph |
| 0089 | LIMITED | La restricción vale para contacto sobre el eje y marcos coherentes; la propia fuente invalida su transferencia al contacto adelantado. | background |
| 0090 | FAIL | Una distancia de frenado 1D no garantiza factibilidad simultánea de todas las barreras. | archive-only |
| 0091 | FAIL | La prioridad lexicográfica no evita que el conjunto seguro de entradas sea vacío. | archive-only |
| 0092 | FAIL | Maximizar fuerza opuesta no asegura par nulo ni la deceleración pura usada en la prueba. | archive-only |
| 0093 | FAIL | `xi_d->0` no implica `dot xi_d->0`; precio cero tampoco implica salida ni desacoplamiento. | archive-only |
| 0094 | CONJECTURE | El testigo carece de definición telescópica de coste, mapas de reset y prueba. | monograph |
| 0095 | PASS | La telescopía semi-Markov da las cotas esperadas y llegada casi segura bajo `tau_min>0`. | monograph |
| 0096 | LIMITED | La cota necesita que `P_hat` sea un kernel normalizado y una convención de norma explícita. | monograph |
| 0097 | FAIL | La prueba concatena resultados locales fallidos y no demuestra invariancia de resets ni entrega. | archive-only |
| 0098 | LIMITED | El QP de máxima disipación es plausible y dimensionalmente coherente, pero no se deriva. | monograph |
| 0099 | LIMITED | Las tres propiedades requieren restringir la clase mecánica, el dominio y la parametrización. | background |
| 0100 | PASS | La identidad adaptativa cancela Coriolis y error paramétrico; no reclama identificación ni ISS completo. | monograph |

## Bloqueos de promoción

Los resultados `0053`, `0056`, `0057`, `0076`–`0078`, `0080`–`0081`, `0090`–`0093` y `0097` no deben migrarse como lema, proposición, teorema o corolario. Sus contraejemplos o saltos lógicos están documentados en el CSV.

Los quince `PASS` siguen sin `claim-ID` ni artefacto independiente. Para utilizar alguno en la memoria VIU habría que: registrar una afirmación exacta y limitada en la matriz de evidencia; armonizar símbolos y unidades con `docs/05_NOTATION.md`; aportar prueba autocontenida en la fuente activa; y revisar su necesidad frente al presupuesto de páginas. Mientras eso no ocurra, el destino recomendado es la monografía.

Los veinte `LIMITED` no deben citarse como garantía. Pueden conservarse como material de trabajo o antecedente únicamente después de incorporar los supuestos y correcciones indicados. Los dos `CONJECTURE` son ideas de investigación explícitas, no resultados establecidos.
