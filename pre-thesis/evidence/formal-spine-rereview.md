# Re-revisión delta de la columna vertebral formal

**Fecha:** 2026-09-08  
**Modo:** verificación independiente posterior a revisión  
**Decisión:** correcciones sustantivas aceptadas, con una corrección menor todavía obligatoria y un riesgo de integración explícito.

## Resultado ejecutivo

Las correcciones de maximalidad de SP1 y SP7, positividad de costes de SP6, cuantificación de la imposibilidad por partición y normalización de la cota perturbada SP4 son matemáticamente correctas en el árbol activo de `pre-thesis`. La cota temporal SP6 también tiene ahora las hipótesis y el factor de ventanas correctos en su enunciado. Sin embargo, su demostración no está en el anexo que compila: el único desarrollo histórico permanece detrás de `\ifdefined\VIUFullSPsixProofs`, no se incluye desde `thesis-appendices.tex` y todavía conserva la fórmula anterior. Por ello, la re-revisión no emite un cierre global `PASS`.

No se identificó un P0. El estado agregado es:

- 7 hallazgos de revisión: **6 PASS, 1 FAIL**;
- 4 enlaces externos SP2: **4 PASS** como trazabilidad semántica;
- inventario estructural: **PASS**, con separación explícita de responsabilidades;
- nuevo riesgo de integración: los cuatro resultados SP2 canónicos están enlazados, pero no forman parte del PDF activo.

## Matriz de verificación

| ID | Hallazgo anterior | Estado | Verificación independiente |
|---|---|---:|---|
| RR-P1-SP1 | Maximalidad y cota de SP1 | **PASS** | `thesis-results.tex:23-32` define la ejecución que continúa mientras exista una mejora, limita solo cambios aceptados y excluye segundos/rondas. La prueba completa está en el cuerpo activo. |
| RR-P1-SP7 | Maximalidad y cota de SP7 | **PASS** | `sp7.tex:107-110` dice “camino maximal” y `08-sp7-proofs.tex:18` distingue expresamente una trayectoria truncada. La cota es `prod_i |R_i|-1` cambios, no tiempo. |
| RR-P1-SP6-COST | Costes positivos de recuperación | **PASS** | `sp6.tex:138-146` incorpora capacidades no negativas, pesos positivos y `kappa_i^6>0`. El anexo activo usa esa positividad en ambas inclusiones. El contraejemplo de coste cero queda fuera por hipótesis. |
| RR-P1-SP6-TIME | Ventanas temporales de recuperación | **FAIL** | El enunciado activo es correcto: cubre detección--primera revisión, revisiones sucesivas y certificación terminal, y usa `2^{n_R} bar_tau_a`. No existe, sin embargo, una prueba activa de ese conteo. El bloque no incluido `07-sp6-proofs.tex:103-108` aún usa `(2^{n_R}-1) bar_tau_a` y la premisa antigua “entre cambios aceptados”. |
| RR-P1-PARTITION | Cuantificadores de la imposibilidad | **PASS** | `thesis-results.tex:64-71` exige dos instancias indistinguibles y proyecciones óptimas disjuntas; la prueba por contradicción coincide exactamente con el enunciado y declara singleton/interacción conocida como frontera. |
| RR-P1-SP4 | Normalización de la perturbación SP4 | **PASS** | El anexo activo fija `ell_0`, usa `S_q=diag(ell_0,ell_0,1)`, `D_tilde=S_q^T(D+K_D)S_q` y `r_tilde=S_q^T r`. Young se aplica en coordenadas adimensionalizadas y el texto reconoce que la cota depende de `ell_0`. |
| RR-P1-SP2-LINK | Resultados canónicos SP2 fuera del inventario | **PASS** para trazabilidad | Los cuatro reciben IDs externos, hash común, líneas de enunciado/prueba y claim-ID en `formal-spine-rereview.csv`. No se altera el universo de cuatro corpus del manifiesto. Esto no equivale a inclusión editorial en la tesis. |

## Comprobación de las pruebas activas

### SP1: potencial y cuotas

El archivo activo define acciones `a_i in {0,...,K}`, cuotas obligatorias, costes fijos adimensionales en `[0,kappa_max]`, `sum n_k <= N` y `lambda>kappa_max`. Para cualquier desviación, la referencia WLU que retira al robot es idéntica antes y después, por lo que `Delta U_i=Delta Phi_1`.

La prueba cubre todos los perfiles inexactos:

1. con robot libre y déficit, entrar mejora al menos `lambda-kappa_max`;
2. sin robots libres, déficit implica exceso y un traslado reduce dos penalizaciones;
3. con exceso sin déficit, una salida disminuye exceso sin aumentar coste.

