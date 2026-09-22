"""Independent eight-family factorial audit: metrics, membership, weights; no models."""
import csv,json,hashlib,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];E=ROOT/'outputs/experimento-radar-factorial-blocos-20260921';A=ROOT/'outputs/experimento-radar-core33-20260921';sources={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def rows(p):return list(csv.DictReader(use(p).open()))
def val(v):return float(v) if v not in ('',None) else np.nan
def check(name,condition):checks.append(dict(name=name,passed=bool(condition)));assert condition,name
def save(n,rs):
 with (OUT/n).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def future(a,h):return np.r_[a[h:],np.full(h,np.nan)]
P=rows(E/'predictions.csv');old=rows(A/'predictions.csv');evaluation=rows(E/'evaluation.csv');training=rows(E/'training.csv');protocol=json.loads(use(E/'protocol.json').read_text());manifest=json.loads(use(E/'artifact-hashes.json').read_text());mh={r['file']:r['sha256'] for r in manifest};oldm=dict(np.load(use(A/'training-masks.npz')));newm=dict(np.load(use(E/'training-masks.npz')))
families=protocol['families'];assert len(families)==8;key=lambda r:(r['phase'],r['origin'],r['nominal_lead_h']);lookup={key(r):r for r in old}
check('102084unique keys',len(P)==102084 and len({key(r) for r in P})==102084);check('all keys preserved',set(lookup)=={key(r) for r in P});check('same mask keys',set(oldm)==set(newm))
for k in oldm:check('mask '+k,np.array_equal(oldm[k],newm[k]))
for r in P:
 o=lookup[key(r)]
 for field in ['base_m','actual_m','target_time','original_complete24','observed_control_m','augmented_m','core_original_m','core_augmented_m']:assert r[field]==o[field],(key(r),field)
 assert len({np.isfinite(val(r[f+'_m'])) for f in families})==1,key(r)
check('all bases targets four frozen controls and eight-family availability exact',True)
check('no promotion',protocol['promoted'] is False and protocol['goal_achieved'] is False)
D=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));N=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2023-20260921/features.npz')));trainchecks=[]
for r in training:
 h=int(r['horizon_h']);phase=r['phase'];om=newm[f'{phase}_original_h{h}'];nm=newm[f'new_h{h}'];include=r['family'].endswith('_augmented');y=future(D['truth'],h);ny=future(N['truth'],h);delta=y-D['base'];ndelta=ny-N['base'];w=1+2*(abs(delta[om])>=1)+2*(y[om]>=9);nw=1+2*(abs(ndelta[nm])>=1)+2*(ny[nm]>=9)
 assert int(r['original_n'])==om.sum();assert int(r['added_n'])==(nm.sum() if include else 0);assert int(r['weight_sum'])==w.sum()+(nw.sum() if include else 0);assert int(r['features'])==(45 if r['family'].startswith('levels45') else 108);assert int(r['n'])==om.sum()+(nm.sum() if include else 0)
 trainchecks.append(dict(phase=phase,horizon_h=h,family=r['family'],original_n=int(om.sum()),added_n=int(nm.sum()) if include else 0,weight_sum=int(w.sum()+(nw.sum() if include else 0))))
check('96 memberships and weight sums',len(trainchecks)==96)
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
  contrasts=[
   ('year120','observed_control','augmented'),('year33','core_original','core_augmented'),('year45','levels45_original','levels45_augmented'),('year108','rain108_original','rain108_augmented'),
   ('rain_with_aux_original','levels45_original','observed_control'),('rain_with_aux_augmented','levels45_augmented','augmented'),('rain_without_aux_original','core_original','rain108_original'),('rain_without_aux_augmented','core_augmented','rain108_augmented'),
   ('aux_with_rain_original','rain108_original','observed_control'),('aux_with_rain_augmented','rain108_augmented','augmented'),('aux_without_rain_original','core_original','levels45_original'),('aux_without_rain_augmented','core_augmented','levels45_augmented')]
  for contrast,a,b in contrasts:
   effect=dict(phase=phase,horizon_h=h,contrast=contrast,reference=a,candidate=b)
   for field in ['hits','mae_m','bias_m','p98_abs_m','max_abs_m']:
    effect['reference_'+field]=mv[a][field];effect['candidate_'+field]=mv[b][field];effect['change_'+field]=mv[b][field]-mv[a][field]
   effects.append(effect)
