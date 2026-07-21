# Plantilla canónica para una sección SPX

## 1. Propósito y obligatoriedad

Este documento define la microestructura de `sp0.tex`--`sp8.tex` dentro de `thesis/sections/mainmatter/06-results-and-analysis/`. Se aplica al crear, completar o revisar un subproblema. Complementa `docs/01_VIU_REQUIREMENTS.md`; no modifica los capítulos superiores de la plantilla VIU.

La secuencia es obligatoria como contrato de contenido, pero la profundidad es desigual: SP0--SP2 y los SP de evidencia A/B requieren mayor desarrollo formal; una extensión de nivel C puede ser más breve. Puede agruparse contenido común en `index.tex` o entre SP adyacentes para evitar nueve miniartículos repetitivos. Nunca se inventa una sección de control, una prueba o una comparación solo para llenar la plantilla.

Excepción narrativa documentada para SP0: al ser un caso de calibración cuyo resultado central es la caracterización del juego, el bloque de juego puede preceder a la tabla de métodos. La tabla y el protocolo aparecen inmediatamente después para que la proposición motive la comparación. Esta excepción no modifica el orden de SP1--SP8 ni elimina ningún bloque obligatorio.

La plantilla maestra del autor se integra como una ampliación de este contrato: cada SP debe incluir un contraejemplo incremental, declarar la cadena de información realmente ejecutada, clasificar el estado de sus aportes y separar límite teórico de límite práctico. No se altera el orden exigido por la memoria VIU ni se obliga a una extensión uniforme.


Cada SP es una `\subsection` del capítulo 6 y debe comenzar en una página nueva mediante `\clearpage` antes de su inclusión. Debe comenzar con un párrafo introductorio y no puede haber dos encabezados consecutivos sin texto intermedio.

## 2. Secuencia canónica

| Orden | Bloque | Contenido mínimo | Salida verificable |
|---:|---|---|---|
| 1 | Título e introducción | Pregunta local, cambio respecto al SP anterior, supuestos, alcance y nivel de evidencia | Un párrafo que permita entender qué añade SPX |
| 2 | Diagrama TikZ | Escenario espacial, actores, decisiones, mensajes y magnitudes que cambian | Figura numerada, citada y con fuente |
| 3 | Problema de optimización | Variables, dominios, objetivo, restricciones, unidades y clase del problema | Oráculo/baseline/problema de evaluación claramente etiquetado |
| 4 | Métodos y literatura comparada | Propuesta, oráculo, baselines y ablación; fuentes verificadas, garantías y limitaciones | Tabla crítica tipo revisión de literatura |
| 5 | Juego distribuido e implementación | Jugadores, acciones, información local, fitness/payoff, potencial, dinámica de revisión, mensajes y coste | Formulación ejecutable y garantía formal honesta |
| 6 | Problema de control y acoplamiento | Servorregulación estratégica en todos los SP y, cuando corresponda, control físico: salidas, referencias, errores, feedback, estimadores, entradas, leyes, restricciones, discretización e interfaz | Lazo estratégico reproducible y capa física separada, con garantía o limitación explícita |
| 7 | Simulaciones | Hipótesis, configuración, factores, semillas, escenarios, métricas, ablaciones y estadística | Protocolo reconstruible desde archivos versionados |
| 8 | Resultados y comparaciones | Distribuciones e incertidumbre, gap al oráculo, comparación pareada, fallos, negativos y contraste con teoría | Tablas/figuras generadas desde datos y análisis crítico |
| 9 | Conclusión y transición | Respuesta local, evidencia alcanzada, limitaciones y cambio que hereda el SP siguiente | Cierre que no sobreafirma ni repite todo el apartado |

## 3. Reglas por bloque

### 3.1 Título e introducción

Usar `\subsection{SPX: ...}` y `\label{subsec:spx}`. El primer párrafo debe responder, en este orden:

1. qué pregunta local se estudia;
2. qué cambia respecto a SPX-1;
3. qué se mantiene fijo;
4. qué queda fuera;
5. qué nivel de evidencia se busca o se alcanzó.

No comenzar con definiciones aisladas ni repetir la formulación común del capítulo 6.

El incremento debe acompañarse de un contraejemplo mínimo: dos soluciones que satisfacen la propiedad de SPX-1, pero solo una satisface la propiedad nueva de SPX. La figura puede representar ese contraste; si no lo hace, el texto debe describirlo y enlazar su demostración o evidencia. SP0 usa como frontera dos asignaciones factibles/Nash con costes distintos.

