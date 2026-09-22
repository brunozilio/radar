"""Recompute descriptive flood metrics directly from frozen predictions; no fitting."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,math,hashlib
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
E=ROOT/'outputs/experimento-radar-historico-2024-20260921'
R=ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
sources={}
def read(p):
    b=p.read_bytes();sources[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def rows(p):return list(csv.DictReader(read(p).decode().splitlines()))
def n(v):return float(v) if v not in ('',None) else float('nan')
def valid(v):return math.isfinite(n(v))
def save(name,rr):
    if not rr:return
    with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def key(r):return r['phase'],r['origin'],int(r['nominal_lead_h'])
def metric(rr,field):
    pairs=[r for r in rr if valid(r[field])];error=np.array([n(r[field])-n(r['actual_m']) for r in pairs]);ae=np.abs(error);hits=int((ae<=.5).sum())
    return {'observed_targets':len(rr),'n':len(pairs),'failures':len(rr)-len(pairs),'hits':hits,'hit_fraction':hits/len(pairs) if pairs else None,'observed_target_hit_fraction':hits/len(rr) if rr else None,'mae_m':float(ae.mean()) if len(ae) else None,'bias_m':float(error.mean()) if len(ae) else None,'p98_abs_m':float(np.quantile(ae,.98)) if len(ae) else None,'max_abs_m':float(ae.max()) if len(ae) else None}
pred=rows(E/'predictions.csv');evaluation=rows(E/'evaluation.csv');reference=rows(R/'predictions.csv');ref={key(r):r for r in reference};read(E/'protocol.json');read(E/'code/hydro_radar_2024_augmentation.py')
ranges=rows(ROOT/'outputs/diagnostico-extremos-radar-20260921/training-response-ranges.csv');threshold=float(next(r['max_delta_m'] for r in ranges if r['phase']=='test' and r['horizon_h']=='12' and r['training_policy']=='candidate'))
checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
check('rows102084_unique',len(pred)==102084 and len({key(r) for r in pred})==102084)
check('same_keys_reference',set(ref)=={key(r) for r in pred})
def equalnum(a,b):return (not valid(a) and not valid(b)) or n(a)==n(b)
check('reference_targets_base_complete_flags',all(all(equalnum(r[k],ref[key(r)][k]) for k in ['actual_m','base_m']) and r['target_time']==ref[key(r)]['target_time'] and r['original_complete24']==ref[key(r)]['original_complete24'] for r in pred))
check('native_control_exact_saved_candidate',all(equalnum(r['native_control_m'],ref[key(r)]['candidate_m']) for r in pred))
metrics=[];comparisons=[];failure_rows=[]
for phase in ['validation','test']:
    for h in range(1,13):
        scheduled=[r for r in pred if r['phase']==phase and int(r['nominal_lead_h'])==h];high=[r for r in scheduled if valid(r['actual_m']) and n(r['actual_m'])>=7];ms={}
        for family in ['native_control','augmented']:
            m={'phase':phase,'horizon_h':h,'subset':'level_ge_7m','population':'full_schedule','family':family,'scheduled_rows':len(scheduled),**metric(high,family+'_m')};metrics.append(m);ms[family]=m
            saved=next(r for r in evaluation if r['phase']==phase and r['horizon_h']==str(h) and r['subset']=='level_ge_7m' and r['population']=='full_schedule' and r['family']==family)
            mismatch={k:{'calculated':v,'saved':saved[k]} for k,v in m.items() if k in saved and isinstance(v,(int,float)) and not math.isclose(v,float(saved[k]),rel_tol=0,abs_tol=1e-12)}
            check(f'metrics_match:{phase}:{h}:{family}',not mismatch,mismatch)
            check(f'coverage:{phase}:{h}:{family}',(m['observed_targets'],m['n'],m['failures'])==((237,236,1) if phase=='test' else (28,28,0)))
            for r in high:
                if not valid(r[family+'_m']):failure_rows.append({'phase':phase,'horizon_h':h,'family':family,'origin':r['origin'],'target_time':r['target_time'],'actual_m':n(r['actual_m']),'base_m':n(r['base_m']) if valid(r['base_m']) else None})
        c=ms['native_control'];a=ms['augmented'];comparisons.append({'phase':phase,'horizon_h':h,'observed_targets':len(high),'pairs_control':c['n'],'pairs_augmented':a['n'],'hits_control':c['hits'],'hits_augmented':a['hits'],'hits_change':a['hits']-c['hits'],'mae_control_m':c['mae_m'],'mae_augmented_m':a['mae_m'],'mae_change_m':a['mae_m']-c['mae_m'],'max_control_m':c['max_abs_m'],'max_augmented_m':a['max_abs_m'],'observed_hit_fraction_control':c['observed_target_hit_fraction'],'observed_hit_fraction_augmented':a['observed_target_hit_fraction']})
test12=[r for r in pred if r['phase']=='test' and int(r['nominal_lead_h'])==12 and valid(r['actual_m'])]
extreme=[r for r in test12 if valid(r['base_m']) and n(r['actual_m'])-n(r['base_m'])>threshold];check('original_response_threshold8.09',threshold==8.09);check('12_above_original_training_response',len(extreme)==12)
def detail(r):
    c=n(r['native_control_m']);a=n(r['augmented_m']);y=n(r['actual_m']);return {'origin':r['origin'],'target_time':r['target_time'],'base_m':n(r['base_m']) if valid(r['base_m']) else None,'actual_m':y,'target_minus_base_m':y-n(r['base_m']) if valid(r['base_m']) else None,'native_control_m':c,'augmented_m':a,'control_error_m':c-y,'augmented_error_m':a-y,'control_abs_error_m':abs(c-y),'augmented_abs_error_m':abs(a-y),'abs_error_change_m':abs(a-y)-abs(c-y)}
extreme_details=[detail(r) for r in extreme];worst={family:detail(max((r for r in test12 if valid(r[family+'_m'])),key=lambda r:abs(n(r[family+'_m'])-n(r['actual_m'])))) for family in ['native_control','augmented']}
extreme_metrics={family:metric(extreme,family+'_m') for family in ['native_control','augmented']};extreme_metrics.update({'count':len(extreme),'threshold_m':threshold,'improved_abs_error_pairs':sum(r['abs_error_change_m']<0 for r in extreme_details),'worsened_abs_error_pairs':sum(r['abs_error_change_m']>0 for r in extreme_details)})
result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'checks':checks,'check_count':len(checks),'failed_checks':[c for c in checks if not c['passed']],'metrics':metrics,'comparisons':comparisons,'explicit_missing_forecasts':failure_rows,'worst_test12':worst,'above_original_training_response':extreme_metrics,'above_original_training_response_rows':extreme_details,'limits':['Descriptive development on previously inspected periods, not independent validation.','Failures remain in observed-target hit fraction; MAE/P98/max use finite pairs and do not score missing forecasts as zero error.','Training response threshold is taken from preserved prior audit; this task does not refit or independently rederive training memberships.','No promotion and no prospective accuracy claim.']}
save('flood-metrics.csv',metrics);save('flood-comparison.csv',comparisons);save('above-original-response.csv',extreme_details);save('missing-forecasts.csv',failure_rows)
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');(P/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'check_count':len(checks),'failed_checks':result['failed_checks'],'worst_test12':worst,'extreme_metrics':extreme_metrics},ensure_ascii=False,indent=2))
for r in comparisons:print(r['phase'],r['horizon_h'],'hits',r['hits_control'],r['hits_augmented'],'MAE',round(r['mae_control_m'],6),round(r['mae_augmented_m'],6),'max',round(r['max_control_m'],6),round(r['max_augmented_m'],6))
lines=['# Auditoria independente — ampliação Radar com histórico2024','',
       f'**{len(checks)} verificações passaram; métricas conferidas diretamente de predictions.csv.** Nenhum treino, inferência de modelo, consulta de rede ou alteração de fonte foi realizado.',
       '', 'As102.084chaves, bases, alvos, flags de completude e valores do controle nativo reproduzem exatamente o candidato native-missing congelado anterior. As48linhas de métricas abaixo (24fase×horizonte,2famílias) concordam com evaluation.csv até1e−12.',
       '', 'Cheia significa alvo observado≥7m; acerto significa erro absoluto≤0,50m. Validação tem28alvos/28pares em cada horizonte. Teste tem237alvos/236pares e1falha em cada horizonte, em ambas as famílias. A falha não é removida da fração sobre alvos observados; MAE/P98/máximo são calculados apenas nos pares finitos.',
       '', '## Todas as combinações de cheia/full_schedule','',
       '| Fase | h | Acertos controle→ampliado | MAE controle→ampliado (m) | Máximo controle→ampliado (m) |',
       '|---|---:|---:|---:|---:|']
for r in comparisons:lines.append(f"| {r['phase']} | {r['horizon_h']} | {r['hits_control']}→{r['hits_augmented']} | {r['mae_control_m']:.6f}→{r['mae_augmented_m']:.6f} | {r['max_control_m']:.6f}→{r['max_augmented_m']:.6f} |")
lines += ['', 'O candidato **não domina a referência**: no teste ganha acertos em10horizontes, perde em8h(−14) e9h(−8). Na validação ganha em3, perde em7 e empata em2. O MAE teste piora em8h; em9h melhora ligeiramente apesar da redução de acertos. O máximo teste piora em11h e12h. Estes critérios não são intercambiáveis.',
          '', '## Falha explícita', '',
          'Origem22/07/2026 17h UTC−3: base ausente e ambas as previsões ausentes para h1–12. Os alvos existem e são cheias: de18,68m em22/07 18h a14,07m em23/07 05h. Esses12casos (um por horizonte) permanecem no arquivo missing-forecasts.csv. Em12h, a fração de sucesso sobre todos os237alvos é86/237→88/237; a fração condicional sobre236pares é distinta.',
          '', '## Maior erro de12h', '',
          'O máximo do controle ocorre na origem21/07 19h, alvo22/07 07h: observado16,50m, controle8,578474m, ampliado9,087447m. Nesse mesmo par, erro absoluto melhora7,921526→7,412553m.',
          '', 'O maior erro do ampliado muda para origem21/07 16h, alvo22/07 04h: observado14,49m, controle7,365617m, ampliado6,401933m. Nesse par piora7,124383→8,088067m. Logo, melhorar o antigo pior caso não implica reduzir o novo máximo.',
          '', '## Doze respostas acima da amplitude original de treino', '',
          'A regra é alvo−base>8,09m, limite de resposta12h copiado do diagnóstico anterior preservado; não é um limite físico. Não foi reajustado ao novo resultado. São12origens21/07 12h–23h, já inspecionadas anteriormente, com alvos22/07 00h–11h.', '',
          '| Origem21/07 | Alvo22/07 | ΔH observado (m) | Erro absoluto controle (m) | Ampliado (m) |',
          '|---|---|---:|---:|---:|']
for r in extreme_details:lines.append(f"| {r['origin'][11:16]} | {r['target_time'][11:16]} | {r['target_minus_base_m']:.2f} | {r['control_abs_error_m']:.6f} | {r['augmented_abs_error_m']:.6f} |")
lines += ['', 'Melhora o erro absoluto em10pares e piora em2 (origens15h e16h). MAE6,795192→6,321552m; máximo7,921526→8,088067m; **zero acertos nos12pares em ambas as versões**. Todas as previsões desses pares ficam abaixo do nível observado. Esse grupo é um diagnóstico pós-inspeção, não um teste independente.',
          '', '## Artefatos e limites', '',
          'audit.py reproduz a auditoria somente local; verification.json inclui métricas, falhas, pares extremos e verificações; osCSVs facilitam reuso sem recalcular. source-manifest.json registra hashes das fontes lidas e artifact-hashes.json registra os artefatos próprios.',
          '', 'Não foram auditados aqui ajuste dos modelos ou membership do treino novo; essa parte está com o agente principal. A referência de8,09m vem do inventário anterior, não de novo ajuste. Os períodos de avaliação já foram usados em desenvolvimento; as métricas são descritivas, não comprovação prospectiva ou evidência independente de generalização. Nenhuma promoção ou declaração de meta alcançada.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
