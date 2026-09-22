"""Outcome strata use the declared training-weight boundaries, not model choice."""
import csv,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-peso-cheia-7m-20260922'
FAMILIES=('profile_A_control','profile_B_control','mixed_profile_candidate','flood_weight_7m')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    for item in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/item['file'])==item['sha256']
    groups=defaultdict(list)
    for r in csv.DictReader((SOURCE/'predictions.csv').open()):groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
    ref={(r['phase'],r['profile'],int(r['horizon_h']),r['family'],r['subset']):r for r in csv.DictReader((SOURCE/'evaluation.csv').open()) if r['population']=='full_schedule'}
    metrics=[];changes=[];checks=0
    for (phase,profile,h),rows in sorted(groups.items()):
        actual=np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in rows])
        labels=np.where(~np.isfinite(actual),'unknown',np.where(actual<7,'below_7m',np.where(actual<9,'7_to_9m','ge_9m')))
        pred={f:np.array([float(r[f+'_m']) if r[f+'_m'] else np.nan for r in rows]) for f in FAMILIES}
        for family,values in pred.items():
            start=len(metrics)
            for band in ('below_7m','7_to_9m','ge_9m','unknown'):
                selected=labels==band;observed=selected&np.isfinite(actual);paired=observed&np.isfinite(values)
                error=values[paired]-actual[paired];ae=abs(error)
                metrics.append(dict(phase=phase,profile=profile,horizon_h=h,family=family,observed_level_band=band,scheduled_rows=int(selected.sum()),
                    unknown_truth=int((selected&~np.isfinite(actual)).sum()),observed_targets=int(observed.sum()),pairs=int(paired.sum()),failures=int(observed.sum()-paired.sum()),hits=int((ae<=.5).sum()),
                    sum_abs_error_m=float(ae.sum()),mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(error) else None,max_abs_m=float(ae.max()) if len(ae) else None))
            for subset,bands in (('all',('below_7m','7_to_9m','ge_9m','unknown')),('level_ge_7m',('7_to_9m','ge_9m','unknown'))):
                selected=[r for r in metrics[start:] if r['observed_level_band'] in bands];expected=ref[phase,profile,h,family,subset]
                for field in ('observed_targets','pairs','failures','hits'):
                    assert sum(r[field] for r in selected)==int(expected[field]);checks+=1
                assert sum(r['unknown_truth'] for r in selected)==int(expected['missing_truth']);checks+=1
                if int(expected['pairs']):
                    np.testing.assert_allclose(sum(r['sum_abs_error_m'] for r in selected)/int(expected['pairs']),float(expected['mae_m']),rtol=0,atol=1e-12);checks+=1
        before,after=pred['mixed_profile_candidate'],pred['flood_weight_7m'];both=np.isfinite(actual)&np.isfinite(before)&np.isfinite(after)
        oldhit=abs(before-actual)<=.5;newhit=abs(after-actual)<=.5
        for band in ('below_7m','7_to_9m','ge_9m','unknown'):
            m=both&(labels==band)
            changes.append(dict(phase=phase,profile=profile,horizon_h=h,observed_level_band=band,pairs=int(m.sum()),gained=int((m&~oldhit&newhit).sum()),lost=int((m&oldhit&~newhit).sum()),net_hits=int((m&newhit).sum()-(m&oldhit).sum())))
    assert len(metrics)==768 and len(changes)==192
    save('level-band-metrics.csv',metrics);save('level-band-transitions.csv',changes)
    (OUT/'level-band-analysis.json').write_text(json.dumps(dict(metrics=len(metrics),transitions=len(changes),reconciliations=checks,source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),goal_achieved=False),indent=2)+'\n')
    lookup={(r['phase'],r['profile'],r['horizon_h'],r['family'],r['observed_level_band']):r for r in metrics}
    with (OUT/'README.md').open('a') as f:
        f.write('\n## Faixas de nível observado\n\nAs fronteiras são as mesmas do protocolo de pesos. Alvos desconhecidos ficam em grupo próprio. As768métricas e192transições mantêm todos os horizontes e recompõem os totais original/all e>=7m. Não são uma seleção de modelo por nível futuro.\n\n| Perfil | h | Faixa | Acertos peso9 → peso7 / observados | MAE peso9 → peso7 |\n|---|---:|---|---:|---:|\n')
        for r in metrics:
            if r['phase']=='test' and r['horizon_h'] in (1,6,12) and r['family']=='flood_weight_7m' and r['observed_level_band']!='unknown':
                old=lookup[r['phase'],r['profile'],r['horizon_h'],'mixed_profile_candidate',r['observed_level_band']]
                fmt=lambda v:f'{v:.4f}' if v is not None else '—'
                f.write(f"| {r['profile']} | {r['horizon_h']} | {r['observed_level_band']} | {old['hits']} → {r['hits']} / {r['observed_targets']} | {fmt(old['mae_m'])} → {fmt(r['mae_m'])} |\n")
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(dict(metrics=len(metrics),transitions=len(changes),checks=checks)))

if __name__=='__main__':main()
