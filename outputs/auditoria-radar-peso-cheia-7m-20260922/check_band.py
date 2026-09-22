"""Four requested level-band groups, recomputed without inference."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1];E=R/'outputs/experimento-radar-peso-cheia-7m-20260922';A=R/'outputs/analise-radar-peso-cheia-7m-20260922'
paths=[E/'predictions.csv',A/'level-band-metrics.csv',A/'artifact-hashes.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads(paths[2].read_text());assert next(r['sha256'] for r in manifest if r['file']=='level-band-metrics.csv')==sha(paths[1])
rows=list(csv.DictReader(paths[0].open()));reference=list(csv.DictReader(paths[1].open()));out=[]
for profile in ('A','B'):
 selected=[r for r in rows if r['phase']=='test' and r['profile']==profile and r['nominal_lead_h']=='12' and r['actual_m'] and 7<=float(r['actual_m'])<9]
 for family in ('mixed_profile_candidate','flood_weight_7m'):
  paired=[r for r in selected if r[family+'_m']];error=np.array([float(r[family+'_m'])-float(r['actual_m']) for r in paired]);ae=abs(error)
  r=dict(phase='test',profile=profile,horizon_h=12,family=family,observed_level_band='7_to_9m',scheduled_rows=len(selected),unknown_truth=0,observed_targets=len(selected),pairs=len(paired),failures=len(selected)-len(paired),hits=int((ae<=.5).sum()),sum_abs_error_m=float(ae.sum()),mae_m=float(ae.mean()),bias_m=float(error.mean()),max_abs_m=float(ae.max()))
  saved=next(s for s in reference if all(s[k]==str(r[k]) for k in ('phase','profile','horizon_h','family','observed_level_band')))
  for k,v in r.items():assert saved[k]==v if isinstance(v,str) else abs(float(saved[k])-v)<1e-12
  out.append(r)
(P/'band-check.json').write_text(json.dumps(dict(passed=True,groups=4,results=out,input_sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Only test h12 [7,9), old mixed/candidate, profiles A/B. No inference or full secondary-analysis audit.'),indent=2)+'\n')
print('PASS 4 groups',[(r['profile'],r['family'],r['hits'],r['observed_targets']) for r in out])
