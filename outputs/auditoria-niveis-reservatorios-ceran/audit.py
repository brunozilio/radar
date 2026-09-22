from pathlib import Path
import csv,json,hashlib,re,html,datetime,math,collections
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];RAW=R/'outputs/mucum-propagacao-2026-09-21/raw';H=R/'outputs/mucum-hourly-20260921T180020-0300/raw'
cols=['val_nivelmontante','val_niveljusante'];records=[];manifest=[]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def dump(f,x):(P/f).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(f,rows,fields=None):
 with (P/f).open('w') as q:
  w=csv.DictWriter(q,fieldnames=fields or list(rows[0]) if rows else fields or ['no_records']);w.writeheader();w.writerows(rows)
for f in sorted(RAW.glob('DADOS_HIDROLOGICOS_HO_*-ceran.csv')):
 manifest.append({'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':sha(f),'role':'historical ONS source-derived CSV'})
 for line,r in enumerate(csv.DictReader(f.open(),delimiter=';'),2):
  records.append({**r,'source_file':str(f.relative_to(R)),'source_line':line})
d=pd.DataFrame(records);d['t']=pd.to_datetime(d.din_instante,errors='coerce');d['plant']=d.id_reservatorio.str.strip();susp=[];jumps=[];gaps=[];dups=[];summary=[]
for rid,g in d.groupby('plant'):
 g=g.sort_values('t',kind='stable').copy();rawdups=g[g.duplicated('t',keep=False)]
 for _,r in rawdups.iterrows():dups.append({k:r[k] for k in ['plant','din_instante',*cols,'source_file','source_line']})
 t=g.t;canonical=t.where(~((t.dt.hour==23)&(t.dt.minute==59)),t+pd.Timedelta(minutes=1));expected=pd.date_range(canonical.min(),canonical.max(),freq='h');missing=expected.difference(pd.DatetimeIndex(canonical));off=g[(canonical.dt.minute!=0)|(canonical.dt.second!=0)]
 for tt in missing:gaps.append({'plant':rid,'missing_hour_end_interpreted':str(tt),'mapping':'23:59 to24:00 hypothesis for gap inventory only'})
 out={'plant':rid,'name':g.nom_reservatorio.iloc[0].strip(),'rows':len(g),'first_original':str(t.min()),'last_original':str(t.max()),'duplicate_rows':len(rawdups),'invalid_timestamp_rows':int(t.isna().sum()),'labels2359':int(((t.dt.hour==23)&(t.dt.minute==59)).sum()),'off_hour_after_hypothesis':len(off),'missing_hours_under_hypothesis':len(missing),'variables':{}}
 for col in cols:
  v=pd.to_numeric(g[col],errors='coerce');finite=v.map(math.isfinite);z=v==0;neg=v<0
  out['variables'][col]={'finite':int(finite.sum()),'blank':int(g[col].str.strip().eq('').sum()),'nonfinite_or_unparseable':int((~finite).sum()),'zero':int(z.sum()),'negative':int(neg.sum()),'min_finite':float(v[finite].min()),'max_finite':float(v[finite].max())}
  for ix,r in g[(~finite)|z|neg].iterrows():susp.append({k:r[k] for k in ['plant','din_instante','source_file','source_line']}|{'variable':col,'raw_value':r[col],'finite':bool(finite.loc[ix]),'zero':bool(z.loc[ix]),'negative':bool(neg.loc[ix]),'other_level_raw':r[cols[1] if col==cols[0] else cols[0]],'I_raw':r.val_vazaoafluente,'Q_raw':r.val_vazaodefluente})
  gg=list(g.iterrows());vlist=list(v)
  for k in range(1,len(gg)):
   _,pr=gg[k-1];_,r=gg[k];dt=(r.t-pr.t).total_seconds()/3600
   if not (59/60<=dt<=61/60 and math.isfinite(vlist[k]) and math.isfinite(vlist[k-1])):continue
   delta=vlist[k]-vlist[k-1];jumps.append({'plant':rid,'variable':col,'previous_timestamp':pr.din_instante,'timestamp':r.din_instante,'previous_value_m':vlist[k-1],'value_m':vlist[k],'delta_m':delta,'elapsed_hours':dt,'rate_m_per_hour':delta/dt,'previous_source_file':pr.source_file,'previous_source_line':pr.source_line,'source_file':r.source_file,'source_line':r.source_line,'I_raw':r.val_vazaoafluente,'Q_raw':r.val_vazaodefluente,'context_zero_or_negative':vlist[k]<=0 or vlist[k-1]<=0})
  jj=[x for x in jumps if x['plant']==rid and x['variable']==col];a=pd.Series([abs(x['delta_m']) for x in jj]);out['variables'][col].update(adjacent_hour_differences=len(jj),absolute_delta_quantiles_m={str(q):float(a.quantile(q)) for q in [.5,.95,.99,.999,1]},delta_ge1m_count=sum(abs(x['delta_m'])>=1 for x in jj),delta_ge5m_count=sum(abs(x['delta_m'])>=5 for x in jj))
 summary.append(out)