Los perfiles exactos no admiten salida, entrada ni traslado rentable. La ejecución declarada no se detiene mientras exista mejora y la justicia activa una mejora persistentemente disponible. Como la cota se formula sobre cambios aceptados, las revisiones sin cambio y el tiempo físico no quedan indebidamente acotados. El hallazgo se considera cerrado.

### SP7: potencial de rutas

El enunciado y su prueba activa usan “camino maximal”. La identidad `binom(m+1,2)-binom(m,2)=m` sigue igualando las diferencias de utilidad y potencial. La finitud impide repetir perfiles; maximalidad, no mera finitud, fuerza que el perfil terminal sea Nash. La prueba añade de forma útil que una trayectoria truncada no hereda la conclusión. El hallazgo se considera cerrado.

### SP6: recuperación

La caracterización Nash ya declara los supuestos que su prueba utiliza: capacidades no negativas, `w_a>0`, costes estrictamente positivos, reserva completa factible y `lambda_6>kappa_max^6/delta_min`. La demostración compacta activa en `thesis-appendices.tex:25-32` prueba las dos inclusiones y el contraejemplo de coste cero deja de pertenecer al dominio. Queda un caso degenerado menor: si `D_6(0)=0`, no existen perfiles deficitarios y `delta_min` es un mínimo sobre el vacío; conviene declarar déficit postfallo no trivial o separar ese caso, cuyo Nash único es la coalición vacía bajo costes positivos.

Para la cota temporal, el factor nuevo es correcto. Si hay `m<=2^{n_R}-1` cambios aceptados, hay a lo sumo `m+1<=2^{n_R}` ventanas: una hasta cada cambio y una para certificar el terminal. Al sumar detección, desplazamientos paralelos acotados por el máximo y asentamiento se obtiene la expresión de `sp6.tex:177-180`. Esta derivación de cuatro líneas no aparece en el anexo activo. Debe añadirse al bloque compacto; activar sin más `07-sp6-proofs.tex` no sirve, porque duplicaría material/etiquetas y reintroduciría la cota antigua.

### Partición

La proposición activa ya no cuantifica sobre una familia arbitraria. El determinismo y la igualdad del historial fuerzan la misma salida local; las proyecciones disjuntas de óptimos hacen imposible que esa salida sea óptima en ambas instancias. La extensión de detección usa el mismo argumento con un predicado binario. Las excepciones declaradas impiden la refutación por familia singleton o por óptimo local común. El hallazgo se considera cerrado.

### SP4 perturbado

Con `q=S_q z`, se tiene `q_dot=S_q z_dot` y

```text
q_dot^T (D+K_D) q_dot = z_dot^T D_tilde z_dot,
q_dot^T r_W             = z_dot^T r_tilde_W.
```

Las componentes de `z` son adimensionales; `r_tilde_W` homogeneiza fuerza y momento como trabajo generalizado, y `lambda_min(D_tilde)` pertenece a esa métrica fijada. La desigualdad de Young y la cota resultante son dimensionalmente coherentes. Riesgo residual bajo: el enunciado de `sp4.tex:177` todavía abrevia la dependencia como `||r_k^W||`; para evitar una lectura como norma SI cruda, la versión final debería decir `||S_q^T r_k^W||` o “norma inducida por la escala declarada”. La prueba, no obstante, corrige el P1 original.

## Grafo documental que realmente compila

`pre-thesis/main.tex` incluye `sections/thesis-results.tex` y `sections/thesis-appendices.tex`. En ese grafo:

- SP1 y la proposición de partición tienen enunciado y prueba completos directamente en `thesis-results.tex`;
- SP7 usa `source-snapshot/.../sp7.tex` y su prueba activa `source-snapshot/appendices/08-sp7-proofs.tex`;
- SP4 usa `source-snapshot/.../sp4.tex` y la prueba normalizada activa `source-snapshot/appendices/06-sp4-proofs.tex`;
- SP6 usa `source-snapshot/.../sp6.tex` y una demostración compacta escrita en `thesis-appendices.tex`;
- no se incluyen los anexos históricos 03, 07 o 09 completos;
- `Subdocuments/SP2/sp2.tex` no se incluye en la memoria activa.

La omisión deliberada de los anexos históricos evita duplicación, pero hace especialmente importante no asumir que una prueba existente en `source-snapshot/appendices/` está compilada. Ese fue el origen del único `FAIL`.

## Papel de `formal-results-audit.csv`

Sí, `formal-results-audit.csv` puede permanecer sin cambios como **inventario estructural de los cuatro corpus** `books/work/paper/thesis`, aunque la columna formal se gobierne mediante los CSV semánticos. Deben respetarse estas reglas:

1. su presencia de `proof` significa proximidad léxica, no validación;
2. sus hashes describen las fuentes de los cuatro corpus, no necesariamente la versión ensamblada en `pre-thesis`;
3. no debe alimentar automáticamente estados `SUPPORTED`;
4. la precedencia de decisión debe ser `formal-spine-rereview.csv` → `formal-spine-verdicts.csv` → `formal-results-audit.csv`;
5. el join debe usar ID, ruta y SHA-256; una etiqueta LaTeX sola no basta por la copia inactiva histórica de SP1.

Esta separación es preferible a ampliar artificialmente el manifiesto: el manifiesto responde “qué material había en los cuatro corpus”, mientras los overlays responden “qué afirmación formal fue auditada y qué versión está activa”.

## Enlace explícito de los cuatro resultados SP2

`formal-spine-rereview.csv` contiene cuatro filas `EXT-SP2-*` con:

- claim-ID canónico de `docs/04_CLAIMS_EVIDENCE.md`;
- ID externo estable;
- ruta `Subdocuments/SP2/sp2.tex`;
- SHA-256 `8002b52d0ba3c71239856ec23be51106ffacfb5b655d9741d0697d034593d2e4`;
- línea de enunciado y prueba;
- relación `EXTERNAL_SEMANTIC_OVERLAY_OUTSIDE_FOUR_CORPUS`;
- estado de inclusión en el PDF.

Así quedan enlazados sin convertir `Subdocuments/` en un quinto corpus. El mismo hash en las cuatro filas es intencional: cada claim apunta a un ancla distinta del mismo archivo. La trazabilidad queda resuelta; la inclusión editorial no. Si los cuatro forman parte vinculante de la columna científica de la memoria, deben condensarse en `thesis-results.tex` o en un anexo activo. Hoy el PDF solo contiene la proposición SP4 histórica, no los cuatro resultados canónicos de `Subdocuments/SP2/sp2.tex`.

## Hashes de las unidades revisadas

| Unidad | SHA-256 |
|---|---|
| `pre-thesis/sections/thesis-results.tex` | `240cbc9894a01886dc56f5b81504c3da36082e3881b4539f725f0cd2a797115f` |
| `pre-thesis/sections/thesis-appendices.tex` | `769eb5d1929e5fe22831e5af91fa90ae3e2e05c44edcdd7feba88566879fc3a9` |
| SP4 activo | `2447c4f4da5d953e7099ddda4d5fb7264ddf2b3269629d8f8a495cd987ca63c5` |
| prueba SP4 activa | `4110eff9c0b63969494da7987b028ce98feb18a14a1de5278b783cca89de5991` |
| SP6 activo | `59f6accbd197fc3feeff135d39ab3a2e6dad3cdc562e950bfe9bf8fe46e1b4ae` |
| anexo histórico SP6 no activo | `e58c72ceee92012315480659cc13c869999a8d09199fd5fe43ae490b3b5682ba` |
| SP7 activo | `ba164ee84933b9d0ef6d416dfeb9a627919112bbec421fc6859736d47ca36a1e` |
| prueba SP7 activa | `a3ed731e8571afe497068d0506c474e7ae656e958930537f1b5cc16b45ac574f` |
| SP2 canónico externo | `8002b52d0ba3c71239856ec23be51106ffacfb5b655d9741d0697d034593d2e4` |
| inventario estructural | `f92ebeb32941e7d4a83bf8a865cf51c209fa1bac290f5533a34e4c8cfa6ab219` |
| primera auditoría semántica | `543c87d4eebc176d8830d15c69c8877c485e7be5f95a259aa11df0081e6d2d96` |

## Verificación ejecutable

Se repitió la batería focal sobre el árbol actual:

```text
python -m pytest -q -p no:cacheprovider \
  tests/test_sp1_theory.py tests/test_sp2_canonical.py \
  tests/test_sp2_submit_ready.py tests/test_sp6_recovery.py \
  tests/test_sp7_traffic.py tests/test_sp8_network.py
59 passed in 26.07s
```

Los tests no sustituyen las pruebas. En particular, el helper de tiempo SP6 calcula una suma dada, pero no impone la hipótesis del planificador que acota cada ventana.

## Acción mínima para cierre

La corrección obligatoria restante es insertar en el anexo compacto activo la derivación `m<=2^{n_R}-1`, `m+1<=2^{n_R}` y la suma de viaje paralelo/asentamiento. Después de ello, los P1 matemáticos de la primera auditoría pueden cerrarse. Por separado, debe decidirse si los cuatro SP2 canónicos serán solo soporte trazado o contenido formal visible de la memoria; tratarlos como parte de la columna aprobada exige lo segundo.
