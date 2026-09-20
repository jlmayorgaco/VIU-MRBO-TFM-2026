---
name: tfm-voice
description: Registro de prosa académica en español para el TFM (VIU-MRBO). Úsala SIEMPRE antes de escribir o reescribir prosa en Subdocuments/**/*.tex, thesis/**/*.tex, pre-thesis/**/*.tex o cualquier memoria, resumen, pie de figura o abstract del TFM. Aplica el criterio calibrado en docs/SP1_VOICE_CALIBRATION.md y docs/SP1_EDITORIAL_SPEC.md. Para una auditoría de patrones de IA a escala de documento completo (estilo Turnitin/AI-detector), usa además `ai-writing-audit`; para el linter léxico general en español e inglés, `no-ai-slop`.
---

# Voz del TFM

**Principio rector: ser riguroso sin explicar que se es riguroso.**

El texto que este repositorio produce por defecto acumula las huellas de sus
propias rondas de auditoría. La poda consiste en retirarlas, no en escribir de
forma más sofisticada. Las ecuaciones, definiciones y enunciados formales **no
se tocan**.

## 1. Las ocho reglas

1. Ningún párrafo empieza anunciando lo que va a hacer.
2. Un resultado, una limitación. Las demás van a la sección de Limitaciones.
3. Sin verbos que evalúan la propia evidencia: *sostener*, *respaldar*,
   *confirmar*, *demostrar contundentemente*, *establecer*.
4. Sin fórmulas de suspense ni de guía: *más fuerte de lo que parece*,
   *conviene*, *cabe*, *es importante*, *nótese que*.
5. La cifra va antes que su interpretación, y a veces sin interpretación.
6. Romper la simetría: si tres conceptos se enuncian en paralelo perfecto, unir
   dos o separar en dos frases de longitud distinta.
7. Punto y coma sólo cuando une dos cláusulas de igual peso. En duda, punto.
8. Los pies de figura describen; no interpretan.

## 2. Patrón de párrafo objetivo

**Resultado → interpretación → límite.** Sin gestionar la lectura.

> En 1 159 mundos con solución certificada, Weighted-GRAPE y Pair-GRAPE
> alcanzaron factibilidad del 99,8 % y 100 %, frente al 75,8 % de CBBA-RB. Sobre
> los 878 mundos del soporte común, las brechas medianas fueron 20,9 %, 9,4 % y
> 40,3 %. Esa mejora requirió más comunicación: las variantes GRAPE transmitieron
> 20 909 y 25 791 bytes/AMR frente a 9 089 de CBBA-RB. La partición permanente
> establece el límite del protocolo al impedir un perfil globalmente consistente.

## 3. Calibración medida (referencia de esfuerzo)

Los tres pasajes reescritos en `docs/SP1_VOICE_CALIBRATION.md` fijan la escala:

| Pasaje | Antes | Después | Recorte |
|---|---:|---:|---:|
| Apertura de capítulo | 118 palabras | 92 | −22 % |
| Resultado central N4 | 104 palabras | 61 | −41 % |
| Integralidad en N2 | 78 palabras | 56 | −28 % |

Si una reescritura no recorta, probablemente no ha retirado nada: revisa otra vez.

Alcance esperado sobre un capítulo completo: ~65 % de párrafos con edición ligera
(retirar una o dos frases), ~25 % reescritura real (introducciones, transiciones,
pies de figura), ~10 % intactos (demostraciones, definiciones, descripciones
cuantitativas).

## 4. Sustituciones canónicas

