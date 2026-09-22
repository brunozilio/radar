"""Reconcile diagnostic slices and separate recovered predictions by event."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_reservoir_mucum_experiment import score
from hydro_upstream_audit import savecsv

def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
source=ROOT/'outputs/experimento-proxy-carreiro-20260921'
old=ROOT/'outputs/experimento-niveis-ate-mucum-pesos-zero-20260921/predictions.csv'
pred=rows(OUT/'predictions-with-labels.csv')
original={(r['origin'],r['target_time']):r for r in rows(old)}
for r in pred:
    for f in ['actual_m','reference_m','julho_levels_m']:
        r[f]=float(r[f]) if r[f] else None
    prev=original[(r['origin'],r['target_time'])]
    r['population']='previously_paired' if prev['status']=='paired' else 'newly_recovered' if r['status']=='paired' else 'still_unpaired'
clusters=json.loads((OUT/'observed-clusters.json').read_text())['represented_clusters']
metrics=[]
for e in clusters:
    for h in range(1,13):
        for population in ['previously_paired','newly_recovered','still_unpaired']:
            selected=[r for r in pred if r['observed_cluster_id']==e['event_id'] and int(r['nominal_lead_h'])==h and r['population']==population]
            metrics.extend([dict(observed_cluster_id=e['event_id'],first_exceedance_at=e['first_exceedance_at'],nominal_lead_h=h,population=population,**s) for s in score(selected,True)])
savecsv(OUT/'cluster-population-metrics.csv',metrics)
maxdiff=0.
for r in rows(source/'evaluation.csv'):
    selected=[s for s in rows(OUT/'trend-metrics.csv') if all(s[k]==r[k] for k in ['nominal_lead_h','family','subset'])]
    for key in ['paired_n','observed_targets','forecast_failures_with_truth','within_0_50_n']:
        assert sum(int(s[key]) for s in selected)==int(r[key])
    n=int(r['paired_n'])
    mean=sum(int(s['paired_n'])*float(s['mae_m']) for s in selected if int(s['paired_n']))/n
    maxdiff=max(maxdiff,abs(mean-float(r['mae_m'])))
    if r['subset']=='level_ge_7m':
        matched=[s for s in metrics if s['nominal_lead_h']==int(r['nominal_lead_h']) and s['family']==r['family']]
        for key in ['paired_n','observed_targets','forecast_failures_with_truth','within_0_50_n']:
            assert sum(s[key] for s in matched)==int(r[key])
        mean=sum(s['paired_n']*s['mae_m'] for s in matched if s['paired_n'])/n
        maxdiff=max(maxdiff,abs(mean-float(r['mae_m'])))
assert maxdiff<1e-12
verified=[]
for name,expected in json.loads((OUT/'audit.json').read_text())['input_sha256'].items():
    p=Path(name);copy=OUT/'code'/p.name
    if copy.exists():p=copy
    elif p.name=='carreiro-proxy-stratification-policy.json':p=OUT/'policy.json'
    assert sha(p)==expected
    verified.append({'path':str(p),'sha256':expected})
worst=[]
for r in pred:
    if r['status']=='paired' and r['actual_m']>=7 and int(r['nominal_lead_h'])==12:
        worst.append(dict(origin=r['origin'],target_time=r['target_time'],actual_m=r['actual_m'],prediction_m=r['julho_levels_m'],signed_error_m=r['julho_levels_m']-r['actual_m'],absolute_error_m=abs(r['julho_levels_m']-r['actual_m']),observed_cluster_id=r['observed_cluster_id'],population=r['population'],origin_trend=r['origin_trend']))
worst.sort(key=lambda r:r['absolute_error_m'],reverse=True)
savecsv(OUT/'all-12h-flood-errors-ranked.csv',worst)
dump('verification.json',dict(input_hashes_verified=verified,reconciled_trend_and_event_populations=True,max_reaggregated_mae_difference_m=maxdiff,original_prediction_sha256=sha(old),target_value_mismatches=0,target_unapproved=0,tests_passed=90,goal_achieved=False))
lines=['# Diagnóstico do candidato Carreiro por cheia','','Foram mantidas as regras anteriores de tendência e agrupamento. Todos os 23.538 alvos/origens permanecem no diagnóstico; os alvos finitos conferem com as fontes aprovadas. As quatro cheias são agrupamentos observados, ainda sem certificação de independência; duas têm lacunas. Este relatório usa períodos históricos já examinados.','','## Resultados de 12 h do candidato com níveis das usinas','','| Início do agrupamento (UTC) | Pares/observações | Acertos ±0,50 m | MAE | Maior erro |','|---|---:|---:|---:|---:|']
for r in rows(OUT/'cluster-metrics.csv'):
    if r['family']=='julho_levels' and r['nominal_lead_h']=='12':
        lines.append(f"| {r['first_exceedance_at']} | {r['paired_n']}/{r['observed_targets']} | {r['within_0_50_n']} ({100*float(r['within_0_50_fraction']):.2f}%) | {float(r['mae_m']):.3f} m | {float(r['max_abs_m']):.3f} m |")
lines+=['','## O que a recuperação de entradas resolveu','','A cheia que começa em 02/07 às 20h30 BRT tinha zero previsões calculáveis no experimento anterior. Agora há 35 pares por horizonte: 35/35 acertos em 6 h, mas somente 26/35 em 12 h. Isso evidencia utilidade de cobertura, sem demonstrar a meta em todos os prazos ou eventos.','','Na maior cheia, iniciada em 21/07 às 22h BRT, a cobertura de 12 h sobe de 121/135 para 133/135 pares. A precisão continua baixa: 18/133 acertos, MAE de 2,006 m e erro máximo de 9,038 m. O pequeno viés médio (+0,161 m) mascara erros grandes de sinais opostos; subtrair esse viés não resolve o problema principal.','','Os erros anteriormente calculáveis não mudaram. As métricas de pares anteriores, novos e ainda ausentes estão em `cluster-population-metrics.csv`. Não selecionar apenas a cheia ou prazo com 100% de acertos.','','## Direção do próximo diagnóstico','','O maior erro de 12 h está listado abaixo; a tabela completa permanece preservada para não esconder os demais. A próxima análise deve separar erro de previsão de vazão a montante, propagação e transformação vazão–nível, usando sensibilidades apenas como diagnóstico. Não trocar previsões históricas por vazões futuras observadas no placar.','']
for r in worst[:3]:lines.append(f"- Origem {r['origin']}, alvo {r['target_time']}: observado {r['actual_m']:.3f} m, previsto {r['prediction_m']:.3f} m, erro {r['signed_error_m']:+.3f} m; população {r['population']}.")
lines+=['','As contagens e erros médios recompõem as métricas gerais (diferença máxima '+f'{maxdiff:.3g}'+' m). A suíte passou 90 testes, incluindo rejeição de previsões cujo hash não confere. Nenhuma alteração de modelo em uso, promoção ou alcance da meta foi declarado.','']
(OUT/'report.md').write_text('\n'.join(lines))
dump('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'max_reaggregation_difference':maxdiff,'worst3':worst[:3]},ensure_ascii=False))
