# SP1 — Especificación editorial para la reescritura única

Principio rector: **ser riguroso sin explicar que se es riguroso.** El texto
actual acumula las huellas de sus propias rondas de auditoría; la poda consiste
en retirarlas, no en escribir de forma más sofisticada.

Se conserva el **100 % de los resultados formales y de la evidencia principal**.

---

## 1. Línea base medida (sp1.tex, 2026-08-19)

| Dimensión | Actual | Objetivo | Verificación |
|---|---|---|---|
| Metadiscurso léxico | 20 marcas · 3,8 / 1000 palabras | **≤ 14** (−30 %) | `meta_lint.py` |
| Elementos visuales | 62 · 2,58 por página | **≤ 48** (−22 %) | recuento estructural |
| Bandas negras | 25 · 1,04 por página | **0 en el `main`** | `\section` de plantilla |
| Fichas F-I…F-IV | 52 | **0 en el cuerpo** | traslado a N3 / anexo |
| Páginas | 27 | **20–23** | recuento |

**Hallazgo:** el problema es ~4 veces más estructural que léxico. La reducción
sale del traslado de material, no de reescribir frases.

---

## 2. Frases a eliminar (localizadas)

| Línea | Actual | Sustitución |
|---|---|---|
| 168 | «El capítulo responde una pregunta única:» + recuadro | Prosa: «SP1 estudia cómo cambia la formación de coaliciones al retirar sucesivamente tres simplificaciones: homogeneidad de capacidad, información global y revisión unilateral.» Sin recuadro. |
| 372 | «Conviene no leer (5b) como una caracterización exacta…» | «La condición (5b) garantiza únicamente que la ventana suficiente sea no vacía; no caracteriza todas las instancias factibles.» |
| 377 | «Conviene señalar de dónde procede la facilidad de N1…» | «La integralidad de (4) procede de su matriz de incidencia bipartita totalmente unimodular.» |
| 435 | «no cabe leerla como superioridad general del LSAP» | «La ventaja medida está condicionada a esa heurística y al orden en que recorre las cargas.» |
| 472 | «La observación es más fuerte de lo que parece y conviene leerla junto a (5c)…» | **Eliminar sin reemplazo.** Continuar: «La relajación ponderada de (6) puede ser fraccionaria incluso bajo capacidades homogéneas: la brecha mediana medida en ese régimen fue 23,1 %.» |
| 568 | «El mismo contrato impone un límite que ninguna regla de decisión puede sortear.» | «Bajo partición permanente, una política basada únicamente en la información de su componente no puede garantizar optimalidad global en todas las instancias.» |
| 686 | «N4 conserva este contrato y cambia la pregunta.» | «Bajo el mismo contrato de información, N4 analiza cuántos AMR deben revisar simultáneamente.» |
| 688 | «Eso no significa que sea buena» | «La factibilidad no garantiza una brecha pequeña.» |
| 781 | «DMIS+TX resuelve otro problema» | «DMIS+TX actúa sobre la arquitectura de confirmación, no sobre la utilidad ni sobre el orden estratégico.» |
| 930–940 | Caja «Balance teórico» con Demostrado / Medido / No afirmado | Dos párrafos corridos, sin caja ni etiquetas. |
| 1262 | «La aportación principal aparece en N4.» | «El análisis de N4 mostró que…» |
| N2 | «La cobertura ponderada **destruye** la estructura TU» | «La incorporación de coeficientes individuales de capacidad elimina, en general, la garantía de unimodularidad total de la formulación por incidencia empleada en N1.» |
| N2 | «La brecha no es ruido numérico: nace del requisito atómico» | «La diferencia entre ambos objetivos es estructural: el LP admite participación fraccionaria, mientras la coalición ejecutable exige $x_{ik}\in\{0,1\}$.» |

**Regla de cautela:** una limitación fuerte **por resultado**, no una advertencia
preventiva por oración.

---

## 3. Títulos

