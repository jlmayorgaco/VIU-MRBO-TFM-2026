"""Arnés de depuración: una misión con traza de fases."""
import numpy as np, time, sys
from .bench import make_scenario, side_of, OPENING
from .mechanism import Mechanism, Config

SPECS = {"cargo": [dict(m=60.0, L=1.6, W=1.1, r=3, modes=("cargo",))],
         "caging": [dict(m=45.0, L=1.25, W=0.95, r=4, modes=("caging",))],
         "both": None, "cargo2": [dict(m=60.0, L=1.6, W=1.1, r=3, modes=("cargo",)), dict(m=95.0, L=1.9, W=1.3, r=3, modes=("cargo",))]}


def run_debug(seed=0, K=2, specs=None, N=8, every=15.0, **kw):
    cfg = Config(seed=seed, **kw)
    P = make_scenario(seed, N=N, K=K, load_specs=specs); M = Mechanism(P, cfg, side_of, OPENING)
    print("cargas:", [(np.round(P.ql[k, :2], 1).tolist(), np.round(P.loads[k].goal, 1).tolist(), P.loads[k].modes[0], P.loads[k].r_req, round(P.loads[k].m)) for k in range(K)])
    print("caps:", np.round([a.cap for a in P.amr], 0).tolist())
    t0 = time.perf_counter(); last = None; steps = int(round(cfg.ctrl_dt / P.dt)); M.caging_sets = {}; M.groups = {}; nxt = 0.0
    while P.t < cfg.T_max and any(ph != "DONE" for ph in M.phase):
        M.control_step()
        for _ in range(steps): P.step(M.tau_cmd, M.caging_sets, M.groups)
        st = (tuple(M.phase), tuple(len(m) for m in M.members), M.lease_owner)
        if st != last: print(f"t={P.t:6.1f} fases={M.phase} miembros={[len(m) for m in M.members]} lease={M.lease_owner}"); last = st
        if P.t >= nxt:
            nxt += every
            info = []
            for k in range(K):
                if M.phase[k] == "FORM":
                    d = [round(float(np.linalg.norm(M.slot_world(k, M.mode[k], s, P.loads[k].r_req) - P.q[i, :2])), 2) for s, i in M.members[k].items()]
                    info.append(f"FORM{k} dist={d}")
                if M.phase[k] == "TRANSPORT":
                    info.append(f"TR{k} pos={np.round(P.ql[k, :2], 2).tolist()} v={np.linalg.norm(P.zl[k, :2]):.2f} p={np.round(M.price[k], 1).tolist()}")
            print(f"   t={P.t:5.0f} minsep={P.min_sep_amr:.2f} pen={P.wall_pen_max:.3f} slip={P.slip_events} " + " | ".join(info))
    m = M.metrics(); print("metrics:", {k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in m.items()}); print("cpu %.1f s" % (time.perf_counter() - t0))
    return M


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "cargo"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    specs = SPECS[which]
    run_debug(seed=seed, K=1 if (specs and len(specs) == 1) else 2, specs=specs, T_max=240.0)
