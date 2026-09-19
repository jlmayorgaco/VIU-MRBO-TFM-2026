# Literatura, marco teorico, citas y referencias

> Parte de las directrices del TFM. Contenido copiado sin cambios de
> `GUIDELINES.md`, lineas 4674 a 7307. Indice en [`00-INDICE.md`](00-INDICE.md).

---

Sí. Esta debería ser una auditoría independiente de la revisión editorial general. Aquí la pregunta sería:

> **¿La tesis utiliza la literatura como lo haría un investigador serio: fuentes reales, relevantes, primarias cuando corresponde, correctamente interpretadas, citadas exactamente donde sostienen una afirmación, integradas críticamente en el argumento y referenciadas sin un solo error APA?**

Para tu TFM usaría un **Mega-checklist de Literatura, Marco Teórico, Fuentes, Citaciones y Referencias** con gates suficientemente estrictos como para que una fuente incorrecta, una cita que no sustente lo dicho o un DOI inventado hagan fallar la auditoría.

La base normativa es clara. Las instrucciones específicas del Máster VIU en Robótica exigen **APA 7.ª edición** para citas y referencias y dicen expresamente que todas deben ser correctas.  VIU también exige originalidad, citar las fuentes consultadas y advierte del uso de herramientas antiplagio.  Para el Marco Teórico pide teorías, conceptos y antecedentes; una revisión crítica del estado del arte; identificar limitaciones; explicar fundamentos; analizar tecnologías/enfoques existentes y relacionar las herramientas utilizadas con los objetivos.  Finalmente, exige una bibliografía completa en APA 7 que incluya bibliografía temática **y metodológica**.  Otras guías oficiales VIU refuerzan además la correspondencia exacta entre citas y referencias, orden alfabético y sangría francesa. ([VIU Universidad Online][1])

Con eso, este sería mi estándar.

---

# MEGA-CHECKLIST DE LITERATURA, MARCO TEÓRICO, CITACIONES Y REFERENCIAS

## A. Gate cero: ninguna referencia existe “porque sí”

Para **cada referencia de la tesis** debemos poder responder:

* [ ] ¿Existe realmente?
* [ ] ¿La hemos leído o inspeccionado suficientemente?
* [ ] ¿Sabemos exactamente qué afirmación sostiene?
* [ ] ¿Es la mejor fuente disponible para esa afirmación?
* [ ] ¿Es primaria o estamos citando una fuente secundaria innecesariamente?
* [ ] ¿La cita está situada junto a la afirmación que sustenta?
* [ ] ¿La tesis no dice más que la fuente?
* [ ] ¿Los autores son correctos?
* [ ] ¿El año es correcto?
* [ ] ¿El título es exacto?
* [ ] ¿El venue es correcto?
* [ ] ¿El volumen/número/páginas o article number son correctos?
* [ ] ¿El DOI pertenece realmente a ese documento?
* [ ] ¿El DOI resuelve?
* [ ] ¿Existe una versión publicada más reciente que el preprint?
* [ ] ¿Ha sido retractado o corregido?
* [ ] ¿La entrada APA está correcta?
* [ ] ¿Aparece en el texto?
* [ ] ¿Toda cita en texto tiene referencia?
* [ ] ¿Podría un jurado abrirla y encontrar lo que nosotros afirmamos?

Una sola respuesta “no sé” → **referencia pendiente**.

---

# B. Pregunta fundamental del Marco Teórico

El Marco Teórico de VIU no debe ser una colección de resúmenes. VIU exige analizar teorías, conceptos, antecedentes, tecnologías y limitaciones que justifiquen el estudio. 

Cada sección debe responder:

$$
\boxed{
\text{¿Qué necesita saber el lector para entender por qué mi solución tiene esta forma?}
}
$$

Revisar:

* [ ] ¿Cada teoría introducida se utiliza después?
* [ ] ¿Cada método discutido reaparece como fundamento, comparador o contraste?
* [ ] ¿Cada concepto contribuye a una RQ/OE/hipótesis?
* [ ] ¿Hay teoría incluida únicamente “porque es interesante”?
* [ ] ¿Hay libros enteros resumidos sin impacto posterior?
* [ ] ¿Hay literatura que pueda eliminarse sin cambiar ningún argumento?
* [ ] ¿Falta teoría necesaria para entender un teorema o experimento posterior?
* [ ] ¿El nivel de detalle es proporcional a su importancia?

VIU pide precisamente que los fundamentos ya propios del máster se presenten brevemente y que los nuevos o profundizados reciban mayor detalle. 

---

# C. Arquitectura intelectual del Marco Teórico

No organizarlo como:

> Autor A hizo X.
> Autor B hizo Y.
> Autor C hizo Z.

Organizarlo por **problemas y propiedades**.

Para tu TFM:

$$
\text{asignación/coalición}
\rightarrow
\text{información/juegos}
\rightarrow
\text{contacto/wrench}
\rightarrow
\text{transporte/control}
\rightarrow
\text{seguridad}
\rightarrow
\text{fallo/recuperación}
\rightarrow
\text{tráfico/red}
$$

Para cada bloque:

* [ ] Definir el problema.
* [ ] Identificar familias metodológicas.
* [ ] Explicar qué garantía entrega cada familia.
* [ ] Explicar qué información requiere.
* [ ] Explicar qué modelo físico supone.
* [ ] Explicar qué NO resuelve.
* [ ] Identificar trabajos más próximos.
* [ ] Terminar con la implicación concreta para tu diseño.

La última frase de cada subsection debería poder escribirse como:

> “Por esta razón, en este TFM se necesita ______.”

Eso convierte literatura en **argumento**.

---

# D. Fundamentos vs Estado del Arte

Separar conceptualmente:

### Fundamentos

Resultados relativamente estables:

* juegos potenciales;
* GNE/VI;
* consenso;
* MRTA;
* wrench/grasp map;
* CBF;
* MAPF;
* Lyapunov/pasividad.

Aquí interesa:

$$
\text{definición}
+
\text{teorema pertinente}
+
\text{supuestos}
+
\text{cómo lo utilizas}.
$$

### Estado del Arte

Trabajos concretos recientes que intentan resolver tu problema.

Aquí interesa:

$$
\text{problema}
+
\text{método}
+
\text{evidencia}
+
\text{limitación}
+
\text{diferencia con tu tesis}.
$$

No mezclar continuamente ambas funciones.

---

# E. Cada fundamento teórico debe tener una “ficha”

Para cada teoría importante:

* [ ] Nombre.
* [ ] Fuente fundacional.
* [ ] Fuente moderna/autoritaria si conviene.
* [ ] Definición.
* [ ] Supuestos.
* [ ] Resultado utilizado.
* [ ] Qué NO dice ese resultado.
* [ ] Adaptación hecha en el TFM.
* [ ] Qué hipótesis cambia la adaptación.
* [ ] Dónde se usa.
* [ ] Si se implementa o solo sirve de contexto.

