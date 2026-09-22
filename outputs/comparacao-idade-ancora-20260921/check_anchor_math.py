"""Recompute changed anchor terms over six independently replayed origins."""
import csv, hashlib, json, math
from datetime import datetime
from pathlib import Path
import numpy as np
ROOT = Path('/Users/brunozilio/Documents/radar')
OUT = Path(__file__).resolve().parent
REPLAY = ROOT/'outputs/verificacao-integral-chuva-mucum-20260921'
BASE = ROOT/'outputs/mucum-atualizacao-15h-2026-09-21'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for artifact in json.loads((REPLAY/'artifact-hashes.json').read_text()):
    assert sha(REPLAY/artifact['path']) == artifact['sha256']
paths = [REPLAY/'recomputed-levels.csv', REPLAY/'computation.json',
         BASE/'telemetria-latencia.npz', BASE/'conferencia-balanco.json']
for d in (15, 30, 45):
    paths.append(ROOT/f'outputs/experimento-idade-ancora-{d}min-20260921/predictions.csv')
hashes = {str(p): sha(p) for p in paths}
old_inputs = json.loads(paths[1].read_text())['input_sha256']
for p in paths[2:4]: assert sha(p) == old_inputs[str(p)]
z = dict(np.load(paths[2])); a,b,c = json.loads(paths[3].read_text())['rating_parameters']
stage = lambda q: a*(q/1000)**b+c
lookup = {d: {(r['origin'], int(r['nominal_lead_h'])): r for r in csv.DictReader(paths[k+4].open())}
          for k,d in enumerate((15,30,45))}
results = []
for row in csv.DictReader(paths[0].open()):
    origin = datetime.fromisoformat(row['origin']).timestamp(); h = int(row['nominal_lead_h'])
    for minutes in (15,30,45):
        anchor = origin-minutes*60; j = int(np.searchsorted(z['times'], anchor))
        assert z['times'][j] == anchor
        ah = float(z['raw:86510000:H'][j]); aq = float(z['raw:86510000:Q'][j])
        # Independent linear interpolation using timestamps, not shared helper.
        start = float(row['past_reconstructed_q_m3_s']); end = float(row['origin_reconstructed_q_m3_s'])
        predicted_anchor = start+(end-start)*(anchor-(origin-3600))/3600
        residual = aq-predicted_anchor
        age_to_target = (origin+h*3600-anchor)/3600
        total = sum(float(row[key]) for key in ('julho77_routed_m3_s','carreiro_routed_m3_s','local_q_m3_s'))
        total += residual*math.exp(-age_to_target/6)
        value = stage(total)+ah-stage(aq) if total>=0 else None
        saved = lookup[minutes][row['origin'],h]['julho_levels_m']
        difference = value-float(saved) if value is not None and saved else None
        passed = abs(difference)<=1e-10 if difference is not None else value is None and not saved
        assert passed, (row['origin'],h,minutes,difference)
        results.append({'origin':row['origin'],'horizon_h':h,'delay_minutes':minutes,
                        'recomputed_m':value,'saved_m':saved,'difference_m':difference,'passed':passed})
assert len(results)==216
for p,v in hashes.items(): assert sha(Path(p))==v
with (OUT/'anchor-math-comparison.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
summary={'comparisons':len(results),'origins':6,'family':'julho_levels','delays_minutes':[15,30,45],
         'tolerance_m':1e-10,'max_absolute_difference_m':max(abs(r['difference_m']) for r in results if r['difference_m'] is not None),
         'passed':all(r['passed'] for r in results),'input_sha256':hashes,
         'scope':'Changed anchor interpolation, correction and elapsed-time decay independently recomputed over six previously fully replayed origins. Not a full re-simulation of every scenario row or publication audit.'}
(OUT/'anchor-math-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
