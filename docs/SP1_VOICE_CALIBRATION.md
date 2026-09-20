# SP1 — Calibración de voz

Tres pasajes reales reescritos antes de aplicar el criterio al capítulo entero.
El objetivo es acordar el registro, no todavía reescribir.

Criterio aplicado en los tres: **resultado y consecuencia; una sola limitación
por resultado; sin gestionar la lectura; sin autoevaluar.**

---

## 1. Apertura del capítulo

### Actual (p. 1) — 118 palabras, con recuadro destacado

> Antes de iniciar el transporte, SP1 determina qué robots móviles autónomos
> (AMR) forman la coalición asignada a cada carga. El capítulo responde una
> pregunta única:
>
> > ¿Cómo cambia el reclutamiento de coaliciones de AMR cuando se eliminan
> > progresivamente la homogeneidad de capacidad, la disponibilidad de
> > información global y la restricción a desviaciones unilaterales?
>
> Cada nivel aísla y elimina una fuente distinta de dificultad, y cada uno
> responde una subpregunta: **N1**, ¿cuándo basta la cardinalidad?; **N2**,
> ¿cuándo importa la capacidad individual de cada AMR?; **N3**, ¿qué cuesta
> eliminar la vista global?; **N4**, ¿qué orden local permite escapar de los
> mínimos unilaterales? N1--N3 delimitan las fronteras del problema; N4 contiene
> la contribución metodológica principal de SP1: una formulación de reclutamiento
> atómico mediante potencial local, jerarquía de desviaciones y confirmación
> vecinal. El movimiento físico comienza en SP2.

### Propuesta — 92 palabras, sin recuadro

> Antes de mover una carga hay que decidir qué robots móviles autónomos (AMR) se
> encargan de ella. Con capacidades iguales basta contarlos: el problema se
> reduce a una asignación por puestos que admite solución exacta. Cuando cada AMR
> aporta una capacidad distinta, la composición de la coalición entra en la
> decisión y esa reducción deja de valer.
>
> Las secciones siguientes retiran dos supuestos más. La tercera sustituye el
> estado global por mensajes vecinales y mide lo que cuesta. La cuarta estudia
> qué ocurre cuando ningún AMR puede mejorar por su cuenta pero un intercambio
> entre dos sí. SP2 recibe la coalición y decide si es físicamente realizable.

**Qué se eliminó.** El recuadro; «pregunta única»; la enumeración de
subpreguntas; «aísla y elimina una fuente distinta de dificultad»; «delimitan
las fronteras»; «contribución metodológica principal». El lector deduce la
estructura del orden de las secciones.

---

## 2. Resultado central de N4

### Actual (p. 22) — 104 palabras, cuatro capas de matización

> El primer escape conectado fue bilateral en 1\,156 de 1\,200 mundos (96,3 %) y
> trilateral en cuatro (0,3 %); en los 40 restantes (3,3 %) no se halló escape
> hasta $h=3$. La cifra indica en qué fracción de terminales BR ese primer escape
> fue bilateral; $h_c^\star$ localiza el primer orden en el que existe una
> mejora, y no mide su magnitud. El patrón es por tanto consistente con que $h=2$
> capture una parte importante de la mejora disponible, sin establecerlo por sí
> solo. N4.E4 confirma esa asociación en el banco estudiado: la brecha cae 40,9
> puntos entre BR y 2BR y solo 11,6 más entre 2BR y C3. Ambas observaciones,
> tomadas juntas, sostienen $h=2$ como punto de operación de F-I dentro de este
> dominio.

### Propuesta — 61 palabras

> Tras agotar BR, la primera mejora conectada fue bilateral en 1\,156 de los
> 1\,200 mundos y trilateral en cuatro. En los 40 restantes la búsqueda terminó
> en $h=3$ sin encontrarla.
>
> La brecha mediana siguió el mismo orden: 55,7 % con BR, 14,6 % con 2BR y 3,1 %
> con C3. La caída se concentra al admitir desviaciones bilaterales. Los
> experimentos posteriores emplean $h=2$.

**Qué se eliminó.** «La cifra indica»; «y no mide su magnitud»; «es por tanto
consistente con»; «sin establecerlo por sí solo»; «confirma esa asociación»;
«ambas observaciones, tomadas juntas, sostienen»; «punto de operación»; «dentro
de este dominio». La limitación —búsqueda truncada en $h=3$— se enuncia **una
vez**, en Limitaciones. El corte de párrafo rompe la cadencia declarativa.

---

## 3. Integralidad en N2

### Actual (p. 8) — 78 palabras

> La observación es más fuerte de lo que parece y conviene leerla junto a
> \eqref{eq:n1-lp-integral}: la integralidad no depende de que las capacidades
> sean iguales, sino de que el problema pueda escribirse por puestos. La
> cobertura ponderada de \eqref{eq:n2-milp} ya es fraccionaria incluso con
> capacidades homogéneas ---la brecha mediana medida en ese régimen fue
> 23,1 %--- porque un AMR puede repartirse entre cuotas. La heterogeneidad no
> rompe la integralidad: rompe la posibilidad de construir los puestos que la
> producían.

### Propuesta — 56 palabras

> La igualdad de capacidades no basta para que la relajación sea integral. Con
> $\mathrm{CV}=0$ la brecha mediana entre \eqref{eq:n2-milp} y su relajación fue
> del 23,1 %, porque un AMR puede repartirse entre varias cuotas. La integralidad
> de N1 procede de la formulación por puestos y de su matriz totalmente
> unimodular; con capacidades individuales esa formulación deja de existir.

**Qué se eliminó.** «La observación es más fuerte de lo que parece»; «conviene
leerla junto a»; el doble «no depende de… sino de…»; el «no rompe… rompe…» final,
que repite en forma quiástica lo ya dicho.

---

## 4. Reglas derivadas

1. Ningún párrafo empieza anunciando lo que va a hacer.
2. Un resultado, una limitación. Las demás van a Limitaciones.
3. Sin verbos que evalúan la propia evidencia: *sostener*, *respaldar*,
   *confirmar*, *demostrar contundentemente*.
4. Sin fórmulas de suspense ni de guía: *más fuerte de lo que parece*,
   *conviene*, *cabe*, *es importante*.
5. La cifra va antes que su interpretación, y a veces sin interpretación.
6. Romper la simetría: si tres conceptos se enuncian en paralelo perfecto, unir
   dos o separar en dos frases de longitud distinta.
7. Punto y coma sólo cuando une dos cláusulas de igual peso. En duda, punto.
8. Los pies de figura describen; no interpretan.

## 5. Alcance estimado

- ~65 % de los párrafos: edición ligera (retirar una o dos frases).
- ~25 %: reescritura real, sobre todo introducciones, transiciones y captions.
- ~10 %: intactos — demostraciones, definiciones y descripciones cuantitativas.

Las ecuaciones y los enunciados formales no se tocan.
