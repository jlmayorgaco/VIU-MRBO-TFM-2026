"""Mecanismo distribuido: megajuego híbrido de n saltos sobre la planta.

Cada AMR decide con la información de sus n saltos en el grafo de comunicación:
  * capa discreta z_i in {idle} U {(k, modo, puesto)} revisada por un protocolo
    (best_response | smith | bnn | logit | replicator) sobre el potencial exacto
    Phi (construcción de utilidad marginal: J_i = Phi(z) - Phi(idle_i, z_{-i}));
  * aptitud (fitness) de una coalición: 'vector' (margen de wrench por columnas de
    contacto, unilateral en caging) o 'scalar' (suma de capacidades);
  * mercado de wrench por coalición: precio dual p_k, respuesta local de cada
    miembro con sus límites, varias rondas por paso físico (T_wrench < T_phys);
  * trayectoria y pasillo: 'lease' (arrendamiento exclusivo con orden total) o
    'price' (precio de congestión sin exclusividad);
  * seguridad: 'nested' (barrera de coalición + barrera por AMR), 'coalition'
    (solo coalición) o 'none';
  * hiperjuego: creencias erróneas sobre masas/capacidades con o sin
    recertificación al formar;
  * 'gne_pd': reclutamiento como shares continuos con multiplicadores (PDM) y
    atomización posterior.
Todo mensaje intercambiado se cuenta.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from .plant import Plant, rot, wrap, G
from .trajgame import TrajPlayer

IDLE = None


@dataclass
class Config:
    protocol: str = "smith"          # best_response|smith|bnn|logit|replicator
    fitness: str = "vector"          # vector|scalar
    corridor: str = "lease"          # lease|price
    safety: str = "nested"           # nested|coalition|none
    recruit: str = "atomic"          # atomic|gne_pd
    belief_err: float = 0.0          # hiperjuego: error relativo máximo en creencias
    recertify: bool = True
    n_hops: int = 2
    R_com: float = 9.0
    rev_rate: float = 1.0            # revisiones/s por AMR (reloj de Poisson)
    eps_sw: float = 0.5              # histéresis
    dwell: float = 2.0               # permanencia mínima (s)
    beta: float = 3.0                # logit
    market_rounds: int = 4
    ctrl_dt: float = 0.02
    T_max: float = 300.0
    seed: int = 0
    a_ref: float = 0.35              # aceleración de diseño de la carga
    v_load: float = 0.6
    d_safe: float = 0.25
    a_brake: float = 0.3
    cap_scale: float = 1.0           # escala de capacidades de contacto (hiperjuego vinculante)
    planner: str = "game"           # game (juego continuo de trayectorias) | waypoint (seguidor heurístico)
    replan_dt: float = 0.2


def cargo_slots(ld, r):
    """Puestos bajo la carga (marco cuerpo) para r miembros."""
    L, W = ld.L, ld.W
    if r == 2: return [np.array([L * 0.3, 0.0]), np.array([-L * 0.3, 0.0])]
    if r == 3: return [np.array([L * 0.32, W * 0.25]), np.array([L * 0.32, -W * 0.25]), np.array([-L * 0.32, 0.0])]
    return [np.array([L * 0.32, W * 0.28]), np.array([L * 0.32, -W * 0.28]), np.array([-L * 0.32, W * 0.28]), np.array([-L * 0.32, -W * 0.28])][:r]


def caging_slots(ld, r, goal_dir_body):
    """Caras de empuje (punto en el borde, normal exterior) en marco cuerpo.
    Se colocan detrás respecto de la dirección al objetivo y a los lados."""
    L, W = ld.L, ld.W
    back = -goal_dir_body / (np.linalg.norm(goal_dir_body) + 1e-9)
    # candidatos: cuatro caras
    faces = [(np.array([L / 2, 0.0]), np.array([1.0, 0.0])), (np.array([-L / 2, 0.0]), np.array([-1.0, 0.0])),
             (np.array([0.0, W / 2]), np.array([0.0, 1.0])), (np.array([0.0, -W / 2]), np.array([0.0, -1.0]))]
    faces.sort(key=lambda f: -(f[1] @ back))
    out = []
    for p, n in faces[:r]:
        out.append((p, n))
    if r == 3:  # dos en la cara trasera separados + una lateral
        p, n = faces[0]; tvec = np.array([-n[1], n[0]]); width = (W if abs(n[0]) > 0.5 else L)
        out = [(p + 0.28 * width * tvec, n), (p - 0.28 * width * tvec, n), faces[1]]
    if r == 4:
        p, n = faces[0]; tvec = np.array([-n[1], n[0]]); width = (W if abs(n[0]) > 0.5 else L)
        # dos traseros separados (par de giro) + dos laterales adelantados (contención y par); frena el suelo
        sides = []
        for ps, ns in (faces[1], faces[2]):
            fwd = -n / np.linalg.norm(n); length = (L if abs(ns[1]) > 0.5 else W)
            sides.append((ps + 0.0 * length * fwd, ns))
        out = [(p + 0.40 * width * tvec, n), (p - 0.40 * width * tvec, n)] + sides
    return out


class Mechanism:
    def __init__(self, plant: Plant, cfg: Config, sides, opening):
        self.P = plant; self.cfg = cfg; self.rng = np.random.default_rng(cfg.seed)
        N, K = len(plant.amr), len(plant.loads)
        self.N, self.K = N, K
        self.z = [IDLE] * N                       # estrategia discreta
        self.last_switch = np.full(N, -1e9)
        self.phase = ["REC"] * K                  # REC|FORM|TRANSPORT|DONE
        self.mode = [None] * K
        self.members = [dict() for _ in range(K)]  # k -> {slot: i}
        self.price = np.zeros((K, 3)); self.p_hist = []
        self.msgs = 0; self.revisions = 0; self.false_cert = 0; self.recert_reject = 0
        self.side_of = sides; self.opening = np.array(opening, float)
        self.lease_owner = None; self.lease_queue = []; self.lease_version = 0
        self.corridor_time_double = 0.0; self.deliver_t = [None] * K
        self.next_rev = self.rng.exponential(1 / cfg.rev_rate, N)
        # creencias (hiperjuego)
        e = cfg.belief_err
        self.bel_cap = np.array([[a.cap * (1 + self.rng.uniform(-e, e)) for a in plant.amr] for _ in range(N)])
        self.bel_mass = np.array([[ld.m * (1 + self.rng.uniform(-e, e)) for ld in plant.loads] for _ in range(N)])
        # gne_pd
        self.x = np.full((N, K + 1), 1.0 / (K + 1)); self.lam = np.zeros(K); self.gne_committed = False
        self.t_ctrl = 0.0
        self.tau_cmd = np.zeros((N, 2)); self.v_cmd = np.zeros((N, 2))
        self.formation_t0 = [None] * K
        self.slot_geom = {}
        self.wint = np.zeros((N, 2))
        self.vint = np.zeros((K, 3))
        self.at_stand = set()
        self.head_err = np.zeros(K); self.head_bad_t = np.zeros(K); self.V_des_last = np.zeros((K, 2))
        # juego continuo de trayectorias: un jugador por coalición y por AMR libre; continuaciones publicadas
        self.tp_load = {}; self.tp_amr = {}; self.plans = {}; self.last_replan = {}
        self.hist = [[] for _ in range(K)]; self.start_pos = plant.ql[:, :2].copy(); self._hist_t = -1.0

    # ------------------------------------------------------------ información
    def comm_graph(self):
        q = self.P.q[:, :2]; D = np.linalg.norm(q[:, None] - q[None], axis=2)
        A = (D <= self.cfg.R_com) & ~np.eye(self.N, dtype=bool)
        return A

    def nhop_sets(self):
        A = self.comm_graph(); reach = np.eye(self.N, dtype=bool)
        for _ in range(self.cfg.n_hops):
            reach = reach | (reach.astype(int) @ A.astype(int) > 0)
        self.msgs += int(A.sum()) * self.cfg.n_hops    # difusión por inundación acotada
        # cargas visibles: a n saltos de algún AMR alcanzable
        lq = self.P.ql[:, :2]; q = self.P.q[:, :2]
        see = np.zeros((self.N, self.K), dtype=bool)
        for i in range(self.N):
            for k in range(self.K):
                see[i, k] = np.any(np.linalg.norm(q[reach[i]] - lq[k], axis=1) <= self.cfg.R_com)
        return reach, see

    # ------------------------------------------------------------ aptitud
    def slot_columns(self, k, mode, r, viewer=None):
        key = (k, mode, r)
        if key in self.slot_geom: return self.slot_geom[key]
        cols = self._slot_columns(k, mode, r)
        self.slot_geom[key] = cols
        return cols

    def _slot_columns(self, k, mode, r):
        ld = self.P.loads[k]
        if mode == "cargo":
            slots = cargo_slots(ld, r)
            cols = [];
            for rb in slots:
                cols.append((rb, None))
            return cols
        gd = rot(self.P.ql[k, 2]).T @ (ld.goal - self.P.ql[k, :2])
        return caging_slots(ld, r, gd)

    def wrench_margin(self, k, mode, member_caps, viewer):
        """Margen del conjunto de wrench realizable frente a la demanda de diseño.
        cargo: cada pad transmite fuerza en cualquier dirección con |f|<=Fmax (disco), la carga va levantada;
        caging: cada pusher solo empuja (0<=lambda<=Fmax a lo largo de -n) y debe vencer la fricción del suelo;
        el suelo frena, luego la demanda hacia atrás es nula. Certificado por funciones soporte
        sobre una malla de 180 direcciones (aproximación externa fina)."""
        P = self.P; ld = P.loads[k]; m = self.bel_mass[viewer, k] if viewer is not None else ld.m
        r = len(member_caps); cols = self.slot_columns(k, mode, r)
        if mode == "cargo":
            Fdem = m * self.cfg.a_ref + 8.0 * self.cfg.v_load; Mdem = ld.I * 0.3 + 4.0 * 0.3
            ang = np.linspace(0, 2 * np.pi, 16, endpoint=False)
            Wd = np.array([[Fdem * np.cos(t), Fdem * np.sin(t), sg * Mdem] for t in ang for sg in (-1, 1)])
        else:
            Fdem = ld.mu_f * m * G + m * self.cfg.a_ref + 8.0 * self.cfg.v_load; Mdem = ld.I * 0.3 + 4.0 * 0.3
            gd = rot(P.ql[k, 2]).T @ (ld.goal - P.ql[k, :2]); gd = gd / (np.linalg.norm(gd) + 1e-9)
            tv = np.array([-gd[1], gd[0]])
            Wd = np.array([list(Fdem * gd) + [sg * Mdem] for sg in (-1, 0, 1)] +
                          [list(0.35 * Fdem * (gd * np.cos(t) + tv * np.sin(t))) + [sg * Mdem] for t in (np.pi / 2, -np.pi / 2, np.pi / 4, -np.pi / 4) for sg in (-1, 1)])
        scale = np.array([1 / Fdem, 1 / Fdem, 1 / max(Mdem, 1e-3)])
        if not hasattr(self, "_etas"):
            self._etas = np.array([[np.cos(t), np.sin(t), bb] for t in np.linspace(0, 2 * np.pi, 36, endpoint=False) for bb in (-0.8, -0.3, 0.0, 0.3, 0.8)])
        etas = self._etas * scale
        h = np.zeros(len(etas))
        for (rb, n), cap in zip(cols, member_caps):
            rp = np.array([-rb[1], rb[0]])
            if n is None:
                g = etas[:, :2] + etas[:, 2:3] * rp[None, :]
                h += cap * np.linalg.norm(g, axis=1)
            else:
                gcol = np.array([-n[0], -n[1], -(rb[0] * n[1] - rb[1] * n[0])])
                h += cap * np.maximum(0.0, etas @ gcol)
        M = (h[None, :] - Wd @ etas.T) / np.linalg.norm(etas, axis=1)[None, :]
        return float(M.min()) / Fdem

    def coalition_value(self, k, mode, members_caps, viewer):
        """Valor de la coalición (aptitud). vector: B si margen>=0 (+bono por margen); scalar: suma de capacidades."""
        ld = self.P.loads[k]; r = ld.r_req
        if len(members_caps) < r:
            # crédito parcial convexo: progreso hacia r* (prospecto), sin comprobar geometría aún
            return 0.9 * ld.B * (len(members_caps) / r) ** 2
        if self.cfg.fitness == "scalar":
            mm = (self.bel_mass[viewer, k] if viewer is not None else ld.m)
            need = mm * self.cfg.a_ref * 1.6 + (ld.mu_f * mm * G if mode == "caging" else 0.0)
            return ld.B if sum(members_caps) >= need else 0.0
        mg = self.wrench_margin(k, mode, members_caps[:r], viewer)
        return ld.B * (1.0 + 0.2 * min(mg, 1.0)) if mg >= 0 else 0.0

    # ------------------------------------------------------------ potencial
    def travel_cost(self, i, k, mode, slot):
        p = self.P.q[i, :2]; target = self.slot_world(k, mode, slot, len(self.slot_columns(k, mode, self.P.loads[k].r_req)))
        d = np.linalg.norm(target - p)
        if self.side_of(p) != self.side_of(target): d += 2.0 * np.linalg.norm(p - self.opening)
        return 0.15 * d + 0.002 * max(0.0, 2000.0 - self.P.E[i]) / 10.0

    def slot_world(self, k, mode, slot, r):
        cols = self.slot_columns(k, mode, r); rb, n = cols[slot]
        p = self.P.load_body_to_world(k, rb)
        if n is not None:  # caging: el AMR se coloca fuera de la cara
            p = p + rot(self.P.ql[k, 2]) @ n * (self.P.amr[0].R + 0.05)
        return p

    def potential(self, z, viewer, visible_amr, visible_loads):
        """Phi sobre la información visible del AMR viewer."""
        Phi = 0.0
        for k in range(self.K):
            if not visible_loads[k] or self.phase[k] == "DONE":
                continue
            for mode in self.P.loads[k].modes:
                caps = [self.bel_cap[viewer, j] for j in range(self.N) if visible_amr[j] and z[j] is not IDLE and z[j][0] == k and z[j][1] == mode]
                if caps:
                    Phi += self.coalition_value(k, mode, caps, viewer)
        for j in range(self.N):
            if visible_amr[j] and z[j] is not IDLE:
                k, mode, s = z[j]
                Phi -= self.travel_cost(j, k, mode, s)
        return Phi

    def candidates(self, i, visible_loads, z):
        cands = [IDLE]
        for k in range(self.K):
            if not visible_loads[k] or self.phase[k] not in ("REC",):
                continue
            ld = self.P.loads[k]
            for mode in ld.modes:
                if self.mode[k] is not None and self.mode[k] != mode:
                    continue
                r = ld.r_req
                taken = {zz[2] for j, zz in enumerate(z) if j != i and zz is not IDLE and zz[0] == k and zz[1] == mode}
                for s in range(r):
                    if s not in taken:
                        cands.append((k, mode, s))
        return cands

    # ------------------------------------------------------------ revisión
    def revise(self, i, reach, see):
        cfg = self.cfg; z = list(self.z)
        if z[i] is not IDLE and self.phase[z[i][0]] != "REC":
            return  # comprometido en una coalición ya formada
        if self.P.t - self.last_switch[i] < cfg.dwell:
            return
        vis = reach[i]; vl = see[i]
        base = self.potential(z, i, vis, vl)
        cands = self.candidates(i, vl, z)
        gains = []
        for c in cands:
            if c == z[i]:
                gains.append(0.0); continue
            z2 = list(z); z2[i] = c
            gains.append(self.potential(z2, i, vis, vl) - base)
        gains = np.array(gains)
        proto = cfg.protocol; choice = None
        if proto == "best_response":
            j = int(np.argmax(gains)); choice = cands[j] if gains[j] > cfg.eps_sw else None
        elif proto == "smith":
            w = np.maximum(gains - cfg.eps_sw, 0.0)
            if w.sum() > 0:
                pr = np.minimum(w / 10.0, 1.0)   # tasa proporcional al exceso, acotada
                j = self.rng.choice(len(cands), p=w / w.sum())
                choice = cands[j] if self.rng.random() < pr[j] else None
        elif proto == "bnn":
            ex = np.maximum(gains - gains.mean() - cfg.eps_sw, 0.0)
            if ex.sum() > 0:
                j = self.rng.choice(len(cands), p=ex / ex.sum()); choice = cands[j] if gains[j] > cfg.eps_sw else None
        elif proto == "logit":
            pr = np.exp(cfg.beta * (gains - gains.max())); pr /= pr.sum()
            j = self.rng.choice(len(cands), p=pr); choice = cands[j] if cands[j] != z[i] and gains[j] > -1e-9 else None
        elif proto == "replicator":
            # imitación: solo estrategias usadas por vecinos visibles (frontera invariante)
            used = {z[j] for j in range(self.N) if vis[j] and j != i and z[j] is not IDLE}
            opts = [(c, g) for c, g in zip(cands, gains) if c is not IDLE and (c[0], c[1]) in {(u[0], u[1]) for u in used}]
            if opts:
                c, g = max(opts, key=lambda t: t[1])
                if g > cfg.eps_sw and self.rng.random() < min(1.0, g / 10.0):
                    choice = c
        if choice is not None and choice != z[i]:
            # arbitraje del puesto por arrendamiento versionado (tender de la carga)
            self.msgs += 2
            if choice is not IDLE:
                k, mode, s = choice
                if s in self.members[k] and self.members[k][s] != i:
                    return  # concesión rechazada (puesto ya arrendado)
                if self.mode[k] is not None and self.mode[k] != mode:
                    return
            if z[i] is not IDLE:
                k0, m0, s0 = z[i]; self.members[k0].pop(s0, None)
                if not self.members[k0]: self.mode[k0] = None
            if choice is not IDLE:
                k, mode, s = choice; self.members[k][s] = i; self.mode[k] = mode
            self.z[i] = choice; self.last_switch[i] = self.P.t; self.revisions += 1
            self.lease_version += 1

    # --------------------------------------------------- gne primal-dual (shares)
    def gne_pd_step(self, reach, see, dt):
        """Smith sobre shares x_i (idle + K cargas) con multiplicadores de capacidad (PDM)."""
        for i in range(self.N):
            pay = np.zeros(self.K + 1)
            for k in range(self.K):
                if not see[i, k] or self.phase[k] != "REC": pay[k + 1] = -1e3; continue
                ld = self.P.loads[k]
                cover = sum(self.x[j, k + 1] * self.bel_cap[i, j] for j in range(self.N) if reach[i, j])
                need = self.bel_mass[i, k] * self.cfg.a_ref * 1.6
                pay[k + 1] = ld.B / ld.r_req + self.lam[k] * self.bel_cap[i, i] - 0.15 * np.linalg.norm(self.P.ql[k, :2] - self.P.q[i, :2]) - 0.5 * max(0, cover - need) / need
            x = self.x[i]; V = np.zeros_like(x)
            for a in range(len(x)):
                for b in range(len(x)):
                    V[a] += x[b] * max(pay[a] - pay[b], 0) - x[a] * max(pay[b] - pay[a], 0)
            self.x[i] = np.clip(x + dt * 0.5 * V, 0, 1); self.x[i] /= self.x[i].sum()
        for k in range(self.K):
            cover = sum(self.x[j, k + 1] * self.P.amr[j].cap for j in range(self.N)); need = self.P.loads[k].m * self.cfg.a_ref * 1.6
            self.lam[k] = max(0.0, self.lam[k] + dt * 0.02 * (need - cover))
        self.msgs += int(reach.sum())

    def gne_pd_commit(self, see):
        """Atomización: cada AMR toma su share máxima; asignación de puestos por orden de share."""
        order = np.argsort(-self.x[:, 1:].max(1))
        for i in order:
            k = int(np.argmax(self.x[i])) - 1
            if k < 0 or not see[i, k] or self.phase[k] != "REC": continue
            ld = self.P.loads[k]; mode = ld.modes[0]
            taken = set(self.members[k].keys())
            for s in range(ld.r_req):
                if s not in taken:
                    self.members[k][s] = i; self.mode[k] = mode; self.z[i] = (k, mode, s); self.last_switch[i] = self.P.t; break
        self.gne_committed = True

    # ------------------------------------------------------------ fases
    def update_phases(self):
        P = self.P
        for k in range(self.K):
            ld = P.loads[k]
            if self.phase[k] == "DONE": continue
            if self.phase[k] == "REC" and len(self.members[k]) >= ld.r_req:
                # certificación (con creencias del tender = miembro 0) y recertificación con datos reales
                i0 = list(self.members[k].values())[0]
                caps_bel = [self.bel_cap[i0, j] for j in self.members[k].values()]
                v_bel = self.coalition_value(k, self.mode[k], caps_bel, i0)
                caps_true = [P.amr[j].cap for j in self.members[k].values()]
                v_true = self.coalition_value(k, self.mode[k], caps_true, None) if self.cfg.fitness == "vector" else v_bel
                if self.cfg.fitness == "vector":
                    mg_true = self.wrench_margin(k, self.mode[k], caps_true[:ld.r_req], None)
                    if v_bel > 0 and mg_true < 0:
                        self.false_cert += 1
                        if self.cfg.recertify:
                            self.recert_reject += 1
                            # reabrir: expulsar al miembro de menor capacidad
                            s_min = min(self.members[k], key=lambda s: P.amr[self.members[k][s]].cap)
                            j = self.members[k].pop(s_min); self.z[j] = IDLE; self.last_switch[j] = P.t
                            continue
                if self.mode[k] == "caging": self.replan_caging(k)
                self.phase[k] = "FORM"; self.formation_t0[k] = P.t; self.msgs += ld.r_req
            elif self.phase[k] == "FORM":
                r = ld.r_req; ok = True
                for s, i in self.members[k].items():
                    target = self.slot_world(k, self.mode[k], s, r)
                    if np.linalg.norm(P.q[i, :2] - target) > 0.15 or abs(P.eta[i, 0]) > 0.2:
                        ok = False
                    if self.mode[k] == "caging":
                        rb, n = self.slot_columns(k, "caging", r)[s]; nw = rot(P.ql[k, 2]) @ n
                        if abs(np.cos(P.q[i, 2]) * nw[0] + np.sin(P.q[i, 2]) * nw[1]) < 0.9: ok = False
                if ok:
                    if self.mode[k] == "cargo":
                        for s, i in self.members[k].items():
                            P.attach_pad(i, k, cargo_slots(ld, r)[s])
                    else:
                        rb, n = self.slot_columns(k, "caging", r)[0]; nw = rot(P.ql[k, 2]) @ n
                        gd = ld.goal - P.ql[k, :2]; gd = gd / (np.linalg.norm(gd) + 1e-9)
                        if (-nw) @ gd < 0.6:     # la caja giró en la formación: re-planificar caras y volver a formar
                            self.replan_caging(k)
                            for i in self.members[k].values(): self.at_stand.discard(i)
                            continue
                    self.phase[k] = "TRANSPORT"; self.vint[k] = 0.0
                elif P.t - self.formation_t0[k] > 60.0:
                    # formación fallida: liberar y reabrir el tender
                    for s, i in list(self.members[k].items()):
                        self.z[i] = IDLE; self.last_switch[i] = P.t; self.at_stand.discard(i)
                    self.members[k] = {}; self.mode[k] = None; self.phase[k] = "REC"
                    self.slot_geom = {kk: v for kk, v in self.slot_geom.items() if kk[0] != k}
            elif self.phase[k] == "TRANSPORT":
                if self.mode[k] == "caging":
                    self.head_bad_t[k] = self.head_bad_t[k] + self.cfg.ctrl_dt if abs(self.head_err[k]) > 0.6 else 0.0
                    if self.head_bad_t[k] > 2.0:      # la caja giró demasiado: re-formar con caras nuevas
                        self.replan_caging(k)
                        for i in self.members[k].values(): self.at_stand.discard(i)
                        self.phase[k] = "FORM"; self.formation_t0[k] = P.t; self.head_bad_t[k] = 0.0; self.msgs += ld.r_req
                        continue
                dpos = np.linalg.norm(P.ql[k, :2] - ld.goal); spd = np.linalg.norm(P.zl[k, :2])
                if dpos < 0.30 and spd < 0.08:
                    self.phase[k] = "DONE"; self.deliver_t[k] = P.t
                    for s, i in list(self.members[k].items()):
                        P.detach(i); self.z[i] = IDLE; self.last_switch[i] = P.t; self.at_stand.discard(i)
                    self.members[k] = {}
                    if self.lease_owner == k: self.lease_owner = None

    # ------------------------------------------------------------ pasillo
    def corridor_request(self, k, dist_to_opening):
        """Arrendamiento exclusivo con orden total (por distancia al paso en el momento de pedir)."""
        if self.lease_owner == k: return True
        if k not in self.lease_queue: self.lease_queue.append(k); self.msgs += 1
        if self.lease_owner is None and self.lease_queue and self.lease_queue[0] == k:
            self.lease_owner = k; self.lease_queue.pop(0); self.lease_version += 1; self.msgs += 1
            return True
        return False

    def corridor_release(self, k):
        if self.lease_owner == k:
            self.lease_owner = None; self.msgs += 1

    def in_corridor(self, k):
        c = self.P.load_corners(k); x = self.opening[0]
        return np.any(np.abs(c[:, 0] - x) < 1.6)

    # ------------------------------------------------------------ control
    def load_command(self, k):
        """Velocidad deseada del cuerpo de la carga: ruta con paso por el hueco, barreras y pasillo."""
        P = self.P; ld = P.loads[k]; cfg = self.cfg
        p = P.ql[k, :2]; goal = ld.goal
        cross = self.side_of(p) != self.side_of(goal)
        sgn = 1.0 if goal[0] > p[0] else -1.0
        if cross:
            wp_in = np.array([self.opening[0] - sgn * 3.0, self.opening[1]]); wp_out = np.array([self.opening[0] + sgn * 3.0, self.opening[1]])
            # antes del hueco: ir al punto de entrada alineado; dentro/después: salir recto
            if abs(p[0] - self.opening[0]) > 3.2 and (p[0] - self.opening[0]) * sgn < 0 and np.linalg.norm(wp_in - p) > 1.0:
                target = wp_in
            else:
                target = wp_out
        else:
            target = goal
        d = target - p; dist = np.linalg.norm(d); u = d / (dist + 1e-9)
        if cross and target is not goal and abs(p[0] - self.opening[0]) <= 3.2:
            u = np.array([sgn, 0.6 * (self.opening[1] - p[1])]); u = u / np.linalg.norm(u)
        v_des = min(cfg.v_load, 0.8 * dist) if not cross else cfg.v_load
        if not cross:
            v_des = min(v_des, np.sqrt(2 * 0.25 * max(dist - 0.05, 0.0)))
        if cfg.planner == "game":
            # juego continuo de trayectorias con ruta por puntos de espera laterales (circulación por la derecha)
            # y paso por el eje del vano; quien espera el arrendamiento publica un plan estático.
            key = ("load", k)
            if key not in self.tp_load:
                self.tp_load[key] = TrajPlayer(N=12, delta=0.5, v_max=cfg.v_load, r=0.5 * ld.W + 0.22, d_safe=cfg.d_safe)
            tp = self.tp_load[key]
            lane = -1.7 if sgn > 0 else 1.7
            hold = np.array([self.opening[0] - sgn * 3.0, self.opening[1] + lane])
            mid = np.array([self.opening[0], self.opening[1]])
            out = np.array([self.opening[0] + sgn * 3.0, self.opening[1] + lane])
            waiting = False
            if cross:
                owner = (self.lease_owner == k)
                if cfg.corridor == "lease":
                    if abs(p[0] - self.opening[0]) < 4.5 and not owner: owner = self.corridor_request(k, dist)
                    if not owner:
                        g = hold; waiting = np.linalg.norm(hold - p) < 1.2
                    else:
                        g = mid if abs(p[0] - self.opening[0]) > 2.5 else np.array([np.clip(p[0] + sgn * 2.5, min(mid[0], out[0]), max(mid[0], out[0])), self.opening[1] + lane * min(1.0, max(0.0, (p[0] - self.opening[0]) * sgn) / 3.0)])
                else:
                    g = mid if abs(p[0] - self.opening[0]) > 2.5 else np.array([np.clip(p[0] + sgn * 2.5, min(mid[0], out[0]), max(mid[0], out[0])), self.opening[1] + lane * min(1.0, max(0.0, (p[0] - self.opening[0]) * sgn) / 3.0)])
            else:
                g = goal if abs(p[0] - self.opening[0]) > 2.5 else out    # abandonar el vano por el carril de salida
                if self.lease_owner == k and not self.in_corridor(k): self.corridor_release(k)
            if P.t - self.last_replan.get(key, -1.0) >= cfg.replan_dt:
                obstacles = [(P.ql[l, :2].copy(), 0.5 * np.hypot(P.loads[l].L, P.loads[l].W)) for l in range(self.K) if l != k]
                others = [(self.plans[kk], self.tp_load[kk].r, self.tp_load[kk].delta) for kk in self.plans if kk[0] == "load" and kk != key and kk in self.tp_load]
                vg, _ = tp.step(p, g, P.t, P.walls.rects, obstacles, others)
                self.plans[key] = (np.repeat(p[None, :], tp.N, axis=0) if waiting else tp.X.copy()); self.last_replan[key] = P.t; self.msgs += 2 * (self.K - 1)
                self.vg_last = getattr(self, "vg_last", {}); self.vg_last[key] = (np.zeros(2) if waiting else vg)
            vg = getattr(self, "vg_last", {}).get(key, np.zeros(2))
            sg = np.linalg.norm(vg)
            if waiting or sg < 1e-3:
                v_des = 0.0
            else:
                u = vg / sg; v_des = min(v_des, sg) if not cross else min(cfg.v_load, sg)
                if cross and not (self.lease_owner == k) and cfg.corridor == "lease": v_des = min(v_des, 0.35)   # ir despacio al carril de espera
        near = abs(p[0] - self.opening[0]) < 3.5
        inside = self.in_corridor(k)
        if cfg.corridor == "lease" and cfg.planner != "game":
            if cross and (near or inside):
                if not self.corridor_request(k, dist):
                    hold = 2.6 - abs(p[0] - self.opening[0])
                    if hold > 0: v_des = 0.0
            elif self.lease_owner == k and not inside and not cross:
                self.corridor_release(k)
        elif cfg.corridor == "price" and cfg.planner != "game":  # precio de congestión sobre la celda del paso (no exclusivo)
            occ = sum(1 for l in range(self.K) if l != k and self.phase[l] == "TRANSPORT" and abs(P.ql[l, 0] - self.opening[0]) < 3.0)
            if cross and near and not inside and occ > 0:
                mu = 1.0 * occ
                # cede el que está más lejos del paso (gradiente del coste de espera frente al precio)
                others = [abs(P.ql[l, 0] - self.opening[0]) for l in range(self.K) if l != k and self.phase[l] == "TRANSPORT" and abs(P.ql[l, 0] - self.opening[0]) < 3.0]
                if abs(p[0] - self.opening[0]) >= min(others):
                    v_des *= max(0.0, 1.0 - mu)
        V_des = v_des * u
        # orientación: alinear el eje largo con el avance dentro del pasillo
        th_des = np.arctan2(u[1], u[0])
        if cross and abs(p[0] - self.opening[0]) < 5.0:
            th_des = 0.0 if sgn > 0 else np.pi           # eje largo a lo largo del pasillo
        e_th = wrap(th_des - P.ql[k, 2])
        if abs(e_th) > np.pi / 2: e_th = wrap(e_th + np.pi)   # la carga es simétrica: basta alinear el eje
        W_des = np.clip(0.5 * e_th, -0.25, 0.25) if cross else 0.0
        if self.mode[k] == "caging":
            rb, n = self.slot_columns(k, "caging", ld.r_req)[0]; nrear = rot(P.ql[k, 2]) @ n; fwd = -nrear
            e_h = wrap(np.arctan2(u[1], u[0]) - np.arctan2(fwd[1], fwd[0]))
            self.head_err[k] = e_h
            W_des = 0.0
            V_des = V_des * max(0.0, np.cos(e_h))
        return V_des, W_des

    def wrench_market(self, k, V_des, W_des):
        """Precio dual p_k y respuesta local de cada miembro. Devuelve fuerzas objetivo por miembro."""
        P = self.P; ld = P.loads[k]; cfg = self.cfg; r = ld.r_req; mode = self.mode[k]
        ev = np.concatenate([V_des - P.zl[k, :2], [W_des - P.zl[k, 2]]])
        self.vint[k] = np.clip(self.vint[k] + cfg.ctrl_dt * ev, -0.6, 0.6)
        a_des = 0.9 * ev[:2] + 0.2 * self.vint[k, :2]; al_des = 1.2 * ev[2] + 0.2 * self.vint[k, 2]
        w_d = np.concatenate([ld.m * a_des + 8.0 * P.zl[k, :2], [ld.I * al_des + 12.0 * P.zl[k, 2]]])
        if mode == "caging":
            w_d[2] = -6.0 * P.zl[k, 2]   # feedforward de fricción de suelo en la dirección deseada, escalado con la velocidad pedida
            sv = np.linalg.norm(V_des)
            if sv > 0.02: w_d[:2] += ld.mu_f * ld.m * G * (V_des / sv) * min(1.0, sv / 0.15)
            if sv < 0.02 and np.linalg.norm(P.zl[k, :2]) < 0.05: w_d[:2] = 0.0   # bloqueada por barrera o pasillo: no empujar
        cols = self.slot_columns(k, mode, r); Rm = rot(P.ql[k, 2])
        members = sorted(self.members[k].items())
        p = self.price[k]
        Q = np.diag([1.0, 1.0, 0.5])
        f = {}
        for _ in range(cfg.market_rounds):
            tot = np.zeros(3)
            for s, i in members:
                rb, n = cols[s]; rw = Rm @ rb; rp = np.array([-rw[1], rw[0]])
                Fmax = P.amr[i].cap
                if n is None:
                    Gt = np.array([[1, 0, rp[0]], [0, 1, rp[1]]])    # G_i^T p (2 comps)
                    g = Gt @ p; c_i = 0.02
                    fi = g / c_i; nf = np.linalg.norm(fi)
                    if nf > Fmax: fi *= Fmax / nf
                    f[i] = fi; tot += np.array([fi[0], fi[1], rp[0] * fi[1] - rp[1] * fi[0]])
                else:
                    nw = Rm @ n; gcol = np.array([-nw[0], -nw[1], -(rw[0] * nw[1] - rw[1] * nw[0])])
                    lam = np.clip((gcol @ p) / 0.02, 0.0, Fmax)
                    f[i] = lam; tot += lam * gcol
            p = np.clip(p + 0.004 * Q @ (w_d - tot) - 0.001 * p, -20.0, 20.0)
            self.msgs += 2 * len(members)
        self.price[k] = p
        return f, w_d

    def amr_low_level(self, i, v_vec, w_extra=0.0, f_ff=0.0):
        """Vector de velocidad deseado del chasis -> pares de rueda (swivel de rumbo + PI de rueda)."""
        P = self.P; a = P.amr[i]; th = P.q[i, 2]; e = np.array([np.cos(th), np.sin(th)])
        spd = np.linalg.norm(v_vec)
        if spd > 1e-3:
            th_des = np.arctan2(v_vec[1], v_vec[0]); e_th = wrap(th_des - th)
            if abs(e_th) > np.pi / 2:  # marcha atrás si es más corto
                th_des = wrap(th_des + np.pi); e_th = wrap(th_des - th); spd = -spd
            v_ref = spd * np.cos(e_th); w_ref = np.clip(1.8 * e_th - 0.35 * P.eta[i, 1], -a.w_max, a.w_max) + w_extra
        else:
            v_ref = 0.0; w_ref = w_extra
        v_ref = np.clip(v_ref, -a.v_max, a.v_max)
        ws_ref = np.array([v_ref - w_ref * a.b / 2, v_ref + w_ref * a.b / 2]) / a.r_w + (f_ff / 2) / (a.c_g * a.r_w)   # deslizamiento que exige la fuerza
        err = ws_ref - P.ww[i]
        self.wint[i] = np.clip(self.wint[i] + err * self.cfg.ctrl_dt, -3.0, 3.0)
        tau = 1.2 * err + 1.5 * self.wint[i] + 0.5 * a.r_w * (a.b_v * v_ref / 2) + a.r_w * f_ff / 2
        tau = np.clip(tau, -a.tau_max, a.tau_max)
        sat = np.abs(tau) >= a.tau_max - 1e-9
        self.wint[i][sat] -= err[sat] * self.cfg.ctrl_dt    # anti-windup
        return tau

    def navigate(self, i, target, others_pos, avoid_loads=True):
        """Navegación libre de un AMR a un punto, con paso por el hueco y barrera por AMR."""
        P = self.P; cfg = self.cfg; p = P.q[i, :2]
        if cfg.planner == "game":
            return self.navigate_game(i, target, avoid_loads)
        cross = self.side_of(p) != self.side_of(target)
        wp = self.opening if cross else target
        d = wp - p; dist = np.linalg.norm(d); u = d / (dist + 1e-9)
        v = min(P.amr[i].v_max, 1.0 * dist) if not cross else P.amr[i].v_max
        # evitación de paredes: si el rumbo choca cerca, desviar hacia el hueco en y
        clear = P.walls.clearance(p + 0.8 * u) - P.amr[i].R
        if clear < 0.35:
            u = np.array([u[0] * 0.3, np.sign(self.opening[1] - p[1] + 1e-6) * 1.0]); u /= np.linalg.norm(u)
        if avoid_loads:   # las cargas son obstáculos para quien no las transporta
            for k in range(self.K):
                if self.groups.get(i) == k: continue
                dc = np.linalg.norm(P.ql[k, :2] - p)
                if dc < 2.8: v = min(v, 0.4)
                for la in (0.6, 1.2):
                    delta, n = P.disc_vs_rect(p + la * u, P.amr[i].R, k)
                    if delta > -0.45:
                        side = np.array([-u[1], u[0]]); u = u + 1.5 * side * np.sign(side @ n + 1e-9); u /= np.linalg.norm(u); v = min(v, 0.35); break
        if cfg.safety == "nested":
            for pj, Rj in others_pos:
                dj = pj - p; dd = np.linalg.norm(dj) - P.amr[i].R - Rj
                if dd < 2.0 and dj @ u > 0.3 * np.linalg.norm(dj):
                    v = min(v, np.sqrt(2 * 0.6 * max(dd - 0.3, 0.0)))
                    side = np.array([-u[1], u[0]]); u = u + 0.8 * side * np.sign(side @ (-dj) + 1e-9); u /= np.linalg.norm(u)
        return v * u

    def replan_caging(self, k):
        """Recalcula las caras de empuje con la dirección actual al objetivo y reasigna miembros al puesto más cercano."""
        P = self.P; ld = P.loads[k]; r = ld.r_req
        self.slot_geom = {kk: v for kk, v in self.slot_geom.items() if kk[0] != k}
        cols = self.slot_columns(k, "caging", r)
        members = list(self.members[k].values()); free = list(range(r)); new = {}
        for i in sorted(members, key=lambda i: i):
            s = min(free, key=lambda s: np.linalg.norm(self.slot_world(k, "caging", s, r) - P.q[i, :2])); free.remove(s)
            new[s] = i; self.z[i] = (k, "caging", s)
        self.members[k] = new

    def navigate_game(self, i, target, avoid_loads=True):
        """AMR libre como jugador del juego de trayectorias: evita paredes, cargas y las continuaciones publicadas."""
        P = self.P; cfg = self.cfg; p = P.q[i, :2]; key = ("amr", i)
        cross = self.side_of(p) != self.side_of(target)
        sgn = 1.0 if target[0] > p[0] else -1.0
        if cross:
            wp_in = np.array([self.opening[0] - sgn * 2.0, self.opening[1]]); wp_out = np.array([self.opening[0] + sgn * 2.0, self.opening[1]])
            g = wp_in if ((p[0] - self.opening[0]) * sgn < -2.2 and np.linalg.norm(wp_in - p) > 0.8) else wp_out
        else:
            g = target
        if key not in self.tp_amr:
            self.tp_amr[key] = TrajPlayer(N=10, delta=0.4, v_max=P.amr[i].v_max, r=P.amr[i].R, d_safe=0.25)
        tp = self.tp_amr[key]
        if P.t - self.last_replan.get(key, -1.0) >= cfg.replan_dt:
            own = self.z[i][0] if self.z[i] is not IDLE else None
            obstacles = []
            if avoid_loads:
                obstacles = [(P.ql[l, :2].copy(), 0.5 * np.hypot(P.loads[l].L, P.loads[l].W)) for l in range(self.K) if l != own]
            reach = getattr(self, "_reach", None)
            others = []
            for kk, X in self.plans.items():
                if kk == key: continue
                if kk[0] == "amr":
                    j = kk[1]
                    if reach is not None and not reach[i, j]: continue
                    if own is not None and j in self.members[own].values(): continue
                    others.append((X, P.amr[j].R, self.tp_amr[kk].delta if kk in self.tp_amr else 0.4))
                else:
                    if kk[1] == own: continue
                    others.append((X, self.tp_load[kk].r, self.tp_load[kk].delta))
            vg, _ = tp.step(p, g, P.t, P.walls.rects, obstacles, others, iters=20)
            self.plans[key] = tp.X.copy(); self.last_replan[key] = P.t
            self.vg_amr = getattr(self, "vg_amr", {}); self.vg_amr[key] = vg
            self.msgs += int(reach[i].sum()) if reach is not None else 0
        vg = getattr(self, "vg_amr", {}).get(key, np.zeros(2))
        if not cross:
            d = np.linalg.norm(target - p); sg = np.linalg.norm(vg)
            if sg > 1e-6: vg = vg / sg * min(sg, 1.0 * d)
        return vg

    def approach_slot(self, i, k, mode, s, r, others, standoff_only=False):
        """Ir al punto de espera exterior (evitando cargas y AMR) y después entrar recto al puesto, sin empujar."""
        P = self.P; p = P.q[i, :2]
        slot = self.slot_world(k, mode, s, r); cols = self.slot_columns(k, mode, r); rb, n = cols[s]
        if n is None:
            dout = slot - P.ql[k, :2]; dout = dout / (np.linalg.norm(dout) + 1e-9)
            stand = slot + dout * (0.5 * max(P.loads[k].L, P.loads[k].W) + 0.8)
            nw = dout
        else:
            nw = rot(P.ql[k, 2]) @ n; stand = slot + nw * 1.0
        mates = set(self.members[k].values())
        oth = [o for j, o in enumerate(others) if j != i and j not in mates]
        ds = np.linalg.norm(stand - p)
        if ds <= (0.12 if mode == "caging" else 0.35): self.at_stand.add(i)
        if i in self.at_stand and np.linalg.norm(slot - p) > 1.6 and ds > 0.6:
            self.at_stand.discard(i)          # el puesto se alejó: volver por el punto de espera
        if standoff_only or i not in self.at_stand:
            v = self.navigate(i, stand, oth, avoid_loads=(ds > 0.5))
            if ds < 0.8: v = 0.8 * (stand - p)
            return v
        vmax = 0.2 if mode == "caging" else 0.5
        v = np.clip(0.8 * (slot - p), -vmax, vmax)
        if mode == "caging":
            delta, nn = P.disc_vs_rect(p, P.amr[i].R, k)
            if delta > -0.01:                 # en contacto: no empujar hacia dentro durante la formación
                vin = v @ (-nw)
                if vin > 0: v = v - vin * (-nw)
        return v

    def control_step(self):
        """Un paso de control (cfg.ctrl_dt): fases, mercado, trayectoria, seguridad -> pares."""
        P = self.P; cfg = self.cfg
        reach, see = self.nhop_sets(); self._reach = reach
        # revisión discreta (relojes de Poisson) o gne_pd
        if cfg.recruit == "gne_pd" and not self.gne_committed:
            self.gne_pd_step(reach, see, cfg.ctrl_dt)
            if P.t > 12.0: self.gne_pd_commit(see)
        else:
            for i in range(self.N):
                if P.t >= self.next_rev[i]:
                    self.next_rev[i] = P.t + self.rng.exponential(1 / cfg.rev_rate)
                    self.revise(i, reach, see)
        self.update_phases()
        tau = np.zeros((self.N, 2)); caging = {}
        busy = set()
        others = [(P.q[j, :2], P.amr[j].R) for j in range(self.N)]
        for k in range(self.K):
            if self.phase[k] == "DONE": continue
            mode = self.mode[k]; r = P.loads[k].r_req
            if self.phase[k] == "FORM":
                if mode == "caging": caging[k] = set(self.members[k].values())
                for s, i in self.members[k].items():
                    busy.add(i)
                    v = self.approach_slot(i, k, mode, s, r, others)
                    if mode == "caging" and i in self.at_stand:
                        # en el punto de espera: girar hasta encarar la normal; luego entrar recto por el rumbo
                        rb, n = self.slot_columns(k, mode, r)[s]; nw = rot(P.ql[k, 2]) @ n; th = P.q[i, 2]
                        e_i = np.array([np.cos(th), np.sin(th)]); slot = self.slot_world(k, mode, s, r)
                        dvec = slot - P.q[i, :2]; dist = np.linalg.norm(dvec); delta, _ = P.disc_vs_rect(P.q[i, :2], P.amr[i].R, k)
                        lat_err = np.linalg.norm(dvec - (dvec @ nw) * nw)
                        if lat_err > 0.12 and dist < 0.6:
                            self.at_stand.discard(i)     # descolocado lateralmente: re-entrar por el punto de espera
                            tau[i] = self.amr_low_level(i, self.approach_slot(i, k, mode, s, r, others)); continue
                        # lejos del puesto: apuntar al puesto; cerca: alinearse con la normal de la cara
                        ref = dvec / (dist + 1e-9) if dist > 0.3 else -nw
                        e_th = wrap(np.arctan2(ref[1], ref[0]) - th)
                        if abs(e_th) > np.pi / 2: e_th = wrap(e_th + np.pi)
                        if abs(e_th) > 0.12 and dist > 0.3:
                            tau[i] = self.amr_low_level(i, np.zeros(2), w_extra=float(np.clip(2.0 * e_th, -1.5, 1.5)))
                        else:
                            v_along = float(np.clip(0.8 * dist, 0.0, 0.2)) * np.sign(float(dvec @ e_i) + 1e-9)
                            if delta > -0.01 and v_along * float(e_i @ (-nw)) > 0: v_along = 0.0
                            tau[i] = self.amr_low_level(i, v_along * e_i, w_extra=float(np.clip(1.5 * e_th, -0.8, 0.8)))
                    else:
                        tau[i] = self.amr_low_level(i, v)
            elif self.phase[k] == "TRANSPORT":
                V_des, W_des = self.load_command(k)
                V_des = 0.92 * self.V_des_last[k] + 0.08 * V_des if np.linalg.norm(self.V_des_last[k]) > 1e-6 else V_des
                self.V_des_last[k] = V_des
                f, w_d = self.wrench_market(k, V_des, W_des)
                cols = self.slot_columns(k, mode, r); Rm = rot(P.ql[k, 2])
                if mode == "caging": caging[k] = set(self.members[k].values())
                for s, i in self.members[k].items():
                    busy.add(i); rb, n = cols[s]
                    if n is None:
                        anchor = P.load_body_to_world(k, rb); v_anchor = P.load_point_vel(k, anchor)
                        eps = P.pad_eps.get(i, np.zeros(2)); ld = P.loads[k]
                        # fuerza sobre la carga deseada f[i]  => f_pad = -f[i];  k eps + d u = -f[i]
                        u_cmd = (-f[i] - ld.k_pad * eps) / ld.d_pad
                        v_amr = v_anchor - u_cmd
                        v_amr = np.clip(v_amr, -P.amr[i].v_max, P.amr[i].v_max)
                        e_i = np.array([np.cos(P.q[i, 2]), np.sin(P.q[i, 2])])
                        tau[i] = self.amr_low_level(i, v_amr, f_ff=float(f[i] @ e_i))
                    else:
                        # marco nominal: la formación define la orientación; la caja se alinea contra los empujadores
                        Vd = self.V_des_last[k]
                        th_nom = np.arctan2(Vd[1], Vd[0]) if np.linalg.norm(Vd) > 0.05 else P.ql[k, 2]
                        rb0, n0 = self.slot_columns(k, mode, r)[0]; th_nom = th_nom - np.arctan2(-n0[1], -n0[0])
                        Rn = rot(th_nom); nw = Rn @ n; cp = P.ql[k, :2] + Rn @ rb; v_cp = Vd.copy()
                        delta, _ = P.disc_vs_rect(P.q[i, :2], P.amr[i].R, k)
                        spot = cp + nw * (P.amr[i].R + 0.02); lateral = spot - P.q[i, :2]
                        lat = lateral - (lateral @ nw) * nw
                        gap = -(delta)   # >0 sin contacto
                        th = P.q[i, 2]; e_i = np.array([np.cos(th), np.sin(th)])
                        th_des = np.arctan2(-nw[1], -nw[0]); e_th = wrap(th_des - th)
                        if abs(e_th) > np.pi / 2: e_th = wrap(e_th + np.pi)     # empujar marcha atrás si está más cerca
                        if gap > 0.3 or np.linalg.norm(lat) > 0.45:
                            # descolocado: volver por el punto de espera (evitando la caja) y entrar recto
                            v = self.approach_slot(i, k, mode, s, r, others)
                            tau[i] = self.amr_low_level(i, v)
                        else:
                            vn = (-0.12 if (f[i] > 1.0 and gap > 0.004) else (0.08 if (f[i] <= 1.0 and gap < 0.01) else 0.0))
                            v_along = float((v_cp + vn * nw) @ e_i)          # solo a lo largo del rumbo
                            f_ff = float(f[i] * ((-nw) @ e_i)) if gap < 0.02 else 0.0
                            tau[i] = self.amr_low_level(i, v_along * e_i, w_extra=float(np.clip(2.0 * e_th, -1.5, 1.5)), f_ff=f_ff)
            if self.phase[k] in ("TRANSPORT",) and self.in_corridor(k):
                pass
        # dobles ocupaciones del pasillo
        inside = [k for k in range(self.K) if self.phase[k] == "TRANSPORT" and abs(P.ql[k, 0] - self.opening[0]) < 1.3]   # centro en el vano
        if len(inside) >= 2: self.corridor_time_double += cfg.ctrl_dt
        # AMR libres: acudir al puesto reclutado (REC) o mantenerse
        for i in range(self.N):
            if i in busy: continue
            if self.z[i] is not IDLE:
                k, mode, s = self.z[i]
                tau[i] = self.amr_low_level(i, self.approach_slot(i, k, mode, s, P.loads[k].r_req, others, standoff_only=True))
            else:
                tau[i] = self.amr_low_level(i, np.zeros(2))
        self.tau_cmd = tau; self.caging_sets = caging
        if P.t - self._hist_t >= 0.2:
            self._hist_t = P.t
            for k in range(self.K):
                if self.phase[k] == 'TRANSPORT': self.hist[k].append(P.ql[k, :2].copy())
        for i in busy: self.plans[("amr", i)] = np.repeat(P.q[i, :2][None, :], 10, axis=0)   # ocupados: plan estático (posición)
        for k in range(self.K):
            if self.phase[k] != "TRANSPORT": self.plans.pop(("load", k), None); self.tp_load.pop(("load", k), None)
        self.groups = {i: k for k in range(self.K) for i in self.members[k].values() if self.phase[k] in ('FORM', 'TRANSPORT')}

    def run(self):
        P = self.P; cfg = self.cfg; steps = int(round(cfg.ctrl_dt / P.dt))
        self.caging_sets = {}; self.groups = {}
        while P.t < cfg.T_max and any(ph != "DONE" for ph in self.phase):
            self.control_step()
            for _ in range(steps):
                P.step(self.tau_cmd, self.caging_sets, self.groups)
        return self.metrics()

    def metrics(self):
        P = self.P
        done = [ph == "DONE" for ph in self.phase]
        tort = []; curv = []
        for k in range(self.K):
            H = np.array(self.hist[k])
            if len(H) > 5:
                seg = np.diff(H, axis=0); L = np.linalg.norm(seg, axis=1); path = L.sum()
                straight = np.linalg.norm(self.P.loads[k].goal - self.start_pos[k]) + 2.0    # +2 m por el rodeo mínimo del vano
                tort.append(path / max(straight, 1e-6))
                ang = np.arctan2(seg[:, 1], seg[:, 0]); dang = np.abs(np.angle(np.exp(1j * np.diff(ang)))); m = L[1:] > 0.02
                curv.append(float(np.sum(dang[m]) / max(path, 1e-6)))     # rad/m: cambio de rumbo por metro recorrido
        return dict(success=all(done), n_done=sum(done), tortuosity=float(np.mean(tort)) if tort else float('nan'), curvature=float(np.mean(curv)) if curv else float('nan'), makespan=(max(t for t in self.deliver_t if t is not None) if any(done) else P.t),
                    energy_Wh=P.energy / 3600.0, min_sep_amr=P.min_sep_amr, min_sep_load=P.min_sep_load,
                    wall_pen_max=P.wall_pen_max, slip=P.slip_events, msgs=self.msgs, revisions=self.revisions,
                    false_cert=self.false_cert, recert_reject=self.recert_reject, corridor_double=self.corridor_time_double,
                    t_end=P.t)
