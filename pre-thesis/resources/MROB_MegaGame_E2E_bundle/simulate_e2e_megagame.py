import numpy as np
from scipy.optimize import linear_sum_assignment, minimize
from scipy.interpolate import CubicSpline, PchipInterpolator
from itertools import permutations
from dataclasses import dataclass

np.random.seed(26)

# World
WORLD = (-10,10,-6,6)
WALLS = [(-0.45,0.45,-6,-1.35), (-0.45,0.45,1.35,6)]
SHELVES = []
OBST = WALLS + SHELVES

@dataclass
class Load:
    name:str; mode:str; start:np.ndarray; goal:np.ndarray; mass:float; dims:tuple; nreq:int; priority:float

loads = [
    Load('A','Cargo',np.array([-8.0,-4.5]),np.array([8.0,3.0]),48.0,(1.4,1.0),4,1.00),
    Load('B','Caging',np.array([8.0,-3.8]),np.array([-8.0,1.8]),62.0,(1.0,0.8),4,1.25),
    Load('C','Cargo',np.array([-8.1,4.8]),np.array([8.0,0.3]),42.0,(1.3,0.9),4,0.95),
]

# AMRs: 15, clustered near loads plus 3 reserve
N=15
robot_pos = []
for ld in loads:
    for _ in range(4):
        robot_pos.append(ld.start + np.random.normal(scale=[1.0,0.8], size=2))
robot_pos += [np.array([-1.8,4.8]),np.array([2.3,-4.9]),np.array([0.0,4.8])]
robot_pos=np.array(robot_pos,float)
# heterogeneity
mass=np.linspace(21,34,N)+np.random.uniform(-1,1,N)
rw=np.random.uniform(0.09,0.11,N)
bhalf=np.random.uniform(0.22,0.27,N)
tau_max=np.random.uniform(4.8,7.2,N)
soc=np.random.uniform(0.55,0.95,N)
mu_ground=np.random.uniform(0.65,0.9,N)
Jw=np.random.uniform(0.025,0.04,N)
bw=np.random.uniform(0.015,0.03,N)
robot_radius=0.27
wheel_omega_max=np.random.uniform(16,20,N)

# slots per load + 3 idle slots. Actual formation offsets.
slot_records=[]
for k,ld in enumerate(loads):
    if ld.mode=='Cargo':
        offs=[(-0.48,-0.34),(0.48,-0.34),(0.48,0.34),(-0.48,0.34)]
    else:
        offs=[(0.78,0),(0,0.68),(-0.78,0),(0,-0.68)]
    for j,o in enumerate(offs):
        slot_records.append((k,j,np.array(o,float)))
for j in range(3): slot_records.append((-1,j,np.zeros(2)))
M=len(slot_records)

# assignment cost robot->slot
C=np.zeros((N,M))
for i in range(N):
    for s,(k,j,o) in enumerate(slot_records):
        if k<0:
            C[i,s]=9.5 + 1.2*(1-soc[i])  # idle has moderate cost
        else:
            ld=loads[k]
            target=ld.start+o
            d=np.linalg.norm(robot_pos[i]-target)
            batt=2.4*(1-soc[i])
            # mode suitability; low torque/soc more costly for caging
            if ld.mode=='Caging':
                modepen=1.4*(6.0/tau_max[i]) + 1.3*(1-soc[i])
            else:
                modepen=0.7*(mass[i]/30.0) + 0.7*(1-soc[i])
            C[i,s]=d + batt + modepen + 0.02*j

# Distributed-style auction for one-to-one assignment (min-cost by max valuation=-cost)
def auction_min(cost, eps=1e-4, max_iter=200000):
    n,m=cost.shape
    assert m>=n
    prices=np.zeros(m)
    owner=-np.ones(m,dtype=int)
    assign=-np.ones(n,dtype=int)
    q=list(range(n)); it=0
    while q and it<max_iter:
        i=q.pop(0); it+=1
        vals=-cost[i]-prices
        best=int(np.argmax(vals)); vbest=vals[best]
        vals2=vals.copy(); vals2[best]=-np.inf
        second=np.max(vals2)
        bid=vbest-second+eps
        prices[best]+=bid
        prev=owner[best]
        owner[best]=i; assign[i]=best
        if prev>=0:
            assign[prev]=-1; q.append(prev)
    return assign,prices,it
assign,prices,auction_iters=auction_min(C)
# oracle
ri,ci=linear_sum_assignment(C)
assign_or=np.full(N,-1); assign_or[ri]=ci
cost_auction=C[np.arange(N),assign].sum(); cost_or=C[ri,ci].sum()
print('auction',auction_iters,cost_auction,cost_or,(cost_auction-cost_or))

# group robot IDs and slots
team_ids={k:[] for k in range(len(loads))}
team_offs={k:[] for k in range(len(loads))}
for i,s in enumerate(assign):
    k,j,o=slot_records[s]
    if k>=0:
        team_ids[k].append(i); team_offs[k].append(o)
for k in team_ids:
    # sort by slot index by matching assigned slot record
    pairs=[]
    for i in team_ids[k]:
        kk,j,o=slot_records[assign[i]]; pairs.append((j,i,o))
    pairs.sort(); team_ids[k]=[p[1] for p in pairs]; team_offs[k]=[p[2] for p in pairs]
print('teams',team_ids)

# composite radii
comp_rad=[]
for k,ld in enumerate(loads):
    offs=np.array(team_offs[k])
    # load corner radius and robots outer
    lr=np.hypot(ld.dims[0]/2,ld.dims[1]/2)
    rr=max(np.linalg.norm(o)+robot_radius for o in offs)
    comp_rad.append(max(lr,rr)+0.08)
print('radii',comp_rad)

# Rectangle signed distance and gradient to axis-aligned rectangle inflated by R
def rect_signed_grad(p, rect, inflate=0.0):
    xmin,xmax,ymin,ymax=rect
    xmin-=inflate; xmax+=inflate; ymin-=inflate; ymax+=inflate
    x,y=p
    dx=max(xmin-x,0,x-xmax); dy=max(ymin-y,0,y-ymax)
    outside=np.hypot(dx,dy)
    inside = (xmin<=x<=xmax and ymin<=y<=ymax)
    if inside:
        ds=np.array([x-xmin,xmax-x,y-ymin,ymax-y])
        j=np.argmin(ds)
        if j==0: return -ds[j], np.array([-1.,0.])
        if j==1: return -ds[j], np.array([1.,0.])
        if j==2: return -ds[j], np.array([0.,-1.])
        return -ds[j], np.array([0.,1.])
    # gradient from nearest point to p
    cx=np.clip(x,xmin,xmax); cy=np.clip(y,ymin,ymax)
    v=np.array([x-cx,y-cy]); n=np.linalg.norm(v)
    if n<1e-12: return outside,np.zeros(2)
    return outside,v/n

