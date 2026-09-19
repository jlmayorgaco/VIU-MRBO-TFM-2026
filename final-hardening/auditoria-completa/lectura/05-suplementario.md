# Documento suplementario

**Criterio aplicado:** `pre-thesis/guidelines/05-checklist-por-fases.md`, FASE 27
(SUPPLEMENTARY) y FASE 26 (ANEXOS), más
`pre-thesis/guidelines/04-literatura-citas-y-referencias.md`, sección CO
(«Main vs supplementary»). Esos ficheros son la norma; aquí no se añade
criterio propio.

**Artefactos auditados**

| Artefacto | Contenido |
|---|---|
| `pre-thesis/supplementary/build/supplementary.pdf` | 113 páginas de PDF = 4 preliminares + 109 arábigas |
| `pre-thesis/supplementary/main.tex` | maestro; 6 `\input` de `sections/source-snapshot/`, 3 de `supplementary/sections/` |
| `pre-thesis/supplementary/sections/` | `formal-candidate-atlas.tex` (20 912 B), `epistemic-delta-gossip.tex`, `historical-e0-e1.tex` |
| `pre-thesis/build-v2/main-v2.pdf` | 146 páginas de PDF = 17 preliminares + 129 arábigas (comparador) |

**Convención de paginación.** En el suplementario, *página impresa = página del
PDF − 4*. En `main-v2.pdf`, *página impresa = página del PDF − 17*. Salvo
indicación expresa, en este informe los números son **páginas impresas** del
suplementario.

**Fecha de la auditoría:** 2026-09-19. No se modificó ningún fichero del TFM.

---

## Veredicto

**FALLA FASE 27 en cuatro de los seis puntos de eliminación obligatoria, y
FALLA el espíritu de la fase completa («debe complementar, no duplicar»).**
Cumple la sección CO sin reservas.

| FASE 27 — eliminar del PDF público | Estado | Dónde |
|---|---|---|
| `raw PASS/FAIL ledger` | **PRESENTE** | §5, pp. 73–81 (9 pp.) |
| hashes | **PRESENTE** | 1 SHA-256 de 64 hex, p. 73 |
| `semantic-all.csv` | **PRESENTE** | p. 73, citado como fuente de verdad |
| workflow del agente | ausente (1 resto) | ruta de repositorio en p. 25 |
| candidatos no ejecutados | **PRESENTE** | §5 completa (165–166 filas) y §6 (pp. 82–84) |
| «30 páginas copiadas del main» | **PRESENTE, 33 pp.** | ver §2 de este informe |

| FASE 27 — debe contener | Estado |
|---|---|
| pruebas extendidas | **SÍ** — §7, pp. 85–101 (17 pp.), la mejor parte del documento |
| datos adicionales | parcial — las tablas son las mismas que ya están en los anexos del main |
| sensibilidad | débil — ablaciones repetidas del main, no ampliadas |
| campañas históricas útiles | **SÍ** — §4.1, E0–E1, pp. 13–24 (12 pp. sin equivalente en el main) |
| detalles reproducibles | **SÍ** — protocolos y diseños experimentales completos |

| Sección CO — main vs supplementary | Estado |
|---|---|
| misma bibliografía o subconjunto coherente | **CUMPLE**: 72 claves citadas frente a 101 del main; 69 comunes, 3 propias (`fiorini1998velocity`, `karp1972reducibility`, `zhangParker2013Resources`), 0 divergentes |
| metadata idéntica / misma clave / mismas fechas | **CUMPLE**: ambos documentos cargan `bibliography/references.bib` + `bibliography/references-v2.bib`, `style=apa`, `backend=biber`, `sorting=nyt` |
| una sola `.bib` | **CUMPLE** (dos ficheros, pero los mismos dos en ambos documentos) |
| no citar arXiv en uno y journal en otro | **CUMPLE**: no hay ninguna clave divergente |

---

## 1. Estructura

### 1.1 Lista de secciones con extensión

| § | Título | Págs. impresas | Págs. PDF | Extensión |
|---|---|---|---|---|
| — | Portada | — | 1 | 1 |
| — | Índice | i–iii | 2–4 | 3 |
| 1 | Propósito y frontera de evidencia | 1 | 5 | <1 |
| 2 | Modelo común y estado del arte | 1–2 | 5–6 | 2 |
| 2.1 | Contrato entre decisión y transporte | 1 | 5 | — |
| 2.2 | Criterios de comparación | 2 | 6 | — |
| 3 | Marco teórico y estado del arte | 3–12 | 7–16 | **10** |
| 4 | Resultados técnicos conservados | 13–72 | 17–76 | **60** |
| 4.1 | Etapas históricas E0–E1: asignación y cuotas | 13–24 | 17–28 | 12 |
| 4.2 | SP1 canónico: capacidad y factibilidad mecánica | 25–40 | 29–44 | 16 |
| 4.3 | SP2 canónico: ejecución, seguridad y recuperación | 41–61 | 45–65 | 21 |
| 4.4 | SP3 canónico: rutas, red y piloto AWS | 62–72 | 66–76 | 11 |
| 5 | **Atlas de resultados formales candidatos** | 73–81 | 77–85 | **9** |
| 6 | Protocolo de la capa epistemológica delta | 82–84 | 86–88 | 3 |
| 7 | Demostraciones extendidas (7.1–7.34) | 85–101 | 89–105 | **17** |
| 8 | Referencias | 102–109 | 106–113 | 8 |

