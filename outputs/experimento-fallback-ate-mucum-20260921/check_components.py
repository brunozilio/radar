"""Full-routing check on six origins using independently replayed HGE components."""
import csv,json,hashlib,math
from pathlib import Path
from datetime import datetime
import numpy as np
ROOT=Path('/Users/brunozilio/Documents/radar');OUT=Path(__file__).resolve().parent
BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
REPLAY=ROOT/'outputs/verificacao-integral-chuva-mucum-20260921'
UP=ROOT/'outputs/experimento-fallback-componentes-20260921'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in json.loads((REPLAY/'artifact-hashes.json').read_text()):assert sha(REPLAY/x['path'])==x['sha256']
paths=[BASE/'dados-roteamento.npz',BASE/'roteamento-vazao-pesos.csv',BASE/'conferencia-balanco.json',
       REPLAY/'recomputed-levels.csv',REPLAY/'computation.json',UP/'predictions.csv',OUT/'predictions.csv']
hashes={str(p):sha(p) for p in paths};old=json.loads(paths[4].read_text())['input_sha256']
for p in paths[:3]:assert sha(p)==old[str(p)]
d=dict(np.load(paths[0]));a,b,c=json.loads(paths[2].read_text())['rating_parameters']
kernel=[(int(r['lag_h']),float(r['weight'])) for r in csv.DictReader(paths[1].open()) if r['source']=='14 de Julho']
flows={(r['origin'],int(r['lead_h'])):r for r in csv.DictReader(paths[5].open()) if r['phase']=='test'}
want={(r['origin'],int(r['nominal_lead_h'])):r for r in csv.DictReader(paths[6].open())}
comparisons=[]
for r in csv.DictReader(paths[3].open()):
    origin=r['origin'];h=int(r['nominal_lead_h']);at=datetime.fromisoformat(origin).timestamp()
    i=int(np.searchsorted(d['times'],at));assert d['times'][i]==at
    for family,column in [('reference','reference_m3_s'),('candidate','forecast_m3_s')]:
        terms=[]
        for lag,w in kernel:
            if w==0:continue
            k=h-lag
            q=float(flows[origin,k][column]) if k>=0 else float(d['julho'][i+k]*1000)
            terms.append(w*q)
        qtotal=sum(terms)+sum(float(r[k]) for k in ('carreiro_routed_m3_s','local_q_m3_s','decayed_residual_m3_s'))
        assert qtotal>=0
        level=a*(qtotal/1000)**b+c+float(r['anchor_offset_m'])
        expected=float(want[origin,h][family+'_m']);difference=level-expected
        assert abs(difference)<1e-8
        comparisons.append(dict(origin=origin,horizon_h=h,family=family,recomputed_m=level,saved_m=expected,difference_m=difference))
with (OUT/'component-comparison.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
assert len(comparisons)==144
for p,digest in hashes.items():assert sha(Path(p))==digest
summary=dict(comparisons=144,origins=6,affected_origins=3,max_absolute_difference_m=max(abs(r['difference_m']) for r in comparisons),
             tolerance_m=1e-8,passed=True,input_sha256=hashes,
             method='Recompute fullJuly routing from source history and frozenfuturepredictions. Sum preserved independently replayedCarreiro,HGE and residual components; no inversion of baseline level or delta helper.',
             limitation='Six origin audit with previously independently simulated components; not fresh fullHGE simulation of all23538rows or historic availability proof.')
(OUT/'component-verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
