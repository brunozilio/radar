"""Independent reserved RADAR source→matrix reconstruction; never imports builders/models."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
import csv,json,hashlib,bisect,math
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
M=ROOT/'outputs/radar-matrizes-reservadas-2021-2022-20260922';ANA=ROOT/'outputs/radar-insumos-reservados-2021-2022-20260922';ONS=ROOT/'outputs/ons-reserva-2021-2022-20260922'
TZ=timezone(timedelta(hours=-3));checks=[];sources={};cache={}
LEVELS={'86510000':900,'86472000':1800,'86472600':900,'86500000':1800};PLANTS={'julho':'JIUHQJ','monte':'JIUHMC','castro':'JIUHCA'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def use(p):sources[str(p.relative_to(ROOT))]=sha(p);return p
def read(p):return json.loads(use(p).read_text())
def ep(v):
 d=datetime.fromisoformat(v);return (d if d.tzinfo else d.replace(tzinfo=TZ)).timestamp()
def iso(v):return datetime.fromtimestamp(v,TZ).isoformat()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ok(name,value):assert value,name;checks.append(dict(name=name,passed=True))
def compare(name,a,b,tol=0):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape,name;assert np.array_equal(np.isnan(a),np.isnan(b)),name+' NaNmask';np.testing.assert_allclose(a,b,atol=tol,rtol=0,equal_nan=True,err_msg=name)
 finite=np.isfinite(a)&np.isfinite(b);checks.append(dict(name=name,passed=True,cells=int(a.size),finite=int(finite.sum()),nan=int(np.isnan(a).sum()),max_abs=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0,tolerance=tol))
def manifest(folder):
 entries=read(folder/'artifact-hashes.json');entries=entries['files'].items() if isinstance(entries,dict) else [(r['file'],r['sha256']) for r in entries]
 for file,h in entries:assert sha(folder/file)==h,(folder,file)
 ok('manifest:'+str(folder.relative_to(ROOT)),True)
def number(v):
 try:n=float(v)
 except (ValueError,TypeError):return np.nan
 return n if np.isfinite(n) else np.nan
def parse(r,field,strict=False):
 n=number(r.get(field));qc=r.get('CQ_'+field)
 if not np.isfinite(n) or n<0 or qc not in (('Dado aprovado',) if strict else ('Dado aprovado',None)):return np.nan
 if field=='ChuvaFinal' and n>150:return np.nan
 return n/100 if field=='NivelFinal' else n
def station(year,c):
 if (year,c) not in cache:cache[year,c]=[json.loads(x) for x in use(ANA/'stations'/str(year)/f'ana-{c}-all-qc.jsonl').read_text().splitlines()]
 return cache[year,c]
def asof(t,v,qq,maxage):
 t=np.asarray(t);v=np.asarray(v);out=np.full(len(qq),np.nan);ix=np.searchsorted(t,qq,side='right')-1
 good=ix>=0
 if len(t):good&=qq-t[np.maximum(ix,0)]<=maxage;out[good]=v[ix[good]]
 return out,ix

def delayed(a,n):return np.r_[np.full(n,np.nan),a[:-n]] if n else a.copy()
def integrate_ended_intervals(left,right,values,duration,queries,window):
 # Direct sum of geometric overlap, only intervals fully ended at each query.
 # Independent from production cumulative-sum implementation.
 amount=np.zeros(len(queries));cover=np.zeros(len(queries));low=queries-window*3600
 starts=np.searchsorted(right,low,side='right');stops=np.searchsorted(right,queries,side='right')
 for i,(a,b) in enumerate(zip(starts,stops)):
  if a>=b:continue
  overlap=right[a:b]-np.maximum(left[a:b],low[i]);amount[i]=np.sum(overlap/duration[a:b]*values[a:b]);cover[i]=np.sum(overlap)/(window*3600)
 return amount,np.clip(cover,0,1)
def savecsv(name,rows):
 if rows:
  with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# Run only once the matrix publisher announces stable artifacts.
def main():
 for folder in (ANA,ONS,M):manifest(folder)
 protocol=read(ROOT/'docs/radar-reserved-2021-2022-challenge-protocol.json')
 weights=read(ROOT/'outputs/mucum-propagacao-2026-09-21/chuva-pesos.json');lags=read(ROOT/'outputs/auditoria-latencias-chuva-20260921/latencies.json')['stations'];ok('27stations',len(lags)==27 and {r['station'] for r in lags}=={c for g in weights for c in g['weights']})
 all_ons=[]
 for r in read(ONS/'ons-references.json'):
  csvp=use(ROOT/r['literal_csv']);raw=use(ROOT/r['raw_source_path']);ok('ONSsource:'+r['month'],sha(csvp)==r['csv_sha256'] and sha(raw)==r['raw_source_sha256'])
  all_ons.extend(x for x in csv.DictReader(csvp.open()) if x['din_instante'].startswith(r['month']))
 stored_qi=list(csv.DictReader(use(ONS/'lag-source-trace.csv').open()));stored_origins=list(csv.DictReader(use(ONS/'origin-diagnostics.csv').open()));results=[];base_trace=[];target_schedule=[];zero_trace=[];qi_origins=[];feature_catalog=[]
 for year in (2021,2022):
  folder=M/str(year);D=dict(np.load(use(folder/'features.npz')));Q=dict(np.load(use(folder/'quarter-hour.npz')))
  end=ep(f'{year}-06-01' if year==2021 else f'{year}-07-01');grid=np.arange(ep(f'{year}-04-28'),end,900);times=np.arange(ep(f'{year}-05-01'),end,3600);idx=np.searchsorted(grid,times);n=len(times)
  compare(f'{year}:hourgrid',times,D['times']);compare(f'{year}:quartergrid',grid,Q['times']);ok(f'{year}:shape',D['features'].shape==(n,120))
  raw={};delayed_fields={};cols=[];names=[];ons_by={};level_traces=[]
  for code,delay in LEVELS.items():
   rr=station(year,code);ts=np.array([ep(r['DataHora']) for r in rr]);v=np.array([parse(r,'NivelFinal') for r in rr]);ok(f'{year}:{code}:sorted',np.all(np.diff(ts)>0))
   raw[code+':H'],_=asof(ts,v,grid,0);delayed_fields[code+':H'],_=asof(ts,v,grid-delay,900)
   compare(f'{year}:{code}:raw',raw[code+':H'],Q['raw:'+code+':H']);compare(f'{year}:{code}:delayed',delayed_fields[code+':H'],Q[code+':H'])
   h=delayed_fields[code+':H'];cols.append(h[idx]);names.append(code+':H')
   for hours in (.5,1,2,4,8):cols.append(((h-delayed(h,int(hours*4)))/hours)[idx]);names.append(code+f':dH{hours}')
   _,selected=asof(ts,v,times-delay,900)
   for i,j in enumerate(selected):
    rr0=rr[j] if j>=0 else {};query=times[i]-delay;usable=j>=0 and query-ts[j]<=900 and np.isfinite(v[j]);value=v[j] if usable else np.nan
    level_traces.append(dict(station=code,origin=iso(times[i]),query=iso(query),source_time=iso(ts[j]) if j>=0 else '',value_m=value,usable=bool(usable)))
    if code=='86510000':base_trace.append(dict(year=year,origin=iso(times[i]),query=iso(query),source_time=rr0.get('DataHora'),age_seconds=float(query-ts[j]) if j>=0 else None,raw_level=rr0.get('NivelFinal'),qc=rr0.get('CQ_NivelFinal'),base_finite=bool(usable),source_file=rr0.get('source_file'),source_record_index=rr0.get('source_record_index')))
  compare(f'{year}:base',delayed_fields['86510000:H'][idx],D['base'])
  rr=station(year,'86510000');ts=np.array([ep(r['DataHora']) for r in rr]);strict=np.array([parse(r,'NivelFinal',True) for r in rr]);truth,_=asof(ts,strict,times,0);strict_quarter,_=asof(ts,strict,grid,0);compare(f'{year}:strict_truth_quarter',strict_quarter,Q['strict_truth']);compare(f'{year}:explicitly_approved_exact_truth',truth,D['truth'])
  stored=list(csv.DictReader(use(folder/'level-source-trace.csv').open()));lookup={(r['station'],r['origin']):r for r in stored};ok(f'{year}:leveltrace_size',len(stored)==len(lookup)==len(level_traces)==4*n)
  for r in level_traces:
   s=lookup[r['station'],r['origin']];assert s.get('query',s.get('query_time'))==r['query'] and s.get('source_time','')==r['source_time'] and (s['usable']=='True')==r['usable']
   if r['usable']:assert float(s['value_m'])==r['value_m']
  ok(f'{year}:all_leveltrace_values',True)
  for plant,code in PLANTS.items():
   rr=sorted((r for r in all_ons if r['id_reservatorio'].strip()==code and r['din_instante'].startswith(str(year))),key=lambda r:r['din_instante']);ts=np.array([ep(r['din_instante']) for r in rr]);ok(f'{year}:{plant}:uniqueONS',len(ts)==len(set(ts)));ons_by[code]=(ts,rr)
   for field,key in [('val_vazaodefluente','Q'),('val_vazaoafluente','I')]:
    v=np.array([number(r[field]) for r in rr]);raw[plant+':'+key],_=asof(ts,v,grid,5400);delayed_fields[plant+':'+key],_=asof(ts,v,grid-3600,5400)
    compare(f'{year}:{plant}:{key}:raw',raw[plant+':'+key],Q['raw:'+plant+':'+key]);compare(f'{year}:{plant}:{key}:delayed',delayed_fields[plant+':'+key],Q[plant+':'+key])
   q=delayed_fields[plant+':Q']/1000;p=np.maximum(q,0)**.6;cols.extend([p[idx],q[idx],delayed_fields[plant+':I'][idx]/1000]);names.extend([plant+':Q06',plant+':Q',plant+':I'])
   for h in (1,2,4,8):cols.append(((p-delayed(p,h*4))/h)[idx]);names.append(plant+f':dQ{h}')
  compare(f'{year}:45levels_and_QI',np.column_stack(cols),D['features'][:,:45])
  # All station windows reconstructed independently over the entire quarter-hour grid.
  station_rain={}
  for lag in lags:
   code=lag['station'];delay=int(lag['delay_seconds']/900)*900;ok(f'{year}:{code}:rain_delay',delay==lag['shift_steps_15min']*900);rr=station(year,code);ts=np.array([ep(r['DataHora']) for r in rr]);v=np.array([parse(r,'ChuvaFinal') for r in rr]);dt=np.r_[0,np.diff(ts)] if len(ts) else np.array([]);good=np.isfinite(v)&(dt>0)&(dt<=5400);right=ts[good];dur=dt[good];left=right-dur;rv=v[good]
   for w in (1,3,6,12,24,48):station_rain[code,w]=integrate_ended_intervals(left,right,rv,dur,grid-delay,w)
  for group in weights:
   name=group['group']
   for w in (1,3,6,12,24,48):
    rain=sum(weight*station_rain[c,w][0] for c,weight in group['weights'].items());coverage=sum(weight*station_rain[c,w][1] for c,weight in group['weights'].items());val=np.where(coverage>=.5,rain,np.nan);delayed_fields[name+f':P{w}']=val;delayed_fields[name+f':C{w}']=coverage
    compare(f'{year}:{name}:P{w}:allquarters',val,Q[name+f':P{w}'],2e-10);compare(f'{year}:{name}:C{w}:allquarters',coverage,Q[name+f':C{w}'],2e-10);cols.extend([val[idx],coverage[idx]]);names.extend([name+f':P{w}',name+f':C{w}'])
   for h in (3,6,12):cols.append(delayed(delayed_fields[name+':P3'],h*4)[idx]);names.append(name+f':P3lag{h}')
  F=np.column_stack(cols);compare(f'{year}:all120features',F,D['features'],2e-10);compare(f'{year}:complete24',np.isfinite(F[:,:24]).all(1).astype(float),D['complete24'].astype(float));ok(f'{year}:names120',len(names)==120)
  for j,name in enumerate(names):feature_catalog.append(dict(year=year,column=j,name=name,finite=int(np.isfinite(F[:,j]).sum()),missing=int(np.isnan(F[:,j]).sum())))
  np.savez_compressed(OUT/f'reconstructed-{year}.npz',times=times,features=F,base=delayed_fields['86510000:H'][idx],truth=truth)
  # Validate each existing Q/I dependency trace independently and recover the21feature columns.
  traces=[r for r in stored_qi if int(r['year'])==year];ok(f'{year}:QItracecount',len(traces)==18*n);tracevalues={};localzeros=[];origdiag=defaultdict(list)
  for r in traces:
   origin=ep(r['origin']);back=int(r['back_hours']);query=origin-(1+back)*3600;assert ep(r['query_naive'])==query;ts,rr=ons_by[r['plant']];j=np.searchsorted(ts,query,side='right')-1;src=rr[j] if j>=0 else None;field='val_vazaodefluente' if r['variable']=='Q' else 'val_vazaoafluente';v=number(src[field]) if src else np.nan;usable=bool(j>=0 and query-ts[j]<=5400 and np.isfinite(v));assert r['usable']==str(usable)
   if j>=0:
    assert ep(r['source_time_naive'])==ts[j] and float(r['age_seconds'])==query-ts[j];assert r['source_file']==src['source_file'] and r['source_record_index']==src['source_record_index']
   else:assert not r['source_time_naive']
   if usable:assert float(r['value_m3s'])==v
   else:assert not r['value_m3s']
   comp=[number(src[f]) for f in ('val_vazaoturbinada','val_vazaovertida','val_vazaooutrasestruturas')] if src else [np.nan]*3
   contradiction=bool(usable and r['variable']=='Q' and v==0 and np.isfinite(comp).all() and sum(comp)>1);balance=bool(usable and r['variable']=='Q' and np.isfinite(comp).all() and abs(v-sum(comp))>1);zero=bool(usable and v==0);negative=bool(usable and v<0)
   assert r['zero']==str(zero) and r['negative']==str(negative) and r['Q_zero_positive_components']==str(contradiction) and r['Q_balance_residual_gt1']==str(balance)
   tracevalues[r['origin'],r['plant'],r['variable'],back]=v if usable else np.nan;origdiag[r['origin']].append(dict(usable=usable,zero=zero,negative=negative,contradiction=contradiction,balance=balance))
   if zero:localzeros.append(dict(year=year,origin=r['origin'],plant=r['plant'],variable=r['variable'],back_hours=back,source_time_literal=src['din_instante'],value=0,contradictory_components=contradiction));zero_trace.extend(localzeros[-1:] if zero else [])
  tcols=[]
  for code in PLANTS.values():
   q=np.array([tracevalues[iso(t),code,'Q',0] for t in times])/1000;i=np.array([tracevalues[iso(t),code,'I',0] for t in times])/1000;p=np.maximum(q,0)**.6;tcols.extend([p,q,i])
   for h in (1,2,4,8):prior=np.array([tracevalues[iso(t),code,'Q',h] for t in times])/1000;tcols.append((p-np.maximum(prior,0)**.6)/h)
  compare(f'{year}:QItrace_to21features',np.column_stack(tcols),F[:,24:45]);ok(f'{year}:all_QI_flags_preserved_withoutmask',True)
  for r in (r for r in stored_origins if int(r['year'])==year):
   ds=origdiag[r['origin']];assert r['all_18_lookups_available']==str(all(d['usable'] for d in ds));assert r['uses_any_zero']==str(any(d['zero'] for d in ds));assert r['uses_any_negative']==str(any(d['negative'] for d in ds));assert r['uses_Q_zero_positive_components']==str(any(d['contradiction'] for d in ds));qi_origins.append(dict(year=year,origin=r['origin'],any_zero=any(d['zero'] for d in ds),all18available=all(d['usable'] for d in ds),any_negative=any(d['negative'] for d in ds),any_contradiction=any(d['contradiction'] for d in ds)))
  copied_qidiag=list(csv.DictReader(use(folder/'qi-origin-diagnostics.csv').open()));ok(f'{year}:QIorigin_diagnostics_exact_source',copied_qidiag==[r for r in stored_origins if int(r['year'])==year])
  saved_targets=list(csv.DictReader(use(folder/'target-coverage.csv').open()));stats=[]
  for h in range(1,13):
   target=np.r_[truth[h:],np.full(h,np.nan)];inside=times+h*3600<end;ok(f'{year}:boundaryh{h}',int((~inside).sum())==h and np.isnan(target[~inside]).all());valid=inside&np.isfinite(target)&np.isfinite(D['base']);r=dict(year=year,horizon_h=h,origin_rows=n,within_window=int(inside.sum()),boundary_excluded=int((~inside).sum()),finite_target=int(np.isfinite(target).sum()),finite_base=int(np.isfinite(D['base']).sum()),valid_pairs=int(valid.sum()),missing_target_inside=int((inside&~np.isfinite(target)).sum()),missing_base_target_finite=int((np.isfinite(target)&~np.isfinite(D['base'])).sum()));r.update(finite_base_in_schedule=int((np.isfinite(D['base'])&inside).sum()),high_observed_targets=int(((target>=7)&inside&np.isfinite(target)).sum()),high_valid_pairs=int(((target>=7)&valid).sum()));stats.append(r)
   saved=next(v for v in saved_targets if int(v['horizon_h'])==h)
   mapped={'origins':n,'scheduled_rows':r['within_window'],'boundary_excluded':r['boundary_excluded'],'finite_base_in_schedule':r['finite_base_in_schedule'],'observed_targets':r['finite_target'],'valid_pairs':r['valid_pairs'],'missing_truth_in_schedule':r['missing_target_inside'],'missing_base_observed_target':r['missing_base_target_finite'],'high_observed_targets':r['high_observed_targets'],'high_valid_pairs':r['high_valid_pairs']}
   ok(f'{year}:target_schedule_summary_h{h}',all(int(saved[k])==v for k,v in mapped.items()))
   for k,t in enumerate(times):target_schedule.append(dict(year=year,origin=iso(t),horizon_h=h,target_time=iso(t+h*3600),inside_window=bool(inside[k]),target_m=float(target[k]) if np.isfinite(target[k]) else None,base_finite=bool(np.isfinite(D['base'][k]))))
  results.append(dict(year=year,shape=[n,120],cells=n*120,nan_cells=int(np.isnan(F).sum()),finite_base=int(np.isfinite(D['base']).sum()),finite_truth=int(np.isfinite(truth).sum()),complete24=int(D['complete24'].sum()),level_traces=len(level_traces),qi_traces=len(traces),zero_qi_traces=len(localzeros),zero_qi_origins=len({r['origin'] for r in localzeros}),target_coverage=stats))
  print('Verified year',year,'cells',n*120,flush=True)
 # Frozen input lists, when present, are checked independently of the numeric reconstruction.
 for f in sorted(M.rglob('preparation.json')):
  pp=read(f)
  for path,h in pp.get('input_sha256',{}).items():ok('inputhash:'+path,sha(ROOT/path)==h)
 ok('all264960cells',sum(r['cells'] for r in results)==264960)
 savecsv('feature-catalog.csv',feature_catalog);savecsv('base-source-audit.csv',base_trace);savecsv('target-schedule.csv',target_schedule);savecsv('zero-qi-traces.csv',zero_trace);savecsv('qi-origin-checks.csv',qi_origins)
 max_difference=max(c.get('max_abs',0) for c in checks)
 report=dict(passed=True,checks=checks,years=results,total_cells=264960,maximum_absolute_cell_difference=max_difference,source_sha256=sources,limitations=['No inference/training/error calculation.','SourceALL-QC was previously compared fieldwise to XML; current audit uses immutable hashes and JSONL.','ONS literalCSV and originalhashes verified, not a new decode of original CSV here.','Timezone/datum/physical regime and historic availability remain assumed, not certified by numerical agreement.','Source-reported zeros/negatives retained; diagnostic flags never modify matrix.'])
 dump(OUT/'verification.json',report)
 lines=['# Verificação independente — matrizes reservadas 2021/2022','','Todas as 264.960 células foram reconstruídas a partir das séries ANA e dos CSVs ONS literais, sem importar builders ou helpers operacionais. Níveis e Q/I coincidem exatamente. A chuva foi recalculada por soma direta da sobreposição de intervalos encerrados; tolerância 2e-10 e máscaras NaN idênticas.', '', f'Maior diferença absoluta: {max_difference:.16g}. Passaram {len(checks)} verificações. Também foram conferidos os arrays de 15 minutos, atrasos, ordem das 120 colunas, bases, truth explicitamente aprovado e rastros de origem.', '']
 for r in results:
  lines.append(f"Ano {r['year']}: {r['shape'][0]} origens, {r['nan_cells']} células NaN, {r['finite_base']} bases finitas, {r['finite_truth']} níveis contemporâneos aprovados e {r['qi_traces']} consultas Q/I; {r['zero_qi_origins']} origem(ns) com algum zero preservado.")
  selected=[x for x in r['target_coverage'] if x['horizon_h'] in (1,6,12)];lines.append('Pares base/alvo h1/h6/h12: '+ '/'.join(str(x['valid_pairs']) for x in selected)+'.')
 lines+=['','Alvos são exatos e permanecem dentro da janela de cada ano: os últimos h ficam fora do conjunto de avaliação por fronteira, sem cruzar anos. As duas cópias de diagnósticos Q/I coincidem com as fontes. Os 39.744 rastros Q/I e os 8.832 rastros de nível foram conferidos; flags não alteram valores. A ausência de campos auxiliares não criou filtro adicional.', '', 'A auditoria não carregou modelos nem executou inferência, treino, cálculo de erros ou consultas externas. A igualdade numérica não certifica disponibilidade histórica, fuso, datum ou regime físico. ANA ALL-QC foi conferida contra XML na coleta; aqui os hashes foram verificados e a seleção/integração foi reconstruída. ONS usa CSVs literais previamente auditados e hashes originais, sem nova decodificação do arquivo de origem.']
 (OUT/'README.md').write_text('\n'.join(lines)+'\n');dump(OUT/'artifact-hashes.json',[dict(file=str(p.relative_to(OUT)),sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']);print('Passed',len(checks),'checks',flush=True)
if __name__=='__main__':main()
