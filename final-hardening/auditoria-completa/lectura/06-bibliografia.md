# Bibliografía y citas

**Criterio aplicado:** `pre-thesis/guidelines/04-literatura-citas-y-referencias.md`
(2634 líneas, secciones A–DZ). Ese fichero es la norma; aquí no se añade
criterio propio.

**Artefactos auditados**

| Artefacto | Contenido |
|---|---|
| `pre-thesis/bibliography/references.bib` | 116 entradas (biblioteca sellada v1) |
| `pre-thesis/bibliography/references-v2.bib` | 39 entradas (aditivo de la v2) |
| `pre-thesis/build-v2/main-v2.pdf` | 146 páginas; bibliografía en pp. 70–82 impresas (pp. 87–99 del PDF) |
| `pre-thesis/build-v2/main-v2.bbl` / `.blg` | lo que biber emitió realmente |
| `final-hardening/census.json` | 89 ficheros `.tex` del documento activo, usados para extraer las citas |

**Fecha de la auditoría:** 2026-09-19.

**Verificación externa:** los metadatos marcados como «verificado» se
contrastaron contra Crossref (`api.crossref.org/works/<DOI>`), arXiv y las
páginas de catálogo de norma. No se modificó ningún fichero del TFM.

---

## Veredicto

**FALLA el gate DZ.** De los diez contadores que DZ exige a cero, cuatro no lo
están. Los defectos se concentran casi por completo en
`bibliography/references-v2.bib`, que —según el propio
`pre-thesis/CITATION_AUDIT.md`— **nunca estuvo cubierto por la auditoría de
metadatos anterior**: aquel dictamen `PASS` audita 116 entradas / 76 claves
activas de `references.bib`, con alcance `thesis` y `monograph`, no `main-v2`.

---

## 1. Recuento y correspondencia (BP, BQ, BR, DG)

| | |
|---|---:|
| `bibliography/references.bib` | **116** entradas |
| `bibliography/references-v2.bib` | **39** entradas |
| Unión (no hay colisión de claves entre ficheros) | **155** |
| Citadas por el documento activo v2 (89 ficheros del censo) | **101** |
| Impresas en `main-v2.bbl` / PDF | **101** |

`main-v2.blg` está limpio: «Found 101 citekeys in bib section 0», sin avisos ni
claves indefinidas.

- **Citas huérfanas (C − R): 0.** PASA BR.
- **C = claves del `.bbl`, exactamente.** No hay inflado por `\nocite`.
- **Referencias huérfanas (R − C): 54.** FALLA BQ («Nada de bibliografía
  decorativa»). Reparto: **41 de 116** en `references.bib`, **13 de 39** en
  `references-v2.bib`. Es el 35 % de la biblioteca maestra arrastrado sin uso.

### 1.1 Huérfanas de `references-v2.bib` (13)

Son entradas añadidas *para* la v2 que siguen sin citarse; prioridad máxima
para borrar o colocar.

`bichler2026sadcher`, `elaamery2021mpc`, `eohPark2021Curriculum`,
`gong2023connector`, `huo2025selfLearning`, `lohTraechtler2012Nonholonomic`,
`machado2019attractor`, `ottoFleetManager`, `pandit2026pinchLiftMove`,
`rizzo2020geomove`, `swisslogIntramove`, `verma2025cfhmrta`,
`yufkaOzkan2015Formation`.

**Siete de ellas se dibujan como puntos en la Figura
`fig:lit-methodological-map`** (`sections/v2/floats/lit-fig-methodological-map.tex`)
sin ningún `\cite`: `elaamery2021mpc`, `gong2023connector`,
`machado2019attractor`, `rizzo2020geomove`, `lohTraechtler2012Nonholonomic`,
`yufkaOzkan2015Formation` y, con cita en otro sitio, `verma2019replacement`.
Bajo AS, una figura derivada de fuentes debe llevar la cita en el pie o en la
nota. O se citan ahí, o se retiran los puntos.

### 1.2 Huérfanas de `references.bib` (41)

