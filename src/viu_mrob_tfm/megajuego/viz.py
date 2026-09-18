"""Visualización cenital 2D del megajuego: grabación de estados, figuras estáticas y animaciones.

Uso:  PYTHONPATH=src python -m viu_mrob_tfm.megajuego.viz <cargo2|cargo|caging|both> <seed> [clave=valor ...]
Genera results/megajuego/figs/<nombre>_traj.pdf/.png, <nombre>_timeline.png y <nombre>.mp4
"""
from __future__ import annotations
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrow
from matplotlib.collections import LineCollection
import matplotlib.animation as animation
from .bench import make_scenario, side_of, OPENING, PLANT_W, PLANT_H, WALL_X, OPEN_W
from .mechanism import Mechanism, Config
from .plant import rot
from .debug import SPECS

PHASE_COL = {"REC": "#9e9e9e", "FORM": "#ff9800", "TRANSPORT": "#1e88e5", "DONE": "#43a047"}
LOAD_COL = ["#1e88e5", "#d81b60", "#8e24aa"]


def record(seed=0, which="cargo2", every=0.1, **kw):
    cfg = Config(seed=seed, **kw)
    specs = SPECS[which]; K = 1 if (specs and len(specs) == 1) else 2
    P = make_scenario(seed, N=8, K=K, load_specs=specs)
    for a in P.amr: a.cap *= cfg.cap_scale
    M = Mechanism(P, cfg, side_of, OPENING)
    steps = int(round(cfg.ctrl_dt / P.dt)); M.caging_sets = {}; M.groups = {}
    rec = dict(t=[], q=[], ql=[], phase=[], members=[], lease=[], attach=[], events=[], msgs=[], cfg=kw, seed=seed, which=which,
               loads=[dict(L=ld.L, W=ld.W, goal=ld.goal.tolist(), mode=ld.modes[0], r=ld.r_req, m=ld.m) for ld in P.loads],
               R=[a.R for a in P.amr], walls=P.walls.rects)
    nxt = 0.0; last_pair_t = {}
    while P.t < cfg.T_max and any(ph != "DONE" for ph in M.phase):
        M.control_step()
        for _ in range(steps): P.step(M.tau_cmd, M.caging_sets, M.groups)
        if P.t >= nxt:
            nxt += every
            rec["t"].append(P.t); rec["q"].append(P.q.copy()); rec["ql"].append(P.ql.copy())
            rec["phase"].append(list(M.phase)); rec["members"].append([dict(m) for m in M.members]); rec["lease"].append(M.lease_owner)
            rec["attach"].append(dict(P.attach)); rec["msgs"].append(M.msgs)
            # conflictos: contacto AMR-AMR no acoplado, carga contra pared
            N = len(P.amr)
            for i in range(N):
                for j in range(i + 1, N):
                    same = (i in M.groups and j in M.groups and M.groups[i] == M.groups[j] and i in P.attach and j in P.attach)
                    d = np.linalg.norm(P.q[i, :2] - P.q[j, :2]) - P.amr[i].R - P.amr[j].R
                    if d < 0 and not same and P.t - last_pair_t.get((i, j), -9) > 2.0:
                        last_pair_t[(i, j)] = P.t; rec["events"].append(dict(t=P.t, kind="amr-amr", p=((P.q[i, :2] + P.q[j, :2]) / 2).tolist(), d=float(d)))
            for k in range(len(P.loads)):
                for c in P.load_corners(k):
                    depth, n = P.walls.penetration(c, 0.0)
                    if depth > 0.02 and P.t - last_pair_t.get(("w", k), -9) > 2.0:
                        last_pair_t[("w", k)] = P.t; rec["events"].append(dict(t=P.t, kind="carga-pared", p=c.tolist(), d=float(depth)))
    rec["metrics"] = M.metrics()
    return rec


def draw_walls(ax, walls):
    for (x0, x1, y0, y1) in walls:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, color="#424242", zorder=1))
    ax.add_patch(Rectangle((WALL_X - 1.3, OPENING[1] - OPEN_W / 2), 2.6, OPEN_W, color="#fff59d", alpha=0.35, zorder=0))


def load_poly(ql, ld):
    L, W = ld["L"], ld["W"]; c = np.array([[L / 2, W / 2], [-L / 2, W / 2], [-L / 2, -W / 2], [L / 2, -W / 2]])
    return ql[:2] + c @ rot(ql[2]).T


