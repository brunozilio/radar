"""Bounded check of six requested availability contrasts; no inference."""
from pathlib import Path
from datetime import datetime
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1]
E=R/'outputs/experimento-radar-ausencia-carreiro-20260922';B=R/'outputs/experimento-radar-mistura-atrasos-20260922';A=R/'outputs/analise-radar-ausencia-carreiro-20260922'
paths=[E/'predictions.csv',B/'prepared-inputs.npz',A/'availability-strata.csv',A/'artifact-hashes.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record=next(r for r in json.loads(paths[3].read_text()) if r['file']=='availability-strata.csv');assert sha(paths[2])==record['sha256']
rows=list(csv.DictReader(paths[0].open()));z=dict(np.load(paths[1]));lookup={float(t):i for i,t in enumerate(z['times'])}
ref={(r['phase'],r['profile'],int(r['horizon_h']),r['subset'],r['family'],r['carreiro_availability']):r for r in csv.DictReader(paths[2].open())};out=[]
for profile in ('A','B'):
 for h,category in ((6,'complete'),(6,'fully_missing'),(12,'fully_missing')):
  rr=[r for r in rows if r['phase']=='test' and r['profile']==profile and int(r['nominal_lead_h'])==h];ix=[lookup[datetime.fromisoformat(r['origin']).timestamp()] for r in rr]
  finite=np.isfinite(z['features_'+profile][ix,18:24]).sum(1);available=(finite==6) if category=='complete' else finite==0
  actual=np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in rr]);obs=available&(actual>=7)
  for family in ('mixed_profile_candidate','carreiro_missing_exposure'):
   pred=np.array([float(r[family+'_m']) if r[family+'_m'] else np.nan for r in rr]);paired=obs&np.isfinite(pred);e=pred[paired]-actual[paired]
   r=dict(profile=profile,horizon_h=h,carreiro_availability=category,family=family,observed_targets=int(obs.sum()),pairs=int(paired.sum()),failures=int(obs.sum()-paired.sum()),hits=int((abs(e)<=.5).sum()),mae_m=float(abs(e).mean()))
   saved=ref['test',profile,h,'level_ge_7m',family,category]
   for k in ('observed_targets','pairs','failures','hits'):assert r[k]==int(saved[k])
   assert abs(r['mae_m']-float(saved['mae_m']))<1e-12
   out.append(r)
(P/'availability-check.json').write_text(json.dumps(dict(passed=True,contrasts=6,metric_groups=12,results=out,input_sha256={str(p.relative_to(R)):sha(p) for p in paths}),indent=2)+'\n')
print('PASS 6 availability contrasts / 12 metric groups')