`activmedia2003pioneer`, `azadeh2019warehouse`, `balch1998behavior`,
`bogomolnaiaJackson2002Hedonic`, `chenSun2011LeaderFollower`,
`crouse2016Rectangular`, `cuturi2013sinkhorn`, `demsar2006Statistical`,
`fiorini1998velocity`, `grayLamport2006Commit`, `grisetti2007gridMapping`,
`halpernMoses1990Knowledge`, `highs2026Official`, `holm1979Sequential`,
`huangfuHall2018Highs`, `jonkerVolgenant1987Shortest`, `kalman1960optimal`,
`karp1972reducibility`, `kerby2014SimpleDifference`, `kube2000cooperative`,
`lakens2013EffectSizes`, `leanh2006agv`, `luby1986MIS`,
`mardenShamma2012LogLinear`, `martinezPiazuelo2022Population`,
`mayne2000mpc`, `nash1950equilibrium`, `nav2StateEstimation2026`,
`nedic2009distributedSubgradient`, `olson2011apriltag`,
`petcuFaltings2005DPOP`, `ponda2010dynamicCommunication`,
`quijano2017population`, `ren2004virtual`, `robotLocalization2026`,
`silver2005cooperativePathfinding`, `song2002potential`,
`uribe2021dualDistributed`, `weed2018entropic`,
`zavlanos2008distributedAuction`, `zhangParker2013Resources`.

### 1.3 Consecuencia aparte: bibliografía metodológica ausente (AT)

Toda la referencia metodológica está huérfana en la v2:
`holm1979Sequential`, `demsar2006Statistical`, `lakens2013EffectSizes`,
`kerby2014SimpleDifference`, `huangfuHall2018Highs`, `highs2026Official`.
VIU exige explícitamente bibliografía **temática y metodológica**; la v2 no cita
ninguna de las seis.

---

## 2. Auditoría de autoría APA 7 — `et al.` / `and others` (AG, AI, DZ)

**Ocho entradas llevan `and others`, todas en `references-v2.bib`. Tres están
citadas y se imprimen literalmente como «et al.» en la lista de referencias**
(pp. 71, 78 y 80 impresas). Es exactamente la violación que AG nombra con
ejemplo: «entradas como `Fukao, T., et al.` son candidatas directas a
corrección». El `.bbl` lo confirma con `\true{moreauthor}` en cada una.

| clave | campo `author` exacto | ¿citada? | impresión en el PDF |
|---|---|---|---|
| `fukao2025swarm` | `{Fukao, T. and others}` | **sí** | `Fukao, T., et al. (2025).` |
| `tian2025irregular` | `{Tian, Y. and others}` | **sí** | `Tian, Y., et al. (2025).` |
| `verma2019replacement` | `{Verma, P. and others}` | **sí** | `Verma, P., et al. (2019).` |
| `elaamery2021mpc` | `{Elaamery, B. and others}` | no | — |
| `gong2023connector` | `{Gong, Z. and others}` | no | — |
| `huo2025selfLearning` | `{Huo, X. and others}` | no | — |
| `machado2019attractor` | `{Machado, T. and others}` | no | — |
| `verma2025cfhmrta` | `{Verma, A. and others}` | no | — |

Listas de autoría reales, verificadas, de las tres citadas:

- `fukao2025swarm` → **Yuto Fukao, Tatsuro Terakawa, Takahiro Endo, Fumitoshi
  Matsuno, Yoshihiro Morimoto, Takumi Koshimoto, Daisuke Mizuno** (7 autores).
- `tian2025irregular` → **Dujie Tian, Lelai Zhou, Chen Zhang, Yibin Li**
  (4 autores).
- `verma2019replacement` → **Pulkit Verma, Rahul Tallamraju, Abhay Rawat,
  Subhasis Chand, Kamalakar Karlapalem** (5 autores).

Las tres tienen ≤ 20 autores, así que APA 7 obliga a escribirlos todos.

**El origen del defecto es una regla escrita.** La cabecera de
`bibliography/references-v2.bib`, líneas 10–18, institucionaliza la infracción:

> «REGLA DE TRANSCRIPCIÓN. Los metadatos se copian literalmente de la lista de
> referencias de esos consolidados. Cuando la fuente abrevia la autoría como
> «et al.», aquí se escribe `and others` y NO se completan los nombres que la
> fuente no da.»

Esa regla contradice AG. Hay que derogarla, no solo parchear las ocho entradas,
o el defecto se regenera en la siguiente incorporación.

El uso de `et al.` **en texto** (AH, AI) lo genera `biblatex-apa` y es correcto
en todo el documento: el defecto está confinado a la lista de referencias.

---

## 3. Las tres entradas señaladas por revisión externa

### 3.1 Muhammed / Nada / El-Hussieny 2026 — **la revisión tiene razón**

`bibliography/references-v2.bib`, líneas 139–146, clave
`muhammed2026decentralizedMpc`. Contenido actual, literal:

```bibtex
@article{muhammed2026decentralizedMpc,
  author       = {Muhammed, I. and Nada, A. A. and El-Hussieny, H.},
  title        = {Real-time decentralized model predictive control for cooperative multi-robot object transport},
  journaltitle = {Scientific Reports},
  date         = {2026},
  doi          = {10.1038/s41598-026-41881-w},
  url          = {https://doi.org/10.1038/s41598-026-41881-w}
}
```

Crossref para ese mismo DOI devuelve:

| campo | valor verificado | estado en el `.bib` |
|---|---|---|
| título | `Real-time decentralized model predictive control for cooperative multi-robot object transport: experimental validation` | **truncado**: falta `: experimental validation` |
| autores | Ibrahim Muhammed, Ayman A. Nada, Haitham El-Hussieny | correcto |
| revista | Scientific Reports | correcto |
| volumen | **16** | ausente |
| número | **1** | ausente |
| número de artículo | **9824** | ausente |
| fecha | 2026-03-22 | `date = {2026}`, aceptable |

Dos incumplimientos: título inexacto (gate A, «¿El título es exacto?»; DB) y
`@article` sin volumen ni número de artículo (AX, DB).

La truncadura además daña DL. La obra se cita en
`sections/v2/theory-discriminant.tex:21` y en
`sections/v2/appendix-review-full-detail.tex:93`, en ambos casos dentro de un
volcado de seis claves; quitar «experimental validation» del título borra justo
la señal de clase de evidencia que DL exige registrar.

### 3.2 ISO 21423 — **la revisión tiene razón, y el problema es mayor**

`bibliography/references-v2.bib`, líneas 323–330, clave `iso21423`. Contenido
actual, literal:

```bibtex
@online{iso21423,
  author  = {{International Organization for Standardization}},
  title   = {{ISO} 21423 --- Industrial trucks: Communication protocols for interoperability of automated mobile robots, fleet managers and enterprise resources},
  date    = {2026},
  note    = {Etapa 60.00, «International Standard under publication»; excluye requisitos de seguridad},
  url     = {https://www.iso.org/standard/70909.html},
  urldate = {2026-09-11}
}
```

Cómo se imprime hoy (p. 74 impresa):

> International Organization for Standardization. (2026). ISO 21423 — Industrial
> trucks: Communication protocols for interoperability of automated mobile
> robots, fleet managers and enterprise resources [Etapa 60.00, «International
> Standard under publication»; excluye requisitos de seguridad]. Consultado el
> 11 de septiembre de 2026, desde https://www.iso.org/standard/70909.html

Cuatro defectos separados:

1. **Título incorrecto.** El título oficial es **«Robotics — Industrial mobile
   robots — Communications and interoperability»**. La cadena actual es una
   paráfrasis del *alcance*, no el título, y además adscribe la norma a la
   familia **«Industrial trucks»** (ISO/TC 110) cuando ISO 21423 es una norma de
   **Robotics** (ISO/TC 299). Incumple AA («título exacto») y BF.
2. **URL incorrecta.** `https://www.iso.org/standard/70909.html` no es el
   registro de ISO 21423. El catálogo correcto es
   **`https://www.iso.org/standard/86749.html`**. Incumple AA («URL oficial») y BZ.
3. **Estado de publicación mal declarado.** El `.bib` afirma etapa 60.00,
   «International Standard under publication». El documento está en
   **ISO/FDIS 21423**: ISO/DIS 21423:2025-07 fue retirado y sustituido por
   ISO/FDIS 21423:2026-05, es decir, sigue siendo borrador en aprobación.
   Incumple BH («Draft standard» no es «under publication», y ninguno de los dos
   puede presentarse como norma publicada) y AA («estado vigente»).
4. **`date = {2026}` imprime «(2026)»**, que se lee como año de publicación de
   una norma que todavía no lo tiene. La plantilla de BF pide
   `(ISO Standard No. xxxx:year)`; ese año no existe aún.

La entrada hermana `iso36914` (líneas 332–339, ISO 3691-4:2023) sí tiene título
y año correctos: el defecto está aislado en `iso21423`.

### 3.3 Tian — **la acusación de desajuste de año queda refutada; el defecto real es otro**

Una revisión externa afirmó que había un desajuste **«Tian 2026 vs 2025»** entre
la figura y la bibliografía; el propio §DH de la directriz lo lista como punto a
buscar. Se comprobaron **todas** las apariciones de «Tian» en `pre-thesis/`
(búsqueda insensible a mayúsculas sobre `.tex`, `.json` y `.md`):