def frame(ax, rec, idx, trail=200):
    ax.cla(); ax.set_xlim(-0.5, PLANT_W + 0.5); ax.set_ylim(-0.5, PLANT_H + 0.5); ax.set_aspect("equal"); ax.set_facecolor("#fafafa")
    draw_walls(ax, rec["walls"])
    q = rec["q"][idx]; ql = rec["ql"][idx]; ph = rec["phase"][idx]; mem = rec["members"][idx]; t = rec["t"][idx]
    K = len(rec["loads"]); N = len(rec["R"])
    # rastros
    i0 = max(0, idx - trail)
    for k in range(K):
        tr = np.array([r[k, :2] for r in rec["ql"][i0:idx + 1]])
        if len(tr) > 1: ax.plot(tr[:, 0], tr[:, 1], color=LOAD_COL[k], lw=2.5, alpha=0.5, zorder=2)
    owner = {i: k for k in range(K) for i in mem[k].values()}
    for i in range(N):
        tr = np.array([r[i, :2] for r in rec["q"][i0:idx + 1]])
        if len(tr) > 1: ax.plot(tr[:, 0], tr[:, 1], color=LOAD_COL[owner[i]] if i in owner else "#bdbdbd", lw=0.8, alpha=0.6, zorder=2)
    # cargas y destinos
    for k, ld in enumerate(rec["loads"]):
        g = ld["goal"]; ax.plot(g[0], g[1], marker="X", ms=11, color=LOAD_COL[k], mec="k", zorder=3)
        ax.plot([ql[k, 0], g[0]], [ql[k, 1], g[1]], ls=":", color=LOAD_COL[k], lw=0.8, alpha=0.6, zorder=2)
        poly = load_poly(ql[k], ld)
        ax.add_patch(Polygon(poly, closed=True, facecolor=PHASE_COL[ph[k]], edgecolor=LOAD_COL[k], lw=2, alpha=0.85, zorder=4))
        ax.text(ql[k, 0], ql[k, 1], f"C{k}\n{ph[k]}\n{len(mem[k])}/{ld['r']}", ha="center", va="center", fontsize=7, zorder=6)
    # AMR
    for i in range(N):
        col = LOAD_COL[owner[i]] if i in owner else "#9e9e9e"
        ax.add_patch(Circle(q[i, :2], rec["R"][i], facecolor=col, edgecolor="k", lw=0.8, alpha=0.9, zorder=5))
        e = np.array([np.cos(q[i, 2]), np.sin(q[i, 2])]); ax.plot([q[i, 0], q[i, 0] + 0.35 * e[0]], [q[i, 1], q[i, 1] + 0.35 * e[1]], color="k", lw=1.5, zorder=6)
        ax.text(q[i, 0], q[i, 1] - 0.45, str(i), ha="center", fontsize=6, zorder=6)
    # eventos recientes
    for ev in rec["events"]:
        if t - 3.0 <= ev["t"] <= t:
            ax.plot(ev["p"][0], ev["p"][1], marker="x", ms=12, mew=2.5, color="red", zorder=7)
    lease = rec["lease"][idx]
    ax.set_title(f"t = {t:5.1f} s   fases {ph}   arrendamiento del hueco: {'C' + str(lease) if lease is not None else '—'}   mensajes {rec['msgs'][idx] / 1000:.0f}k", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])


