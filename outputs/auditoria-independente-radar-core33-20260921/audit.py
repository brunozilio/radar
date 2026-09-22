"""Independent core33 factorial audit: metrics, membership, weights; no models."""
import csv,json,hashlib,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];E=ROOT/'outputs/experimento-radar-core33-20260921';A=ROOT/'outputs/experimento-radar-historico-2023-20260921';sources={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def rows(p):return list(csv.DictReader(use(p).open()))
def val(v):return float(v) if v not in ('',None) else np.nan
def check(name,condition):checks.append(dict(name=name,passed=bool(condition)));assert condition,name
def save(n,rs):
 with (OUT/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def future(a,h):return np.r_[a[h:],np.full(h,np.nan)]
P=rows(E/'predictions.csv');old=rows(A/'predictions.csv');evaluation=rows(E/'evaluation.csv');training=rows(E/'training.csv');protocol=json.loads(use(E/'protocol.json').read_text());manifest=json.loads(use(E/'artifact-hashes.json').read_text());mh={r['file']:r['sha256'] for r in manifest};oldm=dict(np.load(use(A/'training-masks.npz')));newm=dict(np.load(use(E/'training-masks.npz')))
families=['observed_control','augmented','core_original','core_augmented'];key=lambda r:(r['phase'],r['origin'],r['nominal_lead_h']);lookup={key(r):r for r in old}
check('102084unique keys',len(P)==102084 and len({key(r) for r in P})==102084);check('all keys preserved',set(lookup)=={key(r) for r in P});check('same mask keys',set(oldm)==set(newm))
for k in oldm:check('mask '+k,np.array_equal(oldm[k],newm[k]))
for r in P:
 o=lookup[key(r)]
 for field in ['base_m','actual_m','target_time','original_complete24','observed_control_m','augmented_m']:assert r[field]==o[field],(key(r),field)
 assert len({np.isfinite(val(r[f+'_m'])) for f in families})==1,key(r)
check('all bases targets two frozen controls and four-family availability exact',True)
check('no promotion',protocol['promoted'] is False and protocol['goal_achieved'] is False)
D=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));N=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2023-20260921/features.npz')));trainchecks=[]
for r in training:
 h=int(r['horizon_h']);phase=r['phase'];om=newm[f'{phase}_original_h{h}'];nm=newm[f'new_h{h}'];include=r['family']=='core_augmented';y=future(D['truth'],h);ny=future(N['truth'],h);delta=y-D['base'];ndelta=ny-N['base'];w=1+2*(abs(delta[om])>=1)+2*(y[om]>=9);nw=1+2*(abs(ndelta[nm])>=1)+2*(ny[nm]>=9)
 assert int(r['original_n'])==om.sum();assert int(r['added_n'])==(nm.sum() if include else 0);assert int(r['weight_sum'])==w.sum()+(nw.sum() if include else 0);assert int(r['features'])==33;assert int(r['n'])==om.sum()+(nm.sum() if include else 0)
 trainchecks.append(dict(phase=phase,horizon_h=h,family=r['family'],original_n=int(om.sum()),added_n=int(nm.sum()) if include else 0,weight_sum=int(w.sum()+(nw.sum() if include else 0))))