| localización | valor literal |
|---|---|
| `bibliography/references-v2.bib:112` | `@article{tian2025irregular, ... date = {2025}` |
| `sections/v2/floats/lit-fig-methodological-map.tex:64` | `\mappointL{0.02}{-0.90}{Tian}{2025}{T}{23}{controlcol}` |
| `sections/v2/theory-discriminant.tex:21` | `\parencite{...,tian2025irregular,...}` |
| `sections/v2/appendix-review-full-detail.tex:93` | `\parencite{...,tian2025irregular,...}` |
| PDF p. 80 impresa | `Tian, Y., et al. (2025).` |

**Figura y bibliografía dicen 2025 las dos, y el DOI
`10.1109/LRA.2025.3597895` confirma 2025.** No existe ninguna aparición de
«Tian 2026» en el repositorio. **Esa afirmación concreta queda refutada**: o el
desajuste se corrigió antes de esta pasada, o nunca llegó al documento activo.

Pero **debajo de esa acusación hay un defecto real y no corregido: la inicial
del primer autor está mal.**

| clave | `.bib` dice | verificado (Crossref) | corrección |
|---|---|---|---|
| `tian2025irregular` | `Tian, Y.` | **Dujie Tian** (primer autor de *Dujie Tian, Lelai Zhou, Chen Zhang, Yibin Li*) | `Tian, D.` |
| `fukao2025swarm` | `Fukao, T.` | **Yuto Fukao** (primer autor de *Yuto Fukao, Tatsuro Terakawa, Takahiro Endo, Fumitoshi Matsuno, Yoshihiro Morimoto, Takumi Koshimoto, Daisuke Mizuno*) | `Fukao, Y.` |

En ambos casos la inicial parece haberse tomado de un coautor: la `Y.` de Tian
coincide con *Yibin* Li, y la `T.` de Fukao con *Tatsuro* Terakawa o *Takahiro*
Endo. El efecto es grave porque la inicial errónea se propaga a la cita en
texto: hoy el documento escribe `(Tian et al., 2025)` señalando a una persona
distinta de la que firma el artículo. Incumple el gate A («¿Los autores son
correctos?»), DB y AL.

Resumen: **la queja registrada era falsa; la entrada sí estaba rota, por otra
razón.** Corregir solo el año que se denunció habría dejado el defecto intacto.

---

## 4. Auditoría de metadatos, entradas 2024–2026 (DB, DI, AX, AW, BA, BF)

La unión contiene 35 entradas fechadas 2024–2026; 28 de ellas citadas. Defectos
verificados:

### 4.1 `@article` sin volumen y sin páginas ni número de artículo (AX, DB)

Cinco entradas citadas:

| clave | estado actual | valores correctos verificados |
|---|---|---|
| `diehlAdams2026Grapes` | `Autonomous Agents and Multi-Agent Systems`, sin vol./págs.; título `{GRAPE-S}: Near real-time coalition formation for multiple service collectives` | **40**(1), art. **29**; Crossref escribe «near real-time» en minúscula; autores Grace Diehl y Julie A. Adams (el `.bib` ya es correcto) |
| `fukao2025swarm` | `ROBOMECH Journal`, sin vol./págs. | **12**(1), art. **20** |
| `muhammed2026decentralizedMpc` | `Scientific Reports`, sin vol./págs. | **16**(1), art. **9824** |
| `tian2025irregular` | `IEEE Robotics and Automation Letters`, sin vol./págs. | **10**(10), **9822–9829** |
| `serviceAdams2011Coalition` | `Autonomous Agents and Multi-Agent Systems`, sin vol./págs. | (2011, fuera de la ventana, mismo defecto) |

Ninguna entrada citada de tipo `@article` carece de DOI, y ninguna que tenga
volumen carece de páginas: el defecto es exactamente este bloque de cinco.

### 4.2 Preprint citado existiendo versión final (AW; contador 6 de DZ)

- **`phan2024cactus`** (`@inproceedings`, `references.bib`). Campos actuales:
  `booktitle = {Proceedings of the 23rd International Conference on Autonomous
  Agents and MultiAgent Systems}`, `note = {AAMAS 2024}`,
  `url = {https://arxiv.org/abs/2401.05860}`, `eprint = {2401.05860}`,
  `eprinttype = {arxiv}`, **sin páginas y sin DOI**. El artículo está en las
  actas oficiales de AAMAS 2024, **pp. 1558–1566**, DOI
  **`10.5555/3635637.3663016`**. Peor: hoy se imprime como

  > Phan, T., Driscoll, J., Romberg, J., y Koenig, S. (2024). Confidence-Based
  > Curriculum Learning for Multi-Agent Path Finding [AAMAS 2024].

  es decir, **la referencia impresa no nombra ningún congreso ni actas**, solo
  una nota entre corchetes. Fallo duro de BA y DB.