La introducción termina declarando el último estado realmente acreditado de la cadena `OBSERVED--ESTIMATED--RAW--CLOSED--GUARDED--EXECUTED`, no el estado que se pretende alcanzar en una campaña futura.


### 3.2 Diagrama TikZ

El diagrama es una vista conceptual del escenario, no decoración. Debe mostrar únicamente variables relevantes para ese SP: robots, cargas, coaliciones, posiciones, asignaciones, comunicación, fuerzas, obstáculos o fallos según corresponda.

- Usar `\begin{spdiagram}`, `\spdrawarena` y los estilos definidos en `thesis/viu-mrob-thesis.sty`.
- Diferenciar asignación seleccionada, alternativa, comunicación y movimiento mediante los estilos comunes.
- Incluir una leyenda compacta dentro del marco reservado.
- Citar la figura antes de insertarla y añadir `\viuownsource` o una fuente real.
- No introducir símbolos que no se definan en el texto o en `docs/05_NOTATION.md`.

### 3.3 Problema de optimización

Antes de la ecuación se deben definir conjuntos, variables, dominios, parámetros y unidades. Después de la ecuación se debe declarar expresamente si representa:

- un oráculo central con información global;
- un baseline de optimización;
- un problema de evaluación o certificado; o
- el mecanismo propuesto, solo si realmente se implementa así.

Incluir factibilidad, tamaño del espacio de soluciones y complejidad cuando sean relevantes. No llamar NP-difícil a un problema por ser combinatorio: la afirmación exige reducción, teorema o referencia primaria verificable.

### 3.4 Tabla de métodos como revisión comparada

La tabla no es una lista de nombres. Debe sintetizar la literatura necesaria para justificar la selección experimental. Columnas recomendadas:

| Fuente/método | Clase del problema | Coste asintótico | Arquitectura e información | Parámetros principales | Garantía y limitación |
|---|---|---|---|---|---|
| Fuente primaria verificada | P/NP/NP-difícil, con referencia o reducción | Tiempo, memoria y/o mensajes | Central/global o distribuida/local | Paso, tolerancia, horizonte, pesos | Óptimo, cota o ninguna; diferencia arquitectónica |
| Fuente primaria verificada | Clase bajo los supuestos citados | Coste por iteración y total | Mensajes, estado y conectividad | Ganancias y condición de parada | Convergencia bajo supuestos; supuestos no compartidos |
| Este TFM | Clase del problema resuelto, no del algoritmo | Coste por agente, evento y total | Estado propio y vecinos | Parámetros que alteran conducta o coste | Resultado formal propio y alcance exacto de la prueba |
| Este TFM | Igual que el método completo | Coste de la variante | Misma información salvo el componente retirado | Parámetro fijado o componente eliminado | Ablación; aísla una hipótesis concreta |

La clase de complejidad nunca se asigna por intuición: NP-difícil exige una reducción propia o una fuente primaria verificada. Para una heurística sobre un problema NP-difícil se informa por separado la clase del problema y el coste polinómico de la regla. Si no existe una cota total transferible, se declara el coste por actualización y su dependencia del número de iteraciones. Una ley de control o un certificado que no resuelve el problema combinatorio se marca como ``N/A'' en lugar de forzar una etiqueta P/NP.

Cada referencia debe existir en `references/LITERATURE_LEDGER.md`. Una fuente pendiente no respalda una afirmación fuerte. La tabla complementa el capítulo 5: compara métodos para la decisión concreta del SP, no vuelve a narrar todo el estado del arte.

La tabla maestra audita doce dimensiones: método/referencia, rol, arquitectura, paradigma, información o entrenamiento, Big-O, garantía aplicable, ventajas, desventajas, límite teórico, límite práctico y estado en el SP. Para respetar la legibilidad y el presupuesto VIU, el cuerpo puede agruparlas en las seis columnas anteriores, pero ninguna dimensión puede omitirse del párrafo crítico, la nota de tabla o la matriz de auditoría. Una tabla panorámica de doce columnas se reserva para el anexo cuando la agrupación produzca ambigüedad.

La celda de complejidad separa `tiempo; memoria; comunicación` y define sus variables. El tiempo de CPU medido pertenece a resultados, no a Big-O. El paradigma se clasifica como `model-based`, `data-driven` o híbrido; la arquitectura como centralizada, descentralizada, distribuida o híbrida. El estado distingue ejecutado/auditado, reproducido, proxy/adaptación, contextual no ejecutado y pendiente.

Una adaptación no hereda las garantías del método original. Debe rotularse “inspirada en” o “adaptación/proxy” y declarar qué cambio impide transferir automáticamente la prueba.


