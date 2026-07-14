"""Independent mechanics validation: Hamiltonian balance and HOCBF QP."""
from __future__ import annotations
import json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT/'scripts'))
from tfm_submit_utils import THEORY_ROOT, ensure_dir, write_csv
from viu_mrob_tfm.control.explicit_law import CircularHazard, ExplicitControlGains, closed_form_hocbf_projection

def main()->int:
    rng=np.random.default_rng(20260711); out=THEORY_ROOT/'v2'; fig=out/'figures'; tab=out/'tables'; ensure_dir(fig); ensure_dir(tab)
    mass=np.diag([18.,18.,5.2]); damping=np.diag([1.5,1.5,.9]); energy_rows=[]
    for case in range(600):
        v=rng.normal(0,1,3); tau=rng.normal(0,25,3); acc=np.linalg.solve(mass,tau-damping@v); eps=1e-6
        fd=(.5*(v+eps*acc)@mass@(v+eps*acc)-.5*(v-eps*acc)@mass@(v-eps*acc))/(2*eps)
        power=float(v@tau-v@damping@v); energy_rows.append({'case_id':case,'hamiltonian_rate_fd':fd,'input_minus_dissipation':power,'abs_error':abs(fd-power)})
    hocbf_rows=[]; gains=ExplicitControlGains(safety_k1=2.4,safety_k2=2.4); hazard=CircularHazard(center_xy=np.zeros(2),velocity_xy=np.zeros(2),radius_m=.72)
    for case in range(350):
        angle=rng.uniform(-np.pi,np.pi); radius=rng.uniform(1.56,4.0); p=radius*np.array([np.cos(angle),np.sin(angle)]); v=rng.normal(0,.8,2); nominal=rng.normal(0,2.,2)
        projected=closed_form_hocbf_projection(nominal,p,v,[hazard],.82,gains=gains,passes=8)
        h=radius**2-(.72+.82)**2; hdot=2*float(p@v); a=2*p; b=-2*float(v@v)-(gains.safety_k1+gains.safety_k2)*hdot-gains.safety_k1*gains.safety_k2*h
        result=minimize(lambda x:.5*float(np.dot(x-nominal,x-nominal)),nominal,jac=lambda x:x-nominal,constraints=[{'type':'ineq','fun':lambda x,a=a,b=b:float(a@x-b),'jac':lambda x,a=a:a}],method='SLSQP',options={'ftol':1e-12,'maxiter':100})
        err=float(np.linalg.norm(projected-result.x)); hocbf_rows.append({'case_id':case,'qp_success':bool(result.success),'projection_error':err,'hocbf_margin':float(a@projected-b)})
    write_csv(tab/'v2_hamiltonian_identity.csv',energy_rows,list(energy_rows[0])); write_csv(tab/'v2_hocbf_vs_qp.csv',hocbf_rows,list(hocbf_rows[0]))
    e=np.array([r['abs_error'] for r in energy_rows]); q=np.array([r['projection_error'] for r in hocbf_rows]); margins=np.array([r['hocbf_margin'] for r in hocbf_rows])
    f,axes=plt.subplots(1,2,figsize=(9.2,3.8)); axes[0].hist(np.maximum(e,1e-16),bins=35); axes[0].set_xscale('log'); axes[0].set_title('Identidad de potencia Hamiltoniana'); axes[0].set_xlabel('error absoluto'); axes[1].scatter(range(len(q)),q,s=8,alpha=.55); axes[1].set_yscale('log'); axes[1].set_title('Proyección cerrada vs. QP SLSQP'); axes[1].set_xlabel('caso'); axes[1].set_ylabel('error L2'); [ax.grid(alpha=.25) for ax in axes]; f.tight_layout(); f.savefig(fig/'fig_v2_hamiltonian_hocbf.png',dpi=220); f.savefig(fig/'fig_v2_hamiltonian_hocbf.pdf'); plt.close(f)
    manifest={'validation':'V2 Lagrange-Hamilton balance and independent HOCBF QP','energy_max_abs_error':float(e.max()),'hocbf_max_projection_error':float(q.max()),'hocbf_min_margin':float(margins.min()),'qp_failures':sum(not r['qp_success'] for r in hocbf_rows),'passed':bool(e.max()<1e-7 and q.max()<1e-6 and margins.min()>-1e-8)}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); print(json.dumps(manifest,indent=2)); return 0 if manifest['passed'] else 1
if __name__=='__main__': raise SystemExit(main())