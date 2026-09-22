"""Inspect frozen tree paths and training support; no fitting or counterfactual edits."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch,iso

OUT=Path(__file__).resolve().parent
REF=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
NEW=ROOT/'outputs/radar-matriz-2024-20260921'
RUN=ROOT/'outputs/experimento-radar-historico-2024-20260921'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return list(csv.DictReader(p.open()))
def save(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def leaves(nodes,X):
    assert not nodes['is_categorical'].any()
    indices=np.zeros(len(X),dtype=int)
    for _ in range(len(nodes)):
        active=np.where(~nodes['is_leaf'][indices].astype(bool))[0]
        if not len(active): return indices
        current=nodes[indices[active]]
        values=X[active,current['feature_idx']]
        goleft=np.where(np.isnan(values),current['missing_go_to_left'].astype(bool),values<=current['num_threshold'])
        indices[active]=np.where(goleft,current['left'],current['right'])
    raise AssertionError('Tree traversal failed to terminate')


def path(nodes,x):
    i=0;route=[]
    while not nodes[i]['is_leaf']:
        node=nodes[i];j=int(node['feature_idx']);v=x[j]
        left=bool(node['missing_go_to_left']) if np.isnan(v) else v<=node['num_threshold']
        route.append((i,j,bool(left)))
        i=int(node['left'] if left else node['right'])
    return route


def names():
    out=[]
    for code in ('86510000','86472000','86472600','86500000'):
        out += [code+':H']+[code+f':dH{h}' for h in (.5,1,2,4,8)]
    for plant in ('julho','monte','castro'):
        out += [plant+':Q06',plant+':Q',plant+':I']+[plant+f':dQ{h}' for h in (1,2,4,8)]
    for group in ('Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas'):
        for w in (1,3,6,12,24,48): out += [group+f':P{w}',group+f':C{w}']
        out += [group+f':P3lag{h}' for h in (3,6,12)]
    for model in ('gfs_seamless','ecmwf_ifs025','icon_global'):
        for loc in range(5):
            out += [model+f':location{loc}:P{h}' for h in (3,6,9,12)]
    assert len(out)==180
    return out


def main():
    paths=[REF/'features.npz',NEW/'features.npz',RUN/'training-masks.npz',RUN/'predictions.csv',
           REF/'models/test-candidate-12.joblib',RUN/'models/test-12.joblib']
    for p in paths:
        parent=REF if p.is_relative_to(REF) else NEW if p.is_relative_to(NEW) else RUN
        m=json.loads((parent/'artifact-hashes.json').read_text())
        assert sha(p)==next(r['sha256'] for r in m if r['file']==str(p.relative_to(parent)))
    d=dict(np.load(paths[0]));n=dict(np.load(paths[1]));masks=dict(np.load(paths[2]))
    oldmask=masks['test_original_h12'];newmask=masks['new_h12']
    target=np.r_[d['truth'][12:],np.full(12,np.nan)]
    ntarget=np.r_[n['truth'][12:],np.full(12,np.nan)]
    delta=target-d['base'];ndelta=ntarget-n['base']
    original_max=float(delta[oldmask].max());assert original_max==8.09
    candidate=read(paths[3])
    selected=[r for r in candidate if r['phase']=='test' and r['nominal_lead_h']=='12' and r['actual_m'] and r['base_m'] and float(r['actual_m'])-float(r['base_m'])>original_max]
    assert len(selected)==12
    index={iso(t):i for i,t in enumerate(d['times'])}
    ix=np.array([index[r['origin']] for r in selected]); query=d['features'][ix]
    nf=n['features'][newmask];oldf=d['features'][oldmask]
    responses=np.r_[ndelta[newmask],delta[oldmask]]
    levels=np.r_[ntarget[newmask],target[oldmask]]
    weights=1+2*(abs(responses)>=1)+2*(levels>=9)
    augmented=np.vstack([nf,oldf]); extreme=responses>original_max
    assert extreme.sum()==7 and extreme[:len(nf)].sum()==7
    added_rows=[]
    for i in np.flatnonzero(newmask&(ndelta>original_max)):
        added_rows.append(dict(origin=iso(n['times'][i]),base_m=float(n['base'][i]),target_m=float(ntarget[i]),
            response_m=float(ndelta[i]),mucum_dH1=float(n['features'][i,2]),mucum_dH4=float(n['features'][i,4])))
    save('added-extremes.csv',added_rows)
    summary_rows=[];tree_rows=[];divergences=Counter();features=names();reproduction=[]
    for family,p,fit in [('native_control',paths[4],oldf),('augmented',paths[5],augmented)]:
        model=joblib.load(p);manual=np.full(len(query),float(model._baseline_prediction[0,0]))
        for tree_no,trees in enumerate(model._predictors):
            nodes=trees[0].nodes
            fit_leaf=leaves(nodes,fit);q_leaf=leaves(nodes,query)
            counts=np.bincount(fit_leaf,minlength=len(nodes))
            leafmask=nodes['is_leaf'].astype(bool)
            np.testing.assert_array_equal(counts[leafmask],nodes['count'][leafmask])
            manual+=nodes['value'][q_leaf]
            for j,node in enumerate(q_leaf):
                support=fit_leaf==node
                record=dict(family=family,origin=selected[j]['origin'],tree=tree_no,leaf=int(node),
                    leaf_delta_contribution_m=float(nodes['value'][node]),training_rows=int(support.sum()))
                if family=='augmented':
                    record.update(added_2024_rows=int(support[:len(nf)].sum()),
                        extreme_2024_rows=int((support&extreme).sum()),
                        extreme_weight_fraction=float(weights[support&extreme].sum()/weights[support].sum()))
                    qpath=path(nodes,query[j])
                    for example in np.flatnonzero(extreme):
                        epath=path(nodes,fit[example])
                        for a,b in zip(qpath,epath):
                            assert a[0]==b[0]
                            if a[2]!=b[2]:
                                divergences[a[1]]+=1
                                break
                tree_rows.append(record)
        prediction=manual+d['base'][ix]
        actual=model.predict(query)+d['base'][ix]
        np.testing.assert_allclose(prediction,actual,atol=1e-12,rtol=0)
        expected=np.array([float(r[family+'_m']) for r in selected])
        np.testing.assert_array_equal(actual,expected)
        reproduction.append(dict(family=family,trees=len(model._predictors),maximum_manual_error_m=float(abs(actual-prediction).max()),
                                 training_rows=len(fit),all_leaf_memberships_reproduced=True))
        for j,r in enumerate(selected):
            related=[s for s in tree_rows if s['family']==family and s['origin']==r['origin']]
            q=dict(family=family,origin=r['origin'],target_time=r['target_time'],base_m=float(r['base_m']),
                actual_m=float(r['actual_m']),forecast_m=float(actual[j]),error_m=float(actual[j])-float(r['actual_m']),
                actual_response_m=float(r['actual_m'])-float(r['base_m']),
                predicted_response_m=float(manual[j]),initial_response_m=float(model._baseline_prediction[0,0]),
                tree_contribution_sum_m=float(manual[j]-model._baseline_prediction[0,0]))
            if family=='augmented':
                q.update(trees_sharing_any_2024_extreme=sum(s['extreme_2024_rows']>0 for s in related),
                    mean_extreme_weight_fraction=float(np.mean([s['extreme_weight_fraction'] for s in related])),
                    median_training_rows_same_leaf=float(np.median([s['training_rows'] for s in related])))
            summary_rows.append(q)
    def flexible_save(name,rows):
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with (OUT/name).open('w') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    flexible_save('case-support.csv',summary_rows);flexible_save('tree-support.csv',tree_rows)
    ds=[dict(column=j,feature=features[j],first_divergences=count) for j,count in divergences.most_common()]
    save('first-divergences.csv',ds)
    lower=min(float(r['base_m']) for r in selected);upper=max(float(r['base_m']) for r in selected)
    matched_old=oldmask&(d['base']>=lower)&(d['base']<=upper)
    matched_new=newmask&(n['base']>=lower)&(n['base']<=upper)
    conditional=dict(base_lower_m=lower,base_upper_m=upper,
        original_pairs=int(matched_old.sum()),added_pairs=int(matched_new.sum()),
        original_max_response_m=float(delta[matched_old].max()),added_max_response_m=float(ndelta[matched_new].max()),
        combined_max_response_m=float(max(delta[matched_old].max(),ndelta[matched_new].max())),
        posthoc_descriptive_range=True)
    report=dict(original_training_max_response_m=original_max,added_extreme_count=7,test_case_count=12,
        added_extreme_base_range_m=[min(r['base_m'] for r in added_rows),max(r['base_m'] for r in added_rows)],
        selected_test_base_range_m=[min(float(r['base_m']) for r in selected),max(float(r['base_m']) for r in selected)],
        reproduction=reproduction,conditional_response=conditional,input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},
        first_divergences=ds,causal_attribution_established=False,trained=False,promoted=False,goal_achieved=False)
    (OUT/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Suporte dos novos exemplos extremos nas árvores RADAR','',
        'Diagnóstico dos modelos congelados de12h. Os12 casos foram selecionados depois dos resultados por resposta observada acima do máximo original de treino(8,09m). Não é novo teste, ajuste, ablação ou prova causal.','',
        f"Os sete exemplos novos de2024 acima desse máximo partem de níveis entre{report['added_extreme_base_range_m'][0]:.2f} e{report['added_extreme_base_range_m'][1]:.2f}m. Os12 casos posteriores partem de{report['selected_test_base_range_m'][0]:.2f} a{report['selected_test_base_range_m'][1]:.2f}m. As faixas não se sobrepõem: ampliar a resposta máxima de treino não garante cobrir a combinação de nível inicial e subida rápida.",'',
        '| Origem | Base(m) | Resposta real(m) | Resposta prevista(m) | Árvores que compartilham folha com algum extremo2024 | Fração média do peso desses exemplos na folha |',
        '|---|---:|---:|---:|---:|---:|']
    for r in summary_rows:
        if r['family']=='augmented':
            lines.append(f"| {r['origin']} | {r['base_m']:.2f} | {r['actual_response_m']:.2f} | {r['predicted_response_m']:.4f} | {r['trees_sharing_any_2024_extreme']}/180 | {r['mean_extreme_weight_fraction']:.4%} |")
    lines+=['',
        f"Restringindo descritivamente a base ao intervalo posterior de{lower:.2f}–{upper:.2f}m, há{conditional['original_pairs']} pares originais e{conditional['added_pairs']} novos. A resposta máxima original é{conditional['original_max_response_m']:.2f}m e a nova é{conditional['added_max_response_m']:.2f}m: a máxima combinada permanece{conditional['combined_max_response_m']:.2f}m. Esse intervalo foi escolhido depois de examinar os casos; não é um filtro de treino ou avaliação.",
        '','## O que a inspeção comprova','',
        'A soma da resposta inicial com os180 valores de folhas reproduz a inferência de cada modelo. O roteamento manual de todas as amostras de treino reproduz exatamente as contagens de todas as folhas nas360 árvores. Nenhum modelo foi retreinado.','',
        'first-divergences.csv conta o primeiro corte que separa cada caso posterior de cada um dos sete exemplos2024, em cada árvore do candidato. Não é importância causal de variável, SHAP ou demonstração de que mudar esse campo reduziria o erro. Folhas do boosting aprendem correções residuais; a fração de exemplos extremos em uma folha não é o peso final da previsão.','',
        'Os erros continuam no conjunto. Nenhum valor de2024 foi deslocado, nenhuma variável foi modificada para forçar similaridade, e nenhum período virou holdout. A hipótese de falta de exemplos em regimes comparáveis orienta pesquisa adicional, sem resolver datum, geometria, sensores ou disponibilidade histórica.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('first_divergences','input_sha256')},indent=2))
    print(ds[:8])


if __name__=='__main__':
    with threadpool_limits(limits=2): main()