| Actual | Final |
|---|---|
| N1: dominio de validez de la cardinalidad | **Reducción por cardinalidad en el caso homogéneo** |
| N2: la coalición depende de quién participa | **Asignación ponderada con capacidades individuales** |
| N3: localidad informativa sin coordinador global | **Reclutamiento bajo información vecinal** |
| N4: localidad estratégica en reclutamiento atómico | **Refinamiento estratégico de coaliciones enteras** |
| Calidad, comunicación y conectividad | **Efecto de la distribución y de la topología de comunicación** |
| Distribución del primer escape conectado | **Orden mínimo conectado de mejora** |
| Síntesis, trazabilidad y contrato de salida de SP1 | **Síntesis y alcance de SP1** |

---

## 4. Traslados estructurales

**Fuera del cuerpo:** protocolo Monte Carlo → metodología general; tabla de
generadores → metodología; pseudocódigos CBBA/GRAPE completos → anexo; atlas
F-I unilateral y coalicional → fusionar en una figura; F-IV → anexo; traza
individual F-I → anexo; DPOP detallado y regresiones de escalado → anexo;
tablas estadísticas completas → anexo.

**Reubicaciones:** Replicator/Smith/BNN/Logit y primal-dual de N4 → **N3.B**.

**Recuperar en el cuerpo:** N2 CV×ρ (mapa de atomicidad, ya generado como F4).

**Incorporar:** $R=m\,r_c$, $\Gamma_R$ y $\lambda_2$ en N3.C (ya generado en F6
panel C).

---

## 5. Terminología

- **AMR** en prosa, pies, tablas y **dentro de los TikZ**.
- **bytes/AMR**, nunca «bytes por agente» ni «por robot».
- «AMR compartido», no «robot compartido».
- «propuestas de reasignación», no «propuestas físicas» — N4 no actúa sobre la
  planta.
- $h_c^\star$ en las leyendas de figura, no $h^\star$.
- Tercera categoría: «**no detectado hasta $h=3$**», nunca «$h_c^\star>3$»:
  no hallado no equivale a inexistente.
- «Último estado continuo registrado», no «estado continuo final».
- «PD-vGNE-seeking + $\mathcal R$», no «PD-vGNE distribuido + R».

---

## 6. Figuras

**Conservar como núcleo:** jerarquía N1–N4 (simplificada, sin la franja de
nomenclatura); contraejemplos N2; contrato N3; calidad–comunicación; $h_c^\star$;
Pareto final. Toda otra figura debe justificar su espacio frente a estas seis.

**Rediseños obligatorios:**
- BR–2BR–C3: ampliar a ancho completo; suprimir la «Tabla 5», que es una lista
  de abreviaturas y no una tabla de datos.
- Página de mecanismo: separar en dos figuras (mecanismo $h_c^\star$; arquitectura
  CF/DMIS+TX). **Sin violín para $n=4$ ni $n=1$**: usar puntos individuales.
- Pareto final: círculo = salida entera directa, triángulo = continuo + cierre
  central $\mathcal R$; tamaño = factibilidad; declarar que el coste de
  $\mathcal R$ no está en el eje horizontal.

---

## 7. Fuente numérica

Toda cifra procede de `canonical_metrics.tex`. Ningún número se escribe a mano.
Cada macro declara su soporte en el nombre (`...GapCommon` frente a `...GapOwn`).

---

## 8. Verificación antes de congelar

```
python scripts/sp1_final_figs/meta_lint.py sp1.tex     # <= 14 marcas
```

Más: 0 bandas negras en el `main`; 0 fichas F-I…F-IV en el cuerpo; ≤ 48
elementos visuales; 20–23 páginas; sin página huérfana; numeración consecutiva
de figuras, tablas y ecuaciones; sin `Overfull`.

---

## 9. Patrón de párrafo objetivo

> En 1 159 mundos con solución certificada, Weighted-GRAPE y Pair-GRAPE
> alcanzaron factibilidad del 99,8 % y 100 %, frente al 75,8 % de CBBA-RB. Sobre
> los 878 mundos del soporte común, las brechas medianas fueron 20,9 %, 9,4 % y
> 40,3 %. Esa mejora requirió más comunicación: las variantes GRAPE transmitieron
> 20 909 y 25 791 bytes/AMR frente a 9 089 de CBBA-RB. La partición permanente
> establece el límite del protocolo al impedir un perfil globalmente consistente.

**Resultado → interpretación → límite.** Sin gestionar la lectura.