check('48 memberships and weight sums',len(trainchecks)==48)
metrics=[];effects=[];failures=[]
for phase in ['validation','test']:
 for h in range(1,13):
  schedule=[r for r in P if r['phase']==phase and int(r['nominal_lead_h'])==h];observed=[r for r in schedule if val(r['actual_m'])>=7];mv={};masks={}
  for family in families:
   pairs=[r for r in observed if np.isfinite(val(r[family+'_m']))];masks[family]=[key(r) for r in pairs];err=np.array([val(r[family+'_m'])-val(r['actual_m']) for r in pairs]);ae=abs(err);hits=int((ae<=.5).sum());m=dict(phase=phase,horizon_h=h,subset='level_ge_7m',population='full_schedule',family=family,scheduled_rows=len(schedule),observed_targets=len(observed),n=len(pairs),failures=len(observed)-len(pairs),hits=hits,hit_fraction=hits/len(pairs),observed_target_hit_fraction=hits/len(observed),mae_m=float(ae.mean()),bias_m=float(err.mean()),p98_abs_m=float(np.quantile(ae,.98)),max_abs_m=float(ae.max()));metrics.append(m);mv[family]=m
   s=next(s for s in evaluation if s['phase']==phase and s['horizon_h']==str(h) and s['family']==family and s['subset']=='level_ge_7m' and s['population']=='full_schedule')
   check(f'metrics {phase} {h} {family}',all(math.isclose(v,float(s[k]),abs_tol=1e-12,rel_tol=0) for k,v in m.items() if isinstance(v,(int,float))));check(f'coverage {phase} {h} {family}',(len(observed),len(pairs),m['failures'])==((237,236,1) if phase=='test' else (28,28,0)))
   for r in observed:
    if not np.isfinite(val(r[family+'_m'])):failures.append(dict(phase=phase,horizon_h=h,family=family,origin=r['origin'],target_time=r['target_time'],base_m=r['base_m'],actual_m=r['actual_m']))
  check(f'identical paired keys {phase} {h}',all(masks[f]==masks[families[0]] for f in families))
  contrasts=[('add2023_with120','observed_control','augmented'),('add2023_with33','core_original','core_augmented'),('reduce120to33_original','observed_control','core_original'),('reduce120to33_augmented','augmented','core_augmented')]
  for contrast,a,b in contrasts:
   effect=dict(phase=phase,horizon_h=h,contrast=contrast,reference=a,candidate=b)
   for field in ['hits','mae_m','bias_m','p98_abs_m','max_abs_m']:
    effect['reference_'+field]=mv[a][field];effect['candidate_'+field]=mv[b][field];effect['change_'+field]=mv[b][field]-mv[a][field]
   effects.append(effect)
  e=dict(phase=phase,horizon_h=h,contrast='interaction_addition_difference_33_minus120',reference='add2023_with120',candidate='add2023_with33')
  for field in ['hits','mae_m','bias_m','p98_abs_m','max_abs_m']:
   a=mv['augmented'][field]-mv['observed_control'][field];b=mv['core_augmented'][field]-mv['core_original'][field];e['reference_'+field]=a;e['candidate_'+field]=b;e['change_'+field]=b-a
  effects.append(e)
summary={}
for phase in ['validation','test']:
 for contrast in ['add2023_with120','add2023_with33','reduce120to33_original','reduce120to33_augmented']:
  rr=[r for r in effects if r['phase']==phase and r['contrast']==contrast];summary[phase+':'+contrast]=dict(hit_gain_horizons=[r['horizon_h'] for r in rr if r['change_hits']>0],hit_loss_horizons=[r['horizon_h'] for r in rr if r['change_hits']<0],mae_improved_horizons=[r['horizon_h'] for r in rr if r['change_mae_m']<0],mae_worsened_horizons=[r['horizon_h'] for r in rr if r['change_mae_m']>0])
for f,h in sources.items():
 p=ROOT/f
 if p.parent==E and p.name in mh:check('manifest '+p.name,h==mh[p.name])
result=dict(passed=True,check_count=len(checks),checks=checks,metrics=metrics,effects=effects,summary=summary,training=trainchecks,failures=failures,limits=['Already inspected development periods; not independent holdout.','Validation28targets are one continuous November2025interval, repeated across horizons.','Factorial changes are descriptive algorithmic contrasts; no attribution to sensor missingness alone.','No per-horizon family selection, promotion, source equivalence certification or98percent claim.','Model inference verified separately by parent; no model loaded here.'])
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');save('flood-metrics.csv',metrics);save('factorial-effects.csv',effects);save('training-weights.csv',trainchecks);save('missing-forecasts.csv',failures)
lines=['# Auditoria independente do experimento fatorial Radar core33','',f'{len(checks)} verificações passaram. Recalculei os96 grupos de cheia/full_schedule diretamente de predictions.csv; concordância até1e-12 com evaluation.csv. As102.084 chaves, bases, alvos, duas previsões controle e disponibilidade das quatro famílias coincidem exatamente com o experimento anterior. Todas as36 máscaras e os48 totais de treino/pesos conferem.','',
'Cada horizonte/família mantém28alvos/28pares na validação e237alvos/236pares/1falha no teste. A falta da origem22/07 17h é preservada; MAE usa pares finitos e sucesso sobre alvos usa237 como denominador.','',
'Comparação por horizonte, sem escolher versões após observar desempenho. Acerto é erro≤0,50m e cheia é alvo≥7m. A tabela mostra **original→com2023** dentro de cada conjunto de entradas.','',
'| Fase | h | Acertos120 | MAE120 (m) | Acertos33 | MAE33 (m) |','|---|---:|---:|---:|---:|---:|']
for phase in ['validation','test']:
 for h in range(1,13):
  a=next(r for r in effects if r['phase']==phase and r['horizon_h']==h and r['contrast']=='add2023_with120');b=next(r for r in effects if r['phase']==phase and r['horizon_h']==h and r['contrast']=='add2023_with33')
  lines.append(f"| {phase} | {h} | {a['reference_hits']}→{a['candidate_hits']} | {a['reference_mae_m']:.6f}→{a['candidate_mae_m']:.6f} | {b['reference_hits']}→{b['candidate_hits']} | {b['reference_mae_m']:.6f}→{b['candidate_mae_m']:.6f} |")
