"""Describe regression by target/base response without changing any forecast."""
import csv,hashlib,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
RUN=ROOT/'outputs/experimento-radar-historico-2023-20260921'
def read(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def response(r):
    if not r['base_m']:return 'unavailable_base'
    d=float(r['actual_m'])-float(r['base_m'])
    return 'increase_gt_0.5m' if d>.5 else 'decrease_gt_0.5m' if d<-.5 else 'within_0.5m'
def stats(group,family):
    pairs=[r for r in group if r[family+'_m']]
    e=np.array([float(r[family+'_m'])-float(r['actual_m']) for r in pairs]);ae=abs(e)
    return dict(observed=len(group),n=len(pairs),failures=len(group)-len(pairs),hits=int((ae<=.5).sum()),
        mae_m=float(ae.mean()) if len(ae) else None,bias_m=float(e.mean()) if len(e) else None,
        absolute_error_sum_m=float(ae.sum()),maximum_error_m=float(ae.max()) if len(ae) else None)
def main():
    manifest=json.loads((RUN/'artifact-hashes.json').read_text())
    for name in ('predictions.csv','evaluation.csv','training.csv'):
        assert sha(RUN/name)==next(r['sha256'] for r in manifest if r['file']==name)
    rows=read(RUN/'predictions.csv');metrics=read(RUN/'evaluation.csv')
    lookup={(r['phase'],int(r['horizon_h']),r['subset'],r['family']):r for r in metrics if r['population']=='full_schedule'}
    strata=[];comparisons=[];summaries=[];checks=0
    kinds=['increase_gt_0.5m','decrease_gt_0.5m','within_0.5m','unavailable_base']
    for phase in ('validation','test'):
        for h in range(1,13):
            full=[r for r in rows if r['phase']==phase and int(r['nominal_lead_h'])==h]
            for subset in ('all','level_ge_7m'):
                group=[r for r in full if r['actual_m'] and (subset=='all' or float(r['actual_m'])>=7)]
                paired=[r for r in group if r['observed_control_m'] and r['augmented_m']]
                change=np.array([float(r['augmented_m'])-float(r['observed_control_m']) for r in paired])
                aechange=np.array([abs(float(r['augmented_m'])-float(r['actual_m']))-abs(float(r['observed_control_m'])-float(r['actual_m'])) for r in paired])
                summaries.append(dict(phase=phase,horizon_h=h,subset=subset,paired=len(paired),
                    mean_forecast_shift_m=float(change.mean()),mean_absolute_error_change_m=float(aechange.mean()),
                    improved=int((aechange<0).sum()),worsened=int((aechange>0).sum()),unchanged=int((aechange==0).sum()),
                    upward_forecast_changes=int((change>0).sum()),downward_forecast_changes=int((change<0).sum())))
                for family in ('observed_control','augmented'):
                    total=stats(group,family);prior=lookup[phase,h,subset,family]
                    for k,oldkey in [('observed','observed_targets'),('n','n'),('failures','failures'),('hits','hits')]:assert total[k]==int(prior[oldkey])
                    for k in ('mae_m','bias_m'):assert abs(total[k]-float(prior[k]))<1e-12
                    pieces=[]
                    for kind in kinds:
                        selected=[r for r in group if response(r)==kind];s=stats(selected,family);pieces.append(s)
                        strata.append(dict(phase=phase,horizon_h=h,subset=subset,response_group=kind,family=family,**s))
                    for k in ('observed','n','failures','hits'):assert sum(s[k] for s in pieces)==total[k]
                    assert abs(sum(s['absolute_error_sum_m'] for s in pieces)-total['absolute_error_sum_m'])<1e-9
                    checks+=1
                if phase=='validation' and subset=='level_ge_7m':
                    for r in paired:
                        a=float(r['observed_control_m']);b=float(r['augmented_m']);y=float(r['actual_m'])
                        comparisons.append(dict(origin=r['origin'],target_time=r['target_time'],horizon_h=h,base_m=float(r['base_m']),actual_m=y,
                            response_group=response(r),control_m=a,candidate_m=b,control_error_m=a-y,candidate_error_m=b-y,
                            forecast_shift_m=b-a,absolute_error_change_m=abs(b-y)-abs(a-y)))
    targets=sorted({r['target_time'] for r in comparisons})
    for h in range(1,13):assert sorted(r['target_time'] for r in comparisons if r['horizon_h']==h)==targets
    gaps=[(datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds() for a,b in zip(targets,targets[1:])]
    assert all(v==3600 for v in gaps) and len(targets)==28
    save('response-strata.csv',strata);save('forecast-changes.csv',summaries);save('validation-high-cases.csv',comparisons)
    result=dict(rows=len(rows),metric_groups_reconciled=checks,validation_high_unique_targets=len(targets),
        validation_high_forecast_pairs=len(comparisons),first_validation_high_target=targets[0],last_validation_high_target=targets[-1],
        contiguous_hourly_targets=True,independent_event_certified=False,
        input_sha256={name:sha(RUN/name) for name in ('predictions.csv','evaluation.csv','training.csv')},
        strata_use_future_observed_response_for_diagnosis_only=True,trained=False,promoted=False,goal_achieved=False)
    (OUT/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Regressão após acrescentar setembro2023 ao RADAR','',
        'Diagnóstico posterior ao ensaio, sem novas previsões ou ajustes. As faixas abaixo usam a resposta observada alvo−base apenas para explicar resultados; não são entradas disponíveis antecipadamente nem filtros de avaliação.','',
        f"Os28 alvos de cheia na validation são as mesmas28 observações em todos os horizontes, de{targets[0]} a{targets[-1]}, sem lacunas horárias. São336 pares de previsão, não336 observações ou eventos independentes. O trecho contínuo não foi certificado como um evento independente.",'',
        '| Horizonte | Viés controle(m) | Viés +2023(m) | Deslocamento médio da previsão(m) | Casos que melhoram/pioram |',
        '|---|---:|---:|---:|---:|']
    for h in range(1,13):
        a=lookup['validation',h,'level_ge_7m','observed_control'];b=lookup['validation',h,'level_ge_7m','augmented']
        s=next(r for r in summaries if r['phase']=='validation' and r['horizon_h']==h and r['subset']=='level_ge_7m')
        lines.append(f"| {h}h | {float(a['bias_m']):.4f} | {float(b['bias_m']):.4f} | {s['mean_forecast_shift_m']:+.4f} | {s['improved']}/{s['worsened']} |")
    lines+=['','## Recorte de12h por resposta observada','',
        '| Fase | Resposta alvo−base | Versão | Pares | Acertos | MAE(m) | Viés(m) |','|---|---|---|---:|---:|---:|---:|']
    for r in strata:
        if r['horizon_h']==12 and r['subset']=='level_ge_7m' and r['n']:
            lines.append(f"| {r['phase']} | {r['response_group']} | {r['family']} | {r['n']} | {r['hits']} | {r['mae_m']:.4f} | {r['bias_m']:.4f} |")
    lines+=['','## Interpretação e limites','',
        'Os arquivos conservam os dois períodos, todos os12h, todos os alvos observados e as falhas com base ausente. As quatro classes de resposta reconciliam contagens, acertos e soma dos erros absolutos de96 grupos originais. Linhas sem alvo permanecem no experimento original.','',
        'Viés positivo significa previsão acima da observação. Um deslocamento médio positivo junto de viés previamente positivo indica piora descritiva da sobrestimação; não demonstra sozinho causa física, efeito de um preditor específico ou validade de subtrair uma constante na operação. O período já foi examinado, e corrigir com seu erro futuro seria vazamento.','',
        'Não se inferiu significância tratando horas correlacionadas como independentes. Nenhuma tolerância foi ampliada e nenhuma amostra foi retirada. Candidato não promovido; meta98% não demonstrada.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps(result,indent=2));print('\n'.join(lines[6:21]))
if __name__=='__main__':main()
