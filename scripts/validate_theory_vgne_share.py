"""Independent KKT validation of the closed-form weighted wrench allocation."""
from __future__ import annotations
import json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT/'scripts'))
from tfm_submit_utils import THEORY_ROOT, ensure_dir, write_csv
from viu_mrob_tfm.control.explicit_law import vgne_force_share

def kkt_solution(eta: np.ndarray, offsets: np.ndarray, wrench: np.ndarray) -> np.ndarray:
    n=len(eta); q_inv=np.diag(np.repeat(eta,2)); c=np.zeros((3,2*n))
    for i,(x,y) in enumerate(offsets):
        c[0,2*i]=1.; c[1,2*i+1]=1.; c[2,2*i]=-y; c[2,2*i+1]=x
    return (q_inv@c.T@np.linalg.solve(c@q_inv@c.T,wrench)).reshape(n,2)

def main()->int:
    rng=np.random.default_rng(20260710); out=THEORY_ROOT/'v1'; fig=out/'figures'; tab=out/'tables'; ensure_dir(fig); ensure_dir(tab)
    rows=[]; errors=[]
    for case in range(250):
        n=int(rng.integers(3,8)); eta=rng.uniform(.2,2.,n); offsets=rng.normal(0,.7,(n,2)); offsets-=np.sum(eta[:,None]*offsets,axis=0)/np.sum(eta)
        wrench=np.array([rng.uniform(-40,40),rng.uniform(-40,40),rng.uniform(-15,15)])
        h=float(np.sum(eta)); s=float(np.sum(eta*np.sum(offsets**2,axis=1)))
        numeric=kkt_solution(eta,offsets,wrench)
        closed=np.vstack([vgne_force_share(wrench,offsets[i],float(eta[i]),h,s) for i in range(n)])
        for i in range(n):
            err=float(np.linalg.norm(closed[i]-numeric[i])); errors.append(err)
            rows.append({'case_id':case,'robot_id':i,'team_size':n,'closed_fx':closed[i,0],'closed_fy':closed[i,1],'kkt_fx':numeric[i,0],'kkt_fy':numeric[i,1],'l2_error':err})
    write_csv(tab/'v1_share_vs_independent_kkt.csv',rows,list(rows[0]))
    arr=np.asarray(errors); fig_obj,ax=plt.subplots(figsize=(5.5,4.0)); ax.hist(np.maximum(arr,1e-16),bins=35); ax.set_xscale('log'); ax.set_xlabel('Error L2 frente a KKT independiente'); ax.set_ylabel('Frecuencia'); ax.set_title('V1: reparto cerrado vs. solución KKT'); ax.grid(alpha=.25); fig_obj.tight_layout(); fig_obj.savefig(fig/'fig_v1_kkt_wrench_allocation.png',dpi=220); fig_obj.savefig(fig/'fig_v1_kkt_wrench_allocation.pdf'); plt.close(fig_obj)
    manifest={'validation':'V1 independent KKT wrench allocation','independent_reference':'direct equality-constrained quadratic KKT solve','cases':250,'rows':len(rows),'max_l2_error':float(arr.max()),'rmse':float(np.sqrt(np.mean(arr**2))),'passed':bool(arr.max()<1e-9)}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); print(json.dumps(manifest,indent=2)); return 0 if manifest['passed'] else 1
if __name__=='__main__': raise SystemExit(main())