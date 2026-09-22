"""Offline audit; all generated artifacts stay in this folder. No model/train/test mutation.
Requires numpy/pandas and DuckDB1.4.4 installed in _runtime for Parquet.
"""
from pathlib import Path
import sys,json,xml.etree.ElementTree as ET,hashlib,datetime
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(P/'_runtime'));import duckdb
# Reuse frozen normalization implementation, with its main disabled and output forced here.
ns={'__name__':'audit_ana_helper','__file__':str(ROOT/'scripts/hydro_collect_flood_history.py')};exec(compile((P/'ana-helper-snapshot.txt').read_text(),'ana-helper-snapshot.txt','exec'),ns);ns['OUT']=P
man=json.loads((P/'source-manifest.json').read_text());rows=[]
for m in man:
 if not m['file'].endswith('.xml') or 'sha256' not in m:continue
 b=(P/m['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==m['sha256'];doc=ET.fromstring(b);items=[{x.tag.split('}')[-1]:x.text for x in r} for r in doc.iter() if r.tag.split('}')[-1]=='DadosHidrometereologicos'];m['parsed_rows']=len(items);m['source_errors']=[r.text for r in doc.iter() if r.tag.split('}')[-1]=='Error' and r.text]
 rows.extend([{**r,'source_file':m['file']} for r in items])
ana=ns['summarize']('ana-mucum',[('2023-09-01','2023-09-30')],rows)
(P/'source-manifest.json').write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n')
q=duckdb.connect();f=P/'raw/ons-2023-09.parquet';d=q.execute('select * from read_parquet(?)',[str(f)]).fetchdf();targets={'JIUHQJ':'14 DE JULHO','JIUHMC':'MONTE CLARO','JIUHCA':'CASTRO ALVES'}
inventory=d.groupby(['id_reservatorio','nom_reservatorio','cod_usina'],dropna=False).size().reset_index(name='rows');inventory.to_csv(P/'ons-reservoir-inventory.csv',index=False)
d=d[d.id_reservatorio.isin(targets)].copy().sort_values(['id_reservatorio','din_instante']);d.to_csv(P/'ons-ceran-source-values.csv',index=False);summary=[];flags=[];missing=[];norm=[]
def runs(values):
 out=[]
 for t in sorted(set(values)):
  if out and t==out[-1]['end']+pd.Timedelta(hours=1):out[-1]['end']=t;out[-1]['hours']+=1
  else:out.append({'start':t,'end':t,'hours':1})
 return [{'start_hour_end':str(r['start']),'end_hour_end':str(r['end']),'hours':r['hours']} for r in out]
for rid,name in targets.items():
 g=d[d.id_reservatorio==rid].copy();t=g.din_instante;is2359=(t.dt.hour==23)&(t.dt.minute==59);et=t.where(~is2359,t+pd.Timedelta(minutes=1));expected=pd.date_range('2023-09-01 01:00','2023-10-01 00:00',freq='h');gaps=expected.difference(pd.DatetimeIndex(et));vv={}
 for col in [c for c in d if c.startswith('val_')]:
  vals=g[col];v=vals.dropna();vv[col]={'present':int(vals.notna().sum()),'missing':int(vals.isna().sum()),'zeros':int((vals==0).sum()),'negative':int((vals<0).sum()),'value9999_count':int((vals==9999).sum()),'min':None if v.empty else float(v.min()),'max':None if v.empty else float(v.max()),'missing_hour_end_runs':runs(set(gaps)|set(et[vals.isna()])),'zero_hour_end_runs':runs(et[vals==0])}
 comp=g[['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']].sum(axis=1,min_count=3);res=g.val_vazaodefluente-comp
 for ix,row in g.iterrows():
  reasons=[]
  if row.val_vazaodefluente==0 and comp.loc[ix]>0:reasons.append('ZERO_Q_WITH_POSITIVE_COMPONENT_SUM')
  if pd.notna(res.loc[ix]) and abs(res.loc[ix])>1:reasons.append('BALANCE_RESIDUAL_GT1_REVIEW_NOT_OFFICIAL_TOLERANCE')
  if row[['val_vazaodefluente','val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']].lt(0).any():reasons.append('NEGATIVE_OUTFLOW_COMPONENT_SCHEMA_REVIEW')
  if reasons:flags.append({**row.to_dict(),'balance_residual_m3s':res.loc[ix],'qc_review':'|'.join(reasons)})
 g['hour_end_local_interpreted']=et;g['hour_end_utc_assuming_brasilia']=et.dt.tz_localize('America/Sao_Paulo').dt.tz_convert('UTC');g['timezone_status']='ONS_NORM_BRASILIA_PERIOD_EXPORT_LINK_UNVERIFIED';g['hour2359_interpretation']=is2359.map({True:'23:59_AS_24:00_UNVERIFIED',False:'WHOLE_HOUR_ORIGINAL'});g['quality_status']='AGENT_REPORTED_NOT_VALIDATED_BY_ONS';g['balance_residual_m3s']=res;norm.append(g)
 for tt in gaps:missing.append({'reservoir_id':rid,'name':name,'missing_hour_end_interpreted':str(tt)})
 s={'reservoir_id':rid,'name':name,'codes_in_file':g.cod_usina.dropna().unique().tolist(),'rows':len(g),'expected_hours':720,'missing_rows':len(gaps),'missing_row_runs':runs(gaps),'first_original':str(t.min()),'last_original':str(t.max()),'duplicate_timestamps':int(t.duplicated().sum()),'timestamps2359':int(is2359.sum()),'variables':vv,'balance_complete_rows':int(res.notna().sum()),'balance_abs_residual_gt1':int((res.abs()>1).sum()),'zeroQ_positive_components':int(((g.val_vazaodefluente==0)&(comp>0)).sum())};summary.append(s)
pd.concat(norm).to_csv(P/'ons-ceran-interpreted.csv',index=False);pd.DataFrame(flags).to_csv(P/'ons-semantic-review.csv',index=False);pd.DataFrame(missing,columns=['reservoir_id','name','missing_hour_end_interpreted']).to_csv(P/'ons-missing-hours.csv',index=False)
result={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'2023-09 Taquari-Antas','status':'AUDIT_ONLY_NO_NEW_HOLDOUT_CLAIM','previous_exposure':'Sep5 Muçum sample and SGB2023 peak/marks already inspected in previous research','interpolation':'NONE','training':'NONE','ana':ana,'ons':summary};(P/'catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('ANA',ana['level_counts'],ana['grid_counts'])
for s in summary:print('ONS',s['name'],'rows',s['rows'],'missing',s['missing_rows'],'Q',s['variables']['val_vazaodefluente']['present'],'I',s['variables']['val_vazaoafluente']['present'],'Qzeros',s['variables']['val_vazaodefluente']['zeros'],'balance>1',s['balance_abs_residual_gt1'],'gaps',s['missing_row_runs'][:5])