- **`zhou2026cttapf`** (`@online`, `references.bib`): `note = {Preprint}`,
  `eprint = {2605.16097}`, **sin DOI**. El propio campo *journal-ref* de arXiv
  declara **AAMAS 2026, Proc. of the 25th International Conference on Autonomous
  Agents and Multiagent Systems**. Presentarlo como preprint ya es incorrecto.

### 4.3 DOI ausente existiendo (AX, BY)

| clave | DOI que falta | metadatos verificados |
|---|---|---|
| `qiu2024payloadConsumption` | `10.48550/arXiv.2412.10087` | Xuekai Qiu, Pengming Zhu, Yiming Hu, Zhiwen Zeng, Huimin Lu — coinciden con el `.bib`; no consta versión publicada |
| `verma2019replacement` | `10.48550/arXiv.1904.03049` | Pulkit Verma *et al.*; arXiv declara journal-ref «Autonomous Robots and Multirobot Systems, 2019» |
| `zhou2026cttapf` | `10.48550/arXiv.2605.16097` | ver 4.2 |
| `phan2024cactus` | `10.5555/3635637.3663016` | ver 4.2 |

`qiu2024payloadConsumption` tampoco lleva marca `[Preprint]`: se imprime como
recurso web corriente, incumpliendo AW y el Nivel C de I («marcar: preprint / no
necesariamente peer-reviewed»). Contraste: `zhou2026cttapf` sí imprime
`[Preprint]`.

### 4.4 Tipo de entrada mal elegido

**No hay ningún `@misc`** en ninguno de los dos ficheros, pero `@online` se usa
para cosas que no son páginas web:

- Normas como `@online`: `iso21423`, `iso36914`, `ansiA3R1508part3`,
  `vda5050v3`. BF pide la forma de norma con `(ISO Standard No. …)`; `@online`
  no puede producirla.
- Preprints y artículos como `@online`: `qiu2024payloadConsumption`,
  `verma2019replacement`, `zhou2026cttapf`.

### 4.5 Año frente a año embebido en el DOI

Los tres casos en que el año del `.bib` es probablemente el equivocado (los tres
son huérfanos, así que la prioridad es baja):

| clave | `.bib` | DOI | lectura |
|---|---|---|---|
| `bichler2026sadcher` | `date = {2026}` | `10.1109/MRS66243.2025.11357250` | MRS **2025** |
| `huo2025selfLearning` | `date = {2025}` | `10.1109/TASE.2024.3395283` | TASE **2024** |
| `sahuKumar2026FaultManagement` | `date = {2026}` | `10.3390/automation7010001` | Crossref devuelve **2025** para *Automation* 7(1), 1; verificar contra la línea «Published:» del propio artículo antes de tocarlo |

Los otros quince desfases detectados (`ames2017cbf` 2017/DOI 2016,
`ebel2024cooperative` 2024/2023, `sharon2015cbs` 2015/2014,
`shibata2023event` 2023/2022, `cherukuri2016primalDual`, `franci2022stochasticGNE`,
`kar2009imperfectConsensus`, `zhangParker2013IQASyMTRe`, `barreiro2017distributed`,
`azadeh2019warehouse`, `bogomolnaiaJackson2002Hedonic`, `grisetti2007gridMapping`,
`leanh2006agv`, `nedic2009distributedSubgradient`, `quijano2017population`,
`uribe2021dualDistributed`) responden al patrón normal *online-first* de
Elsevier e IEEE y **no son defectos**.

### 4.6 Fuentes corporativas con título inventado (Z, BE, CS)

| clave | `title` | `url` |
|---|---|---|
| `ottoFleetManager` | `{Documentación de producto de gestión de flota autónoma}` | `https://ottomotors.com/` |
| `swisslogIntramove` | `{Documentación de producto de gestión de flotas de robots móviles}` | `https://www.swisslog.com/` |

Son títulos descriptivos inventados que apuntan a la portada de la empresa, no a
una página real con ese título. Bajo CS quedarían en `UNVERIFIED`, que DZ no
admite. Ambas son huérfanas: procede borrarlas, no repararlas.

---

## 5. Duplicados (BS)

**Cero DOI duplicados. Cero títulos duplicados. Ningún par arXiv + versión final
arrastrado como dos claves.** El único parecido detectado por similitud de
título (ratio 0,82) es `ottoFleetManager` / `swisslogIntramove`, que son dos
empresas distintas compartiendo el mismo título genérico inventado: es el
síntoma de §4.6, no un duplicado bibliográfico. **PASA BS.**

---

