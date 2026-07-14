"""Common-Lyapunov practical ISS certificate for switched coalition realization errors."""
from __future__ import annotations
import json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_lyapunov
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from tfm_submit_utils import THEORY_ROOT, ensure_dir, write_csv

def main()->int:
    out=THEORY_ROOT/'v3'; fig=out/'figures'; tab=out/'tables'; ensure_dir(fig); ensure_dir(tab)
    m=np.diag([18.,18.,5.2]); d=np.diag([1.5,1.5,.9]); kp=np.diag([18*.85,18*.85,5.2*.9]); kd=np.diag([2*18*np.sqrt(.85),2*18*np.sqrt(.85),2*5.2*np.sqrt(.9)])
    inv=np.linalg.inv(m); z=np.zeros((3,3)); eye=np.eye(3); a=np.block([[z,eye],[-inv@kp,-inv@(kd+d)]]); b=np.vstack([z,inv])
    p=solve_continuous_lyapunov(a.T,-np.eye(6)); eig=np.linalg.eigvalsh(p); residual=np.linalg.norm(a.T@p+p@a+np.eye(6),ord=2); eps=.5; alpha=(1-eps)/eig.max(); sigma=np.linalg.norm(p@b,ord=2)**2/eps
    rows=[]; rng=np.random.default_rng(20260711)
    for dbar in (.25,.5,1.,2.,4.):
        z0=rng.normal(0,.5,6); t_grid=np.linspace(0,35,701); switch_times=np.arange(0,36,1.75); dirs=rng.normal(size=(len(switch_times),3)); dirs/=np.linalg.norm(dirs,axis=1,keepdims=True)
        def ode(t,state):
            idx=min(int(t//1.75),len(dirs)-1); return a@state+b@(dbar*dirs[idx])
        sol=solve_ivp(ode,(0,35),z0,t_eval=t_grid,rtol=1e-9,atol=1e-11); norms=np.linalg.norm(sol.y.T,axis=1); v0=float(z0@p@z0); bound=np.sqrt(np.maximum((v0*np.exp(-alpha*t_grid)+(sigma/alpha)*dbar**2*(1-np.exp(-alpha*t_grid)))/eig.min(),0))
        violation=float(np.max(norms-bound)); ultimate=float(np.sqrt(sigma/(alpha*eig.min()))*dbar); rows.append({'disturbance_bound':dbar,'alpha':alpha,'sigma':sigma,'lambda_min_P':eig.min(),'lambda_max_P':eig.max(),'ultimate_radius_bound':ultimate,'max_numeric_norm':float(norms.max()),'max_bound_violation':violation})
        if dbar==1.: plot_t=t_grid; plot_norm=norms; plot_bound=bound
    write_csv(tab/'v3_practical_iss_certificate.csv',rows,list(rows[0]))
    f,ax=plt.subplots(figsize=(6.4,4.2)); ax.plot(plot_t,plot_norm,label='norma del estado, entrada conmutada'); ax.plot(plot_t,plot_bound,'--',label='cota ISS por Lyapunov común'); ax.set_xlabel('tiempo [s]'); ax.set_ylabel(r'$\|[e,\dot e]\|$'); ax.set_title('V3: ISS práctica bajo error de wrench acotado'); ax.grid(alpha=.25); ax.legend(fontsize=8); f.tight_layout(); f.savefig(fig/'fig_v3_practical_iss.png',dpi=220); f.savefig(fig/'fig_v3_practical_iss.pdf'); plt.close(f)
    manifest={'validation':'V3 common-Lyapunov practical ISS','theorem_status':'proved_under_stated_fixed-load_no-reset_bounded-input_assumptions','lyapunov_min_eigenvalue':float(eig.min()),'lyapunov_residual_2norm':float(residual),'alpha':float(alpha),'sigma':float(sigma),'max_numeric_bound_violation':max(r['max_bound_violation'] for r in rows),'switching_interpretation':'coalition replacement changes bounded wrench-realization input but not load state or common closed-loop A','passed':bool(eig.min()>0 and residual<1e-9 and max(r['max_bound_violation'] for r in rows)<1e-7)}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); print(json.dumps(manifest,indent=2)); return 0 if manifest['passed'] else 1
if __name__=='__main__': raise SystemExit(main())