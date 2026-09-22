"""Independent metrics audit, no model reads or inference."""
import csv,json,hashlib,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];E=ROOT/'outputs/experimento-radar-historico-2023-20260921';sources={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):sources[str(p.relative_to(ROOT))]=sha(p);return list(csv.DictReader(p.open()))
def num(s):return float(s) if s not in ('',None) else np.nan
def ok(name,condition):checks.append(dict(name=name,passed=bool(condition)));assert condition,name
def save(name,rs):
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
pred=rows(E/'predictions.csv');saved=rows(E/'evaluation.csv');prior=rows(ROOT/'outputs/experimento-radar-observado-120-20260921/predictions.csv');protocol=json.loads((E/'protocol.json').read_text());sources[str((E/'protocol.json').relative_to(ROOT))]=sha(E/'protocol.json')
key=lambda r:(r['phase'],r['origin'],r['nominal_lead_h'])
ok('unique102084keys',len(pred)==102084 and len({key(r) for r in pred})==102084);old={key(r):r for r in prior};ok('same_schedule',set(old)=={key(r) for r in pred})
for r in pred:
 p=old[key(r)];assert r['actual_m']==p['actual_m'] and r['base_m']==p['base_m'] and r['target_time']==p['target_time'];assert (r['observed_control_m']==p['observed_only_m'])
ok('control_targets_base_exact_prior',True);ok('no_promotion',protocol['promoted'] is False and protocol['goal_achieved'] is False)
metrics=[];comparisons=[];failures=[]
for phase in ('validation','test'):
 for h in range(1,13):
  group=[r for r in pred if r['phase']==phase and int(r['nominal_lead_h'])==h];high=[r for r in group if num(r['actual_m'])>=7];mv={};masks={}
  for family in ('observed_control','augmented'):
   pairs=[r for r in high if np.isfinite(num(r[family+'_m']))];masks[family]=[key(r) for r in pairs];err=np.array([num(r[family+'_m'])-num(r['actual_m']) for r in pairs]);a=abs(err);hits=int((a<=.5).sum())
   m=dict(phase=phase,horizon_h=h,subset='level_ge_7m',population='full_schedule',family=family,scheduled_rows=len(group),observed_targets=len(high),n=len(pairs),failures=len(high)-len(pairs),hits=hits,hit_fraction=hits/len(pairs),observed_target_hit_fraction=hits/len(high),mae_m=float(a.mean()),bias_m=float(err.mean()),p98_abs_m=float(np.quantile(a,.98)),max_abs_m=float(a.max()));metrics.append(m);mv[family]=m
   s=next(s for s in saved if s['phase']==phase and s['horizon_h']==str(h) and s['family']==family and s['subset']=='level_ge_7m' and s['population']=='full_schedule')
   ok(f'metrics {phase} {h} {family}',all(math.isclose(v,float(s[k]),rel_tol=0,abs_tol=1e-12) for k,v in m.items() if isinstance(v,(int,float))))
   ok(f'coverage {phase} {h} {family}',(m['observed_targets'],m['n'],m['failures'])==((237,236,1) if phase=='test' else (28,28,0)))
   for r in high:
    if not np.isfinite(num(r[family+'_m'])):failures.append(dict(phase=phase,horizon_h=h,family=family,origin=r['origin'],target_time=r['target_time'],actual_m=r['actual_m'],base_m=r['base_m']))
  ok(f'same_pair_keys {phase} {h}',masks['observed_control']==masks['augmented']);c=mv['observed_control'];a=mv['augmented'];comparisons.append(dict(phase=phase,horizon_h=h,observed_targets=len(high),paired=c['n'],hits_control=c['hits'],hits_augmented=a['hits'],hits_change=a['hits']-c['hits'],mae_control_m=c['mae_m'],mae_augmented_m=a['mae_m'],mae_change_m=a['mae_m']-c['mae_m'],max_control_m=c['max_abs_m'],max_augmented_m=a['max_abs_m']))