Ejemplo conceptual:

**Juegos de potencial**

* Monderer & Shapley → fundamento.
* Sandholm → dinámica poblacional/contexto.
* Tu tesis → potencial particular.
* Demostrar tú mismo que tu payoff satisface identidad.
* No escribir “por Monderer-Shapley nuestro algoritmo converge” si esa convergencia requiere supuestos adicionales.

---

# F. Audit de “citation overreach”

Esta es una de las auditorías más importantes.

Para cada frase con cita:

> ¿La fuente realmente dice esto?

Clasificar:

### Nivel 1 — directo

La fuente demuestra/reportó exactamente la afirmación.

### Nivel 2 — síntesis razonable

La afirmación resulta de combinar varias fuentes.

Debe citar varias.

### Nivel 3 — inferencia del autor

Entonces escribir:

> “Esto sugiere…”
> “En este trabajo se interpreta…”
> “Estos resultados son compatibles con…”

### Nivel 4 — no sustentada

Eliminar o buscar evidencia.

---

# G. Una cita no debe sostener cuatro afirmaciones diferentes

Mal:

> X es distribuido, óptimo, robusto a pérdidas y escalable a 1000 robots (Autor, 2024).

Quizá el paper solo demuestra dos.

Mejor separar:

> X utiliza comunicación vecinal (Autor, 2024). En las instancias ensayadas alcanza… Sin embargo, el artículo no proporciona una garantía de optimalidad…

Checklist:

* [ ] Cada cita tiene objeto inequívoco.
* [ ] No queda al final de un párrafo con cuatro claims.
* [ ] Si varias fuentes sostienen distintos elementos, situarlas junto al elemento correspondiente.

---

# H. Verbos de atribución

Congelar una taxonomía.

### Si hay demostración formal

> demuestra
> establece
> prueba
> caracteriza

### Si hay experimento

> reporta
> observa
> obtiene
> evalúa

### Si es propuesta

> propone
> introduce
> formula
> plantea

### Si solo lo menciona

> describe
> documenta

### Si es interpretación nuestra

> sugiere
> es compatible con
> motiva

Nunca usar:

> “demuestra robustez”

para tres simulaciones.

---

# I. Jerarquía de fuentes

No todas las referencias tienen el mismo valor probatorio.

Para esta tesis usaría aproximadamente:

### Nivel A — evidencia científica primaria

* journal peer-reviewed;
* conference peer-reviewed de primer nivel;
* libros académicos de referencia.

En robótica, **ICRA/IROS/RSS/CoRL/etc. pueden tener enorme peso**; no asumir que journal > conference automáticamente.

### Nivel B — autoridad normativa/técnica

* ISO;
* ANSI/A3;
* VDA;
* documentación técnica oficial.

Adecuadas para:

> especificaciones, normas, interoperabilidad.

No para:

> demostrar rendimiento científico.

### Nivel C — preprints

* arXiv;
* TechRxiv.

Útiles para frontera reciente.

Pero marcar:

> preprint / no necesariamente peer-reviewed.

Si existe versión publicada:

$$
\boxed{\text{citar versión final}}
$$

salvo razón concreta para citar ambas.

### Nivel D — fabricante

Útiles para:

* producto;
* capacidad declarada;
* arquitectura anunciada;
* caso comercial.

Redactar:

> “El fabricante informa…”

No:

> “se ha demostrado…”

### Nivel E — patentes

Útiles para:

* actividad de protección;
* reivindicaciones;
* tendencias tecnológicas.

No prueban:

* despliegue;
* rendimiento;
* adopción;
* eficacia.

### Nivel F — blogs/Wikipedia/agregadores

Sirven para descubrir fuentes.

No deberían sostener claims científicos principales.

---

# J. Fuente primaria obligatoria cuando existe

Si dices:

> “CBBA garantiza…”

citar Choi et al., no un survey que menciona CBBA.

Si dices:

> “el Hungarian es polinómico…”

citar Kuhn/fuente matemática apropiada.

Si dices:

> “ORCA…”

citar van den Berg.

Si dices:

> “CBF…”

citar Ames y/o la fuente concreta utilizada.

Los reviews pueden utilizarse para:

* síntesis;
* taxonomía;
* contexto.

No para reemplazar sistemáticamente originales.

---

# K. Citation laundering

Buscar casos:

> Paper B dice que Paper A demostró X
> → nosotros citamos B como si B hubiera demostrado X.

Revisar.

Regla:

> Si el claim depende de A y A es recuperable, leer/citar A.

Purdue también recomienda que las fuentes secundarias se utilicen como tales, dejando claro que el original no fue consultado. ([Purdue OWL][2])

---

# L. SOTA real

Para cada tema central:

* [ ] clásico/fundacional;
* [ ] review reciente;
* [ ] 3–10 trabajos recientes realmente próximos;
* [ ] papers 2024–2026;
* [ ] trabajos adversariales que podrían invalidar nuestra brecha;
* [ ] literatura de grupos distintos.

No llenar 2026 solo por actualidad.

Un clásico relevante de 1995 puede ser mucho mejor que un paper superficial de 2026.

---

# M. Audit de actualidad

Para una tesis defendida en 2026:

* [ ] última búsqueda fechada;
* [ ] revisar 2025;
* [ ] revisar 2026 hasta fecha de cierre;
* [ ] buscar “online first”;
* [ ] buscar conference papers recientes;
* [ ] buscar publicados derivados de preprints que ya tenemos;
* [ ] verificar si un “gap” fue cerrado durante la escritura.

El estado del arte envejece.

El día de congelar la tesis haría una última búsqueda de:

> `multi-robot cooperative transport coalition formation`

y los conceptos específicos centrales.

---

# N. Audit de closest prior work

Construir una tabla privada de los **10–20 trabajos más peligrosos para la novedad**.

Columnas:

| Paper | Coalición dinámica | carga compartida | wrench | local | fallo/replacement | tráfico | hardware | garantía |
| ----- | ------------------ | ---------------- | ------ | ----- | ----------------- | ------- | -------- | -------- |

Después preguntar:

* [ ] ¿Cuál es el más parecido?
* [ ] ¿Qué hace que nosotros no?
* [ ] ¿Qué hacemos que él no?
* [ ] ¿La diferencia es realmente importante?
* [ ] ¿Es algoritmo, información, planta o garantía?
* [ ] ¿Estamos representándolo justamente?

Una tesis fuerte discute el rival más cercano, no el más fácil de superar.

---

# O. Literatura adversarial

Buscar deliberadamente papers que destruyan nuestra narrativa:

> “dynamic robot replacement cooperative transport”

> “distributed cooperative object transport heterogeneous robots”

> “coalition formation physical feasibility multi robot”

> “decentralized MPC cooperative transport”

> “multi robot transport failure recovery”