Inventario de flotantes: **18 figuras y 31 tablas**, numeradas 1–18 y 1–31, es
decir, renumeradas desde cero como si fueran las de un documento independiente.
De los 41 pies extraíbles, **17 (41 %) son literalmente idénticos a un pie de
`main-v2.pdf`** (medido sobre los pies de ≥25 caracteres).

### 1.2 ¿Suplemento o segunda tesis?

**Se lee como una segunda tesis más un libro mayor interno, no como un
suplemento.** La evidencia es estructural, no impresionista:

1. **Reproduce el esqueleto completo de una memoria.** Portada propia con
   título propio, índice de tres páginas con entradas hasta nivel `paragraph`,
   marco teórico y estado del arte completo (§3, 10 pp.), resultados (§4, 60 pp.),
   anexos de demostraciones (§7) y bibliografía propia de 8 pp. Falta solo el
   resumen. Un suplemento no vuelve a exponer el estado del arte.
2. **Renumera todo desde 1.** Figuras 1–18, tablas 1–31, proposiciones 4.10,
   4.11… El lector no puede citar «Tabla 29» sin ambigüedad, porque hay una
   Tabla 29 en cada documento y no son la misma.
3. **Solo 5 referencias explícitas al documento que supuestamente amplía**
   («memoria principal» / «memoria VIU»), todas en pp. 1 y 82. No hay una sola
   remisión del tipo «amplía la Sección 6.3 de la memoria». El suplemento no
   está anclado al main en ningún punto interno.
4. **El main apenas lo llama.** En `sections/v2/`, una sola frase remite al
   «material suplementario» (`appendix-megajuego-detail.tex:235`) y un
   comentario LaTeX. No hay entrada bibliográfica, DOI ni URL del suplemento.
   La promesa de `supplementary/main.tex:8` («Se cita desde main-v2.tex como
   Anexo 2 / referencia bibliográfica») **no está cumplida**.
5. **La numeración interna contradice los rótulos.** §4.2 se titula «SP1
   canónico» pero incluye `06-results-and-analysis/sp2.tex` y `sp3.tex`;
   §4.3 «SP2 canónico» incluye `sp4`–`sp6`. El propio `main.tex` avisa de ello
   («Los identificadores SP2–SP8 de esta sección son históricos»), lo que
   confirma que el documento se montó por copia de ficheros, no por redacción.
6. **§5 es un libro mayor interno**, no material académico (ver apartado 3).

Lo que sí funciona como suplemento legítimo: **§4.1 (E0–E1, 12 pp.)** y **§7
(demostraciones extendidas, 17 pp.)**, ambos con 0 % y 15 % de copia
respectivamente. Son 29 páginas de contenido real que no cabe en el main.

---

## 2. Duplicación respecto al documento principal

### 2.1 Método

1. Extracción de texto con PyMuPDF 1.2x (`page.get_text("text")`), por página,
   de los 146 pp. de `main-v2.pdf` y los 113 pp. de `supplementary.pdf`.
2. Normalización: NFC, eliminación de guiones blandos, **re-unión de palabras
   cortadas por guion al final de línea** (`-\n` → ∅), unificación de guiones
   Unicode y comillas tipográficas, colapso de todo espacio en blanco a un
   espacio simple, comparación en minúsculas.
3. **Exclusión de las bibliografías de ambos documentos** (main PDF 87–97,
   suplementario PDF 106–113). Sin esta exclusión las cifras suben ~2 puntos de
   forma espuria, porque las entradas APA comunes son literalmente idénticas
   por construcción.
4. Frases: corte en `[.!?]` seguido de espacio y mayúscula/apertura. **Frase
   larga = ≥80 caracteres** tras normalizar.
5. Párrafos: **reconstruidos a partir de la geometría de línea** (x0/x1 de cada
   línea frente a los márgenes modales del documento; una línea abre párrafo si
   la anterior terminó corta, si ella misma va sangrada, si cambia el cuerpo
   tipográfico, o si hay salto vertical >1,3 interlíneas). Se hace así porque
   los «bloques» que devuelve PyMuPDF en este PDF son **líneas sueltas**, no
   párrafos: usarlos directamente da 31 párrafos de ≥300 car. en 146 páginas,
   un artefacto. **Párrafo largo = ≥300 caracteres.**