extreme=[]
for r in pred:
 if r['phase']=='test' and r['nominal_lead_h']=='12' and num(r['actual_m'])-num(r['base_m'])>8.09:
  c=num(r['observed_control_m']);a=num(r['augmented_m']);y=num(r['actual_m']);extreme.append(dict(origin=r['origin'],target_time=r['target_time'],base_m=num(r['base_m']),actual_m=y,response_m=y-num(r['base_m']),control_m=c,augmented_m=a,control_abs_error_m=abs(c-y),augmented_abs_error_m=abs(a-y),error_change_m=abs(a-y)-abs(c-y)))
ok('12_large_response_cases',len(extreme)==12)
trades={p:{'hit_gains':[r['horizon_h'] for r in comparisons if r['phase']==p and r['hits_change']>0],'hit_losses':[r['horizon_h'] for r in comparisons if r['phase']==p and r['hits_change']<0],'mae_worse':[r['horizon_h'] for r in comparisons if r['phase']==p and r['mae_change_m']>0]} for p in ('validation','test')}
exsum=dict(n=len(extreme),improved=sum(r['error_change_m']<0 for r in extreme),worsened=sum(r['error_change_m']>0 for r in extreme),control_mae_m=float(np.mean([r['control_abs_error_m'] for r in extreme])),augmented_mae_m=float(np.mean([r['augmented_abs_error_m'] for r in extreme])),control_max_m=max(r['control_abs_error_m'] for r in extreme),augmented_max_m=max(r['augmented_abs_error_m'] for r in extreme))
report=dict(passed=True,checks=checks,metrics=metrics,comparisons=comparisons,tradeoffs=trades,extreme_response_summary=exsum,extreme_response_cases=extreme,failures=failures,limits=['Development data already inspected; not independent holdout.','Errors use finite pairs; hit fraction over observed targets retains failures.','No fits or model inspection in this audit.','Mixed changes do not establish causal attribution or promotion.'])
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');save('flood-metrics.csv',metrics);save('flood-comparison.csv',comparisons);save('extreme-response-cases.csv',extreme);save('missing-forecasts.csv',failures)
lines=['# Auditoria independente: acréscimo de 2023 ao Radar observado','',f'{len(checks)} verificações passaram. As 48 métricas de cheia/full_schedule foram recalculadas diretamente das previsões e coincidem até 1e-12. Controle de 120 campos, alvos, bases e chaves reproduzem exatamente o experimento anterior.','', 'Cada horizonte tem 28 alvos/28 pares na validação e 237 alvos/236 pares/1 falha no teste. A falha da origem 22/07 17h permanece no denominador de sucesso sobre alvos observados. Erros finitos não recebem zero para ausências.','', '| Fase | h | Acertos controle→2023 | MAE (m) | Máximo (m) |','|---|---:|---:|---:|---:|']
for r in comparisons:lines.append(f"| {r['phase']} | {r['horizon_h']} | {r['hits_control']}→{r['hits_augmented']} | {r['mae_control_m']:.6f}→{r['mae_augmented_m']:.6f} | {r['max_control_m']:.6f}→{r['max_augmented_m']:.6f} |")
lines+=['',f"Nos 12 pares de teste/12h com resposta acima de 8,09 m, {exsum['improved']} melhoram e {exsum['worsened']} pioram. MAE {exsum['control_mae_m']:.6f}→{exsum['augmented_mae_m']:.6f} m; máximo {exsum['control_max_m']:.6f}→{exsum['augmented_max_m']:.6f} m. As 12 origens e erros estão preservados no CSV.",'','Resultado misto: não há dominância geral nem promoção. Os períodos já inspecionados constituem desenvolvimento; esta auditoria não estabelece causalidade física dos ganhos, disponibilidade histórica certificada, equivalência de datum/regime entre anos ou meta de 98%. Nenhum treino ou consulta nova foi executado.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),tradeoffs=trades,extremes=exsum),indent=2))
