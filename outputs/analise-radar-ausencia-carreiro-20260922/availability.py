"""Separate real availability groups after the frozen masking experiment."""
import csv,hashlib,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/experimento-radar-ausencia-carreiro-20260922'
PARENT=ROOT/'outputs/experimento-radar-mistura-atrasos-20260922'
FAMILIES=('profile_A_control','profile_B_control','mixed_profile_candidate','carreiro_missing_exposure')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    for item in json.loads((SOURCE/'artifact-hashes.json').read_text()):assert sha(SOURCE/item['file'])==item['sha256']
    data=dict(np.load(PARENT/'prepared-inputs.npz'))
    groups=defaultdict(list)
    for r in csv.DictReader((SOURCE/'predictions.csv').open()):groups[r['phase'],r['profile'],int(r['nominal_lead_h'])].append(r)
    ref={(r['phase'],r['profile'],int(r['horizon_h']),r['family'],r['subset']):r for r in csv.DictReader((SOURCE/'evaluation.csv').open()) if r['population']=='full_schedule'}
    metrics=[];transitions=[];checks=0
    for (phase,profile,h),rows in sorted(groups.items()):
        times=np.array([datetime.fromisoformat(r['origin']).timestamp() for r in rows]);ix=np.searchsorted(data['times'],times)
        np.testing.assert_array_equal(data['times'][ix],times)
        n=np.isfinite(data['features_'+profile][ix,18:24]).sum(axis=1)
        labels=np.where(n==0,'fully_missing',np.where(n==6,'complete','partial'))
        actual=np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in rows])
        predictions={f:np.array([float(r[f+'_m']) if r[f+'_m'] else np.nan for r in rows]) for f in FAMILIES}
        for subset in ('all','level_ge_7m'):
            pop=np.ones(len(rows),dtype=bool) if subset=='all' else ((actual>=7)|~np.isfinite(actual))
            observed=pop&np.isfinite(actual)
            for family,pred in predictions.items():
                start=len(metrics)
                for category in ('complete','partial','fully_missing'):
                    mask=pop&(labels==category);obs=mask&observed;paired=obs&np.isfinite(pred)
                    error=pred[paired]-actual[paired];ae=abs(error)
                    metrics.append(dict(phase=phase,profile=profile,horizon_h=h,subset=subset,family=family,carreiro_availability=category,
                        classified_rows=int(mask.sum()),unknown_truth=int((mask&~np.isfinite(actual)).sum()),observed_targets=int(obs.sum()),pairs=int(paired.sum()),failures=int(obs.sum()-paired.sum()),
                        hits=int((ae<=.5).sum()),sum_abs_error_m=float(ae.sum()),mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(error.mean()) if len(error) else None,max_abs_m=float(ae.max()) if len(ae) else None))
                expected=ref[phase,profile,h,family,subset]
                for field in ('observed_targets','pairs','failures','hits'):
                    assert sum(r[field] for r in metrics[start:])==int(expected[field]);checks+=1
                assert sum(r['unknown_truth'] for r in metrics[start:])==int(expected['missing_truth']);checks+=1
                if int(expected['pairs']):
                    np.testing.assert_allclose(sum(r['sum_abs_error_m'] for r in metrics[start:])/int(expected['pairs']),float(expected['mae_m']),rtol=0,atol=1e-12);checks+=1
            old,new=predictions['mixed_profile_candidate'],predictions['carreiro_missing_exposure']
            paired=observed&np.isfinite(old)&np.isfinite(new);a=abs(old-actual)<=.5;b=abs(new-actual)<=.5
            for category in ('complete','partial','fully_missing'):
                m=paired&(labels==category)
                transitions.append(dict(phase=phase,profile=profile,horizon_h=h,subset=subset,carreiro_availability=category,pairs=int(m.sum()),gained=int((m&~a&b).sum()),lost=int((m&a&~b).sum()),net_hits=int((m&b).sum()-(m&a).sum())))
    assert len(metrics)==1152 and len(transitions)==288
    save('availability-strata.csv',metrics);save('availability-transitions.csv',transitions)
    (OUT/'availability.json').write_text(json.dumps(dict(metrics=len(metrics),transitions=len(transitions),reconciliations=checks,source_manifest_sha256=sha(SOURCE/'artifact-hashes.json'),matrix_sha256=sha(PARENT/'prepared-inputs.npz'),posthoc_diagnostic=True,promoted=False),indent=2)+'\n')
    with (OUT/'README.md').open('a') as f:
        f.write('\n## Disponibilidade real do Carreiro\n\nA partição abaixo usa os seis campos reais de entrada, sem mascarar a avaliação. É diagnóstico posterior, não critério para escolher versões. No recorte alto, alvos de verdade ausente continuam separados e não são considerados cheias.\n\n| Perfil | h | Carreiro real | Acertos original → candidato / alvos |\n|---|---:|---|---:|\n')
        lookup={(r['phase'],r['profile'],r['horizon_h'],r['subset'],r['family'],r['carreiro_availability']):r for r in metrics}
        for r in metrics:
            if r['phase']=='test' and r['horizon_h'] in (6,12) and r['subset']=='level_ge_7m' and r['family']=='carreiro_missing_exposure':
                old=lookup[r['phase'],r['profile'],r['horizon_h'],r['subset'],'mixed_profile_candidate',r['carreiro_availability']]
                f.write(f"| {r['profile']} | {r['horizon_h']} | {r['carreiro_availability']} | {old['hits']} → {r['hits']} / {r['observed_targets']} |\n")
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(dict(metrics=len(metrics),transitions=len(transitions),checks=checks)))

if __name__=='__main__':main()