6. Criterio de duplicado: la cadena normalizada aparece **literalmente** como
   subcadena del otro documento completo.
7. Contraste adicional con **8-gramas de palabras** (*shingles*), que tolera el
   reflujo de línea y la repaginación.

Guiones usados: `scratchpad/dup2.py`, `dup3.py`, `dup4.py`, `sections.py`
(no se versionan; son reproducibles con el método anterior).

### 2.2 Resultado principal

| Medida | Universo | Duplicado | % |
|---|---:|---:|---:|
| **Frases largas (≥80 car.) del main que aparecen literalmente en el suplementario** | 1 298 | 371 | **28,6 %** |
| **Párrafos largos (≥300 car.) del main que aparecen literalmente en el suplementario** | 206 | 50 | **24,3 %** |
| Masa de caracteres de párrafo del main duplicada | 258 365 | 76 642 | **29,7 %** |
| 8-gramas del main presentes en el suplementario | 39 943 | 11 907 | **29,8 %** |

Dirección inversa (qué parte del suplementario es copia):

| Medida | Universo | Copiado del main | % |
|---|---:|---:|---:|
| Frases largas del suplementario que ya están en el main | 1 100 | 347 | **31,5 %** |
| Párrafos largos del suplementario que ya están en el main | 148 | 54 | **36,5 %** |
| Masa de caracteres de párrafo copiada | 205 829 | 73 346 | **35,6 %** |
| 8-gramas del suplementario ya presentes en el main | 33 328 | 11 907 | **35,7 %** |

### 2.3 Verificación de la estimación externa previa

> Estimación externa: «≈25 % de frases largas y ≈14 % de párrafos largos».

- **Frases largas: confirmada, algo baja.** Medida propia **28,6 %**. La cifra
  es robusta al umbral: 27,3 % (≥40 car.), 27,9 % (≥60), **28,6 % (≥80)**,
  26,6 % (≥100), 25,7 % (≥120), 20,8 % (≥160). El 25 % externo cae dentro del
  rango pero por debajo del valor en el umbral declarado.
- **Párrafos largos: refutada. El 14 % es una infraestimación de casi la
  mitad.** Medida propia **24,3 %** con el umbral ≥300 car., y la cifra es
  estable: 23,9 % (≥150), 23,8 % (≥200), 24,0 % (≥250), **24,3 % (≥300)**,
  21,3 % (≥400).
  - El 14 % externo es el número que sale si se toman los «bloques» de PyMuPDF
    como si fueran párrafos, o si no se re-unen las palabras cortadas por guion
    al final de línea: ambos errores rompen la coincidencia literal justo en
    los párrafos más largos, que son los más copiados.
  - Con coincidencia tolerante a repaginación (≥80 % de 8-gramas compartidos),
    el párrafo largo duplicado sube a **38,8 %** (main) y **54,7 %**
    (suplementario). La caída del literal a 8,2 % en el umbral ≥500 car. es un
    artefacto de repaginación, no una señal de originalidad.

**Cifra para el informe: ~29 % de las frases largas y ~24 % de los párrafos
largos del documento principal están literalmente en el suplementario. En masa
de texto, 36 % del suplementario es copia del main.**

### 2.4 Peores infractores — por sección del suplementario

| § suplementario | Págs. | Frases largas | Copiadas del main | % |
|---|---|---:|---:|---:|
| **3. Marco teórico y estado del arte** | 3–12 | 131 | 106 | **81 %** |
| 2. Modelo común y estado del arte | 1–2 | 26 | 11 | 42 % |
| **4.3 SP2 canónico** | 41–61 | 245 | 110 | **45 %** |
| **4.4 SP3 canónico** | 62–72 | 128 | 49 | **38 %** |
| 1. Propósito y frontera de evidencia | 1 | 14 | 4 | 29 % |
| 4.2 SP1 canónico | 25–40 | 179 | 41 | 23 % |
| 7. Demostraciones extendidas | 85–101 | 197 | 29 | 15 % |
| 5. Atlas de candidatos | 73–81 | 18 | 1 | 6 % |
| **4.1 Etapas históricas E0–E1** | 13–24 | 140 | **0** | **0 %** |
| 6. Protocolo capa epistemológica delta | 82–84 | 29 | 0 | 0 % |

**§3 es el peor infractor con diferencia: 10 páginas cuyo 81 % de las frases
largas son copia literal del capítulo 5 del main.** Es además el caso menos
defendible, porque un suplemento no necesita repetir el estado del arte.

