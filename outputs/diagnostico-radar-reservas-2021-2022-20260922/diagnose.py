"""Exploratory error direction audit after the fixed challenge; no model changes."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,math
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
D=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922';M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(P/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
for h in json.loads((D/'artifact-hashes.json').read_text()):assert sha(D/h['file'])==h['sha256']
assert not (P/'diagnostic-plan.json').exists()
dump('diagnostic-plan.json',dict(registered_at_utc=datetime.now(timezone.utc).isoformat(),
    status='Exploratory after first reserved evaluation; not a new holdout or test of a new model.',
    scope='All pairs, separate2021/2022, h6/h12 and all/high targets. Describe hit transitions and bias by realized movement and observed recent slope; never select/refit/promote.',
    future_motion='target-base >=0.50m rise, <=-0.50m fall, else stable; diagnostic label using future truth, never a forecast input.',
    recent_motion='Muçum observed dH1 input(column2) >=0.05m/h rising, <=-0.05 falling, otherwise stable; missing gets separate unknown group.',
    prediction_sha256=sha(D/'predictions.csv')))
raw=list(csv.DictReader((D/'predictions.csv').open()));index={};hashes={str((D/'predictions.csv').relative_to(ROOT)):sha(D/'predictions.csv')}
for y in (2021,2022):
    p=M/str(y)/'features.npz';a=np.load(p);hashes[str(p.relative_to(ROOT))]=sha(p)
    index[y]={float(t):float(f[2]) for t,f in zip(a['times'],a['features'])}
rows=[]
for r in raw:
    if r['nominal_lead_h'] not in ('6','12') or not all(r[k] for k in ('base_m','actual_m','control120_m','candidate120_plus2020_m')):continue
    year=int(r['year']);actual=float(r['actual_m']);base=float(r['base_m']);control=float(r['control120_m']);candidate=float(r['candidate120_plus2020_m'])
    b=control-actual;c=candidate-actual;delta=actual-base;slope=index[year][datetime.fromisoformat(r['origin']).timestamp()]
    future='rise' if delta>=.5 else 'fall' if delta<=-.5 else 'stable'
    recent='unknown' if not math.isfinite(slope) else 'rise' if slope>=.05 else 'fall' if slope<=-.05 else 'stable'
    transition=('hit' if abs(b)<=.5 else 'miss')+'_to_'+('hit' if abs(c)<=.5 else 'miss')
    rows.append(dict(year=year,horizon_h=int(r['nominal_lead_h']),origin=r['origin'],target_time=r['target_time'],base_m=base,actual_m=actual,
        control_error_m=b,candidate_error_m=c,future_motion=future,recent_motion=recent,hit_transition=transition))
summary=[]
for y in (2021,2022):
    for h in (6,12):
        for subset in ('all','level_ge_7m'):
            scope=[r for r in rows if r['year']==y and r['horizon_h']==h and (subset=='all' or r['actual_m']>=7)]
            for axis in ('future_motion','recent_motion'):
                for label in ('rise','stable','fall','unknown'):
                    rr=[r for r in scope if r[axis]==label];n=len(rr)
                    summary.append(dict(year=y,horizon_h=h,subset=subset,axis=axis,category=label,pairs=n,
                        control_hits=sum(abs(r['control_error_m'])<=.5 for r in rr),candidate_hits=sum(abs(r['candidate_error_m'])<=.5 for r in rr),
                        gained_hits=sum(r['hit_transition']=='miss_to_hit' for r in rr),lost_hits=sum(r['hit_transition']=='hit_to_miss' for r in rr),
                        control_bias=sum(r['control_error_m'] for r in rr)/n if n else None,candidate_bias=sum(r['candidate_error_m'] for r in rr)/n if n else None,
                        control_mae=sum(abs(r['control_error_m']) for r in rr)/n if n else None,candidate_mae=sum(abs(r['candidate_error_m']) for r in rr)/n if n else None))
for name,rr in [('paired-error-directions.csv',rows),('strata.csv',summary)]:
    with (P/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
result=dict(input_sha256=hashes,diagnostic_pairs=len(rows),strata=len(summary),model_access=False,training=False,promotion=False,
    limitations='Exploratory partitions after evaluation; correlated hours, no causal attribution or official independent-event inference. No failures removed from primary score: this direction audit is paired only.')
dump('diagnostic.json',result)
dump('artifact-hashes.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(P.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'])
print(json.dumps([r for r in summary if r['year']==2022 and r['horizon_h']==12 and r['subset']=='level_ge_7m' and r['axis']=='future_motion'],indent=2))