## 6. Gates de formato sobre el PDF compilado (BW, BX, BV, AE, AF, BU, DC)

| gate | resultado | medición |
|---|---|---|
| **BW** orden alfabético | **PASA** | secuencia monótona; `van den Berg` y `van der Schaft` correctamente archivados bajo *v* antes de `Verband`; las dos entradas `vandenberg` ordenadas por segundo autor (Guy antes que Lin), no por año, como manda APA |
| **BX** sangría francesa | **PASA** | pp. 88–99 del PDF: 126 primeras líneas en x0 = 85,0 pt y más de 200 líneas de continuación en x0 = 121,0 pt → **exactamente 1,27 cm** |
| **AE** formato de DOI | **PASA** | cero ocurrencias de `DOI:` en la lista impresa; todos los DOI salen como `https://doi.org/…` |
| **AF** fechas de recuperación | **parcial** | 22 entradas imprimen «Consultado el …» |
| **BU/DC** sentence case | **FALLA** | 34 títulos citados en Title Case |

### 6.1 Fechas de recuperación (AF)

Veintidós entradas llevan `urldate` y lo imprimen. La mayoría son defendibles
bajo AF (páginas de producto, normas «under publication», dashboards). Dos no lo
son:

- **`verma2019replacement`**, `urldate = {2026-09-11}` sobre un registro arXiv
  versionado e inmutable.
- **`awsRobomakerWarehouse2021`**, mismo caso.

Listado completo de entradas con `urldate`: `agiloxXswarmBmw2023`,
`ansiA3R1508part3`, `awsRobomakerWarehouse2021`, `beaconDualAmr2026`,
`geekplusWarehouseSolutions`, `greatoxGtvl2026`, `hubtexAviation2020`,
`hyundaiHmgics2023`, `internationalFederationRobotics2025`, `iso21423`,
`iso36914`, `kukaKmp3000p2025`, `kukaOmnimoveAirbus2016`,
`mirInternalTransport`, `siasunDualVehicle2024`, `staubliR3Drawbar2022`,
`tiiScheuerleSpmt2023`, `usptoCpcG05D`, `vda5050v3`, `verma2019replacement`,
`wipoPatentLandscape`, `zhou2026cttapf`.

### 6.2 Entradas sin fecha (BD)

Tres imprimen `(s.f.)` teniendo fecha averiguable:
`geekplusWarehouseSolutions`, `mirInternalTransport`, `usptoCpcG05D`.

### 6.3 Title Case (BU, DC)

**34 títulos citados están en Title Case y se imprimen así**, cuando APA exige
sentence case para artículos y libros. Es un fallo sistemático de
`references.bib` —aproximadamente el 34 % de la lista impresa— mientras que
`references-v2.bib` ya está en sentence case: los dos ficheros son además
**incoherentes entre sí** en estilo de casa.

`an2023cooperativeReview`, `awsRobomakerWarehouse2021`,
`barreiro2017distributed`, `bezerra2025dynamicCoalition`, `bullo2009distributed`,
`cherukuri2016primalDual`, `dai2024dynamicCoalition`, `dutta2021hedonic`,
`ebel2024cooperative`, `fischerLynchPaterson1985Impossibility`,
`franci2022stochasticGNE`, `geekplusWarehouseSolutions`, `huang2022mlLns`,
`internationalFederationRobotics2025`, `kia2019dynamicConsensus`,
`koshal2016aggregative`, `naito2025tihdp`, `ortega2002passivity`,
`paul2023collective`, `phan2024cactus`, `qiu2024payloadConsumption`,
`rosenfelder2024force`, `sartoretti2019primal`, `shan2024collectiveTransport`,
`shibata2023event`, `shibata2023localGlobal`, `shida2025infeasibleTasks`,
`tang2025railgun`, `vanderschaf2017passivity`, `wurman2008coordinating`,
`yi2019operatorGNE`, `yu2023graphTransformer`, `zhang2024coalition`,
`zhou2026cttapf`.

Ejemplo de cómo se imprime hoy: `naito2025tihdp` → «Task-Priority Intermediated
Hierarchical Distributed Policies: Reinforcement Learning of Adaptive
Multi-Robot Cooperative Transport».

---

## 7. Totales, distribución por año y composición de fuentes

### 7.1 Bibliografía impresa — las 101 referencias de `main-v2.pdf`

**Distribución por año**

```
1955:1  1985:1  1986:2  1988:1  1989:1  1993:1  1995:1  1996:1  1998:2
2001:1  2002:2  2004:3  2006:5  2008:3  2009:4  2010:2  2011:3  2012:1
2013:2  2014:1  2015:2  2016:3  2017:5  2018:2  2019:7  2020:1  2021:2
2022:4  2023:9  2024:8  2025:8  2026:12
```