### 2.5 Peores infractores — por sección del main

| § main (pp. impresas) | Frases largas | Reaparecen en el suplementario | % |
|---|---:|---:|---:|
| **H. Detalle completo de SP2 (102–116)** | 172 | 118 | **69 %** |
| **I. Detalle completo de SP3 (117–122)** | 65 | 42 | **65 %** |
| **5. Marco teórico y estado del arte (19–33)** | 174 | 104 | **60 %** |
| **G. Detalle completo de SP1 (95–101)** | 78 | 43 | **55 %** |
| A–E. Anexos de demostraciones (81–87) | 81 | 31 | 38 % |
| 1. Introducción (1–5) | 52 | 7 | 13 % |
| 4. Metodología (11–18) | 102 | 8 | 8 % |
| F. Detalle de la revisión (88–94) | 82 | 6 | 7 % |
| J. Juego de integración (123–129) | 69 | 5 | 7 % |
| 6. Resultados y análisis (34–62) | 229 | 6 | 3 % |
| 2, 3, 7. Objetivos / Hipótesis / Conclusiones | 125 | 0 | 0 % |

**Lectura:** el cuerpo argumental del main (capítulo 6, conclusiones,
objetivos, hipótesis) **no** está duplicado. Lo que está duplicado es el
capítulo 5 y los anexos G/H/I —es decir, exactamente el material que la FASE 26
exige recortar de los anexos y que se decidió mover al suplementario **sin
retirarlo del main**. El resultado es que ese material está *dos veces en el
depósito*, no una vez en cada sitio.

### 2.6 Reparto página a página del suplementario

| Banda | Págs. impresas | Nº |
|---|---|---:|
| **≥50 % de sus frases largas copiadas** | 2–12, 28–29, 31–33, 42, 44–46, 53, 56–62, 65–67, 72, 94 | **33** |
| 1–49 % copiadas | 1, 27, 41, 43, 47, 54–55, 63–64, 69, 73, 90–91, 93, 95, 99–100 | 17 |
| 0 % copiadas (páginas originales) | preliminares, 13–26, 30, 34–40, 48–52, 68, 70–71, 74–89, 92, 96–98, 101 | 55 |

Solapamiento de 8-gramas por página, los picos: p. 9 (**96 %**), p. 12 (95 %),
pp. 5, 8 y 58 (94 %), pp. 3 y 57 (93 %), pp. 4, 11, 46 y 61 (92 %).

**La FASE 27 prohíbe «30 páginas copiadas del main». Hay 33 páginas con al
menos la mitad de su prosa copiada, y 50 con alguna copia literal.** El punto
está incumplido por encima del propio umbral que la directriz fija como
inaceptable.

### 2.7 Procedencia página a página (muestra)

| Supl. (impresa) | Copiadas | Origen en el main (PDF) |
|---|---|---|
| 2–12 | 7/12 … 6/7 | main PDF 34–45 (= cap. 5, pp. impresas 17–28) |
| 27–33 | 4/11 … 8/12 | main PDF 113–119 (= anexo H, SP2) |
| 41–47 | 4/13 … 3/11 | main PDF 119–124 |
| 53–67 | 6/11 … 3/11 | main PDF 125–136 |
| 65–67, 72 | 12/14, 7/13, 10/13 | main PDF 137–140 (= anexo J) |
| 90–95 | 1/12 … 8/11 | main PDF 98–102 (= anexos A–E) |

---

## 3. El atlas de candidatos formales (§5)

### 3.1 Extensión exacta

**Páginas impresas 73–81 = páginas 77–85 del PDF. Nueve páginas.** El título de
sección y el párrafo introductorio arrancan a media página 73, bajo el final de
§4.4.3; la Tabla 31 abre en la misma p. 73 y ocupa íntegras las pp. 74–81, con
«Continúa en la página siguiente» en ocho de ellas.

Contenido medido de la tabla:

| Magnitud | Valor |
|---|---|
| Filas con identificador recuperable | **165** (el texto declara 166) |
| Identificadores `PAPER-FR-nnnn-<label>` | 144 |
| Identificadores `THESIS-FR-nnnn-<label>` | 21 |
| Columnas | ID · Tipo · Veredicto · Destino · Título |
| Filas por página | 10 (p. 73), 22, 22, 21, 22, 20, 23, 18, 7 (p. 81) |
| Tokens `LIMITED` | 89 |
| Tokens `FAIL` | 45 |
| Tokens `PASS` | 20 |
| Tokens `DUPLICATE` (partido como `DUPLICA-TE`) | 18 |
| Tokens `CONJECTURE` | 4 |
| Tokens `archive-only` | 41 |
| Tokens `existing-active-claim` | 19 |
| Tokens `background-only` | 4 |
| Tokens `existing-active-result` | 2 |
| Tokens `monograph-candidate` (partido en `monograph-`/`candidate`) | ≈100 |
| Distribución declarada en prosa (p. 73) | CONJECTURE 2, DUPLICATE 16, FAIL 43, LIMITED 87, PASS 18 = 166 |

