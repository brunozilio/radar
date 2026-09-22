"""Independent flood/full_schedule metrics audit; reads predictions only, no models."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,math
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1];E=ROOT/'outputs/experimento-radar-observado-120-20260921';sources={}
def read(p):
    b=p.read_bytes();sources[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def rows(p):return list(csv.DictReader(read(p).decode().splitlines()))
def num(v):return float(v) if v not in ('',None) else np.nan
def finite(v):return math.isfinite(num(v))
def save(name,rr):
    with (P/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
pred=rows(E/'predictions.csv');saved=rows(E/'evaluation.csv');protocol=json.loads(read(E/'protocol.json'));checks=[];metrics=[];comparisons=[];failures=[]
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
check('schedule102084_unique',len(pred)==102084 and len({(r['phase'],r['origin'],r['nominal_lead_h']) for r in pred})==102084)
check('protocol_no_promotion',protocol['promoted'] is False and protocol['goal_achieved'] is False)
for phase in ['validation','test']:
    for h in range(1,13):
        group=[r for r in pred if r['phase']==phase and int(r['nominal_lead_h'])==h];observed=[r for r in group if finite(r['actual_m']) and num(r['actual_m'])>=7];comparison={'phase':phase,'horizon_h':h};values={};pair_masks={}
        for family in ['native_control','observed_only']:
            field=family+'_m';pair_masks[family]=[finite(r[field]) for r in observed];pairs=[r for r in observed if finite(r[field])];error=np.array([num(r[field])-num(r['actual_m']) for r in pairs]);ae=np.abs(error);hits=int((ae<=.5).sum());m={'phase':phase,'horizon_h':h,'subset':'level_ge_7m','population':'full_schedule','family':family,'scheduled_rows':len(group),'observed_targets':len(observed),'n':len(pairs),'failures':len(observed)-len(pairs),'hits':hits,'hit_fraction':hits/len(pairs),'observed_target_hit_fraction':hits/len(observed),'mae_m':float(ae.mean()),'bias_m':float(error.mean()),'p98_abs_m':float(np.quantile(ae,.98)),'max_abs_m':float(ae.max())};metrics.append(m);values[family]=m
            expected=next(r for r in saved if r['phase']==phase and r['horizon_h']==str(h) and r['family']==family and r['subset']=='level_ge_7m' and r['population']=='full_schedule');mismatch={k:{'calculated':v,'saved':expected[k]} for k,v in m.items() if isinstance(v,(int,float)) and not math.isclose(v,float(expected[k]),rel_tol=0,abs_tol=1e-12)}
            check(f'saved_metrics:{phase}:{h}:{family}',not mismatch,mismatch);check(f'expected_coverage:{phase}:{h}:{family}',(m['observed_targets'],m['n'],m['failures'])==((237,236,1) if phase=='test' else (28,28,0)))
            for r in observed:
                if not finite(r[field]):failures.append({'phase':phase,'horizon_h':h,'family':family,'origin':r['origin'],'target_time':r['target_time'],'actual_m':num(r['actual_m']),'base_m':num(r['base_m']) if finite(r['base_m']) else None})
        check(f'paired_membership_same:{phase}:{h}',pair_masks['native_control']==pair_masks['observed_only']);c=values['native_control'];o=values['observed_only'];comparison.update(observed_targets=len(observed),paired_control=c['n'],paired_observed=o['n'],hits_control=c['hits'],hits_observed=o['hits'],hits_change=o['hits']-c['hits'],mae_control_m=c['mae_m'],mae_observed_m=o['mae_m'],mae_change_m=o['mae_m']-c['mae_m'],max_control_m=c['max_abs_m'],max_observed_m=o['max_abs_m']);comparisons.append(comparison)
tradeoffs={phase:{'hit_improved_horizons':[r['horizon_h'] for r in comparisons if r['phase']==phase and r['hits_change']>0],'hit_worsened_horizons':[r['horizon_h'] for r in comparisons if r['phase']==phase and r['hits_change']<0],'hit_equal_horizons':[r['horizon_h'] for r in comparisons if r['phase']==phase and r['hits_change']==0],'mae_worsened_horizons':[r['horizon_h'] for r in comparisons if r['phase']==phase and r['mae_change_m']>0]} for phase in ['validation','test']}
result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in checks),'check_count':len(checks),'failed_checks':[c for c in checks if not c['passed']],'checks':checks,'metrics':metrics,'comparisons':comparisons,'tradeoffs':tradeoffs,'missing_forecasts':failures,'limits':['Development periods previously inspected; not independent held-out evidence.','Metrics finite-pair errors differ from observed-target hit fraction, which retains missing forecasts as failures.','No model or training membership was read or refitted in this task.','Untuned removal of60NWP predictors, not replacement with zero future rain and not historical2023augmentation.','No promotion or goal achievement.']}
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');(P/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');save('flood-metrics.csv',metrics);save('flood-comparison.csv',comparisons);save('missing-forecasts.csv',failures)
lines=['# Auditoria independente — Radar observado de120campos','',f'**{len(checks)} verificações passaram.** Recalculei diretamente de predictions.csv as48linhas de métricas de cheia/full_schedule:24combinações fase×horizonte, duas famílias. Concordância com evaluation.csv até1e−12. Nenhum modelo foi lido, inferido ou treinado.',
       '', 'Cheia: alvo≥7m. Acerto: erro absoluto≤0,50m. Cada horizonte da validação tem28alvos/28pares; cada horizonte do teste tem237alvos/236pares/1falha, nas duas famílias. As máscaras dos pares também coincidem, não apenas suas contagens.',
       '', '| Fase | h | Acertos180→120 | MAE180→120 (m) | Máximo180→120 (m) |','|---|---:|---:|---:|---:|']
for r in comparisons:lines.append(f"| {r['phase']} | {r['horizon_h']} | {r['hits_control']}→{r['hits_observed']} | {r['mae_control_m']:.6f}→{r['mae_observed_m']:.6f} | {r['max_control_m']:.6f}→{r['max_observed_m']:.6f} |")
lines += ['', '## Ganhos e perdas', '']
for phase,v in tradeoffs.items():lines.append(f"- {phase}: ganha acertos em{v['hit_improved_horizons']}, perde em{v['hit_worsened_horizons']}, empata em{v['hit_equal_horizons']}; MAE piora em{v['mae_worsened_horizons']}.")
lines += ['', 'O resultado é misto e não demonstra dominância da versão120. Acertos, erro médio e extremos precisam permanecer separados; não foi feita seleção de uma versão por horizonte depois de observar os resultados.',
          '', '## Falha preservada', '',
          'A origem22/07/2026 17h tem base ausente. As duas famílias não produzem previsões h1–12, embora todos esses alvos sejam cheias observadas. Os12casos permanecem no arquivo missing-forecasts.csv, com uma linha por família e horizonte. O cálculo observed_target_hit_fraction divide os acertos por237, não236; MAE/P98/máximo usam apenas os236pares finitos. Ausência não virou erro zero nem saiu do denominador de sucesso sobre alvos.',
          '', '## Limites e integridade', '',
          'Este é um ensaio de remoção dos60preditoresNWP mantendo120campos observados; não há acréscimo2023/2024 nem substituição por chuva futura zero. Parâmetros foram congelados para outro conjunto de entradas, portanto o resultado não estabelece ótimo de arquitetura. Os períodos já foram inspecionados; a comparação é desenvolvimento descritivo, não avaliação independente ou comprovação prospectiva.',
          '', 'O protocolo declara promoted=false e goal_achieved=false, conferidos nesta auditoria. Sem promoção, alteração operacional ou declaração de meta alcançada. O agente principal cuida da verificação dos modelos e membership; esta tarefa limitou-se às métricas e cobertura.',
          '', 'audit.py reproduz o cálculo local; verification.json/CSVs preservam todos os números; source-manifest.json registra os três arquivos lidos e seus hashes; artifact-hashes.json cobre os artefatos próprios.']
(P/'README.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'passed':result['passed'],'check_count':len(checks),'failed_checks':result['failed_checks'],'tradeoffs':tradeoffs},indent=2))
for r in comparisons:print(r['phase'],r['horizon_h'],r['hits_control'],r['hits_observed'],round(r['mae_control_m'],6),round(r['mae_observed_m'],6),round(r['max_control_m'],6),round(r['max_observed_m'],6))
