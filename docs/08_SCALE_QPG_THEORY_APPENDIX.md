# Apéndice teórico de SCALE-QPG

## Alcance

Este apéndice delimita la propiedad formal usada por
`SCALE-QPG-LogitBR-LocalAR`. Solo se refiere a la fase determinista de
revisiones atómicas con mundo, cuotas, costes, compatibilidad, conjunto activo
y asignación previa congelados. No demuestra optimalidad social, factibilidad
final, convergencia de la exploración Logit, completitud del recovery ni
estabilidad de una planta física.

## Estado y potencial

Sea \(\mathcal S=\prod_i(\mathcal A_i\cup\{0\})\) el conjunto finito de
compromisos enteros compatibles. Para \(s\in\mathcal S\),

\[
Q_k(s)=\sum_{i:s_i=k}\chi_i,
\]

\[
V_k(Q)=
-\frac{\rho_-}{2}[\underline m_k-Q]_+^2
-\frac{\rho_+}{2}[Q-\overline m_k]_+^2,
\]

y

\[
\Phi_t(s)=
\sum_k V_k(Q_k(s))
-\sum_{i:s_i\ne0}\widehat c_{i,s_i}
-\gamma_{\mathrm{sw}}
\sum_i\mathbf 1\{s_i\ne s_i^{\mathrm{prev}}\}.
\]

Una propuesta unilateral \(h\to k\) usa la diferencia finita exacta
\(\Delta_i=\Phi_t(s^{i\to k})-\Phi_t(s)\). El precio marginal se usa solo para
construir el conjunto activo sparse; no sustituye a esta diferencia en el
criterio de aceptación.

## Proposición: terminación finita de strict-BR

**Proposición.** Supóngase que durante la fase strict-BR:

1. \(\mathcal S\) es finito;
2. los costes, cuotas, capacidades, compatibilidades, asignación previa y
   conjuntos activos permanecen congelados entre revisiones aceptadas, salvo
   las versiones derivadas del propio compromiso;
3. el protocolo serializa cada compromiso y no acepta una propuesta con
   versiones obsoletas;
4. toda revisión aceptada satisface
   \(\Delta_i>\varepsilon_{\mathrm{imp}}>0\).

Entonces la fase no contiene ciclos de compromisos y termina después de un
número finito de movimientos aceptados en un estado sin mejora unilateral
admisible mayor que \(\varepsilon_{\mathrm{imp}}\) respecto a los conjuntos
activos vigentes.

**Demostración.** Cada compromiso aceptado produce
\(\Phi_t(s^{r+1})>\Phi_t(s^r)+\varepsilon_{\mathrm{imp}}\), por lo que la
sucesión de valores del potencial es estrictamente creciente. Si un estado se
repitiera, el potencial —función unívoca del estado y de los datos congelados—
también se repetiría, contradiciendo el crecimiento estricto. Como
\(\mathcal S\) es finito, no puede existir una sucesión infinita de estados
distintos. Por tanto, tras un número finito de aceptaciones se completa una
época sin movimiento admisible. El estado terminal solo es equilibrio respecto
al vecindario sparse y al umbral declarados. \(\square\)

## Corolarios que no se siguen

La proposición no implica:

- que el estado terminal cumpla todas las cuotas;
- que sea un equilibrio respecto a cargas fuera de \(\mathcal A_i\);
- que minimice distancia o `all_world_cost`;
- que coincida con el MILP;
- que LocalAR encuentre una solución aunque exista globalmente;
- que la ejecución asíncrona sea libre de retardo o fallos reales.

Estas propiedades se evalúan empíricamente y se clasifican por separado.

## Compromiso en dos fases

Una propuesta contiene robot, origen, destino, capacidad, diferencia exacta,
versiones de ambos mercados y activación lógica. `prepare` reserva capacidad
sin alterar \(s_i\). `commit` modifica origen y destino de forma atómica si las
versiones siguen vigentes. Timeout, conflicto o cambio de asignación ejecuta
rollback. En la simulación, un robot tiene exactamente un entero `commitment`;
la reserva nunca crea un segundo compromiso físico.

## Recuperación local

El universo residual comienza en las cargas afectadas o violadas. Cada capa
añade robots que tienen esas cargas en su conjunto activo o compromiso y,
después, las cargas actuales/activas de esos robots. Fuera del radio \(h\), la
compatibilidad se congela a la asignación actual. El buscador aumentante usa
longitud máxima \(H\), nodos y tiempo acotados. Por ello, un fallo local es
evidencia de los límites declarados, no prueba de inviabilidad global.
