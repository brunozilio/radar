"""Read-only independent reconstruction of 2023 Radar matrix; writes this audit only."""
import csv,json,hashlib,bisect
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
M=ROOT/'outputs/radar-matriz-observada-2023-20260921'; S=ROOT/'outputs/radar-insumos-observados-2023-20260921'
TZ=timezone(timedelta(hours=-3)); checks=[]; sources={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def ep(v):
 d=datetime.fromisoformat(v);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(v):return datetime.fromtimestamp(v,TZ).isoformat()
def check(name,a,b,tol=0):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape,name
 np.testing.assert_allclose(a,b,atol=tol,rtol=0,equal_nan=True,err_msg=name)
 checks.append(dict(name=name,cells=a.size,max_abs=float(np.nanmax(abs(a-b))) if np.isfinite(a-b).any() else 0))
def lag(a,n):return np.r_[np.full(n,np.nan),a[:-n]] if n else a.copy()
def val(r,field):
 try:v=float(r.get(field))
 except (ValueError,TypeError):return np.nan
 if not np.isfinite(v) or v<0 or r.get('CQ_'+field) not in ('Dado aprovado',None):return np.nan
 if field=='ChuvaFinal' and v>150:return np.nan
 return v/100 if field=='NivelFinal' else v
def select(ts,v,queries,age):
 out=[];ix=[]
 for q in queries:
  j=bisect.bisect_right(ts,q)-1;ix.append(j)
  out.append(v[j] if j>=0 and q-ts[j]<=age else np.nan)
 return np.array(out),ix
for folder in (M,S,ROOT/'outputs/auditoria-latencias-chuva-20260921'):
 manifest=json.loads(use(folder/'artifact-hashes.json').read_text())
 entries=manifest['files'].items() if isinstance(manifest,dict) else [(r['file'],r['sha256']) for r in manifest]
 for f,h in entries:assert sha(folder/f)==h,(folder,f)
prep=json.loads(use(M/'preparation.json').read_text())
for f,h in prep['input_sha256'].items():assert sha(ROOT/f)==h,f
D=dict(np.load(use(M/'features.npz'))); Q=dict(np.load(use(M/'quarter-hour.npz')))
times=D['times'];grid=Q['times'];assert len(times)==720 and D['features'].shape==(720,120)
check('hourly_times',times,np.arange(ep('2023-09-01'),ep('2023-10-01'),3600)); indices=np.searchsorted(grid,times)
levels={'86510000':900,'86472000':1800,'86472600':900,'86500000':1800};delayed={};raw={};cols=[];traces=[];rows_by={}
for code in levels:
 rows=[json.loads(s) for s in use(S/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()];rows_by[code]=rows
 ts=[ep(r['DataHora']) for r in rows];v=[val(r,'NivelFinal') for r in rows];assert all(a<b for a,b in zip(ts,ts[1:]))
 raw[code],_=select(ts,v,grid,0);delayed[code],_=select(ts,v,grid-levels[code],900)
 check(code+' raw exact',raw[code],Q['raw:'+code+':H']);check(code+' delayed',delayed[code],Q[code+':H'])
 hv,ix=select(ts,v,times-levels[code],900)
 for t,x,j in zip(times,hv,ix):traces.append(dict(station=code,origin=iso(t),query=iso(t-levels[code]),source_time=iso(ts[j]) if j>=0 else '',value_m=x,usable=np.isfinite(x)))
 cols.append(delayed[code][indices])
 for hours in (.5,1,2,4,8):cols.append(((delayed[code]-lag(delayed[code],int(hours*4)))/hours)[indices])
check('base',D['base'],delayed['86510000'][indices]);check('truth exact',D['truth'],raw['86510000'][indices])
stored={(r['station'],r['origin']):r for r in csv.DictReader(use(M/'level-source-trace.csv').open())}
for t in traces:
 r=stored[t['station'],t['origin']]
 assert r['query']==t['query'] and r['source_time']==t['source_time'] and (r['usable']=='True')==t['usable']
 if t['usable']:assert float(r['value_m'])==t['value_m']
ons=[];ref=json.loads(use(S/'ons-references.json').read_text())
for r in ref:
 p=use(ROOT/r['literal_csv']);assert sha(p)==r['csv_sha256'];assert sha(ROOT/r['raw_source_path'])==r['raw_source_sha256']
 ons.extend(v for v in csv.DictReader(p.open()) if v['din_instante'].startswith(r['month']))
onsmeta=[]
for plant,code in [('julho','JIUHQJ'),('monte','JIUHMC'),('castro','JIUHCA')]:
 rs=sorted((r for r in ons if r['id_reservatorio'].strip()==code),key=lambda r:r['din_instante']);ts=[ep(r['din_instante']) for r in rs];assert len(ts)==len(set(ts))
 for field,key in [('val_vazaodefluente','Q'),('val_vazaoafluente','I')]:
  v=[float(r[field]) if r[field] else np.nan for r in rs]
  rv,_=select(ts,v,grid,5400);dv,_=select(ts,v,grid-3600,5400);check(plant+key+' raw',rv,Q['raw:'+plant+':'+key]);check(plant+key+' delayed',dv,Q[plant+':'+key]);delayed[plant+key]=dv
  picked,ix=select(ts,v,times-3600,5400)
  onsmeta.append(dict(plant=plant,field=key,finite_hourly=int(np.isfinite(picked).sum()),literal_2359_selected=sum(j>=0 and rs[j]['din_instante'][11:16]=='23:59' and times[k]-3600-ts[j]<=5400 for k,j in enumerate(ix))))
 q=delayed[plant+'Q']/1000;power=np.maximum(q,0)**.6;cols.extend([power[indices],q[indices],delayed[plant+'I'][indices]/1000])
 for h in (1,2,4,8):cols.append(((power-lag(power,h*4))/h)[indices])
check('all45 level and ONS fields',np.column_stack(cols),D['features'][:,:45])
weights=json.loads(use(ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json').read_text());lags=json.loads(use(ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json').read_text())['stations'];requests=[(w,0) for w in (1,3,6,12,24,48)]+[(3,h) for h in (3,6,12)];rain={};rainmeta=[]
for s in lags:
 code=s['station'];delay=s['shift_steps_15min']*900;assert int(s['delay_seconds']/900)==s['shift_steps_15min']
 rs=[json.loads(line) for line in use(S/'stations'/f'ana-{code}-all-qc.jsonl').read_text().splitlines()]
 end=np.array([ep(r['DataHora']) for r in rs]);dt=np.r_[0,np.diff(end)] if len(end) else np.array([]);v=np.array([val(r,'ChuvaFinal') for r in rs]);good=np.isfinite(v)&(dt>0)&(dt<=5400);right=end[good];duration=dt[good];left=right-duration;rv=v[good]
 rainmeta.append(dict(station=code,rows=len(rs),valid_intervals=int(good.sum()),effective_delay_seconds=delay))
 for w,l in requests:
  queries=times-delay-l*3600;amount=[];cover=[]
  for k in range(0,len(queries),128):
   query=queries[k:k+128,None];overlap=np.maximum(0,right[None,:]-np.maximum(left[None,:],query-w*3600));overlap*=right[None,:]<=query
   amount.extend((overlap/duration[None,:]*rv[None,:]).sum(1));cover.extend(overlap.sum(1)/(w*3600))
  rain[code,w,l]=np.array(amount),np.clip(cover,0,1)
raincols=[]
for g in weights:
 group={}
 for w,l in requests:
  p=sum(weight*rain[c,w,l][0] for c,weight in g['weights'].items());cov=sum(weight*rain[c,w,l][1] for c,weight in g['weights'].items());group[w,l]=np.where(cov>=.5,p,np.nan),cov
 for w in (1,3,6,12,24,48):raincols.extend(group[w,0])
 for l in (3,6,12):raincols.append(group[3,l][0])
check('54000 rain cells independently integrated',np.column_stack(raincols),D['features'][:,45:120],2e-10)
check('all120 columns',np.column_stack(cols+raincols),D['features'],2e-10)
assert np.isnan(D['features']).sum()==23799 and np.isfinite(D['base']).sum()==506 and np.isfinite(D['truth']).sum()==505 and not D['complete24'].any()
targetrows=list(csv.DictReader(use(M/'target-coverage.csv').open()));targetstats=[]
for h in range(1,13):
 y=np.r_[D['truth'][h:],np.full(h,np.nan)];valid=np.isfinite(y)&np.isfinite(D['base']);record=targetrows[h-1];assert int(record['valid_pairs'])==valid.sum();assert int(record['finite_target'])==np.isfinite(y).sum()
 for i in np.where(np.isfinite(y))[0]:assert times[i]+h*3600==times[i+h]
 targetstats.append(dict(horizon_h=h,valid_pairs=int(valid.sum()),finite_targets=int(np.isfinite(y).sum())))
 if h==12:current={iso(t) for t in times[valid]}
oldfile=use(ROOT/'outputs/viabilidade-historico-antigo-radar-20260921/potential-pairs.csv');old={r['origin'] for r in csv.DictReader(oldfile.open()) if r['window']=='2023' and r['horizon_h']=='12' and r['response_m']}
extra=sorted(current-old);lost=sorted(old-current);assert extra==['2023-09-01T00:00:00-03:00'] and not lost
provenance=[]
for stamp in ('2023-08-31T23:45:00','2023-09-01T12:00:00'):
 r=next(r for r in rows_by['86510000'] if ep(r['DataHora'])==ep(stamp));assert val(r,'NivelFinal') in (.86,1.43);assert sha(ROOT/r['source_file'])==r['source_sha256'];provenance.append(r)
report=dict(passed=True,checks=checks,shape=[720,120],nan_cells=23799,finite_base=506,finite_truth=505,level_trace_rows=len(traces),ons=onsmeta,rain_stations=rainmeta,target_coverage=targetstats,extra_h12=dict(old_pairs=len(old),current_pairs=len(current),extra_origins=extra,lost_origins=lost,explanation='New August warmup source contains exact approved base at August31 23:45. The extra pair is NOT caused by asof tolerance.',provenance=provenance),limitations=['Historical publication delays assumed from 2026, not observed receipt logs in 2023.','ANA normalized all-QC source previously audited against XML; current audit verifies hashes and explicit extra-pair raw provenance.','No timezone, vertical datum or cross-year operational regime certification.','No training, new queries or promotion.'],source_sha256=sources)
(OUT/'verification.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item())+'\n')
(OUT/'README.md').write_text('# Auditoria independente da matriz observada de 2023\n\nTodas as 86.400 células dos 120 campos foram reconstruídas: 17.280 de níveis, 15.120 de Q/I e 54.000 de chuva. Níveis e Q/I coincidem exatamente; chuva coincide até 2e-10 mm, inclusive máscaras de NaN. São 720 origens, 506 bases, 505 níveis contemporâneos e 23.799 células ausentes. Os 2.880 rastros de níveis e os hashes dos insumos conferem.\n\nA chuva foi integrada por sobreposição de intervalos completos, diretamente das séries ANA ALL-QC, sem helpers operacionais. A última linha ausente não é ignorada na consulta de níveis; atrasos e expiração seguem o protocolo. Q/I mantém 23:59 literal, atraso de 60 min e expiração de 90 min após a consulta.\n\nOs pares h1/h6/h12 são 503/493/481. O par extra de 12h é 01/09 00h → 12h: base aprovada de 0,86 m exatamente em 31/08 23h45, agora incluída pelo aquecimento de agosto; alvo aprovado de 1,43 m. Não decorre da tolerância asof e não foi imputado.\n\nLimites: a normalização ALL-QC foi auditada anteriormente contra XML; aqui verificamos hashes, seleção, integração e proveniência específica do par extra. Atrasos históricos continuam presumidos, fuso/datum e comparabilidade operacional não certificados. Nenhum treino, consulta nova ou promoção.\n')
(OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=p.name,sha256=sha(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),shape=report['shape'],extra=extra,target_coverage=targetstats,rain_max_difference=checks[-2]['max_abs']),indent=2))
