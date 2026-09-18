"""Planta 2D con ruedas dinámicas, cargas rígidas y contacto (cargo / caging).

Modelo declarado (todo lo que el mecanismo puede y no puede suponer):
  * AMR diferencial: chasis (x, y, th, v, w) + dos ruedas con inercia J_w.
      J_w dw_s/dt = tau_s - r_w F_s - b_w w_s,   F_s = tracción de la rueda s
      F_s = clip(c_g (r_w w_s - v_s), disco de fricción compartido con la lateral)
      m dv/dt = F_L + F_R - b_v v + e^T f_contacto
      I dw/dt = (F_R - F_L) b/2 + par de contacto
    La restricción lateral del chasis es ideal (sin deslizamiento lateral) salvo
    que la fuerza lateral requerida exceda el presupuesto del disco: entonces se
    registra un evento de deslizamiento y la fuerza lateral se satura.
  * Carga: cuerpo rígido (x, y, th, V, W) con huella rectangular.
  * cargo: pad en punto fijo de la carga; f = k eps + d u (eps = desplazamiento
    pad–anclaje, u = velocidad relativa); límite mu_top N_i con N_i = m g / n.
  * caging (empuje perimetral): parachoques circular del AMR contra el borde
    de la carga; f_n = k_b [delta]_+, |f_t| <= mu_b f_n; no hay tracción a distancia.
  * Paredes: penetración registrada como violación; fuerza de penalización.
Unidades SI. Integración semi-implícita con paso dt.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field

G = 9.81


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def rot(th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, -s], [s, c]])


@dataclass
class Walls:
    """Rectángulos sólidos (xmin, xmax, ymin, ymax)."""
    rects: list

    def penetration(self, p, radius):
        """Devuelve (profundidad, normal) máxima de un disco contra los muros."""
        best = (0.0, np.zeros(2))
        for (x0, x1, y0, y1) in self.rects:
            cx = np.clip(p[0], x0, x1); cy = np.clip(p[1], y0, y1)
            d = p - np.array([cx, cy]); dist = np.linalg.norm(d)
            if dist < 1e-9:  # centro dentro del muro
                # empuja hacia la cara más cercana
                dx = min(p[0] - x0, x1 - p[0]); dy = min(p[1] - y0, y1 - p[1])
                n = np.array([np.sign(p[0] - (x0 + x1) / 2) or 1.0, 0.0]) if dx < dy else np.array([0.0, np.sign(p[1] - (y0 + y1) / 2) or 1.0])
                depth = radius + min(dx, dy)
            else:
                depth = radius - dist; n = d / dist
            if depth > best[0]:
                best = (depth, n)
        return best

    def clearance(self, p):
        best = 1e9
        for (x0, x1, y0, y1) in self.rects:
            cx = np.clip(p[0], x0, x1); cy = np.clip(p[1], y0, y1)
            best = min(best, np.hypot(p[0] - cx, p[1] - cy))
        return best


@dataclass
class AMRParams:
    m: float; I: float; r_w: float; b: float; J_w: float; tau_max: float
    c_g: float; mu: float; b_v: float; b_w: float; R: float; cap: float; E0: float
    v_max: float = 1.2; w_max: float = 2.0


@dataclass
class LoadParams:
    m: float; I: float; L: float; W: float; mu_top: float; k_pad: float; d_pad: float
    k_b: float; mu_b: float; r_req: int; B: float; goal: np.ndarray; modes: tuple
    mu_f: float = 0.2


@dataclass
class Plant:
    amr: list
    loads: list
    walls: Walls
    dt: float = 0.005
    # estados
    q: np.ndarray = field(default=None)      # N x 3 (x,y,th)
    eta: np.ndarray = field(default=None)    # N x 2 (v,w)
    ww: np.ndarray = field(default=None)     # N x 2 (w_L, w_R)
    E: np.ndarray = field(default=None)      # batería J
    ql: np.ndarray = field(default=None)     # K x 3
    zl: np.ndarray = field(default=None)     # K x 3 (Vx,Vy,W)
    t: float = 0.0
    # registro
    slip_events: int = 0
    wall_pen_max: float = 0.0
    wall_pen_count: int = 0
    min_sep_amr: float = 1e9
    min_sep_load: float = 1e9
    energy: float = 0.0
    # contacto en cargo: anclajes por (i) -> (k, r_body) ; pads fijados al acoplar
    attach: dict = field(default_factory=dict)
    pad_eps: dict = field(default_factory=dict)
    caging_contacts: int = 0
    caging_steps: int = 0

    def __post_init__(self):
        N, K = len(self.amr), len(self.loads)
        self.q = np.zeros((N, 3)); self.eta = np.zeros((N, 2)); self.ww = np.zeros((N, 2))
        self.E = np.array([a.E0 for a in self.amr], float)
        self.ql = np.zeros((K, 3)); self.zl = np.zeros((K, 3))

    # ----- geometría de la carga
    def load_corners(self, k):
        L, W = self.loads[k].L, self.loads[k].W
        c = np.array([[L / 2, W / 2], [-L / 2, W / 2], [-L / 2, -W / 2], [L / 2, -W / 2]])
        Rm = rot(self.ql[k, 2]); return self.ql[k, :2] + c @ Rm.T

    def load_body_to_world(self, k, r):
        return self.ql[k, :2] + rot(self.ql[k, 2]) @ r

    def load_point_vel(self, k, p_world):
        r = p_world - self.ql[k, :2]; W = self.zl[k, 2]
        return self.zl[k, :2] + W * np.array([-r[1], r[0]])

    def disc_vs_rect(self, p, radius, k):
        """Penetración (delta, normal hacia fuera de la carga) de un disco contra la carga k."""
        Rm = rot(self.ql[k, 2]); pl = Rm.T @ (p - self.ql[k, :2])
        L, W = self.loads[k].L / 2, self.loads[k].W / 2
        cx, cy = np.clip(pl[0], -L, L), np.clip(pl[1], -W, W)
        d = pl - np.array([cx, cy]); dist = np.linalg.norm(d)
        if dist < 1e-9:
            return radius + min(L - abs(pl[0]), W - abs(pl[1])), Rm @ np.array([np.sign(pl[0]) or 1, 0.0])
        return radius - dist, Rm @ (d / dist)

    def obb_separation(self, k, l):
        """Separación (SAT) entre las huellas rectangulares de las cargas k y l: (>0 hueco, <0 penetración) y normal k<-l."""
        ck, cl = self.load_corners(k), self.load_corners(l)
        axes = []
        for c in (ck, cl):
            for a in (c[1] - c[0], c[3] - c[0]):
                axes.append(a / (np.linalg.norm(a) + 1e-12))
        best = (-1e9, np.zeros(2))
        for ax in axes:
            pk, pl = ck @ ax, cl @ ax
            gap = max(pl.min() - pk.max(), pk.min() - pl.max())
            if gap > best[0]:
                n = ax if (self.ql[k, :2] - self.ql[l, :2]) @ ax > 0 else -ax
                best = (gap, n)
        return best

    # ----- acoplamiento cargo
    def attach_pad(self, i, k, r_body):
        self.attach[i] = (k, np.array(r_body, float)); self.pad_eps[i] = np.zeros(2)

    def detach(self, i):
        self.attach.pop(i, None); self.pad_eps.pop(i, None)

    # ----- paso de integración
    def step(self, tau, caging_members, groups=None):
        """tau: N x 2 pares de rueda (L,R). caging_members: dict k -> set(i) en modo empuje.
        groups: dict i -> k (coalición a la que pertenece i), exenta de repulsión interna."""
        groups = groups or {}
        dt = self.dt; N = len(self.amr); K = len(self.loads)
        f_amr = np.zeros((N, 2)); m_amr = np.zeros(N)
        f_load = np.zeros((K, 2)); m_load = np.zeros(K)
        # --- contactos cargo (pads)
        for i, (k, rb) in self.attach.items():
            a = self.amr[i]; ld = self.loads[k]
            anchor = self.load_body_to_world(k, rb)
            p = self.q[i, :2]
            eps = anchor - p                      # desplazamiento pad (anclaje - amr)
            v_anchor = self.load_point_vel(k, anchor)
            v_amr = self.eta[i, 0] * np.array([np.cos(self.q[i, 2]), np.sin(self.q[i, 2])])
            u = v_anchor - v_amr
            f = ld.k_pad * eps + ld.d_pad * u     # fuerza sobre el AMR (tira hacia el anclaje)
            n_members = max(1, sum(1 for j, (kk, _) in self.attach.items() if kk == k))
            Nn = ld.m * G / n_members
            fn = np.linalg.norm(f); fmax = ld.mu_top * Nn
            if fn > fmax:
                f = f * (fmax / fn); self.slip_events += 1
            f_amr[i] += f
            f_load[k] -= f
            r = anchor - self.ql[k, :2]; m_load[k] -= r[0] * f[1] - r[1] * f[0]
            self.pad_eps[i] = eps
        # --- contactos caging (parachoques contra la carga)
        for k, members in caging_members.items():
            ld = self.loads[k]
            for i in members:
                a = self.amr[i]; p = self.q[i, :2]
                delta, n = self.disc_vs_rect(p, a.R, k)
                if delta > 0:
                    v_amr = self.eta[i, 0] * np.array([np.cos(self.q[i, 2]), np.sin(self.q[i, 2])])
                    cp = p - n * (a.R - delta / 2)
                    v_cp = self.load_point_vel(k, cp)
                    fn = ld.k_b * delta + 30.0 * max(0.0, (v_amr - v_cp) @ (-n))
                    tvec = np.array([-n[1], n[0]]); vrel_t = (v_amr - v_cp) @ tvec
                    ft = -np.clip(200.0 * vrel_t, -ld.mu_b * fn, ld.mu_b * fn)
                    F = -fn * n + ft * tvec          # sobre la carga: empuje hacia dentro (−n)
                    f_load[k] += F; r = cp - self.ql[k, :2]; m_load[k] += r[0] * F[1] - r[1] * F[0]
                    f_amr[i] -= F
                    self.caging_contacts += 1
            self.caging_steps += 1
        # --- paredes: cargas
        for k in range(K):
            for c in self.load_corners(k):
                depth, n = self.walls.penetration(c, 0.0)
                if depth > 0:
                    self.wall_pen_max = max(self.wall_pen_max, depth); self.wall_pen_count += 1
                    F = 4000.0 * depth * n - 200.0 * (self.load_point_vel(k, c) @ n) * n
                    f_load[k] += F; r = c - self.ql[k, :2]; m_load[k] += r[0] * F[1] - r[1] * F[0]
        # --- paredes: AMR
        for i in range(N):
            depth, n = self.walls.penetration(self.q[i, :2], self.amr[i].R)
            if depth > 0:
                self.wall_pen_max = max(self.wall_pen_max, depth); self.wall_pen_count += 1
                f_amr[i] += 4000.0 * depth * n
        # --- separaciones (monitor)
        for i in range(N):
            for j in range(i + 1, N):
                d = np.linalg.norm(self.q[i, :2] - self.q[j, :2]) - self.amr[i].R - self.amr[j].R
                same = (i in groups and j in groups and groups[i] == groups[j] and i in self.attach and j in self.attach)
                if not same: self.min_sep_amr = min(self.min_sep_amr, d)
                if d < 0 and not same:  # colisión AMR-AMR: repulsión
                    n = (self.q[i, :2] - self.q[j, :2]); n /= (np.linalg.norm(n) + 1e-9)
                    f_amr[i] += 3000.0 * (-d) * n; f_amr[j] -= 3000.0 * (-d) * n
        # AMR no miembro contra carga: repulsión (no puede atravesarla)
        for i in range(N):
            for k in range(K):
                if groups.get(i) == k: continue
                delta, n = self.disc_vs_rect(self.q[i, :2], self.amr[i].R, k)
                if delta > 0:
                    v_amr = self.eta[i, 0] * np.array([np.cos(self.q[i, 2]), np.sin(self.q[i, 2])])
                    F = 6000.0 * delta * n + 60.0 * max(0.0, -(v_amr @ n)) * n; f_amr[i] += F; f_load[k] -= F
                    r = self.q[i, :2] - n * self.amr[i].R - self.ql[k, :2]; m_load[k] -= r[0] * F[1] - r[1] * F[0]
        for k in range(K):
            for l in range(k + 1, K):
                d, n = self.obb_separation(k, l)
                self.min_sep_load = min(self.min_sep_load, d)
                if d < 0:   # contacto carga-carga (huellas rectangulares, SAT): repulsión
                    F = 4000.0 * (-d) * n - 100.0 * ((self.zl[k, :2] - self.zl[l, :2]) @ n) * n
                    f_load[k] += F; f_load[l] -= F
        # --- dinámica de ruedas y chasis
        for i in range(N):
            a = self.amr[i]; th = self.q[i, 2]; e = np.array([np.cos(th), np.sin(th)]); en = np.array([-np.sin(th), np.cos(th)])
            v, w = self.eta[i]
            v_s = v + np.array([-1, 1]) * w * a.b / 2           # velocidad longitudinal de cada rueda
            slipv = a.r_w * self.ww[i] - v_s
            F_long = a.c_g * slipv
            # fuerza lateral requerida para mantener la restricción (centrípeta + contacto lateral)
            f_lat_req = a.m * v * w - (f_amr[i] @ en)
            N_wheel = a.m * G / 2
            f_lat_wheel = f_lat_req / 2
            for s in range(2):
                budget = a.mu * N_wheel
                mag = np.hypot(F_long[s], f_lat_wheel)
                if mag > budget:
                    F_long[s] *= budget / mag; self.slip_events += 1
            tau_i = np.clip(tau[i], -a.tau_max, a.tau_max)
            dww = (tau_i - a.r_w * F_long - a.b_w * self.ww[i]) / a.J_w
            self.ww[i] += dt * dww
            F_tot = F_long.sum() - a.b_v * v + f_amr[i] @ e
            dv = F_tot / a.m
            dw = ((F_long[1] - F_long[0]) * a.b / 2 + m_amr[i]) / a.I
            v += dt * dv; w += dt * dw
            v = np.clip(v, -a.v_max * 1.5, a.v_max * 1.5); w = np.clip(w, -a.w_max * 1.5, a.w_max * 1.5)
            self.eta[i] = (v, w)
            self.q[i, 0] += dt * v * np.cos(th); self.q[i, 1] += dt * v * np.sin(th); self.q[i, 2] = wrap(th + dt * w)
            # energía eléctrica: [tau*omega]_+ / eta_m + pérdidas
            Pm = np.sum(np.maximum(tau_i * self.ww[i], 0.0)) / 0.8 + 15.0
            self.E[i] -= dt * Pm; self.energy += dt * Pm
        # --- dinámica de cargas
        for k in range(K):
            ld = self.loads[k]
            lifted = (ld.modes[0] == "cargo") and (sum(1 for j, (kk, _) in self.attach.items() if kk == k) >= ld.r_req)
            if not lifted:   # fricción de Coulomb con el suelo (regularizada) en traslación y giro
                V = self.zl[k, :2]; sp = np.linalg.norm(V)
                if sp < 0.02 and np.linalg.norm(f_load[k]) < ld.mu_f * ld.m * G:  # adherencia estática
                    f_load[k] = np.zeros(2); self.zl[k, :2] *= 0.0
                else:
                    f_load[k] += -ld.mu_f * ld.m * G * V / max(sp, 0.02)
                m_load[k] += -ld.mu_f * ld.m * G * 0.12 * max(ld.L, ld.W) * self.zl[k, 2] / max(abs(self.zl[k, 2]), 0.05)
            self.zl[k, :2] += dt * (f_load[k] - 8.0 * self.zl[k, :2]) / ld.m
            self.zl[k, 2] += dt * (m_load[k] - 4.0 * self.zl[k, 2]) / ld.I
            self.ql[k, :2] += dt * self.zl[k, :2]; self.ql[k, 2] = wrap(self.ql[k, 2] + dt * self.zl[k, 2])
        self.t += dt
