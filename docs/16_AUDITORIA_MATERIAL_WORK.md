# 16 — Auditoría del material de `material/compendios/` y `material/books/`

Fecha: 2026-09-07. Corpus revisado: 31 PDF en `material/compendios/` (~3.700 páginas) y 21
libros en `material/books/`.

## 1. Higiene del corpus

Seis pares son **idénticos byte a byte** (SHA-256):

| Conservar | Duplicado |
|---|---|
| `TFM_MROB_MegaPaper_IEEE_Unificado_2026.pdf` | `… (1).pdf` |
| `Compendio_Maestro_MROB_2026_DENSO_v2_100p.pdf` | `… (1).pdf` |
| `TFM_MROB_Monografia_Canonica_200p_2026.pdf` | `… (1).pdf` |
| `SP1_VIU_corregido_cierre_20260823.pdf` | `… (2).pdf` |
| `TFM_MROB_Documento_Canonico_Vivo_v0_1_2026.pdf` | `… (1).pdf` |
| `SP3_Advanced_Game_Control_N1_N5_20260904 (1).pdf` | `SP3 (4).pdf` |

Quedan **19 documentos únicos**, 588.544 palabras.

## 2. Densidad formal por documento

| Documento | Palabras | Teo | Prop | Lema | Def | Demo |
|---|---:|---:|---:|---:|---:|---:|
| `Documento_Canonico_Vivo` (248 p) | 76.424 | **20** | **22** | **10** | 7 | **85** |
| `Monografia_Canonica_200p` | 61.084 | 16 | 15 | 10 | 7 | 73 |
| `Compendio_Maestro_Exhaustivo` (553 p) | 211.389 | 12 | 3 | 8 | 0 | 90 |
| `Compendio_Definitivo_R5_Teoria_Avanzada` | 20.994 | 12 | 5 | 1 | 0 | 21 |
| `MegaPaper_IEEE_Unificado` | 13.474 | 8 | 2 | 4 | 0 | 5 |
| `desarrollo_cargo_push_GNE` | 7.774 | 4 | 7 | 0 | 0 | 11 |

`Documento_Canonico_Vivo` es la fuente principal: mayor densidad formal y mejor
proporción demostración/enunciado. `Compendio_Maestro_Exhaustivo` tiene 211.000
palabras y solo 12 teoremas: es transcripción de sesión, no material formal.

Estado actual de la memoria, para comparar: **22 objetos formales** (3 teoremas,
12 proposiciones, 6 corolarios, 1 observación, 0 lemas, 0 definiciones).

## 3. Procedencia y cautela

Los compendios están generados con asistencia de IA; uno se llama
`Compendio_Integral_Chat_…`. **Un enunciado en un PDF no es un teorema
demostrado.** Se comprobaron cinco a mano (§4) y los cinco son resultados
estándar correctamente enunciados, pero cada importación exige verificar
hipótesis, demostración y alcance antes de entrar en la memoria
(`math-rigor`, `claims-evidence-guard`).

## 4. Hallazgos que llenan huecos reales

### 4.1 Descomposición exacta de cuatro niveles — el hallazgo principal

`Documento_Canonico_Vivo`, Teorema 11.3:

$$J(Z_t) - J^{*}_{\mathrm{rel}} = \Delta_{\mathrm{int}} + \Delta_{\mathrm{top}} + \Delta_{\mathrm{dyn}}$$

con $\Delta_{\mathrm{int}} = J^{*}_{IP} - J^{*}_{\mathrm{rel}}$,
$\Delta_{\mathrm{top}} = J^{*}_{C} - J^{*}_{IP}$,
$\Delta_{\mathrm{dyn}} = J(Z_t) - J^{*}_{C}$, los tres no negativos por
$\mathcal X \supseteq \mathcal F \supseteq CM(z_0)$.

Algebraicamente es una identidad telescópica. Conceptualmente **es el esqueleto
formal de la escalera N1–N4**, que hoy solo existe como narrativa:

| Término | Nivel | Qué mide la memoria hoy |
|---|---|---|
| $\Delta_{\mathrm{int}}$ | N2 | brecha de integralidad LP↔entero (23,1 % con CV=0) |
| $\Delta_{\mathrm{top}}$ | N3 | coste de la información vecinal; partición permanente |
| $\Delta_{\mathrm{dyn}}$ | N4 | escape de orden $h$; 55,7 % BR → 14,6 % 2BR → 3,1 % C3 |

La escalera pasa de «retiramos supuestos de uno en uno» a «la brecha total se
descompone exactamente en tres términos no negativos y cada nivel mide uno». Es
la unificación de ideas dispersas con mayor retorno del corpus, y **comprime**:
sustituye párrafos de motivación por una identidad.

Requiere: definir $J^{*}_{\mathrm{rel}}$, $J^{*}_{IP}$, $J^{*}_{C}$ y $CM(z_0)$
con la notación de `docs/05_NOTATION.md`, y comprobar que las cifras medidas
corresponden a esos tres términos y no a otros soportes.

### 4.2 Unilateralidad del contacto — cierra la circularidad de OE2

`Documento_Canonico_Vivo` §4, Proposiciones 4.1 y 4.2:

- **4.1 (No existe tirón normal).** Por complementariedad, $n^\top f = \lambda_n \ge 0$;
  si el hueco $g > 0$ entonces $\lambda_n = 0$ y el cono fuerza $\lambda_t = 0$,
  luego $f = 0$.
