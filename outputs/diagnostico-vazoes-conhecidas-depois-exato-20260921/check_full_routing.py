"""NON-FORECAST validation over six independently simulated HGE origins."""
import csv,json,hashlib,math
from pathlib import Path
from datetime import datetime
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=Path(__file__).resolve().parent
REPLAY=ROOT/'outputs/verificacao-integral-chuva-mucum-20260921';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in json.loads((REPLAY/'artifact-hashes.json').read_text()):assert sha(REPLAY/x['path'])==x['sha256']
paths=[BASE/'dados-roteamento.npz',BASE/'roteamento-vazao-pesos.csv',BASE/'conferencia-balanco.json',
       REPLAY/'recomputed-levels.csv',REPLAY/'computation.json',
       ROOT/'outputs/experimento-proxy-carreiro-20260921/modeled-carreiro-inputs.npz',
       OUT/'reference-estimated-flows.npz',OUT/'exact-diagnostic-observations.npz',OUT/'reconstructions-not-forecasts.csv']
hashes={str(p):sha(p) for p in paths};old=json.loads(paths[4].read_text())['input_sha256']
for p in paths[:3]+[paths[5]]:assert sha(p)==old[str(p)]
d=dict(np.load(paths[0]));proxies=dict(np.load(paths[5]));est=dict(np.load(paths[6]));truth=dict(np.load(paths[7]));t=d['times']
for x in (proxies,est,truth):np.testing.assert_array_equal(x['times'],t)
a,b,c=json.loads(paths[2].read_text())['rating_parameters']
kr=list(csv.DictReader(paths[1].open()));kernels={s:[(int(r['lag_h']),float(r['weight'])) for r in kr if r['source']==name] for s,name in [('julho','14 de Julho'),('carreiro','Passo Carreiro')]}
past={'julho':d['julho']*1000,'carreiro':np.where(np.isfinite(d['carreiro']),d['carreiro']*1000,proxies['estimated_q_m3_s'][:,0])}
want={(r['origin'],int(r['nominal_lead_h'])):r for r in csv.DictReader(paths[8].open())}
def route(source,i,h,use_observed):
    terms=[]
    for lag,w in kernels[source]:
        if w==0:continue
        k=h-lag
        if k<0:q=past[source][i+k]
        else:q=truth[source][i+k] if use_observed else est[source][i,k]
        if not np.isfinite(q):return None
        terms.append(w*q)
    return sum(terms)
comparisons=[]
for row in csv.DictReader(paths[3].open()):
    origin=row['origin'];h=int(row['nominal_lead_h']);at=datetime.fromisoformat(origin).timestamp()
    i=int(np.searchsorted(t,at));assert t[i]==at
    for family in ('reference','observed_julho','observed_carreiro','observed_both'):
        jq=route('julho',i,h,family in ('observed_julho','observed_both'))
        cq=route('carreiro',i,h,family in ('observed_carreiro','observed_both'))
        if jq is None or cq is None:value=None
        else:
            q=jq+cq+float(row['local_q_m3_s'])+float(row['decayed_residual_m3_s'])
            value=a*(q/1000)**b+c+float(row['anchor_offset_m']) if q>=0 else None
        saved=want[origin,h][family+'_m'];difference=value-float(saved) if value is not None and saved else None
        passed=abs(difference)<=1e-8 if difference is not None else value is None and not saved
        assert passed,(origin,h,family,value,saved)
        comparisons.append(dict(origin=origin,horizon_h=h,family=family,recomputed_m=value,saved_m=saved,difference_m=difference,passed=passed))
assert len(comparisons)==288
with (OUT/'full-routing-comparison.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
numeric=[abs(r['difference_m']) for r in comparisons if r['difference_m'] is not None]
summary=dict(passed=True,comparisons=288,finite_comparisons=len(numeric),matching_unavailable=288-len(numeric),origins=6,
             max_absolute_difference_m=max(numeric),input_sha256=hashes,
             scope='Independent full routing with exactdiagnostic and estimatedfutureflows; localHGE/residual components from prior independent replay. No baselinelevel inversion. Not freshHGE simulation on all23538rows.',
             valid_forecast=False,eligible_for_goal=False)
for p,digest in hashes.items():assert sha(Path(p))==digest
(OUT/'full-routing-verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