Además, en la p. 73:

- `semantic-all.csv` en tipografía monoespaciada, declarado como el sitio donde
  «permanecen» textos, supuestos, dominios, unidades y contraejemplos;
- `complete=true` en monoespaciada;
- el SHA-256 completo
  `b6416d52c9ce4cadec678285b16861687bbf20d08639ff4e1e63673dad807ef2`,
  partido en dos líneas.

### 3.2 Cómo lo lee un evaluador académico

Nueve páginas seguidas de una tabla de cinco columnas y ~20 filas por página, a
**7,9 pt** (el cuerpo del documento es 12 pt), con:

- **Identificadores que son etiquetas LaTeX crudas**: `PAPER-FR-0003-pr:degeneracion`,
  `THESIS-FR-0015-thm:sp6-feasible-nash`. Los dos puntos, los prefijos `pr:`,
  `thm:`, `le:`, `co:` y el conteo con relleno de ceros son vocabulario de
  repositorio, no de memoria.
- **Cinco tokens de veredicto en inglés y mayúsculas** dentro de un documento en
  español, uno de ellos partido por el guionado (`DUPLICA-TE`), lo que ya
  delata que el texto no se compuso, se volcó.
- **Una columna «Destino» con valores de máquina** (`monograph-candidate`,
  `archive-only`, `existing-active-claim`, `existing-active-result`,
  `background-only`) que describen un flujo de trabajo editorial privado del
  autor, no una propiedad del resultado matemático.
- **Títulos sin acentuar**: se contaron **154 palabras españolas sin tilde**
  dentro del atlas, entre ellas **84 apariciones de `proposicion`** —cero de
  «proposición»—, más `Caracterizacion`, `inanicion`, `Limite`, `Condicion`,
  `Regulacion`, `terminacion`, `descomposicion`, `friccion`… El resto del PDF
  está acentuado correctamente. Es la huella inequívoca de un volcado ASCII
  desde un CSV.
- **Un hash y un nombre de fichero** que el lector no puede abrir.

El efecto sobre un tribunal es doble y ambos lados son malos. Si lo lee, ve al
autor declarando por escrito que **43 de sus propios resultados formales han
fallado la auditoría y 87 están limitados**, sin poder comprobar ninguno de los
dos extremos porque el texto de los enunciados está en un CSV que no se
adjunta. Si no lo lee —lo más probable—, son nueve páginas que empujan el
documento hacia el tamaño de una segunda tesis sin aportar un solo argumento.
La sección **no cumple ningún punto de la lista «debe contener» de la FASE 27**
y cumple tres de la lista «eliminar».

### 3.3 Qué contendría el reemplazo de una página

Una página, sin tabla de filas individuales. Cinco piezas:

1. **Un párrafo de encuadre (4–5 frases).** Qué corpus se barrió (los
   enunciados formales de los borradores y del artículo en curso), con qué
   criterio se evaluó cada uno (enunciado + demostración *en su fuente*), y la
   regla que gobierna todo: **ningún resultado se promovió automáticamente; un
   resultado solo sostiene una afirmación de la memoria si además cruza con
   evidencia declarada**. Esta frase ya existe en el documento y es la única de
   §5 que merece sobrevivir.

2. **Una tabla de cinco filas**, una por clase de veredicto, en español, sin
   tokens en mayúsculas:

   | Resultado de la revisión | Nº | Qué significa | Qué se hizo |
   |---|---:|---|---|
   | Verificado | 18 | enunciado e hipótesis completos y demostración cerrada | los que sostienen una afirmación de la memoria se demuestran en §7; el resto queda fuera de su alcance |
   | Con frontera explícita | 87 | válido solo bajo supuestos que el enunciado declara | se conservan con su frontera; no sostienen afirmaciones generales |
   | Duplicado | 16 | reformulación de un resultado ya activo | remite al resultado canónico |
   | No sostenido | 43 | hipótesis insuficiente o paso no cerrado | retirado; no respalda ninguna conclusión |
   | Conjetura | 2 | sin demostración | declarado como trabajo futuro |

3. **La lista nominal de los 18 verificados**, en español, con título legible y
   la remisión exacta a dónde está demostrado cada uno («§7.11», «Anexo B.2 de
   la memoria»). Son los únicos 18 que el lector puede usar; hoy están
   escondidos entre 148 que no puede usar. Doce líneas.

