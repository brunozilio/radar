"""Offline audit only. No model input writes or network requests.
Run with bundled Python; uses DuckDB 1.4.4 installed in this folder's _runtime.
23:59 -> next midnight is an explicit interpretation, not verified export contract.
"""
from pathlib import Path
import sys,json,hashlib,datetime,calendar
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'_runtime'))
import duckdb
import pandas as pd
TARGETS={'JIUHQJ':('14 DE JULHO',99),'JIUHMC':('MONTE CLARO',98),'JIUHCA':('CASTRO ALVES',97)}
con=duckdb.connect();summaries=[];all_norm=[];inventories=[]
def runs(times):
 times=sorted(set(times));out=[]
 for t in times:
  if out and t==out[-1]['end']+pd.Timedelta(hours=1):out[-1]['end']=t;out[-1]['hours']+=1
  else:out.append({'start':t,'end':t,'hours':1})
 return [{'start_hour_end':str(x['start']),'end_hour_end':str(x['end']),'hours':x['hours']} for x in out]
for month in ['2024-05','2020-07']:
 path=P/'raw'/f'ons-{month}.parquet';df=con.execute('select * from read_parquet(?)',[str(path)]).fetchdf()
 inventory=df.groupby(['id_reservatorio','nom_reservatorio','cod_usina'],dropna=False).size().reset_index(name='rows');inventory.to_csv(P/f'inventory-{month}.csv',index=False)
 subset=df[df.id_reservatorio.isin(TARGETS)].sort_values(['id_reservatorio','din_instante']).copy();subset.to_csv(P/f'ceran-{month}-source-values.csv',index=False)
 inventories.append({'month':month,'all_source_rows':len(df),'all_source_reservoirs':int(df.id_reservatorio.nunique()),'selected_rows':len(subset),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'schema':[(x,str(df[x].dtype)) for x in df.columns]})
 y,m=map(int,month.split('-'));end=pd.Timestamp(y,m,calendar.monthrange(y,m)[1])+pd.Timedelta(days=1)
 expected=pd.date_range(pd.Timestamp(y,m,1)+pd.Timedelta(hours=1),end,freq='h')
 for rid,(name,code) in TARGETS.items():
  g=subset[subset.id_reservatorio==rid].copy();assert set(g.nom_reservatorio)=={name};assert set(g.cod_usina)=={code}
  ts=g.din_instante;is2359=(ts.dt.hour==23)&(ts.dt.minute==59)&(ts.dt.second==0);whole=(ts.dt.minute==0)&(ts.dt.second==0)
  adjusted=ts.where(~is2359,ts+pd.Timedelta(minutes=1));offgrid=~(is2359|whole)
  g['hour_end_local_interpreted']=adjusted;g['hour_start_local_interpreted']=adjusted-pd.Timedelta(hours=1)
  g['timestamp_interpretation']=is2359.map({True:'23:59_AS_24:00_UNVERIFIED',False:'SOURCE_WHOLE_HOUR'})
  g['hour_end_utc_assuming_brasilia']=adjusted.dt.tz_localize('America/Sao_Paulo').dt.tz_convert('UTC')
  g['timezone_status']='ONS_NORM_BRASILIA_EXPORT_AND_PERIOD_LINK_UNVERIFIED';g['quality_status']='AGENT_REPORTED_NOT_VALIDATED_BY_ONS';g['source_month']=month;all_norm.append(g)
  slots=set(adjusted[~offgrid]);missing=set(expected)-slots;outside=slots-set(expected)
  metrics={}
  for col in [x for x in df if x.startswith('val_')]:
   vals=g[col];nonnull=vals.dropna();metrics[col]={'present':int(vals.notna().sum()),'null':int(vals.isna().sum()),'zero':int((vals==0).sum()),'negative':int((vals<0).sum()),'zero_hour_end_runs':runs(adjusted[vals==0]),'min':None if len(nonnull)==0 else float(nonnull.min()),'max':None if len(nonnull)==0 else float(nonnull.max()),'unavailable_hour_end_runs':runs(missing|set(adjusted[vals.isna()]))}
  residual=g.val_vazaodefluente-(g.val_vazaoturbinada+g.val_vazaovertida+g.val_vazaooutrasestruturas)
  significant=residual.abs()>1.0
  g.loc[significant].assign(balance_residual_m3s=residual[significant]).to_csv(P/f'balance-review-{rid}-{month}.csv',index=False)
  s={'month':month,'id_reservatorio':rid,'name':name,'cod_usina':code,'source_basin_labels':list(g.nom_bacia.unique()),'source_rows':len(g),'nominal_month_hours':len(expected),'duplicate_original_timestamps':int(ts.duplicated().sum()),'duplicate_interpreted_hour_ends':int(adjusted.duplicated().sum()),'timestamps_2359':int(is2359.sum()),'other_off_grid_rows':int(offgrid.sum()),'missing_rows_on_interpreted_grid':len(missing),'missing_row_runs':runs(missing),'outside_interpreted_grid':[str(t) for t in sorted(outside)],'variables':metrics,'balance_check':{'formula':'QDEF-QTUR-QVER-QOTR; no missing-as-zero','complete_component_rows':int(residual.notna().sum()),'abs_residual_gt_1_m3s':int(significant.sum()),'max_abs_residual':None if residual.dropna().empty else float(residual.abs().max())},'first_timestamp_original':str(ts.min()),'last_timestamp_original':str(ts.max())}
  summaries.append(s)
(P/'summary.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duckdb_version':duckdb.__version__,'inference_policy':'23:59 end-of-day interpretation and Brasília timezone explicitly labelled; no imputation, validation, training or model promotion','source_inventory':inventories,'plant_months':summaries},ensure_ascii=False,indent=2)+'\n')
pd.concat(all_norm).to_csv(P/'ceran-all-interpreted.csv',index=False)
for s in summaries:
 print(s['month'],s['name'],'rows',s['source_rows'],'missing',s['missing_rows_on_interpreted_grid'],'afl',s['variables']['val_vazaoafluente']['present'],'def',s['variables']['val_vazaodefluente']['present'],'23:59',s['timestamps_2359'],'offgrid',s['other_off_grid_rows'],'balance',s['balance_check'])
 print('longest missing',sorted(s['missing_row_runs'],key=lambda x:x['hours'],reverse=True)[:3])
