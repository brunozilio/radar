"""Frozen 120-column reconstruction and prior rainfall audit input-hash binding."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];B=W/'outputs/mucum-atualizacao-15h-2026-09-21';E=W/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921';P=W/'outputs/auditoria-latencias-chuva-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def back(a,n):return np.r_[np.full(n,np.nan),a[:-n]] if n else a.copy()
z=dict(np.load(B/'telemetria-latencia.npz'));D=dict(np.load(E/'features.npz'));cols=[];names=[];phase=np.arange(0,len(z['times']),4)
for code in ['86510000','86472000','86472600','86500000']:
 v=z[code+':H'];cols.append(v);names.append(code+':H')
 for h in [.5,1,2,4,8]:cols.append((v-back(v,int(h*4)))/h);names.append(code+f':dH{h}')
for plant in ['julho','monte','castro']:
 q=z[plant+':Q']/1000;p=np.maximum(q,0)**.6;cols.extend([p,q,z[plant+':I']/1000]);names.extend([plant+':Q06',plant+':Q',plant+':I'])
 for h in [1,2,4,8]:cols.append((p-back(p,h*4))/h);names.append(plant+f':dQ{h}')
for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
 for h in [1,3,6,12,24,48]:cols.extend([z[group+f':P{h}'],z[group+f':C{h}']]);names.extend([group+f':P{h}',group+f':C{h}'])
 for h in [3,6,12]:cols.append(back(z[group+':P3'],h*4));names.append(group+f':P3lag{h}')
F=np.column_stack(cols)[phase];assert F.shape==D['features'][:,:120].shape and np.array_equal(F,D['features'][:,:120],equal_nan=True);assert np.array_equal(z['times'][phase],D['times']);assert np.array_equal(z['86510000:H'][phase],D['base'],equal_nan=True);assert np.array_equal(z['raw:86510000:H'][phase],D['truth'],equal_nan=True)
prior=json.loads((P/'source-manifest.json').read_text());bindings=[]
for path,m in prior.items():
 if path.endswith('.py'):continue
 bindings.append({'path':path,'sha256':sha(W/path),'expected':m['sha256'],'passed':sha(W/path)==m['sha256']})
assert all(x['passed'] for x in bindings)
pc=json.loads((P/'regional-comparison.json').read_text());assert pc['all_exact'] and pc['compared_fields']==60 and pc['total_mismatches_gt1e10']==0
sources={str(p.relative_to(W)):sha(p) for p in [B/'telemetria-latencia.npz',E/'features.npz',P/'source-manifest.json',P/'regional-comparison.json',P/'latencies.json']}
out={'passed':True,'frozen_observed_cells':F.size,'rows':len(D['times']),'columns':120,'features_exact':True,'base_truth_times_exact':True,'prior_rainfall_source_hashes_verified':len(bindings),'prior_rainfall_comparison_fields':60,'prior_rainfall_rows_per_field':pc['rows_per_field'],'prior_rainfall_exact':pc['all_exact'],'source_sha256':sources,'bindings':bindings,'method':'Manually reconstructed the120observed columns from frozen telemetry without importing helpers. Bound prior rainfall integration audit to unchanged input hashes. Did not rerun interval integration here.'}
(R/'frozen-observed-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['frozen_observed_cells'],len(bindings),'passed')
