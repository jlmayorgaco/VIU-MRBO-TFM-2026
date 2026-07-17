# Rúbrica de clasificación de la Figura 3

## Propósito

Este registro hace reproducible la posición metodológica de los trabajos mostrados en la Figura 3. No es una métrica de rendimiento, impacto, calidad ni madurez: resume únicamente la arquitectura de decisión declarada por cada fuente primaria verificada.

## Escala y fórmula

Para cada trabajo `p` se codifican cuatro indicadores arquitectónicos en `{0, 0.5, 1}`:

- `dec`: autoridad de decisión en ejecución (`0` planificador central; `0.5` líder, mercado o arquitectura híbrida; `1` decisiones de pares sin coordinador).
- `loc`: localidad de la información en ejecución (`0` estado o plan global; `0.5` mezcla de información global y local; `1` estado propio y mensajes vecinales).
- `learn`: dependencia del componente aprendido en la decisión primaria (`0` ninguna; `0.5` heurística o módulo aprendido dentro de un método explícito; `1` política aprendida primaria).
- `exp`: explicitud del mecanismo primario (`0` política opaca; `0.5` híbrido; `1` objetivo, restricciones o ley de actualización explícitos).

Las coordenadas nominales son:

\[
x_p=1-2\left(0.6\,\chi_p^{\mathrm{dec}}+0.4\,\chi_p^{\mathrm{loc}}\right),
\qquad
y_p=\chi_p^{\mathrm{learn}}-\chi_p^{\mathrm{exp}}.
\]

El peso de 0.6 en `dec` expresa que el eje horizontal pregunta primero **quién decide** en tiempo de ejecución y, en segundo lugar, qué información emplea. El nivel intermedio no demuestra descentralización: representa una arquitectura líder--seguidor, de mercado, híbrida o insuficientemente especificada para atribuir autonomía local completa.

La coordenada nominal $u_p=(x_p,y_p)$ conserva la interpretación cartesiana. La coordenada de presentación $z_p$ se obtiene con la proyección agrupada definida más abajo. Esta capa visual no modifica los valores de la tabla ni permite interpretar la separación gráfica como rendimiento.

## Distancia metodológica y agrupamiento

La distancia metodológica entre dos trabajos se calcula en el espacio de la rúbrica, no entre sus píxeles de presentación:

\[
d_{\mathrm{met}}(p,q)=
\sqrt{0.35(\Delta\chi^{\mathrm{dec}})^2+
       0.25(\Delta\chi^{\mathrm{loc}})^2+
       0.25(\Delta\chi^{\mathrm{learn}})^2+
       0.15(\Delta\chi^{\mathrm{exp}})^2}.
\]

Los pesos suman uno y todos los indicadores están en $[0,1]$, de modo que $d_{\mathrm{met}}\in[0,1]$.

Cada trabajo recibe además una familia primaria $F_p$:

- `G`: juegos, mercados, subastas y formación de coaliciones;
- `H`: búsqueda, heurísticas, planificación y optimización combinatoria;
- `C`: control, consenso, seguridad e interacción física;
- `L`: política aprendida como mecanismo primario.

La distancia de familia y la distancia de alcance son

\[
d_{\mathrm{fam}}(p,q)=\mathbf 1[F_p\ne F_q],
\qquad
d_{\mathrm{SP}}(p,q)=1-\frac{|S_p\cap S_q|}{|S_p\cup S_q|},
\]

donde $S_p\subseteq\{\mathrm{SP0},\ldots,\mathrm{SP8}\}$ procede del ledger. La proximidad que gobierna la presentación es

\[
D(p,q)=0.50\,d_{\mathrm{met}}(p,q)
      +0.35\,d_{\mathrm{fam}}(p,q)
      +0.15\,d_{\mathrm{SP}}(p,q).
\]

La arquitectura conserva la mitad del peso; la familia del mecanismo forma los clústeres y el alcance SP solo refina vecindades. Estos pesos son una decisión descriptiva, no un ajuste estadístico.

Sea $a_p=0.82u_p$. Las coordenadas de presentación $z_p$ minimizan un estrés anclado:

\[
\begin{aligned}
Z^\star=\arg\min_{Z\in\mathcal Q}\quad
&\frac{2}{n(n-1)}\sum_{p<q}
  \left(\lVert z_p-z_q\rVert_2-1.55D(p,q)\right)^2\\
&+\frac{1.35}{n}\sum_p\lVert z_p-a_p\rVert_2^2
+\frac{200}{n(n-1)}\sum_{p<q}
  \left[0.18-\lVert z_p-z_q\rVert_2\right]_+^2\\
&+\frac{440}{n(n-1)}\sum_{p<q}
  \exp\!\left[-\left(\frac{z_{p,x}-z_{q,x}}{0.25}\right)^2\right]
  \left[0.18-|z_{p,y}-z_{q,y}|\right]_+^2.
\end{aligned}
\]