4. **Una frase sobre el material retirado**, sin enumerarlo: cuántos resultados
   quedaron fuera y por qué el criterio fue conservador.

5. **Una línea de disponibilidad**: la tabla completa con enunciados, supuestos,
   dominios, contraejemplos y hashes se publica como conjunto de datos en el
   repositorio de reproducibilidad, citado por su DOI o URL. **El hash, el
   nombre `semantic-all.csv`, `complete=true`, los identificadores
   `PAPER-FR-*` y la columna «Destino» desaparecen del PDF** y viven en ese
   conjunto de datos, que es donde son útiles.

Ahorro: **9 páginas → 1**. Ganancia: el lector pasa de no poder verificar nada
a poder verificar dieciocho cosas.

---

## 4. Restos de lenguaje de taller (*pipeline*)

Barrido sobre las 113 páginas con el texto de-guionado y normalizado.

| Patrón | Ocurrencias | Páginas impresas |
|---|---:|---|
| `LIMITED` | 89 | 73–81 |
| `FAIL` | 45 | 73–81 |
| `archive-only` | 41 | 73–81 |
| `PASS` | 20 | 73, 75–78, 80–81 |
| `claim` / `claims` (en inglés) | 20 | 73–75, 78, 80–81 |
| `existing-active-claim` | 19 | 73–75, 78, 80–81 |
| `DUPLICATE` (incl. `DUPLICA-TE`) | 18 | 73–75, 78–81 |
| `monograph-candidate` | ≈100 | 73–81 |
| `background-only` | 4 | 73–75, 79 |
| `CONJECTURE` | 4 | 73, 77, 81 |
| `existing-active-result` | 2 | 80–81 |
| `ledger` | 1 | 81 |
| `complete=true` | 1 | 73 |
| `SHA-256` (literal) | 1 | 73 |
| Cadena hexadecimal de 64 caracteres | 1 | 73 |
| `semantic-all.csv` | 1 | 73 |
| Ruta de repositorio `evidence/generated-figures-manifest.json` | 1 | 25 |
| «humo acotado» | 1 | 1 |
| «veredicto» | 3 | 1, 8, 73 |
| `gate` | 0 | — |
| `artefacto` / `artifact` | 0 | — |
| `smoke` | 0 | — |
| `TODO` / `FIXME` | 0 | — |
| Otros `.csv`, `.py`, `.tex`, rutas `scripts/`, `src/` | 0 | — |

**Total: 372 ocurrencias contadas —con solapamiento entre patrones anidados
(`claim` dentro de `existing-active-claim`)—, de las cuales 368 (99 %) están
dentro del atlas de §5, pp. 73–81.** Retirar §5 resuelve prácticamente todo el
apartado. Los cuatro restos fuera del atlas son:

1. **p. 1** — «un **humo acotado** completó seis ejecuciones sin fallos de
   software». Calco de *smoke test* en la primera página del documento y en la
   frase que fija el alcance de la validación física. Debe decir «una ejecución
   de comprobación acotada» o «seis ejecuciones de verificación».
2. **p. 1** — «cada resultado mantiene… su **veredicto**»; **p. 73** — «El
   **veredicto** evalúa el enunciado». En p. 8, en cambio, «veredicto» se usa
   correctamente en sentido técnico («el certificado debe asociar su veredicto
   con una demanda de *wrench*»); esa ocurrencia no es un resto.
3. **p. 25** — «El manifiesto `evidence/generated-figures-manifest.json` enlaza
   cada PDF vectorial con el generador, la configuración, el manifiesto de
   corrida y sus hashes.» Es la única ruta de repositorio del documento. La
   frase es defendible como reproducibilidad, pero la ruta cruda debería ir al
   anexo de disponibilidad, no al cuerpo.
4. **p. 70** — «Los 450 registros no enumerados del oráculo permanecen marcados
   como **no ejecutados**, para 4500 filas totales.» Describe el estado de un
   fichero de resultados, no un hallazgo.

**No se encontró** ni `gate`, ni `artefacto`, ni `smoke`, ni rutas `scripts/`,
ni nombres de guiones `.py`: en eso el suplementario está más limpio que el
propio documento principal (cf. `mecanica/03-lenguaje-pipeline.md`).

---

## 5. Pseudocódigo roto

**El defecto sobrevive en el suplementario. Se corrigió en el main y no se
propagó a la copia.**

Causa: `\Return` de `algpseudocode` al principio de línea sin `\State` delante.
`\Return` no abre línea numerada, así que su texto se pega al final de la línea
anterior, o queda colgando sin número.

### 5.1 Fichero culpable