### 3.5 Juego distribuido e implementación

Este bloque describe el aporte estratégico y su implementación white-box. Debe incluir, cuando aplique:

1. jugadores o población y conjunto de acciones;
2. estado estratégico y estado local observado;
3. mensajes vecinales necesarios y supuestos de comunicación;
4. fitness de cada acción y payoff, con unidades e interpretación de cada término;
5. función potencial o función social y relación exacta con variaciones de payoff;
6. regla de actualización asíncrona, desempate y condición de parada;
7. lema, proposición o teorema con supuestos, síntesis interpretativa y referencia a su demostración completa en anexos; en su ausencia, marcar conjetura u observación empírica;
8. complejidad por agente, total y comunicativa;
9. diferencia entre dinámica matemática continua y ejecución digital muestreada;
10. trazabilidad técnica en los registros internos del repositorio, sin insertar en la prosa académica rutas, nombres de funciones, pruebas o detalles del código.

La memoria describe el mecanismo y su evidencia, no la estructura del repositorio. Las rutas, funciones, clases, pruebas unitarias y nombres de archivos se documentan en los planes y matrices de trazabilidad; no deben aparecer como comentarios meta en el texto final de un SP.

Las formulaciones y resultados producidos por este TFM se encierran en el entorno `contribucion`, cuyo borde naranja permite localizarlos visualmente. La marca significa aportación del trabajo dentro del alcance declarado; no acredita por sí sola prioridad universal, validez general ni un estado de evidencia superior al registrado en `docs/04_CLAIMS_EVIDENCE.md`. Las demostraciones completas se ubican en anexos para preservar el flujo del capítulo 6 y su límite de páginas; el cuerpo conserva el enunciado, los supuestos, una síntesis del argumento, la interpretación y la referencia al anexo.


La primera línea de cada caja usa `\estadoaporte{...}` y adopta una de cuatro categorías: `demostrado`, `validado empíricamente`, `propuesto` o `conjetural`. Puede combinar categorías si separa los componentes. Una caja propuesta es admisible para identificar autoría, pero debe indicar “evidencia pendiente” y no puede redactarse como resultado alcanzado.

La palabra “nuevo” solo significa formulación propia dentro del TFM. No acredita prioridad universal; cualquier afirmación de prioridad se limita al corpus bibliográfico verificado.

No usar indistintamente fitness, payoff, potencial y bienestar. Un Nash no se presenta como óptimo social, factible mecánicamente o seguro salvo prueba adicional.

### 3.6 Problema de control y acoplamiento estratégico y físico

El bloque no se limita al movimiento. Cada SP debe formular primero un problema de \emph{servorregulación estratégica}: la optimización define el conjunto o referencia deseada y la ley distribuida explica cómo el estado de decisión intenta alcanzarlo mediante feedback. Deben declararse:

1. estado estratégico y salida regulada;
2. referencia, conjunto objetivo o tolerancia alcanzable;
3. error que se desea llevar a cero; si la escasez impide error cero global, el conjunto alcanzable debe incorporar selección o abstención;
4. información medida, mensajes y variables estimadas por cada robot;
5. entrada estratégica, entendida como revisión de acción, flujo de preferencia, puja o precio;
6. ley de actualización continua y su ejecución digital, con activación, proyección, paso y condición de parada;
7. garantía disponible: estabilización del conjunto, convergencia, invariancia, cota o, si no existe prueba, formulación candidata claramente marcada;
8. relación con el problema de optimización: regular factibilidad no equivale necesariamente a seleccionar el óptimo social.


Cada SP mapea además su mecanismo sobre esta cadena común:

1. `OBSERVED`: estado propio y mediciones locales;
2. `ESTIMATED`: agregados inferidos, consenso o lecturas globales declaradas;
3. `RAW`: preferencias o masas continuas, aún no ejecutables;
4. `CLOSED`: decisión entera con exclusividad y cierre;
5. `GUARDED`: decisión que supera el certificado de capacidad, mecánica o seguridad aplicable;
6. `EXECUTED`: entrada aplicada a la planta con sensores, control y límites.

No se denomina distribuido a un pipeline si alguna etapa usa matrices o agregados globales sin declararlo; tampoco se denomina coalición a RAW, físicamente factible a CLOSED sin guardia, ni ejecutado a un perfil que no atraviesa la planta.

Cuando exista movimiento o interacción física, se añade una segunda capa, sin confundirla con la anterior:

