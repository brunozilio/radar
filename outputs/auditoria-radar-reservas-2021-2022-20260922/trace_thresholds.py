"""Explain frozen-tree routing sensitivity without changing or refitting any model."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib
import numpy as np
import joblib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];R=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922';M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922';report=json.loads((P/'verification.json').read_text());protocol=json.loads((ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922/protocol.json').read_text());models={(r['family'],r['horizon_h']):r for r in protocol['model_records']};data={};loaded={};catalog={(int(r['year']),int(r['column'])):r['name'] for r in csv.DictReader((R/'feature-catalog.csv').open())};traces=[]
from datetime import datetime

def path(nodes,x):
 p=[0]
 while not nodes[p[-1]]['is_leaf']:
  n=nodes[p[-1]];assert not n['is_categorical'];value=x[int(n['feature_idx'])];left=bool(n['missing_go_to_left']) if np.isnan(value) else value<=n['num_threshold'];p.append(int(n['left'] if left else n['right']))
 return p,float(nodes[p[-1]]['value'])

for case in report['threshold_sensitivity_cases']:
 year=case['year'];k=case['family'],case['horizon_h']
 if year not in data:data[year]=(dict(np.load(M/str(year)/'features.npz')),dict(np.load(R/f'reconstructed-{year}.npz')))
 a,b=data[year];i=int(np.flatnonzero(a['times']==datetime.fromisoformat(case['origin']).timestamp())[0]);x=a['features'][i];y=b['features'][i]
 if k not in loaded:
  ref=models[k];p=ROOT/ref['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'];loaded[k]=joblib.load(p)
 m=loaded[k];total=0.;changedtrees=0
 for iteration,trees in enumerate(m._predictors):
  assert len(trees)==1;nodes=trees[0].nodes;pa,va=path(nodes,x);pb,vb=path(nodes,y);total+=vb-va
  if pa==pb:continue
  changedtrees+=1;kdiff=next(j for j in range(min(len(pa),len(pb))) if pa[j]!=pb[j]);nodeindex=pa[kdiff-1];node=nodes[nodeindex];col=int(node['feature_idx']);threshold=float(node['num_threshold'])
  traces.append(dict(year=year,family=case['family'],horizon_h=case['horizon_h'],origin=case['origin'],iteration=iteration,node=nodeindex,column=col,feature=catalog[year,col],original_value=float(x[col]),reconstructed_value=float(y[col]),value_difference=float(y[col]-x[col]),threshold=threshold,original_goes_left=bool(x[col]<=threshold),reconstructed_goes_left=bool(y[col]<=threshold),original_leaf=pa[-1],reconstructed_leaf=pb[-1],leaf_contribution_difference=vb-va))
 assert abs(total-case['difference_m'])<1e-12,(case,total)
 assert changedtrees>0
with (P/'tree-threshold-crossings.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(traces[0]));w.writeheader();w.writerows(traces)
result=dict(cases=len(report['threshold_sensitivity_cases']),all_cases_explained_by_frozen_numeric_tree_threshold_crossings=True,all_prediction_differences_reproduced_by_sum_of_leaf_differences_tolerance=1e-12,tree_crossings=len(traces),feature_counts=dict(Counter(r['feature'] for r in traces)),largest_prediction_difference_case=max(report['threshold_sensitivity_cases'],key=lambda r:abs(r['difference_m'])),limits='Diagnostic only; original frozen matrices/predictions preserved. No rounding or normalization introduced.')
(P/'tree-threshold-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
