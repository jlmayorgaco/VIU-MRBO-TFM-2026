"""Juego continuo de trayectorias en horizonte deslizante (addendum R6, ecs. 43-56).

Cada jugador a (coalición en transporte o AMR libre) mantiene una continuación
X_a = (x_1..x_N) sobre N nodos separados Delta s, y la deforma en tiempo de cálculo
por gradiente proyectado del coste
   J_a = w_f |x_N - g|^2 + w_p sum_k |x_k - g|^2 / N            (tiempo / progreso)
       + w_s sum_k |x_{k+1} - 2x_k + x_{k-1}|^2                   (suavidad, esfuerzo)
       + w_v sum_k [ |x_{k+1}-x_k| - v_max Delta ]_+^2            (límite físico de velocidad)
       + w_o sum_k [ d_safe - c_k ]_+^2                           (barrera de paredes)
       + w_o sum_k sum_l [ d_safe - dist(x_k, carga l) ]_+^2      (cargas ajenas como obstáculos)
       + w_c sum_k sum_b [ d_ab - |x_k - y^b_k| ]_+^2             (externalidad atómica con las
                                                                   continuaciones publicadas de los otros)
El término de interacción es simétrico por pares: el juego es de potencial exacto
(th:externalidad-atomica). La primera velocidad de la continuación es el comando.
"""
from __future__ import annotations
import numpy as np


class TrajPlayer:
    def __init__(self, N=12, delta=0.5, v_max=0.6, r=0.6, d_safe=0.3, w=None):
        self.N, self.delta, self.v_max, self.r, self.d_safe = N, delta, v_max, r, d_safe
        self.w = dict(f=1.0, p=0.15, s=6.0, v=30.0, o=40.0, c=25.0, e=0.6)
        if w: self.w.update(w)
        self.X = None; self.t_anchor = None

    # ----- utilidades geométricas
    @staticmethod
    def wall_clearance(p, rects):
        best = 1e9; bn = np.zeros(2)
        for (x0, x1, y0, y1) in rects:
            cx = np.clip(p[0], x0, x1); cy = np.clip(p[1], y0, y1)
            d = p - np.array([cx, cy]); dist = np.linalg.norm(d)
            if dist < best:
                best = dist; bn = d / dist if dist > 1e-9 else np.array([0.0, 1.0])
        return best, bn

    def init(self, p0, goal, t):
        """Recta hacia el objetivo a velocidad máxima (única propuesta inicial, ec. 43)."""
        d = goal - p0; L = np.linalg.norm(d); u = d / (L + 1e-9)
        s = np.minimum(np.arange(1, self.N + 1) * self.v_max * self.delta, L)
        self.X = p0[None, :] + s[:, None] * u[None, :]; self.t_anchor = t

    def shift(self, p0, t):
        """Warm start: desplazar la continuación conforme avanza el tiempo físico."""
        if self.X is None: return
        k = int((t - self.t_anchor) // self.delta)
        if k >= 1:
            k = min(k, self.N - 1)
            last = self.X[-1]
            self.X = np.vstack([self.X[k:], np.repeat(last[None, :], k, axis=0)]); self.t_anchor += k * self.delta

    def cost_grad(self, p0, goal, rects, obstacles, others):
        """Coste y gradiente respecto de X (N x 2). obstacles: lista (centro, radio) de cargas ajenas;
        others: lista de (Y (N x 2), radio) continuaciones publicadas por otros jugadores."""
        X = self.X; N = self.N; w = self.w; dl = self.delta
        G = np.zeros_like(X); J = 0.0
        # terminal y progreso
        e = X[-1] - goal; J += w["f"] * e @ e; G[-1] += 2 * w["f"] * e
        E = X - goal[None, :]; J += w["p"] / N * np.sum(E * E); G += 2 * w["p"] / N * E
        # suavidad (aceleración) con x_0 = p0
        Xa = np.vstack([p0[None, :], X]); acc = Xa[2:] - 2 * Xa[1:-1] + Xa[:-2]
        J += w["s"] * np.sum(acc * acc)
        Ga = np.zeros_like(Xa); Ga[2:] += 2 * w["s"] * acc; Ga[1:-1] += -4 * w["s"] * acc; Ga[:-2] += 2 * w["s"] * acc
        G += Ga[1:]
        # límite de velocidad
        dX = Xa[1:] - Xa[:-1]; sp = np.linalg.norm(dX, axis=1) + 1e-9; exc = np.maximum(sp - self.v_max * dl, 0.0)
        J += w["v"] * np.sum(exc ** 2)
        gv = (2 * w["v"] * exc / sp)[:, None] * dX      # d/d(x_{k+1})
        G += gv; G[:-1] -= gv[1:]
        # esfuerzo: moverse cuesta; ceder significa frenar, no dar vueltas
        J += w["e"] * np.sum(dX * dX); ge = 2 * w["e"] * dX; G += ge; G[:-1] -= ge[1:]
        # paredes
        for k in range(N):
            c, n = self.wall_clearance(X[k], rects); c -= self.r
            if c < self.d_safe:
                J += w["o"] * (self.d_safe - c) ** 2; G[k] += -2 * w["o"] * (self.d_safe - c) * n
        # cargas ajenas (círculos envolventes)
        for (pc, rc) in obstacles:
            d = X - pc[None, :]; dist = np.linalg.norm(d, axis=1) + 1e-9; gap = dist - rc - self.r
            m = gap < self.d_safe
            if np.any(m):
                J += w["o"] * np.sum((self.d_safe - gap[m]) ** 2)
                G[m] += (-2 * w["o"] * (self.d_safe - gap[m]) / dist[m])[:, None] * d[m]
        # otros jugadores (mismo índice temporal): externalidad atómica exacta
        tk = np.arange(1, N + 1) * dl
        for (Y, rb, dlo) in others:
            to = np.arange(1, len(Y) + 1) * dlo      # re-muestrear la continuación ajena en mis instantes
            Yi = np.stack([np.interp(tk, to, Y[:, 0]), np.interp(tk, to, Y[:, 1])], axis=1)
            d = X - Yi; dist = np.linalg.norm(d, axis=1) + 1e-9; gap = dist - rb - self.r
            m = gap < self.d_safe
            if np.any(m):
                J += w["c"] * np.sum((self.d_safe - gap[m]) ** 2)
                G[m] += (-2 * w["c"] * (self.d_safe - gap[m]) / dist[m])[:, None] * d[m]
        return J, G

    def step(self, p0, goal, t, rects, obstacles, others, iters=25, lr=0.05):
        """Unas iteraciones de deformación en tiempo de cálculo (ec. 53). Devuelve la velocidad comandada."""
        if self.X is None: self.init(p0, goal, t)
        else: self.shift(p0, t)
        # re-anclar el primer nodo si la planta se ha desviado mucho
        if np.linalg.norm(self.X[0] - p0) > 1.5 * self.v_max * self.delta + 0.5: self.init(p0, goal, t)
        J = None
        for _ in range(iters):
            J, G = self.cost_grad(p0, goal, rects, obstacles, others)
            gn = np.linalg.norm(G) + 1e-9
            self.X = self.X - lr * G / max(1.0, gn / (4.0 * self.N))     # paso normalizado (gradiente proyectado en R^2N)
        v = (self.X[0] - p0) / self.delta
        sv = np.linalg.norm(v)
        if sv > self.v_max: v = v * self.v_max / sv
        return v, J
