"""Independent frozen reserved challenge audit. Predict only; never fit/tune."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from collections import Counter
import csv,json,hashlib,math,importlib.metadata
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
EXP=ROOT/'outputs/experimento-radar-reservas-2021-2022-20260922';M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922';R=ROOT/'outputs/verificacao-radar-matrizes-reservadas-2021-2022-20260922';FROZEN=ROOT/'outputs/congelamento-radar-reserva-2021-2022-20260922';ANALYSIS=ROOT/'outputs/analise-radar-reservas-2021-2022-20260922'
FAMILIES=('control120','candidate120_plus2020');TZ=timezone(timedelta(hours=-3));checks=[];sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def rows(p):return list(csv.DictReader(use(p).open()))
def ok(name,value):assert value,name;checks.append(dict(name=name,passed=True))
def eq(a,b):return np.array_equal(np.asarray(a),np.asarray(b),equal_nan=True)
def number(v):return float(v) if v not in ('',None) else np.nan
def iso(t):return datetime.fromtimestamp(t,TZ).isoformat()
def epoch(t):return datetime.fromisoformat(t).timestamp()
def nullable(n):return float(n) if np.isfinite(n) else None
def dump(name,v): (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(name,rr):
 if rr:
  with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def manifest(p):
 m=read(p/'artifact-hashes.json');items=m['files'].items() if isinstance(m,dict) else [(r['file'],r['sha256']) for r in m]
 for f,h in items:assert sha(p/f)==h,(p,f)
 ok('manifest:'+str(p.relative_to(ROOT)),True)
def main():
 for folder in (EXP,M,R,FROZEN,ANALYSIS):manifest(folder)
 protocol=read(EXP/'protocol.json');gate=read(EXP/'pre-inference-manifest.json');start=read(EXP/'inference-started.json');done=read(EXP/'experiment.json');reservation=read(ROOT/'docs/radar-historical-evaluation-reservation.json')
 ok('protocol_frozen_identity',sha(EXP/'protocol.json')==sha(FROZEN/'protocol.json')==sha(ROOT/'docs/radar-reserved-2021-2022-challenge-protocol.json')==gate['protocol_sha256'])
 ok('freeze_before_first_logged_inference',reservation['registered_at_utc']<protocol['registered_at_utc']<gate['registered_at_utc']<start['started_at_utc']==done['started_at_utc']<done['finished_at_utc'])
 ok('gate_hash_link',start['pre_inference_manifest_sha256']==done['pre_inference_manifest_sha256']==sha(EXP/'pre-inference-manifest.json'))
 ok('153_gate_inputs',len(gate['input_sha256'])==153)
 for p,h in gate['input_sha256'].items():ok('gate_input:'+p,sha(ROOT/p)==h)
 for p,h in protocol['reference_sha256'].items():ok('protocol_reference:'+p,sha(ROOT/p)==h)
 ok('runtime_exact',gate['runtime']=={k:importlib.metadata.version(k) for k in gate['runtime']})
 ok('no_fit_or_promotion',done['models_fitted']==0 and done['training_membership_changed'] is False and done['promoted'] is False and done['goal_achieved'] is False and gate['training_allowed'] is False)
 # Membership identity and strict target cutoff, independently from the freeze report.
 old=dict(np.load(use(ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921/features.npz')));new=dict(np.load(use(ROOT/'outputs/radar-matriz-observada-2020-20260921/features.npz')))
 masks=dict(np.load(use(ROOT/'outputs/experimento-radar-historico-2020-20260921/training-masks.npz')));originalmasks=dict(np.load(use(ROOT/'outputs/experimento-radar-observado-120-20260921/training-masks.npz')))
 for w in reservation['windows']:
  lo=epoch(w['start_inclusive_local']);hi=epoch(w['stop_exclusive_local']);ok('reserved_origin_absent:'+w['start_inclusive_local'],not any(((d['times']>=lo)&(d['times']<hi)).any() for d in (old,new)))
 records={(r['family'],r['horizon_h']):r for r in protocol['model_records']};ok('24_unique_frozen_models',len(records)==len(protocol['model_records'])==24);models={};membership=[]
 for h in range(1,13):
  o=masks[f'test_original_h{h}'];n=masks[f'new_h{h}'];ok(f'membership_control_candidate_h{h}',np.array_equal(o,originalmasks[f'test_h{h}']));ok(f'strict_training_target_cutoff_h{h}',np.all(old['times'][o]+h*3600<epoch('2026-07-01T00:00:00-03:00')) and np.all(new['times'][n]+h*3600<epoch('2020-07-21T00:00:00-03:00')))
  for family in FAMILIES:
   r=records[family,h];p=use(ROOT/r['file']);source=use(ROOT/r['source']);ok(f'model_original_frozen_hash:{family}:{h}',sha(p)==sha(source)==r['sha256']);m=joblib.load(p);ok(f'model_config:{family}:{h}',m.n_features_in_==120 and m.get_params()==r['parameters']);models[family,h]=m
   t=r['training'];expected=int(o.sum())+(int(n.sum()) if family==FAMILIES[1] else 0);ok(f'membership_count:{family}:{h}',int(t['n'])==expected and epoch(t['latest_training_target'])<epoch(t['cutoff_exclusive']))
   membership.append(dict(family=family,horizon_h=h,original=int(o.sum()),added2020=int(n.sum()) if family==FAMILIES[1] else 0,total=expected,latest_training_target=t['latest_training_target'],cutoff_exclusive=t['cutoff_exclusive']))
 pred=rows(EXP/'predictions.csv');bound=rows(EXP/'boundary-coverage.csv');saved=rows(EXP/'evaluation.csv');key=lambda r:(int(r['year']),r['origin'],int(r['nominal_lead_h']));index={key(r):r for r in pred};ok('26340_unique_rows',len(pred)==len(index)==26340);ok('156_boundary_exclusions',sum(int(r['boundary_excluded']) for r in bound)==156 and len(bound)==24)
 replay=[];threshold_changes=[];expectedkeys=set();missing_rows=[];loads=24;applications=0;original_replays=0
 for year in (2021,2022):
  original=dict(np.load(use(M/str(year)/'features.npz')));ind=dict(np.load(use(R/f'reconstructed-{year}.npz')));tt,base,truth,F=(ind[k] for k in ('times','base','truth','features'));n=len(tt)
  ok(f'{year}:independent_base_truth_exact',eq(base,original['base']) and eq(truth,original['truth']) and eq(tt,original['times']));ok(f'{year}:independent_feature_nans',np.array_equal(np.isnan(F),np.isnan(original['features'])));ok(f'{year}:independent_feature_tolerance',np.nanmax(abs(F-original['features']))<=2e-10)
  diag={r['origin']:r for r in rows(M/str(year)/'qi-origin-diagnostics.csv')}
  for h in range(1,13):
   scheduled=n-h;target=truth[h:];bb=base[:scheduled];finite=np.isfinite(bb);keys=[(year,iso(t),h) for t in tt[:scheduled]];expectedkeys.update(keys);ss=[index[k] for k in keys]
   b=next(r for r in bound if int(r['year'])==year and int(r['horizon_h'])==h);ok(f'{year}:boundary_h{h}',int(b['origins'])==n and int(b['scheduled_rows'])==scheduled and int(b['boundary_excluded'])==h)
   ok(f'{year}:source_labels_h{h}',eq([number(r['actual_m']) for r in ss],target) and eq([number(r['base_m']) for r in ss],bb))
   for i,r in enumerate(ss):
    assert r['target_time']==iso(tt[i]+h*3600)==iso(tt[i+h]);assert r['missing_base']==str(not bool(finite[i]));assert r['missing_truth']==str(not bool(np.isfinite(target[i])));assert r['complete24']==str(bool(original['complete24'][i]));assert r['qi_reported_zero_used']==diag[r['origin']]['uses_any_zero']
    if not finite[i] or not np.isfinite(target[i]):missing_rows.append(dict(year=year,origin=r['origin'],horizon_h=h,target_time=r['target_time'],missing_base=r['missing_base'],missing_truth=r['missing_truth'],actual_m=nullable(target[i]),control_m=nullable(number(r[FAMILIES[0]+'_m'])),candidate_m=nullable(number(r[FAMILIES[1]+'_m']))))
   for family in FAMILIES:
    m=models[family,h];values=np.full(scheduled,np.nan);values[finite]=m.predict(F[:scheduled][finite])+bb[finite];applications+=1;savedpred=np.array([number(r[family+'_m']) for r in ss]);ok(f'{year}:{family}:missingness_h{h}',eq(np.isfinite(savedpred),finite) and np.isfinite(values[finite]).all());diff=values[finite]-savedpred[finite];changed=np.flatnonzero(finite&(np.nan_to_num(values,nan=0)!=np.nan_to_num(savedpred,nan=0)))
    original_max=0.
    if len(changed):
     original_values=np.full(scheduled,np.nan);original_values[finite]=m.predict(original['features'][:scheduled][finite])+bb[finite];original_replays+=1;ok(f'{year}:{family}:original_matrix_exact_h{h}',eq(original_values,savedpred));original_max=float(np.max(abs(original_values[finite]-savedpred[finite])))
     for i in changed:threshold_changes.append(dict(year=year,family=family,horizon_h=h,origin=iso(tt[i]),saved_m=float(savedpred[i]),independent_m=float(values[i]),difference_m=float(values[i]-savedpred[i]),original_reproduces=True))
    else:ok(f'{year}:{family}:independent_inference_exact_h{h}',eq(values,savedpred))
    replay.append(dict(year=year,family=family,horizon_h=h,scheduled_rows=scheduled,applied=int(finite.sum()),missing_base=int((~finite).sum()),independent_changed_rows=len(changed),max_abs_independent_difference=float(np.max(abs(diff))) if len(diff) else 0,original_matrix_max_abs_difference=original_max))
 ok('schedule_keys_exact',set(index)==expectedkeys);ok('48_applications',applications==done['model_load_calls']==48 and done['unique_models']==24)
 # Recompute all432metrics from preserved rows; missing truth excluded from hits/observed denominator.
 metrics=[];metricindex={}
 for period in ('2021','2022','pooled'):
  for h in range(1,13):
   for population in ('full_schedule','complete24','missing24'):
    pop=[r for r in pred if (period=='pooled' or r['year']==period) and int(r['nominal_lead_h'])==h and (population=='full_schedule' or (r['complete24']=='True')==(population=='complete24'))]
    for subset in ('all','level_ge_7m'):
     actual=np.array([number(r['actual_m']) for r in pop]);obs=np.isfinite(actual)&((actual>=7) if subset=='level_ge_7m' else True)
     for family in FAMILIES:
      forecast=np.array([number(r[family+'_m']) for r in pop]);pair=obs&np.isfinite(forecast);err=forecast[pair]-actual[pair];ab=np.abs(err);hits=int(np.count_nonzero(ab<=.5));no=int(obs.sum());nn=int(pair.sum())
      m=dict(period=period,horizon_h=h,population=population,subset=subset,family=family,scheduled_population_rows=len(pop),missing_truth_in_population=int((~np.isfinite(actual)).sum()),observed_targets=no,paired_predictions=nn,missing_forecasts=no-nn,hits=hits,paired_hit_fraction=hits/nn if nn else None,observed_target_hit_fraction=hits/no if no else None,mae_m=float(np.mean(ab)) if nn else None,bias_m=float(np.mean(err)) if nn else None,p98_abs_m=float(np.quantile(ab,.98)) if nn else None,max_abs_m=float(np.max(ab)) if nn else None);metrics.append(m);metricindex[period,h,population,subset,family]=m
      sr=next(r for r in saved if all(r[k]==str(m[k]) for k in ('period','horizon_h','population','subset','family')))
      for k,v in m.items():
       if k in ('period','horizon_h','population','subset','family'):continue
       if v is None:assert sr[k]=='',(m,k,sr[k])
       else:assert math.isclose(v,float(sr[k]),rel_tol=0,abs_tol=1e-12),(m,k,sr[k])
      ok(f'metric:{period}:{h}:{population}:{subset}:{family}',True)
 ok('432_metrics',len(metrics)==len(saved)==432)
 changes=[];tallies=[]
 for period in ('2021','2022','pooled'):
  for subset in ('all','level_ge_7m'):
   rr=[]
   for h in range(1,13):
    c=metricindex[period,h,'full_schedule',subset,FAMILIES[0]];a=metricindex[period,h,'full_schedule',subset,FAMILIES[1]]
    r=dict(period=period,subset=subset,horizon_h=h,observed_targets=c['observed_targets'],pairs=c['paired_predictions'],failures=c['missing_forecasts'],control_hits=c['hits'],candidate_hits=a['hits'],hit_change=a['hits']-c['hits'],control_fraction=c['observed_target_hit_fraction'],candidate_fraction=a['observed_target_hit_fraction'],control_mae=c['mae_m'],candidate_mae=a['mae_m'],mae_change=a['mae_m']-c['mae_m'],control_max=c['max_abs_m'],candidate_max=a['max_abs_m'],max_change=a['max_abs_m']-c['max_abs_m']);rr.append(r);changes.append(r)
   tallies.append(dict(period=period,subset=subset,hits_improve=sum(r['hit_change']>0 for r in rr),hits_tie=sum(r['hit_change']==0 for r in rr),hits_worse=sum(r['hit_change']<0 for r in rr),mae_improve=sum(r['mae_change']<0 for r in rr),mae_worse=sum(r['mae_change']>0 for r in rr),max_worse=sum(r['max_change']>0 for r in rr),candidate_point_fraction_ge98_horizons=[r['horizon_h'] for r in rr if r['candidate_fraction']>=.98]))
 published=rows(ANALYSIS/'changes.csv');ok('72_analysis_changes',len(published)==len(changes)==72)
 for r in changes:
  pp=next(x for x in published if x['period']==r['period'] and x['subset']==r['subset'] and int(x['horizon_h'])==r['horizon_h'])
  for k,v in r.items():
   if isinstance(v,(int,float)):assert math.isclose(v,float(pp[k]),rel_tol=0,abs_tol=1e-12)
 ok('changes_match_independent_metrics',True);ok('tallies_match',read(ANALYSIS/'analysis.json')['tallies']==tallies)
 for p,h in gate['input_sha256'].items():assert sha(ROOT/p)==h,p
 selected=[r for r in changes if r['horizon_h'] in (1,6,12)]
 report=dict(passed=True,checks=checks,unique_models=24,replay_applications=48,original_matrix_fallback_replays=original_replays,replay=replay,threshold_sensitivity_cases=threshold_changes,prediction_rows=26340,boundary_exclusions=156,metrics_verified=432,gate_input_hashes_verified=len(gate['input_sha256']),time_order=dict(reservation=reservation['registered_at_utc'],protocol=protocol['registered_at_utc'],input_freeze=gate['registered_at_utc'],inference_start=start['started_at_utc'],inference_finish=done['finished_at_utc']),tallies=tallies,selected_changes=selected,training_memberships=membership,source_sha256=sources,limits=['No training or model selection. Audit reapplies previously frozen models only.','Training includes2025/2026: retrospective transfer, not a forecast possible using only then-past training.','Source timezones/datums/availability remain assumed. Data collection and documentary exposure preceded evaluation.','Hourly samples correlated; no independent-event/prospective98% claim.','Any future adjustments informed by these results make the windows development data.','Logged freeze/inference order plus hashes verified; not a global proof of all prior computations outside this scope.'])
 dump('verification.json',report);dump('source-manifest.json',sources);csvsave('independent-metrics.csv',metrics);csvsave('independent-changes.csv',changes);csvsave('replay.csv',replay);csvsave('threshold-sensitivity.csv',threshold_changes);csvsave('missingness.csv',missing_rows);csvsave('training-memberships.csv',membership)
 lines=['# Auditoria independente — primeira avaliação reservada2021/2022','',f'{len(checks)} verificações passaram. Conferidos24modelos congelados,48aplicações,26.340linhas agendadas,156exclusões de fronteira e432métricas. Os153hashes do congelamento e as referências de modelos/treino/helpers permanecem iguais.','',f"Congelamento de entradas {gate['registered_at_utc']}; início registrado da inferência {start['started_at_utc']}. {len(threshold_changes)} previsões diferiram ao usar a matriz reconstruída independentemente; detalhes no JSON. Nenhum treino foi executado.",'','| Ano/período | Grupo | h | Acertos controle→candidato / observados | MAE(m) | Máximo(m) |','|---|---|---:|---:|---:|---:|']
 for r in selected:lines.append(f"| {r['period']} | {r['subset']} | {r['horizon_h']} | {r['control_hits']}→{r['candidate_hits']}/{r['observed_targets']} | {r['control_mae']:.6f}→{r['candidate_mae']:.6f} | {r['control_max']:.6f}→{r['candidate_max']:.6f} |")
 lines+=['','As falhas de previsão contam contra a fração sobre alvos observados; truth ausente não recebe acerto. Todas as linhas têm ausências em algum dos24campos iniciais, portanto complete24 é vazio e missing24 coincide com full_schedule. Não houve exclusão por condição favorável de entradas.','','Ganhos/regressões por horizonte estão em independent-changes.csv; os totais conferem com a análise publicada. Não há promoção automática ou alcance certificado de98%.','',*report['limits']]
 (OUT/'README.md').write_text('\n'.join(lines)+'\n');dump('artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']);print(json.dumps(dict(passed=True,checks=len(checks),threshold_changes=len(threshold_changes),tallies=tallies),indent=2),flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