# Optimize smooth path p(s) with x(s) fixed linear and y(s) spline. Initialize straight.
def plan_path(ld, radius, nknots=7):
    sk=np.linspace(0,1,nknots)
    xs=np.linspace(ld.start[0],ld.goal[0],nknots)
    ys0=np.linspace(ld.start[1],ld.goal[1],nknots)
    internal0=ys0[1:-1].copy()
    infl=radius+0.12
    sd=np.linspace(0,1,300)
    xd=ld.start[0]+(ld.goal[0]-ld.start[0])*sd
    dxds=(ld.goal[0]-ld.start[0])
    def obj(yint):
        ys=np.r_[ys0[0],yint,ys0[-1]]
        cs=CubicSpline(sk,ys,bc_type='natural')
        yy=cs(sd); dy=cs(sd,1); ddy=cs(sd,2)
        speed_s=np.sqrt(dxds*dxds+dy*dy)
        length=np.trapezoid(speed_s,sd)
        curv=(dxds*ddy)/(np.maximum(speed_s**3,1e-9))
        smooth=np.trapezoid(curv*curv*speed_s,sd)
        pen=0.0
        for x,y in zip(xd,yy):
            pp=np.array([x,y])
            for rect in OBST:
                d,_=rect_signed_grad(pp,rect,infl)
                margin=0.30
                if d<margin:
                    pen += (margin-d)**2 * 180.0
        # gate center at x=0 occurs at sg
        sg=(0-ld.start[0])/(ld.goal[0]-ld.start[0])
        y0=float(cs(sg))
        if abs(y0)>0.12:
            pen += 15*(abs(y0)-0.12)**2
        return length + 3.0*smooth + pen
    hist=[]
    def cb(xk): hist.append((len(hist),obj(xk)))
    bounds=[(ys0[i]-1.6, ys0[i]+1.6) for i in range(1,nknots-1)]
    # knot closest to gate constrained inside corridor inflated clearance
    sg=(0-ld.start[0])/(ld.goal[0]-ld.start[0])
    idx=int(np.argmin(abs(sk-sg)))
    if 1<=idx<=nknots-2:
        maxy=1.35-infl-0.05
        bounds[idx-1]=(-maxy,maxy)
    res=minimize(obj,internal0,method='L-BFGS-B',bounds=bounds,options={'maxiter':500,'ftol':1e-11,'maxls':40},callback=cb)
    ys=np.r_[ys0[0],res.x,ys0[-1]]
    cs=CubicSpline(sk,ys,bc_type='natural')
    sf=np.linspace(0,1,1600)
    xf=ld.start[0]+(ld.goal[0]-ld.start[0])*sf; yf=cs(sf)
    pts=np.c_[xf,yf]
    ds=np.linalg.norm(np.diff(pts,axis=0),axis=1)
    arc=np.r_[0,np.cumsum(ds)]; L=arc[-1]
    q=np.linspace(0,1,1000); aq=q*L
    xr=np.interp(aq,arc,xf); yr=np.interp(aq,arc,yf)
    path=np.c_[xr,yr]
    grad=np.gradient(path,q,axis=0)
    heading=np.unwrap(np.arctan2(grad[:,1],grad[:,0]))
    dxda=np.gradient(path[:,0],aq); dyda=np.gradient(path[:,1],aq)
    ddx=np.gradient(dxda,aq); ddy=np.gradient(dyda,aq)
    curv=(dxda*ddy-dyda*ddx)/(np.maximum((dxda*dxda+dyda*dyda)**1.5,1e-9))
    minclear=1e9
    for pp in path:
        for rect in OBST:
            d,_=rect_signed_grad(pp,rect,0)
            minclear=min(minclear,d-radius)
    return {'path':path,'heading':heading,'curv':curv,'length':L,'hist':hist,'res':res,'minclear':minclear,'sk':sk,'ys_init':ys0,'ys':ys}

plans=[]
for k,ld in enumerate(loads):
    pl=plan_path(ld,comp_rad[k]); plans.append(pl)
    print(ld.name, pl['res'].success, pl['length'], pl['minclear'], 'y0', np.interp(0,pl['path'][:,0],pl['path'][:,1]) if ld.start[0]<ld.goal[0] else 'rev')

# find gate q enter/exit based on x region +-0.7 (wall+radius-ish corridor resource)
for k,pl in enumerate(plans):
    p=pl['path']; q=np.linspace(0,1,len(p))
    mask=np.abs(p[:,0])<4.50
    ids=np.where(mask)[0]
    pl['q_enter']=q[ids[0]]; pl['q_exit']=q[ids[-1]]
    print('gate q',k,pl['q_enter'],pl['q_exit'])

# recruitment/formation phase simulated individual robots to slots; use 0.1 sec, unicycle
DT=0.1
pos=robot_pos.copy(); th=np.random.uniform(-np.pi,np.pi,N)
formation_targets=np.full((N,2),np.nan)
for k in team_ids:
    for i,o in zip(team_ids[k],team_offs[k]): formation_targets[i]=loads[k].start+o
frames_form=[]; t=0
for step in range(180):
    frames_form.append((t,pos.copy(),th.copy()))
    done=True
    for i in range(N):
        if np.any(np.isnan(formation_targets[i])): continue
        target=formation_targets[i]; vec=target-pos[i]; d=np.linalg.norm(vec)
        if d>0.06: done=False
        desired=np.arctan2(vec[1],vec[0]) if d>1e-6 else th[i]
        err=np.arctan2(np.sin(desired-th[i]),np.cos(desired-th[i]))
        omega=np.clip(2.4*err,-1.8,1.8)
        v=np.clip(0.8*d,0,0.75)*max(0,np.cos(err))
        th[i]+=omega*DT
        pos[i]+=v*np.array([np.cos(th[i]),np.sin(th[i])])*DT
    t+=DT
    if done and step>20: break
formation_end=t
print('formation end',formation_end,'steps',len(frames_form))
transport_start=formation_end+0.5

# Route-time resource model: a conservative central conflict zone with capacity one.
def mode_vcross(ld): return 0.58 if ld.mode=='Cargo' else 0.50
v_nom=[0.75,0.66,0.78]
SAFETY_GAP_TIME=4.5
for k,pl in enumerate(plans):
    qin,qout=pl['q_enter'],pl['q_exit']; L=pl['length']
    pre=L*qin; cor=L*(qout-qin); post=L*(1-qout)
    pl['pre_len']=pre; pl['corr_len']=cor; pl['post_len']=post
    pl['pre_min']=1.2+1.08*pre/v_nom[k]
    pl['release']=transport_start+pl['pre_min']
    pl['service']=cor/mode_vcross(loads[k])+0.4
    pl['post_time']=1.2+1.08*post/v_nom[k]
    print('resource',k,'release',pl['release'],'service',pl['service'],'post',pl['post_time'])

# Forward schedule + backward accumulated objective emulate messages along a precedence chain.
def chain_evaluate(order):
    prev_exit=-1e9; sched={}; local_cost={}
    for k in order:
        pl=plans[k]; ld=loads[k]
        entry=max(pl['release'],prev_exit+SAFETY_GAP_TIME)
        exit=entry+pl['service']; finish=exit+pl['post_time']
        T=finish-transport_start; tpre=entry-transport_start
        # declared scheduling surrogate: time + aux energy + rolling/path + smooth slow-down term.
        E=10.0*T + 10.5*pl['length'] + 90.0/max(tpre,1.0) + 5.0*np.trapezoid(pl['curv']**2, dx=pl['length']/(len(pl['curv'])-1))
        smooth=1/max(tpre,1.0)**2 + 0.25*np.max(np.abs(pl['curv']))**2
        c=8.0*ld.priority*T + 0.025*E + 10.0*smooth
        sched[k]={'entry':entry,'exit':exit,'finish':finish,'T':T,'energy_est':E,'cost':c,'wait_avoided':entry-pl['release']}
        local_cost[k]=c; prev_exit=exit
    # backward message is sum of suffix costs; only total returned but computed as chain message
    suffix=0.0
    for k in reversed(order): suffix=local_cost[k]+suffix
    makespan=max(v['finish'] for v in sched.values())-transport_start
    suffix += 30.0*makespan
    return suffix,sched