- 2023–2026: **37 de 101 (36,6 %)**. 2024–2026: **28 (27,7 %)**. La actualidad
  está cubierta en volumen (M y L pasan en cantidad).
- Anteriores a 2000: 11 (10,9 %). La capa fundacional existe (CW pasa).
- Las **12 entradas de 2026** son el bloque de mayor riesgo bajo DI, y **8 de
  esas 12 son corporativas/web o páginas de norma**, no trabajo revisado por
  pares.

**Composición de fuentes (101 impresas)**

| clase | n | % |
|---|---:|---:|
| Artículo de revista (peer-reviewed) | 56 | 55,4 % |
| Congreso / actas | 16 | 15,8 % |
| Corporativa / web (Niveles D y F) | 16 | 15,8 % |
| Libro / capítulo de libro | 5 | 5,0 % |
| Preprint (arXiv) | 4 | 4,0 % |
| Normas (ISO / ANSI-A3 / VDA) | 3 | 3,0 % |
| Informe técnico (WIPO) | 1 | 1,0 % |

Evidencia primaria revisada por pares (Nivel A: revista + congreso + libros) =
**77 / 101 = 76,2 %**. No revisada por pares (corporativa/web + preprint) =
**20 / 101 = 19,8 %**. La proporción es defendible bajo I **siempre que ningún
claim central descanse sobre el bloque de Nivel D**; eso es una cuestión de
*claim truth*, que queda fuera de esta pasada: la propia directriz (línea 2630)
la sitúa en la segunda de las tres pasadas.

### 7.2 Biblioteca completa (155 entradas, los dos ficheros)

Artículo de revista 93 (60,0 %), congreso 25 (16,1 %), corporativa/web 22
(14,2 %), libro/capítulo 6 (3,9 %), preprint 5 (3,2 %), normas 3 (1,9 %),
informe 1 (0,6 %). Rango 1950–2026; 2026 es el año más numeroso, con 19.

---

## 8. Marcador DZ

| contador DZ | exigido | real |
|---|---:|---|
| referencias inexistentes | 0 | 0 — todas las comprobadas resuelven |
| DOI incorrectos | 0 | 0 DOI erróneos; **4 entradas citadas sin el DOI que existe** |
| citas sin referencia | 0 | **0 — PASA** |
| referencias huérfanas | 0 | **54 — FALLA** |
| `et al.` indebidos en bibliografía | 0 | **3 impresos, 8 en fuente — FALLA** |
| preprints con versión final disponible | 0 | **2 (`phan2024cactus`, `zhou2026cttapf`) — FALLA** |
| claims centrales sostenidos por marketing | 0 | fuera de esta pasada (*claim truth*) |
| claims de inexistencia absoluta | 0 | fuera de esta pasada |
| figuras adaptadas sin atribución | 0 | **7 puntos de `fig:lit-methodological-map` sin cita — FALLA (AS)** |
| ecuaciones importadas sin origen | 0 | fuera de esta pasada |

Añadido por DB y DC, fuera de la lista de DZ pero igual de bloqueante: **5
`@article` sin volumen ni páginas; 1 título truncado; 1 norma con título, URL y
estado equivocados; 2 iniciales de primer autor erróneas; 34 títulos en Title
Case.**

---

## 9. Conjunto mínimo de correcciones para pasar el gate

Ordenado por coste de aplicación, de menor a mayor. Cada punto es directamente
accionable sobre un fichero y una línea concretos.

1. **Corregir dos iniciales de primer autor** (2 ediciones de un carácter, alto
   impacto porque contaminan la cita en texto).
   `bibliography/references-v2.bib:112` → `Tian, Y.` pasa a `Tian, D.`;
   `bibliography/references-v2.bib` entrada `fukao2025swarm` → `Fukao, T.` pasa a
   `Fukao, Y.`

2. **Restaurar el título truncado.** En `muhammed2026decentralizedMpc`
   (`references-v2.bib:141`), el `title` termina en
   `... object transport: experimental validation`.

3. **Añadir volumen, número y páginas a las cinco `@article` incompletas.**
   `muhammed2026decentralizedMpc` → `volume = {16}`, `number = {1}`,
   `eid = {9824}`. `tian2025irregular` → `volume = {10}`, `number = {10}`,
   `pages = {9822--9829}`. `fukao2025swarm` → `volume = {12}`, `number = {1}`,
   `eid = {20}`. `diehlAdams2026Grapes` → `volume = {40}`, `number = {1}`,
   `eid = {29}` y «Near» en minúscula. `serviceAdams2011Coalition` → completar
   contra Crossref.