1. modelo cinemático/dinámico y estado físico;
2. sensores, observadores y estimadores de pose, contacto o esfuerzo;
3. entrada de control y límites de actuador;
4. referencia producida por el juego o planificador;
5. ley de control, restricciones, seguridad y unidades;
6. modelo de contacto, formación o \emph{wrench};
7. candidato de Lyapunov, pasividad o certificado, con derivada/diferencia y conjunto invariante si se reclama estabilidad;
8. integrador, paso de muestreo, saturaciones y condiciones numéricas;
9. interfaz exacta entre decisión, estimación, control y comunicación.

En SP0--SP2 no existe todavía planta física, pero sí existe regulación estratégica de cobertura, cuota o capacidad. Debe formularse ese lazo y después delimitar que las poses solo parametrizan costes. No se fabrica una ley de movimiento ni se llama estabilidad física a la terminación de una dinámica estratégica finita.

### 3.7 Simulaciones

Definir antes de ejecutar:

- pregunta e hipótesis local;
- escenario, parámetros fijos y factores variables;
- configuración versionada y semillas explícitas;
- oráculo, baselines y ablaciones;
- información disponible para cada método;
- métricas únicas y unidades;
- número de ejecuciones y procedimiento estadístico;
- criterios de éxito, timeout, invalidez y fallo;
- rutas de datos crudos, procesados, tablas, figuras y manifiesto.

Todos los métodos deben recibir instancias pareadas. Un oráculo con información global se presenta como techo, no como comparación arquitectónica justa.

### 3.8 Resultados y comparaciones

Reportar distribuciones, tamaño muestral e intervalos de confianza, no solo medias. Incluir resultados negativos, ejecuciones no convergentes y violaciones. Separar:

En la prosa principal, cada párrafo cuantitativo debe priorizar una comparación y su interpretación, idealmente en dos frases: **el indicador cambió de A a B; por tanto, el resultado respalda o no respalda la afirmación concreta**. Cuando la tabla o el anexo ya recoge intervalos, valores $p$ y comparadores secundarios, no repetirlos todos en el párrafo; conservar en el cuerpo solo el detalle estadístico necesario para matizar la conclusión.

- verificación de la teoría o de invariantes;
- calidad de solución y gap al oráculo;
- coste computacional y de comunicación;
- efecto de la ablación;
- sensibilidad y región de fallo;
- amenazas a la validez y límites de generalización.

Las tablas y figuras cuantitativas deben generarse desde datos procesados; no se codifican resultados manualmente en LaTeX.

### 3.9 Conclusión y transición

El cierre debe indicar: hecho demostrado u observado, evidencia que lo sustenta, limitación principal y riesgo que pasa al siguiente SP. Usar lenguaje acorde al nivel de evidencia: demostrado, sustentado experimentalmente, no sustentado, refutado o pendiente.

## 4. Esqueleto LaTeX reutilizable

El siguiente esqueleto fija el orden, no el contenido matemático. Los comentarios deben sustituirse por información del SP y no permanecer en la versión final.

```latex
\clearpage
\subsection{SPX: título específico}
\label{subsec:spx}

% Párrafo introductorio: pregunta local, cambio incremental, supuestos,
% alcance/no alcance y nivel de evidencia.

\subsubsection{Esquema del subproblema}

% Párrafo que explica qué debe leerse en la figura.

\begin{figure}[H]
  \centering
  \begin{spdiagram}
    \spdrawarena{SPX \textbar\ descripción breve}
    % Nodos, arcos, anotaciones y leyenda con estilos SP comunes.
  \end{spdiagram}
  \caption{Vista conceptual de SPX: ...}
  \label{fig:spx-scenario}
  \viuownsource
\end{figure}

\subsubsection{Problema formal de referencia}

% Definir conjuntos, variables, dominios, parámetros y unidades.

\begin{equation}
\label{eq:spx-reference}
\begin{aligned}
  \operatorname*{minimize}_{z}\quad & J_X(z) \\
  \text{sujeto a}\quad & g_X(z)\leq 0,\\
  & h_X(z)=0,\\
  & z\in\mathcal Z_X.
\end{aligned}
\end{equation}

% Clasificar la ecuación: oráculo, baseline, evaluación o propuesta.
% Explicar factibilidad, complejidad y garantía sin sobreafirmar.

\subsubsection{Métodos y literatura comparada}

% Párrafo crítico que justifica los métodos seleccionados.

\begin{table}[H]
  \centering
  \caption{Métodos y literatura comparada para SPX.}
  \label{tab:spx-methods}
  \scriptsize
  \begin{tabularx}{\textwidth}{p{2.2cm} p{1.5cm} p{2.2cm} p{2.1cm} p{1.8cm} Y}
    \toprule
    Fuente/método & Clase & Coste & Arquitectura & Parámetros & Garantía/límite \\
    \midrule
    % Añadir solo fuentes verificadas y la propuesta/ablación del TFM.
    \bottomrule
  \end{tabularx}
  \viuownsource
\end{table}

\subsubsection{Juego distribuido propuesto e implementación}

% Jugadores, acciones, información, mensajes, fitness/payoff, potencial,
% actualización, resultado formal marcado con el entorno contribucion, enlace
% a la demostración en anexos y complejidad. La trazabilidad técnica queda
% en los documentos internos, no en la prosa de la memoria.

\subsubsection{Problema de control y acoplamiento}

% Primero: salida estratégica, referencia, error, feedback/estimador, entrada de
% revisión, ley muestreada y garantía. Después, si existe planta: estado físico,
% sensores, entrada, ley, restricciones, certificado e interfaz entre capas.

\subsubsection{Protocolo de simulación}

% Hipótesis, escenarios, configuración, factores, semillas, baselines,
% ablaciones, métricas, estadística, fallos y rutas de artefactos.

\subsubsection{Resultados y comparación}

% Tablas/figuras generadas, intervalos, gap, ablación, fallos,
% contraste con teoría y amenazas a la validez.

\subsubsection{Conclusión y transición}

% Respuesta local, evidencia, limitación y cambio que hereda SPX+1.
```