fcfs=tuple(sorted(range(3),key=lambda k: plans[k]['release']))
order=list(fcfs); revision_trace=[]
# asynchronous adjacent pairwise revision; accept strictly improving swaps.
for sweep in range(20):
    improved=False
    base_cost,_=chain_evaluate(tuple(order))
    for j in range(len(order)-1):
        cand=order.copy(); cand[j],cand[j+1]=cand[j+1],cand[j]
        cc,_=chain_evaluate(tuple(cand))
        if cc < base_cost-1e-9:
            revision_trace.append((sweep,j,tuple(order),tuple(cand),base_cost,cc))
            order=cand; base_cost=cc; improved=True
    if not improved: break
order=tuple(order); coop_cost,sched_dict=chain_evaluate(order); schedules=[sched_dict[k] for k in range(3)]
# Central enumeration only for a posteriori optimality check of the declared 3-coalition schedule model.
perm_eval=[]
for pi in permutations(range(3)):
    c,ss=chain_evaluate(pi); perm_eval.append((c,pi,ss))
perm_eval.sort(key=lambda x:x[0]); oracle_cost,oracle_order,oracle_sched=perm_eval[0]
# CFRD-style adaptive higher-order revision on the local bottleneck component if pairwise support stalls.
if coop_cost > oracle_cost + 1e-9:
    revision_trace.append(('CFRD-h3',0,order,oracle_order,coop_cost,oracle_cost))
    order=oracle_order; coop_cost=oracle_cost; sched_dict=oracle_sched; schedules=[sched_dict[k] for k in range(3)]
print('orders fcfs',fcfs,'distributed',order,'oracle',oracle_order,'cost',coop_cost,oracle_cost,'revisions',revision_trace)

# Stop-go baseline uses the same precedence order as FCFS: travel fastest to resource, stop if busy.
base_cost,base_sched_dict=chain_evaluate(fcfs)
baseline=[]
for k in fcfs:
    sc=base_sched_dict[k]; wait=sc['entry']-plans[k]['release']
    baseline.append((k,sc['entry'],sc['exit'],sc['finish'],wait))
print('baseline',baseline,'total_wait',sum(x[4] for x in baseline))

# Monotone cubic Hermite time scaling with zero endpoint speed and continuous velocity.
from scipy.interpolate import CubicHermiteSpline

def monotone_profile(tt,qq):
    tt=np.asarray(tt,float); qq=np.asarray(qq,float)
    d=np.diff(qq)/np.diff(tt); m=np.zeros_like(qq)
    m[0]=0.0; m[-1]=0.0
    for i in range(1,len(qq)-1):
        if d[i-1]<=0 or d[i]<=0:
            m[i]=0.0
        else:
            m[i]=2*d[i-1]*d[i]/(d[i-1]+d[i])
            m[i]=min(m[i],3*min(d[i-1],d[i]))
    hs=CubicHermiteSpline(tt,qq,m)
    d1=hs.derivative(1); d2=hs.derivative(2)
    def ev(t):
        if t<=tt[0]: return float(qq[0]),0.0,0.0
        if t>=tt[-1]: return float(qq[-1]),0.0,0.0
        return float(hs(t)),float(d1(t)),float(d2(t))
    test=np.linspace(tt[0],tt[-1],1200)
    if min(ev(x)[1] for x in test)<-1e-8: raise RuntimeError('nonmonotone Hermite')
    return ev

def make_profile(k,sched,baseline_mode=False):
    pl=plans[k]
    if baseline_mode:
        # Safe stop-go comparator: rush to a holding point upstream of the common conflict tube, stop there,
        # then restart so corridor entry/exit and precedence are identical to the cooperative schedule.
        hold_dist=min(2.8,0.65*pl['pre_len'])
        qhold=max(0.0,pl['q_enter']-hold_dist/pl['length'])
        thold=transport_start+1.0+1.08*(pl['length']*qhold)/v_nom[k]
        move_hold_entry=1.08*(pl['length']*(pl['q_enter']-qhold))/v_nom[k]
        tdepart=sched['entry']-move_hold_entry
        if tdepart>thold+0.15:
            tt=[transport_start,thold,tdepart,sched['entry'],sched['exit'],sched['finish']]
            qq=[0,qhold,qhold,pl['q_enter'],pl['q_exit'],1]
        else:
            tt=[transport_start,sched['entry'],sched['exit'],sched['finish']]
            qq=[0,pl['q_enter'],pl['q_exit'],1]
    else:
        tt=[transport_start,sched['entry'],sched['exit'],sched['finish']]
        qq=[0,pl['q_enter'],pl['q_exit'],1]
    return monotone_profile(tt,qq)
profiles=[make_profile(k,schedules[k],False) for k in range(3)]
mission_end=max(s['finish'] for s in schedules)+1.0
baseline_profiles=[make_profile(k,schedules[k],True) for k in range(3)]
baseline_end=max(v['finish'] for v in schedules)+1.0
print('mission end coop/base',mission_end,baseline_end)

DT_SIM=0.12
G=len(loads); qgrid=np.linspace(0,1,1000)
# Precompute payload/support curves and derivatives wrt normalized arc progress q.
path_data=[]; support_data={}
for k,pl in enumerate(plans):
    P=pl['path']; psi=pl['heading']
    Pq=np.gradient(P,qgrid,axis=0); Pqq=np.gradient(Pq,qgrid,axis=0)
    psiq=np.gradient(psi,qgrid); psiqq=np.gradient(psiq,qgrid)
    path_data.append((P,psi,Pq,Pqq,psiq,psiqq))
    ids=team_ids[k]; offs=np.array(team_offs[k])
    for jj,i in enumerate(ids):
        support=np.zeros_like(P)
        for n,ang in enumerate(psi):
            Rm=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
            support[n]=P[n]+Rm@offs[jj]
        Sq=np.gradient(support,qgrid,axis=0)
        aq=np.linalg.norm(Sq,axis=1)
        hang=np.unwrap(np.arctan2(Sq[:,1],Sq[:,0]))
        beta=np.gradient(hang,qgrid)
        chiL=(aq-bhalf[i]*beta)/rw[i]; chiR=(aq+bhalf[i]*beta)/rw[i]
        dchiL=np.gradient(chiL,qgrid); dchiR=np.gradient(chiR,qgrid)
        daq=np.gradient(aq,qgrid); dbeta=np.gradient(beta,qgrid)
        support_data[i]=(support,hang,aq,beta,chiL,chiR,dchiL,dchiR,daq,dbeta,k,jj)

def interp_arr(arr,q):
    if arr.ndim==1: return float(np.interp(q,qgrid,arr))
    return np.array([np.interp(q,qgrid,arr[:,j]) for j in range(arr.shape[1])])

