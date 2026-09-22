"""Reconstruct all core33 metrics and model predictions without refitting."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch,iso

OUT=Path(__file__).resolve().parent
RUN=ROOT/'outputs/experimento-radar-core33-20260921'
REF=ROOT/'outputs/experimento-radar-historico-2023-20260921'
DATA=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
NEW=ROOT/'outputs/radar-matriz-observada-2023-20260921'

def rows(p): return list(csv.DictReader(p.open()))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mkey(r): return tuple(r[k] for k in ('phase','horizon_h','subset','population','family'))
def save(p,data):
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

def main():
    manifest=json.loads((RUN/'artifact-hashes.json').read_text())
    for r in manifest: assert sha(RUN/r['file'])==r['sha256']
    exp=json.loads((RUN/'experiment.json').read_text())
    for path,value in exp['input_sha256'].items(): assert sha(Path(path))==value
    d=dict(np.load(DATA/'features.npz')); nd=dict(np.load(NEW/'features.npz'))
    t,F,base,truth,complete=(d[k] for k in ('times','features','base','truth','complete24'))
    F=F[:,np.r_[0:12,24:45]]
    nt,nb,ny=(nd[k] for k in ('times','base','truth'))
    index={iso(v):i for i,v in enumerate(t)}
    predictions=rows(RUN/'predictions.csv');previous=rows(REF/'predictions.csv')
    assert len(predictions)==len(previous)==102084
    for a,b in zip(predictions,previous):
        for field,value in b.items(): assert a[field]==value
        assert bool(a['core_original_m'])==bool(a['core_augmented_m'])==bool(a['observed_control_m'])
    masks=dict(np.load(RUN/'training-masks.npz'))
    info={(r['phase'],int(r['horizon_h']),r['family']):r for r in rows(RUN/'training.csv')}
    oldinfo={(r['phase'],int(r['horizon_h'])):r for r in rows(ROOT/'outputs/experimento-radar-observado-120-20260921/training.csv')}
    start=epoch('2025-10-01T00:00:00-03:00');end=epoch('2026-07-01T00:00:00-03:00')
    boundary=epoch('2023-10-01T00:00:00-03:00')
    model_checks=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            target=np.r_[truth[h:],np.full(h,np.nan)];newtarget=np.r_[ny[h:],np.full(h,np.nan)]
            first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
            oldmask=np.isfinite(base)&np.isfinite(target)&(first if phase=='validation' else first|second)
            newmask=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
            np.testing.assert_array_equal(oldmask,masks[f'{phase}_original_h{h}'])
            np.testing.assert_array_equal(newmask,masks[f'new_h{h}'])
            selected=[r for r in predictions if r['phase']==phase and int(r['nominal_lead_h'])==h and r['core_original_m']]
            indices=np.array([index[r['origin']] for r in selected])
            for family in ('core_original','core_augmented'):
                meta=info[phase,h,family];original=oldinfo[phase,h];include=family=='core_augmented'
                assert int(meta['original_n'])==int(oldmask.sum())==int(original['n'])
                assert int(meta['added_n'])==(int(newmask.sum()) if include else 0)
                levels=np.r_[newtarget[newmask],target[oldmask]] if include else target[oldmask]
                delta=np.r_[newtarget[newmask]-nb[newmask],target[oldmask]-base[oldmask]] if include else target[oldmask]-base[oldmask]
                weights=1+2*(abs(delta)>=1)+2*(levels>=9)
                assert int(meta['n'])==len(delta) and int(meta['weight_sum'])==int(weights.sum())
                assert float(meta['response_min_m'])==delta.min() and float(meta['response_max_m'])==delta.max()
                assert np.all(t[oldmask]+h*3600<epoch(meta['cutoff_exclusive']))
                model=joblib.load(RUN/'models'/f'{phase}-{family}-{h}.joblib')
                actual=model.predict(F[indices])+base[indices]
                expected=np.array([float(r[family+'_m']) for r in selected])
                np.testing.assert_array_equal(actual,expected)
                assert model.n_features_in_==33 and model.n_iter_==180
                params=model.get_params()
                for k,v in dict(max_iter=180,max_leaf_nodes=int(original['leaf_nodes']),loss=original['loss'],
                    min_samples_leaf=35,learning_rate=.055,l2_regularization=10,early_stopping=False,random_state=57).items():
                    assert params[k]==v
                assert all(tree[0].nodes[0]['count']==len(delta) for tree in model._predictors)
                model_checks.append(dict(phase=phase,horizon_h=h,family=family,predictions=len(selected),max_difference_m=0.0))
    metrics=rows(RUN/'evaluation.csv');lookup={mkey(r):r for r in metrics}
    for r in metrics:
        group=[p for p in predictions if p['phase']==r['phase'] and p['nominal_lead_h']==r['horizon_h'] and
            (r['population']=='full_schedule' or (p['original_complete24']=='True')==(r['population']=='complete24'))]
        obs=[p for p in group if p['actual_m'] and (r['subset']=='all' or float(p['actual_m'])>=7)]
        pairs=[p for p in obs if p[r['family']+'_m']]
        errors=np.array([float(p[r['family']+'_m'])-float(p['actual_m']) for p in pairs]);ae=abs(errors)
        hits=int((ae<=.5).sum())
        for k,v in dict(scheduled_rows=len(group),observed_targets=len(obs),n=len(pairs),failures=len(obs)-len(pairs),hits=hits).items():
            assert int(r[k])==v
        for k,v in dict(hit_fraction=hits/len(ae) if len(ae) else None,observed_target_hit_fraction=hits/len(obs) if len(obs) else None,
            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(errors.mean()) if len(ae) else None,
            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None).items():
            assert float(r[k])==v if v is not None else not r[k]
    previousmetrics=rows(REF/'evaluation.csv')
    for r in previousmetrics: assert lookup[mkey(r)]==r
    effects=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                for a,b in [('observed_control','augmented'),('core_original','core_augmented'),
                            ('observed_control','core_original'),('augmented','core_augmented')]:
                    left=lookup[phase,str(h),subset,'full_schedule',a];right=lookup[phase,str(h),subset,'full_schedule',b]
                    effects.append(dict(phase=phase,horizon_h=h,subset=subset,reference=a,candidate=b,
                        delta_hits=int(right['hits'])-int(left['hits']),delta_mae_m=float(right['mae_m'])-float(left['mae_m']),
                        delta_max_abs_m=float(right['max_abs_m'])-float(left['max_abs_m'])))
    save(OUT/'effects.csv',effects)
    result=dict(artifact_hashes_verified=len(manifest),input_hashes_verified=len(exp['input_sha256']),
        models_verified=len(model_checks),metric_rows_recomputed=len(metrics),frozen_metric_rows_exact=len(previousmetrics),
        prediction_rows=len(predictions),checks=model_checks,promoted=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# RADAR: compatibilidade das 33 entradas','',
        'Comparação fatorial local: 120/33 entradas, com/sem acréscimo de setembro de 2023. Mesmas máscaras, parâmetros, pesos e 102.084 previsões. 48 novos modelos e 48 controles congelados. Nenhuma promoção operacional.','',
        'Acerto: erro absoluto ≤0,50 m; cheia: observado ≥7 m, recorte analítico. As duas fases são desenvolvimento já inspecionado; não são prova prospectiva.','',
        '| Fase | Horizonte | Família | Acertos/pares cheia | Acertos/alvos com falhas | MAE (m) | Maior erro (m) |',
        '|---|---:|---|---:|---:|---:|---:|']
    for phase in ('validation','test'):
        for h in (1,6,12):
            for family in ('observed_control','augmented','core_original','core_augmented'):
                r=lookup[phase,str(h),'level_ge_7m','full_schedule',family]
                lines.append(f"| {phase} | {h}h | {family} | {r['hits']}/{r['n']} | {r['hits']}/{r['observed_targets']} | {float(r['mae_m']):.4f} | {float(r['max_abs_m']):.4f} |")
    lines+=['','## Efeito de acrescentar 2023 às 33 entradas','',
        '| Fase | Horizonte | Diferença acertos cheia | Diferença MAE (m) | Diferença maior erro (m) |',
        '|---|---:|---:|---:|---:|']
    for r in effects:
        if r['subset']=='level_ge_7m' and r['reference']=='core_original':
            lines.append(f"| {r['phase']} | {r['horizon_h']}h | {r['delta_hits']:+d} | {r['delta_mae_m']:+.4f} | {r['delta_max_abs_m']:+.4f} |")
    lines+=['','Todos os horizontes, populações, recortes e quatro contrastes estão em effects.csv/evaluation.csv. Não combinar horizontes com base nos resultados já vistos. A retirada de chuva não a torna fisicamente irrelevante; diferenças de modelos não identificam sozinhas uma causa hidrológica. Metadados, datum, regime das usinas e publicação histórica permanecem sem certificação. As faltas remanescentes foram preservadas.','',
        f"Verificação: {len(model_checks)} modelos reproduzidos exatamente, {len(metrics)} métricas recalculadas e {len(previousmetrics)} métricas congeladas idênticas. Contagens, pesos, parâmetros, cortes e hashes conferidos. Meta de 98% não atingida."]
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    print('\n'.join(lines[6:32]))

if __name__=='__main__':
    with threadpool_limits(limits=2): main()
