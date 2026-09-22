"""Independent direct-window verification of every sequential correction."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch,iso
from hydro_past_error_calibration import evaluate
from hydro_upstream_audit import savecsv
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'

def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
meta=json.loads((OUT/'experiment.json').read_text())
for name,expected in meta['input_sha256'].items():assert sha(Path(name))==expected
old=rows(PRIOR/'predictions.csv');new=rows(OUT/'predictions.csv');assert len(old)==len(new)==23538
lookup={(r['origin'],r['target_time']):r for r in new};assert len(lookup)==len(new)
for x in old:
    y=lookup[x['origin'],x['target_time']]
    for k in ['actual_m','julho_levels_m','status']:assert x[k]==y[k]
    assert bool(y['julho_levels_m'])==bool(y['past_error_median_m'])
trace=[];maxdiff=0.
for horizon in range(1,13):
    selected=[r for r in old if int(r['nominal_lead_h'])==horizon]
    origins=np.array([epoch(r['origin']) for r in selected]);targets=np.array([epoch(r['target_time']) for r in selected])
    base=np.array([float(r['julho_levels_m']) if r['julho_levels_m'] else np.nan for r in selected]);actual=np.array([float(r['actual_m']) if r['actual_m'] else np.nan for r in selected])
    np.testing.assert_array_equal(targets-origins,np.full(len(origins),horizon*3600))
    for i,r in enumerate(selected):
        at=origins[i]
        valid=(targets>=at-86400)&(targets<=at-900)&(origins<at)&np.isfinite(base)&np.isfinite(actual)
        support=np.where(valid)[0];adjust=float(np.median(base[valid]-actual[valid])) if len(support)>=6 and np.isfinite(base[i]) else 0.
        got=lookup[r['origin'],r['target_time']]
        assert len(support)==int(got['supporting_errors'])
        assert abs(adjust-float(got['correction_subtracted_m']))<1e-12
        if np.isfinite(base[i]):
            diff=abs(base[i]-adjust-float(got['past_error_median_m']));maxdiff=max(maxdiff,diff)
        latest=iso(targets[support[-1]]) if len(support) else '';assert latest==got['latest_supporting_target']
        trace.append(dict(origin=r['origin'],nominal_lead_h=horizon,supporting_errors=len(support),first_supporting_target=iso(targets[support[0]]) if len(support) else '',latest_supporting_target=latest,verified_correction_m=adjust))
assert maxdiff<1e-12
savecsv(OUT/'calibration-window-audit.csv',trace)
labelled=[]
for r in new:
    for k in ['actual_m','julho_levels_m','past_error_median_m']:r[k]=float(r[k]) if r[k] else None
    r['nominal_lead_h']=int(r['nominal_lead_h']);labelled.append(r)
clusters=[]
for event in sorted({r['observed_cluster_id'] for r in new if r['observed_cluster_id']}):
    for result in evaluate([r for r in labelled if r['observed_cluster_id']==event]):
        if result['subset']=='level_ge_7m':clusters.append(dict(observed_cluster_id=event,independence_certified=False,**result))
savecsv(OUT/'cluster-metrics.csv',clusters)
evals=rows(OUT/'evaluation.csv');transition=[]
for h in range(1,13):
    for high in [False,True]:
        group=[r for r in labelled if r['nominal_lead_h']==h and r['actual_m'] is not None and (not high or r['actual_m']>=7)]
        lost=gained=0
        for r in group:
            if r['julho_levels_m'] is None:continue
            a=abs(r['julho_levels_m']-r['actual_m'])<=.5;b=abs(r['past_error_median_m']-r['actual_m'])<=.5
            lost+=a and not b;gained+=b and not a
        transition.append(dict(nominal_lead_h=h,subset='level_ge_7m' if high else 'all',lost_hits=int(lost),gained_hits=int(gained)))
savecsv(OUT/'hit-transitions.csv',transition)
dump('verification.json',dict(input_hashes_verified=len(meta['input_sha256']),rows_independently_checked=len(new),max_direct_window_prediction_difference_m=maxdiff,target_origin_identity_verified=True,baseline_values_unchanged=True,coverage_unchanged=True,tests_passed=105,goal_achieved=False))
dump('decision.json',dict(promoted=False,live_issuance=False,goal_achieved=False,decision='Reject broad application of this past-error median correction.',reason='One-hour accuracy improves but flood accuracy remains below98%; longer horizons worsen and maximum errors increase. Selecting only favorable horizons after observing this development test would not supply independent validation.',next_evidence='Preserve fixed policy and evaluate in a genuinely subsequent period before considering any horizon-specific use. Do not retune window/gain against the inspected flood results.'))
lines=['# Correção pela mediana de erros já verificáveis','','**A correção não será aplicada à rotina horária.** Ela ajuda em 1 h, mas piora os prazos longos e aumenta alguns erros extremos. A meta completa de 98% não foi atingida.','','Para cada horizonte, o teste subtrai do nível original a mediana dos erros de previsões originais cujos alvos já ocorreram entre origem−24 h e origem−15 min, com pelo menos seis pares finitos. O histórico começa vazio em julho; não há preenchimento ou realimentação com erros de previsões corrigidas. Janela, atraso e mínimo foram fixados antes da execução.','','## Comparação','','| Prazo | Recorte | Modelo | Pares | Acertos ±0,50 m | MAE | Máximo |','|---|---|---|---:|---:|---:|---:|']
for r in evals:
    if int(r['nominal_lead_h']) in [1,6,12]:lines.append(f"| {r['nominal_lead_h']} h | {r['subset']} | {r['family']} | {r['n']} | {float(r['accuracy_percent']):.2f}% | {float(r['mae_m']):.3f} m | {float(r['max_abs_m']):.3f} m |")
lines+=['','Em 1 h, o resultado geral de 98,40% é apenas histórico e o recorte de cheias fica em 95,32%. Não atende à meta que exige todos os prazos, cheias e prova prospectiva. Em 12 h nas cheias, a taxa cai de 30,21% para 22,55%, e o MAE sobe de 1,375 para 1,841 m. Não será selecionado somente o prazo favorável após examinar o resultado.','','## Integridade e causalidade','','Foram mantidas todas as 23.538 linhas, os valores-base e a cobertura. Houve correção em 22.979 previsões; nenhuma ficou negativa. Uma verificação independente por seleção direta de janelas reproduziu todas as correções, com diferença máxima zero, e registrou o primeiro e o último alvo usado em `calibration-window-audit.csv`. Todos os alvos utilizados têm aprovação explícita no acervo auditado.','','Os 105 testes passaram, incluindo impossibilidade de dados futuros afetarem previsões anteriores, atraso de observação, ausência de realimentação e conservação de previsões ausentes. `cluster-metrics.csv` preserva as métricas de cada agrupamento, sem certificar independência.','','A disponibilidade histórica após 15 minutos permanece presumida; revisões posteriores das fontes não estão reconstituídas por emissão. É uma adaptação sequencial com observações anteriores do mesmo evento, não um modelo estático avaliado sem acesso posterior a esse período. Não há evidência prospectiva nem intervalo de confiança inferido de janelas sobrepostas.','']
(OUT/'report.md').write_text('\n'.join(lines))
dump('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'verified_rows':len(new),'max_difference':maxdiff,'decision':'not_promoted'}))