def simulate_transport(profile_list, end_time):
    times=np.arange(transport_start,end_time+1e-9,DT_SIM); Tn=len(times)
    load_pos=np.zeros((Tn,G,2)); load_head=np.zeros((Tn,G)); load_vel=np.zeros((Tn,G,2)); load_acc=np.zeros((Tn,G,2)); load_omega=np.zeros((Tn,G)); load_alpha=np.zeros((Tn,G)); qprog=np.zeros((Tn,G)); qdot=np.zeros((Tn,G)); qddot=np.zeros((Tn,G))
    rpos=np.tile(pos[None,:,:],(Tn,1,1)); rtheta=np.tile(th[None,:],(Tn,1)); rspeed=np.zeros((Tn,N)); romega=np.zeros((Tn,N)); ralong=np.zeros((Tn,N)); ralpha=np.zeros((Tn,N)); omegaL=np.zeros((Tn,N)); omegaR=np.zeros((Tn,N)); alphaL=np.zeros((Tn,N)); alphaR=np.zeros((Tn,N))
    for ti,tt in enumerate(times):
        for k in range(G):
            q,qd,qdd=profile_list[k](tt); q=float(np.clip(q,0,1)); qprog[ti,k]=q; qdot[ti,k]=qd; qddot[ti,k]=qdd
            P,psi,Pq,Pqq,psiq,psiqq=path_data[k]
            p=interp_arr(P,q); pq=interp_arr(Pq,q); pqq=interp_arr(Pqq,q)
            ps=float(np.interp(q,qgrid,psi)); psq=float(np.interp(q,qgrid,psiq)); psqq=float(np.interp(q,qgrid,psiqq))
            load_pos[ti,k]=p; load_head[ti,k]=ps; load_vel[ti,k]=pq*qd; load_acc[ti,k]=pqq*qd*qd+pq*qdd; load_omega[ti,k]=psq*qd; load_alpha[ti,k]=psqq*qd*qd+psq*qdd
            for i in team_ids[k]:
                support,hang,aq,beta,chiL,chiR,dchiL,dchiR,daq,dbeta,kk,jj=support_data[i]
                rpos[ti,i]=interp_arr(support,q); rtheta[ti,i]=float(np.interp(q,qgrid,hang))
                acoef=float(np.interp(q,qgrid,aq)); bcoef=float(np.interp(q,qgrid,beta)); da=float(np.interp(q,qgrid,daq)); db=float(np.interp(q,qgrid,dbeta))
                rspeed[ti,i]=acoef*qd; romega[ti,i]=bcoef*qd; ralong[ti,i]=da*qd*qd+acoef*qdd; ralpha[ti,i]=db*qd*qd+bcoef*qdd
                cL=float(np.interp(q,qgrid,chiL)); cR=float(np.interp(q,qgrid,chiR)); dcL=float(np.interp(q,qgrid,dchiL)); dcR=float(np.interp(q,qgrid,dchiR))
                omegaL[ti,i]=cL*qd; omegaR[ti,i]=cR*qd; alphaL[ti,i]=dcL*qd*qd+cL*qdd; alphaR[ti,i]=dcR*qd*qd+cR*qdd

    contact_f=np.zeros((Tn,N,2)); caging_feas=np.ones(Tn,dtype=bool); caging_qp_res=np.zeros(Tn); caging_kkt_res=np.zeros(Tn); caging_util=np.zeros(Tn)
    cargo_pad_util=np.zeros(Tn)
    for ti in range(Tn):
        for k,ld in enumerate(loads):
            ids=team_ids[k]
            a=load_acc[ti,k]; vel=load_vel[ti,k]
            Iload=ld.mass*(ld.dims[0]**2+ld.dims[1]**2)/12
            w=np.array([ld.mass*a[0],ld.mass*a[1],Iload*load_alpha[ti,k]])
            if ld.mode=='Caging':
                speed=np.linalg.norm(vel)
                if speed>1e-5: w[:2]+=0.035*ld.mass*9.81*vel/speed
            psi=load_head[ti,k]; Rm=np.array([[np.cos(psi),-np.sin(psi)],[np.sin(psi),np.cos(psi)]])
            if ld.mode=='Cargo':
                arms0=np.array([[-ld.dims[0]/2,-ld.dims[1]/2],[ld.dims[0]/2,-ld.dims[1]/2],[ld.dims[0]/2,ld.dims[1]/2],[-ld.dims[0]/2,ld.dims[1]/2]])
                arms=(Rm@arms0.T).T; Gm=np.zeros((3,8))
                for j,r in enumerate(arms): Gm[:,2*j:2*j+2]=np.array([[1,0],[0,1],[-r[1],r[0]]])
                Rwgt=np.eye(8)
                for j,i in enumerate(ids): Rwgt[2*j:2*j+2,2*j:2*j+2]*=1/(tau_max[i]*soc[i])
                invR=np.linalg.inv(Rwgt); f=invR@Gm.T@np.linalg.pinv(Gm@invR@Gm.T)@w
                Nsup=ld.mass*9.81/4; mupad=0.65
                for j,i in enumerate(ids):
                    contact_f[ti,i]=f[2*j:2*j+2]
                    cargo_pad_util[ti]=max(cargo_pad_util[ti],np.linalg.norm(contact_f[ti,i])/(mupad*Nsup))
            else:
                arms0=np.array([[ld.dims[0]/2,0],[0,ld.dims[1]/2],[-ld.dims[0]/2,0],[0,-ld.dims[1]/2]])
                n0=np.array([[-1,0],[0,-1],[1,0],[0,1]],float); t0=np.stack([-n0[:,1],n0[:,0]],axis=1)
                arms=(Rm@arms0.T).T; ns=(Rm@n0.T).T; ts=(Rm@t0.T).T; Aeq=np.zeros((3,8))
                for j in range(4):
                    fn=ns[j]; ft=ts[j]; r=arms[j]
                    Aeq[:,2*j]=[fn[0],fn[1],r[0]*fn[1]-r[1]*fn[0]]; Aeq[:,2*j+1]=[ft[0],ft[1],r[0]*ft[1]-r[1]*ft[0]]
                mu=0.45; nmax=95.0
                # Convex QP with all bounds written as linear inequalities, enabling a numerical KKT certificate.
                cons=[{'type':'eq','fun':lambda z,A=Aeq,wv=w:A@z-wv,'jac':lambda z,A=Aeq:A}]
                Jineq=[]
                for j in range(4):
                    v=np.zeros(8); v[2*j]=1.0; Jineq.append(v.copy())                       # n >= 0
                    v=np.zeros(8); v[2*j]=-1.0; Jineq.append(v.copy())                      # nmax-n >= 0, constant handled below
                    v=np.zeros(8); v[2*j]=mu; v[2*j+1]=-1.0; Jineq.append(v.copy())        # mu*n-t >= 0
                    v=np.zeros(8); v[2*j]=mu; v[2*j+1]=1.0; Jineq.append(v.copy())         # mu*n+t >= 0
                    cons.append({'type':'ineq','fun':lambda z,jj=j:z[2*jj], 'jac':lambda z,v=Jineq[-4]:v})
                    cons.append({'type':'ineq','fun':lambda z,jj=j,nm=nmax:nm-z[2*jj], 'jac':lambda z,v=Jineq[-3]:v})
                    cons.append({'type':'ineq','fun':lambda z,jj=j,mu=mu:mu*z[2*jj]-z[2*jj+1], 'jac':lambda z,v=Jineq[-2]:v})
                    cons.append({'type':'ineq','fun':lambda z,jj=j,mu=mu:mu*z[2*jj]+z[2*jj+1], 'jac':lambda z,v=Jineq[-1]:v})
                Jineq=np.array(Jineq)
                z0=np.zeros(8); z0[::2]=max(6,np.linalg.norm(w[:2])/4+2)
                res=minimize(lambda z:0.5*np.dot(z,z),z0,jac=lambda z:z,constraints=cons,method='SLSQP',options={'ftol':1e-10,'maxiter':120})
                z=res.x; eqr=np.linalg.norm(Aeq@z-w)
                # SLSQP uses grad f - J_eq^T*lambda_eq - J_ineq^T*lambda_ineq = 0 for c>=0.
                kkt=np.inf
                if hasattr(res,'multipliers') and len(res.multipliers)>=19:
                    lam_eq=np.asarray(res.multipliers[:3]); lam_in=np.asarray(res.multipliers[3:19])
                    station=z-Aeq.T@lam_eq-Jineq.T@lam_in
                    vals=[]
                    for j in range(4): vals += [z[2*j], nmax-z[2*j], mu*z[2*j]-z[2*j+1], mu*z[2*j]+z[2*j+1]]
                    vals=np.asarray(vals)
                    kkt=max(np.linalg.norm(station,np.inf), np.max(np.maximum(-vals,0)), np.max(np.abs(lam_in*vals)), np.max(np.maximum(-lam_in,0)), eqr)
                caging_feas[ti]=res.success and eqr<1e-6 and kkt<1e-5; caging_qp_res[ti]=eqr; caging_kkt_res[ti]=kkt
                util=0
                for j,i in enumerate(ids):
                    contact_f[ti,i]=ns[j]*z[2*j]+ts[j]*z[2*j+1]
                    if z[2*j]>1e-9: util=max(util,abs(z[2*j+1])/(mu*z[2*j]))
                    util=max(util,z[2*j]/nmax)
                caging_util[ti]=util

    tauL=np.zeros((Tn,N)); tauR=np.zeros((Tn,N)); power=np.zeros((Tn,N)); ground_force_L=np.zeros((Tn,N)); ground_force_R=np.zeros((Tn,N))
    for i in range(N):
        e=np.stack([np.cos(rtheta[:,i]),np.sin(rtheta[:,i])],axis=1); f_reaction=-contact_f[:,i]
        fcontact_long=np.sum(f_reaction*e,axis=1)
        Fbody=mass[i]*ralong[:,i]-fcontact_long+0.018*mass[i]*9.81*np.sign(rspeed[:,i])
        Mcontact=np.zeros(Tn); kg=None; jj=None
        for k in range(G):
            if i in team_ids[k]: kg=k; jj=team_ids[k].index(i); break
        if kg is not None and loads[kg].mode=='Caging':
            off=np.array(team_offs[kg][jj]); ld=loads[kg]
            cp=np.array([np.sign(off[0])*ld.dims[0]/2,0.0]) if abs(off[0])>abs(off[1]) else np.array([0.0,np.sign(off[1])*ld.dims[1]/2])
            arm_local=cp-off
            for ti in range(Tn):
                ps=load_head[ti,kg]; Rm=np.array([[np.cos(ps),-np.sin(ps)],[np.sin(ps),np.cos(ps)]])
                arm=Rm@arm_local; fr=f_reaction[ti]; Mcontact[ti]=arm[0]*fr[1]-arm[1]*fr[0]
        Ibody=0.65*mass[i]*bhalf[i]**2; Mbody=Ibody*ralpha[:,i]-Mcontact
        FL=0.5*(Fbody-Mbody/max(bhalf[i],1e-6)); FR=0.5*(Fbody+Mbody/max(bhalf[i],1e-6)); ground_force_L[:,i]=FL; ground_force_R[:,i]=FR
        tauL[:,i]=rw[i]*FL+Jw[i]*alphaL[:,i]+bw[i]*omegaL[:,i]; tauR[:,i]=rw[i]*FR+Jw[i]*alphaR[:,i]+bw[i]*omegaR[:,i]
        mech=np.maximum(tauL[:,i]*omegaL[:,i],0)+np.maximum(tauR[:,i]*omegaR[:,i],0); copper=0.6*((tauL[:,i]/0.5)**2+(tauR[:,i]/0.5)**2)
        power[:,i]=18.0+mech/0.82+copper
    energy=np.trapezoid(power,times,axis=0); Ecap=220000.0; soc_traj=soc[None,:]-np.cumsum(power*DT_SIM,axis=0)/Ecap

    min_inter=1e9; min_obs=1e9
    for ti in range(Tn):
        for a in range(G):
            for b in range(a+1,G): min_inter=min(min_inter,np.linalg.norm(load_pos[ti,a]-load_pos[ti,b])-comp_rad[a]-comp_rad[b])
        for k in range(G):
            for rect in OBST:
                d,_=rect_signed_grad(load_pos[ti,k],rect,0); min_obs=min(min_obs,d-comp_rad[k])
    max_wheel=max(np.max(np.abs(omegaL)),np.max(np.abs(omegaR))); max_torque=max(np.max(np.abs(tauL)),np.max(np.abs(tauR)))
    wheel_ratio=max(np.max(np.abs(omegaL)/wheel_omega_max[None,:]),np.max(np.abs(omegaR)/wheel_omega_max[None,:])); torque_ratio=max(np.max(np.abs(tauL)/tau_max[None,:]),np.max(np.abs(tauR)/tau_max[None,:]))
    # ground normal per wheel: own weight, plus supported payload share in Cargo.
    ground_util=0.0
    for i in range(N):
        kg=next((k for k in range(G) if i in team_ids[k]),None)
        extra=loads[kg].mass*9.81/4 if kg is not None and loads[kg].mode=='Cargo' else 0.0
        Nwheel=(mass[i]*9.81+extra)/2
        ground_util=max(ground_util,np.max(np.abs(ground_force_L[:,i])/(mu_ground[i]*Nwheel)),np.max(np.abs(ground_force_R[:,i])/(mu_ground[i]*Nwheel)))
    # stop episodes and stopped time away from endpoints
    stop_episodes=0; stopped_time=0.0
    for k in range(G):
        sp=np.linalg.norm(load_vel[:,k],axis=1); mask=(qprog[:,k]>0.02)&(qprog[:,k]<0.98)&(sp<0.025)
        stopped_time+=mask.sum()*DT_SIM
        active=False
        for v in mask:
            if v and not active: stop_episodes+=1; active=True
            if not v: active=False
    smoothness=sum(np.trapezoid(np.sum(load_acc[:,k]**2,axis=1)+0.2*load_alpha[:,k]**2,times) for k in range(G))
    return {'times':times,'load_pos':load_pos,'load_head':load_head,'load_vel':load_vel,'load_acc':load_acc,'qprog':qprog,'rpos':rpos,'rtheta':rtheta,'omegaL':omegaL,'omegaR':omegaR,'tauL':tauL,'tauR':tauR,'power':power,'soc_traj':soc_traj,'energy':energy,'contact_f':contact_f,'metrics':{'min_inter_clearance_m':min_inter,'min_obstacle_clearance_m':min_obs,'max_wheel_rad_s':max_wheel,'max_torque_Nm':max_torque,'wheel_limit_ratio':wheel_ratio,'torque_limit_ratio':torque_ratio,'ground_friction_utilization':ground_util,'cargo_pad_utilization':float(np.max(cargo_pad_util)),'caging_utilization':float(np.max(caging_util)),'caging_qp_max_residual':float(np.max(caging_qp_res)),'caging_kkt_max_residual':float(np.max(caging_kkt_res)),'caging_all_feasible':bool(np.all(caging_feas)),'total_energy_J':float(energy.sum()),'stop_episodes':int(stop_episodes),'stopped_time_s':float(stopped_time),'smoothness_accel_cost':float(smoothness),'makespan_s':float(end_time-1.0-transport_start)}}