El primer término aproxima las distancias compuestas, el segundo conserva los ejes, el tercero evita oclusiones y el cuarto impide que puntos cercanos horizontalmente permanezcan en una misma fila visual. El conjunto $\mathcal Q$ mantiene cada punto en el cuadrante nominal, dentro de $[-1.10,1.10]^2$ y a distancia máxima $0.52$ de $a_p$ por componente. Se emplean tres inicializaciones deterministas y se conserva la de menor objetivo. La proyección se usa solo para presentación: dos trabajos con el mismo $y_p$ nominal pueden aparecer a diferente altura; la comparación exacta debe usar la tabla y $D(p,q)$.

## Familias primarias auditadas

| Familia | Trabajos del mapa |
|---|---|
| `G` juego/mercado | Bertsekas, Shehory, Vig, Zlot, IQ-ASyMTRe, CBBA, ACBBA, Dutta, Zhang, Shan y este TFM |
| `H` búsqueda/heurística | Hungarian, CBS/ECBS, LA-MAPF, MAPF-LNS2, Zhou, ML-LNS y GraphT |
| `C` control/consenso | Pereira, ORCA, Tsitsiklis, Olfati--Saber, Gossip, Ebel, Rosenfelder, Yoshikawa, Alonso--Mora y Ames |
| `L` política aprendida | RAILGUN, Paul, Shibata, PRIMAL, CACTUS, Shibata--LG y TIHDP |

La familia primaria describe el mecanismo que produce la decisión representada. Por eso ML-LNS y GraphT permanecen en búsqueda/heurística aunque contengan un módulo aprendido, mientras que Shibata, PRIMAL o RAILGUN pertenecen a política aprendida. La distancia expresa semejanza metodológica y de alcance: no es distancia de calidad, año, impacto ni rendimiento.

## Auditoría por trabajo

