"""Read local inputs only; write audit artifacts here, never change source/model files."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,csv,re,hashlib
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent;ROOT=P.parents[1];H=ROOT/'outputs/mucum-propagacao-2026-09-21';R=H/'raw';BASE=ROOT/'outputs/mucum-atualizacao-15h-2026-09-21';TZ=timezone(timedelta(hours=-3))
PLANTS={'14 DE JULHO':'julho','MONTE CLARO':'monte','CASTRO ALVES':'castro'}
def ep(s):return datetime.fromisoformat(s).replace(tzinfo=TZ).timestamp()
def iso(t):return datetime.fromtimestamp(float(t),TZ).isoformat()
def num(v):
 try:x=float(v);return x if np.isfinite(x) and x>=0 else np.nan
 except (ValueError,TypeError):return np.nan
sources=[]
def fingerprint(p):
 b=p.read_bytes();sources.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
def dump(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
files=sorted(R.glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv'));frames=[];mapping={};duplicates=[]
for f in files:
 fingerprint(f);d=pd.read_csv(f,sep=';');d['source_file']=f.name;d['source_line']=np.arange(len(d))+2;d['plant']=d.nom_reservatorio.str.strip().map(PLANTS);frames.append(d)
 for r in csv.DictReader(f.open(),delimiter=';'):
  plant=PLANTS[r['nom_reservatorio'].strip()];t=ep(r['din_instante']);key=plant,t
  if key in mapping:duplicates.append({'plant':plant,'time':iso(t),'later_file':f.name})
  mapping[key]={'Q':num(r['val_vazaodefluente']),'I':num(r['val_vazaoafluente']),'source':'ONS','source_file':f.name}
onsmap=dict(mapping)
oldcer=ROOT/'outputs/mucum-bacia-2026-09-21/raw/producao/ceran.json';fingerprint(oldcer);crows=[]
for batch in json.loads(oldcer.read_text()):
 for r in batch['results']:
  plant=r['plant_id'];t=datetime.fromisoformat(r['timestamp']).timestamp();crows.append({'plant':plant,'ts':t,'time':iso(t),'Q':r['outflow'],'I':r['inflow'],'turbined':r['turbined'],'spilled':r['spilled'],'residual':r['residual'],'source':'JSON'})
  if (plant,t) not in mapping:mapping[(plant,t)]={'Q':r['outflow'],'I':r['inflow'],'source':'CERAN_JSON','source_file':str(oldcer.relative_to(ROOT))}
for plant in PLANTS.values():
 f=R/f'ceran-current-{plant}.html';fingerprint(f)
 for tr in re.findall(r'<tr>(.*?)</tr>',f.read_text(),re.S):
  td=re.findall(r'<td>(.*?)</td>',tr,re.S)
  if len(td)!=8:continue
  t=datetime.strptime(td[0],'%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).timestamp();crows.append({'plant':plant,'ts':t,'time':iso(t),'Q':num(td[7]),'I':num(td[3]),'turbined':num(td[4]),'spilled':num(td[5]),'residual':num(td[6]),'source':'HTML'})
  if (plant,t) not in mapping:mapping[(plant,t)]={'Q':num(td[7]),'I':num(td[3]),'source':'CERAN_HTML','source_file':f.name}
fingerprint(H/'telemetria.npz');z=dict(np.load(H/'telemetria.npz'));grid=z['times'];trace=[];rep=[];rawflags={};metrics=[];flags=[];jumps=[];gaps=[]
df=pd.concat(frames,ignore_index=True);df['ts']=pd.to_datetime(df.din_instante);df['epoch']=df.din_instante.map(ep)
df.loc[(df.val_vazaoafluente==0)|(df.val_vazaodefluente==0)].to_csv(P/'all-zero-QI-rows.csv',index=False)
df.loc[df[['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']].isna().any(axis=1)].to_csv(P/'missing-components.csv',index=False)
for plant,g in df.groupby('plant'):
 g=g.sort_values('ts').reset_index(drop=True);t=g.ts;is2359=(t.dt.hour==23)&(t.dt.minute==59);end=t.where(~is2359,t+pd.Timedelta(minutes=1));expected=pd.date_range(end.min(),end.max(),freq='h');missing=expected.difference(pd.DatetimeIndex(end));q=g.val_vazaodefluente;i=g.val_vazaoafluente;components=g[['val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas']].sum(axis=1,min_count=3);balance=q-components
 reasons={
 'balance_abs_gt1_m3s':balance.abs()>1,
 'Q_zero_with_positive_components':(q==0)&(components>1),
 'I_zero_Q_gt100_candidate':(i==0)&(q>100),
 'any_negative_QI':(q<0)|(i<0),
 'missing_QI':q.isna()|i.isna(),
 }
 for ix,row in g.iterrows():
  rr=[r for r,mask in reasons.items() if mask.iloc[ix]]
  if rr:
   flags.append({**row.drop(['ts']).to_dict(),'reasons':'|'.join(rr),'component_sum':None if pd.isna(components.iloc[ix]) else float(components.iloc[ix]),'balance_residual':None if pd.isna(balance.iloc[ix]) else float(balance.iloc[ix])})
   rawflags[(plant,float(row.epoch))]=rr
 for v in ['val_vazaoafluente','val_vazaodefluente']:
  delta=g[v].diff();delta_h=end.diff().dt.total_seconds()/3600;ok=delta_h.eq(1)
  # Triage only: no inference that a physical flood rise is erroneous.
  selected=ok & (delta.abs()>=500)
  for ix in np.flatnonzero(selected):jumps.append({'plant':plant,'variable':v,'time':str(t.iloc[ix]),'previous':float(g[v].iloc[ix-1]),'value':float(g[v].iloc[ix]),'delta_m3s_h':float(delta.iloc[ix]),'source_file':g.source_file.iloc[ix],'source_line':int(g.source_line.iloc[ix]),'interpretation':'REVIEW_ONLY_NOT_INVALIDATED'})
 for tt in missing:gaps.append({'plant':plant,'missing_hour_end_assuming_2359_as24':str(tt)})
 metrics.append({'plant':plant,'rows':len(g),'first':str(t.min()),'last':str(t.max()),'missing_rows_interpreted_grid':len(missing),'duplicates':int(t.duplicated().sum()),'timestamps_2359':int(is2359.sum()),'null_Q':int(q.isna().sum()),'null_I':int(i.isna().sum()),'zero_Q':int((q==0).sum()),'zero_I':int((i==0).sum()),'negative_Q':int((q<0).sum()),'negative_I':int((i<0).sum()),'balance_complete_rows':int(balance.notna().sum()),'balance_abs_gt1':int((balance.abs()>1).sum()),'balance_abs_gtmax10_or1pctQ':int((balance.abs()>np.maximum(10,q.abs()*.01)).sum()),'zero_Q_positive_components':int(((q==0)&(components>1)).sum()),'max_Q':float(q.max()),'max_I':float(i.max()),'min_Q':float(q.min()),'min_I':float(i.min()),'unique_flags':int(np.column_stack(list(reasons.values())).any(axis=1).sum())})
 # Exact recreation of production asof: no 23:59 adjustment here.
 tt=np.array(sorted(x[1] for x in mapping if x[0]==plant));pos=np.searchsorted(tt,grid,side='right')-1;safe=np.maximum(pos,0);ok=(pos>=0)&(grid-tt[safe]<=5400)
 for variable in ['Q','I']:
  vals=np.array([mapping[(plant,t)][variable] for t in tt]);recreated=np.where(ok,vals[safe],np.nan);actual=z[f'{plant}:{variable}'];equal=np.isclose(recreated,actual,equal_nan=True,rtol=0,atol=1e-9)
  rep.append({'key':f'{plant}:{variable}','points':len(grid),'mismatch_count':int((~equal).sum()),'missing_points':int(np.isnan(actual).sum()),'zero_points':int((actual==0).sum())})
 for j in np.flatnonzero(ok):
  entry=mapping[(plant,tt[safe[j]])];rr=rawflags.get((plant,tt[safe[j]]),[])
  if rr:trace.append({'plant':plant,'grid_time':iso(grid[j]),'source_time':iso(tt[safe[j]]),'source_epoch':tt[safe[j]],'age_min':(grid[j]-tt[safe[j]])/60,'Q':float(z[plant+':Q'][j]),'I':float(z[plant+':I'][j]),'reasons':'|'.join(rr)})
# Check that identified source anomalies survive the actual frozen training array.
fingerprint(BASE/'telemetria-latencia.npz');fz=dict(np.load(BASE/'telemetria-latencia.npz'));ft=fz['times'];ags=list(csv.DictReader((BASE/'idades-fontes.csv').open()));fingerprint(BASE/'idades-fontes.csv');ftrace=[]
for r in trace:
 lag=float(next(x['delay_minutes'] for x in ags if x['source']==r['plant']))*60;when=ep(r['grid_time'])+lag;k=int(np.searchsorted(ft,when))
 if k<len(ft) and ft[k]==when:
  ftrace.append({**r,'frozen_delayed_time':iso(when),'frozen_Q':float(fz[r['plant']+':Q'][k]),'frozen_I':float(fz[r['plant']+':I'][k]),'QI_equal_to_source_grid':bool(np.isclose(fz[r['plant']+':Q'][k],r['Q'],equal_nan=True) and np.isclose(fz[r['plant']+':I'][k],r['I'],equal_nan=True))})
# Hourly model inputs depend on current values and 1/3/6h lags. Only mark exposure, no fitting/target inspection.
exposure=[]
for plant in PLANTS.values():
 current={ep(r['frozen_delayed_time']) for r in ftrace if r['plant']==plant};affected={t+lag*3600 for t in current for lag in [0,1,3,6]}
 for t in sorted(affected):
  if t in set(ft[::4]):exposure.append({'plant':plant,'origin':iso(t),'dependency':'current_or_1_3_6h_input','before_final_cutoff':t<ep('2026-09-21T00:00:00')})
comp=[]
for r in crows:
 key=r['plant'],r['ts']
 if key in onsmap:
  a=onsmap[key];comp.append({**r,'ONS_Q':a['Q'],'ONS_I':a['I'],'delta_Q':r['Q']-a['Q'],'delta_I':r['I']-a['I'],'CERAN_Q_minus_turbined_spilled':r['Q']-r['turbined']-r['spilled'],'CERAN_Q_minus_all_including_residual':r['Q']-r['turbined']-r['spilled']-r['residual']})
for name,rows in [('anomalies.csv',flags),('jumps-ge500-review.csv',jumps),('gaps.csv',gaps),('telemetry-anomaly-trace.csv',trace),('frozen-training-anomaly-trace.csv',ftrace),('upstream-feature-exposure.csv',exposure),('ceran-ons-overlaps.csv',comp)]:
 pd.DataFrame(rows).to_csv(P/name,index=False)
for f in [ROOT/'scripts/hydro_routing_data.py',ROOT/'scripts/hydro_model.py',ROOT/'scripts/hydro_latency_forecast.py',ROOT/'scripts/hydro_hourly_models.py',ROOT/'scripts/hydro_routing_fit.py',R/'ons-manifest.json']:fingerprint(f)
manifest=json.loads((R/'ons-manifest.json').read_text());hashchecks=[]
for r in manifest:
 match=next(x for x in sources if x['path'].endswith('/'+r['file']));hashchecks.append({'file':r['file'],'expected_available':'sha256_filtered' in r,'match':match['sha256']==r['sha256_filtered'] if 'sha256_filtered' in r else None,'source_url_in_manifest':r.get('url')})
dump('source-fingerprints.json',sources);dump('summary.json',{'audited_at':datetime.now(timezone.utc).isoformat(),'source_rows':len(df),'source_month_files':len(files),'sources_merge_counts':dict(pd.Series([x['source'] for x in mapping.values()]).value_counts().map(int)),'plants':metrics,'telemetry_reproduction':rep,'ONS_duplicate_keys':duplicates,'manifest_checks':hashchecks,'anomaly_source_rows':len(flags),'anomaly_quarterhour_exposures':len(trace),'frozen_matching_rows':sum(x['QI_equal_to_source_grid'] for x in ftrace),'frozen_compared_rows':len(ftrace),'upstream_hourly_feature_exposures':len(exposure),'training_performed':False,'downloads_performed':False})
print(json.dumps({'plants':metrics,'reproduction':rep,'anomalies':len(flags),'frozen_matches':sum(x['QI_equal_to_source_grid'] for x in ftrace),'frozen_compared':len(ftrace),'exposure':len(exposure)},indent=2))