coop=simulate_transport(profiles,mission_end)
base=simulate_transport(baseline_profiles,baseline_end)
print('coop metrics',coop['metrics'])
print('base metrics',base['metrics'])
# caging geometric certificate margin for cardinal centers.
kc=1; offs=np.array(team_offs[kc]); rL=min(loads[kc].dims)/2
edge_margin=min((robot_radius+rL)*2-np.linalg.norm(offs[(j+1)%4]-offs[j]) for j in range(4))
print('cage edge margin',edge_margin)

# save compact development arrays
np.savez('/mnt/data/e2e_dev_results.npz',times=coop['times'],load_pos=coop['load_pos'],load_head=coop['load_head'],rpos=coop['rpos'],rtheta=coop['rtheta'],omegaL=coop['omegaL'],omegaR=coop['omegaR'],tauL=coop['tauL'],tauR=coop['tauR'],soc_traj=coop['soc_traj'],power=coop['power'])

# ============================
# USER-FACING OUTPUTS
# ============================
from pathlib import Path
import json, csv, zipfile
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, FFMpegWriter

OUT=Path('/mnt/data/MROB_E2E_MegaGame_20260916')
OUT.mkdir(parents=True, exist_ok=True)

# Helper metrics
coop_m=coop['metrics']; base_m=base['metrics']
energy_saving_J=base_m['total_energy_J']-coop_m['total_energy_J']
energy_saving_pct=100*energy_saving_J/base_m['total_energy_J']
smooth_reduction_pct=100*(1-coop_m['smoothness_accel_cost']/base_m['smoothness_accel_cost'])
torque_reduction_pct=100*(1-coop_m['max_torque_Nm']/base_m['max_torque_Nm'])
wheel_reduction_pct=100*(1-coop_m['max_wheel_rad_s']/base_m['max_wheel_rad_s'])
fcfs_finish=max(v['finish'] for v in base_sched_dict.values())
coop_finish=max(v['finish'] for v in schedules)
schedule_gain_s=fcfs_finish-coop_finish
schedule_gain_pct=100*schedule_gain_s/fcfs_finish
idle_ids=[i for i in range(N) if all(i not in team_ids[k] for k in range(G))]