Si encuentras uno más cercano:

> actualizar la brecha.

Nunca esconderlo.

---

# P. Review balance

Evitar:

* 15 citas del mismo grupo;
* 12 referencias de un solo autor;
* autocitación artificial;
* exceso de un país/lab porque nuestra query favoreció cierto vocabulario.

Revisar diversidad de:

* grupos;
* métodos;
* perspectivas;
* años.

No por cuota política, sino para evitar **literature tunnel vision**.

---

# Q. Autocitas

Las propias publicaciones reales son citables si son relevantes.

Pero:

* [ ] no crear technical reports internos solo para citarlos;
* [ ] no citar “revisión matemática interna” como autoridad externa;
* [ ] no citar la propia tesis dentro de sí misma;
* [ ] no inflar bibliografía con artefactos internos.

Un resultado original del TFM:

> se presenta directamente.

No necesita autocita.

---

# R. Marco Teórico no debe anticipar resultados propios

Buscar frases:

> “como demostraremos…”

Está bien ocasionalmente.

Pero no llenar el review con:

> “nuestro método supera…”

El estado del arte debe permitir que la solución parezca **necesaria**, no predeterminada.

---

# S. No usar literatura para decorar

Mal:

> “La robótica es un campo en rápido crecimiento (A; B; C; D; E).”

Cinco citas sin función.

Toda cita debe hacer trabajo intelectual.

Preguntar:

> ¿Qué cambia si elimino esta cita?

Si nada:

> probablemente sobra.

---

# T. Citation dumping

Evitar:

> (A, 2017; B, 2018; C, 2019; D, 2020; E, 2021; F, 2022; G, 2023)

sin explicar diferencias.

Mejor:

> A y B abordan asignación; C y D añaden restricciones dinámicas; E introduce reemplazo…

Las citas se convierten en **síntesis**.

---

# U. Cada párrafo del Marco Teórico

Debe tener aproximadamente:

$$
\boxed{
\text{afirmación temática}
\to
\text{evidencia de literatura}
\to
\text{comparación/síntesis}
\to
\text{implicación para el TFM}
}
$$

No:

$$
\text{paper A}
\to
\text{paper B}
\to
\text{paper C}.
$$

---

# V. Conceptos comunes vs claims citables

No necesitas citar:

> “un robot posee posición y orientación”

si es mero contexto.

Sí debes citar:

* definiciones específicas;
* algoritmos;
* teoremas;
* estadísticas;
* capacidades de productos;
* resultados previos;
* normas;
* taxonomías;
* claims de novedad.

Evitar tanto la **subcitación** como la **sobrecitación**.

---

# W. Ecuaciones tomadas/adaptadas

Para cada ecuación que no es originalmente tuya:

* [ ] identificar origen;
* [ ] citar fuente;
* [ ] si está adaptada, decirlo;
* [ ] explicar cambios de símbolos;
* [ ] comprobar que los supuestos siguen siendo válidos;
* [ ] no atribuir a una fuente nuestra extensión.

Ejemplo:

> “Siguiendo la formulación de Ames et al. (2017), se particulariza la condición CBF al cuerpo compuesto…”

No fingir que la ecuación particular aparece literalmente en Ames.

---

# X. Teoremas de literatura

Para cada theorem importado:

* [ ] enunciado fiel;
* [ ] no eliminar hipótesis;
* [ ] no cambiar `joint connectivity` por `connected`;
* [ ] no cambiar tiempo continuo por discreto;
* [ ] no cambiar grafo dirigido por no dirigido;
* [ ] no cambiar convexidad por no convexidad;
* [ ] no transferir guarantee a una modificación.

En tu TFM esto es especialmente crítico en:

* consenso;
* primal-dual;
* juegos poblacionales;
* CBF;
* MAPF;
* estabilidad.

---

# Y. Adaptaciones de algoritmos

Si modificamos CBBA, ORCA, Smith, etc.:

No decir:

> “CBBA obtiene…”

si implementamos una adaptación.

Escribir:

> **“adaptación inspirada en CBBA”**

y citar original.

Separar:

$$
\text{garantía del paper}
\neq
\text{garantía de nuestra adaptación}.
$$

---

# Z. Literatura comercial

Para cada empresa:

* [ ] fuente oficial;
* [ ] fecha;
* [ ] producto exacto;
* [ ] qué afirma el fabricante;
* [ ] qué observamos nosotros;
* [ ] no añadir funciones no documentadas;
* [ ] no interpretar marketing como prueba independiente.

Verbos:

> “documenta”
> “declara”
> “describe”

No:

> “demuestra”.

---

# AA. Normas

Cada norma:

* [ ] organismo oficial;
* [ ] número exacto;
* [ ] año/edición;
* [ ] estado vigente;
* [ ] título exacto;
* [ ] alcance;
* [ ] qué excluye;
* [ ] URL oficial;
* [ ] fecha de consulta si es página dinámica.

No usar un blog para explicar ISO si la página oficial existe.

---

# AB. Patentes

Para un patent:

* [ ] publication/application/grant number correcto;
* [ ] jurisdiction;
* [ ] assignee;
* [ ] inventors;
* [ ] priority/publication date;
* [ ] familia;
* [ ] no duplicar misma invención como patentes distintas sin aclararlo.

Y en narrativa:

> “reivindica…”

No:

> “implementa exitosamente…”

---

# AC. Fuentes de datos y bibliometría

OpenAlex/Crossref/Google Patents sirven como **fuentes de datos**, no como fuentes del contenido científico de un paper.

Distinguir:

> metadata source

de:

> scientific source.

Citar correctamente el dataset/API si sus datos sustentan una figura.

---

# AD. DOI audit

Para todos los artículos con DOI:

$$
\boxed{
\text{DOI}\rightarrow\text{publisher metadata}
}
$$

Verificar automáticamente:

* author list;
* title;
* year;
* journal;
* volume;
* issue;
* pages/article number.

Si uno no coincide:

> FAIL.

No copiar DOI de Semantic Scholar sin validar.

---

# AE. URLs

APA 7 trata DOI y URL como enlaces. Ya no utiliza `DOI:` antes del identificador; se usa:

> `https://doi.org/...`

([Purdue OWL][3])

Revisar:

* [ ] HTTPS.
* [ ] sin trackers.
* [ ] sin `utm_source`.
* [ ] sin sesión.
* [ ] fuente estable.
* [ ] publisher > agregador.
* [ ] DOI > URL de journal cuando DOI existe.

---

# AF. Fechas de recuperación

APA 7 generalmente **no exige fecha de recuperación para contenido estable**; se reserva principalmente para recursos que pueden cambiar con el tiempo. ([Purdue OWL][4])

Por tanto:

No:

> “Consultado el…” para cada journal article.

Sí puede tener sentido para:

* páginas de producto;
* estándares “under publication”;
* wikis/dashboards actualizables;
* páginas web sin versión archivada.