summary={}
for phase in ['validation','test']:
 for contrast,a,b in contrasts:
  rr=[r for r in effects if r['phase']==phase and r['contrast']==contrast];summary[phase+':'+contrast]=dict(reference=a,candidate=b,hit_gain_horizons=[r['horizon_h'] for r in rr if r['change_hits']>0],hit_loss_horizons=[r['horizon_h'] for r in rr if r['change_hits']<0],mae_improved_horizons=[r['horizon_h'] for r in rr if r['change_mae_m']<0],mae_worsened_horizons=[r['horizon_h'] for r in rr if r['change_mae_m']>0])
# Global descriptive dominance: no horizon selection and no statistical claim.
dominance=[]
for phase in ['validation','test','both']:
 for a in families:
  for b in families:
   if a==b:continue
   cells=[m for m in metrics if m['family']==a and (phase=='both' or m['phase']==phase)];comparisons=[(m,next(n for n in metrics if n['family']==b and n['phase']==m['phase'] and n['horizon_h']==m['horizon_h'])) for m in cells]
   nonworse=all(x['hits']>=y['hits'] and x['mae_m']<=y['mae_m'] and x['max_abs_m']<=y['max_abs_m'] for x,y in comparisons);strict=any(x['hits']>y['hits'] or x['mae_m']<y['mae_m'] or x['max_abs_m']<y['max_abs_m'] for x,y in comparisons)
   dominance.append(dict(phase=phase,candidate=a,reference=b,dominates_hits_mae_max_all_horizons=bool(nonworse and strict)))
# Effect modifications are signed differences of matched factorial contrasts.
interactions=[]
for phase in ['validation','test']:
 for h in range(1,13):
  for label,left,right in [('rain_year_with_aux','rain_with_aux_original','rain_with_aux_augmented'),('rain_year_without_aux','rain_without_aux_original','rain_without_aux_augmented'),('aux_year_with_rain','aux_with_rain_original','aux_with_rain_augmented'),('aux_year_without_rain','aux_without_rain_original','aux_without_rain_augmented'),('rain_aux_original','rain_without_aux_original','rain_with_aux_original'),('rain_aux_augmented','rain_without_aux_augmented','rain_with_aux_augmented')]:
   a=next(r for r in effects if r['phase']==phase and r['horizon_h']==h and r['contrast']==left);b=next(r for r in effects if r['phase']==phase and r['horizon_h']==h and r['contrast']==right);r=dict(phase=phase,horizon_h=h,interaction=label,left=left,right=right)
   for f in ['hits','mae_m','max_abs_m']:r['difference_of_effects_'+f]=b['change_'+f]-a['change_'+f]
   interactions.append(r)
for f,h in sources.items():
 p=ROOT/f
 if p.parent==E and p.name in mh:check('manifest '+p.name,h==mh[p.name])
check('192 metric groups',len(metrics)==192);check('288 contrast groups',len(effects)==288);check('36 masks',len(newm)==36)
result=dict(passed=True,check_count=len(checks),checks=checks,metrics=metrics,effects=effects,summary=summary,training=trainchecks,failures=failures,dominance=dominance,interactions=interactions,limits=['All previously inspected development data; not independent holdout.','Same28validationtargets repeated across12h; not336independent observations.','Rain block includes45amount/lag and30coverage fields; effect does not separate physical rain from data availability.','Fixed unretuned algorithm comparison, not physical causality or optimal feature-family models.','Dominance is explicitly joint hits>=,MAE<=,max<= at every horizon; no statistical or prospective claim.','No per-horizon family selection, model execution, new fit, source queries or promotion.'])
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'source-manifest.json').write_text(json.dumps(sources,indent=2)+'\n');save('flood-metrics.csv',metrics);save('factorial-effects.csv',effects);save('training-weights.csv',trainchecks);save('missing-forecasts.csv',failures);save('dominance.csv',dominance);save('interactions.csv',interactions)
lines=['# Auditoria independente: oito famílias Radar','',f'{len(checks)} verificações passaram. As192 métricas de cheia/full_schedule foram recalculadas diretamente das previsões, com tolerância1e-12. As102.084 chaves/bases/alvos e quatro controles são exatos; disponibilidade idêntica nas oito famílias;36máscaras e96memberships/pesos conferem.','',
'Cada horizonte/família preserva28alvos/28pares de validação e237alvos/236pares/1falha de teste. Sucesso sobre alvos usa237 e mantém a falha; MAE usa236 pares finitos.','',
'Foram calculados12contrastes: adição2023 em cada um dos quatro conjuntos de entradas; adição da chuva com/sem auxiliares, em cada conjunto de anos; adição dos auxiliares com/sem chuva, em cada conjunto de anos. Valores positivos de Δacertos são ganhos; valores negativos de ΔMAE/máximo são reduções de erro.','',
'## Efeitos por horizonte','', '| Fase/contraste | Ganho de acertos | Perda de acertos | MAE melhora | MAE piora |','|---|---|---|---|---|']
for k,s in summary.items():lines.append(f"| {k} | {s['hit_gain_horizons']} | {s['hit_loss_horizons']} | {s['mae_improved_horizons']} | {s['mae_worsened_horizons']} |")
lines+=['','## Resultados h1/h6/h12','', '| Fase | h | Família | Acertos/alvos | MAE | Máximo |','|---|---:|---|---:|---:|---:|']
for m in metrics:
 if m['horizon_h'] in [1,6,12]:lines.append(f"| {m['phase']} | {m['horizon_h']} | {m['family']} | {m['hits']}/{m['observed_targets']} | {m['mae_m']:.6f} | {m['max_abs_m']:.6f} |")