def render_static(rec, out_base):
    K = len(rec["loads"]); N = len(rec["R"]); T = rec["t"]
    fig, ax = plt.subplots(figsize=(11, 7.2))
    ax.set_xlim(-0.5, PLANT_W + 0.5); ax.set_ylim(-0.5, PLANT_H + 0.5); ax.set_aspect("equal"); ax.set_facecolor("#fafafa")
    draw_walls(ax, rec["walls"])
    # trayectorias completas
    for i in range(N):
        tr = np.array([r[i, :2] for r in rec["q"]]); ax.plot(tr[:, 0], tr[:, 1], color="#9e9e9e", lw=0.6, alpha=0.7)
        ax.add_patch(Circle(tr[0], rec["R"][i], facecolor="none", edgecolor="#616161", lw=0.8, ls="--"))
        ax.text(tr[0, 0], tr[0, 1], str(i), ha="center", va="center", fontsize=6, color="#616161")
    for k, ld in enumerate(rec["loads"]):
        tr = np.array([r[k, :2] for r in rec["ql"]])
        # color por fase a lo largo del tiempo
        pts = tr.reshape(-1, 1, 2); segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
        cols = [PHASE_COL[rec["phase"][j][k]] for j in range(len(tr) - 1)]
        ax.add_collection(LineCollection(segs, colors=cols, linewidths=3.5, alpha=0.9))
        ax.add_patch(Polygon(load_poly(rec["ql"][0][k], ld), closed=True, facecolor="none", edgecolor=LOAD_COL[k], lw=2, ls="--"))
        ax.add_patch(Polygon(load_poly(rec["ql"][-1][k], ld), closed=True, facecolor=LOAD_COL[k], alpha=0.35, edgecolor=LOAD_COL[k], lw=2))
        g = ld["goal"]; ax.plot(g[0], g[1], marker="X", ms=12, color=LOAD_COL[k], mec="k")
        ax.text(tr[0, 0], tr[0, 1] + ld["W"] / 2 + 0.3, f"C{k} ({ld['mode']}, {ld['m']:.0f} kg, r*={ld['r']})", ha="center", fontsize=8, color=LOAD_COL[k])
    # instantes de fase: marcar puntos de formación cerrada y entrada al hueco
    for k in range(K):
        prev = None; nlab = 0
        for j, ph in enumerate(rec["phase"]):
            if prev is not None and ph[k] != prev:
                p = rec["ql"][j][k]; ax.plot(p[0], p[1], marker="o", ms=6, color=PHASE_COL[ph[k]], mec="k", zorder=6)
                dy = 6 + 9 * (nlab % 3); nlab += 1
                ax.annotate(f"{ph[k]} {T[j]:.0f}s", (p[0], p[1]), textcoords="offset points", xytext=(5, dy), fontsize=6,
                            arrowprops=dict(arrowstyle="-", lw=0.4, color="#616161"))
            prev = ph[k]
    for ev in rec["events"]:
        ax.plot(ev["p"][0], ev["p"][1], marker="x", ms=9, mew=2, color="red", zorder=7)
    m = rec["metrics"]
    ax.set_title(f"{rec['which']} semilla {rec['seed']} {rec['cfg']}  —  éxito={m['success']} T={m['makespan']:.0f}s E={m['energy_Wh']:.1f}Wh sep.mín={m['min_sep_amr']:.2f}m conflictos={len(rec['events'])}", fontsize=8)
    ax.set_xticks(range(0, 23, 2)); ax.set_yticks(range(0, 15, 2)); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0], [0], color=PHASE_COL[p], lw=3, label=f"fase {p}") for p in ["REC", "FORM", "TRANSPORT", "DONE"]] +
              [Line2D([0], [0], color=LOAD_COL[k], lw=2, label=f"C{k}: inicio (discontinuo) / final (relleno) / destino (X)") for k in range(K)] +
              [Line2D([0], [0], color="#9e9e9e", lw=0.8, label="trayectoria de cada AMR (número = inicio)"),
               Line2D([0], [0], marker="x", color="red", lw=0, label="conflicto: contacto AMR–AMR o carga–pared")], loc="upper right", fontsize=6.5)
    fig.tight_layout(); fig.savefig(out_base + "_traj.pdf"); fig.savefig(out_base + "_traj.png", dpi=150); plt.close(fig)
    # línea de tiempo
    fig, ax = plt.subplots(figsize=(11, 1.2 + 0.5 * K))
    for k in range(K):
        prev = rec["phase"][0][k]; t0 = T[0]
        for j in range(1, len(T)):
            if rec["phase"][j][k] != prev or j == len(T) - 1:
                ax.barh(k, T[j] - t0, left=t0, color=PHASE_COL[prev], edgecolor="none", height=0.6); prev = rec["phase"][j][k]; t0 = T[j]
    lease_t = [T[j] for j in range(len(T)) if rec["lease"][j] is not None]
    if lease_t:
        for j in range(len(T)):
            if rec["lease"][j] is not None: ax.plot([T[j]], [K + 0.0], marker="|", color=LOAD_COL[rec["lease"][j]], ms=8)
    for ev in rec["events"]: ax.plot(ev["t"], K + 0.5, marker="x", color="red", ms=6)
    ax.set_yticks(list(range(K)) + [K, K + 0.5]); ax.set_yticklabels([f"C{k}" for k in range(K)] + ["arrendamiento", "conflictos"], fontsize=8)
    ax.set_xlabel("t [s]"); ax.set_xlim(0, T[-1]); fig.tight_layout(); fig.savefig(out_base + "_timeline.png", dpi=150); fig.savefig(out_base + "_timeline.pdf"); plt.close(fig)


def render_anim(rec, out_mp4, speed=8.0, fps=25):
    every = rec["t"][1] - rec["t"][0]
    stride = max(1, int(round(speed / (fps * every))))
    idxs = list(range(0, len(rec["t"]), stride))
    fig, ax = plt.subplots(figsize=(11, 7.2))
    def upd(n):
        frame(ax, rec, idxs[n]); return []
    ani = animation.FuncAnimation(fig, upd, frames=len(idxs), blit=False)
    ani.save(out_mp4, writer="ffmpeg", fps=fps, dpi=110, bitrate=2400); plt.close(fig)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "cargo2"; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    kw = {}
    for a in sys.argv[3:]:
        k, v = a.split("="); kw[k] = (float(v) if v.replace(".", "", 1).replace("-", "", 1).isdigit() else (v == "True" if v in ("True", "False") else v))
    out_dir = "results/megajuego/figs"; os.makedirs(out_dir, exist_ok=True)
    name = f"{which}_s{seed}" + "".join(f"_{k}-{v}" for k, v in kw.items())
    import pickle
    pk = os.path.join(out_dir, name + ".pkl")
    if os.environ.get("RENDER_ONLY") and os.path.exists(pk):
        rec = pickle.load(open(pk, "rb"))
    else:
        rec = record(seed=seed, which=which, **kw); pickle.dump(rec, open(pk, "wb"))
    render_static(rec, os.path.join(out_dir, name))
    if os.environ.get("RENDER_ONLY"):
        print("ok (solo figuras)", name); return
    render_anim(rec, os.path.join(out_dir, name + ".mp4"))
    json.dump({k: v for k, v in rec["metrics"].items()}, open(os.path.join(out_dir, name + "_metrics.json"), "w"), default=float)
    print("ok", name, rec["metrics"]["success"], f"T={rec['metrics']['makespan']:.0f}", "eventos", len(rec["events"]))


if __name__ == "__main__":
    main()
