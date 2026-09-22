import csv,hashlib,json
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
PRIOR=ROOT/'outputs/experimento-proxy-carreiro-20260921'

def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
meta=json.loads((OUT/'experiment.json').read_text())
for name,expected in meta['input_sha256'].items():assert sha(Path(name))==expected
old=rows(PRIOR/'predictions.csv');new=rows(OUT/'predictions.csv');assert len(old)==len(new)==23538
unchanged=0;missing_targets_updated=0
for x,y in zip(old,new):
    for k in ['origin','target_time','anchor_at','actual_m','modeled_car_history_inputs','modeled_car_future_inputs','uses_missing_flow_proxy']:
        assert x[k]==y[k],k
    if x['julho_levels_m']:
        assert float(x['julho_levels_m'])==float(y['julho_levels_m']);unchanged+=1
    else:assert not y['julho_levels_m']
    if x['status']=='missing_exact_target' and y['julho_levels_rain_m']:missing_targets_updated+=1
assert unchanged==23250 and missing_targets_updated==147
transitions=[]
for h in range(1,13):
    for high in [False,True]:
        selected=[r for r in new if r['nominal_lead_h']==str(h) and r['actual_m'] and (not high or float(r['actual_m'])>=7)]
        c=Counter()
        for r in selected:
            if not r['julho_levels_m'] or not r['julho_levels_rain_m']:c['unpaired']+=1;continue
            actual=float(r['actual_m']);oldhit=abs(float(r['julho_levels_m'])-actual)<=.5;newhit=abs(float(r['julho_levels_rain_m'])-actual)<=.5
            c['kept_hit' if oldhit and newhit else 'lost_hit' if oldhit else 'gained_hit' if newhit else 'both_miss']+=1
        transitions.append(dict(nominal_lead_h=h,subset='level_ge_7m' if high else 'all',observed_targets=len(selected),**{k:c[k] for k in ['kept_hit','lost_hit','gained_hit','both_miss','unpaired']}))