4. **Añadir los cuatro DOI que faltan.**
   `qiu2024payloadConsumption` → `10.48550/arXiv.2412.10087`;
   `verma2019replacement` → `10.48550/arXiv.1904.03049`;
   `zhou2026cttapf` → `10.48550/arXiv.2605.16097`;
   `phan2024cactus` → `10.5555/3635637.3663016`.

5. **Quitar dos `urldate` improcedentes** (AF): `verma2019replacement` y
   `awsRobomakerWarehouse2021`.

6. **Poner fecha real a las tres entradas que imprimen `(s.f.)`**:
   `geekplusWarehouseSolutions`, `mirInternalTransport`, `usptoCpcG05D`.

7. **Marcar `qiu2024payloadConsumption` como preprint** (`note = {Preprint}`, o
   el mecanismo que ya usa `zhou2026cttapf`).

8. **Reescribir por completo la entrada `iso21423`** (`references-v2.bib:323–330`):
   título oficial «Robotics — Industrial mobile robots — Communications and
   interoperability»; URL `https://www.iso.org/standard/86749.html`; estado
   ISO/FDIS 21423:2026-05, borrador en aprobación, **no** etapa 60.00; retirar o
   condicionar el `date = {2026}` para que no se lea como año de publicación.

9. **Sustituir las dos referencias de preprint por su versión final** (AW):
   `phan2024cactus` → actas AAMAS 2024, pp. 1558–1566, DOI
   `10.5555/3635637.3663016`, y quitar la nota `{AAMAS 2024}` que hoy suplanta
   al nombre de las actas en la impresión; `zhou2026cttapf` → AAMAS 2026, y
   retirar `note = {Preprint}`.

10. **Completar las listas de autoría de las tres entradas con `and others`
    citadas** (AG), escribiendo los nombres hasta 20:
    `fukao2025swarm` → Fukao, Y., Terakawa, T., Endo, T., Matsuno, F.,
    Morimoto, Y., Koshimoto, T., y Mizuno, D.;
    `tian2025irregular` → Tian, D., Zhou, L., Zhang, C., y Li, Y.;
    `verma2019replacement` → Verma, P., Tallamraju, R., Rawat, A., Chand, S., y
    Karlapalem, K.

11. **Derogar la regla de transcripción** de `bibliography/references-v2.bib`,
    líneas 10–18, que ordena escribir `and others` y no completar autorías. Sin
    esto, el punto 10 se revierte en la siguiente incorporación. Completar
    también las cinco entradas huérfanas con `and others` si se decide
    conservarlas.

12. **Verificar los tres años dudosos frente al DOI**: `bichler2026sadcher`
    (MRS 2025), `huo2025selfLearning` (TASE 2024), `sahuKumar2026FaultManagement`
    (Crossref devuelve 2025).

13. **Citar o retirar los 7 puntos de `fig:lit-methodological-map` sin cita**
    (AS): `elaamery2021mpc`, `gong2023connector`, `machado2019attractor`,
    `rizzo2020geomove`, `lohTraechtler2012Nonholonomic`, `yufkaOzkan2015Formation`
    y `verma2019replacement` en el pie o la nota de la figura.

14. **Borrar las dos entradas corporativas con título inventado**:
    `ottoFleetManager` y `swisslogIntramove`.

15. **Resolver las 54 referencias huérfanas** (BQ): citarlas donde de verdad
    sostienen algo, o eliminarlas. Empezar por las 13 de `references-v2.bib` y
    por las 6 metodológicas de `references.bib`, que además AT exige que estén
    citadas: `holm1979Sequential`, `demsar2006Statistical`,
    `lakens2013EffectSizes`, `kerby2014SimpleDifference`, `huangfuHall2018Highs`,
    `highs2026Official`.

16. **Pasar a sentence case los 34 títulos en Title Case** de `references.bib`
    (lista completa en §6.3). Es el punto más caro en número de ediciones y el
    de menor riesgo semántico; conviene dejarlo para el final, cuando el resto
    de la biblioteca ya esté estable.

17. **Convertir las cuatro normas de `@online` al tipo de norma** (`iso21423`,
    `iso36914`, `ansiA3R1508part3`, `vda5050v3`) para que BF pueda producir
    `(ISO Standard No. …)`. Requiere tocar el estilo, por eso va al final.

---

*Auditoría de solo lectura. No se modificó ningún `.tex`, `.bib` ni artefacto de
compilación del TFM.*
