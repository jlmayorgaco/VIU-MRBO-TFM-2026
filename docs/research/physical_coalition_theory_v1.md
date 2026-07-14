# Teorema de cierre físico y certificado ISS práctico

## Modelo

Para una carga plana rígida, (q=(x,y,\theta)), se adopta

\[
M\ddot q + D\dot q = w_c + d,
\]

con (M\succ0), (D\succeq0), wrench cooperativo realizado (w_c) y error agregado (d). Una coalición (S) supera sucesivamente: cardinalidad entera, capacidad efectiva, pertenencia aproximada del wrench estático al cono acotado de contacto, autoridad dinámica y seguridad HOCBF, y recuperación local acotada.

## Proposición 1 — necesidad de capacidad

Si \(\sum_{i\in S} c_i h_i<C_{\rm req}\), ninguna redistribución interna de la coalición satisface la demanda escalar de capacidad. La prueba sigue de aditividad y no negatividad. Es una condición necesaria, no suficiente para transporte.

## Proposición 2 — certificado de wrench

Sea \(G_S\) la matriz de grasp y \(0\le f\le \bar f\). La distancia normalizada

\[
\rho_S(w)=\frac{\min_{0\le f\le\bar f}\|G_Sf-w\|_2}{\max(\|w\|_2,\varepsilon)}
\]

se usa únicamente como certificado estático. \(\rho_S\le\epsilon_w\) no implica por sí sola seguimiento dinámico, seguridad ni recuperación; esa separación es precisamente la hipótesis sometida a contraste por A3 frente a A4 y FULL.

## Teorema 1 — ISS práctica común bajo cambio de coalición

Considérese el error \(z=(e,\dot e)\) del lazo PD de la carga con matriz cerrada Hurwitz

\[
\dot z=Az+Bd_{\sigma(t)},
\]

sin reset de estado al cambiar la coalición y con \(\|d_{\sigma(t)}\|\le\bar d\). Si existe \(P\succ0\) común tal que \(A^\top P+PA=-I\), entonces, para cualquier conmutación medible \(\sigma(t)\),

\[
\dot V\le-\alpha V+\sigma_d\bar d^2,
\quad V=z^\top Pz,
\]

con

\[
\alpha=\frac{1-\varepsilon}{\lambda_{\max}(P)},
\qquad
\sigma_d=\frac{\|PB\|_2^2}{\varepsilon},
\quad 0<\varepsilon<1.
\]

Por comparación,

\[
\|z(t)\|\le
\sqrt{\frac{V(0)e^{-\alpha t}+(\sigma_d/\alpha)\bar d^2(1-e^{-\alpha t})}{\lambda_{\min}(P)}}.
\]

Así, el seguimiento es ISS práctico y converge a una bola proporcional a \(\bar d\). No se necesita dwell time porque la coalición modifica la entrada de realización del wrench, no la matriz \(A\), y no existe salto de estado. Si cambian masa, ganancias o se reinicia el estado, este teorema deja de aplicar y sería necesario un argumento de Lyapunov múltiple.

## Seguridad

Para un obstáculo circular, (h(p)=\|p-c\|^2-R^2\). El filtro exige

\[
\ddot h+(k_1+k_2)\dot h+k_1k_2h\ge0,
\]

una restricción afín sobre la aceleración. La proyección HOCBF certifica invariancia solo con estado inicialmente seguro y aceleración proyectada realizable. Por ello el experimento comprueba además el clearance de la trayectoria; no convierte la mera resolución del filtro en éxito físico.

## Alcance honesto

El resultado es fuerte para la carga fija con error de wrench acotado y cambio sin reset. No demuestra estabilidad de coaliciones arbitrarias con dinámica propia cambiante, no convierte PoA observado en cota y no prueba validez física fuera del simulador numérico especificado.