with (OUT/'hit-transitions.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(transitions[0]));w.writeheader();w.writerows(transitions)
evaluation=rows(OUT/'evaluation.csv');old_eval=rows(PRIOR/'evaluation.csv');maxmetricdiff=0.
for r in evaluation:
    if r['family']!='julho_levels' or r['population']!='all_available':continue
    ref=next(s for s in old_eval if all(s[k]==r[k] for k in ['nominal_lead_h','subset','family']))
    for key in ['paired_n','observed_targets','forecast_failures_with_truth','within_0_50_n']:assert r[key]==ref[key]
    for key in ['mae_m','bias_m','coverage','within_0_50_fraction','p90_abs_m','p98_abs_m','max_abs_m']:maxmetricdiff=max(maxmetricdiff,abs(float(r[key])-float(ref[key])))
assert maxmetricdiff<1e-12
dump('verification.json',dict(input_hashes_verified=len(meta['input_sha256']),identical_origin_target_rows=len(new),unchanged_baseline_finite_values=unchanged,missing_target_forecasts_also_updated=missing_targets_updated,baseline_metric_max_difference=maxmetricdiff,tests_passed=101,goal_achieved=False))
dump('decision.json',dict(promoted=False,live_issuance=False,goal_achieved=False,decision='Do not promote the forecast-rain candidate to the hourly stage forecast.',reason='At12h the high-water mean absolute error decreases slightly but hits within0.50m fall from71/235 to67/235. Overall hits also fall1159/1914 to1151/1914. The user accuracy objective is not improved consistently across horizons. This remains inspected historical development, not independent or prospective proof.'))
lines=['# Efeito da chuva prevista no nível de Muçum','','**O ganho de vazão não melhorou a métrica principal do nível. O candidato não foi promovido.**','','A comparação troca apenas a vazão futura prevista de Julho, mantendo Carreiro e suas entradas estimadas, chuva/escoamento local HGE, pesos de propagação, curva vazão–nível, correção residual e âncora. Foram mantidas as 23.538 linhas originais e todos os valores anteriores. Os 23.103 pares válidos e as exclusões são os mesmos.','','## Comparação dos níveis','','Acerto = erro absoluto de no máximo 0,50 m. Todos os prazos estão em `evaluation.csv`; os exemplos abaixo não substituem a avaliação completa.','','| Prazo | Recorte | Modelo | Pares | Acertos | MAE |','|---|---|---|---:|---:|---:|']
for r in evaluation:
    if r['population']=='all_available' and int(r['nominal_lead_h']) in [1,6,12]:lines.append(f"| {r['nominal_lead_h']} h | {r['subset']} | {r['family']} | {r['paired_n']} | {r['within_0_50_n']} ({100*float(r['within_0_50_fraction']):.2f}%) | {float(r['mae_m']):.3f} m |")
lines+=['','Em 12 h nas cheias, o erro médio cai de 1,375 para 1,359 m e o máximo de 9,038 para 8,323 m. Contudo, os acertos caem de 71 para 67 entre 235 pares (30,21%→28,51%). No conjunto geral de 12 h, a taxa cai de 60,55% para 60,14%. A cobertura não mudou.','','## Transições de acerto nas cheias','','| Prazo | Acertos perdidos | Acertos novos | Falhas de previsão com alvo |','|---|---:|---:|---:|']
for r in transitions:
    if r['subset']=='level_ge_7m':lines.append(f"| {r['nominal_lead_h']} h | {r['lost_hit']} | {r['gained_hit']} | {r['unpaired']} |")
lines+=['','## Verificação e limites','','A atualização inverte a curva monotônica no nível anterior, acrescenta somente a diferença de vazão futura propagada e reaplica a mesma curva/offset. Pesos com lag mínimo de 1 h garantem que as âncoras de origem e origem−1 h não dependem dessa troca. Entram corretamente leads de Julho 0…11; não foram usadas vazões futuras observadas.','','Os modelos de vazão congelados foram reproduzidos; a inversão/reconversão tem erro máximo de 7,11e-15 m. As 147 previsões com alvo ausente também foram atualizadas, sem inventar alvos. As 288 falhas de âncora permanecem. Vazão total negativa produziria falha explícita; nenhuma foi encontrada. A referência preservada reproduz suas métricas sem diferença.','','A suíte passou 101 testes, incluindo equivalência com cálculo direto da curva, índices de propagação, preservação de ausências e falhas no denominador. A disponibilidade histórica das previsões meteorológicas continua presumida, e a distribuição do arquivo não equivale à previsão operacional mais recente. Não há prova prospectiva, independente ou de 98% de acertos.','']
(OUT/'report.md').write_text('\n'.join(lines))
independent=ROOT/'outputs/verificacao-integral-chuva-mucum-20260921'
if (independent/'verification.json').exists():
    check=json.loads((independent/'verification.json').read_text())
    assert check['passed'] and check['rows_per_family']==72
    for path,expected in check['comparison_inputs_sha256'].items():assert sha(Path(path))==expected
    dump('independent-replay.json',dict(verification=check,source=str(independent),verification_sha256=sha(independent/'verification.json'),computation_sha256=sha(independent/'computation.json'),scope='Six selected origins, all12 horizons, two families; not a replay of every historical origin.'))
    with (OUT/'report.md').open('a') as f:
        f.write('\n## Repetição integral independente\n\nUma implementação separada recalculou o estado HGE, chuva futura, todas as vazões propagadas, âncora, residual e curva em seis origens, sem usar a inversão dos níveis. Foram comparados 72 níveis por família (144 comparações), todos dentro da tolerância de 1e-8 m; diferença máxima 7,11e-15 m. As origens incluem cheias e entradas estimadas do Carreiro. Os demais pontos têm a verificação algébrica e os hashes, mas não esta repetição integral. Evidências em `../verificacao-integral-chuva-mucum-20260921/verification.json`. Isso confirma a implementação, não a precisão hidrológica.\n')
log=Path('/tmp/radar-downstream-rain.log')
if log.exists() and not (OUT/'execution.log').exists():log.rename(OUT/'execution.log')
dump('artifact-hashes.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json'})
print(json.dumps({'unchanged_baseline_values':unchanged,'metric_difference':maxmetricdiff,'12h_flood_transitions':transitions[-1]}))