| Fichero | Líneas con `\Return` sin `\State` | Lo usa |
|---|---|---|
| `pre-thesis/sections/source-snapshot/mainmatter/06-results-and-analysis/cargo-e2e.tex` | 48, 53, **64**, **67** | **solo el suplementario** |
| `pre-thesis/sections/source-snapshot/mainmatter/06-results-and-analysis/sp7.tex` | **173** | **solo el suplementario** |
| `pre-thesis/sections/v2/support/cargo-e2e-v2.tex` | ninguna (corregido: `\State \Return`) | `main-v2.pdf` |
| `pre-thesis/sections/v2/support/sp3-e7-trimmed.tex` | 112 | `main-v2.pdf` |

### 5.2 Defectos renderizados en el suplementario

**Defecto 1 — p. 59 impresa (p. 63 del PDF), Algoritmo 1 «Demostrador Cargo
híbrido», línea 17.** Cadena exacta tal como se imprime:

```
17:      si nodevolver fallo de recuperación o agotamiento del horizonte
```

(`\Else` de `algpseudocode` en español imprime «si no»; el `\Return` de la
línea 64 del fuente se le pega sin espacio). En el main, la misma línea se
imprime correctamente en la p. 114 impresa / 131 del PDF:
`devolver fallo de recuperación o agotamiento del horizonte`.

**Defecto 2 — p. 59 impresa (p. 63 del PDF), Algoritmo 1, línea final.** Cadena
exacta:

```
         devolver entrega en pose destino
```

sin número de línea y sin sangría de bloque, colgando bajo la línea 17 (fuente:
`cargo-e2e.tex:67`). En el main la misma línea se imprime como
`21: devolver entrega en pose destino`.

**Defecto 3 — p. 65 impresa (p. 69 del PDF), Algoritmo 2 «Reserva vecinal y
avance discreto de una coalición (E7)», línea final.** Cadena exacta:

```
         devolver c+
                   i
```

sin número de línea (debería ser «15:»); fuente `sp7.tex:173`.

No aparece «entoncesdevolver» en el suplementario: las líneas 7 y 9 del
Algoritmo 1 se imprimen bien («si no se satisface (59) **entonces devolver**
abstención»), porque `\If{...}` sí abre línea numerada aunque falte el `\State`.
El defecto solo se materializa tras `\Else` y tras `\EndIf`.

### 5.3 Efecto colateral en el documento principal

El defecto 3 **también sigue en `main-v2.pdf`**, p. 120 impresa / **p. 137 del
PDF**: `devolver c+i` sin número de línea, desde
`sections/v2/support/sp3-e7-trimmed.tex:112`. La corrección del main cubrió
`cargo-e2e-v2.tex` pero no `sp3-e7-trimmed.tex`. Conviene anotarlo en el
informe del main.

---

## 6. Auditoría visual

### 6.1 Páginas vacías o desaprovechadas

| Pág. impresa | Pág. PDF | Ocupación vertical | Contenido |
|---|---|---:|---|
| 84 | 88 | **19 %** | seis líneas de cierre de §6; el resto en blanco |
| 0 (iii) | 4 | **25 %** | cola del índice: 7 entradas |
| **81** | **85** | **47 %** | siete filas del atlas + párrafo de cierre; media página en blanco |
| 101 | 105 | 64 % | cierre de §7.34 |
| 109 | 113 | 68 % | última página de bibliografía |
| — | 1 | 72 % | portada (normal) |

**La p. 81 es la más cara: media página desperdiciada solo para arrastrar siete
filas de una tabla que no debería existir.** La p. 84 es un `\clearpage` que
cuesta una hoja para seis líneas; se resuelve moviendo el cierre de §6 al pie de
la p. 83.

Ninguna página está completamente vacía. No hay páginas en blanco intercaladas.

### 6.2 Cuerpo tipográfico mínimo por página

| Cuerpo mínimo | Nº de páginas |
|---|---:|
| 2,6 pt | 1 |
| 3,4 pt | 1 |
| 3,7 pt | 1 |
| 4,0 pt | 1 |
| 4,8 pt | 1 |
| 4,9 pt | 1 |
| 5,0 pt | 3 |
| 6,0 pt | 38 |
| 6,3 pt | 1 |
| 7,0 pt | 1 |
| 7,5 pt (solo el folio y la cabecera) | 63 |
| 12,0 pt | 1 |

El suelo estructural de 7,5 pt corresponde a la cabecera corrida (autor +
título, 93 caracteres en todas las páginas): es uniforme y no es un defecto. Los
6,0 pt de 38 páginas son las llamadas de nota y los subíndices matemáticos.

### 6.3 Figuras con texto ilegible