# Review selection is amplitude only, fixed before examining model errors; never a rejection rule.
top=[]
for rid in d.plant.unique():
 for col in cols:top+=sorted([x for x in jumps if x['plant']==rid and x['variable']==col],key=lambda x:abs(x['delta_m']),reverse=True)[:20]
save('nonfinite-zero-negative.csv',susp);save('duplicate-source-rows.csv',dups,['plant','din_instante',*cols,'source_file','source_line']);save('missing-hours.csv',gaps);save('hourly-jumps-ge1m.csv',[x for x in jumps if abs(x['delta_m'])>=1]);save('top20-hourly-jumps-per-series.csv',top)
cer=[];matches=[]
for plant,rid in [('castro','JIUHCA'),('monte','JIUHMC'),('julho','JIUHQJ')]:
 f=H/f'ceran-{plant}-fresh.html';manifest.append({'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':sha(f),'role':'preserved public CERAN18h HTML; source URL/collection in hourly raw manifest'})
 text=f.read_text();headers=[html.unescape(re.sub('<[^>]+>',' ',x)).strip() for x in re.findall(r'<th>(.*?)</th>',text,re.S)];rows=[]
 for tr in re.findall('<tr>(.*?)</tr>',text,re.S):
  cells=[html.unescape(re.sub('<[^>]+>',' ',x)).strip() for x in re.findall('<td>(.*?)</td>',tr,re.S)]
  if len(cells)!=8:continue
  r={'timestamp_original':cells[0],'montante_raw':cells[1],'jusante_label_Justante_raw':cells[2]};rows.append(r)
  tt=datetime.datetime.strptime(cells[0],'%d/%m/%Y %H:%M:%S');ons=d[(d.plant==rid)&(d.t==tt)]
  for _,o in ons.iterrows():
   for col,cell in zip(cols,cells[1:3]):
    try:cv=float(cell.replace(',','.'));ov=float(o[col]);diff=cv-ov
    except ValueError:continue
    matches.append({'plant':rid,'timestamp_original':cells[0],'variable':col,'ceran_m':cv,'ons_m':ov,'difference_m':diff,'ons_file':o.source_file,'ons_line':o.source_line,'ceran_file':str(f.relative_to(R))})
 cer.append({'plant':rid,'file':str(f.relative_to(R)),'headers':headers,'rows':rows,'unit_evidence':'Nível Montante(m), Nível Justante(m) as printed','timezone_declared':bool(re.search(r'UTC|GMT|Brasília|fuso',text,re.I)),'vertical_datum_declared':False,'interpretation':'second label likely typo for Jusante; administrative/source consistency only, not common vertical datum verified'})
save('ceran-ons-same-clock-levels.csv',matches);dump('ceran-field-contract.json',cer);dump('source-manifest.json',manifest);dump('summary.json',{'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'ONS2025-2026 levels only, review without masks','raw_rows':len(d),'raw_files':18,'gap_mapping':'23:59->24:00 unverified; original timestamps preserved','jump_definition':'Adjacent originals59-61minutes; absolute delta thresholds1m and5m only review labels; top20 per series, no filtering','series':summary,'ceran_same_clock_numeric_pairs':len(matches),'ceran_max_abs_difference_m':max(abs(x['difference_m']) for x in matches) if matches else None,'eligibility_changed':False,'mask_applied':False});print(json.dumps(summary,ensure_ascii=False,indent=2));print('CERAN pairs',len(matches),'maxdiff',max(abs(x['difference_m']) for x in matches) if matches else None)
