"""Independent replay, membership and metric checks for the observed-only ablation."""
import csv,json,hashlib,sys
from pathlib import Path
import joblib,numpy as np
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch,iso
OUT=Path(__file__).resolve().parent
RUN=ROOT/'outputs/experimento-radar-observado-120-20260921'
REF=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((RUN/'artifact-hashes.json').read_text())
    for r in manifest:assert sha(RUN/r['file'])==r['sha256']
    exp=json.loads((RUN/'experiment.json').read_text())
    for p,h in exp['input_sha256'].items():assert sha(Path(p))==h
    pred=rows(RUN/'predictions.csv');old=rows(REF/'predictions.csv');assert len(pred)==len(old)==102084
    for a,b in zip(pred,old):
        for k in ('phase','origin','target_time','nominal_lead_h','original_complete24','base_m','actual_m'):assert a[k]==b[k]
        assert a['native_control_m']==b['candidate_m']
        assert bool(a['observed_only_m'])==bool(b['candidate_m'])
    d=dict(np.load(REF/'features.npz'));masks=dict(np.load(RUN/'training-masks.npz'))
    t=d['times'];base=d['base'];truth=d['truth'];ix={iso(v):i for i,v in enumerate(t)}
    infos={(r['phase'],int(r['horizon_h'])):r for r in rows(RUN/'training.csv')}
    oldinfos={(r['phase'],int(r['horizon_h'])):r for r in rows(REF/'training.csv') if r['family']=='candidate'}
    start=epoch('2025-10-01T00:00:00-03:00');end=epoch('2026-07-01T00:00:00-03:00');replays=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            target=np.r_[truth[h:],np.full(h,np.nan)];first=t+h*3600<start;second=(t>=start)&(t+h*3600<end)
            mask=np.isfinite(base)&np.isfinite(target)&(first if phase=='validation' else first|second)
            np.testing.assert_array_equal(mask,masks[f'{phase}_h{h}'])
            info=infos[phase,h];prior=oldinfos[phase,h]
            assert mask.sum()==int(info['n'])==int(prior['n'])
            assert info['latest_training_target']==prior['latest_training_target']==iso((t[mask]+h*3600).max())
            assert info['cutoff_exclusive']==prior['cutoff_exclusive']
            group=[r for r in pred if r['phase']==phase and r['nominal_lead_h']==str(h) and r['observed_only_m']]
            indices=np.array([ix[r['origin']] for r in group]);model=joblib.load(RUN/'models'/f'{phase}-{h}.joblib')
            value=model.predict(d['features'][indices,:120])+base[indices]
            np.testing.assert_array_equal(value,[float(r['observed_only_m']) for r in group])
            assert model.n_features_in_==120 and model.n_iter_==180
            for k,v in dict(max_leaf_nodes=int(prior['leaf_nodes']),loss=prior['loss'],max_iter=180,min_samples_leaf=35,learning_rate=.055,l2_regularization=10,early_stopping=False,random_state=57).items():assert model.get_params()[k]==v
            assert all(tree[0].nodes[0]['count']==int(info['n']) for tree in model._predictors)
            replays.append(dict(phase=phase,horizon_h=h,n=len(group),maximum_difference_m=0.0))
    metrics=rows(RUN/'evaluation.csv')
    def key(r):return tuple(r[k] for k in ('phase','horizon_h','subset','population','family'))
    lookup={key(r):r for r in metrics}
    for r in metrics:
        group=[a for a in pred if a['phase']==r['phase'] and a['nominal_lead_h']==r['horizon_h'] and
            (r['population']=='full_schedule' or (a['original_complete24']=='True')==(r['population']=='complete24'))]
        obs=[a for a in group if a['actual_m'] and (r['subset']=='all' or float(a['actual_m'])>=7)]
        pairs=[a for a in obs if a[r['family']+'_m']]
        errors=np.array([float(a[r['family']+'_m'])-float(a['actual_m']) for a in pairs]);ae=abs(errors);hits=int((ae<=.5).sum())
        for k,v in dict(scheduled_rows=len(group),observed_targets=len(obs),n=len(pairs),failures=len(obs)-len(pairs),hits=hits).items():assert int(r[k])==v
        stats=dict(hit_fraction=hits/len(ae) if len(ae) else None,observed_target_hit_fraction=hits/len(obs) if len(obs) else None,
            mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(errors.mean()) if len(ae) else None,
            p98_abs_m=float(np.quantile(ae,.98)) if len(ae) else None,max_abs_m=float(ae.max()) if len(ae) else None)
        for k,v in stats.items():assert float(r[k])==v if v is not None else not r[k]
    control_count=0
    for r in rows(REF/'evaluation.csv'):
        if r['family']!='candidate':continue
        translated=dict(r,family='native_control');current=lookup[key(translated)]
        for k,v in translated.items():assert current[k]==v
        control_count+=1
    changes=[]
    for phase in ('validation','test'):
        for h in range(1,13):
            for subset in ('all','level_ge_7m'):
                a=lookup[phase,str(h),subset,'full_schedule','native_control'];b=lookup[phase,str(h),subset,'full_schedule','observed_only']
                changes.append(dict(phase=phase,horizon_h=h,subset=subset,delta_hits=int(b['hits'])-int(a['hits']),delta_mae_m=float(b['mae_m'])-float(a['mae_m']),delta_max_m=float(b['max_abs_m'])-float(a['max_abs_m'])))
    with (OUT/'changes.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
    report=dict(models_verified=24,metric_rows_recomputed=len(metrics),frozen_control_metric_rows_exact=control_count,
        artifact_hashes_verified=len(manifest),input_hashes_verified=len(exp['input_sha256']),replays=replays,promoted=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# RADAR: ensaio com120campos observados','',
        'Comparação histórica de desenvolvimento, com as mesmas102.084 linhas e os mesmos parâmetros. Somente os60campos de previsão meteorológica foram retirados; chuva futura não foi imposta igual azero. Não entraram dados novos de2023/2024. Não houve promoção.','',
        '| Fase | Horizonte | Versão | Acertos/pares cheia | Acertos/alvos com falhas | MAE(m) | Máximo(m) |','|---|---:|---|---:|---:|---:|---:|']
    for phase in ('validation','test'):
        for h in range(1,13):
            for family in ('native_control','observed_only'):
                r=lookup[phase,str(h),'level_ge_7m','full_schedule',family]
                lines.append(f"| {phase} | {h}h | {family} | {r['hits']}/{r['n']} | {r['hits']}/{r['observed_targets']} | {float(r['mae_m']):.4f} | {float(r['max_abs_m']):.4f} |")
    lines+=['','Acerto significa erro≤0,50m; cheia é recorte analítico observado≥7m. evaluation.csv inclui todos os horizontes e recortes, indisponibilidade e falhas. changes.csv preserva ganhos e regressões.','',
        'Os24modelos foram recarregados e suas previsões reproduzidas exatamente. Máscaras, cortes, parâmetros, contagens por árvore,288linhas de métricas e144linhas do controle foram conferidos.','',
        'Este ensaio estabelece um controle de120campos para eventual acréscimo de histórico sem NWP. Os parâmetros foram escolhidos anteriormente para180campos e não foram otimizados de novo. Todas as fases jáforam examinadas; não constituem validação independente nem prova de98% prospectivos. Permanecem pendências de metadados, publicação e comparabilidade física.']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='replays'},indent=2))
    print([r for r in changes if r['phase']=='test' and r['subset']=='level_ge_7m'])
if __name__=='__main__':
    with threadpool_limits(limits=2):main()
