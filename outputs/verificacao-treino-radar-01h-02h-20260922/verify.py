"""Independent history/rain-alignment verification. No fit/network/helper imports."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;R=P.parents[1]
A=R/'outputs/mucum-hourly-20260922T010016-0300';B=R/'outputs/mucum-hourly-20260922T020011-0300';D=R/'outputs/diagnostico-treino-radar-01h-02h-20260922'
S=[R/'outputs/auditoria-suporte-radar-live-01h-20260922',R/'outputs/auditoria-suporte-radar-live-02h-20260922'];TZ=timezone(timedelta(hours=-3));checks=[];inputs={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tr(p):inputs[str(p.relative_to(R))]=sha(p);return p
def js(p):return json.loads(tr(p).read_text())
def nz(p):return dict(np.load(tr(p)))
def rd(p):return list(csv.DictReader(tr(p).open()))
def ck(n,b):checks.append(dict(check=n,passed=bool(b)));assert b,n
def eq(a,b):return np.array_equal(a,b,equal_nan=True)
def changes(a,b):return int((~((a==b)|(np.isnan(a)&np.isnan(b)))).sum())
def ep(s):return datetime.fromisoformat(s).timestamp()
def iso(v):return datetime.fromtimestamp(float(v),TZ).isoformat()
def dump(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def save(n,rows):
 with (P/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def interval_windows(source,queries,window):
 # Independent sums on valid, non-overlapping measured intervals. Discard an
 # interval until its end is <=query, then subtract only its overlap before left.
 tt=source['times'];vv=source['rain'];dt=np.r_[0,np.diff(tt)];good=np.isfinite(vv)&(vv>=0)&(dt>0)&(dt<=5400)
 ends=tt[good];starts=ends-dt[good];rain=vv[good];duration=dt[good]
 total_r=np.r_[0,np.cumsum(rain)];total_t=np.r_[0,np.cumsum(duration)]
 q=queries;left=q-window*3600;right_index=np.searchsorted(ends,q,side='right');left_index=np.searchsorted(ends,left,side='right')
 amount=total_r[right_index]-total_r[left_index];cover=total_t[right_index]-total_t[left_index]
 crossing=(left_index<right_index)&(left_index<len(ends));positions=np.flatnonzero(crossing);j=left_index[positions]
 overlap=np.maximum(0,left[positions]-starts[j]);amount[positions]-=rain[j]*overlap/duration[j];cover[positions]-=overlap
 return np.maximum(amount,0),np.clip(cover/(window*3600),0,1)
def main():
 cut=ep('2026-09-21T00:00:00-03:00');root=js(D/'comparison.json')
 tr(R/'scripts/hydro_latency_forecast.py');tr(R/'scripts/hydro_rain_windows.py')
 for item in js(D/'artifact-hashes.json'):ck('coordinator '+item['file'],sha(tr(D/item['file']))==item['sha256'])
 for path,digest in root['input_sha256'].items():ck('coordinator source '+path,sha(tr(Path(path) if Path(path).is_absolute() else R/path))==digest)
 paths=[A,B];quarter=[nz(p/'telemetria-latencia.npz') for p in paths];feature=[nz(p/'radar-features.npz') for p in paths];origins=[ep(js(p/'run.json')['reference_time']) for p in paths]
 histories=[{},{}];history=[]
 for k,p in enumerate(paths):
  manifest=js(p/'history/manifest.json')
  for f in sorted((p/'history').glob('*.npz')):ck('history hash '+p.name+'/'+f.name,sha(tr(f))==manifest['files'][f.name]);histories[k][f.name]=nz(f)
 ck('same source inventory',set(histories[0])==set(histories[1]))
 for name,a in histories[0].items():
  b=histories[1][name];ia=a['times']<cut;ib=b['times']<cut;ck('history time '+name,eq(a['times'][ia],b['times'][ib]))
  for field in a:
   if field!='times':history.append(dict(source=name,field=field,rows=int(ia.sum()),changed=changes(a[field][ia],b[field][ib])))
 ck('114 historyfields unchanged',len(history)==114 and all(r['changed']==0 for r in history))
 qi=[z['times']<cut for z in quarter];fi=[z['times']<cut for z in feature];ck('same grids',eq(quarter[0]['times'][qi[0]],quarter[1]['times'][qi[1]]) and eq(feature[0]['times'][fi[0]],feature[1]['times'][fi[1]]))
 raw=[dict(field=f,changed=changes(quarter[0][f][qi[0]],quarter[1][f][qi[1]])) for f in quarter[0] if f.startswith('raw:')];ck('raw quarter unchanged',all(r['changed']==0 for r in raw))
 fc=[dict(column=j,changed=changes(feature[0]['features'][fi[0],j],feature[1]['features'][fi[1],j])) for j in range(180)]
 ck('75columns144159cells',sum(r['changed']>0 for r in fc)==75 and sum(r['changed'] for r in fc)==144159 and all(r['changed']==0 for r in fc if not 45<=r['column']<120))
 rootcols=rd(D/'feature-changes-before-cutoff.csv');ck('coordinator columns exact',all(int(r['changed'])==fc[int(r['column'])]['changed'] for r in rootcols))
 ck('base/truth unchanged',eq(feature[0]['base'][fi[0]],feature[1]['base'][fi[1]]) and eq(feature[0]['truth'][fi[0]],feature[1]['truth'][fi[1]]))
 weights=js(R/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json');codes=sorted({c for g in weights for c in g['weights']});delays=[];station_windows={};spec=[(w,0) for w in (1,3,6,12,24,48)]+[(3,lag) for lag in (3,6,12)];evidence=[]
 for code in codes:
  row=dict(station=code);regions=[g['group'] for g in weights if code in g['weights']];row['regions']=';'.join(regions)
  for k,p in enumerate(paths):
   z=histories[k]['ana-'+code+'.npz'];valid=(z['times']<=origins[k])&np.isfinite(z['rain']);ck(code+str(k)+'rain available',valid.any());latest=z['times'][valid][-1];delay=origins[k]-latest;steps=int(delay/900)
   row[f'cycle{k+1}_rain_last']=iso(latest);row[f'cycle{k+1}_rain_delay_minutes']=delay/60;row[f'cycle{k+1}_steps']=steps
   ages={x['source']:x for x in rd(p/'idades-fontes.csv')};row[f'cycle{k+1}_level_delay_minutes']=float(ages[code]['delay_minutes']) if code in ages else None
   tt=feature[k]['times'][fi[k]];gridstart=quarter[k]['times'][0]
   for w,lag in spec:
    query=tt-steps*900-lag*3600;amount,coverage=interval_windows(z,query,w)
    # shift() acts on a finite grid before weighted regional reduction.
    unavailable=query<gridstart;amount[unavailable]=0;coverage[unavailable]=0
    station_windows[k,code,w,lag]=(amount,coverage)
  row['steps_delta']=row['cycle2_steps']-row['cycle1_steps'];delays.append(row)
 for k in (0,1):
  columns=[]
  for g in weights:
   results={}
   for w,lag in spec:
    amounts=sum(weight*station_windows[k,code,w,lag][0] for code,weight in g['weights'].items());coverage=sum(weight*station_windows[k,code,w,lag][1] for code,weight in g['weights'].items())
    results[w,lag]=(np.where(coverage>=.5,amounts,np.nan),coverage)
   for w in (1,3,6,12,24,48):columns.extend(results[w,0])
   for lag in (3,6,12):
    col=results[3,lag][0].copy();col[feature[k]['times'][fi[k]]<quarter[k]['times'][0]+lag*3600]=np.nan;columns.append(col)
  recon=np.column_stack(columns);expected=feature[k]['features'][fi[k],45:120];ck(f'cycle{k+1}rainNaNs',eq(np.isnan(recon),np.isnan(expected)))
  difference=float(np.nanmax(abs(recon-expected)));ck(f'cycle{k+1}rain reconstruction',difference<2e-10)
  evidence.append(dict(cycle=k+1,cells=recon.size,max_difference_millimeters_or_fraction=difference,NaNs_exact=True));np.savez_compressed(P/f'reconstructed-rain-cycle{k+1}.npz',times=feature[k]['times'][fi[k]],features=recon)
 membership=[];support=[nz(s/'training-indices.npz') for s in S]
 for h in range(1,15):
  savedindices=[]
  for k in (0,1):
   z=feature[k];target=np.r_[z['truth'][h:],np.full(h,np.nan)];mask=(z['times']+h*3600<cut)&np.isfinite(z['base'])&np.isfinite(target)&np.isfinite(z['features'][:,:24]).all(1);ix=np.flatnonzero(mask);ck(f'cycle{k+1}h{h}membership',eq(ix,support[k][f'h{h}']));savedindices.append(ix)
  i,j=savedindices;ck(f'h{h}same indices/bases/targets',eq(i,j) and eq(feature[0]['base'][i],feature[1]['base'][j]) and eq(feature[0]['truth'][i+h],feature[1]['truth'][j+h]))
  y0=feature[0]['truth'][i+h]-feature[0]['base'][i];y1=feature[1]['truth'][j+h]-feature[1]['base'][j]
  w0=1+2*(abs(y0)>=1)+2*(feature[0]['truth'][i+h]>=9);w1=1+2*(abs(y1)>=1)+2*(feature[1]['truth'][j+h]>=9)
  ck(f'h{h}same responses/weights',eq(y0,y1) and eq(w0,w1))
  membership.append(dict(nominal_lead_h=h,before=len(i),after=len(j),added=0,removed=0,common=len(i),common_base_changed=0,common_target_changed=0))
 rootmembers=rd(D/'membership.csv');ck('root14memberships',all(all(int(r[k])==v for k,v in own.items()) for r,own in zip(rootmembers,membership)))
 ck('seven changed rain delays',sum(r['steps_delta']!=0 for r in delays)==7)
 for path,digest in inputs.items():ck('unchanged '+path,sha(R/path)==digest)
 save('history-comparison.csv',history);save('raw-grid-comparison.csv',raw);save('feature-changes.csv',fc);save('rain-delays.csv',delays);save('membership.csv',membership);dump('rain-reconstruction.json',evidence);dump('input-hashes.json',inputs)
 dump('verification.json',dict(passed=True,checked_at_utc=datetime.now(timezone.utc).isoformat(),checks_count=len(checks),checks=checks,history_fields=114,changed_history_fields=0,changed_feature_columns=75,changed_feature_cells=144159,rain_delay_changes=[r for r in delays if r['steps_delta']!=0],rain_reconstruction=evidence,membership_same_all14=True,fit_network_or_operational_execution=False,limitations=['Normalized sealed numeric histories compared, not every historical raw XML QC field.','Rain source delay separately reconstructed; idades-fontes is not rain delay metadata.','Current delay reused across historical grid changes fitted input matrix despite fixed cutoff; no claim about future error.','Reconstructed normalized history is not original publication-time certification.']))
 print('PASS',len(checks),'checks',json.dumps(evidence))
if __name__=='__main__':main()