positive=[d for d in dominance if d['dominates_hits_mae_max_all_horizons']]
lines+=['','## Dominância e limites','',f'Dominância descritiva conjunta definida como acertos não menores, MAE e máximo não maiores em todos os12horizontes, com alguma melhora estrita. Relações encontradas: {positive}. Nenhuma seleção de família por horizonte foi realizada.','',
'As diferenças dos efeitos por ano/bloco estão em interactions.csv; são contrastes aritméticos, não atribuição física nem estimativa de significância. Chuva inclui indicadores de cobertura, e os hiperparâmetros não foram reajustados por representação. Permanecem os limites de disponibilidade/datum/regime entre anos e a ausência do pico2023. Esta auditoria não interpreta ausência como zero nem comprova98% prospectivos.','',
'Os modelos e inferência são verificados separadamente pelo agente principal. Esta tarefa leu apenas matrizes, máscaras, previsões, métricas, código/protocolo e hashes; nenhum modelo foi carregado ou executado. Sem promoção.']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),dominance=positive,summary=summary),indent=2))
result['interpretation']={
'validation_year_effect':'Adding2023 worsens MAE12/12with120 and10/12with108, versus5/12with45 and3/12with33. Removing only auxiliary gauges does not remove the broad validation deterioration.',
'validation_rain_effect':'With auxiliary gauges, adding rain improves validation MAE9/12onoriginal training but only1/12after2023augmentation. Without auxiliary gauges, it improves9/12original and2/12augmented. This is a fixed-algorithm conditional effect, not physical causality.',
'test_tradeoff':'Adding2023to45 improves test MAE12/12yet loses hits8/12. Adding2023to108 improves MAE10/12and hits9/12, but loses hits2/12. No universal dominance.',
'h12_tradeoff':'Test108augmented has MAE1.238302vs1.256706for120augmented, but81vs89hits and max7.462013vs7.362831. Validation108augmentation worsens MAE0.810315to1.107090and8to4hits.'}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'README.md').open('a') as f:f.write('''
## Interpretação dos efeitos condicionais

O acréscimo2023 piora MAE na validação em12/12horizontes com120campos e10/12com108; em45piora5/12 e em33piora3/12. **Retirar somente os níveis auxiliares não elimina a regressão ampla da validação.** Em h12,108original→108+2023 passa de0,810315→1,107090m e8→4acertos;45original→45+2023 passa de1,174292→1,243306m e3→2acertos.

O efeito das entradas de chuva muda conforme os anos usados no treino. Mantendo os auxiliares, adicionar chuva melhora MAE da validação em9/12horizontes no treino original, mas só1/12 após acrescentar2023. Sem auxiliares, melhora9/12original e2/12 aumentado. Essa interação depende do procedimento de ajuste congelado, inclui indicadores de cobertura e não prova efeito físico da precipitação.

No teste, acrescentar2023 ao conjunto45 melhora MAE em12/12horizontes, mas perde acertos em8/12; ao conjunto108 melhora MAE10/12 e acertos9/12, mas perde acertos em2/12. Nenhuma família apresenta dominância conjunta nos critérios declarados, mesmo considerando cada fase separadamente.

Em teste/h12,108+2023 tem MAE1,238302m contra1,256706m de120+2023, mas81contra89acertos e máximo7,462013contra7,362831m. Ganho de erro médio não equivale a ganho de precisão no limiar de0,50m. Não escolheremos uma família diferente por horizonte depois desses resultados.
''')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
