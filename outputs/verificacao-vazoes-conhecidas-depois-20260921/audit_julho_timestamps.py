from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
from bisect import bisect_right
import json,csv,hashlib,math
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=ROOT/'outputs/verificacao-vazoes-conhecidas-depois-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21';RUN=ROOT/'outputs/diagnostico-vazoes-conhecidas-depois-20260921'
def ep(s):
 d=datetime.fromisoformat(s);return (d if d.tzinfo else d.replace(tzinfo=timezone(timedelta(hours=-3)))).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),timezone(timedelta(hours=-3))).isoformat()
d=dict(np.load(BASE/'dados-roteamento.npz'));t=d['times'];z=dict(np.load(BASE/'telemetria-latencia.npz'));ix=np.searchsorted(z['times'],t)
assert np.array_equal(d['julho'],z['raw:julho:Q'][ix]/1000,equal_nan=True)
m=json.loads((ROOT/'outputs/auditoria-consistencia-componentes-ceran-20260921/source-manifest.json').read_text());source={};hashes={}
for item in m:
 p=ROOT/item['path'];hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();assert hashes[str(p)]==item['sha256']
 for line,r in enumerate(csv.DictReader(p.open(),delimiter=';'),2):
  if r['id_reservatorio']=='JIUHQJ':
   stamp=ep(r['din_instante']);assert stamp not in source
   try:q=float(r['val_vazaodefluente'])
   except ValueError:q=np.nan
   source[stamp]={'q':q,'source_file':str(p),'line':line,'time_original':r['din_instante']}
st=sorted(source);rows=list(csv.DictReader((RUN/'reconstructions-not-forecasts.csv').open()))
kernels=[(int(r['lag_h']),float(r['weight'])) for r in csv.DictReader((BASE/'roteamento-vazao-pesos.csv').open()) if r['source']=='14 de Julho']
required=Counter();rowrequired={}
for r in rows:
 origin=ep(r['origin']);h=int(r['nominal_lead_h']);tt=[origin+(h-l)*3600 for l,w in kernels if w!=0 and h-l>=0]
 rowrequired[r['origin'],h]=tt;required.update(tt)
audit=[];classmap={}
for at,n in sorted(required.items()):
 i=int(np.searchsorted(t,at));assert t[i]==at;gridq=float(d['julho'][i]*1000);exact=source.get(at);bi=bisect_right(st,at)-1;prev=source[st[bi]] if bi>=0 else None
 if exact is None:label='no_exact_ons_timestamp'
 elif not math.isfinite(exact['q']):label='exact_ons_q_missing'
 elif not math.isfinite(gridq):label='grid_q_missing'
 elif abs(exact['q']-gridq)<=1e-8:label='exact_ons_timestamp_and_q_match'
 else:label='exact_ons_timestamp_q_differs'
 age=(at-st[bi])/60 if bi>=0 else None
 carried_match=exact is None and prev is not None and math.isfinite(gridq) and math.isfinite(prev['q']) and abs(gridq-prev['q'])<=1e-8
 classmap[at]=label
 audit.append({'required_time':iso(at),'diagnostic_term_occurrences':n,'classification':label,'grid_q_m3_s':gridq if math.isfinite(gridq) else None,'exact_ons_q_m3_s':exact['q'] if exact is not None and math.isfinite(exact['q']) else None,'latest_ons_time_original':prev['time_original'] if prev else None,'age_latest_ons_minutes':age,'latest_ons_q_m3_s':prev['q'] if prev and math.isfinite(prev['q']) else None,'matches_older_ons_value_without_exact_timestamp':carried_match,'source_file':(exact or prev)['source_file'] if exact or prev else None,'source_line':(exact or prev)['line'] if exact or prev else None})
with (OUT/'julho-original-timestamp-audit.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
affectedrows=Counter()
for (o,h),tt in rowrequired.items():
 for label in set(classmap[x] for x in tt):affectedrows[label]+=1
summary={'classification_counts_distinct_timestamps':dict(Counter(x['classification'] for x in audit)),'classification_counts_required_terms':dict(sum((Counter({x['classification']:x['diagnostic_term_occurrences']}) for x in audit),Counter())),'rows_with_at_least_one_case':dict(affectedrows),'required_unique_timestamps':len(required),'required_terms':sum(required.values()),'no_exact_matches_older_ons':sum(x['matches_older_ons_value_without_exact_timestamp'] for x in audit),'no_exact_age_distribution_minutes':dict(Counter(str(x['age_latest_ons_minutes']) for x in audit if x['classification']=='no_exact_ons_timestamp')),'source_sha256':hashes,'d_julho_identical_raw_asof_grid':True,'interpretation':'No exact timestamp is not a certified measured observation. Older-value matches show consistency with carry, not unique source provenance. Timestamp-equal value differences remain source/version ambiguity. Original timestamp strings unchanged, no23:59 normalization.'}
(OUT/'julho-original-timestamp-summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2))