| Pág. impresa | Pág. PDF | Figura | Cuerpo mínimo | Qué es ilegible |
|---|---|---|---|---|
| **26** | 30 | **Fig. 8** (E0: CPU / trabajo lógico / bienestar) | **2,6 pt** | leyenda de cinco métodos dentro del panel (a); rótulos de eje de los tres paneles a 3,1–3,7 pt |
| **26** | 30 | **Fig. 9** (E1, cierre y valor por presión de demanda) | 3,7 pt | leyenda inferior de seis series; rótulos de los cuatro paneles |
| **12** | 16 | **Fig. 4** (mapa metodológico del corpus) | **3,7 pt** | los ~40 rótulos de trabajo («Ebel 2024», «CBBA 2009», «Q-ASyMTRe 2013»…) y los años |
| **11** | 15 | Fig. 3 (retratos de fase, 4 paneles) | 6,3 pt | rótulos de vértice del símplex y ejes |
| **25** | 29 | Fig. 7 (cardinalidad de Nash / brecha) | 3,4 pt | rótulos de eje y leyenda |
| **40** | 44 | tabla ancha | 7,5 pt en todo el cuerpo | tabla compuesta entera a 7,5 pt (546 car.) |

Las tres primeras son fallos claros: **a 2,6–3,7 pt el texto no es legible ni en
pantalla al 200 % ni impreso en A4**, y las tres figuras afectadas son las que
sustentan las cifras de E0/E1 y el posicionamiento del TFM frente al corpus.
Son además **exactamente las tres figuras que solo existen en el
suplementario**: no hay versión legible en el main a la que remitir.

Corrección: exportar de nuevo con `figsize` mayor y cuerpo ≥7 pt, o partir la
Fig. 8 en tres figuras de un panel y sacar la leyenda de la Fig. 9 a un pie de
figura textual. La p. 26 tiene tres figuras apiladas; con dos por página el
problema se resuelve sin crecer en extensión.

### 6.4 Otros

- Índice de **tres páginas** con entradas hasta nivel `paragraph` (p. ej.
  «Caso base», «Síntesis» repetidos once veces). Para 109 páginas es excesivo y
  refuerza la lectura de «segunda tesis». Limitar a `subsection` deja el índice
  en una página y libera dos.
- No hay índice de figuras ni de tablas, pese a haber 18 y 31. Inconsistente con
  el main, que sí los tiene.
- La Tabla 31 no tiene «Fuente:», al contrario que las otras 30 tablas del
  documento.

---

## 7. Qué hacer

Por orden de rendimiento (páginas ahorradas y riesgo retirado por unidad de
esfuerzo):

| # | Acción | Efecto |
|---|---|---|
| 1 | **Sustituir §5 (pp. 73–81) por la página única del apartado 3.3.** | −8 pp.; retira 368 de las 372 ocurrencias de lenguaje de taller, el hash, `semantic-all.csv`, `complete=true` y las 154 palabras sin tilde. Resuelve además la p. 81 desaprovechada. |
| 2 | **Suprimir §3 (pp. 3–12) y remitir al capítulo 5 del main.** | −10 pp.; retira el bloque con 81 % de copia literal, el peor infractor de la FASE 27. |
| 3 | **Decidir, para §4.2–§4.4, qué versión es la buena.** Si el detalle vive en el suplementario, recortar los anexos G/H/I del main (pp. 95–122 impresas), que es lo que la FASE 26 pide de todos modos; si vive en el main, recortarlo aquí. Hoy está en los dos sitios. | −20 a −40 pp. en uno de los dos documentos; baja la duplicación del 29 % a un dígito. |
| 4 | **Añadir `\State` en `cargo-e2e.tex:48,53,64,67` y `sp7.tex:173`**, y de paso en `sp3-e7-trimmed.tex:112` para el main. | arregla los tres defectos de pseudocódigo del suplementario y el que queda en el main. |
| 5 | **Regenerar las Figs. 4, 7, 8 y 9 con cuerpo ≥7 pt.** | las únicas figuras exclusivas del suplementario pasan a ser legibles. |
| 6 | **Citar el suplementario desde el main** con entrada bibliográfica o DOI, como promete `supplementary/main.tex:8`, y añadir remisiones internas («amplía §6.3»). | convierte el documento en suplemento de algo, que es lo que la FASE 27 presupone. |
| 7 | Limitar el índice a `subsection`; mover el cierre de §6 al pie de la p. 83; poner «Fuente:» a la Tabla 31 o a lo que la sustituya. | −3 pp. |

Ejecutados 1–3 y 7, el documento pasa de **113 a ~70 páginas**, la duplicación
literal cae por debajo del 10 %, y lo que queda —§4.1 (E0–E1), §6, §7 y las
campañas SP1–SP3 que se decida conservar aquí— **sí** es lo que la FASE 27
describe: pruebas extendidas, campañas históricas útiles y detalles
reproducibles.