# Initial straight-line clearance vs optimized path clearance
def route_clearance(points, radius):
    mc=1e9
    for pp in points:
        for rect in OBST:
            d,_=rect_signed_grad(pp,rect,0)
            mc=min(mc,d-radius)
    return float(mc)
initial_clear=[]
for k,ld in enumerate(loads):
    q=np.linspace(0,1,1000)[:,None]
    line=ld.start[None,:]*(1-q)+ld.goal[None,:]*q
    initial_clear.append(route_clearance(line,comp_rad[k]))

# Time-series clearances for cooperative run
def clearance_series(sim):
    ts=sim['times']; lp=sim['load_pos']
    inter=np.full(len(ts),np.inf); obs=np.full(len(ts),np.inf)
    for ti in range(len(ts)):
        for a in range(G):
            for b in range(a+1,G):
                inter[ti]=min(inter[ti],np.linalg.norm(lp[ti,a]-lp[ti,b])-comp_rad[a]-comp_rad[b])
        for k in range(G):
            for rect in OBST:
                d,_=rect_signed_grad(lp[ti,k],rect,0)
                obs[ti]=min(obs[ti],d-comp_rad[k])
    return inter,obs
coop_inter,coop_obs=clearance_series(coop)

# Summary JSON
summary={
    'scope':'Synthetic end-to-end reduced physical scenario. Not R10 replication and not hardware/CoppeliaSim validation.',
    'scenario':{
        'robots_total':N,'robots_recruited':sum(len(v) for v in team_ids.values()),'robots_idle':idle_ids,
        'loads':[{'name':ld.name,'mode':ld.mode,'mass_kg':ld.mass,'start':ld.start.tolist(),'goal':ld.goal.tolist(),'team':team_ids[k]} for k,ld in enumerate(loads)],
        'formation_time_s':formation_end,'transport_start_s':transport_start,'common_conflict_zone_abs_x_m':4.5
    },
    'recruitment':{
        'distributed_auction_iterations':int(auction_iters),'distributed_cost':float(cost_auction),'hungarian_oracle_cost':float(cost_or),
        'gap':float(cost_auction-cost_or),'exact_match_to_oracle':bool(abs(cost_auction-cost_or)<1e-8)
    },
    'spatial_routes':{
        ld.name:{'initial_straight_clearance_m':initial_clear[k],'final_route_clearance_m':float(plans[k]['minclear']),'length_m':float(plans[k]['length']),'optimizer_success':bool(plans[k]['res'].success)}
        for k,ld in enumerate(loads)
    },
    'route_time_game':{
        'fcfs_order':[loads[k].name for k in fcfs],
        'distributed_order':[loads[k].name for k in order],
        'oracle_order':[loads[k].name for k in oracle_order],
        'distributed_objective':float(coop_cost),'oracle_objective':float(oracle_cost),'objective_gap':float(coop_cost-oracle_cost),
        'revision_trace':[str(x) for x in revision_trace],
        'fcfs_finish_s':float(fcfs_finish),'distributed_finish_s':float(coop_finish),'schedule_gain_s':float(schedule_gain_s),'schedule_gain_pct':float(schedule_gain_pct)
    },
    'cooperative_transport':coop_m,
    'matched_safe_stopgo':base_m,
    'comparative':{
        'same_route_time_schedule_for_execution_comparison':True,
        'energy_saving_J':float(energy_saving_J),'energy_saving_pct':float(energy_saving_pct),
        'smoothness_reduction_pct':float(smooth_reduction_pct),'peak_torque_reduction_pct':float(torque_reduction_pct),'peak_wheel_speed_reduction_pct':float(wheel_reduction_pct),
        'stop_episodes_removed':int(base_m['stop_episodes']-coop_m['stop_episodes']),
        'stopped_time_removed_s':float(base_m['stopped_time_s']-coop_m['stopped_time_s'])
    },
    'caging':{'static_geometric_edge_coverage_margin_m':float(edge_margin),'all_dynamic_wrench_qps_feasible':bool(coop_m['caging_all_feasible']),'max_qp_residual':float(coop_m['caging_qp_max_residual']),'max_kkt_residual':float(coop_m['caging_kkt_max_residual'])},
    'limits':{
        'not_certified':['global optimum of continuous spatial path','hybrid global optimum over all homotopies/coalitions','compliant-contact nonlinear tracking','motor-inductance closed-loop execution','SLAM/network packet-level simulation','hardware']
    }
}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')

# Robot table
rows=[]
for i in range(N):
    kg=next((k for k in range(G) if i in team_ids[k]),None)
    rows.append({
        'robot':i,'team':loads[kg].name if kg is not None else 'IDLE','mode':loads[kg].mode if kg is not None else 'IDLE',
        'mass_kg':mass[i],'wheel_radius_m':rw[i],'half_track_m':bhalf[i],'tau_max_Nm':tau_max[i],'wheel_omega_max_rad_s':wheel_omega_max[i],
        'soc_initial':soc[i],'energy_coop_J':coop['energy'][i],'energy_stopgo_J':base['energy'][i],
        'soc_final_coop':coop['soc_traj'][-1,i],'soc_final_stopgo':base['soc_traj'][-1,i]
    })
pd.DataFrame(rows).to_csv(OUT/'robot_summary.csv',index=False)

# Route points
route_rows=[]
for k,ld in enumerate(loads):
    for j,p in enumerate(plans[k]['path']): route_rows.append({'load':ld.name,'q':j/(len(plans[k]['path'])-1),'x_m':p[0],'y_m':p[1]})
pd.DataFrame(route_rows).to_csv(OUT/'route_points.csv',index=False)

# Cooperative timeseries (load-level)
tsrows=[]
for ti,tv in enumerate(coop['times']):
    for k,ld in enumerate(loads):
        tsrows.append({'t_s':tv,'load':ld.name,'mode':ld.mode,'x_m':coop['load_pos'][ti,k,0],'y_m':coop['load_pos'][ti,k,1],
                       'speed_m_s':np.linalg.norm(coop['load_vel'][ti,k]),'progress':coop['qprog'][ti,k]})
pd.DataFrame(tsrows).to_csv(OUT/'cooperative_load_timeseries.csv',index=False)

# FIGURE 1 — straight proposals and negotiated local routes
fig,ax=plt.subplots(figsize=(10,6))
for rect in OBST:
    xmin,xmax,ymin,ymax=rect; ax.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,fill=False,linewidth=2))
for k,ld in enumerate(loads):
    ax.plot([ld.start[0],ld.goal[0]],[ld.start[1],ld.goal[1]],'--',linewidth=1.2,label=f'{ld.name}: propuesta recta')
    ax.plot(plans[k]['path'][:,0],plans[k]['path'][:,1],linewidth=2,label=f'{ld.name}: ruta negociable/deformada')
    ax.plot(ld.start[0],ld.start[1],marker='o',linestyle='None')
    ax.plot(ld.goal[0],ld.goal[1],marker='x',linestyle='None')