| Clave | Etiqueta | dec | loc | learn | exp | $(x_p,y_p)$ | Base de clasificación verificada |
|---|---|---:|---:|---:|---:|---:|---|
| `bertsekas1988Auction` | Bertsekas | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Subasta distribuible con precios; el artículo no acredita percepción robótica vecinal. |
| `pereira2004caging` | Pereira | 1 | 1 | 0 | 1 | $(-1,-1)$ | Algoritmo explícitamente descentralizado de caging. |
| `shehoryKraus1998Coalition` | Shehory | 1 | 1 | 0 | 1 | $(-1,-1)$ | Formación distribuida de coaliciones. |
| `vigAdams2006Coalition` | Vig | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Composición de coaliciones sin una garantía de ejecución vecinal completa. |
| `zlotStentz2006ComplexTasks` | Zlot | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Mercado/subasta de tareas complejas; el nivel de información no es puramente local. |
| `zhangParker2013IQASyMTRe` | IQ-ASyMTRe | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Síntesis de coaliciones ejecutables con configuración e información de tareas acopladas. |
| `choiBrunetHow2009CBBA` | CBBA | 1 | 1 | 0 | 1 | $(-1,-1)$ | Subasta descentralizada con consenso entre pares. |
| `johnson2011acbba` | ACBBA | 1 | 1 | 0 | 1 | $(-1,-1)$ | Consenso asíncrono sin rondas globales. |
| `vandenberg2011orca` | ORCA | 1 | 1 | 0 | 1 | $(-1,-1)$ | Optimización local a partir de vecinos. |
| `tsitsiklis1986asynchronousOptimization` | Tsitsiklis | 1 | 1 | 0 | 1 | $(-1,-1)$ | Iteraciones distribuidas y asíncronas. |
| `olfatiSaber2004switchingConsensus` | Olfati--Saber | 1 | 1 | 0 | 1 | $(-1,-1)$ | Consenso con topología conmutada y comunicación local. |
| `boyd2006randomizedGossip` | Gossip | 1 | 1 | 0 | 1 | $(-1,-1)$ | Intercambios de gossip entre vecinos. |
| `dutta2021hedonic` | Dutta | 1 | 1 | 0 | 1 | $(-1,-1)$ | Formación distribuida de coaliciones hedónicas. |
| `zhang2024coalition` | Zhang | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Juego de coaliciones; la fuente auditada no acredita una ejecución puramente vecinal. |
| `ebel2024cooperative` | Ebel | 1 | 1 | 0 | 1 | $(-1,-1)$ | Control y organización plenamente distribuidos. |
| `shan2024collectiveTransport` | Shan | 0.5 | 1 | 0 | 1 | $(-0.4,-1)$ | Subasta descentralizada con modo líder--seguidor. |
| `rosenfelder2024force` | Rosenfelder | 1 | 1 | 0 | 1 | $(-1,-1)$ | Arquitectura software distribuida y control de fuerza a bordo. |
| `kuhn1955Hungarian` | Hungarian | 0 | 0 | 0 | 1 | $(1,-1)$ | Oráculo central de asignación. |
| `yoshikawa1993coordinated` | Yoshikawa | 0 | 0 | 0 | 1 | $(1,-1)$ | Control coordinado con modelo global del objeto. |
| `alonsomora2017transport` | Alonso--Mora | 0 | 0 | 0 | 1 | $(1,-1)$ | Optimización restringida central/coordinada. |
| `sharon2015cbs` / `barer2014ecbs` | CBS/ECBS | 0 | 0 | 0 | 1 | $(1,-1)$ | Búsqueda MAPF central con estado global. |
| `li2019largeAgentMapf` | LA-MAPF | 0 | 0 | 0 | 1 | $(1,-1)$ | Planificación central para agentes de huella grande. |
| `li2022mapfLns2` | MAPF-LNS2 | 0 | 0 | 0 | 1 | $(1,-1)$ | Reparación central por búsqueda de vecindarios. |
| `ames2017cbf` | CBF-QP | 0.5 | 0.5 | 0 | 1 | $(0,-1)$ | Marco explícito; su arquitectura de ejecución depende de la implementación. |
| `zhou2026cttapf` | Zhou | 0 | 0 | 0 | 1 | $(1,-1)$ | Preprint con planificación discreta y global. |
| `huang2022mlLns` | ML-LNS | 0 | 0 | 0.5 | 0.5 | $(1,0)$ | ML selecciona vecindarios dentro de LNS explícito; arquitectura híbrida. |
| `yu2023graphTransformer` | GraphT | 0 | 0 | 0.5 | 0.5 | $(1,0)$ | Transformador como heurística dentro de CBS; arquitectura híbrida. |
| `tang2025railgun` | RAILGUN | 0 | 0 | 1 | 0 | $(1,1)$ | Política convolucional centralizada. |
| `paul2023collective` | Paul | 0 | 0 | 1 | 0 | $(1,1)$ | Política PPO sobre GNN para planificación centralizada de MRTA-CT. |
| `shibata2023event` | Shibata | 1 | 1 | 1 | 0.5 | $(-1,0.5)$ | MARL con control/consenso vecinal explícito. |
| `sartoretti2019primal` | PRIMAL | 1 | 1 | 1 | 0 | $(-1,1)$ | Política plenamente descentralizada aprendida para MAPF bajo observación parcial. |
| `phan2024cactus` | CACTUS | 1 | 1 | 1 | 0 | $(-1,1)$ | MARL ligero con políticas descentralizadas para MAPF. |
| `shibata2023localGlobal` | Shibata--LG | 0.5 | 0.5 | 1 | 0.5 | $(0,0.5)$ | Prioridades globales y política distribuida aprendida para asignación en transporte. |
| `naito2025tihdp` | TIHDP | 0.5 | 0.5 | 1 | 0.5 | $(0,0.5)$ | Capa intermedia global con asignación y control locales aprendidos. |
| `thisTFM` | Este TFM | 1 | 1 | 0 | 1 | $(-1,-1)$ | Alcance declarado: decisión vecinal y mecanismo white-box; no representa evidencia completa. |

## Evidencia y límites

- Las claves y las fuentes primarias se encuentran en `LITERATURE_LEDGER.md`, todas con estado `VERIFICADA`.
- Para `Paul`, `Shibata`, `Huang`, `Yu`, `Shan`, `Ebel` y `Rosenfelder` se revisó además la arquitectura declarada en las fuentes primarias/edición oficial durante la auditoría del 2026-07-16.
- `PRIMAL`, `CACTUS`, Shibata--LG y TIHDP se añadieron tras revisar fuente primaria o edición oficial el 2026-07-16. PRIMAL y CACTUS quedan en $y=1$ por dependencia aprendida primaria, mientras que las dos arquitecturas de transporte quedan en $y=0.5$ por su capa explícita/global intermedia.
- La auditoría del 2026-07-16 eliminó el bono léxico basado en palabras del título. Un título no altera las coordenadas; solo la arquitectura acreditada por el método determina `learn` y `exp`.
- No se infiere que un método sea distribuido por contener las palabras “multi-robot”, “auction” o “coalition”. Si la arquitectura de ejecución no está demostrada como local, se usa el nivel intermedio o central según la evidencia disponible.
