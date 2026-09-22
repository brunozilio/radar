"""Audit frozen 2020 augmentation without refitting or touching live forecasts."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch, iso

OUT = Path(__file__).resolve().parent
RUN = ROOT/'outputs/experimento-radar-historico-2020-20260921'
REF = ROOT/'outputs/experimento-radar-observado-120-20260921'
DATA = ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
NEW = ROOT/'outputs/radar-matriz-observada-2020-20260921'


def rows(p): return list(csv.DictReader(p.open()))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def metric_key(r): return tuple(r[k] for k in ('phase','horizon_h','subset','population','family'))


def main():
    manifest=json.loads((RUN/'artifact-hashes.json').read_text())
    for r in manifest: assert digest(RUN/r['file'])==r['sha256']
    exp=json.loads((RUN/'experiment.json').read_text())
    for path,value in exp['input_sha256'].items(): assert digest(Path(path))==value
    d=dict(np.load(DATA/'features.npz')); n=dict(np.load(NEW/'features.npz'))
    t,F,base,truth,complete=(d[k] for k in ('times','features','base','truth','complete24'))
    F=F[:,:120]
    nt,nb,ny=(n[k] for k in ('times','base','truth'))
    ix={iso(v):i for i,v in enumerate(t)}
    preds=rows(RUN/'predictions.csv'); reference=rows(REF/'predictions.csv')
    assert len(preds)==len(reference)==102084
    for a,b in zip(preds,reference):
        for field in ('phase','origin','target_time','nominal_lead_h','original_complete24','base_m','actual_m'):
            assert a[field]==b[field]
        assert a['observed_control_m']==b['observed_only_m']
        assert bool(a['observed_control_m'])==bool(a['augmented_m'])
    info={(r['phase'],int(r['horizon_h'])):r for r in rows(RUN/'training.csv')}
    oldinfo={(r['phase'],int(r['horizon_h'])):r for r in rows(REF/'training.csv')}
    masks=dict(np.load(RUN/'training-masks.npz'))
    qi=rows(NEW/'qi-origin-diagnostics.csv')
    assert all(epoch(v['origin'])==tt for v,tt in zip(qi,nt)) and len(qi)==len(nt)
    zero=np.array([v['uses_any_zero']=='True' for v in qi])
    start=epoch('2025-10-01T00:00:00-03:00'); end=epoch('2026-07-01T00:00:00-03:00')
    boundary=epoch('2020-07-21T00:00:00-03:00')
    checks=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            target=np.r_[truth[h:],np.full(h,np.nan)]
            newtarget=np.r_[ny[h:],np.full(h,np.nan)]
            first=t+h*3600<start
            second=(t>=start)&(t+h*3600<end)
            mask=np.isfinite(base)&np.isfinite(target)&(first if phase=='validation' else first|second)
            newmask=np.isfinite(nb)&np.isfinite(newtarget)&(nt+h*3600<boundary)
            np.testing.assert_array_equal(mask,masks[f'{phase}_original_h{h}'])
            np.testing.assert_array_equal(newmask,masks[f'new_h{h}'])
            assert not (newmask&zero).any()
            meta=info[phase,h]; orig=oldinfo[phase,h]
            assert int(mask.sum())==int(meta['original_n'])==int(orig['n'])
            expected_new=next(r['valid_pairs'] for r in json.loads((NEW/'preparation.json').read_text())['target_coverage'] if r['horizon_h']==h)
            assert int(newmask.sum())==int(meta['added_n'])==expected_new
            assert int(meta['n'])==int(mask.sum()+newmask.sum())
            assert np.all(nt[newmask]+h*3600<boundary)
            assert iso((nt[newmask]+h*3600).max())==meta['latest_added_target']
            assert np.all(t[mask]+h*3600<epoch(meta['cutoff_exclusive']))
            assert np.all(nt[newmask]+h*3600<epoch(meta['cutoff_exclusive']))
            olddelta=target[mask]-base[mask]; newdelta=newtarget[newmask]-nb[newmask]
            for label,value in [('original_response_min_m',olddelta.min()),('original_response_max_m',olddelta.max()),
                                ('added_response_min_m',newdelta.min()),('added_response_max_m',newdelta.max()),
                                ('combined_response_min_m',min(olddelta.min(),newdelta.min())),
                                ('combined_response_max_m',max(olddelta.max(),newdelta.max()))]:
                assert float(meta[label])==float(value)
            assert int(meta['added_targets_ge_7m'])==int((newtarget[newmask]>=7).sum())
            group=[r for r in preds if r['phase']==phase and int(r['nominal_lead_h'])==h]
            selected=[r for r in group if r['augmented_m']]
            indices=np.array([ix[r['origin']] for r in selected])
            model=joblib.load(RUN/'models'/f'{phase}-{h}.joblib')
            actual=model.predict(F[indices])+base[indices]
            expected=np.array([float(r['augmented_m']) for r in selected])
            np.testing.assert_array_equal(actual,expected)
            assert model.n_features_in_==120 and model.n_iter_==180
            settings=model.get_params()
            for name,value in dict(max_leaf_nodes=int(orig['leaf_nodes']),loss=orig['loss'],max_iter=180,
                    min_samples_leaf=35,learning_rate=.055,l2_regularization=10,early_stopping=False,random_state=57).items():
                assert settings[name]==value
            assert all(p[0].nodes[0]['count']==int(meta['n']) for p in model._predictors)
            checks.append(dict(phase=phase,horizon_h=h,predictions=len(selected),new_pairs=int(newmask.sum()),
                               maximum_inference_difference_m=float(abs(actual-expected).max())))
    evaluation=rows(RUN/'evaluation.csv'); metrics={metric_key(r):r for r in evaluation}
    metric_checks=0
    for r in evaluation:
        group=[v for v in preds if v['phase']==r['phase'] and v['nominal_lead_h']==r['horizon_h'] and
               (r['population']=='full_schedule' or (v['original_complete24']=='True')==(r['population']=='complete24'))]
        obs=[v for v in group if v['actual_m'] and (r['subset']=='all' or float(v['actual_m'])>=7)]
        paired=[v for v in obs if v[r['family']+'_m']]
        errors=np.array([float(v[r['family']+'_m'])-float(v['actual_m']) for v in paired]); ae=abs(errors)
        hits=int((ae<=.5).sum())
        for field,value in dict(scheduled_rows=len(group),observed_targets=len(obs),n=len(paired),failures=len(obs)-len(paired),hits=hits).items():
            assert int(r[field])==value
        for field,value in dict(hit_fraction=hits/len(ae) if len(ae) else None,
                    observed_target_hit_fraction=hits/len(obs) if len(obs) else None,
                    mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(errors.mean()) if len(ae) else None,
                    p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None).items():
            assert float(r[field])==value if value is not None else not r[field]
        metric_checks+=1
    control_checks=0
    for r in rows(REF/'evaluation.csv'):
        if r['family']!='observed_only': continue
        translated=dict(r,family='observed_control'); current=metrics[metric_key(translated)]
        for field,value in translated.items(): assert current[field]==value
        control_checks+=1
    changes=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                a=metrics[phase,str(h),subset,'full_schedule','observed_control']
                b=metrics[phase,str(h),subset,'full_schedule','augmented']
                changes.append(dict(phase=phase,horizon_h=h,subset=subset,
                    delta_hits=int(b['hits'])-int(a['hits']),delta_mae_m=float(b['mae_m'])-float(a['mae_m']),
                    delta_max_abs_m=float(b['max_abs_m'])-float(a['max_abs_m'])))
    with (OUT/'changes.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
    result=dict(artifact_hashes_verified=len(manifest),input_hashes_verified=len(exp['input_sha256']),
        models_verified=24,metric_rows_recomputed=metric_checks,frozen_control_metric_rows_exact=control_checks,
        prediction_rows=102084,checks=checks,promoted=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# RADAR: acréscimo de histórico de2020','',
        'Ensaio local de desenvolvimento com24 modelos novos e24 controles congelados. O candidato usa os mesmos120 campos e parâmetros da referência que aceita entradas auxiliares ausentes, acrescentando todo o intervalo de 01–20/07/2020 permitido pelo protocolo. Nenhuma promoção ou mudança operacional.','',
        'Acerto: erro absoluto≤0,50m. Cheia: observado≥7m, recorte analítico. As fases validation/test já foram examinadas e não são holdout independente.','',
        '| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos incluindo falhas | MAE(m) | Maior erro(m) |',
        '|---|---:|---|---:|---:|---:|---:|']
    for phase in ('validation','test'):
        for h in (1,6,12):
            for family,label in [('observed_control','Referência120'),('augmented','+2020')]:
                r=metrics[phase,str(h),'level_ge_7m','full_schedule',family]
                lines.append(f"| {phase} | {h}h | {label} | {r['hits']}/{r['n']} | {r['hits']}/{r['observed_targets']} | {float(r['mae_m']):.4f} | {float(r['max_abs_m']):.4f} |")
    lines+=['','## Efeito em todos os horizontes de cheia','',
        '| Fase | Horizonte | Diferença de acertos | Diferença MAE(m) | Diferença maior erro(m) |',
        '|---|---:|---:|---:|---:|']
    for r in changes:
        if r['subset']=='level_ge_7m':
            lines.append(f"| {r['phase']} | {r['horizon_h']}h | {r['delta_hits']:+d} | {r['delta_mae_m']:+.4f} | {r['delta_max_abs_m']:+.4f} |")
    tr=info['test',12]
    lines+=['','## Dados e limites','',
        f"Em12h entram{tr['added_n']} pares, dos quais{tr['added_targets_ge_7m']} com alvo≥7m. A maior resposta no treino passa de{float(tr['original_response_max_m']):.2f}m para{float(tr['combined_response_max_m']):.2f}m. Não há seleção dos exemplos extremos: todo o intervalo elegível de01–20/07 foi incluído.", '',
        'As102.084 linhas de avaliação, os alvos, as bases e a disponibilidade de previsão são idênticos. O novo histórico nunca cruza o hiato2020–2025 no cálculo de alvos. Alvos ausentes e os últimos h exemplos permanecem inelegíveis. Carreiro e Santa Tereza continuam ausentes. O arquivo evaluation.csv contém todos os horizontes, recortes e falhas, inclusive linhas sem alvo.','',
        f"Auditoria:24 modelos reproduzidos exatamente;{metric_checks} linhas de métricas recalculadas;{control_checks} linhas de métricas do controle coincidem com a referência. Máscaras, cortes, parâmetros, contagens por árvore e hashes conferidos.", '',
        'Não comprova98% prospectivos. Publicação histórica, revisão de fontes, fuso, datum e comparabilidade entre regimes não estão certificados. Mais dados podem ajudar alguns horizontes e piorar outros; não montar uma combinação de versões por horizonte usando este conjunto já visto. O próximo candidato exige protocolo próprio e mantém estes resultados como desenvolvimento.']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=digest(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    print('\n'.join(lines[6:20]))


if __name__=='__main__':
    with threadpool_limits(limits=2): main()
