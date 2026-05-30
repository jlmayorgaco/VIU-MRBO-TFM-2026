# CLAUDE_TASK.md — Cierre del Informe Intermedio TFM (entrega hasta Metodología)

## 0. Contexto y reglas

Autor: Jorge Luis Mayorga Taborda. Máster en Robótica y Automatización de Procesos
(MROB), Universidad Internacional de Valencia (VIU). Tutor: José Ignacio Iñíguez Amigot.

Este es el INFORME INTERMEDIO del TFM. Cubre **hasta el final de Metodología (§4)**.
Las secciones 5 (Marco teórico), 6 (Resultados) y 7 (Conclusiones) son **stubs
intencionales y SE QUEDAN como stubs**. No se desarrollan.

Las tareas anteriores (v4 y verificación bibliográfica) ya están aplicadas. Este
prompt cierra únicamente lo que sigue abierto antes del submit.

### Reglas absolutas
1. Trabaja en `docs/doc-02-mid-report/`.
2. PRIMERO explora el repo y devuélveme un PLAN (archivo · línea · diff propuesto por
   tarea + riesgos). NO modifiques nada hasta que confirme.
3. Motor real: **XeLaTeX** (`fontspec` + fuente del sistema). Flujo:
   `xelatex → bibtex → xelatex ×2`. `latexmk`/`pdflatex` fallan aquí.
4. Tras cada tarea: compila y confirma 0 referencias/citas indefinidas, sin `??`.
5. Commits atómicos, en español, formato `tipo(scope): descripción`.
6. NO añadas referencias bibliográficas nuevas. NO inventes números, autores,
   teoremas, resultados ni ecuaciones.
7. NO toques el paquete Python.
8. NO infles el alcance. NO desarrolles los stubs (§5, §6, §7).
9. Español de España, registro académico, coherente con el estilo existente.
10. Para las ecuaciones y el pseudocódigo: cambios QUIRÚRGICOS. Lee el bloque actual
    antes de editar y modifica solo lo indicado, preservando macros y formato.

---

## TAREA 1 — Algoritmo 1: aplicar la histéresis ρ_s en la selección de estrategia

**Problema (bug de coherencia):** el Algoritmo 1 selecciona la estrategia con
`s_i(t+1) ← arg máx_k p_ik(t+1)` directo, lo que **contradice la ec. (12)**, que
define una regla con umbral de histéresis ρ_s (solo se cambia de estrategia si la
dominante aventaja a la actual en más de ρ_s).

**Acción:** localiza en `sections/04-metodologia.tex` la línea del Algoritmo 1 que
asigna `s_i(t+1)` (la del `arg máx`, justo tras la proyección al símplex). Sustituye
esa asignación incondicional por la **regla condicional de la ec. (12)**:
- Calcula `k* ← arg máx_k p_ik(t+1)`.
- Si `p_{i,k*}(t+1) − p_{i,s_i(t)}(t+1) > ρ_s`, entonces `s_i(t+1) ← k*`.
- En otro caso, `s_i(t+1) ← s_i(t)` (mantener).
- Empate dentro de k*: mantener `s_i(t)`.

Preserva el estilo del entorno algorithmic del repo (`\State`, `\If`, `\Else`,
`\EndIf` o equivalente). NO cambies la ec. (12); solo haz que el pseudocódigo la
refleje. Añade un comentario al margen `⊳ regla de histéresis, ec. (12)`.

**Commit:** `fix(algoritmo): selección de estrategia con histéresis ρ_s (coherencia con ec. 12)`

---

## TAREA 2 — Algoritmo 1: caso s_i = 0 (inactividad) en la tasa de revisión μ_i

**Problema:** la línea del Algoritmo 1 que calcula `μ_i` usa `l^eff_{s_i}`, pero para
un robot inactivo (`s_i = 0`) la inactividad no tiene posición física asociada, por lo
que `‖q_i^xy − l_0‖` queda indefinido. El texto de §4.6 ya dice que para `s_i = 0` se
usa `μ_i = μ_0`, pero el pseudocódigo no lo refleja.

**Acción:** en la línea de cálculo de `μ_i` del Algoritmo 1, añade el caso especial:
- Si `s_i = 0`: `μ_i ← μ_0`.
- En otro caso: la expresión modulada actual (ec. 13).

Mantén la coherencia con el texto de §4.6. Cambio mínimo, sin tocar la ec. (13).

**Commit:** `fix(algoritmo): caso de inactividad s_i=0 en μ_i (coherencia con §4.6)`

---

## TAREA 3 — Tabla 1 ausente (numeración de tablas)

**Problema:** el Índice de tablas empieza en "Tabla 2"; no existe Tabla 1. O el
contador de tablas arranca mal, o hay una tabla sin numerar/etiquetar, o la
numeración quedó corrida tras una edición.

**Acción:**
1. Diagnostica la causa: busca todos los entornos `table`/`\caption`/`\label` de
   tipo tabla en `sections/` y en `main.tex`. Identifica por qué la primera tabla
   listada es la 2.
2. NO inventes una tabla nueva. Las soluciones válidas son, en orden de preferencia:
   (a) si hay un `\addtocounter`/`\setcounter{table}` o un `\caption` fuera de
   entorno que descuadra el contador, corrígelo para que la primera tabla real sea
   Tabla 1; (b) si la "Tabla 2" actual es en realidad la primera tabla del documento,
   renumera para que sea Tabla 1 y propaga las referencias cruzadas.