---

# AG. Autores en APA 7 — lista de referencias

Este punto ya afecta tu tesis actual.

En referencias:

* hasta **20 autores** → escribirlos.
* **NO usar `et al.`** en una entrada ordinaria de hasta 20 autores.
* si >20 → primeros 19, …, autor final.

([Purdue OWL][3])

Por tanto entradas como:

> `Fukao, T., et al.`

son candidatas directas a corrección.

---

# AH. Autores en citas dentro del texto

APA 7:

### Un autor

> Pérez (2024)
> (Pérez, 2024)

### Dos autores

Narrativa:

> Pérez y Gómez (2024)

Parentética:

> (Pérez & Gómez, 2024)

### Tres o más

Desde la **primera cita**:

> Pérez et al. (2024)

> (Pérez et al., 2024)

salvo necesidad de desambiguación. ([Purdue OWL][5])

---

# AI. `et al.`

Reglas:

* `et` sin punto.
* `al.` con punto.
* no cursiva.
* siempre representa más de un autor omitido.

Correcto:

> Smith et al. (2025)

Incorrecto:

> Smith et. al
> Smith et al
> Smith *et al.*

---

# AJ. Autores institucionales

Primera aparición, si después usarás sigla:

> International Organization for Standardization (ISO, 2023)

Después:

> ISO (2023)

Parentética inicial:

> (International Organization for Standardization [ISO], 2023)

Después:

> (ISO, 2023)

No inventar siglas poco conocidas solo para ahorrar palabras.

---

# AK. Mismo autor, mismo año

Si existen:

> Smith (2025a)
> Smith (2025b)

las letras deben corresponder al orden de las entradas según APA.

El `.bib` debe producirlas automáticamente.

No asignarlas manualmente a ojo.

---

# AL. Autores con mismo apellido

Desambiguar con iniciales cuando APA lo exige.

Evitar que:

> J. Zhang
> Y. Zhang

se conviertan ambos simplemente en:

> Zhang (2024)

si genera ambigüedad.

---

# AM. Múltiples fuentes en una misma cita

Orden coherente con APA, normalmente alfabético por primer autor dentro del mismo paréntesis:

> (Ames et al., 2017; Choi et al., 2009; Sandholm, 2010)

No ordenarlas según “cuál me gusta más”.

---

# AN. Cita directa

Purdue resume la regla APA:

si se cita textualmente, se añade localizador/página. ([Purdue OWL][6])

En este TFM yo **minimizaría drásticamente las citas textuales**.

Robótica/ingeniería se beneficia más de:

> paráfrasis exacta + referencia.

Las citas literales son necesarias solo si:

* la formulación exacta importa;
* una norma define algo;
* una afirmación comercial específica debe preservarse.

---

# AO. Citas largas

APA usa cita en bloque para citas textuales largas (40 palabras o más).

Para este TFM:

> casi ninguna debería ser necesaria.

Un bloque de 100 palabras de otro paper dentro del marco teórico suele ser síntoma de que falta síntesis.

---

# AP. Paráfrasis

Parafrasear NO es:

> cambiar sinónimos manteniendo la misma estructura.

Debe:

1. comprender la fuente;
2. cerrar la fuente;
3. reconstruir la idea desde nuestro argumento;
4. citar.

Turnitin puede detectar proximidad incluso aunque cambies unas pocas palabras.

---

# AQ. Plagio conceptual

También existe cuando:

* tomamos una taxonomía;
* una idea;
* una estructura;
* un argumento;
* una figura;

y no atribuimos.

No basta con que las palabras sean nuestras.

VIU exige explícitamente evitar contenido ajeno sin referenciar y utiliza antiplagio. 

---

# AR. Figuras y tablas derivadas de literatura

VIU exige procedencia/fuente de las ilustraciones. 

Clasificar:

### 1. Completamente propia

> Fuente: elaboración propia.

### 2. Datos externos, visualización propia

> Fuente: elaboración propia a partir de datos de X (2025).

### 3. Adaptación conceptual

> Adaptado de X (2025).

### 4. Reproducción

> Reproducido de X…

Y revisar licencia/permiso cuando proceda.

Nunca escribir:

> “Elaboración propia”

si en realidad redibujamos casi exactamente una figura ajena.

---

# AS. Captions con referencias

* [ ] cita en caption/note si figura deriva de fuente;
* [ ] la fuente está en Referencias;
* [ ] no depender solo de una cita perdida 2 párrafos antes;
* [ ] copyright/licencia si es necesario.

---

# AT. Referencias metodológicas

VIU dice explícitamente que la bibliografía debe cubrir **tema de investigación y metodología**. 

Por tanto debemos citar también:

* bootstrap;
* McNemar;
* Wilcoxon si se justifica metodológicamente;
* Holm;
* quizá Friedman;
* simuladores/software especializado;
* métodos numéricos relevantes;
* algoritmo exacto utilizado.

No necesitas citar matemáticas elementales.

Pero sí las metodologías científicas que fundamentan decisiones importantes.

---

# AU. Software

APA 7 permite/recomienda referenciar software especializado; no hace falta citar lenguajes o software ofimático estándar. ([Purdue OWL][7])

Para tu tesis revisar:

* CoppeliaSim;
* MuJoCo si finalmente se usa;
* HiGHS;
* solver particular;
* software científico cuyo comportamiento sea metodológicamente importante.

No llenar referencias con:

* Python;
* Word;
* Git.

salvo exigencia metodológica específica.

---

# AV. Datasets

Si un dataset externo sustenta un resultado:

* autor/organización;
* año;
* título;
* versión;
* descriptor `[Data set]`;
* repositorio;
* DOI/URL.

Además, explicar exactamente qué parte se utilizó.

---

# AW. Preprints / arXiv

Formato conceptual APA:

> Autor(es). (Año). *Título* [Preprint]. arXiv. URL

Pero antes:

* [ ] buscar versión journal/conference.
* [ ] comprobar fecha.
* [ ] no presentar peer-review si no existe.
* [ ] si versión publicada existe, preferirla.

---

# AX. Artículos de revista — plantilla

APA 7 básica:

> Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Journal Title, volume*(issue), pages/article number. [https://doi.org/](https://doi.org/)...

Purdue confirma la estructura y que el DOI debe incluirse cuando existe. ([Purdue OWL][8])

Revisar:

* título del artículo en sentence case;
* journal y volumen en cursiva;
* issue entre paréntesis;
* DOI.

---

# AY. Libros

Forma básica APA:

> Author, A. A. (Year). *Title of book*. Publisher.

Ya no se incluye ciudad del editor. ([Purdue OWL][9])

---

# AZ. Capítulos de libro

Conceptualmente:

> Author, A. A. (Year). Title of chapter. In E. E. Editor (Ed.), *Title of book* (pp. xx–xx). Publisher.

No confundir autor del capítulo con editor.

---

# BA. Conference papers

Aquí debemos ser cuidadosos porque en robótica son muy importantes.

Determinar primero:

* ¿paper publicado en proceedings?
* ¿solo presentación?
* ¿extended abstract?
* ¿paper con DOI?

No usar una sola plantilla ciegamente.

Purdue señala que proceedings requieren adaptar el formato según cómo estén publicados. ([Purdue OWL][2])

Lo importante:

* autores;
* año;
* título;
* conference/proceedings;
* pages/article;
* publisher si aplica;
* DOI.

---

# BB. Tesis

Formato APA típico para tesis publicada:

> Author, A. A. (Year). *Title* [Master’s thesis/Doctoral dissertation, University]. Repository/URL.

Purdue ofrece precisamente este esquema. ([Purdue OWL][2])

---

# BC. Informes técnicos

> Organization/Author. (Year). *Title of report*. Organization. URL

Si autor y publisher son la misma organización, revisar regla APA para evitar duplicación innecesaria.

---

# BD. Webpage

Conceptualmente:

> Author/Organization. (Date). *Title of page*. Site. URL

Pero:

* si autor = site, no duplicar innecesariamente;
* usar fecha real;
* si no existe fecha, usar convención coherente `s. f.`/`n.d.` según localización adoptada;
* retrieval date solo si contenido cambia.

---

# BE. Fuente corporativa

Ejemplo conceptual:

> AGILOX. (2024). *Título de la página/caso*. URL

Pero narrativamente:

> “AGILOX informa…”

No:

> “Se ha demostrado…”

---

# BF. Normas técnicas

Para ISO:

> International Organization for Standardization. (Year). *Title of standard* (ISO Standard No. xxxx:year). URL

Auditar siempre contra la página oficial.

---

# BG. Patentes

No tratar como artículo.

Verificar:

* inventores;
* año;
* título;
* número;
* autoridad;
* URL.

Y distinguir:

> 申请/application
> publicación
> grant.

---

# BH. Estado de publicación

Etiquetar correctamente:

* Published.
* Early access.
* Accepted.
* In press.
* Preprint.
* Under publication.
* Draft standard.

No convertir:

> “under publication”

en:

> “norma publicada”.

---

# BI. Retractions y corrections

Para cada paper central:

* [ ] buscar retraction;
* [ ] expression of concern;
* [ ] correction/erratum;
* [ ] nueva versión.

Especialmente papers 2025–2026.

Una fuente retractada no debe sostener un claim sin explicar el problema.

---

# BJ. Predatory venue audit

Para fuentes desconocidas:

* publisher;
* peer-review;
* indexing;
* editorial board;
* DOI;
* venue history.

No excluir automáticamente venue nuevo.

Pero no usar un journal dudoso como pilar si existe literatura sólida.

---

# BK. Quality ≠ citation count

No elegir papers solo porque tienen muchas citas.

Para trabajos recientes:

$$
\text{calidad}
\neq
\text{Google Scholar citations}.
$$

Priorizar:

* proximidad al problema;
* rigor;
* evidencia;
* reproducibilidad;
* relevancia.

---

# BL. Evidence-type tagging

Yo etiquetaría internamente cada referencia:

* `THEORY`
* `ALGORITHM`
* `EXPERIMENTAL`
* `REVIEW`
* `STANDARD`
* `INDUSTRIAL`
* `PATENT`
* `DATA`
* `SOFTWARE`

Después comprobar:

> ¿estamos utilizando una fuente INDUSTRIAL como THEORY?

Si sí:

> problema.

---

# BM. Claim-type tagging

Igualmente cada cita debería sostener uno de:

* definición;
* existencia;
* optimalidad;
* convergencia;
* estabilidad;
* seguridad;
* rendimiento;
* complejidad;
* implementación;
* caso industrial;
* norma.

Eso permite detectar transferencias indebidas.

---

# BN. Literature-to-claim matrix

Crear:

| Claim | Source | Exact support | Source type | Direct/indirect | Strength | Page/section |
| ----- | ------ | ------------- | ----------- | --------------- | -------- | ------------ |

Por ejemplo:

> “ORCA proporciona semiplanos recíprocos”
> van den Berg et al.
> direct
> primary algorithm.

Pero:

> “ORCA garantiza seguridad de Cargo rígido”

quizá:

> **NO SUPPORT**.

---

# BO. Page/equation locator interno

APA no exige páginas para paráfrasis.

Pero para nuestra auditoría privada yo registraría:

* página;
* ecuación;
* theorem;
* sección;

de las fuentes centrales.

Así, si el jurado pregunta:

> “¿Dónde dice esto Ames?”

puedes responder.

---

# BP. Reference-to-text correspondence

VIU insiste en bibliografía completa, y otras guías VIU especifican correspondencia exacta entre citas y referencias. ([VIU Universidad Online][1])

Gate automático:

$$
C=\{\text{citation keys usados}\}
$$

$$
R=\{\text{references impresas}\}
$$

Exigir:

$$
\boxed{C=R}
$$

Operativamente, esa es la opción más segura.

Si una fuente fue “consultada” pero nunca influye materialmente en el texto, no tiene mucho valor engordar la bibliografía; si sí influyó, cítala en el lugar correspondiente. Así cumples tanto la guía específica del máster como la correspondencia exacta.

---

# BQ. Referencias huérfanas

Detectar:

$$
R-C.
$$

Cada entrada que nunca se cita:

* citar donde realmente se usa;
* o eliminar.

Nada de bibliografía decorativa.

---

# BR. Citas huérfanas

Detectar:

$$
C-R.
$$

Cualquier key sin referencia:

> P0.

---

# BS. Duplicados bibliográficos

Detectar:

* mismo DOI;
* mismo title;
* arXiv + final paper;
* variante abreviada de autor;
* conference + preprint idéntico.

Decidir cuál debe citarse.

No contar dos veces el mismo trabajo como dos precedentes independientes.

---

# BT. Normalización de nombres

Especial atención:

* apellidos compuestos;
* partículas `de`, `van`, `von`;
* nombres españoles;
* ORCID metadata;
* tildes;
* guiones.

No dejar:

> Barreiro-Gómez

en una entrada y:

> Barreiro Gómez

en otra si es el mismo autor.

---

# BU. Capitalización

APA:

Artículos/libros:

> sentence case.

Journal:

> Title Case según nombre oficial.

Acrónimos propios:

> conservar.

No usar Title Case estadounidense indiscriminadamente en títulos de papers en las entradas.

---

# BV. Cursivas

Normalmente:

* journal name → cursiva;
* volume → cursiva;
* book/report completo → cursiva;
* article/chapter → no cursiva;
* issue → no cursiva.

Auditar automáticamente el `.bbl`/PDF final.

---

# BW. Orden alfabético

VIU también lo recomienda explícitamente en sus guías. ([VIU Universidad Online][1])

Revisar:

* autores;
* organizaciones;
* misma autoría;
* mismo año;
* `a/b/c`.

No ordenar por orden de aparición.

---

# BX. Sangría francesa

APA:

$$
0.5\text{ inch}\approx1.27\text{ cm}
$$

en líneas posteriores de cada referencia. Purdue también lo especifica. ([Purdue OWL][10])

Verificar visualmente.

---

# BY. DOI vs URL

Si DOI existe:

$$
\boxed{\text{usar DOI}}
$$

normalmente no necesitas además URL de publisher.

No:

> DOI + URL + Google Scholar URL.

---

# BZ. URLs rotas

Automatizar HEAD/GET cuando sea razonable:

* 200/redirect válido;
* no 404;
* no login obligatorio si existe alternativa;
* DOI resuelve.

No asumir que porque aparece azul funciona.

---

# CA. Citas al final del párrafo

Buscar párrafos de literatura con una sola cita al final y muchas afirmaciones.

Pregunta:

> ¿Qué parte sostiene exactamente esa cita?

Mover referencias a las frases adecuadas.

---

# CB. “Cita flotante”

Mal:

> “…como se ha demostrado. (Smith, 2022)”

Corregir integración gramatical.

---

# CC. Citas dentro de ecuaciones/figuras

Evitar meter `(Smith, 2022)` dentro de una expresión matemática.

Citar en la frase introductoria:

> “Siguiendo a Smith (2022), se define…”

---

# CD. Citas dentro de títulos

Evitar headings como:

> “Control basado en Ames et al. (2017)”

Mejor:

> “Control mediante funciones de barrera”

y citar en el texto.

---

# CE. Demasiadas autocitas a un mismo paper

Si un párrafo completo discute un único trabajo, no es necesario citarlo al final de cada oración, siempre que no haya ambigüedad.

Pero la atribución debe seguir clara.

---

# CF. Citas de review como acceso a 20 papers

Un review puede sostener:

> “existen varias familias…”

Pero si después afirmamos características específicas de un método:

> volver al paper original.

---

# CG. Citation chains en claims de novedad

Para un claim:

> “ningún trabajo integra A+B+C”

no basta citar 5 papers.

Necesitas:

* protocolo de búsqueda;
* conjunto examinado;
* matriz de capabilities;
* formulación condicionada:

> “No se identificó…”

Nunca:

> “No existe…”

---

# CH. Gap statement audit

Para cada brecha:

* [ ] población/corpus.
* [ ] fecha de corte.
* [ ] dimensiones exactas.
* [ ] trabajos más cercanos.
* [ ] qué les falta.
* [ ] limitación del claim.

La brecha es una conclusión del review, no una impresión.

---

# CI. Revisión del corpus

El corpus debe documentar:

* bases;
* queries;
* fecha;
* filtros;
* deduplicación;
* etapas;
* lectura de full-text;
* inclusión/exclusión;
* snowballing.

Y distinguir:

$$
\text{descubiertos}
\neq
\text{screened}
\neq
\text{full text}
\neq
\text{canonical}
\neq
\text{close reading}.
$$

---

# CJ. Bias audit del review

Reconocer:

* disponibilidad OA;
* cobertura de bases;
* inglés/español;
* keywords;
* clasificación humana/automática;
* recency;
* patentes;
* corporate sources.

Eso aumenta credibilidad.

---

# CK. Uso de citas en Resultados

Los Resultados propios no necesitan una referencia para existir.

Pero la interpretación sí puede compararse:

> “A diferencia de X…”

Cuidado con llenar Resultados de literature review.

---

# CL. Discusión con literatura

Una buena discusión hace:

$$
\text{nuestro resultado}
\rightarrow
\text{estudio previo}
\rightarrow
\text{coincidencia/diferencia}
\rightarrow
\text{explicación}.
$$

No repetir estado del arte.

---

# CM. Fuente de comparadores

Cada baseline debe tener:

* referencia original;
* versión implementada;
* diferencias de nuestra adaptación.

Si es una baseline propia:

> declararlo.

---

# CN. Referencias en conclusiones

Idealmente muy pocas.

Conclusiones derivan de tus resultados.

Solo citar si comparas explícitamente con literatura.

Una conclusión repleta de 15 nuevas referencias indica que la discusión llegó demasiado tarde.

---

# CO. Main vs supplementary

* misma bibliografía o subset coherente;
* metadata idéntica;
* misma key;
* mismas fechas;
* no citar una versión arXiv en uno y journal en otro sin razón.

Idealmente una sola `.bib`.

---

# CP. Language consistency

Como tesis española:

* APA metadata originales no se traducen arbitrariamente;
* títulos de artículos se mantienen como publicados;
* nombre del journal original;
* “et al.” igual;
* DOI igual.

No traducir títulos científicos ingleses en la referencia salvo regla específica.

---

# CQ. Traducciones de conceptos

Si traduces en el texto:

> “control barrier function (CBF), función de barrera de control…”

citar fuente original.

Pero la referencia sigue con el título original del paper.

---

# CR. AI como buscador, no fuente

Ningún claim científico debería depender de:

> “ChatGPT dice que…”

Si una herramienta de IA encuentra una referencia:

1. abrir referencia;
2. comprobar metadata;
3. leer material relevante;
4. citar fuente real.

Una referencia inventada por un LLM es **P0 absoluto**.

---

# CS. Audit antifake-reference

Automatizar para cada entrada:

1. DOI resuelve.
2. Título coincide.
3. Primer autor coincide.
4. Año coincide.
5. Journal coincide.

Si sin DOI:

* buscar publisher/venue;
* ISBN si libro;
* arXiv ID;
* standard number;
* patent number.

Estado:

* `VERIFIED_PRIMARY`
* `VERIFIED_METADATA`
* `UNVERIFIED`
* `BROKEN`
* `DUPLICATE`

Nada `UNVERIFIED` en versión final.

---

# CT. Retraction audit

Para fuentes que sostienen contribuciones centrales:

* Crossref;
* publisher;
* Crossmark si existe;
* correcciones.

No hace falta hacerlo a todas las 150 páginas corporativas, pero sí a papers esenciales.

---

# CU. Audit de “author credibility”

No es juzgar autores por fama.

Es comprobar:

* ¿publican en el área?
* ¿es la fuente primaria?
* ¿hay conflicto comercial?
* ¿es una fuente académica o marketing?
* ¿el venue corresponde?

No usar autoridad personal como sustituto de evidencia.

---

# CV. Número de referencias

No existe un número mágico.

No perseguir:

> “necesito 100 referencias”.

La pregunta correcta:

> ¿Está representada adecuadamente la literatura necesaria para sostener cada parte de la tesis?

Una referencia relevante vale más que diez tangenciales.

---

# CW. Recency balance

Para cada familia:

$$
\boxed{\text{fundacional}+\text{reciente}}
$$

Ejemplo:

* Monderer & Shapley → potencial.
* Sandholm → population games.
* papers recientes → aplicaciones multi-robot.

No sustituir teoría clásica por un paper nuevo que simplemente la cita.

---

# CX. Literature saturation test

Para cada subproblema:

Preguntar:

> Si busco cinco papers más, ¿probablemente aparecerá una familia metodológica nueva que cambie mi brecha?

Si sí:

> review aún no saturado.

---

# CY. Claim coverage score

Para cada claim fuerte puntuar:

| Factor          | 0          | 1          | 2        |
| --------------- | ---------- | ---------- | -------- |
| fuente existe   | no         | dudosa     | sí       |
| fuente primaria | no         | secundaria | sí       |
| claim directo   | no         | parcial    | sí       |
| actualidad      | obsoleta   | aceptable  | adecuada |
| metadata        | incorrecta | parcial    | exacta   |
| APA             | incorrecto | menor      | correcto |

Máximo:

$$
12.
$$

Claims centrales:

$$
\boxed{12/12}
$$

Nada menos.

---

# CZ. Source quality score

Para cada paper fundamental:

* relevancia;
* proximidad;
* rigor;
* evidencia;
* recoverability;
* status publication.

No convertirlo en ranking político de papers; sirve como herramienta privada para decidir qué sostiene qué.

---

# DA. Citation placement gate

Una cita pasa si:

$$
\boxed{
\text{lector puede señalar exactamente qué proposición respalda}
}
$$

Si no:

> mover o dividir frase.

---

# DB. Reference metadata gate

Una referencia pasa si:

$$
\boxed{
\text{authors + year + title + venue + DOI/URL}
}
$$

han sido verificados contra fuente autoritativa.

---

# DC. APA gate

Pasa solo si:

* orden;
* autores;
* capitalización;
* cursiva;
* volumen;
* número;
* páginas;
* DOI;
* sangría;

están correctos.

---

# DD. Originality gate

Pasa solo si:

* todo contenido ajeno está atribuido;
* citas literales identificadas;
* paráfrasis suficientemente independientes;
* figuras adaptadas atribuidas;
* ideas/taxonomías atribuidas;
* no hay autoplagio relevante main/supp.

VIU es explícita sobre originalidad y antiplagio. 

---

# DE. Marco Teórico gate

Pasa solo si cada sección:

1. define;
2. compara;
3. critica;
4. identifica límite;
5. conecta con el TFM.

No basta resumir.

---

# DF. Estado del Arte gate

Pasa solo si podemos defender:

* búsqueda;
* actualidad;
* representatividad;
* closest prior;
* gap condicionado.

---

# DG. Citation-reference consistency gate

Automático:

$$
\boxed{C=R}
$$

más:

* cero duplicates;
* cero broken DOI;
* cero `et al.` indebidos en references;
* cero missing years;
* cero undefined bib keys.

---

# DH. Audit específico para TU TFM

Yo añadiría búsquedas automáticas de:

* `et al.` dentro de Referencias;
* `s.f.` / `n.d.` mezclados;
* `Retrieved from`;
* `Consultado el` usado indiscriminadamente;
* `DOI:` en vez de `https://doi.org/`;
* arXiv con versión posterior publicada;
* títulos incompletos;
* “Tian 2026” vs 2025;
* ISO 21423 metadata;
* URLs antiguas;
* corporate dates inferidas;
* self-reference Mayorga interna;
* references mencionadas solo en supplementary;
* citas del main no presentes en `.bib`;
* título/DOI mismatch.

---

# DI. Audit de los papers 2025–2026

Especialmente estricto porque son recientes y fáciles de “alucinar”:

* [ ] paper existe;
* [ ] publisher;
* [ ] DOI activo;
* [ ] online date;
* [ ] volume/issue;
* [ ] title exacto;
* [ ] published vs early access;
* [ ] final version vs preprint;
* [ ] claim leído en full text, no solo abstract.

---

# DJ. Audit de teoría matemática

Para cada fuente matemática:

> ¿Estamos citando el resultado correcto o simplemente un paper cercano?

Por ejemplo:

* potencial exacto → fuente correcta;
* VI/GNE → fuente correcta;
* primal-dual → fuente correcta;
* consensus switching → fuente correcta;
* Lyapunov/passivity → fuente correcta;
* MAPF completeness → fuente correcta.

No citar una aplicación reciente para una propiedad clásica si el original es más apropiado.

---

# DK. Audit de la literatura de robótica

Para cada trabajo de transporte cooperativo registrar:

* robots;
* tipo de locomoción;
* carga soportada/empujada/caged/grasped;
* selección de equipo;
* tamaño coalición;
* planificador;
* controlador;
* información;
* contacto;
* fallo;
* hardware/sim;
* guarantee.

Así evitamos agrupar trabajos físicamente incomparables.

---

# DL. Audit de evidencia de hardware

No decir:

> “experimental validation”

como sinónimo de industrial.

Registrar:

* simulation;
* physics simulation;
* lab hardware;
* industrial floor;
* real deployment.

Y citar exactamente.

---

# DM. Audit de “distributed”

Cada paper citado como “distributed”:

* ¿qué está distribuido?
* decisión;
* control;
* estimación;
* comunicación;
* computation?

No aceptar el label del abstract sin entender la arquitectura.

---

# DN. Audit del lenguaje comparativo

Evitar:

> “A supera B”

si:

* distintos escenarios;
* información distinta;
* métricas distintas.

La literatura no es un leaderboard.

Usar:

> “A aborda X bajo…”
> “B añade Y…”

---

# DO. Marco teórico y nuestras ecuaciones

En cada derivación propia:

* identificar qué viene de literatura;
* qué definición adaptamos;
* qué parte es nueva.

Idealmente:

$$
\boxed{
\text{conocido}
\rightarrow
\text{especialización}
\rightarrow
\text{resultado propio}
}
$$

Que el tribunal pueda distinguirlo.

---

# DP. “Contribution boundary”

Esta revisión debe impedir dos errores:

### Plagio intelectual

presentar resultado previo como propio.

### Falsa modestia

presentar resultado propio como mera aplicación si realmente derivamos algo nuevo.

Debemos delimitar exactamente ambas fronteras.

---

# DQ. APA list final — ruleset compacto

Como house style:

$$
\boxed{
\begin{aligned}
&\text{APA 7 obligatoria};\\
&\text{autor-fecha en texto};\\
&\text{3+ autores: et al. desde primera cita};\\
&\text{hasta 20 autores completos en referencias};\\
&\text{DOI en formato https://doi.org/...};\\
&\text{orden alfabético};\\
&\text{sangría francesa};\\
&\text{sentence case en títulos};\\
&\text{journal+volume en cursiva};\\
&\text{correspondencia exacta texto↔referencias};\\
&\text{localizador en cita textual};\\
&\text{fecha de recuperación solo cuando procede}.
\end{aligned}
}
$$

Purdue confirma estas reglas esenciales de APA 7. ([Purdue OWL][3])

---

# DR. Gestión con Zotero/BibLaTeX

VIU recomienda gestores como Zotero/Mendeley para mantener consistencia. 

Pero gestor ≠ garantía de calidad.

Revisar manualmente:

* metadata importada;
* capitalization;
* corporate authors;
* conference names;
* article numbers;
* DOI;
* arXiv.

Un `.bib` malo genera automáticamente una bibliografía consistentemente mala.

---

# DS. Biblioteca canónica

Mantener una sola fuente maestra:

```text
references.bib
```

Cada entrada con:

* DOI;
* URL;
* type;
* verified=true interno;
* notes privadas si se necesita.

Main y supplement consumen el mismo archivo.

---

# DT. Automated literature QA report

Yo pediría a Sonnet/Codex generar:

```text
LITERATURE_AUDIT.csv
```

con:

| key | authors | year | title | type | DOI | DOI resolves | metadata match | cited main | cited supp | APA issue | claim supported | status |
| --- | ------- | ---: | ----- | ---- | --- | ------------ | -------------- | ---------- | ---------- | --------- | --------------- | ------ |

Estados:

* PASS
* FIX_METADATA
* VERIFY_CLAIM
* DUPLICATE
* REPLACE_PREPRINT
* REMOVE
* MISSING_REFERENCE.

Esto queda en repo, **no en el PDF final**.

---

# DU. Claim-source audit file

Separadamente:

```text
CLAIM_SOURCE_MATRIX.csv
```

| claim | text location | source | exact support | locator | source class | strength |
| ----- | ------------- | ------ | ------------- | ------- | ------------ | -------- |

Es la auditoría que detectará las “citas falsas aunque el paper exista”.

---

# DV. Reviewer 1 test

Para cada referencia importante:

> “Si yo fuera el autor de este paper, ¿diría que mi trabajo está representado correctamente?”

Si no:

> corregir.

---

# DW. Reviewer 2 test

> “¿Puede el lector distinguir claramente qué paper realmente hizo hardware, qué hizo simulación y qué solo formuló?”

Si no:

> corregir.

---

# DX. Turnitin test

Para cada párrafo de review:

* [ ] no copiar estructura sintáctica del abstract;
* [ ] no paráfrasis mínima;
* [ ] no cadenas de frases de una misma fuente;
* [ ] atribución de ideas;
* [ ] usar síntesis de múltiples trabajos.

No se trata de “bajar Turnitin”.

Se trata de producir texto realmente propio.

---

# DY. Tribunal test

El jurado debe poder preguntar:

> “¿Cuál es el paper más parecido a lo suyo?”

y tú responder inmediatamente:

1. autor;
2. qué hace;
3. diferencia;
4. por qué la diferencia importa.

Si no puedes:

> estado del arte no está listo.

---

# DZ. Gate final de literatura

Yo no congelaría el TFM hasta tener:

$$
\boxed{
\begin{aligned}
&0\ \text{referencias inexistentes},\\
&0\ \text{DOI incorrectos},\\
&0\ \text{citas sin referencia},\\
&0\ \text{referencias huérfanas},\\
&0\ \text{`et al.' indebidos en bibliography},\\
&0\ \text{preprints cuando existe final sin justificación},\\
&0\ \text{claims centrales sostenidos por marketing},\\
&0\ \text{claims de inexistencia absoluta},\\
&0\ \text{figuras adaptadas sin atribución},\\
&0\ \text{ecuaciones importadas sin origen}.
\end{aligned}
}
$$

Y además:

* 100 % de los **closest prior works** leídos;
* 100 % de las referencias centrales verificadas contra publisher/DOI;
* literatura 2025–2026 actualizada;
* marco teórico con síntesis y crítica;
* every gap condicionado al corpus;
* APA 7 validado visualmente en el PDF final.

---

## La regla que pondría encima del escritorio

Para cada referencia:

$$
\boxed{
\text{EXISTE}
\land
\text{ES CORRECTA}
\land
\text{ES PERTINENTE}
\land
\text{SOSTIENE EL CLAIM}
\land
\text{ESTÁ BIEN CITADA}
}
$$

Si falla una sola condición, **la referencia no está aprobada**.

Y para cada sección del Marco Teórico:

$$
\boxed{
\text{DEFINIR}
\rightarrow
\text{COMPARAR}
\rightarrow
\text{CRITICAR}
\rightarrow
\text{IDENTIFICAR LÍMITE}
\rightarrow
\text{JUSTIFICAR DISEÑO}
}
$$

Eso es exactamente lo que convierte una bibliografía larga en un **marco teórico de nivel tesis**.

En tu caso, yo haría esta auditoría en **tres pasadas separadas**: primero `source truth` —¿las referencias existen y sus metadatos son correctos?—; después `claim truth` —¿realmente sostienen lo que decimos?—; y solo al final `APA/render` —¿está perfectamente formateado?—. Mezclar las tres al mismo tiempo hace que se escapen errores mucho más graves, como un DOI auténtico asociado a una afirmación que el paper nunca hizo.

[1]: https://www.universidadviu.com/sites/universidadviu.com/files/media_files/Gu%C3%ADa%20Did%C3%A1ctica%20TFM%20MCRI.pdf?utm_source=chatgpt.com "•"
[2]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_print_sources.html?utm_source=chatgpt.com "Reference List: Other Print Sources - Purdue OWL® - Purdue University"
[3]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/apa_changes_7th_edition.html?utm_source=chatgpt.com "Changes in the 7th Edition - Purdue OWL® - Purdue University"
[4]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html?nt=1&utm_source=chatgpt.com "Reference List: Electronic Sources - Purdue OWL® - Purdue University"
[5]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/in_text_citations_author_authors.html?utm_source=chatgpt.com "In-Text Citations: Author/Authors - Purdue OWL® - Purdue University"
[6]: https://owl.purdue.edu/owl/owl_en_espanol/estilo_APA_7/citas_en_texto_lo_basico.html?utm_source=chatgpt.com "Citas en el Texto: Lo Básico - Purdue OWL® - Purdue University"
[7]: https://owl.purdue.edu/owl/owl_en_espanol/estilo_APA_7/lista_de_referencias_apa_fuentes_electr%C3%B3nicas.html?utm_source=chatgpt.com "Lista de Referencias APA: Fuentes Electrónicas - Purdue OWL® - Purdue University"
[8]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html?utm_source=chatgpt.com "Reference List: Articles in Periodicals - Purdue OWL® - Purdue University"
[9]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_textual_sources.html?utm_source=chatgpt.com "Reference List: Textual Sources - Purdue OWL® - Purdue University"
[10]: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_basic_rules.html?utm_source=chatgpt.com "Reference List: Basic Rules - Purdue OWL® - Purdue University"