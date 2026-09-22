"""Independently reconstruct preregistered training masks/weights; no model execution."""
import csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];sources={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def ep(v):return datetime.fromisoformat(v).timestamp()
def iso(v):return datetime.fromtimestamp(v,timezone(timedelta(hours=-3))).isoformat()
def shift(a,h):return np.r_[a[h:],np.full(h,np.nan)]
def check(k,v):checks.append(dict(check=k,passed=bool(v)));assert v,k
def save(n,r):
 with (OUT/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
O=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));N=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2020-20260921/features.npz')));R=dict(np.load(use(ROOT/'outputs/experimento-radar-observado-120-20260921/training-masks.npz')));reftrain=list(csv.DictReader(use(ROOT/'outputs/experimento-radar-observado-120-20260921/training.csv').open()));spec=json.loads(use(ROOT/'docs/radar-2020-augmentation-protocol.json').read_text());reservation=json.loads(use(ROOT/'docs/radar-historical-evaluation-reservation.json').read_text());use(ROOT/'scripts/hydro_radar_2020_augmentation.py')
qi=list(csv.DictReader(use(ROOT/'outputs/radar-matriz-observada-2020-20260921/qi-origin-diagnostics.csv').open()));zeros=np.array([r['uses_any_zero']=='True' for r in qi]);t=O['times'];nt=N['times'];check('QI origins aligned',np.array_equal(nt,[ep(r['origin']) for r in qi]));check('2020and2025_26 only',all(datetime.fromtimestamp(x,timezone.utc).year==2020 for x in nt) and all(datetime.fromtimestamp(x,timezone.utc).year in [2025,2026] for x in t));check('2020chronologicallyfirst',max(nt)<min(t))
for i,w in enumerate(reservation['windows']):
 lo=ep(w['start_inclusive_local']);hi=ep(w['stop_exclusive_local']);check(f'reservation{i}zero_inputs',not (((nt>=lo)&(nt<hi)).any() or ((t>=lo)&(t<hi)).any()))
start=ep('2025-10-01T00:00:00-03:00');end=ep('2026-07-01T00:00:00-03:00');boundary=ep('2020-07-21T00:00:00-03:00');members={};rows=[];zero_rows=[];expected=[]
for h in range(1,13):
 y=shift(O['truth'],h);ny=shift(N['truth'],h);delta=y-O['base'];ndelta=ny-N['base'];newmask=np.isfinite(N['base'])&np.isfinite(ny)&(nt+h*3600<boundary);members[f'new_h{h}']=newmask;check(f'zeroQIintersectionh{h}',not (newmask&zeros).any());nw=1+2*(abs(ndelta[newmask])>=1)+2*(ny[newmask]>=9)
 first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
 for phase in ['validation','test']:
  mask=np.isfinite(O['base'])&np.isfinite(y)&(first if phase=='validation' else first|second);members[f'{phase}_original_h{h}']=mask;check(f'frozenoriginalmask {phase}h{h}',np.array_equal(mask,R[f'{phase}_h{h}']));ow=1+2*(abs(delta[mask])>=1)+2*(y[mask]>=9);info=next(r for r in reftrain if r['phase']==phase and int(r['horizon_h'])==h);check(f'traincount {phase}h{h}',mask.sum()==int(info['n']));check(f'cutoff {phase}h{h}',np.all(nt[newmask]+h*3600<ep(info['cutoff_exclusive'])) and np.all(t[mask]+h*3600<ep(info['cutoff_exclusive'])))
  rr=dict(phase=phase,horizon_h=h,original_n=int(mask.sum()),added_n=int(newmask.sum()),n=int(mask.sum()+newmask.sum()),original_weight=int(ow.sum()),added_weight=int(nw.sum()),weight_sum=int(ow.sum()+nw.sum()),weight_fraction_2020=float(nw.sum()/(nw.sum()+ow.sum())),original_targets_ge_7m=int((y[mask]>=7).sum()),added_targets_ge_7m=int((ny[newmask]>=7).sum()),added_targets_ge_9m=int((ny[newmask]>=9).sum()),added_abs_response_ge_1m=int((abs(ndelta[newmask])>=1).sum()),added_response_min_m=float(ndelta[newmask].min()),added_response_max_m=float(ndelta[newmask].max()),zero_qi_admitted=int((newmask&zeros).sum()),latest_training_target=iso((t[mask]+h*3600).max()),latest_added_target=iso((nt[newmask]+h*3600).max()),cutoff_exclusive=info['cutoff_exclusive'],leaf_nodes=int(info['leaf_nodes']),loss=info['loss']);rows.append(rr)
 for i in np.where(newmask)[0]:expected.append(dict(horizon_h=h,origin=iso(nt[i]),target=iso(nt[i]+h*3600),base_m=float(N['base'][i]),actual_m=float(ny[i]),weight=int(1+2*(abs(ndelta[i])>=1)+2*(ny[i]>=9))))
 for i in np.where(zeros)[0]:zero_rows.append(dict(horizon_h=h,origin=iso(nt[i]),base_m=float(N['base'][i]) if np.isfinite(N['base'][i]) else None,target_m=float(ny[i]) if np.isfinite(ny[i]) else None,eligible=bool(newmask[i])))
np.savez_compressed(OUT/'expected-training-masks.npz',**members);save('expected-training.csv',rows);save('added2020-membership.csv',expected);save('zero-qi-eligibility.csv',zero_rows)
finite_zero=np.where(zeros&np.isfinite(N['base']))[0];check('zero23origins',zeros.sum()==23);check('zero22base_missing',np.sum(zeros&~np.isfinite(N['base']))==22);check('onlyonefinitebasezero',len(finite_zero)==1 and iso(nt[finite_zero[0]])=='2020-07-08T05:00:00-03:00' and N['base'][finite_zero[0]]==19.02)
result=dict(passed=True,checks=checks,training=rows,zero_qi_origins=23,zero_qi_base_missing=22,only_finite_base_zero_origin='2020-07-08T05:00:00-03:00',only_finite_base_m=19.02,eligible_zero_qi_pairs_all_horizons=0,reserved_windows_used=False,added_years=[2020],original_years=[2025,2026],source_sha256=sources,limits='Eligibility alone excludes allzeroQIorigins; no new zero rejection mask. Peak QCoutage remains. No models read or fit; documentary reservation metadata read, not2021/22data.')
(OUT/'membership-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,checks=len(checks),zeroQIeligible=0,training=[r for r in rows if r['horizon_h'] in [1,6,12]]),indent=2))