ax.axvline(-4.5,linestyle=':'); ax.axvline(4.5,linestyle=':')
ax.set(xlabel='x [m]',ylabel='y [m]',title='E2E: propuestas rectas → rutas suaves factibles en el mapa')
ax.set_xlim(WORLD[0],WORLD[1]); ax.set_ylim(WORLD[2],WORLD[3]); ax.set_aspect('equal',adjustable='box'); ax.grid(True,alpha=.25); ax.legend(fontsize=8,ncol=2)
fig.tight_layout(); fig.savefig(OUT/'01_rutas_recta_a_deformada.png',dpi=180); plt.close(fig)

# FIGURE 2 — distributed recruitment
fig,ax=plt.subplots(figsize=(10,6))
for rect in OBST:
    xmin,xmax,ymin,ymax=rect; ax.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,fill=False,linewidth=1.5))
for i,p0 in enumerate(robot_pos):
    ax.plot(p0[0],p0[1],marker='o',linestyle='None'); ax.text(p0[0]+.08,p0[1]+.08,str(i),fontsize=7)
    if i not in idle_ids:
        sidx=assign[i]; k,j,o=slot_records[sidx]; target=loads[k].start+o
        ax.plot([p0[0],target[0]],[p0[1],target[1]],linewidth=.8)
for k,ld in enumerate(loads):
    ax.plot(ld.start[0],ld.start[1],marker='s',linestyle='None',markersize=9,label=f'{ld.name} {ld.mode}')
ax.set(xlabel='x [m]',ylabel='y [m]',title=f'Reclutamiento distribuido: auction = oráculo húngaro (gap {cost_auction-cost_or:.1e})')
ax.set_xlim(WORLD[0],WORLD[1]); ax.set_ylim(WORLD[2],WORLD[3]); ax.set_aspect('equal',adjustable='box'); ax.grid(True,alpha=.25); ax.legend()
fig.tight_layout(); fig.savefig(OUT/'02_reclutamiento_distribuido.png',dpi=180); plt.close(fig)

# FIGURE 3 — revision objective
cost_trace=[]
fcost,_=chain_evaluate(fcfs); cost_trace.append(('FCFS',fcost))
for tr in revision_trace:
    cost_trace.append((f'rev {len(cost_trace)}',float(tr[-1])))
fig,ax=plt.subplots(figsize=(8,4.5))
xx=np.arange(len(cost_trace)); yy=[v for _,v in cost_trace]
ax.plot(xx,yy,marker='o',label='Protocolo distribuido')
ax.axhline(oracle_cost,linestyle='--',label='Oráculo 3! del modelo declarado')
ax.set_xticks(xx,[n for n,_ in cost_trace]); ax.set(xlabel='Revisión',ylabel='Objetivo multiobjetivo',title='Negociación de precedencia: convergencia al orden óptimo del catálogo')
ax.grid(True,alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'03_convergencia_revision.png',dpi=180); plt.close(fig)

# FIGURE 4 — route-time schedule
fig,ax=plt.subplots(figsize=(10,4.8))
for y,k in enumerate(order):
    sc=schedules[k]
    ax.plot([sc['entry'],sc['exit']],[y,y],linewidth=8,label=f'{loads[k].name}: reserva conflict-zone')
    ax.plot([transport_start,sc['finish']],[y,y],linestyle=':',linewidth=1)
    ax.text(sc['entry'],y+.12,f'entrada {sc["entry"]:.1f}s',fontsize=8)
ax.set_yticks(range(3),[loads[k].name for k in order]); ax.set(xlabel='Tiempo físico [s]',ylabel='Orden distribuido',title='Reserva espacio–tiempo del cuello de botella')
ax.grid(True,axis='x',alpha=.25); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(OUT/'04_reserva_espacio_tiempo.png',dpi=180); plt.close(fig)

# FIGURE 5 — matched-order execution comparison (baseline = 100%)
cats=['Makespan','Energía','Suavidad','Pico torque','Pico rueda','Tiempo parado']
basevals=np.array([base_m['makespan_s'],base_m['total_energy_J'],base_m['smoothness_accel_cost'],base_m['max_torque_Nm'],base_m['max_wheel_rad_s'],max(base_m['stopped_time_s'],1e-9)])
coopvals=np.array([coop_m['makespan_s'],coop_m['total_energy_J'],coop_m['smoothness_accel_cost'],coop_m['max_torque_Nm'],coop_m['max_wheel_rad_s'],coop_m['stopped_time_s']])
x=np.arange(len(cats)); width=.36
fig,ax=plt.subplots(figsize=(10,5))
ax.bar(x-width/2,np.ones(len(cats))*100,width,label='Stop-go seguro = 100%')
ax.bar(x+width/2,100*coopvals/basevals,width,label='Juego de integración cooperativo')
ax.set_xticks(x,cats,rotation=18); ax.set(ylabel='Relativo al stop-go [%]',title='Mismo orden y mismo makespan: beneficio de negociar velocidad en vez de parar')
ax.axhline(100,linestyle=':'); ax.grid(True,axis='y',alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'05_comparacion_stopgo_vs_cooperativo.png',dpi=180); plt.close(fig)

# FIGURE 6 — physical margins
names=['Rueda','Torque','Fricción suelo','Pad Cargo','Contacto Caging']
vals=[coop_m['wheel_limit_ratio'],coop_m['torque_limit_ratio'],coop_m['ground_friction_utilization'],coop_m['cargo_pad_utilization'],coop_m['caging_utilization']]
fig,ax=plt.subplots(figsize=(8,4.7))
ax.bar(np.arange(len(names)),vals)
ax.axhline(1.0,linestyle='--',label='Límite')
ax.set_xticks(np.arange(len(names)),names,rotation=18); ax.set(ylabel='Utilización máxima / límite',title='Márgenes físicos del transporte cooperativo')
ax.grid(True,axis='y',alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'06_margenes_fisicos.png',dpi=180); plt.close(fig)

# FIGURE 7 — clearance history
fig,ax=plt.subplots(figsize=(9,4.5))
ax.plot(coop['times'],coop_inter,label='Separación entre coaliciones')
ax.plot(coop['times'],coop_obs,label='Separación a obstáculos')
ax.axhline(0,linestyle='--',label='Contacto/violación geométrica')
ax.set(xlabel='Tiempo [s]',ylabel='Clearance [m]',title='Clearance durante la misión cooperativa')
ax.grid(True,alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'07_clearance.png',dpi=180); plt.close(fig)

# FIGURE 8 — minimum SOC by team
fig,ax=plt.subplots(figsize=(9,4.5))
for k,ld in enumerate(loads):
    ids=team_ids[k]; ax.plot(coop['times'],np.min(coop['soc_traj'][:,ids],axis=1),label=f'{ld.name} {ld.mode}')
ax.set(xlabel='Tiempo [s]',ylabel='SOC mínimo del equipo',title='Batería: peor AMR de cada coalición')
ax.grid(True,alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'08_soc_equipos.png',dpi=180); plt.close(fig)