3. Recompila y verifica que el Índice de tablas es correlativo (1, 2, 3, …) y que
   ninguna `\ref`/`\autoref` a tablas queda rota.

En el PLAN, antes de tocar nada, dime cuál es la causa diagnosticada y cuál de las
dos soluciones aplicas.

**Commit:** `fix(tablas): numeración correlativa desde Tabla 1`

---

## TAREA 4 — Nomenclatura: símbolos faltantes

**Problema:** varios símbolos usados en ecuaciones y en la Tabla 6 no figuran en la
sección de Nomenclatura: `α` (ganancia de atracción), `η` (ganancia de repulsión),
`δ` (ganancia de formación), `v_máx` (velocidad lineal máxima), `ω_máx` (velocidad
angular máxima).

**Acción:** añádelos al bloque correspondiente de la Nomenclatura (Parámetros del
sistema / Funciones, según encaje), con la misma descripción breve y unidades que ya
usan en la Tabla 6. NO cambies los valores ni añadas símbolos que no aparezcan en el
texto. Verifica de paso que no falte ningún otro símbolo de la Tabla 6.

**Commit:** `docs(nomenclatura): añadir símbolos α, η, δ, v_máx, ω_máx`

---

## TAREA 5 — Matizar "preserva la estructura de juego de congestión"

**Problema:** la propiedad "preserva la estructura de juego de congestión" se afirma
sin condición en el Resumen y en §4.3, pero solo está demostrada en el caso base
Ψ≡1 (Teorema 4.1). Con descuento espacial Ψ(d)<1 el payoff multiplicativo deja de
depender únicamente de la ocupación, así que la estructura de congestión es
aproximada / perturbada.

**Acción A — Resumen.** Localiza la frase del Resumen sobre el payoff sigmoide que
"preserva la estructura de juego de congestión" y sustitúyela por:
> …un payoff multiplicativo con componente sigmoide monótonamente decreciente en la
> ocupación estimada de cada tarea, que en el caso base (Ψ≡1) induce una estructura
> de juego de congestión; el factor espacial Ψ(d) actúa como perturbación de esa
> estructura, evaluada empíricamente.

**Acción B — §4.3.** Localiza la frase "Esta monotonicidad decreciente es la que
preserva la estructura de juego de congestión ponderado y distingue este diseño…" y
sustitúyela por:
> Esta monotonicidad decreciente induce una estructura de juego de congestión
> ponderado en el caso base Ψ≡1, sobre la que se sustenta el análisis del
> Teorema 4.1; con descuento espacial Ψ(d)<1 el payoff deja de depender únicamente
> de la ocupación y la estructura de congestión se preserva solo de forma aproximada,
> lo que se caracteriza empíricamente. Esta cota inferior por saturación distingue el
> diseño…

NO toques el Teorema 4.1 (ya opera bajo Ψ≡1, el matiz allí sería redundante).

**Commit:** `docs(claim): acotar la estructura de congestión al caso base Ψ≡1`

---

## TAREA 6 — Quitar la fórmula de β_máx del Resumen

**Problema:** el Resumen incluye literalmente `β_máx = 8/(T_s μ_0 r N)` y la fórmula
de β_mín. Un resumen no debe llevar fórmulas largas con todos los símbolos.

**Acción:** en el Resumen, sustituye la frase que enuncia los límites explícitos por:
> El Teorema 4.1 establece estabilidad asintótica local del equilibrio Nash objetivo
> bajo la hipótesis simplificada de comunicación global y factor espacial unitario
> (Ψ≡1), para un intervalo acotado del parámetro de pendiente β cuyos límites se
> derivan explícitamente en la Sección 4.10.

Las ecuaciones explícitas (19)–(20) ya están en §4.10 y NO se tocan.

**Commit:** `docs(resumen): mover los límites explícitos de β a §4.10`

---

## TAREA 7 — Verificación de consistencia O(K/N) vs O(m/N) (solo redacción)

**Problema:** la cota de error de seguimiento del DAC aparece como `O(K/N)` en las
Observaciones 4.1 y 4.6 (cambio individual) y como `O(m/N)` en la Observación 4.3
(m robots simultáneos), sin aclarar la relación.

**Acción:** en la Observación 4.1 (primera aparición), añade una frase breve que
explique que un cambio de estrategia individual desplaza K componentes del vector de
estimación (de ahí O(K/N)), y que m reasignaciones simultáneas escalan como O(m/N).
NO cambies las cotas; solo añade la aclaración para que sean coherentes entre sí.
Si el contenido ya es claro al releerlo, déjalo y anótalo en el informe de resultados.

**Commit:** `docs(dac): aclarar relación entre cotas O(K/N) y O(m/N)`

---

## NO EJECUTAR (queda en cancha del autor)

- **% TODO-CITA — Martínez-Piazuelo 2022a:** confirmar contra el paper que cubre las
  dinámicas de Smith / pairwise específicamente y no solo la clase general. NO tocar
  la cita; dejar el marcador.
- **% TODO-VOZ:** las reescrituras de voz las hace el autor a mano. NO ejecutar.
- **zhang2024:** reconfirmación en IEEE Xplore (autor lo hace).
- **Correo al tutor por el cambio de título:** fuera de alcance del repo.

---

## ORDEN SUGERIDO

Bloqueantes primero (1, 2, 3), luego alto valor (4, 5, 6), luego 7.
Compila y verifica tras cada commit. Devuélveme el PLAN antes de ejecutar.