| En vez de | Escribe |
|---|---|
| «Conviene no leer (5b) como una caracterización exacta…» | «La condición (5b) garantiza únicamente que la ventana suficiente sea no vacía; no caracteriza todas las instancias factibles.» |
| «Conviene señalar de dónde procede la facilidad de N1…» | «La integralidad de (4) procede de su matriz de incidencia bipartita totalmente unimodular.» |
| «no cabe leerla como superioridad general del LSAP» | «La ventaja medida está condicionada a esa heurística y al orden en que recorre las cargas.» |
| «La observación es más fuerte de lo que parece y conviene leerla junto a (5c)…» | *Eliminar sin reemplazo.* Continuar con el hecho. |
| «El mismo contrato impone un límite que ninguna regla de decisión puede sortear.» | «Bajo partición permanente, una política basada únicamente en la información de su componente no puede garantizar optimalidad global en todas las instancias.» |
| «N4 conserva este contrato y cambia la pregunta.» | «Bajo el mismo contrato de información, N4 analiza cuántos AMR deben revisar simultáneamente.» |
| «Eso no significa que sea buena» | «La factibilidad no garantiza una brecha pequeña.» |
| «X **destruye** la estructura TU» | «La incorporación de coeficientes individuales de capacidad elimina, en general, la garantía de unimodularidad total de la formulación por incidencia.» |
| «La brecha no es ruido numérico: nace del requisito atómico» | «La diferencia entre ambos objetivos es estructural: el LP admite participación fraccionaria, mientras la coalición ejecutable exige $x_{ik}\in\{0,1\}$.» |
| «La aportación principal aparece en N4.» | «El análisis de N4 mostró que…» |
| Caja «Balance teórico» con Demostrado / Medido / No afirmado | Dos párrafos corridos, sin caja ni etiquetas. |

**Regla de cautela:** una limitación fuerte **por resultado**, no una advertencia
preventiva por oración.

## 5. Terminología obligatoria

Consulta también `docs/05_NOTATION.md`. Reglas que el linter no siempre atrapa:

- **AMR** en prosa, pies, tablas y **dentro de los TikZ**. Nunca «AGV» salvo en
  las apariciones históricas protegidas.
- **bytes/AMR**, nunca «bytes por agente» ni «bytes por robot».
- «AMR compartido», no «robot compartido».
- «propuestas de reasignación», no «propuestas físicas» (N4 no actúa sobre la planta).
- $h_c^\star$ en las leyendas de figura, no $h^\star$.
- «**no detectado hasta $h=3$**», nunca «$h_c^\star>3$»: no hallado no equivale
  a inexistente.
- «último estado continuo registrado», no «estado continuo final».
- «PD-vGNE-seeking + $\mathcal R$», no «PD-vGNE distribuido + R».
- Nunca «sin reloj» en un sistema implementado digitalmente: dilo como ausencia
  de rondas globales síncronas o de planificación por lotes.

## 6. Títulos

Los títulos nombran el objeto, no la intención del autor.

| Evita | Prefiere |
|---|---|
| «N1: dominio de validez de la cardinalidad» | «Reducción por cardinalidad en el caso homogéneo» |
| «N3: localidad informativa sin coordinador global» | «Reclutamiento bajo información vecinal» |
| «Distribución del primer escape conectado» | «Orden mínimo conectado de mejora» |
| «Síntesis, trazabilidad y contrato de salida de SP1» | «Síntesis y alcance de SP1» |

## 7. Fuente numérica

Toda cifra procede de las macros generadas (`generated/*.tex`,
`canonical_metrics.tex`). **Ningún número se escribe a mano.** Cada macro declara
su soporte en el nombre (`...GapCommon` frente a `...GapOwn`). Si necesitas una
cifra que no existe como macro, genérala en el script correspondiente antes de
citarla en prosa.

## 8. Verificación antes de congelar

```bash
python Subdocuments/SP1/scripts/sp1_final_figs/meta_lint.py Subdocuments/SP1/sp1.tex
```

Objetivo SP1: **≤ 14 marcas** (línea base medida: 20 marcas, 3,8 por 1000
palabras). Además: 0 bandas negras en el `main`; 0 fichas F-I…F-IV en el cuerpo;
≤ 48 elementos visuales; sin página huérfana; numeración consecutiva de figuras,
tablas y ecuaciones; sin `Overfull`.

**Hallazgo estructural:** en la línea base, el problema resultó ~4 veces más
estructural que léxico. La reducción sale del **traslado de material al anexo**,
no de reescribir frases. Antes de pulir léxico, pregunta qué sobra de página.

## 9. Qué NO hace esta habilidad

No reescribe demostraciones, definiciones, enunciados formales ni ecuaciones.
No cambia cifras. No altera el alcance científico ni el título oficial
(ver `AGENTS.md` §2). No convierte una afirmación cauta en una afirmación
fuerte: si el resultado no está demostrado, la poda estilística no lo demuestra.