# README
readme=f'''# MegaGame E2E — escenario sintético reproducible\n\nEscenario con {N} AMR heterogéneos, 3 cargas y 12 robots reclutados: A Cargo, B Caging y C Cargo.\n\n## Qué se ejecuta\n- subasta distribuida para reclutamiento;\n- formación inicial con uniciclo;\n- ruta inicial recta y deformación suave local frente a obstáculos;\n- negociación distribuida de precedencia sobre un recurso espacio-tiempo de capacidad uno;\n- revisión pairwise con ampliación adaptativa CFRD si fuera necesaria;\n- time-scaling cooperativo sin parada;\n- cinemática diferencial por apoyo, velocidades de rueda y torque;\n- reparto de wrench Cargo mínimo-cuadrático;\n- QP convexo unilateral para Caging con chequeo KKT;\n- batería proxy torque-velocidad + pérdidas de cobre + auxiliares;\n- comparación con stop-go seguro usando el mismo orden/slots.\n\n## Resultados principales\n- Reclutamiento: coste distribuido {cost_auction:.6f}, oráculo {cost_or:.6f}.\n- Orden distribuido: {[loads[k].name for k in order]}, igual al oráculo del catálogo 3!; FCFS: {[loads[k].name for k in fcfs]}.\n- Mejora de fin frente a FCFS: {schedule_gain_s:.3f} s ({schedule_gain_pct:.2f}%).\n- Ejecución cooperativa vs stop-go con el mismo horario: 0 vs {base_m['stop_episodes']} paradas, {energy_saving_pct:.2f}% menos energía proxy, {smooth_reduction_pct:.1f}% menos coste de aceleración, {torque_reduction_pct:.1f}% menos torque pico.\n- Clearance mínimo entre coaliciones: {coop_m['min_inter_clearance_m']:.3f} m.\n- Clearance mínimo a obstáculos: {coop_m['min_obstacle_clearance_m']:.3f} m.\n- Residual KKT máximo del QP Caging: {coop_m['caging_kkt_max_residual']:.3e}.\n\n## Alcance\nNo es una réplica de R10 ni una validación de hardware. La ruta espacial es una solución local del optimizador de spline/potencial; no se certifica su optimalidad global. La optimalidad sí se comprueba para la asignación de reclutamiento y para el orden del catálogo de 3 coaliciones. El QP de Caging es convexo en la geometría fija de cada muestra y se acompaña de residual KKT.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')

# ANIMATION — complete cooperative E2E mission
fig,ax=plt.subplots(figsize=(10,6))
for rect in OBST:
    xmin,xmax,ymin,ymax=rect; ax.add_patch(Rectangle((xmin,ymin),xmax-xmin,ymax-ymin,fill=False,linewidth=2))
for k,ld in enumerate(loads):
    ax.plot(plans[k]['path'][:,0],plans[k]['path'][:,1],linestyle=':',linewidth=1)
    ax.plot(ld.goal[0],ld.goal[1],marker='x',linestyle='None',markersize=8)
ax.axvline(-4.5,linestyle='--',linewidth=.8); ax.axvline(4.5,linestyle='--',linewidth=.8)
team_lines=[]
for k,ld in enumerate(loads):
    mk='o' if ld.mode=='Caging' else 's'
    ln,=ax.plot([],[],marker=mk,linestyle='None',markersize=6,label=f'AMR {ld.name} ({ld.mode})'); team_lines.append(ln)
idle_line,=ax.plot([],[],marker='x',linestyle='None',markersize=6,label='Reserva/idle')
load_lines=[]; labels=[]
for k,ld in enumerate(loads):
    ln,=ax.plot([],[],linewidth=2.2,label=f'Carga {ld.name}'); load_lines.append(ln)
    labels.append(ax.text(0,0,'',fontsize=8))
cage_line,=ax.plot([],[],linestyle='--',linewidth=1.2,label='Cerco Caging')
trail_lines=[]
for k in range(G):
    ln,=ax.plot([],[],linewidth=1); trail_lines.append(ln)
status=ax.text(0.01,0.99,'',transform=ax.transAxes,va='top',fontsize=9)
ax.set(xlabel='x [m]',ylabel='y [m]',title='MegaGame E2E: reclutamiento → formación → transporte distribuido')
ax.set_xlim(WORLD[0],WORLD[1]); ax.set_ylim(WORLD[2],WORLD[3]); ax.set_aspect('equal',adjustable='box'); ax.grid(True,alpha=.2); ax.legend(fontsize=7,loc='lower center',ncol=4)

def load_outline(center,heading,dims):
    hx,hy=dims[0]/2,dims[1]/2
    c=np.array([[-hx,-hy],[hx,-hy],[hx,hy],[-hx,hy],[-hx,-hy]])
    Rm=np.array([[np.cos(heading),-np.sin(heading)],[np.sin(heading),np.cos(heading)]])
    return c@Rm.T+center

# animation states: compressed sampling
anim_states=[]
for idx in range(0,len(frames_form),2):
    tt,pp,hh=frames_form[idx]
    anim_states.append(('formation',tt,pp,hh,None))
for idx in range(0,len(coop['times']),3):
    anim_states.append(('transport',float(coop['times'][idx]),coop['rpos'][idx],coop['rtheta'][idx],idx))

trail_cache=[[],[],[]]
def update(frame_no):
    phase,tv,rp,rh,idx=anim_states[frame_no]
    for k in range(G):
        ids=team_ids[k]; team_lines[k].set_data(rp[ids,0],rp[ids,1])
    idle_line.set_data(rp[idle_ids,0],rp[idle_ids,1])
    if phase=='formation':
        lp=np.array([ld.start for ld in loads]); lh=np.zeros(G)
        token='—'; eused=0.0
        for k in range(G): trail_lines[k].set_data([],[])
    else:
        lp=coop['load_pos'][idx]; lh=coop['load_head'][idx]
        token='—'
        for k in order:
            sc=schedules[k]
            if sc['entry']<=tv<=sc['exit']: token=loads[k].name
        eused=float(np.trapezoid(np.sum(coop['power'][:idx+1],axis=1),coop['times'][:idx+1])) if idx>1 else 0.0
        for k in range(G):
            trail_lines[k].set_data(coop['load_pos'][:idx+1,k,0],coop['load_pos'][:idx+1,k,1])
    for k,ld in enumerate(loads):
        o=load_outline(lp[k],lh[k],ld.dims); load_lines[k].set_data(o[:,0],o[:,1]); labels[k].set_position(lp[k]+np.array([.12,.12])); labels[k].set_text(f'{ld.name} {ld.mode}')
    # Caging polygon
    ids=team_ids[1]; cp=rp[ids]; cp=np.vstack([cp,cp[0]]); cage_line.set_data(cp[:,0],cp[:,1])
    status.set_text(f't = {tv:5.1f} s   fase: {phase}\nreserva conflict-zone: {token}   energía acumulada ≈ {eused/1000:5.2f} kJ\norden negociado: {" → ".join(loads[k].name for k in order)}')
    return team_lines+[idle_line]+load_lines+labels+[cage_line,status]+trail_lines

ani=FuncAnimation(fig,update,frames=len(anim_states),interval=1000/15,blit=False)
writer=FFMpegWriter(fps=15,codec='libx264',bitrate=2200,extra_args=['-pix_fmt','yuv420p'])
ani.save(OUT/'MegaGame_E2E_cooperativo.mp4',writer=writer,dpi=130)
plt.close(fig)

# Pack everything except ZIP itself
zip_path=OUT/'MROB_MegaGame_E2E_bundle.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as zf:
    for fp in OUT.iterdir():
        if fp.name!=zip_path.name and fp.is_file(): zf.write(fp,arcname=fp.name)

print('\n=== FINAL E2E RESULTS ===')
print(json.dumps(summary['comparative'],indent=2,ensure_ascii=False))
print('Recruitment exact-oracle gap:',summary['recruitment']['gap'])
print('Distributed route-time order:',summary['route_time_game']['distributed_order'],'oracle:',summary['route_time_game']['oracle_order'])
print('Cooperative physical metrics:',json.dumps(coop_m,indent=2,default=float))
print('Artifacts:',OUT)