lines+=['','## Ganhos e regressões','']
for name,s in summary.items():lines.append(f"- {name}: ganha acertos h{s['hit_gain_horizons']}; perde h{s['hit_loss_horizons']}; melhora MAE h{s['mae_improved_horizons']}; piora MAE h{s['mae_worsened_horizons']}.")
lines+=['','Os CSVs incluem todos os quatro contrastes principais e a diferença entre os efeitos de acréscimo (33 menos120). Essa interação é apenas descritiva: não é inferência estatística, não torna os28alvos independentes e não prova que ausências ou chuva foram a causa física da regressão. Os parâmetros permaneceram congelados, portanto também não há alegação de arquitetura ótima.','',
'Sem novos ajustes, execução de modelos, coleta ou mudança operacional. Os controles e máscaras conferem; a inferência dos modelos é auditada pelo agente principal. Nenhuma promoção ou composição de famílias por horizonte.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),summary=summary),indent=2))
extra=[]
for phase in ['validation','test']:
 rrs=[]
 for h in range(1,13):
  a=next(m for m in metrics if m['phase']==phase and m['horizon_h']==h and m['family']=='observed_control');b=next(m for m in metrics if m['phase']==phase and m['horizon_h']==h and m['family']=='core_augmented');rrs.append(dict(horizon_h=h,hits_change=b['hits']-a['hits'],mae_change_m=b['mae_m']-a['mae_m']))
 extra.append(dict(phase=phase,contrast='core33_augmented_vs120_original',horizons=rrs))
result['additional_comparison']=extra
result['conclusion']='Core33 changes the addition effect but does not generally resolve validation deterioration: adding2023 improves MAE9/12 within33, yet reduced original33 itself worsens validation MAE12/12 versusoriginal120. Test hit losses remain6/12 when adding2023within33. No domination or promotion.'
result['h1_denominator_caution']=dict(family='core_augmented',phase='test',hits=232,paired=236,observed=237,paired_fraction=232/236,observed_target_fraction=232/237)
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'README.md').open('a') as f:f.write('''
## A redução resolveu a regressão da validação?

**Parcialmente no contraste de acréscimo, não como solução geral.** Adicionar2023 a120 piorou o MAE dos12horizontes da validação; dentro33 melhora9 e piora3 (h5/10/11). Entretanto, reduzir120→33 sem2023 já piora MAE nos12horizontes da validação. Assim, inverter o sinal do efeito de acréscimo sobre uma referência pior não equivale a recuperar o desempenho original.

Em h6 da validação,120original→120+2023→33original→33+2023 produz MAE0,258712→0,531288→0,366026→0,328739m e24→18→18→20acertos. Em h12: MAE0,908493→1,210744→1,097877→1,093578m e7→3→8→9acertos. O ganho em acertos pode coexistir com MAE maior.

No teste, acrescentar2023 dentro33 melhora MAE em10/12horizontes, mas perde acertos em6 (h6/7/8/9/11/12). Em h12,120+2023→33+2023 reduz89→79acertos, piora MAE1,256706→1,293003m e máximo7,362831→9,421135m. Não há dominância.

**Cuidado com98%:** core33+2023/teste/h1 tem232/236=98,305% apenas entre pares disponíveis, mas232/237=97,890% sobre os alvos observados, incluindo a falha. Isso não alcança98% no denominador completo e tampouco representa desempenho global ou prospectivo.

A remoção conjunta dos níveis SantaTereza/Carreiro e da chuva não separa o efeito de cada família; esta comparação não identifica a causa específica da regressão.
''')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
