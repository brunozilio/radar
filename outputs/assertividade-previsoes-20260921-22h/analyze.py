"""Offline forecast verification and numeric diagnosis, preserving original issues."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from collections import Counter, defaultdict
import csv, hashlib, json, math, sys

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import hydro_prospective_ledger as ledger
from hydro_verification_metrics import quantile
TZ=timezone(timedelta(hours=-3))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def iso(value): return ledger.timestamp(value).astimezone(TZ).isoformat()
def save(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(name,rows):
 if not rows: return
 keys=list(dict.fromkeys(k for row in rows for k in row))
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def hit(pred,obs,tolerance=.5): return abs(Decimal(str(pred))-Decimal(str(obs)))<=Decimal(str(tolerance))
def stats(rows):
 matched=[r for r in rows if r['status']=='matched'];e=[r['error_m'] for r in matched];a=[abs(v) for v in e];n=len(a)
 return {'registered_points':len(rows),'status_counts':dict(Counter(r['status'] for r in rows)),
  'n':n,'hits':sum(hit(r['forecast_m'],r['observed_m']) for r in matched),'misses':sum(not hit(r['forecast_m'],r['observed_m']) for r in matched),
  'accuracy_percent':100*sum(hit(r['forecast_m'],r['observed_m']) for r in matched)/n if n else None,
  'mae_m':sum(a)/n if n else None,'rmse_m':math.sqrt(sum(v*v for v in e)/n) if n else None,
  'bias_m':sum(e)/n if n else None,'p90_abs_m':quantile(a,.9),'p98_abs_m':quantile(a,.98),'max_abs_m':max(a) if n else None,
  'underpredictions':sum(v<0 for v in e),'overpredictions':sum(v>0 for v in e),
  'unique_targets':len({r['valid_at'] for r in matched}),'distinct_issues':len({r['forecast_record'] for r in matched}),
  'thresholds':{str(t):{'hits':sum(hit(r['forecast_m'],r['observed_m'],t) for r in matched),'percent':100*sum(hit(r['forecast_m'],r['observed_m'],t) for r in matched)/n if n else None} for t in [.2,.5,1.]}}

def pair(issue,point,observations,cutoff):
 at=ledger.timestamp(point['valid_at']);issued=ledger.timestamp(issue['registered_at']);actual=(at-issued).total_seconds()/3600
 obs=observations.get(at)
 status='not_due' if at>cutoff else 'registered_after_target' if issued>=at else 'missing_exact_observation' if obs is None else 'invalid_or_unapproved_observation' if obs['quality']!='Dado aprovado' or obs['level_m'] is None else 'matched'
 error=float(Decimal(str(point['forecast_m']))-Decimal(str(obs['level_m']))) if status=='matched' else None
 return {**issue,**point,'actual_lead_h':actual,'minimum_verified_lead_h':math.floor(actual),'status':status,
  'observed_m':obs['level_m'] if status=='matched' else None,'error_m':error,'abs_error_m':abs(error) if error is not None else None,
  'hit_within_050m':hit(point['forecast_m'],obs['level_m']) if status=='matched' else None}

def feature_names():
 names=[]
 for station in ['86510000','86472000','86472600','86500000']:
  names += [station+':H']+[station+':dH'+str(h) for h in (.5,1,2,4,8)]
 for plant in ['julho','monte','castro']:
  names += [plant+':Q06',plant+':Q',plant+':I']+[plant+':dQ'+str(h) for h in (1,2,4,8)]
 for group in ['Baixo Antas','Carreiro','Prata-Turvo','Alto Antas','Tainhas']:
  names += [group+':'+kind+str(h) for h in (1,3,6,12,24,48) for kind in ('P','C')]+[group+':P3lag'+str(h) for h in (3,6,12)]
 for model in ['gfs_seamless','ecmwf_ifs025','icon_global']:
  for loc in range(5): names += [f'{model}:loc{loc}:futureP{h}' for h in (3,6,9,12)]
 assert len(names)==180
 return names

def run():
 collection=json.loads((OUT/'collection.json').read_text());cutoff=max(ledger.timestamp(r['retrieved_at']) for r in collection)
 for c in collection: assert sha(OUT/c['file'])==c['sha256']
 records=[r for r in ledger.read_records(ledger.DEFAULT) if ledger.timestamp(r['recorded_at'])<=cutoff];bysha={r['sha256']:r for r in records}
 observations=ledger.latest_observations(ledger.DEFAULT,records,cutoff)
 fresh=ledger.parse_ana((OUT/'ana-mucum.xml').read_bytes(),'86510000','ANA:86510000:reference-unverified')
 fresh_at=ledger.timestamp(next(c['retrieved_at'] for c in collection if c['file']=='ana-mucum.xml'))
 for o in fresh:
  if ledger.timestamp(o['valid_at'])<=fresh_at: observations[(o['station_id'],o['datum_id'],ledger.timestamp(o['valid_at']))]=(o,'fresh-ana:'+sha(OUT/'ana-mucum.xml'))
 pairs=ledger.evaluate(ledger.DEFAULT,at=cutoff,records=records,observations=observations)
 active=[p for p in pairs if not ledger.is_retired_model(p['model_id'])]
 observed={key[2]:o for key,(o,receipt) in observations.items() if key[:2]==('86510000','ANA:86510000:reference-unverified')}
 original_records=[r for r in records if r['kind'] in ('forecast_issue','archival_forecast_import') and not ledger.is_retired_model(r['payload']['model_id'])]
 save('forecast-records.json',original_records);save('observations.json',sorted(observed.values(),key=lambda o:o['valid_at']))
 for p in active:
  source=bysha[p['forecast_record']];meta=source['payload'];p['registered_at']=iso(p['registered_at']);p['reference_at']=meta['reference_at']
  p['cohort']='archival' if p['evidence_kind']=='archival_forecast_import' else 'manual_revision' if meta.get('manual_revision') else 'scheduled_local'
  p['error_m']=float(Decimal(str(p['forecast_m']))-Decimal(str(p['observed_m']))) if p['status']=='matched' else None
  p['hit_within_050m']=hit(p['forecast_m'],p['observed_m']) if p['status']=='matched' else None
  last=meta.get('last_observed',{});p['anchor_at']=last.get('last_time');p['anchor_m']=last.get('value')
  p['anchor_age_at_issue_minutes']=(ledger.timestamp(p['registered_at'])-ledger.timestamp(p['anchor_at'])).total_seconds()/60 if p['anchor_at'] else None
 # Site API supplies the last revision per round. Preserved older public snapshots
 # form a separate incomplete revision sample, never separate independent events.
 site_latest=[];site_revisions=[];seen=set()
 site_paths=list(sorted(OUT.glob('site-round-*.json')))+[ROOT/'outputs/validacao-previsao-site-6h/first-public-projection.json',ROOT/'outputs/validacao-previsao-site-6h/automatic-refresh.json']
 for path in site_paths:
  doc=json.loads(path.read_text());s=doc.get('projection',doc)
  if not s: continue
  for model in s['models']:
   identity=(s['generatedAt'],model['id'])
   if identity in seen: continue
   seen.add(identity)
   issue={'forecast_record':f"site:{s['generatedAt']}:{model['id']}",'registered_at':s['generatedAt'],'reference_at':s['referenceAt'],'model_version':s['modelVersion'],'model_id':model['id'],'cohort':'site_saved_revision','source_file':str(path.relative_to(ROOT))}
   for q in model['points']:
    row=pair(issue,{'valid_at':q['timestamp'],'forecast_m':q['level'],'nominal_lead_h':(ledger.timestamp(q['timestamp'])-ledger.timestamp(s['referenceAt'])).total_seconds()/3600},observed,cutoff)
    site_revisions.append(row)
    if path.parent==OUT: site_latest.append(row)
 old=json.loads((ROOT/'outputs/comparacao-sem-previsao-chuva-22h-20260921/result.json').read_text());no_weather=[]
 for q in old['points']:
  no_weather.append(pair({'forecast_record':'observed-only:'+old['computed_at'],'registered_at':old['computed_at'],'reference_at':old['reference_at'],'model_version':'observed-only-local-comparison','cohort':'not_prospective_diagnostic'}, {'valid_at':q['target'],'forecast_m':q['observed_only_m']},observed,cutoff))
 scheduled=[p for p in active if p['cohort']=='scheduled_local']
 cohorts={key:stats([p for p in active if p['cohort']==key]) for key in ['scheduled_local','manual_revision','archival']}
 cohorts.update({'site_latest_rounds':stats(site_latest),'site_preserved_revisions_incomplete':stats(site_revisions),'observed_only_diagnostic':stats(no_weather)})
 groups={}
 for p in scheduled:
  for label,key in [('actual_lead_h',str(p['minimum_verified_lead_h'])),('issue',p['registered_at']),('version',p['model_version'])]: groups.setdefault((label,key),[]).append(p)
 grouped=[{'group':label,'key':key,**stats(rows)} for (label,key),rows in sorted(groups.items())]
 summary={'verification_cutoff':cutoff.isoformat(),'observation_capture_at':fresh_at.isoformat(),'latest_observation':max((o for o in observed.values() if o['level_m'] is not None and o['quality']=='Dado aprovado'),key=lambda o:o['valid_at']),
  'threshold_m':.5,'formula':'100 * count(abs(predicted-observed)<=0.50) / count(exact approved matched observations)',
  'ledger_records':len(records),'ledger_tip_sha256':records[-1]['sha256'],'cohorts':cohorts,
  'scheduled_at_least_1h':stats([p for p in scheduled if p['actual_lead_h']>=1]),
  'scheduled_latest_three_references':stats([p for p in scheduled if ledger.timestamp(p['reference_at'])>=ledger.timestamp('2026-09-21T19:00:00-03:00')]),
  'grouped':grouped,'goal_eligible_n':sum(p['goal_eligible'] for p in scheduled),'independent_events_certified':0,
  'site_full_revision_history_available':False,'limitations':['Observed timestamps matched exactly, no interpolation or carrying forward.','The 0.50 m definition predates this evaluation.','Scheduled local versions remain stratified; aggregate is descriptive, not accuracy of the site or a single version.','Site revisions are an incomplete retrieved sample; API rounds keep last revision.','No-weather comparison was not prospectively issued; its targets have not matured in this snapshot.','One ongoing flood; overlapping horizons and repeated targets are dependent.','Legacy ANA endpoint timezone and gauge datum remain unverified.','Technical model replay and error decomposition are not physical causal attribution.']}
 save('summary.json',summary);csvsave('verification-local.csv',active);csvsave('verification-site-latest.csv',site_latest);csvsave('verification-site-revisions.csv',site_revisions);csvsave('verification-observed-only.csv',no_weather);save('grouped.json',grouped)
 # Reproduce original inference and investigate only measured failures.
 import numpy as np
 import joblib
 from threadpoolctl import threadpool_limits
 names=feature_names();diagnostics=[];replays=[];range_rows=[];inputs=[]
 training_cutoff=ledger.timestamp('2026-09-21T00:00:00-03:00').timestamp()
 with threadpool_limits(limits=2):
  for rec in original_records:
   if rec['kind']!='forecast_issue': continue
   pp=[p for p in active if p['forecast_record']==rec['sha256'] and p['status']=='matched'];packet=rec['payload']
   if not pp: continue
   f=next(bysha[ref]['payload'] for ref in packet['input_receipts'] if bysha[ref]['payload'].get('source_path','').endswith('radar-features.npz'))
   feature_path=ledger.DEFAULT/f['blob'];assert sha(feature_path)==f['blob_sha256'];z=dict(np.load(feature_path));F=z['features'];anchor=float(z['base'][-1]);assert abs(anchor-packet['last_observed']['value'])<1e-12
   for j,name in enumerate(names):inputs.append({'forecast_record':rec['sha256'],'reference_at':packet['reference_at'],'column':j,'name':name,'value':float(F[-1,j]) if np.isfinite(F[-1,j]) else None})
   for p in pp:
    lead=int(p['nominal_lead_h']);artifact=next(a for a in packet['model_artifacts'] if Path(a['path']).name==f'radar-{lead}.joblib')
    model_path=ledger.DEFAULT/artifact['blob'] if artifact.get('blob') else Path(artifact['path']);assert sha(model_path)==artifact['sha256'];model=joblib.load(model_path)
    replay=float(model.predict(F[-1:])[0]+anchor);difference=replay-p['forecast_m'];assert abs(difference)<1e-9
    replays.append({'forecast_record':rec['sha256'],'valid_at':p['valid_at'],'replay_m':replay,'original_m':p['forecast_m'],'difference_m':difference,'artifact_sha256':artifact['sha256'],'features_sha256':f['blob_sha256']})
    if p['cohort']!='scheduled_local' or p['hit_within_050m']: continue
    reference=ledger.timestamp(packet['reference_at']);anchor_at=ledger.timestamp(packet['last_observed']['last_time']);valid=ledger.timestamp(p['valid_at']);at_ref=observed.get(reference);at_anchor=observed.get(anchor_at)
    target=np.r_[z['truth'][lead:],np.full(lead,np.nan)];delta=target-z['base'];train=np.where(np.isfinite(z['base'])&np.isfinite(target)&np.isfinite(F[:,:24]).all(axis=1)&(z['times']+lead*3600<training_cutoff))[0]
    actual_delta=p['observed_m']-anchor;pred_delta=p['forecast_m']-anchor;hours=(valid-anchor_at).total_seconds()/3600
    ref_level=at_ref['level_m'] if at_ref and at_ref['quality']=='Dado aprovado' else None
    d={k:p[k] for k in ['forecast_record','registered_at','reference_at','valid_at','forecast_m','observed_m','error_m','actual_lead_h','anchor_age_at_issue_minutes']}
    d.update(anchor_m=anchor,anchor_at=packet['last_observed']['last_time'],anchor_revision_m=(at_anchor['level_m']-anchor) if at_anchor and at_anchor['level_m'] is not None else None,
     predicted_rise_m=pred_delta,observed_rise_m=actual_delta,implied_average_rise_m_h=pred_delta/hours,observed_average_rise_m_h=actual_delta/hours,
     observed_reference_m=ref_level,anchor_to_reference_rise_m=(ref_level-anchor) if ref_level is not None else None,
     remaining_increment_error_m=pred_delta-(p['observed_m']-ref_level) if ref_level is not None else None,
     training_rows=len(train),training_delta_min_m=float(np.min(delta[train])),training_delta_max_m=float(np.max(delta[train])),
     training_delta_percentile=float(np.mean(delta[train]<=actual_delta)*100),response_above_training_max=bool(actual_delta>np.max(delta[train])),
     current_missing_features=int(np.isnan(F[-1]).sum()),current_missing_level24=int(np.isnan(F[-1,:24]).sum()),cause_status='Observed response underpredicted; range and latency are diagnostic evidence, not isolated causal shares')
    if ref_level is not None: assert abs(-(ref_level-anchor)+d['remaining_increment_error_m']-p['error_m'])<1e-9
    outside=[]
    for j,name in enumerate(names):
     x=F[train,j];x=x[np.isfinite(x)];v=F[-1,j]
     if x.size and np.isfinite(v) and (v<x.min() or v>x.max()):
      outside.append(name);range_rows.append({'forecast_record':rec['sha256'],'valid_at':p['valid_at'],'feature':name,'value':float(v),'train_min':float(x.min()),'train_max':float(x.max()),'kind':'future_weather' if j>=120 else 'observed'})
    d['out_of_range_features']=outside;diagnostics.append(d)
 csvsave('inference-replay.csv',replays);save('error-diagnosis.json',diagnostics);csvsave('error-diagnosis.csv',[{**d,'out_of_range_features':';'.join(d['out_of_range_features'])} for d in diagnostics]);csvsave('input-features.csv',inputs);csvsave('input-range-exceedances.csv',range_rows)
 save('integrity.json',{'original_issues_replayed':len(replays),'maximum_replay_error_m':max(abs(r['difference_m']) for r in replays),'ledger_hash_chain_verified':True,'observations_blob_hashes_verified':True,'sources_modified':False,'trained':False,'published':False})
 print(json.dumps({'cutoff':summary['verification_cutoff'],'latest_observation':summary['latest_observation'],'cohorts':cohorts,'scheduled_at_least_1h':summary['scheduled_at_least_1h'],'replayed':len(replays),'misses_diagnosed':len(diagnostics)},ensure_ascii=False,indent=2))

if __name__=='__main__': run()