- **Fricción de Coulomb con máxima disipación:** $\lambda_t \in -\mu_s\lambda_n\,\partial|u_t|$.
  Con deslizamiento, $\lambda_t u_t = -\mu_s\lambda_n|u_t| \le 0$.

La consecuencia está enunciada allí de forma explícita: *el optimizador no puede
escoger una fuerza tangencial arbitraria dentro del cono ignorando la velocidad
relativa*. Eso es exactamente el defecto del certificador
(`sp1_geo/certifier.py` resuelve `lsq_linear` con $0 \le f \le \bar f$ y elige
magnitudes libremente).

Convierte la `\begin{observacion}` informal de `sp3.tex` —«Lo que el certificado
no certifica»— en **proposiciones demostradas**. OE2 deja de ser circular por vía
analítica, sin esperar a la campaña física.

### 4.3 Versión muestreada y small-gain — cierra el requisito de `AGENTS.md` §3.2

- **W4 (muestreada):** $\bar p_{k+1} = \bar p_k + \gamma(\bar w_d - \bar W(\bar p_k))$
  converge para $0 < \gamma < 2/L$ con $F$ convexa de gradiente $L$-Lipschitz.
- **SG (small-gain):** con $\dot V_z \le -a_z\lVert z\rVert^2 + b_z\lVert e_p\rVert^2 + \sigma_z\lVert d_z\rVert^2$
  y su simétrica, la interconexión es estable si $b_z b_p < a_z a_p$.

`AGENTS.md` §3.2 exige distinguir modelo continuo de ejecución digital
muestreada. La memoria hoy no tiene ningún resultado muestreado. W4 lo aporta con
condición de paso explícita.

### 4.4 Restricción no holónoma

Teorema 9.1 (grado relativo longitudinal con rueda dinámica) y la especificación
de parachoques frontal $\lambda_n\cos\beta_{\mathrm{front}} - e_i^\top n_{i\ell} \le 0$:
para empujar, el eje del chasis debe orientarse hacia el contacto. Cubre la
frontera (iii) de la observación de `sp3.tex`.

El atractor angular $V_\theta = 1 - e_i^\top n$ con
$\dot V_\theta = -k_\theta[(e_i^\perp)^\top n]^2$ se declara allí como alineación
**local**, conservando un equilibrio antipodal. Esa cautela debe conservarse al
importarlo.

### 4.5 Puente VI–potencial

Teorema 11.1: con $\mathcal X$ convexo compacto y $\phi$ diferenciable cóncava,
$x^\star \in \arg\max\phi$ ⟺ $x^\star$ resuelve $VI(-\nabla\phi,\mathcal X)$; bajo
restricciones compartidas y cualificación, es un GNE variacional. Conecta la
formulación de juegos potenciales de SP1 con el PD-vGNE-seeking, hoy presentados
como familias separadas.

La Observación 11.2 que lo acompaña es honesta y debe importarse con él: el
teorema **no** convierte el GNE continuo en coalición ejecutable, porque
$\mathcal X$ contiene puntos fraccionarios fuera de $\mathcal F$.

## 5. Libros: qué respaldo aportan

`material/books/` cubre con fuente primaria lo que hoy se afirma sin ella:

| Libro | Respalda |
|---|---|
| Quijano, Ocampo-Martínez — *Population Games and Evolutionary Dynamics in Distributed Control* | §4.3, dinámicas poblacionales (ya citado) |
| *Generalized Nash Equilibrium Seeking in Population Games* | §4.5, puente VI–GNE |
| Bullo, Cortés, Martínez — *DCRN* | consenso, $\lambda_2$, algoritmos distribuidos (ya citado) |
| Ren, Beard — *Distributed Consensus in Multi-vehicle Cooperative Control* | consenso (ya citado) |
| Tembine, Barreiro-Gómez — *Mean-Field-Type Games for Engineers* | escalado poblacional |
| Yadav — *Advanced Graph Theory* | $CM(z_0)$, componentes y accesibilidad de §4.1 |

**Faltan en `references.bib`** (116 entradas): Facchinei–Pang (canónica para el
puente VI–GNEP, §4.5), Murota (convexidad discreta, Teorema 13.1), Cortés,
Tembine.

## 6. Tensión con el presupuesto de páginas

El cuerpo está en 92 páginas con un máximo de 80. Importar material **añade**.
Excepción: §4.1 comprime, porque sustituye narrativa de motivación por una
identidad.

Criterio propuesto: importar solo lo que (a) cierra un hueco declarado en
`docs/04_CLAIMS_EVIDENCE.md` o en la observación de fronteras de `sp3.tex`, o
(b) sustituye prosa existente. Todo lo demás, al anexo o fuera.

## 7. Orden de trabajo propuesto

1. §4.1 descomposición de cuatro niveles → esqueleto de la escalera N1–N4.
2. §4.2 unilateralidad → proposiciones en `sp3.tex`, sustituyendo la observación.
3. §4.3 W4 muestreada → cierra `AGENTS.md` §3.2.
4. §4.5 puente VI–potencial → unifica SP1 con PD-vGNE.
5. §4.4 no holónoma → frontera (iii).
6. Añadir Facchinei–Pang y Murota al `.bib`; verificar con `citation-hygiene`.

Cada importación pasa por `math-rigor` (hipótesis explícitas y usadas) y
`claims-evidence-guard` (nada se afirma por encima de su evidencia).