## 5. Adaptación mínima por escalón

| SP | Núcleo estratégico | Bloque de control/acoplamiento |
|---|---|---|
| SP0 | Asignación uno-a-uno homogénea | Regular déficit y duplicidad a cero; poses estáticas y sin transporte |
| SP1 | Cardinalidad variable | Regular error de cuota/cierre; bajo escasez, referencia seleccionada todo-o-nada; sin planta física |
| SP2 | Capacidades y requisitos heterogéneos | Regular déficit de capacidad mediante una estimación de capacidad agregada; sin ejecución mecánica |
| SP3 | Certificado de coalición físicamente ejecutable | Regular residual de wrench y congestión de slots; añadir docking, soporte/contacto y sensores de la modalidad |
| SP4 | Selección acoplada con transporte origen--destino | Seguimiento de pose y estabilidad del cuerpo/carga |
| SP5 | Decisión compatible con seguridad | CBF-QP, ORCA u otra capa según modelo y modalidad |
| SP6 | Re-reclutamiento tras fallo | Reconfiguración y recuperación física |
| SP7 | Juego de tráfico o prioridad | Evitación multi-coalición y resolución de conflictos |
| SP8 | Política local bajo red imperfecta y escala | Efecto de muestreo, retardo y pérdidas sobre ejecución/control |

## 6. Lista de cierre de un SP

- [ ] El título y el primer párrafo definen el incremento respecto al SP anterior.
- [ ] El SP comienza en una página nueva y no comparte su página inicial con el SP anterior.
- [ ] El diagrama compila, se cita en el texto, usa estilos comunes y es legible en A4.
- [ ] El problema de optimización está clasificado y todas sus variables tienen dominio y unidades.
- [ ] La tabla compara literatura verificada, propuesta, oráculo/baseline y ablación.
- [ ] El juego define información local, payoff/fitness, potencial, actualización y coste.
- [ ] Toda garantía formal incluye supuestos, síntesis y enlace a su demostración completa en anexos; lo no probado se etiqueta honestamente.
- [ ] Toda formulación o resultado propio usa la caja naranja `contribucion`; la literatura y las afirmaciones pendientes quedan fuera de ella.
- [ ] La servorregulación estratégica declara salida, referencia, error, feedback/estimador, entrada, ley y garantía o limitación.
- [ ] Cuando existe planta física, su servocontrol se formula por separado con sensores, actuadores, restricciones e interfaz con el juego.
- [ ] La ejecución digital declara muestreo, integrador y saturaciones cuando corresponda.
- [ ] Las simulaciones son reproducibles con configuración y semillas versionadas.
- [ ] Las comparaciones usan casos pareados, incertidumbre y fallos registrados.
- [ ] Tablas y figuras cuantitativas proceden de datos, no de valores escritos manualmente.
- [ ] La conclusión distingue hecho, evidencia, limitación y transición.
- [ ] `docs/04_CLAIMS_EVIDENCE.md`, `docs/05_NOTATION.md` y el ledger bibliográfico están sincronizados.
- [ ] Las pruebas pertinentes y la compilación/revisión visual del PDF pasan.
